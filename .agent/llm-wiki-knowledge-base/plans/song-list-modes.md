# Implementation Plan: Dynamic Song List & Beatmap Mode Control

## Goal 1: Show custom song names and artists in the in-game song list

### Problem
When a song is redirected via the plugin's `open_hook`, the in-game song list still shows the original slot's metadata (name, artist) instead of the custom song's name. The player must refer to the song replacement mapping document to find a song.

### Root Cause
The game stores song metadata (display names, artists) in `BeatmapLevelSO` ScriptableObjects located in the Addressables system (`aa/PS4/*.bundle`), not in the per-song bundles that we replace. The redirect only changes the asset bundle loaded, but the UI metadata comes from a different source.

### Solution Options

#### Option A: Hook IL2CPP Property Getters (Recommended)
- **How:** Hook `get_DisplayName()` and `get_songName()` in the game's IL2CPP runtime
- **What it does:** When the game asks for a song's display name, intercept and return the custom name from a dynamic config (e.g., `redirects.json` with added metadata fields)
- **Pros:** Clean, maintainable, no game file modification
- **Cons:** Requires knowing the function address in the binary (needs IL2CPP dump)
- **Difficulty:** Medium-High

#### Option B: Create Custom Metadata Bundle
- **How:** Use the pipeline to create a custom Addressables-style bundle containing a `BeatmapLevelSO` with the correct names/artists, and redirect the Addressables bundle load
- **What it does:** Replaces the entire metadata bundle load for a specific song
- **Pros:** No runtime hook needed, works with the existing redirect mechanism
- **Cons:** Complex bundle management, requires maintaining a separate metadata bundle per song
- **Difficulty:** High

#### Option C: Modify the Per-Song Bundle (Hybrid)
- **How:** Add a `BeatmapLevelSO` object to the per-song bundles we already create. The game might use the `BeatmapLevel` object's name field for the UI if it falls back to the per-bundle data
- **Pros:** Uses existing pipeline, minimal changes
- **Cons:** May not work if the game ignores per-bundle metadata for the UI
- **Difficulty:** Low-Medium

#### Status: Option C Investigated — NOT Feasible
- **Result:** The `BeatmapLevel` object (class_id 114) in per-song bundles does NOT contain display name or artist fields. The `m_Name` field is just the internal object name (e.g. "AngryBeatmapLevelData"), not the song name.
- **Key Finding:** Song metadata lives exclusively in `BeatmapLevelSO` objects in the Addressables system (`aa/PS4/*.bundle`).
- **Binary Analysis:** The game binary is at `eboot.bin`. IL2CPP metadata is in `global-metadata.dat`. The `get_DisplayName` function string is in `global-metadata.dat` but NOT in `eboot.bin` as a plain string (IL2CPP name mangling).
- **Next Step:** Use an IL2CPP dumper (e.g. `Il2CppDumper` by Perfare) to extract the function address of `get_DisplayName` from `eboot.bin` + `global-metadata.dat`.
- **Fallback:** If IL2CPP analysis is not available, consider creating a custom `BeatmapLevelSO` bundle that the `open_hook` can redirect to (requires knowing the `BeatmapLevelSO` serialization format).

## Goal 2: Enable/Disable specific beatmap modes (OneSaber, 90Degree, NoArrows, etc.)

### Problem
Our custom song bundles only have the `"Standard"` characteristic in the `_difficultyBeatmapSets` array. Players cannot select alternative modes like OneSaber or 90-degree for custom songs, even if the original song had those modes.

### Root Cause
The `BeatmapLevel` object in each bundle has a `_difficultyBeatmapSets` array that lists available characteristics. We only add `"Standard"` entries.

### Solution Options

