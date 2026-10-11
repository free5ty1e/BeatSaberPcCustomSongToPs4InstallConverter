"""Song previews (M10, Exp 268/269) — hermetic tests for tools/song_previews.py
and the pipeline's variant threading.

Fixtures are SYNTHETIC (generated PCM + tiny FSB5s) or use the repo's built
lizzo bundles when present (HAS_BUILT gating, like the other hardware-env
classes). No PS4 access anywhere.
"""
import array
import io
import json
import math
import os
import struct
import sys
import wave

import pytest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools')
sys.path.insert(0, TOOLS)

import song_previews  # noqa: E402

HAS_BUILT = os.path.isfile(os.path.join(
    os.path.dirname(TOOLS), 'pack_modes_bundles',
    'lizzo_pack_modes_assets_all_8bf3db217732cc18af0b9a2a32d13a9a.bundle'))


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_pcm(seconds: float, freq: float = 440.0, gain: float = 0.5,
             quiet_frac: float = 0.3):
    """Synthetic stereo int16 PCM — a tone with an amplitude envelope:
    quiet head (quiet_frac), loud middle to the end (heuristic tests rely
    on the loud region being LAST)."""
    n = int(seconds * song_previews.SAMPLE_RATE)
    out = array.array('h')
    for i in range(n):
        t = i / song_previews.SAMPLE_RATE
        env = 0.05 if t < seconds * quiet_frac else 1.0
        v = int(gain * env * 20000 * math.sin(2 * math.pi * freq * t))
        out.append(v)
        out.append(v)
    return out


def rms_of(seg):
    return song_previews._rms_db(seg)


# ─────────────────────────────────────────────────────────────────────────────
# cut_preview + build_preview_fsb5
# ─────────────────────────────────────────────────────────────────────────────

