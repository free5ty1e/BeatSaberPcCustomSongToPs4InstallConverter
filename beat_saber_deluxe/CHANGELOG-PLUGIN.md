# Plugin Changelog — Beat Saber Deluxe

All notable changes to the GoldHEN plugin (`beat_saber_deluxe.prx`) are documented here.

## [v0.59] — 2026-07-13
### Changed
- Added `__attribute__((ms_abi))` to all IL2CPP hooks (proved to be wrong — reverted in v0.60)

## [v0.61] — 2026-07-14
### Added
- **Pack bundle redirect for Rolling Stones** — The open_hook now redirects the rollingstones pack bundle to a modified version on AFR with augmented BeatmapLevelSO preview data. This adds OneSaber, NoArrows, 90Degree, and 360Degree to the mode selector.
- **`tools/patch_pack_bundle.py`** — Binary patching script that modifies the Rolling Stones pack bundle's `_previewDifficultyBeatmapSets` from 1 to 5 entries. Uses UnityPy's `set_raw_data()` with direct byte manipulation to work around UnityPy's save limitations.

## [v0.60] — 2026-07-14
### Removed
- **All `__attribute__((ms_abi))`** — PS4 IL2CPP uses **SysV AMD64** (same as native C), not MS x64. ms_abi caused hooks to read `this` from the wrong register (RCX instead of RDI) → crash on ANY song selection.
- **`set_data_detour`** hook — never fires (SetData called only with 2+ characteristics).
- **`set_content_detour`** hook — causes startup/song-selection crash at RVA 0x1C3B630.

### Changed
- **`get_preview_detour`** — default C convention (no ms_abi). Reads `_previewDifficultyBeatmapSets` at offset 0x98 directly. The ONLY IL2CPP hook installed. Won't crash if inlined; should work if called.

## [v0.58] — 2026-07-13
### Added
- **SetContent hook** (`StandardLevelDetailView.SetContent()`) — directly augments the mode selector with extra characteristics when a song is selected. Overcomes the previous limitation where SetData was never called (because the game only calls it when there are 2+ modes, which it didn't know about).
- **Notification updated** to read "Beat Saber Deluxe vX.XX\nBy Chris Primeish" with an actual newline.

### Changed
- Version increment rule added to dev docs: ANY change to `main.cpp` requires bumping `PLUGIN_VERSION`.
- Global `il2cpp_module_base` stored for reuse across all IL2CPP hooks.

### Previous (v0.57 — merged as PR #2)
- Dynamic redirect system
- 32-song redirect table loaded from `redirects.json`
- Per-song bundle redirects with full audio/beatmap sync
- Debug logging to `/data/GoldHEN/AFR/CUSA12878/bs_log.txt`
- Two IL2CPP hooks installed (get_preview + SetData) but not yet reaching the mode selector