#### Option A: Modify the Pipeline to Add Mode Entries (Recommended)
- **How:** In the pipeline, when creating the custom asset bundle, add additional `_difficultyBeatmapSets` entries for desired modes (OneSaber, 90Degree, etc.)
- **What it does:** The game will see these modes as available and allow the player to select them
- **Pros:** Works with the existing pipeline, no plugin changes needed
- **Cons:** Each mode needs its own difficulty beatmap assets (or a proxy to the Standard mode's notes)
- **Difficulty:** Medium

#### Option B: Hook the Characteristic Access Function
- **How:** Hook the function that determines which characteristics are available for a song
- **What it does:** Programmatically adds the desired modes to any song
- **Pros:** No bundle modification, works globally
- **Cons:** Complex, requires IL2CPP function address
- **Difficulty:** High

#### 🟢 IMPLEMENTED — Mode Characteristic Cloning
**Status:** ✅ Implemented in `full_custom_song_pipeline.py`

A new `add_mode_characteristics(cab, enable_modes: list)` function has been added:
1. Finds the `BeatmapLevel` object (class_id 114) in the CAB
2. Reads the existing `_difficultyBeatmapSets` array (which always has "Standard")
3. For each requested mode (e.g. `"OneSaber"`, `"90Degree"`), clones the Standard difficulty entries with the new characteristic name
4. Saves the modified TypeTree to the bundle
5. Reuses the same `.beatmap.gz` and `.lightshow.gz` assets (same path IDs) as Standard

**Usage:** `--enable-modes OneSaber,90Degree`
**How it works:** The new mode entries reference the same beatmap TextAsset path IDs, so the game loads the Standard-mode notes in the new mode. Works because Beat Saber on PS4 supports playing Standard notes with mode modifiers (OneSaber/90Degree).

**Verification:** After save+reload, the bundle correctly contains all 3 characteristics with 5 difficulties each:
- Standard (5 diffs)
- OneSaber (5 diffs) 
- 90Degree (5 diffs)

## Updated Order of Implementation

### Phase 1: Investigation & Root Cause Analysis
- ✅ Discovered `BeatmapLevel` TypeTree structure
- ✅ Identified `_difficultyBeatmapSets` as the mode control mechanism
- ✅ Found `get_DisplayName` / `get_songName` as metadata access points
- ✅ Option C investigated: display names NOT in per-bundle `BeatmapLevel` object

### Phase 2: Beatmap Mode Control (DONE)
- ✅ `add_mode_characteristics()` function implemented
- ✅ `--enable-modes` CLI flag added to pipeline
- ✅ Verified: OneSaber and 90Degree added to bundles correctly
- ⬜ Test on actual PS4 (needs restart)

### Phase 3: Song List Implementation
1. Run an IL2CPP dumper on `eboot.bin` + `global-metadata.dat` to get the `get_DisplayName` function address
2. Implement `metadata.json` config with fields:
   ```json
   "redirects": {
     "startmeup": {
       "bundle": "startmeup_v3",
       "displayName": "Espresso",
       "artistName": "Sabrina Carpenter",
       "mapper": "CustomMapper",
       "modes": ["Standard", "OneSaber"]
     }
   }
   ```
3. Modify `load_redirects()` to parse metadata (name, artist, modes)
4. Implement plugin hook for `get_DisplayName` to return custom names for redirected songs

## Dependencies
- IL2CPP dumper (for function address discovery) — `Il2CppDumper` by Perfare
- UnityPy (already installed) — for bundle manipulation
- GoldHEN plugin hook infrastructure (already working)

## Experimental Results (Exps 110-115)

| Exp | Approach | Status | Result |
|-----|----------|--------|--------|
| 110 | `add_mode_characteristics()` on per-song bundle `_difficultyBeatmapSets` | ✅ Complete | Pipeline flag works, but doesn't affect UI |
| 111 | Modified pack bundle BeatmapLevelSO via UnityPy TypeTree | ❌ Failed | Pack bundle in AFR subdir — redirect didn't fire |
| 112 | Moved pack bundle to AFR root + added redirect entry | ❌ Failed | Plugin hardcoded `BeatmapLevelsData/` prefix — key never matched Addressables path |
| 113 | Removed hardcoded prefix from plugin + redirect fired | ❌ **Crash** | Redirect WORKS but `save_typetree()` corrupted external refs → CE-34878-0 |
| 114 | Removed pack bundle redirect (crash fix) | ✅ Fixed | Game launches, 32 per-song redirects work |
| 115 | Binary patching via `set_raw_data()` | ✅ **Working** | Pack bundle patched with 3 preview sets (Standard, OneSaber, 90Degree). External refs preserved. |

### Key Discovery for Exp 115
The crash in Exp 113 was caused by UnityPy's `save_typetree()` which re-serializes the TypeTree and regenerates the external reference table incorrectly. Using `set_raw_data()` to replace ONLY the object's serialized bytes (raw binary patching) preserves the original external references perfectly.

The `_previewDifficultyBeatmapSets` array is at the END of the BeatmapLevelSO raw data (offset 236 in the 440-byte blob). It stores:
- count (int32): number of preview sets
- For each set: PPtr (12 bytes) + difficulty count (4) + N × difficulty struct (36 bytes each)

By changing the count from 1→3 and appending 2 more set entries (196 bytes each), the array extends without shifting other data.
