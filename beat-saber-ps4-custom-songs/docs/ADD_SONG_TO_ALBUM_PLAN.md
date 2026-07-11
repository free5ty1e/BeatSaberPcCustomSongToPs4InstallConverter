# Adding a New Song to an Existing Album — Plan

## Goal
Add a custom song as a new selectable entry within an existing Beat Saber PS4 album/pack (e.g., add "Custom Song" to the Rolling Stones pack).

## Current State
We can **replace** an existing song (Start Me Up → $100 Bills) by:
1. Redirecting `BeatmapLevelsData/startmeup` to a custom AssetBundle
2. Renaming the bundle's assets via UnityPy to match the game's expected names

But the song count in the UI doesn't change — we only swap one song for another.

## What's Needed
Adding a **new entry** requires modifying the game's **song database** — a `BeatmapLevelsModel` ScriptableObject stored in `resources.assets`.

## Approaches (Ranked by Difficulty)

### Approach A: UABEA via Wine (Easiest)
1. Install Wine in devcontainer
2. Download UABEA (Unity Asset Bundle Extractor) — Windows tool
3. Open `resources.assets` with UABEA
4. Navigate to `BeatmapLevelsModel` → `_packs` → Rolling Stones pack → `_beatmapLevels`
5. Add a new entry pointing to our custom song's level ID
6. Save the modified `resources.assets`

**Pros:** Visual UI, handles custom type trees automatically  
**Cons:** Requires Wine setup, manual steps

### Approach B: UnityPy + Type Tree Extraction (Medium)
1. Extract the type tree for `BeatmapLevelsModel` from debug symbols or Unity version info
2. Use UnityPy with exported type trees to decode `resources.assets`
3. Programmatically add a new entry to the Rolling Stones pack
4. Save the modified `resources.assets`

**Pros:** Fully automated, scriptable  
**Cons:** Type trees for Beat Saber custom types are hard to obtain

### Approach C: Binary Patching (Hard)
1. Find the Rolling Stones pack entry in `resources.assets` by binary search
2. Add a new 9-char level ID string to the pack's song list
3. Recalculate affected serialized data offsets

**Pros:** No new tools needed  
**Cons:** Extremely error-prone, likely corrupts the file

## Recommended Path
**Start with Approach A** (UABEA via Wine) — it's the most reliable way to modify the song database. Then document the process for automation later.

## Data Flow for Custom Song
When the database has the new entry:
1. Game reads `resources.assets` → finds new level ID in Rolling Stones pack
2. Game constructs path: `BeatmapLevelsData/<new_level_id>`
3. Plugin's `open()` hook redirects to our custom AssetBundle in AFR directory
4. Unity loads the AssetBundle (must have correct asset names)
5. Game displays and plays the custom song

## File Format Requirements

### Custom AssetBundle (via UnityPy)
- **Container path:** `.../so/<level_id>/<level_id>beatmapleveldata.asset`
- **Asset m_Name:** `<LevelId>BeatmapLevelData` (PascalCase level ID + "BeatmapLevelData")
- **AudioClip:** Replaced with custom song audio
- **Beatmap .gz data:** Replaced with custom difficulty data
- **Cover image:** Replaced with custom cover art
- **Metadata fields:** Updated with custom song info

### Level ID Constraints
- Must be 9 characters (to match existing bundle length constraints)
- No spaces, special chars (only alphanumeric + underscore)
- Must be unique (no collision with existing song IDs)
- Serves as both the filename and the asset name prefix

## Testing Checklist
1. ✅ Custom AssetBundle deployed to AFR directory
2. ✅ Plugin redirect for new level ID added
3. [ ] Song appears in the album UI on PS4
4. [ ] Selecting the song plays the correct audio
5. [ ] Difficulty beatmaps load correctly
6. [ ] Cover art displays correctly
7. [ ] Existing songs in the album are unaffected
8. [ ] Returning to menu works after song finishes/fails
