# Plugin Changelog — Beat Saber Deluxe

All notable changes to the GoldHEN plugin (`beat_saber_deluxe.prx`) are documented here.

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