class TestCutPreview:
    def test_cut_is_exactly_10s(self):
        pcm = make_pcm(30.0)
        seg = song_previews.cut_preview(pcm, 5.0)
        assert len(seg) == int(10.0 * song_previews.SAMPLE_RATE) * 2

    def test_cut_start_clamps_near_end(self):
        pcm = make_pcm(15.0)
        seg = song_previews.cut_preview(pcm, 100.0)     # start beyond the end
        # clamped to dur-10 → 5s: the last 10s of the source (the LOUD region)
        assert len(seg) == int(10.0 * song_previews.SAMPLE_RATE) * 2
        mid_rms = rms_of(seg[len(seg) // 2 - 2000:len(seg) // 2 + 2000])
        assert mid_rms > -30.0     # loud region, not the quiet head

    def test_fades_applied(self):
        pcm = make_pcm(20.0, quiet_frac=0.0)
        seg = song_previews.cut_preview(pcm, 5.0)
        # the very first frames are ~0 (fade-in starts at gain 0)
        assert abs(seg[0]) < 100 and abs(seg[1]) < 100
        # the very last frames are ~0 (fade-out ends at gain 0)
        assert abs(seg[-1]) < 100 and abs(seg[-2]) < 100
        # mid is loud
        mid_rms = rms_of(seg[len(seg) // 2 - 2000:len(seg) // 2 + 2000])
        assert mid_rms > -30.0

    def test_normalization_targets_fleet_loudness(self):
        # very quiet source (gain 0.02) → normalized up toward -10.4 dBFS
        pcm = make_pcm(20.0, gain=0.02)
        seg = song_previews.cut_preview(pcm, 5.0)
        db = rms_of(seg)
        assert abs(db - song_previews.PREVIEW_TARGET_DBFS) <= 1.0

    def test_normalization_skipped_when_close(self):
        # a source already near target must pass through (fades aside)
        pcm = make_pcm(20.0, gain=0.42)
        seg = song_previews.cut_preview(pcm, 5.0)
        db = rms_of(seg)
        assert abs(db - song_previews.PREVIEW_TARGET_DBFS) <= song_previews.PREVIEW_TOLERANCE_DB + 1.0

    def test_peak_limited(self):
        pcm = make_pcm(20.0, gain=1.0)      # clipping-hot source
        seg = song_previews.cut_preview(pcm, 5.0)
        peak = max(abs(x) for x in seg)
        peak_target = int(10 ** (song_previews.PREVIEW_PEAK_DBFS / 20.0) * 32768)
        assert peak <= peak_target + 1     # int rounding


class TestPreviewFsb5:
    def test_fsb5_header_fields(self):
        seg = song_previews.cut_preview(make_pcm(12.0), 1.0)
        fsb = song_previews.build_preview_fsb5(seg)
        assert fsb[:4] == b'FSB5'
        assert struct.unpack_from('<I', fsb, 8)[0] == 1              # numSamples
        assert struct.unpack_from('<I', fsb, 24)[0] == 2            # mode = PCM16
        total_frames = len(seg) // 2
        sd = struct.unpack_from('<Q', fsb, 60)[0]
        assert (sd >> 34) & 0x3FFFFFFF == total_frames
        assert len(fsb) == 125 + len(seg.tobytes())

    def test_fsb5_decodes_roundtrip(self):
        import fsb5
        seg = song_previews.cut_preview(make_pcm(12.0), 1.0)
        fsb = song_previews.build_preview_fsb5(seg)
        f = fsb5.FSB5(fsb)
        s = f.samples[0]
        assert int(f.header.mode) == 2        # PCM16
        assert s.frequency == 44100 and s.channels == 2
        assert s.samples == 441000            # exactly 10s


# ─────────────────────────────────────────────────────────────────────────────
# Preview start resolution
# ─────────────────────────────────────────────────────────────────────────────

class TestPreviewStart:
    def test_info_dat_v2_v3(self, tmp_path):
        d = tmp_path / 'song'
        d.mkdir()
        (d / 'Info.dat').write_text(json.dumps({'_previewStartTime': 42.5}))
        assert song_previews.preview_start_from_info(str(d)) == 42.5

    def test_info_dat_v4(self, tmp_path):
        d = tmp_path / 'song'
        d.mkdir()
        (d / 'Info.dat').write_text(json.dumps(
            {'version': '4.0.1', 'audio': {'previewStartTime': 50.0}}))
        assert song_previews.preview_start_from_info(str(d)) == 50.0

    def test_info_dat_absent(self, tmp_path):
        assert song_previews.preview_start_from_info(str(tmp_path)) is None
        (tmp_path / 'Info.dat').write_text('{}')
        assert song_previews.preview_start_from_info(str(tmp_path)) is None

    def test_info_dat_corrupt(self, tmp_path):
        (tmp_path / 'Info.dat').write_text('{not json')
        assert song_previews.preview_start_from_info(str(tmp_path)) is None


# ─────────────────────────────────────────────────────────────────────────────
# AudioClip blob parsing
# ─────────────────────────────────────────────────────────────────────────────

class TestParseAudioClipBlob:
    def _build_blob(self, name=b'TestPreview', off=1234, size=5678, fmt=1):
        src = b'archive:/CAB-abc/CAB-abc.resource'
        blob = bytearray()
        blob += struct.pack('<I', len(name)) + name
        if len(blob) % 4:
            blob += b'\x00' * (4 - len(blob) % 4)
        blob += struct.pack('<IIII', 1, 2, 44100, 16)      # load, ch, freq, bits
        blob += struct.pack('<f', 10.0)                     # length
        blob += bytes([0, 0]) + b'\x00\x00'                  # bools + align
        blob += struct.pack('<i', 0)                         # subsound
        blob += bytes([0, 1, 1]) + b'\x00'                   # preload/bg/legacy + align
        blob += struct.pack('<I', len(src)) + src
        if len(blob) % 4:
            blob += b'\x00' * (4 - len(blob) % 4)      # stream fields are 4-aligned after the string
        blob += struct.pack('<QQ', off, size)
        blob += struct.pack('<i', fmt)
        blob += b'\x00' * 4                                  # trailing pad (real blobs end here)
        return bytes(blob)

    def test_parse(self):
        blob = self._build_blob(off=999, size=111)
        tail_at, off, size, fmt = song_previews.parse_audioclip_blob(blob)
        assert off == 999 and size == 111 and fmt == 1

    def test_name_length_variation(self):
        # longer name shifts the tail — the archive anchor must adapt
        blob = self._build_blob(name=b'AVeryLongPreviewNameHere1234567890', off=7, size=9)
        tail_at, off, size, fmt = song_previews.parse_audioclip_blob(blob)
        assert off == 7 and size == 9

    def test_missing_anchor_raises(self):
        with pytest.raises(RuntimeError):
            song_previews.parse_audioclip_blob(b'\x00' * 64)


# ─────────────────────────────────────────────────────────────────────────────
# Bundle-name variant derivation
# ─────────────────────────────────────────────────────────────────────────────

class TestVariantNaming:
    def test_previews_name(self):
        assert song_previews.previews_bundle_name(
            'lizzo_pack_modes_assets_all_abc123.bundle'
        ) == 'lizzo_pack_modes_previews_assets_all_abc123.bundle'

    def test_round_trip_identity(self):
        modes = 'britneyspears_pack_modes_assets_all_x.bundle'
        var = song_previews.previews_bundle_name(modes)
        assert '_modes_previews_' in var and var != modes


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline variant threading (flag → entries → variant file)
# ─────────────────────────────────────────────────────────────────────────────

class TestPipelineVariantThreading:
    def _pipeline(self):
        import full_custom_song_pipeline as fp
        return fp

    def test_default_features_has_previews_flag(self):
        fp = self._pipeline()
        assert 'enable_song_previews' in fp.DEFAULT_FEATURES
        assert fp.DEFAULT_FEATURES['enable_song_previews'] is False

    def test_previews_enabled_reads_local_features(self, tmp_path, monkeypatch):
        fp = self._pipeline()
        fdir = tmp_path / 'features'
        fdir.mkdir()
        fpath = fdir / 'features.json'
        fpath.write_text(json.dumps({'enable_song_previews': True}))
        monkeypatch.setattr(fp, '_get_local_features_path', lambda *a, **k: str(fpath))
        assert fp._previews_enabled({}) is True
        fpath.write_text(json.dumps({'enable_song_previews': False}))
        assert fp._previews_enabled({}) is False
        # absent → default False
        fpath.write_text(json.dumps({}))
        assert fp._previews_enabled({}) is False

    @pytest.mark.skipif(not HAS_BUILT, reason='requires built lizzo modes bundle (hardware env)')
    def test_entries_point_at_variant_when_flag_on(self, tmp_path, monkeypatch):
        fp = self._pipeline()
        fdir = tmp_path / 'features'
        fdir.mkdir()
        fpath = fdir / 'features.json'
        fpath.write_text(json.dumps({'enable_song_previews': True}))
        monkeypatch.setattr(fp, '_get_local_features_path', lambda *a, **k: str(fpath))
        config = {
            'pack_modes': {
                'build_dir': os.path.join(os.path.dirname(TOOLS), 'pack_modes_bundles'),
                'song_ids_path': os.path.join(os.path.dirname(TOOLS), 'beat_saber_song_ids.json'),
            }
        }
        monkeypatch.setattr(fp, '_load_pack_albums', lambda cfg: {
            'lizzo': {'pack': 'lizzo',
                      'packBundle': 'lizzo_pack_assets_all_8bf3db217732cc18af0b9a2a32d13a9a.bundle'}
        })
        entries = fp._get_pack_modes_entries(config, packs=['lizzo'])
        assert len(entries) == 1
        assert entries[0]['patched_bundle'] == (
            'lizzo_pack_modes_previews_assets_all_8bf3db217732cc18af0b9a2a32d13a9a.bundle')

        # flag OFF → the modes-only name (today's behavior)
        fpath.write_text(json.dumps({'enable_song_previews': False}))
        entries = fp._get_pack_modes_entries(config, packs=['lizzo'])
        assert entries[0]['patched_bundle'] == (
            'lizzo_pack_modes_assets_all_8bf3db217732cc18af0b9a2a32d13a9a.bundle')


# ─────────────────────────────────────────────────────────────────────────────
# End-to-end on the REAL built bundles (hardware-env gated)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not HAS_BUILT, reason='requires built lizzo bundles (hardware env)')
class TestLizzoVariantEndToEnd:
    def test_variant_builds_and_decodes(self, tmp_path):
        """Full production path: build the lizzo variants+previews bundle from
        the real modes bundle; decode every patched clip; verify mode sets."""
        import UnityPy

        root = os.path.dirname(TOOLS)
        modes_path = os.path.join(root, 'pack_modes_bundles',
                                  'lizzo_pack_modes_assets_all_8bf3db217732cc18af0b9a2a32d13a9a.bundle')
        ids = json.load(open(os.path.join(root, 'beat_saber_song_ids.json')))
        album = [a for a in ids['albums'] if a['pack'] == 'lizzo'][0]
        config = {'paths': {'output_dir': os.path.join(root, 'custom_songs')}}

        preview_map = song_previews.build_preview_map(album, config, log=lambda *a: None)
        assert len(preview_map) == 9, 'all 9 lizzo slots are custom — all must preview'
        work = song_previews.patch_pack_previews(album, preview_map, modes_path)
        assert work is not None
        out = os.path.join(str(tmp_path),
                           song_previews.previews_bundle_name(os.path.basename(modes_path)))
        new_bundle = song_previews.rebuild_bundle_with_previews(work, out)
        assert len(new_bundle) > os.path.getsize(modes_path)

        env = UnityPy.load(out)
        patched = stock = 0
        modes_ok = 0
        for obj in env.objects:
            if obj.type.name == 'AudioClip':
                d = obj.read(check_read=False)
                for _k, wav in d.samples.items():
                    w = wave.open(io.BytesIO(wav))
                    assert abs(w.getnframes() / w.getframerate() - 10.0) < 0.01
                    if d.m_Resource.m_Offset >= 5066944:
                        patched += 1
                    else:
                        stock += 1
            elif obj.type.name == 'MonoBehaviour':
                tt = obj.read_typetree()
                if '_previewDifficultyBeatmapSets' in tt:
                    assert len(tt['_previewDifficultyBeatmapSets']) == 4
                    assert tt['_previewStartTime'] == 0.0
                    assert tt['_previewDuration'] == 10.0
                    modes_ok += 1
        assert patched == 9 and stock == 0
        assert modes_ok == 9


# ─────────────────────────────────────────────────────────────────────────────
# Exp 269b regression: the post-deploy catalog check must read the manifest row
# that matches the DEPLOYED bundle variant (flag-aware), never a stale modes row.
# (The live batch deploy failed validation on all 5 packs because the variant
# manifest rows carried packBundle=<pack id> instead of the stock bundle name,
# so the check indexed the modes rows and compared their stale crc/size.)
# ─────────────────────────────────────────────────────────────────────────────

class TestManifestVariantSelection:
    def _write_manifest(self, tmp_path, pack='lizzo',
                        modes_crc=111, var_crc=222,
                        modes_bundle='lizzo_pack_modes_assets_all_abc.bundle',
                        var_bundle='lizzo_pack_modes_previews_assets_all_abc.bundle',
                        stock='lizzo_pack_assets_all_abc.bundle',
                        guid='0092fb8fb92ea09b9665fceaf1a42d0e',
                        modes_packbundle=None, var_packbundle=None):
        """Manifest with BOTH rows. Defaults give the variant row the CORRECT
        packBundle (stock name); *_packbundle overrides let us simulate the bug."""
        entries = [
            {'pack': pack, 'patchedBundle': modes_bundle, 'packBundle':
             modes_packbundle if modes_packbundle is not None else stock,
             'catalogBundleName': guid, 'crc': modes_crc, 'size': 5000},
            {'pack': pack, 'bundle': var_bundle, 'patchedBundle': var_bundle,
             'packBundle': var_packbundle if var_packbundle is not None else stock,
             'catalogBundleName': guid, 'crc': var_crc, 'size': 9000,
             'previews': [pack]},
        ]
        import json as _json
        mp = tmp_path / 'manifest.json'
        mp.write_text(_json.dumps({'entries': entries}))
        return str(mp)

    def test_buggy_packbundle_reproduces_stale_lookup(self, tmp_path):
        """The exact live scenario: variant row's packBundle = the PACK ID →
        index-by-stock-name picks the modes row (stale crc) → check fails."""
        import build_pack_mode_bundles as pmb
        import full_custom_song_pipeline as fp
        mp = self._write_manifest(tmp_path, var_packbundle='lizzo')  # the bug
        manifest = {e['packBundle']: e for e in pmb.load_manifest(str(tmp_path))}
        me = manifest.get('lizzo_pack_assets_all_abc.bundle')
        assert me['crc'] == 111   # modes row won — the stale one. Bug reproduced.

    def test_flag_on_selects_variant_row(self, tmp_path):
        import build_pack_mode_bundles as pmb
        self._write_manifest(tmp_path)   # correct packBundle
        # the FIXED selection logic (mirrors the pipeline's check):
        for want_variant, expect in ((True, 222), (False, 111)):
            manifest = {}
            for me in pmb.load_manifest(str(tmp_path)):
                cur = manifest.get(me['packBundle'])
                is_var = 'previews' in me
                if cur is None or is_var == want_variant:
                    manifest[me['packBundle']] = me
            assert manifest['lizzo_pack_assets_all_abc.bundle']['crc'] == expect
