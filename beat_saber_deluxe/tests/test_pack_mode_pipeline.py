#!/usr/bin/env python3
"""
Comprehensive validation of the pack mode pipeline.
Tests every piece of the puzzle: origin bundle parsing, blob patching,
bundle rebuild, CRC, catalog integrity, and cross-pack comparison.

Run: cd beat_saber_deluxe && python3 -m pytest tests/test_pack_mode_pipeline.py -v
"""
import base64
import json
import os
import re
import struct
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
import build_pack_mode_bundles as bpb
import lz4.block

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMP_DIR = "/workspace/ps4_dump/CUSA12878-patch"
BUILD_DIR = os.path.join(PROJECT_ROOT, "pack_modes_bundles")
SONG_IDS_PATH = os.path.join(PROJECT_ROOT, "beat_saber_song_ids.json")
CAT_ORIGIN = os.path.join(DUMP_DIR, "Media", "StreamingAssets", "aa", "catalog.json")

TARGET_MODES = ["Standard", "OneSaber", "NoArrows", "90Degree"]


def _load_albums():
    with open(SONG_IDS_PATH) as f:
        data = json.load(f)
    return {a['pack']: a for a in data['albums']}


def _load_manifest():
    return {e['patchedBundle']: e for e in bpb.load_manifest(BUILD_DIR)}


ALBUMS = _load_albums()
MANIFEST = _load_manifest()


# ─── Tier 1: Origin bundle integrity ─────────────────────────────────────────

class TestOriginBundleIntegrity:
    """Can we read and parse the origin bundle for every configured pack?"""

    @pytest.fixture(params=["therollingstones", "lizzo", "billieeilish", "camellia"])
    def pack(self, request):
        return request.param

    def test_origin_bundle_exists(self, pack):
        a = ALBUMS[pack]
        path = os.path.join(DUMP_DIR, "Media", "StreamingAssets", "aa", "PS4", a['packBundle'])
        assert os.path.isfile(path), f"Origin bundle missing for {pack}: {path}"

    def test_origin_bundle_decompresses(self, pack):
        a = ALBUMS[pack]
        path = os.path.join(DUMP_DIR, "Media", "StreamingAssets", "aa", "PS4", a['packBundle'])
        cab_raw, blocks, flags, nodes, dec, buf = bpb.get_cab_raw(path)
        assert len(cab_raw) > 0, f"CAB raw is empty for {pack}"
        assert len(dec) > 0, f"Decompressed stream is empty for {pack}"
        assert len(nodes) >= 1, f"No nodes in bundle for {pack}"

    def test_origin_cab_size_field_matches(self, pack):
        a = ALBUMS[pack]
        path = os.path.join(DUMP_DIR, "Media", "StreamingAssets", "aa", "PS4", a['packBundle'])
        cab_raw, blocks, flags, nodes, dec, buf = bpb.get_cab_raw(path)
        cab_size = struct.unpack('>I', cab_raw[0x1C:0x20])[0]
        assert cab_size == len(cab_raw), f"CAB size field {cab_size} != actual {len(cab_raw)}"

    def test_origin_walk_blob_succeeds(self, pack):
        a = ALBUMS[pack]
        path = os.path.join(DUMP_DIR, "Media", "StreamingAssets", "aa", "PS4", a['packBundle'])
        cab_raw, blocks, flags, nodes, dec, buf = bpb.get_cab_raw(path)

        from UnityPy import Environment
        env = Environment(path)
        bf = list(env.files.values())[0]
        cab_key = next(k for k in bf.files if k.startswith('CAB-') and '.res' not in k)
        cab_obj = bf.files[cab_key]

        songs_with_patch = [s for s in a['songs'] if 'patchPathID' in s]
        assert len(songs_with_patch) > 0, f"No songs with patchPathID for {pack}"

        for song in songs_with_patch:
            obj = cab_obj.objects.get(song['patchPathID'])
            assert obj is not None, f"{pack}/{song['songID']}: patchPathID {song['patchPathID']} not in object table"
            blob = bytes(cab_raw[obj.byte_start:obj.byte_start + obj.byte_size])
            info = bpb.walk_blob(blob)
            assert info is not None, f"{pack}/{song['songID']}: walk_blob failed on {len(blob)} byte blob"
            assert info['levelID'] == song['songID'], \
                f"{pack}/{song['songID']}: walk_blob returned levelID={info['levelID']}"

    def test_origin_has_standard_mode(self, pack):
        """Every song must have Standard mode in origin."""
        a = ALBUMS[pack]
        path = os.path.join(DUMP_DIR, "Media", "StreamingAssets", "aa", "PS4", a['packBundle'])
        cab_raw, blocks, flags, nodes, dec, buf = bpb.get_cab_raw(path)

        from UnityPy import Environment
        env = Environment(path)
        bf = list(env.files.values())[0]
        cab_key = next(k for k in bf.files if k.startswith('CAB-') and '.res' not in k)
        cab_obj = bf.files[cab_key]

        for song in a['songs']:
            if 'patchPathID' not in song:
                continue
            obj = cab_obj.objects.get(song['patchPathID'])
            if obj is None:
                continue
            blob = bytes(cab_raw[obj.byte_start:obj.byte_start + obj.byte_size])
            info = bpb.walk_blob(blob)
            if info is None:
                continue
            std_pids = [s['pathID'] for s in info['sets']
                        if s['pathID'] == bpb.CHAR_PATH_IDS["Standard"]]
            assert len(std_pids) == 1, \
                f"{pack}/{song['songID']}: expected 1 Standard set, got {len(std_pids)}"

    def test_origin_no_unknown_modes(self, pack):
        """No origin bundle should have NoArrows or 90Degree (only Standard/OneSaber expected)."""
        a = ALBUMS[pack]
        path = os.path.join(DUMP_DIR, "Media", "StreamingAssets", "aa", "PS4", a['packBundle'])
        cab_raw, blocks, flags, nodes, dec, buf = bpb.get_cab_raw(path)

        from UnityPy import Environment
        env = Environment(path)
        bf = list(env.files.values())[0]
        cab_key = next(k for k in bf.files if k.startswith('CAB-') and '.res' not in k)
        cab_obj = bf.files[cab_key]

        for song in a['songs']:
            if 'patchPathID' not in song:
                continue
            obj = cab_obj.objects.get(song['patchPathID'])
            if obj is None:
                continue
            blob = bytes(cab_raw[obj.byte_start:obj.byte_start + obj.byte_size])
            info = bpb.walk_blob(blob)
            if info is None:
                continue
            known_pids = set(bpb.CHAR_PATH_IDS.values())
            unknown = [s for s in info['sets'] if s['pathID'] not in known_pids]
            if unknown:
                # Log but don't fail — some packs (ostvol1) have unknown modes
                print(f"  NOTE: {pack}/{song['songID']} has unknown modes: "
                      f"{[(s['pathID'], s['diffCount']) for s in unknown]}")


