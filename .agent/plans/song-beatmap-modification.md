# Plan: Beatmap Mode Mapping (`enable_beatmap_mode_mapping`)

## Feature Summary

Auto-detect custom song beatmap modes and map them to the game's 5 characteristic slots (Standard, OneSaber, NoArrows, 90Degree, 360Degree) with configurable fallback logic. Gated behind feature flag `enable_beatmap_mode_mapping`.

---

## Part 1: Pipeline — Per-Song Bundle Mode Mapping

### 1.1 Auto-Detection: `detect_song_modes(song_dir)`

Scan `song_dir` for `.dat`/`.json` files and categorize them by mode and difficulty.

**Input:** `song_dir` path  
**Output:** `dict[str, dict[str, str]]` — `{mode: {difficulty: filename}}`

**Real-world example** (from BeatSaver songs in the repo — official songs don't have external .dat files):

```python
# BeatSaver song with 360Degree (all 5 diffs) + Standard (all 5 diffs)
# e.g. songs_repo/81970cd2d5d3b2dff908e6569648a9a51e494e65/
{
    "Standard": {
        "Easy":   "EasyStandard.dat",
        "Normal": "NormalStandard.dat",
        "Hard":   "HardStandard.dat",
        "Expert": "ExpertStandard.dat",
        "ExpertPlus": "ExpertPlusStandard.dat"
    },
    "360Degree": {
        "Easy":   "Easy360Degree.dat",
        "Normal": "Normal360Degree.dat",
        "Hard":   "Hard360Degree.dat",
        "Expert": "Expert360Degree.dat",
        "ExpertPlus": "ExpertPlus360Degree.dat"
    }
}
```

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
- Known mode suffixes/prefixes: `Standard`, `OneSaber`, `NoArrows`, `90Degree`, `360Degree`, `Legacy`, `Lawless`, `SingleSaber`
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
NoArrows  → [360Degree, Standard]
360Degree → [NoArrows, Standard]
Standard  → []  (no fallback, always required)
```

**CLI overrides:** `--fallback-mode-map SOURCE=DEST`
- Example: `--fallback-mode-map NoArrows=Standard` — skip 360Degree fallback for NoArrows
- Multiple: `--fallback-mode-map NoArrows=Standard --fallback-mode-map 360Degree=Standard`
- Overrides DEFAULT_FALLBACK_CHAIN for that slot

**Input:** `available` (from detect_song_modes), `fallback_overrides` (list of "SRC=DEST" strings)  
**Output:** `dict[str, dict[str, str]]` — `{slot: {difficulty: source_file}}` with every difficulty filled

**Fallback algorithm per slot:**
```
for each game slot [Standard, OneSaber, NoArrows, 90Degree, 360Degree]:
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
[MODE_MAP] Detected modes: Standard(5/5), OneSaber(3/5), 360Degree(1/5)
[MODE_MAP] OneSaber/Normal ← Standard/Normal (fallback)
[MODE_MAP] OneSaber/Hard ← Standard/Hard (fallback)
[MODE_MAP] NoArrows/ExpertPlus ← 360Degree/ExpertPlus (fallback)
[MODE_MAP] Applied: Standard(done), OneSaber(done), NoArrows(done), 90Degree(cloned), 360Degree(done)
```

---

## Part 2: Plugin — Per-Song Bundle Runtime Mode Injection

### 2.1 Problem

The per-song bundle loaded via AFR redirect has `_difficultyBeatmapSets` containing only "Standard" (original template). The pipeline modifies this to include OneSaber/NoArrows/etc., but there's a timing issue:

- The pipeline creates the bundle with mode entries ✓ (Part 1)
- But some original template bundles may not be re-built by the pipeline (e.g., already-deployed songs)

**Solution:** Plugin hooks `open()` to intercept per-song bundle loads and patches `_difficultyBeatmapSets` in the loaded `BeatmapLevel` in memory.

### 2.2 Plugin Hook Approach

1. In `open_hook()`, detect when a beatmap bundle file is being opened (path contains `BeatmapLevelsData/`)
2. Track the redirect target (custom bundle path)
3. After the game loads the bundle, find the `BeatmapLevel` object in memory
4. Modify its `_difficultyBeatmapSets` to add mode entries

**Challenge:** Finding the `BeatmapLevel` object in memory after AssetBundle load. The offset of `_difficultyBeatmapSets` in `BeatmapLevel` needs to be determined.

**Deferred to Phase 2** — requires IL2CPP dump analysis to find field offsets.

---

## Part 3: UI Mode Selector — Pack Bundle Preview Data

### 3.1 Problem

The in-game mode selector reads from `BeatmapLevelSO._previewDifficultyBeatmapSets`, which is stored in the Addressables pack bundle (e.g., `rollingstones_pack.bundle`). Without modifying this, additional modes won't appear in the song details UI.

### 3.2 Approach: Modified Catalog + Modified Pack Bundle

**Key insight:** The plugin hooks `open()` at the POSIX level, so it CAN intercept the catalog.json load. This means we can:
1. Modify the pack bundle (add preview difficulty beatmap sets)
2. Modify the catalog.json to update CRC + size for the pack bundle
3. Deploy both modified files
4. AFR redirects both files

**Steps:**

**A. Pipeline: `patch_pack_preview_data(pack_bundle_path, slot_id, modes)`**
- Load the pack bundle (UnityFS format)
- Find the `BeatmapLevelSO` for the target song (by `_levelID`)
- Add `_previewDifficultyBeatmapSets` entries for requested modes
- Save the modified bundle
- Compute new CRC and size

**B. Pipeline: `patch_catalog(catalog_json_path, bundle_hash, new_crc, new_size)`**
- Load `catalog.json`
- Find the pack bundle's entry by hash
- Update `m_Crc` and `m_BundleSize` to match modified bundle
- Save modified catalog

**C. Plugin: Add catalog redirect**
- Add `catalog.json` path to redirects table
- Deploy modified catalog + pack bundle to PS4 AFR directory
- Plugin intercepts catalog load and returns modified version

### 3.3 Challenges

| Issue | Status | Workaround |
|-------|--------|------------|
| Pack bundle size changes after modification | ✅ CRC correction solves CRC; size mismatch | Patch catalog to match |
| Catalog.json path unknown | ⚠️ Need to determine | Check PS4 dump or game logs |
| Catalog loaded before plugin hooks | ✅ Module_start runs before game init | Hooks active before Addressables |
| Per-song vs pack-wide changes | ⚠️ Pack bundle affects all songs in pack | Only modify preview for redirected song |

### 3.4 Fallback: Pipeline-Only Mode

If pack bundle patching is too risky, the fallback is:
- Pipeline adds `_difficultyBeatmapSets` to per-song bundle (Part 1)
- Plugin injects mode entries into `BeatmapLevel` at runtime (Part 2, if implemented)
- UI doesn't show mode selector, but modes are selectable via gamepad shortcuts (if any) or next experiment

---

## Implementation Order

### Phase 1 (This Experiment)
1. Add `detect_song_modes()` to pipeline
2. Add `build_mode_mapping()` with fallback logic
3. Add `apply_mode_mapping()` to modify per-song bundle
4. Add CLI flags: `--enable-beatmap-mode-mapping`, `--fallback-mode-map`
5. Add `enable_beatmap_mode_mapping` to `DEFAULT_FEATURES`
6. Add plugin feature flag `g_feature_beatmap_mode_mapping` (gating only)
7. Tests for all new functions
8. Documentation updates
   - `beat_saber_deluxe/README.md` — Add summary of the new featureset (beatmap mode mapping + configurable fallback) in the mode control section, link to detailed feature doc
   - Create `beat_saber_deluxe/docs/features/beatmap-mode-mapping.md` — Detailed explanation: how auto-detection works, fallback chains, CLI flags, examples, relationship to `--enable-modes`, limitations (UI mode selector is separate concern)

## Phase 2 Conclusion: DEAD END (Confirmed 2026-08-03)
- **Attempt:** Runtime heap scanning and patching of Addressables pack bundle `BeatmapLevelSO._previewDifficultyBeatmapSets` (v0.8045–v0.8049).
- **Behavior & Findings:** 
  1. **Timing Barrier:** Addressables pack bundles unhide/deserialize asynchronously; BeatmapLevelSO managed heap objects are simply *not present* in GC memory during song-list rendering (`MoveNext` song-list cell populate).
  2. **Performance Freeze:** Searching 64GB of address space causes severe multi-minute stalls/freezes upon entering Solo mode.
  3. **Hardware Constraint:** Non-standard modes like 360Degree are physically impossible on PS4 due to single-camera 90-degree tracking constraints.
- **Resolution:** Phase 2 runtime RAM patching is officially abandoned as a dead end. Mode mapping is fully handled via **Phase 1 (Pipeline bundle patching)** — injecting `_difficultyBeatmapSets` directly into per-song bundles.

---

## Files to Modify

| File | Change |
|------|--------|
| `beat_saber_deluxe/tools/full_custom_song_pipeline.py` | Add 3 new functions + CLI args + pipeline integration |
| `beat_saber_deluxe/src/main.cpp` | Add `g_feature_beatmap_mode_mapping` flag |
| `beat_saber_deluxe/tests/test_pipeline.py` | Unit tests for detect/build/map functions |
| `beat_saber_deluxe/tests/test_integration.py` | Integration test with mock beatmap files |
| `beat_saber_deluxe/tests/conftest.py` | Add beatmap mode fixtures (OneSaber, 90Degree, NoArrows .dat files) |
| `beat_saber_deluxe/VERSION` | Bump |
| `beat_saber_deluxe/CHANGELOG-PIPELINE.md` | New entry |
| `beat_saber_deluxe/CHANGELOG-PLUGIN.md` | New entry (even if plugin logic is just a flag) |
| `.agent/context.yml` | Update |
| `.agent/project_summary.md` | Update |
| `.agent/llm-wiki-knowledge-base/feature-flags.md` | Add new flag |
| `.agent/llm-wiki-knowledge-base/plans/song-beatmap-modification.md` | This file |

---

## Test Plan

### Unit Tests

```python
# detect_song_modes
test_detect_bare_standard:  Hard.dat → Standard/Hard
test_detect_standard_suffix:  ExpertPlusStandard.dat → Standard/ExpertPlus
test_detect_one_saber:  ExpertPlusOneSaber.dat → OneSaber/ExpertPlus
test_detect_360_plus_noarrows:  Expert360Degree.dat, ExpertNoArrows.dat → both detected
test_detect_aliases:  ExpertPlusSingleSaber.dat → OneSaber/ExpertPlus
test_detect_excludes:  Info.dat, BPMInfo.dat, Lightshow files → excluded
test_detect_empty_dir: empty directory → empty dict
test_detect_mixed_modes: mix of modes → complete dict

# build_mode_mapping
test_basic_mapping: Standard only → all slots fall back to Standard
test_one_saber_partial: Standard + OneSaber/ExpertPlus → OneSaber mapped, rest fallback
test_noarrows_360_fallback: NoArrows missing, 360Degree available → NoArrows ← 360Degree
test_360_noarrows_fallback: 360Degree missing, NoArrows available → 360Degree ← NoArrows
test_fallback_override: --fallback-mode-map NoArrows=Standard → skips 360Degree
test_all_modes_available: All 5 modes have files → no fallback needed

# apply_mode_mapping
test_adds_sets: apply_mode_mapping → _difficultyBeatmapSets has new entries
test_preserves_existing: existing Standard set preserved, new modes appended
test_no_standard: error handling if Standard missing
```

### Integration Test
- Create song directory with 5 standard .dat files + ExpertPlusOneSaber.dat + Expert90Degree.dat
- Run pipeline with `--enable-beatmap-mode-mapping`
- Verify output bundle has 4 `_difficultyBeatmapSets` entries (Standard, OneSaber, 90Degree, NoArrows→Standard, 360Degree→NoArrows)
- Verify existing Standard entry unchanged
- Verify OneSaber has 1 difficulty (ExpertPlus) filled, rest cloned from Standard
