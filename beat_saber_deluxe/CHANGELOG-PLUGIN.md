# Plugin Changelog — Beat Saber Deluxe

All notable changes to the GoldHEN plugin (`beat_saber_deluxe.prx`) are documented here.

## [v0.65] — 2026-07-14
### Added
- **Mode selector — 5 preview difficulty modes** — StartMeUp BeatmapLevelSO in pack bundle patched with 5-mode preview data (Standard, OneSaber, NoArrows, 90Degree, 360Degree). Each mode references the correct BeatmapCharacteristicSO via PPtr (fileID=3).

### Fixed
- **m_Script PPtr bug in blob builder** — `build_beatmap_levelso_blob()` was using `_CHAR_PATH_IDS["Standard"]` for the m_Script pathID instead of the correct script pathID (2140275054477726686). This caused Unity deserialization to fail when loading the pack bundle.

### Changed
- **Bundle patching via UnityPy `save("original")`** — instead of raw bundle building (which had multiple bugs with LZ4 compression, block info format, and alignment), now uses UnityPy's `save()` with `"original"` packer to write the modified bundle in the correct UnityFS format.
- **redirects.json updated** — added pack bundle redirect: `therollingstones_pack_assets_all_a99482a8a3da9e991e5ae36f2fea209c` → `rollingstones_pack_patched.bundle`

## [v0.64] — 2026-07-14
### Removed
- **All IL2CPP hooks** (`get_preview_detour`, `ctor_detour`, `maybe_install_il2cpp_hook`) — constructor hook at RVA 0x9891E0 proved definitively dead: Unity deserializes BeatmapLevelSO objects via raw memory copy from AssetBundles, never calling the IL2CPP constructor. DetourMode_x32 (5-byte JMP) was correct and stable, but the hook target simply never fires.

### Verified
- **Redirect-only system is stable** — v0.64 confirms that with IL2CPP hooks removed, no crash occurs at any point: startup, song select, or gameplay. Start Me Up correctly plays Espresso (Hard difficulty verified).

## [v0.59] — 2026-07-13
### Changed
- Added `__attribute__((ms_abi))` to all IL2CPP hooks (proved to be wrong — reverted in v0.60)

## [v0.63] — 2026-07-14
### Fixed
- **DetourMode_x64 → DetourMode_x32** — The constructor hook at RVA 0x9891E0 crashed with CE-34878-0 because `DetourMode_x64` uses a 14-byte absolute JMP that overwrites into the next instruction (the `mov dword [rdi+0xA0], 1` instruction at byte 6 is 10 bytes; bytes 6-13 are truncated). Changed to `DetourMode_x32` (5-byte near JMP E9 xx xx xx xx) which only overwrites bytes 0-4 — all complete instructions.

## [v0.62] — 2026-07-14
### Added
- **BeatmapLevelSO constructor hook** at RVA 0x9891E0 — captures `this` pointers when BeatmapLevelSO objects are deserialized from the pack bundle.
- **Deferred preview array augmentation** — after the rolling stones pack bundle opens, waits 3 file-opens then augments `_previewDifficultyBeatmapSets` from 1→5 entries via malloc'd copies of the Standard preview set.

### Known Crash
- `DetourMode_x64` overwrote 14 bytes, truncating the instruction at byte 6 → CE-34878-0. Fixed in v0.63.

### Removed
- **Pack bundle redirect** — caused CE-34878-0 crash (Unity validates bundle hashes)
- **Memory scanning approach** — page-aligned scan would miss BeatmapLevelSO objects

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