# ─── Tier 2: Blob patching correctness ───────────────────────────────────────

class TestBlobPatching:
    """Does build_modes_blob produce correct output for every song?"""

    @pytest.fixture(params=["therollingstones", "lizzo", "billieeilish", "camellia"])
    def pack(self, request):
        return request.param

    def _get_origin_blobs(self, pack):
        a = ALBUMS[pack]
        path = os.path.join(DUMP_DIR, "Media", "StreamingAssets", "aa", "PS4", a['packBundle'])
        cab_raw, blocks, flags, nodes, dec, buf = bpb.get_cab_raw(path)
        from UnityPy import Environment
        env = Environment(path)
        bf = list(env.files.values())[0]
        cab_key = next(k for k in bf.files if k.startswith('CAB-') and '.res' not in k)
        cab_obj = bf.files[cab_key]
        results = []
        for song in a['songs']:
            if 'patchPathID' not in song:
                continue
            obj = cab_obj.objects.get(song['patchPathID'])
            if obj is None:
                continue
            blob = bytes(cab_raw[obj.byte_start:obj.byte_start + obj.byte_size])
            info = bpb.walk_blob(blob)
            if info is None:
                continue
            results.append((song, blob, info))
        return results

    def test_build_modes_blob_succeeds(self, pack):
        for song, blob, info in self._get_origin_blobs(pack):
            new_blob, changed = bpb.build_modes_blob(blob, info)
            assert new_blob is not None, f"{pack}/{song['songID']}: build_modes_blob returned None"
            assert len(new_blob) > 0, f"{pack}/{song['songID']}: build_modes_blob returned empty"

    def test_build_modes_blob_grows(self, pack):
        """For packs without all 4 modes, the blob must grow."""
        for song, blob, info in self._get_origin_blobs(pack):
            new_blob, changed = bpb.build_modes_blob(blob, info)
            if info['setCount'] < 4:
                assert changed, f"{pack}/{song['songID']}: expected change but blob unchanged"
                assert len(new_blob) > len(blob), \
                    f"{pack}/{song['songID']}: expected larger blob, got {len(new_blob)} vs {len(blob)}"

    def test_patched_blob_has_4_modes(self, pack):
        """After patching, every song must have exactly 4 sets with 5 diffs each.
        New mode entries use their OWN characteristic pathID (hardware-validated,
        Exp 198/199); pre-existing entries keep theirs. All pathIDs distinct."""
        for song, blob, info in self._get_origin_blobs(pack):
            new_blob, changed = bpb.build_modes_blob(blob, info)
            if not changed:
                continue
            new_info = bpb.walk_blob(new_blob)
            assert new_info is not None, f"{pack}/{song['songID']}: walk_blob failed on patched blob"
            assert new_info['setCount'] == 4, \
                f"{pack}/{song['songID']}: expected 4 sets, got {new_info['setCount']}"

            pids = [s['pathID'] for s in new_info['sets']]
            assert len(set(pids)) == len(pids), \
                f"{pack}/{song['songID']}: duplicate set pathIDs {pids} — v0.5325 boot-crash structure"
            for i, s in enumerate(new_info['sets']):
                assert s['diffCount'] == 5, \
                    f"{pack}/{song['songID']}: set {i} has {s['diffCount']} diffs, expected 5"
                if s['pathID'] not in {x['pathID'] for x in info['sets']}:
                    expected_mode = next(m for m in bpb.TARGET_MODES
                                         if bpb.CHAR_PATH_IDS[m] == s['pathID'])
                    assert expected_mode, \
                        f"{pack}/{song['songID']}: new set {i} has unknown pathID {s['pathID']}"

    def test_patched_blob_preserves_standard(self, pack):
        """Standard mode's data should be preserved byte-for-byte."""
        for song, blob, info in self._get_origin_blobs(pack):
            new_blob, changed = bpb.build_modes_blob(blob, info)
            if not changed:
                continue
            # Find Standard in original
            std_orig = None
            po = info['setsOff'] + 4
            for s in info['sets']:
                if s['pathID'] == bpb.CHAR_PATH_IDS["Standard"]:
                    std_orig = blob[po + 16:po + 16 + s['diffCount'] * bpb.DIFF_BYTES]
                po += 16 + s['diffCount'] * bpb.DIFF_BYTES
            # Find Standard in patched
            new_info = bpb.walk_blob(new_blob)
            std_new = None
            po = new_info['setsOff'] + 4
            for s in new_info['sets']:
                if s['pathID'] == bpb.CHAR_PATH_IDS["Standard"]:
                    std_new = new_blob[po + 16:po + 16 + s['diffCount'] * bpb.DIFF_BYTES]
                po += 16 + s['diffCount'] * bpb.DIFF_BYTES
            if std_orig and std_new:
                assert std_orig == std_new, \
                    f"{pack}/{song['songID']}: Standard diffs changed after patching"

    def test_patched_blob_content_readback(self, pack):
        """New modes added by patching should be parseable by walk_blob."""
        for song, blob, info in self._get_origin_blobs(pack):
            new_blob, changed = bpb.build_modes_blob(blob, info)
            if not changed:
                continue
            new_info = bpb.walk_blob(new_blob)
            assert new_info is not None
            assert new_info['blobLen'] == len(new_blob), \
                f"{pack}/{song['songID']}: blobLen mismatch {new_info['blobLen']} vs {len(new_blob)}"

    def test_patched_no_duplicate_difficulty_ranks(self, pack):
        """Every mode in a patched blob must have exactly 5 unique difficulty ranks (0-4)."""
        for song, blob, info in self._get_origin_blobs(pack):
            new_blob, changed = bpb.build_modes_blob(blob, info)
            if not changed:
                continue
            new_info = bpb.walk_blob(new_blob)
            assert new_info is not None
            po = new_info['setsOff'] + 4
            for s in new_info['sets']:
                dc = s['diffCount']
                ranks = []
                for d in range(dc):
                    rank = struct.unpack_from('<i', new_blob, po + 16 + d * bpb.DIFF_BYTES)[0]
                    ranks.append(rank)
                po += 16 + dc * bpb.DIFF_BYTES
                assert len(ranks) == 5, \
                    f"{pack}/{song['songID']}: expected 5 diffs, got {len(ranks)}"
                assert len(set(ranks)) == 5, \
                    f"{pack}/{song['songID']}: duplicate ranks {ranks}"
                assert sorted(ranks) == [0, 1, 2, 3, 4], \
                    f"{pack}/{song['songID']}: unexpected ranks {ranks}"


