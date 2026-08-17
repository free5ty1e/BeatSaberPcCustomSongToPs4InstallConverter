"""
Tests for the generalized pack-patch tooling (Exp 188+):

- tools/build_pack_mode_bundles.py: blob patching (4 modes x 5 difficulties),
  UnityFS rebuild helpers, catalog entry updates (byte-wise extra-data walk).
- full_custom_song_pipeline.py pack_modes integration: deterministic entry /
  redirect derivation, merged-catalog regeneration, skip-if-built.

Pure-logic tests use synthetic blobs / catalogs; a few integration tests exercise
the real beat_saber_song_ids.json + pack_modes_bundles/ + dump when present.
"""
import os
import sys
import json
import base64
import struct
import pytest

from build_pack_mode_bundles import (
    CHAR_PATH_IDS,
    TARGET_MODES,
    TARGET_DIFFS,
    DIFF_BYTES,
    walk_blob,
    build_modes_blob,
    update_catalog_entry,
    patched_bundle_name,
    crc_decompressed_stream,
    validate_catalog_dataindexes,
    find_catalog_entry_js,
    validate_catalog_entries,
)
from full_custom_song_pipeline import (
    _get_pack_modes_entries,
    _get_pack_modes_redirects,
    _get_pack_bundle_redirects,
    _get_remote_pack_paths,
    _ensure_pack_mode_bundles,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _enc8(s: str) -> bytes:
    """Unity serialized UTF-8 string matching walk_blob.read_str (i32 len + pad)."""
    if not s:
        return struct.pack('<i', 0)
    d = s.encode('utf-8')
    pad = (-(4 + len(d))) % 4
    return struct.pack('<i', len(d)) + d + b'\x00' * pad


def _diff_record(i: int) -> bytes:
    """A 36-byte difficulty preview record (deterministic per index)."""
    return struct.pack('<I', i) * 9


def _make_synthetic_blob(sets):
    """
    Build a BeatmapLevelSO blob that walk_blob can parse.

    sets: list of (pathID, diff_count) — fileID fixed to 2.
    Returns (blob_bytes, sets_offset).
    """
    b = bytearray()
    b += b'\x00' * 12          # m_GameObject PPtr
    b += b'\x00' * 4           # m_Enabled + align
    b += b'\x00' * 12          # m_Script PPtr
    b += _enc8('')             # m_Name
    b += struct.pack('<i', 1)  # _version
    for s in ['demo_pack_sample_song', 'Song Name', 'sub', 'Artist', 'bs']:
        b += _enc8(s)
    b += b'\x00' * 12          # _previewAudioClip PPtr
    b += b'\x00' * 32          # 8 floats
    b += b'\x00' * 12          # _coverImage PPtr
    b += _enc8('')             # subtitle
    b += _enc8('')             # author
    b += struct.pack('<i', 0)  # beatmap basic info count
    b += struct.pack('<i', 0)  # characteristic set count
    sets_off = len(b)
    b += struct.pack('<i', len(sets))
    for pid, dc in sets:
        b += struct.pack('<i', 2)  # fileID
        b += struct.pack('<q', pid)
        b += struct.pack('<i', dc)
        for k in range(dc):
            b += _diff_record(k)
    b += struct.pack('<i', 0)  # contentRating
    return bytes(b), sets_off


def _catalog_block(bundle_name: str, crc: int, size: int, parity: int) -> bytes:
    """Build one SerializedObject block for m_ExtraDataString."""
    js = (f'{{"m_Hash":"0123456789abcdef","m_Crc":{crc},'
          f'"m_BundleName":"{bundle_name}","m_BundleSize":{size}}}')
    jsb = js.encode('utf-16-le')
    asm = b'Unity.Addressables'
    cls = b'A' * (parity % 2) + b'AssetBundleRequestOptions'
    out = b'\x07'
    out += bytes([len(asm)]) + asm
    out += bytes([len(cls)]) + cls
    out += struct.pack('<I', len(jsb))
    out += jsb
    return out


def _make_synthetic_catalog(blocks):
    ed = b''.join(blocks)
    return {'m_ExtraDataString': base64.b64encode(ed).decode()}


def _catalog_entries(*offsets):
    """Build m_EntryDataString: count + 7-int32 records (rec[4] = dataIndex)."""
    out = struct.pack('<I', len(offsets))
    for off in offsets:
        out += struct.pack('<7i', 0, 0, 0, 0, off, 0, 0)
    return base64.b64encode(out).decode()


def _read_entry_dataindexes(cat):
    """Return the dataIndex (rec[4]) of every m_EntryDataString record."""
    ed = base64.b64decode(cat['m_EntryDataString'])
    cnt = struct.unpack_from('<I', ed, 0)[0]
    o, out = 4, []
    for _ in range(cnt):
        rec = struct.unpack_from('<7i', ed, o)
        o += 28
        out.append(rec[4])
    return out


def _make_pack_modes_config(tmp_path, song_ids, build_dir=None, packs=None):
    sid = os.path.join(str(tmp_path), 'song_ids.json')
    with open(sid, 'w') as f:
        json.dump({'albums': song_ids}, f)
    if packs is None:
        packs = ['demopacka', 'demopackb']
    return {
        'title': {'id': 'CUSA12878'},
        'paths': {'afr_base': '/data/GoldHEN/AFR', 'afr_target_suffix': '_v3'},
        'pack_modes': {
            'packs': list(packs),
            'build_dir': build_dir or os.path.join(str(tmp_path), 'bundles'),
            'song_ids_path': sid,
            'dump_dir': str(tmp_path),
            'catalog_key': 'aa/catalog.json',
            'patched_catalog': 'catalog_pack_modes.json',
            'patched_catalog_local': os.path.join(str(tmp_path), 'catalog_pack_modes.json'),
        },
    }


_RS = 'demopacka_pack_assets_all_11111111111111111111111111111111.bundle'
_RS_PATCHED = _RS.replace('_assets_all_', '_modes_assets_all_')
_BILLIE = 'demopackb_pack_assets_all_22222222222222222222222222222222.bundle'


def _song_ids_fixture():
    return [
        {'pack': 'demopacka', 'packBundle': _RS,
         'catalogBundleName': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
         'songs': [{'songID': 'demopacka_demo_song_a'}]},
        {'pack': 'demopackb', 'packBundle': _BILLIE,
         'catalogBundleName': 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
         'songs': [{'songID': 'demopackb_demo_song_b'}]},
    ]


# ---------------------------------------------------------------------------
# Patched bundle naming
# ---------------------------------------------------------------------------

class TestPatchedBundleNaming:
    def test_inserts_modes_into_name(self):
        assert patched_bundle_name(_RS) == _RS_PATCHED

    def test_other_pack(self):
        assert patched_bundle_name(_BILLIE) == (
            'demopackb_pack_modes_assets_all_22222222222222222222222222222222.bundle')

    def test_is_deterministic(self):
        assert patched_bundle_name(_RS) == patched_bundle_name(_RS)


# ---------------------------------------------------------------------------
# build_modes_blob logic (synthetic blobs)
# ---------------------------------------------------------------------------

class TestBuildModesBlob:
    def test_single_standard_set_becomes_four_sets(self):
        """One Standard set (3 diffs) -> 4 modes x 5 diffs each."""
        blob, _ = _make_synthetic_blob([(CHAR_PATH_IDS['Standard'], 3)])
        info = walk_blob(blob)
        assert info is not None
        new_blob, changed = build_modes_blob(blob, info)
        assert changed
        new_info = walk_blob(new_blob)
        assert new_info['setCount'] == 4
        pids = {s['pathID'] for s in new_info['sets']}
        assert pids == set(CHAR_PATH_IDS[m] for m in TARGET_MODES)
        for s in new_info['sets']:
            assert s['diffCount'] == TARGET_DIFFS

    def test_short_onesaber_extended_to_five(self):
        """Existing OneSaber with 2 diffs is padded to 5; missing modes added."""
        sets = [(CHAR_PATH_IDS['Standard'], 5), (CHAR_PATH_IDS['OneSaber'], 2)]
        blob, _ = _make_synthetic_blob(sets)
        new_blob, changed = build_modes_blob(blob, walk_blob(blob))
        assert changed
        new_info = walk_blob(new_blob)
        by_pid = {s['pathID']: s for s in new_info['sets']}
        assert by_pid[CHAR_PATH_IDS['OneSaber']]['diffCount'] == 5
        assert by_pid[CHAR_PATH_IDS['Standard']]['diffCount'] == 5
        assert new_info['setCount'] == 4

    def test_full_four_sets_no_change(self):
        """4 modes x 5 diffs -> unchanged (idempotent)."""
        sets = [(CHAR_PATH_IDS[m], TARGET_DIFFS) for m in TARGET_MODES]
        blob, _ = _make_synthetic_blob(sets)
        new_blob, changed = build_modes_blob(blob, walk_blob(blob))
        assert not changed
        assert new_blob == blob

    def test_standard_record_bytes_preserved(self):
        """Existing Standard records stay byte-for-byte (only count changes)."""
        blob, _ = _make_synthetic_blob([(CHAR_PATH_IDS['Standard'], 3)])
        info = walk_blob(blob)
        new_blob, _ = build_modes_blob(blob, info)
        # Standard record prefix (fileID/pathID/count) is unchanged
        po = new_blob.find(struct.pack('<q', CHAR_PATH_IDS['Standard']))
        assert po > 0
        assert new_blob[po - 4:po] == struct.pack('<i', 2)  # fileID
        # count now 5, not 3
        assert new_blob[po + 8:po + 12] == struct.pack('<i', 5)

    def test_head_and_content_rating_preserved(self):
        """Header before sets and contentRating after sets are untouched."""
        blob, sets_off = _make_synthetic_blob([(CHAR_PATH_IDS['Standard'], 3)])
        info = walk_blob(blob)
        head = blob[:sets_off]
        rating = blob[info['contentRatingOff']:info['contentRatingOff'] + 4]
        new_blob, _ = build_modes_blob(blob, info)
        assert new_blob[:sets_off] == head
        new_info = walk_blob(new_blob)
        assert new_blob[new_info['contentRatingOff']:new_info['contentRatingOff'] + 4] == rating

    def test_unsupported_360degree_set_not_extended(self):
        """A 360Degree preview set (pid 4533580413116749821) ships as-is.

        Regression: tools/build_pack_mode_bundles.py once kept a leftover
        "360Degree" entry in CHAR_PATH_IDS, so build_modes_blob padded its
        preview set to TARGET_DIFFS (1->5, +144 B). The dev-built committed
        bundles left it at its shipped count, so the prod module produced
        non-byte-identical bundles for 10/36 packs. 360Degree is unsupported
        on PS4 (camera can't track the full arc) and hidden from the selector.
        """
        assert '360Degree' not in CHAR_PATH_IDS
        assert len(CHAR_PATH_IDS) == len(TARGET_MODES)
        three60_pid = 4533580413116749821
        sets = [(CHAR_PATH_IDS['Standard'], 5), (three60_pid, 1)]
        blob, _ = _make_synthetic_blob(sets)
        new_blob, changed = build_modes_blob(blob, walk_blob(blob))
        assert changed
        new_info = walk_blob(new_blob)
        by_pid = {s['pathID']: s for s in new_info['sets']}
        assert by_pid[three60_pid]['diffCount'] == 1
        std = by_pid[CHAR_PATH_IDS['Standard']]['diffCount']
        assert std == TARGET_DIFFS


# ---------------------------------------------------------------------------
# Catalog extra-data updates (byte-wise walk)
# ---------------------------------------------------------------------------

def _read_catalog_entries(cat):
    """Structurally walk m_ExtraDataString -> {bundle_name: (crc, size)}."""
    ex = bytearray(base64.b64decode(cat['m_ExtraDataString']))
    out = {}
    i, n = 0, len(ex)
    while i < n:
        if ex[i] != 7:
            i += 1
            continue
        try:
            ln = ex[i + 1]; po = i + 2 + ln
            ln = ex[po]; po = po + 1 + ln
            jslen = struct.unpack_from('<I', ex, po)[0]; po += 4
        except Exception:
            i += 1
            continue
        if jslen <= 0 or jslen > 400000 or po + jslen > n:
            i += 1
            continue
        s = ex[po:po + jslen].decode('utf-16-le', 'replace')
        i = po + jslen
        import re
        bn = re.search(r'"m_BundleName":"([^"]+)"', s)
        crc = re.search(r'"m_Crc":(\d+)', s)
        sz = re.search(r'"m_BundleSize":(\d+)', s)
        if bn and crc and sz:
            out[bn.group(1)] = (int(crc.group(1)), int(sz.group(1)))
    return out


class TestUpdateCatalogEntry:
    def test_updates_only_target_block(self):
        """Two blocks, different parity -> only the matching block changes."""
        cat = _make_synthetic_catalog([
            _catalog_block('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 111, 222, 0),
            _catalog_block('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', 333, 444, 1),
        ])
        out = update_catalog_entry(cat, 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', 999, 555)
        entries = _read_catalog_entries(out)
        assert entries['aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'] == (111, 222)
        assert entries['bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'] == (999, 555)

    def test_raises_for_missing_marker(self):
        cat = _make_synthetic_catalog([
            _catalog_block('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 111, 222, 0),
        ])
        with pytest.raises(ValueError):
            update_catalog_entry(cat, 'missing_marker_000000000000000000', 1, 1)

    def test_length_change_resizes_in_place(self):
        """A new CRC with a different digit count is handled."""
        cat = _make_synthetic_catalog([
            _catalog_block('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 9, 100, 0),
            _catalog_block('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', 1234567890, 100, 1),
        ])
        out = update_catalog_entry(cat, 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 1234567890, 100)
        entries = _read_catalog_entries(out)
        assert entries['aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'] == (1234567890, 100)
        assert entries['bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'] == (1234567890, 100)

    def test_entry_dataindexes_shift_when_block_grows(self):
        """
        CRITICAL regression (Exp 188 PS4 crash): m_EntryDataString rec[4] is a
        byte offset into m_ExtraDataString. When a block's JSON grows (e.g. lizzo's
        m_Crc 7->10 digits, +6 bytes), every later block shifts and every entry
        dataIndex pointing past the patched block MUST be shifted too, or the game
        reads garbage and crashes right after loading the catalog.
        """
        b1 = _catalog_block('a' * 32, 111, 222, 0)
        b2 = _catalog_block('b' * 32, 1234567890, 444, 1)
        b3 = _catalog_block('c' * 32, 555, 666, 0)
        off1, off2, off3 = 0, len(b1), len(b1) + len(b2)
        cat = {
            'm_ExtraDataString': base64.b64encode(b1 + b2 + b3).decode(),
            'm_EntryDataString': _catalog_entries(off1, off2, off3),
        }
        out = update_catalog_entry(cat, 'b' * 32, 99, 444)
        idx = _read_entry_dataindexes(out)
        delta = len(('"m_Crc":99').encode('utf-16-le')) - len('"m_Crc":1234567890'.encode('utf-16-le'))
        assert idx[0] == off1                       # before patched block: unchanged
        assert idx[1] == off2                       # the patched block itself: unchanged
        assert idx[2] == off3 + delta               # after patched block: shifted by delta

    def test_entry_dataindexes_shift_multiple_growing_blocks(self):
        """Two patched blocks that both grow -> cumulative shifts for later blocks."""
        b1 = _catalog_block('a' * 32, 9, 100, 0)       # grows: 1 digit -> 10
        b2 = _catalog_block('b' * 32, 1234567890, 200, 1)
        b3 = _catalog_block('c' * 32, 8, 300, 0)       # grows too
        b4 = _catalog_block('d' * 32, 1234567890, 400, 1)
        offs = [0]
        for b in (b1, b2, b3):
            offs.append(offs[-1] + len(b))
        cat = {
            'm_ExtraDataString': base64.b64encode(b1 + b2 + b3 + b4).decode(),
            'm_EntryDataString': _catalog_entries(*offs),
        }
        d1 = len('"m_Crc":1234567890'.encode('utf-16-le')) - len('"m_Crc":9'.encode('utf-16-le'))
        out = update_catalog_entry(cat, 'a' * 32, 1234567890, 100)
        d2 = len('"m_Crc":1234567890'.encode('utf-16-le')) - len('"m_Crc":8'.encode('utf-16-le'))
        out = update_catalog_entry(out, 'c' * 32, 1234567890, 300)
        idx = _read_entry_dataindexes(out)
        assert idx[0] == offs[0]                     # block 1 start unchanged
        assert idx[1] == offs[1] + d1                # block 2 shifted by d1
        assert idx[2] == offs[2] + d1                # block 3 shifted by d1
        assert idx[3] == offs[3] + d1 + d2           # block 4 shifted by d1 then d2

    def test_entry_dataindexes_valid_when_size_grows(self):
        """m_BundleSize digit-count growth shifts later dataIndexes too."""
        b1 = _catalog_block('a' * 32, 111, 9, 0)       # size grows: 1 -> 7 digits
        b2 = _catalog_block('b' * 32, 222, 333, 1)
        off1, off2 = 0, len(b1)
        cat = {
            'm_ExtraDataString': base64.b64encode(b1 + b2).decode(),
            'm_EntryDataString': _catalog_entries(off1, off2),
        }
        out = update_catalog_entry(cat, 'a' * 32, 111, 1234567)
        idx = _read_entry_dataindexes(out)
        delta = len('"m_BundleSize":1234567'.encode('utf-16-le')) - len('"m_BundleSize":9'.encode('utf-16-le'))
        assert idx[0] == off1
        assert idx[1] == off2 + delta


class TestCatalogValidation:
    """Validation helpers used by the post-deploy verify step (Exp 190 hardening)."""

    def _cat(self, blocks, offsets=None):
        ed = b''.join(blocks)
        cat = {'m_ExtraDataString': base64.b64encode(ed).decode()}
        if offsets is not None:
            cat['m_EntryDataString'] = _catalog_entries(*offsets)
        return cat

    def test_dataindexes_valid_after_shift(self):
        """A catalog produced by update_catalog_entry validates cleanly."""
        b1 = _catalog_block('a' * 32, 111, 222, 0)
        b2 = _catalog_block('b' * 32, 1234567890, 444, 1)
        b3 = _catalog_block('c' * 32, 555, 666, 0)
        off1, off2, off3 = 0, len(b1), len(b1) + len(b2)
        cat = {
            'm_ExtraDataString': base64.b64encode(b1 + b2 + b3).decode(),
            'm_EntryDataString': _catalog_entries(off1, off2, off3),
        }
        out = update_catalog_entry(cat, 'b' * 32, 99, 444)
        total, nonzero, bad = validate_catalog_dataindexes(out)
        assert total == 3
        assert bad == 0

    def test_dataindexes_bad_when_unshifted(self):
        """Stale dataIndexes (not shifted after a block grew) are flagged —
        this is exactly the v0.5319 PS4 crash signature."""
        b1 = _catalog_block('a' * 32, 111, 222, 0)
        b2 = _catalog_block('b' * 32, 1234567890, 444, 1)  # block 2 will grow
        b3 = _catalog_block('c' * 32, 555, 666, 0)
        off1, off2, off3 = 0, len(b1), len(b1) + len(b2)
        cat = {
            'm_ExtraDataString': base64.b64encode(b1 + b2 + b3).decode(),
            'm_EntryDataString': _catalog_entries(off1, off2, off3),
        }
        out = update_catalog_entry(cat, 'b' * 32, 99, 444)
        # Simulate a broken pipeline that updated ExtraData but forgot to shift
        # EntryData (v0.5319 bug): restore the ORIGINAL (unshifted) dataIndexes.
        out['m_EntryDataString'] = _catalog_entries(off1, off2, off3)
        total, nonzero, bad = validate_catalog_dataindexes(out)
        assert total == 3
        assert bad == 1  # third entry no longer points at a type-7 block start

    def test_negative_dataindexes_ignored(self):
        """Negative dataIndexes (unset/optional records) are not flagged."""
        b1 = _catalog_block('a' * 32, 111, 222, 0)
        cat = self._cat([b1], offsets=None)
        edi = struct.pack('<I', 2) + struct.pack('<7i', 0, 0, 0, 0, -1, 0, 0) + struct.pack('<7i', 0, 0, 0, 0, -1, 0, 0)
        cat['m_EntryDataString'] = base64.b64encode(edi).decode()
        total, nonzero, bad = validate_catalog_dataindexes(cat)
        assert total == 2
        assert nonzero == 2  # -1 is a valid "unset" marker; still counted as nonzero
        assert bad == 0

    def test_find_catalog_entry_js_returns_block(self):
        b1 = _catalog_block('aaabbbccc', 111, 222, 0)
        cat = self._cat([b1])
        s = find_catalog_entry_js(cat, 'aaabbbccc')
        assert s is not None
        assert '"m_Crc":111' in s and '"m_BundleSize":222' in s

    def test_find_catalog_entry_js_none_when_missing(self):
        cat = self._cat([_catalog_block('aaabbbccc', 111, 222, 0)])
        assert find_catalog_entry_js(cat, 'zzz999') is None

    def test_validate_catalog_entries_ok_and_mismatch(self):
        b1 = _catalog_block('aaabbbccc', 111, 222, 0)
        cat = self._cat([b1])
        missing, mismatched = validate_catalog_entries(cat, [('aaabbbccc', 111, 222)])
        assert missing == [] and mismatched == []
        missing, mismatched = validate_catalog_entries(cat, [('aaabbbccc', 999, 222)])
        assert missing == [] and mismatched == ['aaabbbccc']
        missing, mismatched = validate_catalog_entries(cat, [('nonexistent', 111, 222)])
        assert missing == ['nonexistent'] and mismatched == []


# ---------------------------------------------------------------------------
# Pipeline integration: deterministic entries / redirects (synthetic config)
# ---------------------------------------------------------------------------

class TestPackModesEntries:
    def test_derives_entries_from_song_ids(self, tmp_path):
        cfg = _make_pack_modes_config(tmp_path, _song_ids_fixture())
        entries = _get_pack_modes_entries(cfg)
        assert len(entries) == 2
        rs = next(e for e in entries if e['pack'] == 'demopacka')
        assert rs['bundle_key'] == _RS
        assert rs['patched_bundle'] == _RS_PATCHED
        assert rs['local_path'].endswith(_RS_PATCHED)

    def test_skips_unknown_packs(self, tmp_path):
        cfg = _make_pack_modes_config(tmp_path, _song_ids_fixture(),
                                      packs=['nonexistent'])
        assert _get_pack_modes_entries(cfg) == []

    def test_empty_when_no_packs(self, tmp_path):
        cfg = _make_pack_modes_config(tmp_path, _song_ids_fixture(), packs=[])
        assert _get_pack_modes_entries(cfg) == []


class TestPackModesRedirects:
    def test_no_bundles_no_redirects(self, tmp_path):
        cfg = _make_pack_modes_config(tmp_path, _song_ids_fixture())
        assert _get_pack_modes_redirects(cfg) == {}

    def test_catalog_only_when_merged_catalog_present(self, tmp_path):
        cfg = _make_pack_modes_config(tmp_path, _song_ids_fixture())
        build_dir = cfg['pack_modes']['build_dir']
        os.makedirs(build_dir, exist_ok=True)
        open(os.path.join(build_dir, _RS_PATCHED), 'w').close()
        # bundle exists but no merged catalog -> pack redirect, NO catalog redirect
        red = _get_pack_modes_redirects(cfg)
        assert red == {_RS: _RS_PATCHED}
        # add merged catalog -> catalog redirect appears
        open(cfg['pack_modes']['patched_catalog_local'], 'w').close()
        red = _get_pack_modes_redirects(cfg)
        assert red[_RS] == _RS_PATCHED
        assert red['aa/catalog.json'] == 'catalog_pack_modes.json'

    def test_pack_modes_override_single_pack_prototype(self, tmp_path):
        """When pack_modes covers the demo pack it wins over pack_bundle."""
        cfg = _make_pack_modes_config(tmp_path, _song_ids_fixture())
        cfg['pack_bundle'] = {
            'bundle_key': _RS,
            'patched_bundle': 'demopackc_pack_modes.bundle',
            'catalog_key': 'aa/catalog.json',
            'patched_catalog': 'catalog_demopackc_modes.json',
        }
        build_dir = cfg['pack_modes']['build_dir']
        os.makedirs(build_dir, exist_ok=True)
        open(os.path.join(build_dir, _RS_PATCHED), 'w').close()
        open(cfg['pack_modes']['patched_catalog_local'], 'w').close()
        red = _get_pack_bundle_redirects(cfg)
        assert red[_RS] == _RS_PATCHED  # pack_modes version, not demo pack prototype
        assert red['aa/catalog.json'] == 'catalog_pack_modes.json'

    def test_remote_paths_include_bundles_and_catalog(self, tmp_path):
        cfg = _make_pack_modes_config(tmp_path, _song_ids_fixture())
        cfg['pack_bundle'] = {
            'patched_bundle_local': '/tmp/nonexistent_demo.bundle',
            'patched_bundle': 'demopackc_pack_modes.bundle',
            'patched_catalog_local': '/tmp/nonexistent_cat.json',
            'patched_catalog': 'catalog_demopackc_modes.json',
        }
        build_dir = cfg['pack_modes']['build_dir']
        os.makedirs(build_dir, exist_ok=True)
        open(os.path.join(build_dir, _RS_PATCHED), 'w').close()
        open(os.path.join(build_dir, _BILLIE.replace('_assets_all_', '_modes_assets_all_')), 'w').close()
        open(cfg['pack_modes']['patched_catalog_local'], 'w').close()
        paths = _get_remote_pack_paths(cfg)
        names = [rn for _, rn in paths]
        assert _RS_PATCHED in names
        assert _BILLIE.replace('_assets_all_', '_modes_assets_all_') in names
        assert 'catalog_pack_modes.json' in names


# ---------------------------------------------------------------------------
# Integration with the real repo artifacts (skip if dump/song_ids missing)
# ---------------------------------------------------------------------------

_DUMP_CATALOG = '/workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/aa/catalog.json'
_SONG_IDS = '/workspace/beat_saber_deluxe/beat_saber_song_ids.json'


def _real_pack_modes_cfg():
    """Load the real pipeline config (whatever packs the user configured)."""
    from full_custom_song_pipeline import load_config
    return load_config('/nonexistent/config.json')


class TestPackModesRealArtifacts:
    @pytest.mark.skipif(not os.path.isfile(_SONG_IDS), reason='song_ids.json not present')
    def test_real_entries_and_redirects(self):
        """Real song_ids.json + real built bundles produce the configured redirect set."""
        cfg = _real_pack_modes_cfg()
        packs = cfg['pack_modes']['packs']
        entries = _get_pack_modes_entries(cfg)
        assert len(entries) == len(packs)
        assert {e['pack'] for e in entries} == set(packs)
        red = _get_pack_modes_redirects(cfg)
        assert len(red) == len(packs) + 1  # one pack redirect each + shared catalog
        assert red['aa/catalog.json'] == 'catalog_pack_modes.json'

    @pytest.mark.skipif(not os.path.isfile(_DUMP_CATALOG), reason='dump catalog not present')
    @pytest.mark.skipif(not os.path.isfile(_SONG_IDS), reason='song_ids.json not present')
    def test_ensure_skip_if_already_built(self):
        """All configured packs are built -> _ensure_pack_mode_bundles returns 0."""
        cfg = _real_pack_modes_cfg()
        built = _ensure_pack_mode_bundles(cfg)
        assert built == 0
        merged = cfg['pack_modes']['patched_catalog_local']
        assert os.path.isfile(merged)

    @pytest.mark.skipif(not os.path.isfile(_DUMP_CATALOG), reason='dump catalog not present')
    @pytest.mark.skipif(not os.path.isfile(_SONG_IDS), reason='song_ids.json not present')
    def test_merged_catalog_crcs_match_bundles(self):
        """Every merged-catalog entry's m_Crc equals the bundle's dec-stream CRC."""
        import build_pack_mode_bundles as bpm
        cfg = _real_pack_modes_cfg()
        cat = json.load(open(cfg['pack_modes']['patched_catalog_local']))
        ex = bytearray(base64.b64decode(cat['m_ExtraDataString']))
        manifest = {e['pack']: e for e in bpm.load_manifest(cfg['pack_modes']['build_dir'])}
        for pack in cfg['pack_modes']['packs']:
            m = manifest[pack]
            target = f'"m_BundleName":"{m["catalogBundleName"]}"'
            found = False
            i, n = 0, len(ex)
            while i < n:
                if ex[i] != 7:
                    i += 1
                    continue
                try:
                    ln = ex[i + 1]; po = i + 2 + ln
                    ln = ex[po]; po = po + 1 + ln
                    jslen = struct.unpack_from('<I', ex, po)[0]; po += 4
                except Exception:
                    i += 1
                    continue
                if jslen <= 0 or jslen > 400000 or po + jslen > n:
                    i += 1
                    continue
                s = ex[po:po + jslen].decode('utf-16-le', 'replace')
                if target not in s:
                    i = po + jslen
                    continue
                found = True
                assert f'"m_Crc":{m["crc"]}' in s
                assert f'"m_BundleSize":{m["size"]}' in s
                break
            assert found, f"catalog entry for {pack} not found"

    @pytest.mark.skipif(not os.path.isfile(_DUMP_CATALOG), reason='dump catalog not present')
    def test_merged_catalog_entry_dataindexes_stay_valid(self):
        """
        CRITICAL regression (v0.5319 PS4 crash): m_EntryDataString rec[4] is a
        byte offset into m_ExtraDataString. Merging ANY configured packs (some
        grow when CRC/size digit counts change) must shift later dataIndexes so
        every one still points at a type-7 block start. Runs for whatever packs
        the user configured — no hardcoded pack names.
        """
        import build_pack_mode_bundles as bpm
        cfg = _real_pack_modes_cfg()
        man = bpm.load_manifest(cfg['pack_modes']['build_dir'])
        man_by_pack = {e['pack']: e for e in man}
        cat = json.load(open(_DUMP_CATALOG))
        for pack in cfg['pack_modes']['packs']:
            e = man_by_pack[pack]
            cat = update_catalog_entry(cat, e['catalogBundleName'], e['crc'], e['size'])
        ed = base64.b64decode(cat['m_EntryDataString'])
        ex = base64.b64decode(cat['m_ExtraDataString'])
        cnt = struct.unpack_from('<I', ed, 0)[0]
        o = 4
        bad = 0
        for _ in range(cnt):
            rec = struct.unpack_from('<7i', ed, o)
            o += 28
            di = rec[4]
            if di >= 0 and (di >= len(ex) or ex[di] != 7):
                bad += 1
        assert bad == 0, f'{bad} entry dataIndexes point at non-block bytes'
        merged_entries = _read_catalog_entries(cat)
        for pack in cfg['pack_modes']['packs']:
            e = man_by_pack[pack]
            assert merged_entries[e['catalogBundleName']] == (e['crc'], e['size'])
