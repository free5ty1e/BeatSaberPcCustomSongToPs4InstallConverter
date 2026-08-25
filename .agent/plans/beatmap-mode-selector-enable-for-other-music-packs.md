# Enable Beatmap Mode Selector for All 36 DLC Music Packs

**Status:** EXP 199 - v0.5325 pathID change REVERTED (it was the boot crash; the golden RS structure uses DISTINCT pathIDs). v0.5326 rebuilt bundles byte-identical to hardware-proven artifacts; redeployed via pipeline (lizzo-only + 38 songs), validation PASSED. AWAITING USER BOOT/GAMEPLAY TEST.
**Feature:** Inject 4-mode selector (Standard/OneSaber/NoArrows/90°) into all 36 DLC packs  
**Date:** 2026-08-25  
**Current versions:** Plugin v0.8041 (= v0.8040 baseline + diagnostics), Pipeline v0.5325  

---

## 1. What We're Trying To Do

Beat Saber PS4 shows a mode selector (Standard/OneSaber/NoArrows/90°) per song, but only if the pack's BeatmapLevelSO `_previewDifficultyBeatmapSets` array contains entries for those modes. The original game packs only ship with Standard mode. We:

1. **Build patched pack bundles** — replace the `_previewDifficultyBeatmapSets` blob in each BeatmapLevelSO inside a pack bundle with one containing 4 modes × 5 difficulties
2. **Redirect the pack bundle** — via GoldHEN `open()` hook + `redirects.json`, so when the game opens `aa/PS4/<pack>_assets_all_<hash>.bundle` it reads our patched version from AFR
3. **Redirect the Addressables catalog** — `aa/catalog.json` → `catalog_pack_modes.json` with updated `m_Crc`/`m_BundleSize` for the patched bundles, so the game's CRC validation passes

This worked for **therollingstones only** (1 pack, 11 songs, Standard-only). It **crashes for all other packs** (lizzo, billieeilish, camellia).

---

## 2. What Works vs What Crashes

### Works: therollingstones-only config
- 2 redirects: therollingstones pack bundle + catalog.json
- 0 song redirects (no per-song custom songs deployed)
- Boot completes, all 4 mode buttons appear, game reaches menu
- **Log:** `/tmp/opencode/bs_log_v08045.txt` (9,246 lines, full boot)
- **Key log sequence:** packs load → scene bundles → BeatmapLevelsData → VR init → menu → MoveNext hooks fire