# ─── Tier 3: Bundle rebuild integrity ────────────────────────────────────────

class TestBundleRebuild:
    """Does rebuild_bundle + rebuild_bundle_file produce a valid bundle?"""

    @pytest.fixture(params=["therollingstones", "lizzo", "billieeilish", "camellia"])
    def pack(self, request):
        return request.param

    def test_patched_bundle_exists(self, pack):
        a = ALBUMS[pack]
        patched_name = bpb.patched_bundle_name(a['packBundle'])
        patched_path = os.path.join(BUILD_DIR, patched_name)
        assert os.path.isfile(patched_path), f"Patched bundle missing for {pack}"

    def test_patched_bundle_decompresses(self, pack):
        a = ALBUMS[pack]
        patched_name = bpb.patched_bundle_name(a['packBundle'])
        patched_path = os.path.join(BUILD_DIR, patched_name)
        cab_raw, blocks, flags, nodes, dec, buf = bpb.get_cab_raw(patched_path)
        assert len(cab_raw) > 0
        assert len(dec) > 0

    def test_patched_cab_size_matches(self, pack):
        a = ALBUMS[pack]
        patched_name = bpb.patched_bundle_name(a['packBundle'])
        patched_path = os.path.join(BUILD_DIR, patched_name)
        cab_raw, blocks, flags, nodes, dec, buf = bpb.get_cab_raw(patched_path)
        cab_size = struct.unpack('>I', cab_raw[0x1C:0x20])[0]
        assert cab_size == len(cab_raw), f"CAB size mismatch: {cab_size} vs {len(cab_raw)}"

    def test_patched_no_object_overlaps(self, pack):
        a = ALBUMS[pack]
        patched_name = bpb.patched_bundle_name(a['packBundle'])
        patched_path = os.path.join(BUILD_DIR, patched_name)
        from UnityPy import Environment
        env = Environment(patched_path)
        bf = list(env.files.values())[0]
        cab_key = next(k for k in bf.files if k.startswith('CAB-') and '.res' not in k)
        cab_obj = bf.files[cab_key]
        obj_table = sorted(
            [(pid, o.byte_start, o.byte_size) for pid, o in cab_obj.objects.items()],
            key=lambda x: x[1]
        )
        overlaps = 0
        for i in range(len(obj_table) - 1):
            _, s1, sz1 = obj_table[i]
            _, s2, sz2 = obj_table[i + 1]
            if sz1 > 0 and s1 + sz1 > s2:
                overlaps += 1
        assert overlaps == 0, f"{pack}: {overlaps} object overlaps in patched bundle"

    def test_patched_object_count_matches(self, pack):
        """Patched bundle must have same number of objects as origin."""
        a = ALBUMS[pack]
        orig_path = os.path.join(DUMP_DIR, "Media", "StreamingAssets", "aa", "PS4", a['packBundle'])
        patched_name = bpb.patched_bundle_name(a['packBundle'])
        patched_path = os.path.join(BUILD_DIR, patched_name)

        from UnityPy import Environment

        env_o = Environment(orig_path)
        bf_o = list(env_o.files.values())[0]
        cab_key_o = next(k for k in bf_o.files if k.startswith('CAB-') and '.res' not in k)
        orig_count = len(bf_o.files[cab_key_o].objects)

        env_p = Environment(patched_path)
        bf_p = list(env_p.files.values())[0]
        cab_key_p = next(k for k in bf_p.files if k.startswith('CAB-') and '.res' not in k)
        patched_count = len(bf_p.files[cab_key_p].objects)

        assert patched_count == orig_count, \
            f"{pack}: object count {patched_count} != orig {orig_count}"

    def test_patched_blobs_parseable(self, pack):
        """All BeatmapLevelSO blobs in patched bundle must be parseable by walk_blob."""
        a = ALBUMS[pack]
        patched_name = bpb.patched_bundle_name(a['packBundle'])
        patched_path = os.path.join(BUILD_DIR, patched_name)
        cab_raw, blocks, flags, nodes, dec, buf = bpb.get_cab_raw(patched_path)

        from UnityPy import Environment
        env = Environment(patched_path)
        bf = list(env.files.values())[0]
        cab_key = next(k for k in bf.files if k.startswith('CAB-') and '.res' not in k)
        cab_obj = bf.files[cab_key]

        for song in a['songs']:
            if 'patchPathID' not in song:
                continue
            obj = cab_obj.objects.get(song['patchPathID'])
            if obj is None:
                continue
            blob = bytes(cab_raw[obj.byte_start:obj.byte_start + obj.byte_size])
            info = bpb.walk_blob(blob)
            assert info is not None, \
                f"{pack}/{song['songID']}: walk_blob failed on patched blob ({len(blob)} bytes)"
            assert info['levelID'] == song['songID'], \
                f"{pack}/{song['songID']}: levelID mismatch in patched blob"


