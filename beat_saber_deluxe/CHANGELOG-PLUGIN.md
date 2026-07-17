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
- **Constructor hook approach** — `__attribute__((constructor))` on plugin_main() confirmed working; GoldHEN loads PRX via module_start which calls constructors before main().

## [v0.63] — 2026-07-14
- See previous changelog entries for full history of plugin development.
