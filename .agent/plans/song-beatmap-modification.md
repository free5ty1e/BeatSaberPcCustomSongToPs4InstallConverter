# Plan: Beatmap Mode Mapping (`enable_beatmap_mode_mapping`)

## Feature Summary

Auto-detect custom song beatmap modes and map them to the game's characteristic slots with configurable fallback logic. Gated behind feature flag `enable_beatmap_mode_mapping` (plugin: `g_feature_beatmap_mode_mapping`).

**Supported modes (4):** `Standard`, `OneSaber`, `NoArrows`, `90Degree`.

**`360Degree` is REMOVED entirely** — the PS4 camera is a single sensor with ~90° tracking arc, so 360° gameplay is physically impossible. No 360Degree references may remain anywhere in pipeline or plugin. This removal is **not** a new feature and does **not** get a new flag — it is part of this same feature, and the same `enable_beatmap_mode_mapping` flag gates it.

---

## Current Status (2026-08-04)

### Done & Verified (Phase 1 core, green before 360Degree removal)
- `detect_song_modes()` — filename parsing (suffix/prefix/bare/`.beatmap`), aliases (`SingleSaber`→`OneSaber`, `Lawless`→`NoArrows`, `Legacy`→`Standard`)
- `build_mode_mapping()` — resolves which of the 4 game slots can be enabled from detected files + fallback chain; `--fallback-mode-map SRC=DEST` overrides
- `apply_mode_mapping()` / `add_mode_characteristics()` — clones Standard beatmap assets into per-song bundle `_difficultyBeatmapSets`
- `--enable-beatmap-mode-mapping`, `--fallback-mode-map`, `--enable-modes` CLI flags wired into main
- `enable_beatmap_mode_mapping: True` in `DEFAULT_FEATURES` + plugin `features.json` flag `g_feature_beatmap_mode_mapping`
- Plugin source v0.8049 gated by the same flag

### Done but UNVERIFIED (360Degree purge, edits made, tests NOT run since)
All edits below remove 360Degree (4-mode world). **No pytest has run since these edits** — first task is to verify them.
- `full_custom_song_pipeline.py`: `GAME_CHARACTERISTIC_MODES` = 4 modes; `KNOWN_MODE_SUFFIXES` has no 360Degree; `_select_beatmap_file` tier5 removed, 360Degree files `continue`-excluded; `default_fallback` = `{NoArrows→Standard, 90Degree→Standard, OneSaber→Standard}`; `_CHAR_PATH_IDS` 4 entries; blob count 4; `--enable-modes` filters out 360Degree; CLI help updated
- `tools/inject_pack_bundle.py`, `build_patched_pack_bundle.py` (blob 1257→1061B), `patch_pack_bundle.py` (`new_array_length = 1 + len(CHARS)` = 4), `build_per_song_metadata.py`, `build_replacement_pack.py`/`v2`/`v3`/`v4`/`final` — all 4-mode
- Tests updated to 4-mode expectations: `test_pipeline.py`, `test_integration.py`, `test_inject_pack_bundle.py`, `test_patched_pack_bundle.py`

### Not yet done
- `src/main.cpp` still has 360Degree refs: comment line ~376, `names[4]` array at line ~706 (`{"OneSaber","NoArrows","90Degree","360Degree"}`)
- No pytest run after the purge edits
- No plugin rebuild / PS4 deploy of the 4-mode world

### DEAD ENDS (do not revisit)
- **Phase 2 runtime RAM patch of `BeatmapLevelSO._previewDifficultyBeatmapSets`** (v0.8045–v0.8049): BeatmapLevelSO managed objects not present during song-list render; 64GB scan freezes; confirmed dead end 2026-08-03. Pipeline-only mode mapping is the chosen path.

---

## Part 1: Pipeline — Per-Song Bundle Mode Mapping

### 1.1 Auto-Detection: `detect_song_modes(song_dir)`

Scan `song_dir` for `.dat`/`.json` files and categorize them by mode and difficulty.

**Input:** `song_dir` path  
**Output:** `dict[str, dict[str, str]]` — `{mode: {difficulty: filename}}`