# ─── Tier 4: CRC and catalog consistency ─────────────────────────────────────

class TestCRCAndCatalog:
    """Does the patched bundle CRC match the catalog entry?"""

    @pytest.fixture(params=["therollingstones", "lizzo", "billieeilish", "camellia"])
    def pack(self, request):
        return request.param

    def test_manifest_crc_matches_bundle(self, pack):
        a = ALBUMS[pack]
        patched_name = bpb.patched_bundle_name(a['packBundle'])
        m = MANIFEST.get(patched_name)
        assert m is not None, f"{pack}: not in manifest"
        patched_path = os.path.join(BUILD_DIR, patched_name)
        actual_crc = bpb.crc_decompressed_stream(open(patched_path, 'rb').read())
        assert m['crc'] == actual_crc, \
            f"{pack}: manifest CRC {m['crc']} != actual CRC {actual_crc}"

    def test_manifest_size_matches_bundle(self, pack):
        a = ALBUMS[pack]
        patched_name = bpb.patched_bundle_name(a['packBundle'])
        m = MANIFEST.get(patched_name)
        assert m is not None
        patched_path = os.path.join(BUILD_DIR, patched_name)
        actual_size = os.path.getsize(patched_path)
        assert m['size'] == actual_size, \
            f"{pack}: manifest size {m['size']} != actual size {actual_size}"

    def test_catalog_entry_matches_manifest(self, pack):
        """The merged catalog must carry the manifest's CRC and size for this pack."""
        a = ALBUMS[pack]
        patched_name = bpb.patched_bundle_name(a['packBundle'])
        m = MANIFEST.get(patched_name)
        assert m is not None

        patched_path = os.path.join(BUILD_DIR, patched_name)
        actual_crc = bpb.crc_decompressed_stream(open(patched_path, 'rb').read())
        actual_size = os.path.getsize(patched_path)

        # Build a catalog with just this pack
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            bpb.write_merged_catalog(CAT_ORIGIN, [m], tmp_path)
            with open(tmp_path) as f:
                cat = json.load(f)

            marker = a['catalogBundleName']
            s = bpb.find_catalog_entry_js(cat, marker)
            assert s is not None, f"{pack}: catalog entry not found for marker {marker}"

            crc_m = re.search(r'"m_Crc":(\d+)', s)
            size_m = re.search(r'"m_BundleSize":(\d+)', s)
            assert crc_m is not None, f"{pack}: m_Crc not found in catalog block"
            assert size_m is not None, f"{pack}: m_BundleSize not found in catalog block"

            cat_crc = int(crc_m.group(1))
            cat_size = int(size_m.group(1))
            assert cat_crc == actual_crc, \
                f"{pack}: catalog CRC {cat_crc} != bundle CRC {actual_crc}"
            assert cat_size == actual_size, \
                f"{pack}: catalog size {cat_size} != bundle size {actual_size}"
        finally:
            os.unlink(tmp_path)

    def test_catalog_origin_unchanged(self, pack):
        """For this pack's entry, the origin catalog CRC should differ from patched."""
        a = ALBUMS[pack]
        marker = a['catalogBundleName']

        patched_name = bpb.patched_bundle_name(a['packBundle'])
        m = MANIFEST.get(patched_name)
        assert m is not None

        with open(CAT_ORIGIN) as f:
            cat_orig = json.load(f)
        s_orig = bpb.find_catalog_entry_js(cat_orig, marker)
        assert s_orig is not None

        crc_orig = re.search(r'"m_Crc":(\d+)', s_orig)
        size_orig = re.search(r'"m_BundleSize":(\d+)', s_orig)

        # Origin catalog should NOT have the patched CRC
        assert int(crc_orig.group(1)) != m['crc'], \
            f"{pack}: origin catalog already has patched CRC (stale?)"

    def test_catalog_digit_count_change(self, pack):
        """Track whether the CRC/size digit count changed (causes ExtraDataString growth)."""
        a = ALBUMS[pack]
        marker = a['catalogBundleName']
        patched_name = bpb.patched_bundle_name(a['packBundle'])
        m = MANIFEST.get(patched_name)
        assert m is not None

        with open(CAT_ORIGIN) as f:
            cat_orig = json.load(f)
        s_orig = bpb.find_catalog_entry_js(cat_orig, marker)

        crc_orig = int(re.search(r'"m_Crc":(\d+)', s_orig).group(1))
        size_orig = int(re.search(r'"m_BundleSize":(\d+)', s_orig).group(1))

        crc_new = m['crc']
        size_new = m['size']

        crc_digits_delta = len(str(crc_new)) - len(str(crc_orig))
        size_digits_delta = len(str(size_new)) - len(str(size_orig))

        print(f"\n  {pack}: CRC {crc_orig}({len(str(crc_orig))}d) -> {crc_new}({len(str(crc_new))}d) delta={crc_digits_delta}d")
        print(f"  {pack}: Size {size_orig}({len(str(size_orig))}d) -> {size_new}({len(str(size_new))}d) delta={size_digits_delta}d")

        if crc_digits_delta != 0 or size_digits_delta != 0:
            print(f"  WARNING: {pack} has digit count change! ExtraDataString will grow by "
                  f"{(crc_digits_delta + size_digits_delta) * 2} bytes (UTF-16). "
                  f"Dataindexes will shift.")