### Crashes: lizzo-only config (same crash as billieeilish, camellia)
- 2 redirects: lizzo pack bundle + catalog.json
- 0 song redirects
- CE-34878-0 crash at boot splash, never reaches "turn on VR headset" screen
- **Log:** `/tmp/opencode/lizzo_fixed_crash_log.txt` (609 lines, ends at OPEN #583)
- **Key log sequence:** packs load (all 36 from game data) → log STOPS at last pack load → crash
- **No scene bundles load, no player data loads, no BeatmapLevelsData, no VR init**

---

## 3. Root Cause Analysis

### What we know for certain

**A. The crash was caused by `build_modes_blob()` using the WRONG pathID for new mode entries.**

`build_modes_blob()` creates new entries for missing modes by cloning Standard's difficulty data. The original code assigned each new entry the target mode's own pathID (e.g., NoArrows = `-8583864861369561029`). But BeatmapLevelsData files only contain BeatmapData assets for modes that were in the ORIGINAL pack blob. When the game tries to load NoArrows gameplay, it looks up the pathID in BeatmapLevelsData → not found → CE-34878-0 crash.

**B. Why therollingstones worked:** ALL 11 songs have Standard-only (1 mode). After patching, all 4 entries use Standard's pathID → game loads Standard data for all modes → works.

**C. Why lizzo/billieeilish/camellia crashed:** Some songs have Standard+OneSaber (2 modes). After patching, OneSaber retains its original pathID, but NoArrows/90° get their OWN pathIDs → BeatmapLevelsData lacks those assets → crash.

**D. Fix applied:** `build_modes_blob()` line 274-279 now uses `std_path_id` (Standard's pathID) for new mode entries instead of `CHAR_PATH_IDS[mode]`. The game shows 4 buttons by array index, not by pathID.

### Additional findings (still relevant but not blocking)

**E. Catalog staleness was ALSO a problem (Exp 196):** PS4 catalog didn't match locally rebuilt bundles. Deployed fresh catalog. This was a separate issue from the pathID bug.

**F. Duplicate difficulty ranks bug (Exp 196):** `build_modes_blob()` padded existing modes by blindly copying from Standard template, creating duplicate ranks. Fixed to scan existing ranks and only copy missing ones. This was also separate from the pathID bug.

---

## 4. What We've Tried (Chronological)

| Exp | Date | What | Result |
|-----|------|------|--------|
| 188 | Aug 14 | First deploy: 4 packs + merged catalog + 43 redirects | Crash at OPEN #74 (stale catalog) |
| 189 | Aug 15 | Fixed catalog dataindex shift bug | Catalog valid locally, never deployed |
| 190 | Aug 15 | Reproducibility audit (360Degree removal) | All 36 packs byte-identical |
| 191 | Aug 16 | Deployed fixed catalog | PS4 still had old catalog (size-only check missed it) |
| 192 | Aug 16 | OneSaber note color fix (red→blue) | Fixed, but pack pipeline needs raw-blob recolor |
| 193 | Aug 18 | Plugin revert to stable v0.8040 | Crash persisted (not plugin-side) |
| 194 | Aug 18 | Isolated to per-song bundle corruption | Repair script created |
| 195 | Aug 22 | Stale pack redirect bug found + fixed | Fixed `_ensure_pack_bundle_redirects()` |
| 195 | Aug 22 | 1-pack (therollingstones only) test | **WORKS** — 4 mode buttons functional |
| 196 | Aug 23 | lizzo-only test (pre-rank-fix) | Crash (same as billieeilish) |
| 196 | Aug 23 | Found duplicate difficulty ranks bug | Fixed in `build_modes_blob()` |
| 196 | Aug 24 | lizzo-only test (post-rank-fix) | **STILL CRASHES** |
| — | Aug 24 | Catalog staleness discovered | PS4 catalog ≠ local catalog (8 bytes differ) |
| 197 | Aug 25 | NoArrows crash root cause: pathID bug in `build_modes_blob()` | **FIX APPLIED** — new entries use Standard's pathID. 561/561 tests pass. |

---

## 5. Key Files

### Plugin
- `beat_saber_deluxe/src/main.cpp` — plugin source (v0.8041, stable baseline `a8a06f0`)
  - L42-43: `g_feature_custom_song_replacements`, `g_feature_song_metadata_modification`
  - L286-293: redirect loop gated behind `g_feature_custom_song_replacements`
  - No `enable_beatmap_mode_mapping` feature flag exists — pack bundle redirects and catalog redirect are NOT gated behind any flag

### Pipeline
- `beat_saber_deluxe/tools/full_custom_song_pipeline.py` — pipeline v0.5324
  - L2268: `_ensure_pack_bundle_redirects()` — stale pack redirect removal (Exp 195)
  - L2415: `_regenerate_merged_catalog()` — always uses FULL pack list from config, NOT `--pack-modes-packs`
  - L2449: `_ensure_pack_mode_bundles()` — builds packs + regenerates catalog

- `beat_saber_deluxe/tools/build_pack_mode_bundles.py` — pack bundle patcher
  - L40-45: `CHAR_PATH_IDS` = {Standard, OneSaber, NoArrows, 90Degree}
  - L127: `walk_blob()` — parses BeatmapLevelSO MonoBehaviour blob
  - L209: `build_modes_blob()` — patches previewDifficultyBeatmapSets (fixed duplicate ranks at L248-271)
  - L291: `rebuild_bundle()` — applies blob patches + fixes object table
  - L397: `update_catalog_entry()` — patches m_Crc/m_BundleSize + shifts dataindexes
  - L487: `validate_catalog_dataindexes()` — validates catalog integrity
  - L514: `find_catalog_entry_js()` — byte-wise type-7 block walk
  - L696: `write_merged_catalog()` — regenerates merged catalog from origin

### Data Files
- `beat_saber_deluxe/beat_saber_song_ids.json` — per-pack song data with `patchPathID`, `packBundle`, `catalogBundleName`
- `beat_saber_deluxe/pack_modes_bundles/` — all 36 rebuilt pack bundles + `manifest.json`
- `beat_saber_deluxe/catalog_pack_modes.json` — merged catalog (local, correct)
- `beat_saber_deluxe/features.json` — `{"enable_custom_song_replacements": true, "enable_song_metadata_modification": true}`
- `ps4_dump/CUSA12878-patch/Media/StreamingAssets/aa/catalog.json` — origin catalog

### Tests
- `beat_saber_deluxe/tests/test_pack_mode_pipeline.py` — 110 tests (fixed paths, fixed feature flag test, added duplicate rank test)
- Full suite: 451 tests pass (as of v0.5324)

### Configs
- `/tmp/lizzoonly_config.json` — lizzo-only deploy config (currently on PS4)
- `/tmp/rollsonly_config.json` — therollingstones-only deploy config (worked)

### Logs
- `/tmp/opencode/bs_log_v08045.txt` — therollingstones WORKING log (9,246 lines, full boot)
- `/tmp/opencode/lizzo_fixed_crash_log.txt` — lizzo CRASH log (609 lines, ends at OPEN #583)
- `/tmp/opencode/v0.5324_2pack_billieeilish_crash.txt` — earlier billieeilish crash
- `/tmp/opencode/v0.5324_billie_only_crash.txt` — billie-only crash
- `.ai_memory/experiment_logs/v0.5319_crash_after_packmodes_deploy.txt` — original Exp 189 crash
- `.ai_memory/experiment_logs/v0.5321_crash_after_redeploy.txt` — Exp 191 crash (stale catalog)

### Analysis Scripts
- `/tmp/opencode/compare_blobs.py` — binary comparison of pack bundles
- `/tmp/opencode/check_ranks.py` — rank analysis (verifies no duplicate ranks)
- `/tmp/opencode/all_packs_analysis.py` — per-pack origin mode analysis

---

## 6. Current PS4 State

FTP: `192.168.100.117:2121`, user: `anonymous`  
AFR root: `/data/GoldHEN/AFR/CUSA12878/`

Currently deployed (lizzo-only config):
- `redirects.json` — 2 redirects: lizzo pack + catalog (468 B, Aug 24)
- `lizzo_pack_modes_assets_all_8bf3db217732cc18af0b9a2a32d13a9a.bundle` — 6,893,745 B (FIXED, Aug 24)
- `catalog_pack_modes.json` — 795,775 B (STALE, Aug 23 — does NOT match rebuilt lizzo bundle)
- 38 custom song bundles (unchanged)
- `features.json`, `song_metadata.json`, plugin `.prx`

**Stale files that should be cleaned:**
- `therollingstones_pack_modes_assets_all_*.bundle` (deleted this session)
- `billieeilish_pack_modes_assets_all_*.bundle` (deleted this session)

---

## 7. Next Steps to Try

### Immediate: User Boot/Gameplay Test (stage 1 — DONE deploying, Exp 198)
Stage-1 surgical deploy complete (2026-08-25): v0.5325 lizzo bundle (md5 `4c66ad8b…`, 6,893,622 B) + lizzo-only merged catalog (md5 `bb663cd3…`) swapped onto the existing 2-entry absolute-path isolation config; redirects.json untouched; bs_log.txt cleared. Both files MD5-verified on device by re-download.

**User test:** launch Beat Saber → pick a lizzo song → **No Arrows** → play. Then spot-check 90° + OneSaber. Pull + archive `bs_log.txt` after.

### If stage 1 passes: Stage 2 full restore (Exp 199)
Regenerate everything consistently from the DEFAULT config (all 4 packs) and restore the full experience:
```bash
cd /workspace/beat_saber_deluxe
python3 tools/full_custom_song_pipeline.py --deploy-pack-modes --deploy-config --verify-ps4
```
This redeploys today's rebuilt therollingstones/billieeilish/lizzo/camellia bundles + 4-pack merged catalog + regenerated redirects.json (38 songs + 4 pack pairs + catalog pair). User spot-tests across packs.

### If stage 1 still crashes: Isolate further
- Pull `bs_log.txt` and archive it to `.ai_memory/experiment_logs/`
- Test with a pack that has ONLY Standard songs (extras/greenday/monstercat) to confirm the fix works for all-Standard packs
- Check if the game validates pathIDs in BeatmapLevelsData differently than expected

---

## 8. Key Constants

```python
CHAR_PATH_IDS = {
    "Standard": -7286399427822119286,
    "OneSaber": -5623662769225589684,
    "NoArrows": -8583864861369561029,
    "90Degree": -5995858427784384822,
}
TARGET_MODES = ["Standard", "OneSaber", "NoArrows", "90Degree"]
TARGET_DIFFS = 5
DIFF_BYTES = 36
```

---

## 9. Experiment Log Reference

The active experiment log is at `.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md` (Exp 188-195). Prior features archived in:
- `experiment_log_archive/experiment_log_exp001-159_prior-features_2026-06-08_to_2026-07-31.md`
- `experiment_log_archive/experiment_log_beatmap-mode-mapping_exp160-183_2026-07-28_to_2026-08-11.md`
- `experiment_log_archive/experiment_log_chromeo-source-recovery-mass-redeploy_exp184-187_2026-08-12_to_2026-08-13.md`

---

## 10. Questions for Investigation

1. **Is the catalog staleness the actual root cause?** Deploy the fresh local catalog and test. If it works, the8-byte CRC/size mismatch was enough to crash the game.

2. **If catalog isn't the issue, what does the game do between pack loading and scene loading?** The crash happens in that gap. The game must be processing the catalog entries or validating pack bundle contents. What validation does it do?

3. **Why does therollingstones work with the same stale catalog pattern?** Both tests use a catalog patched for all 36 packs but only redirect1 pack. The other 35 have mismatched CRCs. Does the game skip CRC validation for non-redirected packs?

4. **Is there a pack-level validation that fails for bundles with mixed-mode songs?** therollingstones has all-Standard songs → 1 set per song. lizzo/billieeilish have some Standard+OneSaber songs → 2 sets per song in the original, 4 sets after patching. Could the game reject packs where some songs had non-Standard modes originally?

5. **Could the issue be the `_regenerate_merged_catalog` always patching ALL 36 packs?** Even when only1 pack is redirected, the catalog has updated CRCs for all 36. Maybe the game loads the original pack bundles and checks their CRC against the catalog, finding mismatches for the 35 non-redirected packs.
