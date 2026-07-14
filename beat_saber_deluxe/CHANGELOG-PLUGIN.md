# Plugin Changelog — Beat Saber Deluxe

All notable changes to the GoldHEN plugin (`beat_saber_deluxe.prx`) are documented here.

## [v0.59] — 2026-07-13
### Changed
- Added `__attribute__((ms_abi))` to all IL2CPP hooks (proved to be wrong — reverted in v0.60)

## [v0.62] — 2026-07-14
### Added
- **BeatmapLevelSO constructor hook** at RVA 0x9891E0 — captures `this` pointers when BeatmapLevelSO objects are deserialized from the pack bundle. Fields aren't populated yet at constructor time, so pointers are saved for deferred augmentation.
- **Deferred preview array augmentation** — after the rolling stones pack bundle opens, waits 3 file-opens then iterates saved BeatmapLevelSO pointers, augments `_previewDifficultyBeatmapSets` from 1→5 entries. Creates 4 copies of the Standard PreviewDifficultyBeatmapSet (all reference the Standard characteristic for now).

### Removed
- **Pack bundle redirect** — caused CE-34878-0 crash (Unity validates bundle hashes; modified bundle size doesn't match)
- **Memory scanning approach** — page-aligned scan would miss BeatmapLevelSO objects not at page boundaries

## [v0.61] — 2026-07-14
### Added
- **Pack bundle redirect for Rolling Stones** — redirected to modified bundle with augmented preview data. Crashed due to bundle hash mismatch.

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