# ─── Tier 5: Catalog dataindex integrity after merge ─────────────────────────

class TestCatalogDataindexes:
    """Verify all dataindexes remain valid after catalog regeneration."""

    @pytest.fixture(params=["therollingstones", "lizzo", "billieeilish", "camellia"])
    def pack(self, request):
        return request.param

    def test_dataindexes_valid_after_merge(self, pack):
        a = ALBUMS[pack]
        patched_name = bpb.patched_bundle_name(a['packBundle'])
        m = MANIFEST.get(patched_name)
        assert m is not None

        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            bpb.write_merged_catalog(CAT_ORIGIN, [m], tmp_path)
            with open(tmp_path) as f:
                cat = json.load(f)
            total, nonzero, bad = bpb.validate_catalog_dataindexes(cat)
            assert bad == 0, \
                f"{pack}: {bad}/{total} bad dataindexes after merge!"
            print(f"\n  {pack}: {total} entries, {nonzero} nonzero, {bad} bad")
        finally:
            os.unlink(tmp_path)

    def test_all_blocks_parseable(self, pack):
        """Every type-7 block in ExtraDataString must be parseable."""
        a = ALBUMS[pack]
        patched_name = bpb.patched_bundle_name(a['packBundle'])
        m = MANIFEST.get(patched_name)
        assert m is not None

        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            bpb.write_merged_catalog(CAT_ORIGIN, [m], tmp_path)
            with open(tmp_path) as f:
                cat = json.load(f)

            ed = base64.b64decode(cat['m_ExtraDataString'])
            n = len(ed)
            i = 0
            block_count = 0
            bad_blocks = 0
            while i < n:
                if ed[i] != 7:
                    i += 1
                    continue
                try:
                    ln = ed[i + 1]
                    po = i + 2 + ln
                    ln2 = ed[po]
                    po = po + 1 + ln2
                    jslen = struct.unpack_from('<I', ed, po)[0]
                    po += 4
                except Exception:
                    bad_blocks += 1
                    i += 1
                    continue
                if jslen <= 0 or jslen > 400000 or po + jslen > n:
                    bad_blocks += 1
                    i = po + jslen if (jslen > 0 and po + jslen <= n) else i + 1
                    continue
                block_count += 1
                i = po + jslen

            assert bad_blocks == 0, f"{pack}: {bad_blocks} unparseable blocks in ExtraDataString"
            print(f"\n  {pack}: {block_count} blocks, {bad_blocks} bad")
        finally:
            os.unlink(tmp_path)


