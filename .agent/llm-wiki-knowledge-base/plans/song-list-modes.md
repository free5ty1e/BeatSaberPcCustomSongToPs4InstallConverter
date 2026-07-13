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

#### Recommended Path: Option A → Investigate Option C first
1. Try Option C first (add `m_Name` or custom fields to the per-song bundle's `BeatmapLevel` object)
2. If the game ignores per-bundle metadata for the song list, proceed with Option A
3. Option A requires:
   - Running an IL2CPP dumper to find the `get_DisplayName` function address
   - Implementing a hook in the plugin
   - Adding a `metadata.json` config for custom names/artists

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

#### Recommended Path: Option A
1. Modify the pipeline to detect existing mode-specific beatmaps or generate them from Standard notes
2. Add the `_difficultyBeatmapSets` entries for the desired modes
3. If no custom beatmaps exist for a mode, reject the mode (rather than proxy) to ensure quality

### Mode Implementation Details
Each `_difficultyBeatmapSet` entry requires:
1. `_beatmapCharacteristicSerializedName` - e.g., `"OneSaber"` or `"90Degree"`
2. `_difficultyBeatmaps` array with `{difficulty, beatmapAsset, lightshowAsset}` per level

The `.beatmap.gz` and `.lightshow.gz` assets for each mode must exist in the bundle. They are separate TextAsset objects referenced by path ID.

## Recommended Order of Implementation

### Phase 1: Investigate & Prototype (this investigation)
- ✅ Discovered `BeatmapLevel` TypeTree structure
- ✅ Identified `_difficultyBeatmapSets` as the mode control mechanism
- ✅ Found `get_DisplayName` / `get_songName` as metadata access points
- ⬜ Verify Option C viability (does per-bundle `m_Name` affect the UI?)

### Phase 2: Song List Implementation
1. Download the game from PS4 to get the main executable (for IL2CPP analysis)
2. Run IL2CPP dumper to get function addresses
3. Implement `metadata.json` config with fields:
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
4. Modify `load_redirects()` to parse metadata
5. Implement `open_hook` for `get_DisplayName` or intercept the metadata bundle load

### Phase 3: Beatmap Mode Implementation
1. Modify the pipeline to accept mode-specific `.dat` files
2. Update the `_difficultyBeatmapSets` array in the bundle
3. Create mode-specific `.beatmap.gz` and `.lightshow.gz` TextAsset objects
4. Verify in-game: the mode selector should appear in the UI

## Dependencies
- IL2CPP dumper (for function address discovery) — `Il2CppDumper` from Perfare
- UnityPy (already installed) — for bundle manipulation
- GoldHEN plugin hook infrastructure (already working)