**Real-world example** (from BeatSaver songs in the repo — official songs don't have external .dat files):

```python
# BeatSaver song with OneSaber + Standard (partial coverage, prefix-style naming)
# e.g. songs_repo/5f3b03223b3cf960802005f0910175f1802bd8b2/
{
    "Standard": {
        "Easy":   "EasyStandard.dat",
        "Normal": "NormalStandard.dat",
        "Hard":   "HardStandard.dat",
        "Expert": "ExpertStandard.dat",
        "ExpertPlus": "ExpertPlusStandard.dat"
    },
    "OneSaber": {
        "Easy":   "EasyOneSaber.dat",
        "Normal": "NormalOneSaber.dat",
        "Hard":   "HardOneSaber.dat",
        "Expert": "OneSaberExpert.dat",  # prefix-style: mode before difficulty
    }
}
```

```python
# BeatSaver song with no mode suffix (bare .dat files)
# e.g. songs_repo/050d447ebe73685cdb5515867dd7f065e0001fb7/
{
    "Standard": {
        "Easy":   "Easy.dat",
        "Normal": "Normal.dat",
        "Hard":   "Hard.dat",
        "Expert": "Expert.dat",
        "ExpertPlus": "ExpertPlus.dat"
    }
}
```

**Filename parsing logic:**
- Strip known mode suffix from stem: `ExpertPlusOneSaber` → difficulty=`ExpertPlus`, mode=`OneSaber`
- Check for prefix-style (mode before difficulty): `OneSaberExpert.dat` → mode=`OneSaber`, difficulty=`Expert`
- Known mode suffixes/prefixes: `Standard`, `OneSaber`, `NoArrows`, `90Degree`, `Legacy`, `Lawless`, `SingleSaber`
- **`360Degree` files are hard-excluded** (unsupported on PS4 camera tracking) — see `_select_beatmap_file`
- Bare `.dat` (no mode token) → `Standard`
- `.beatmap.dat` → `Standard` (alternate format)
- Exclude: `Info.dat`, `BPMInfo.dat`, files containing `Lightshow` or `AudioData`

**Mode canonicalization (aliases):**
- `SingleSaber` → `OneSaber`
- `Legacy` → `Standard`
- `Lawless` → `NoArrows`

### 1.2 Fallback Mapping: `build_mode_mapping(available, fallback_overrides=None)`

Build a mapping from game slots to source beatmap files, filling gaps with fallback.

**Default fallback chains (applied per-difficulty):**
```
OneSaber  → [Standard]
90Degree  → [Standard]
NoArrows  → [Standard]   (360Degree removed from the chain — mode no longer exists)
Standard  → []  (no fallback, always required)
```

**CLI overrides:** `--fallback-mode-map SOURCE=DEST`
- Example: `--fallback-mode-map NoArrows=Standard` — override NoArrows fallback
- Multiple: `--fallback-mode-map NoArrows=Standard --fallback-mode-map 90Degree=Standard`
- Overrides DEFAULT_FALLBACK_CHAIN for that slot

**Input:** `available` (from detect_song_modes), `fallback_overrides` (list of "SRC=DEST" strings)  
**Output:** `dict[str, dict[str, str]]` — `{slot: {difficulty: source_file}}` with every difficulty filled

**Fallback algorithm per slot:**
```
for each game slot [Standard, OneSaber, NoArrows, 90Degree]:
    for each difficulty [Easy, Normal, Hard, Expert, ExpertPlus]:
        if slot has beatmap for this difficulty:
            use it
        else:
            for fallback_slot in fallback_chain[slot]:
                if fallback_slot has beatmap for this difficulty:
                    use it from fallback_slot
                    log "MAPPING: {slot}/{difficulty} ← {fallback_slot}/{difficulty}"
                    break
            if no fallback found:
                log "WARNING: {slot}/{difficulty}: no fallback available, cloning from Standard"
                clone from Standard/{difficulty}
```

### 1.3 Application: `apply_mode_mapping(cab, mode_mapping)`

Add `_difficultyBeatmapSets` entries to the per-song bundle's BeatmapLevel (class_id 114) based on the mode mapping.

**Logic:**
1. Read existing `_difficultyBeatmapSets` from the bundle
2. For each slot in mode_mapping:
   - If slot already exists in `_difficultyBeatmapSets`, update entries
   - If slot doesn't exist, create new entry with mode's difficulty beatmaps
3. Each difficulty entry in a slot references the corresponding `.beatmap.gz` and `.lightshow.gz` from the bundle
4. The referenced assets already exist (from the song's own beatmap files); the mode just shares the same asset references

**Relationship to existing `add_mode_characteristics()`:**  
`apply_mode_mapping()` replaces `add_mode_characteristics()` when `--enable-beatmap-mode-mapping` is active. The existing function clones Standard → all modes; the new one uses custom beatmaps per slot with fallback.

### 1.4 Backward Compatibility: `--enable-modes` Flag

`--enable-modes` continues to work as before (clones Standard). When both flags are specified:
- `--enable-modes` modes are merged with auto-detected modes
- Manual modes take precedence (if conflicting, manual wins)

### 1.5 CLI Interface

```
--enable-beatmap-mode-mapping    Auto-detect modes and build mapping
--fallback-mode-map SRC=DEST     Override default fallback chain (repeatable)
                                 Example: --fallback-mode-map NoArrows=Standard
```

### 1.6 Feature Flag Integration

Add `enable_beatmap_mode_mapping` to:
- `DEFAULT_FEATURES` in pipeline (default: `true` — safe default when enabled)
- Plugin `features.json` parsing (gating for future plugin-side usage)
- Pipeline's `apply_feature_flags()` 

### 1.7 Logging

The pipeline logs all mapping decisions:
```
[MODE_MAP] Detected modes: Standard(5/5), OneSaber(3/5), NoArrows(0/5)
[MODE_MAP] OneSaber/Normal ← Standard/Normal (fallback)
[MODE_MAP] OneSaber/Hard ← Standard/Hard (fallback)
[MODE_MAP] NoArrows/ExpertPlus ← Standard/ExpertPlus (fallback)
[MODE_MAP] Applied: Standard(done), OneSaber(done), NoArrows(cloned), 90Degree(cloned)
```

---

## Part 2: Plugin — Per-Song Bundle Runtime Mode Injection ⛔ DEAD END

> **Archived for reference only. Do not revisit.** See Phase 2 Conclusion below.

Phase 2 runtime RAM patching (v0.8045–v0.8049) conclusively failed due to timing barriers and performance freezes. The plugin-side machinery (`mode_find_characteristic_sos`, `mode_try_patch_*`, `mode_patch_all`) remains in `main.cpp` gated behind `g_feature_beatmap_mode_mapping` **for reference only** — only its 360Degree references get cleaned out as part of the current purge. Pipeline-only mode mapping (Part 1) is the chosen path.

---

## Part 3: UI Mode Selector — Pack Bundle Preview Data ⛔ BLOCKED

**Blocked by catalog CRC validation (Exp 136):** `m_UseCrcForCachedBundles: true` causes any modified pack bundle to fail CRC check → CE-34878-0 crash. Catalog is plain JSON (not AssetBundle) so AFR cannot redirect it. Not actively pursued — mode selection happens via pipeline-injected `_difficultyBeatmapSets` (Part 1). Revisit only if a CRC bypass is discovered.

---

## Phase 2 Conclusion: DEAD END (Confirmed 2026-08-03)
- **Attempt:** Runtime heap scanning and patching of Addressables pack bundle `BeatmapLevelSO._previewDifficultyBeatmapSets` (v0.8045–v0.8049).
- **Behavior & Findings:** 
  1. **Timing Barrier:** Addressables pack bundles unhide/deserialize asynchronously; BeatmapLevelSO managed heap objects are simply *not present* in GC memory during song-list rendering (`MoveNext` song-list cell populate).
  2. **Performance Freeze:** Searching 64GB of address space causes severe multi-minute stalls/freezes upon entering Solo mode.
  3. **Hardware Constraint:** Non-standard modes like 360Degree are physically impossible on PS4 due to single-camera 90-degree tracking constraints.
- **Resolution:** Phase 2 runtime RAM patching is officially abandoned as a dead end. Mode mapping is fully handled via **Phase 1 (Pipeline bundle patching)** — injecting `_difficultyBeatmapSets` directly into per-song bundles. The plugin-side machinery (Phase 2 scan code, `mode_find_characteristic_sos`, `mode_try_patch_*`) remains in `main.cpp` **gated behind `g_feature_beatmap_mode_mapping`** for reference; only its 360Degree references get cleaned out.

---

## Implementation Order

### Phase 1 — Pipeline (COMPLETE, verify 360Degree purge)
1. ✅ `detect_song_modes()` — auto-detect mode/difficulty from filenames
2. ✅ `build_mode_mapping()` with fallback logic (4 modes)
3. ✅ `apply_mode_mapping()` / `add_mode_characteristics()` modify per-song bundle
4. ✅ CLI flags: `--enable-beatmap-mode-mapping`, `--fallback-mode-map`
5. ✅ `enable_beatmap_mode_mapping` in `DEFAULT_FEATURES`
6. ✅ Plugin feature flag `g_feature_beatmap_mode_mapping` (same flag, gates Phase 2 leftovers)
7. ⏳ Tests for 4-mode world — **edits done, NOT yet run** (must run before any further work)
8. ✅ Documentation updates

### Next Steps — 360Degree Purge Completion (in progress)
**Step 1 — Verify pipeline edits with tests** (before any plugin work):
```bash
cd /workspace/beat_saber_deluxe
python3 -m pytest tests/test_pipeline.py -v          # 110 tests
python3 -m pytest tests/test_inject_pack_bundle.py -v
python3 -m pytest tests/test_patched_pack_bundle.py -v
python3 -m pytest tests/test_integration.py -v
```
Full suite (361 tests) exceeds 120s shell timeout — always run per-file. Fix any breakage from the purge (likely test expectations referencing 360Degree or 5-mode counts).

**Step 2 — Clean `src/main.cpp` (plugin still v0.8049, unbuilt):**
- Line ~376 comment: drop "360Degree" from the Phase 2 scan section comment
- Line ~706: `const char* names[4] = {"OneSaber","NoArrows","90Degree","360Degree"};` → remove `"360Degree"` entry (becomes `names[3]`, adjust any `i < 4` loop bounds)
- Keep the dead-end scan machinery itself intact (gated) — only remove the 360Degree references
- **Do NOT change the feature flag** — still `g_feature_beatmap_mode_mapping`
- Rebuild `beat_saber_deluxe.prx` (plugin size should shrink slightly from the removed array entry)

**Step 3 — Version bumps + changelogs:**
- Pipeline `VERSION`: 0.53xx → +0.0001; `CHANGELOG-PIPELINE.md`: "Removed 360Degree (unsupported on PS4)"
- Plugin: `PLUGIN_VERSION` v0.8049 → v0.8050; `CHANGELOG-PLUGIN.md`: "Removed 360Degree from mode names table"

**Step 4 — Deploy & verify on PS4:**
- Deploy pipeline build of a test song (e.g. `startmeup`) with `--enable-beatmap-mode-mapping`
- Deploy rebuilt plugin PRX
- Verify: 4 modes selectable in-game (Standard, OneSaber, NoArrows, 90Degree), 360Degree absent everywhere, no CE-34878-0 crash
- Pull PS4 log → `.ai_memory/experiment_logs/`, clear log after

### Phase 1.5 — Mode Generators (future, feeds this feature)
M5 generators produce dedicated `.dat` files per mode instead of cloning Standard:
1. `--generate-no-arrows` (dot notes from Standard; simplest)
2. `--generate-one-saber` (conflict-detection: remove notes <1 beat apart on different columns)
3. `--generate-90-degree` (rotation events every N measures)
These run as pipeline steps AFTER Standard beatmaps, BEFORE mode mapping — they make the mapped modes play actual mode-specific content. No new flags; not new features; still gated by the same pipeline flag path.

### Part 3 (UI mode selector) — BLOCKED / ABANDONED
Pack-bundle preview-data patching is blocked by catalog CRC validation (Exp 136). Not actively pursued — mode selection happens via pipeline-injected `_difficultyBeatmapSets` (modes appear selectable per-song). Revisit only if in-game mode selector is later confirmed required and a CRC bypass is found.

## Files to Modify

| File | Change | Status |
|------|--------|--------|
| `beat_saber_deluxe/tools/full_custom_song_pipeline.py` | detect/build/apply mode mapping + 4-mode purge | ✅ edited, unverified |
| `beat_saber_deluxe/src/main.cpp` | `g_feature_beatmap_mode_mapping` flag (done); remove 360Degree refs (~line 376, ~706) | ⏳ pending |
| `beat_saber_deluxe/tests/test_pipeline.py` | 4-mode unit tests | ✅ edited, unverified |
| `beat_saber_deluxe/tests/test_integration.py` | 4-mode integration tests | ✅ edited, unverified |
| `beat_saber_deluxe/tests/test_inject_pack_bundle.py` | 4-mode + no-360Degree assertions | ✅ edited, unverified |
| `beat_saber_deluxe/tests/test_patched_pack_bundle.py` | 4-mode, 1061-byte blob assertions | ✅ edited, unverified |
| `beat_saber_deluxe/tools/inject_pack_bundle.py`, `build_patched_pack_bundle.py`, `patch_pack_bundle.py`, `build_per_song_metadata.py`, `build_replacement_pack*.py` | 4-mode purge | ✅ edited, unverified |
| `beat_saber_deluxe/VERSION` | Bump | ⏳ pending |
| `beat_saber_deluxe/CHANGELOG-PIPELINE.md` | 360Degree removal entry | ⏳ pending |
| `beat_saber_deluxe/CHANGELOG-PLUGIN.md` | 360Degree removal entry | ⏳ pending |
| `.agent/context.yml` | Update versions/status | ⏳ pending |
| `.agent/project_summary.md` | Update | ⏳ pending (Exp 174 staged) |
| `.ai_memory/.../experiment_log.md` | Exp 175+: verify purge, plugin cleanup, deploy results | ⏳ pending |
| `.agent/llm-wiki-knowledge-base/feature-flags.md` | Confirm single flag `enable_beatmap_mode_mapping` | ⏳ pending |

---

## Test Plan

### Unit Tests (4-mode)

```python
# detect_song_modes
test_detect_bare_standard:  Hard.dat → Standard/Hard
test_detect_standard_suffix:  ExpertPlusStandard.dat → Standard/ExpertPlus
test_detect_one_saber:  ExpertPlusOneSaber.dat → OneSaber/ExpertPlus
test_detect_90_plus_noarrows:  Expert90Degree.dat, ExpertNoArrows.dat → both detected
test_detect_aliases:  ExpertPlusSingleSaber.dat → OneSaber/ExpertPlus
test_detect_excludes:  Info.dat, BPMInfo.dat, Lightshow files → excluded
test_detect_empty_dir: empty directory → empty dict
test_detect_mixed_modes: mix of modes → complete dict

# build_mode_mapping (4-game-slot world)
test_basic_mapping: Standard only → OneSaber/NoArrows/90Degree all fallback to Standard
test_one_saber_partial: Standard + OneSaber/ExpertPlus → OneSaber mapped, rest fallback
test_noarrows_fallback: NoArrows missing, Standard available → NoArrows ← Standard
test_fallback_override: --fallback-mode-map NoArrows=Standard → override applied
test_all_4_modes_available: Standard + OneSaber + NoArrows + 90Degree detected → no fallback
test_360degree_never_enabled: 360Degree detected → still excluded, never mapped

# apply_mode_mapping
test_adds_sets: apply_mode_mapping → _difficultyBeatmapSets has 4 entries
test_preserves_existing: existing Standard set preserved, new modes appended
test_no_standard: error handling if Standard missing
```

### 360Degree Purge Regression Tests
```python
test_detect_360degree_always_excluded: _select_beatmap_file skips "360Degree" files
test_enable_modes_360degree_filtered: --enable-modes 360Degree → removed with log message
test_build_mode_mapping_no_360fallback: build_mode_mapping default_fallback has no 360Degree key
test_blob_4_modes: _build_beatmap_level_so_blob produces count=4, 4×36B entries
```

### Integration Test (4-mode)
- Create song directory with 5 standard .dat files + ExpertPlusOneSaber.dat + Expert90Degree.dat
- Run pipeline with `--enable-beatmap-mode-mapping`
- Verify output bundle has 4 `_difficultyBeatmapSets` entries (Standard, OneSaber, NoArrows→Standard, 90Degree→Standard)
- Verify existing Standard entry unchanged
- Verify OneSaber has 1 difficulty (ExpertPlus) filled, rest cloned from Standard
- Verify `'360Degree' not in modes` and `'360Degree' not in mapping`