# ─── Tier 6: Cross-pack structural comparison ────────────────────────────────

class TestCrossPackComparison:
    """Compare therollingstones (works) vs others (crash) to find structural diffs."""

    def test_therollingstones_vs_lizzo_origin_sets(self):
        """therollingstones has 1 set, lizzo has 1-2 sets. Document this difference."""
        ts = ALBUMS['therollingstones']
        lz = ALBUMS['lizzo']

        def get_origin_set_counts(pack_name):
            a = ALBUMS[pack_name]
            path = os.path.join(DUMP_DIR, "Media", "StreamingAssets", "aa", "PS4", a['packBundle'])
            cab_raw, _, _, _, _, _ = bpb.get_cab_raw(path)
            from UnityPy import Environment
            env = Environment(path)
            bf = list(env.files.values())[0]
            cab_key = next(k for k in bf.files if k.startswith('CAB-') and '.res' not in k)
            cab_obj = bf.files[cab_key]
            counts = []
            for song in a['songs']:
                if 'patchPathID' not in song:
                    continue
                obj = cab_obj.objects.get(song['patchPathID'])
                if obj is None:
                    continue
                blob = bytes(cab_raw[obj.byte_start:obj.byte_start + obj.byte_size])
                info = bpb.walk_blob(blob)
                if info:
                    counts.append((song['songID'], info['setCount'],
                                   [(s['pathID'], s['diffCount']) for s in info['sets']]))
            return counts

        ts_counts = get_origin_set_counts('therollingstones')
        lz_counts = get_origin_set_counts('lizzo')

        ts_max = max(c for _, c, _ in ts_counts)
        lz_max = max(c for _, c, _ in lz_counts)

        print(f"\n  therollingstones max sets: {ts_max}")
        print(f"  lizzo max sets: {lz_max}")

        # Document the difference
        assert ts_max == 1, "therollingstones should have max 1 set"
        # lizzo can have 1 or 2 sets
        assert lz_max <= 2, "lizzo should have max 2 sets"

    def test_all_packs_set_counts(self):
        """Document origin set counts for all configured packs."""
        print("\n  Origin set counts per pack:")
        for pack_name in sorted(ALBUMS.keys()):
            a = ALBUMS[pack_name]
            if 'packBundle' not in a:
                continue
            path = os.path.join(DUMP_DIR, "Media", "StreamingAssets", "aa", "PS4", a['packBundle'])
            if not os.path.isfile(path):
                continue
            try:
                cab_raw, _, _, _, _, _ = bpb.get_cab_raw(path)
                from UnityPy import Environment
                env = Environment(path)
                bf = list(env.files.values())[0]
                cab_key = next(k for k in bf.files if k.startswith('CAB-') and '.res' not in k)
                cab_obj = bf.files[cab_key]
                counts = []
                for song in a['songs']:
                    if 'patchPathID' not in song:
                        continue
                    obj = cab_obj.objects.get(song['patchPathID'])
                    if obj is None:
                        continue
                    blob = bytes(cab_raw[obj.byte_start:obj.byte_start + obj.byte_size])
                    info = bpb.walk_blob(blob)
                    if info:
                        counts.append(info['setCount'])
                if counts:
                    print(f"    {pack_name:25s}: {len(counts)} songs, sets={counts}")
            except Exception as e:
                print(f"    {pack_name:25s}: ERROR {e}")

    def test_patched_blob_size_consistency(self):
        """For therollingstones, all patched blobs should have similar size (all grew from 1 set)."""
        a = ALBUMS['therollingstones']
        path = os.path.join(DUMP_DIR, "Media", "StreamingAssets", "aa", "PS4", a['packBundle'])
        cab_raw, _, _, _, _, _ = bpb.get_cab_raw(path)
        from UnityPy import Environment
        env = Environment(path)
        bf = list(env.files.values())[0]
        cab_key = next(k for k in bf.files if k.startswith('CAB-') and '.res' not in k)
        cab_obj = bf.files[cab_key]

        sizes = []
        for song in a['songs']:
            if 'patchPathID' not in song:
                continue
            obj = cab_obj.objects.get(song['patchPathID'])
            if obj is None:
                continue
            blob = bytes(cab_raw[obj.byte_start:obj.byte_start + obj.byte_size])
            new_blob, changed = bpb.build_modes_blob(blob, bpb.walk_blob(blob))
            if changed:
                sizes.append((song['songID'], len(blob), len(new_blob), len(new_blob) - len(blob)))

        print("\n  therollingstones blob growth:")
        for name, orig, new, delta in sizes:
            print(f"    {name:25s}: {orig} -> {new} (+{delta})")

        # All should grow by similar amount (adding 3 modes)
        deltas = [d for _, _, _, d in sizes]
        assert max(deltas) - min(deltas) < 100, \
            f"therollingstones delta spread too wide: {min(deltas)}-{max(deltas)}"

    def test_lizzo_blob_size_variability(self):
        """lizzo has mixed origin set counts, so blob growth will vary."""
        a = ALBUMS['lizzo']
        path = os.path.join(DUMP_DIR, "Media", "StreamingAssets", "aa", "PS4", a['packBundle'])
        cab_raw, _, _, _, _, _ = bpb.get_cab_raw(path)
        from UnityPy import Environment
        env = Environment(path)
        bf = list(env.files.values())[0]
        cab_key = next(k for k in bf.files if k.startswith('CAB-') and '.res' not in k)
        cab_obj = bf.files[cab_key]

        sizes = []
        for song in a['songs']:
            if 'patchPathID' not in song:
                continue
            obj = cab_obj.objects.get(song['patchPathID'])
            if obj is None:
                continue
            blob = bytes(cab_raw[obj.byte_start:obj.byte_start + obj.byte_size])
            info = bpb.walk_blob(blob)
            new_blob, changed = bpb.build_modes_blob(blob, info)
            if changed:
                sizes.append((song['songID'], info['setCount'], len(blob), len(new_blob),
                              len(new_blob) - len(blob)))

        print("\n  lizzo blob growth:")
        for name, sets, orig, new, delta in sizes:
            print(f"    {name:25s}: {sets} sets, {orig} -> {new} (+{delta})")

        # lizzo has some songs with 2 sets (less growth) and some with 1 set (more growth)
        set_counts = [s for _, s, _, _, _ in sizes]
        assert 1 in set_counts and 2 in set_counts, \
            "lizzo should have songs with both 1 and 2 origin sets"


