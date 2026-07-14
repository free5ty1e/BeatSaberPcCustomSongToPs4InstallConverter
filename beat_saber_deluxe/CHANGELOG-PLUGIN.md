# Plugin Changelog — Beat Saber Deluxe

All notable changes to the GoldHEN plugin (`beat_saber_deluxe.prx`) are documented here.

## [v0.59] — 2026-07-13
### Fixed
- **IL2CPP calling convention mismatch** — added `__attribute__((ms_abi))` to all IL2CPP hook functions. PS4's Clang supports the MS x64 calling convention attribute, making C functions use RCX/RDX/R8/R9 registers (matching IL2CPP generated code) instead of SysV AMD64 RDI/RSI/... Previously all IL2CPP hooks crashed because the Detour jumped from IL2CPP code (MS x64) to C hook functions (SysV) → arguments read from wrong registers → crash.

### Changed
- **`get_preview_detour`** — rewritten to read `_previewDifficultyBeatmapSets` field at offset 0x98 directly from the `this` pointer, eliminating the need to call the original function (and avoiding the Detour_Stub calling convention issue entirely). Augments 1-element arrays to 3 elements for the mode selector.
- **`set_data_detour`** — now uses `TrampolinePtr` with ms_abi function pointer instead of `Detour_Stub`.
- **`set_content_detour`** — re-added (was removed in v0.58 debug) with proper ms_abi attribute.

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