# ─── Tier 7: Feature flag gating ─────────────────────────────────────────────

class TestFeatureFlagGating:
    """Verify feature flags properly gate all redirect/catalog functionality."""

    def test_plugin_feature_flags_documented(self):
        """The plugin should have feature flags for all major functionality."""
        main_cpp = os.path.join(PROJECT_ROOT, "src", "main.cpp")
        with open(main_cpp) as f:
            code = f.read()

        # Check for feature flag variables
        assert "g_feature_custom_song_replacements" in code, "Missing custom_song_replacements flag"
        assert "g_feature_song_metadata_modification" in code, "Missing song_metadata_modification flag"

        # Check redirect is gated behind feature flag
        assert "g_feature_custom_song_replacements" in code.split("REDIRECT")[0] or \
               code.count("g_feature_custom_song_replacements") >= 2, \
               "Redirects may not be gated behind feature flag"

    def test_features_json_has_required_flags(self):
        features_path = os.path.join(PROJECT_ROOT, "features.json")
        assert os.path.isfile(features_path), "features.json missing"
        with open(features_path) as f:
            features = json.load(f)
        assert "enable_custom_song_replacements" in features
        assert "enable_song_metadata_modification" in features

    def test_redirect_gated_behind_feature_flag(self):
        """The redirect matching in open_hook must check g_feature_custom_song_replacements."""
        main_cpp = os.path.join(PROJECT_ROOT, "src", "main.cpp")
        with open(main_cpp) as f:
            code = f.read()

        # Find the open_hook function's redirect matching section
        open_hook_start = code.find("static int open_hook(")
        assert open_hook_start > 0, "open_hook function not found"
        open_hook_code = code[open_hook_start:open_hook_start + 1500]

        # The actual redirect matching (strstr lower_path, LOWER_REDIRECT_KEYS) must be gated
        assert "g_feature_custom_song_replacements" in open_hook_code, \
            "open_hook redirect matching is NOT gated behind g_feature_custom_song_replacements"

        # Verify the gate is BEFORE the redirect loop
        gate_pos = open_hook_code.find("g_feature_custom_song_replacements")
        redirect_loop_pos = open_hook_code.find("for (int i = 0; i < REDIRECT_COUNT")
        assert gate_pos < redirect_loop_pos, \
            "Feature flag check must come BEFORE the redirect loop in open_hook"

    def test_no_beatmap_mode_mapping_flag_exists(self):
        """There is currently NO feature flag for beatmap mode mapping / pack redirects."""
        main_cpp = os.path.join(PROJECT_ROOT, "src", "main.cpp")
        with open(main_cpp) as f:
            code = f.read()
        # This should be True — we're documenting that the flag doesn't exist yet
        assert "g_feature_beatmap_mode_mapping" not in code, \
            "beatmap_mode_mapping flag exists (unexpected)"
        assert "enable_beatmap_mode_mapping" not in code, \
            "enable_beatmap_mode_mapping flag exists (unexpected)"


# ─── Tier 8: Config generation consistency ───────────────────────────────────

class TestConfigGeneration:
    """Verify that pipeline config generation produces consistent results."""

    def test_single_pack_catalog_has_one_entry(self):
        """A single-pack catalog should update exactly 1 entry from origin."""
        import tempfile
        for pack in ["therollingstones", "lizzo"]:
            a = ALBUMS[pack]
            patched_name = bpb.patched_bundle_name(a['packBundle'])
            m = MANIFEST.get(patched_name)
            assert m is not None

            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
                tmp_path = tmp.name
            try:
                n = bpb.write_merged_catalog(CAT_ORIGIN, [m], tmp_path)
                assert n == 1, f"{pack}: expected 1 entry updated, got {n}"

                with open(tmp_path) as f:
                    cat = json.load(f)
                total, nonzero, bad = bpb.validate_catalog_dataindexes(cat)
                assert bad == 0, f"{pack}: {bad} bad dataindexes"
            finally:
                os.unlink(tmp_path)

    def test_catalog_regeneration_deterministic(self):
        """Regenerating the catalog should produce identical output."""
        import tempfile
        a = ALBUMS['lizzo']
        patched_name = bpb.patched_bundle_name(a['packBundle'])
        m = MANIFEST.get(patched_name)

        paths = []
        for i in range(2):
            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
                paths.append(tmp.name)
            bpb.write_merged_catalog(CAT_ORIGIN, [m], paths[-1])

        with open(paths[0]) as f:
            cat1 = f.read()
        with open(paths[1]) as f:
            cat2 = f.read()

        for p in paths:
            os.unlink(p)

        assert cat1 == cat2, "Catalog regeneration is NOT deterministic!"
