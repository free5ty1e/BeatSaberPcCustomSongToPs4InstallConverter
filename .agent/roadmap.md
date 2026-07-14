# Roadmap

## M0 — Proof of Concept (Complete)
- [x] Custom FSB5 audio (PCM16) injected via AssetBundle redirection
- [x] Full song plays, score saves
- [x] GoldHEN PRX plugin hooks `open()`, logs to AFR

## M1 — Pipeline Automation (Complete)
- [x] `full_custom_song_pipeline.py` with `--pcm16` flag
- [x] BeatSaver downloader
- [x] Beatmap conversion V2→V3 (notes, obstacles, bombs, arcs, chains, 360-degree)
- [x] Lapped audio detection and generation
- [x] 12-song redirect table in plugin (all Rolling Stones slots)
- [x] Beatmap filename fallback — handles all BeatSaver naming conventions (5-tier priority)

## M1.5 — Dynamic Configuration & Pipeline Audit

### Plugin Hardcoded Values → Dynamic
- [x] Make plugin redirect table dynamic — reads `redirects.json` from AFR path, falls back to built-in defaults
- [x] Added `titleId` and `afrBase` to redirect config schema
- [ ] Remove hardcoded `PLUGIN_VERSION` — derive from git tag or redirect config

### Pipeline Hardcoded Values → Config-Driven
- [ ] Remove hardcoded `DIFFICULTIES` list — detect from song directory contents
- [ ] Remove hardcoded `ORIGINAL_RESOURCE_SIZE` — set from config per template bundle
- [ ] Remove hardcoded `SAMPLE_RATE` — detect from audio file metadata
- [ ] Remove hardcoded V2/V3 beatmap matching in `load_bpm_regions` — use beatmap scanning
- [ ] Add `--no-beatmap-bpm` flag (fall back to Info.dat BPM if beatmap scanning causes issues)
- [ ] Make `--song-dir` truly optional when `--deploy-plugin` is used alone ✅ (DONE)

### Pipeline Bug Fixes (Completed)
- [x] `bpmData eb` — was in seconds, not beats (v0.52)
- [x] `bpmEvents` empty — BPM=60 fallback caused 2x speed desync (v0.52)
- [x] V3.0.0 beatmaps with empty bpmEvents — converter only handled V2 (v0.52c)
- [x] Note color `c` field — PS4 game uses `c` not `a` (v0.53)
- [x] BPMInfo.dat eb too small — beatmap scan now cross-checks BPMInfo.dat (v0.52c)

## M2 — Song Metadata & Database (In Progress)
- [x] `beat_saber_song_ids.json` — 306 official songs cataloged
- [x] Song name/artist/mapper extraction from `resources.assets` (22 base songs)
- [x] Song testing log document (`song_testing_log.md`)
- [ ] Difficulty metadata extraction from all 306 bundles
- [x] DLC song name extraction from addressables packs — BeatmapLevelSO objects found in `aa/PS4/therollingstones_pack_assets_all_*.bundle` (Exp 111)
- [ ] DLC song `BeatmapCharacteristicSO` references — need to locate OneSaber/90Degree PIDs in external CAB `CAB-cb38b3e2985c65d4cf8a63437da74a89` (Exp 111)

## M3 — Note Color Customization (Planned)
- [ ] Research how BeatmapLevel defines left/right note box colors
- [ ] Check `BeatmapLevelColorSchemeSaveData` in globalgamemanagers.assets
- [ ] Add `--left-color R G B` / `--right-color R G B` flags to pipeline
- [ ] Inject custom color scheme into the song's data structures
- [ ] Test color injection on PS4

## M4 — Advanced Song Manipulation (Planned)
- [ ] Modify existing song entries in the in-game song list (needs IL2CPP hook for `get_DisplayName`)
- [ ] Add new songs to existing album packs
- [ ] Create custom album pack definition
- [x] Per-song `_difficultyBeatmapSets` modification — `add_mode_characteristics()` function added to pipeline (Exp 110)
- [x] Addressables `BeatmapLevelSO._previewDifficultyBeatmapSets` modification — pack bundle patched (Exp 111)
- [x] Pack bundle redirect attempt via AFR root (Exp 112) — FAILED. **Root cause:** plugin hardcoded `"BeatmapLevelsData/"` prefix on all keys
- [x] Plugin key matching fix (Exp 113) — removed hardcoded prefix, keys now used as-is from JSON
- [x] Pack bundle redirect via `open_hook` — Exp 113 tested, redirect WORKS but modified bundle crashes game (CE-34878-0)
- [x] **Root cause:** `UnityPy.save_typetree()` corrupts external reference table
- [x] **Fix (Exp 115):** Binary patching via `set_raw_data()` preserves externals. 3 preview sets deployed.
- [x] Pack bundle redirect with binary-patched bundle — TESTED: game still crashes (UnityPy save incompatible)
- [x] **Root cause (Exp 116):** UnityPy `bf.save()` produces bundles incompatible with PS4 Unity
- [x] **IL2CPP dump (Exp 117):** Il2CppDumper successful. `get_previewDifficultyBeatmapSets()` at RVA 0x988E80
- [x] **Identity hook deployed (Exp 118):** Module base detection + Detour installed. Lazy init from open_hook().
- [x] **Array augmentation deployed (Exp 119):** Malloc-based 3-element array for preview sets
- [x] **SetData hook deployed (Exp 120):** Intercepts `BeatmapCharacteristicSegmentedControlController.SetData()` to inject characteristics into mode selector
- [x] **SetContent hook deployed (Exp 121):** Hooks `StandardLevelDetailView.SetContent()` — calls SetData manually after view renders
- [x] **Root cause identified (Exp 122):** IL2CPP uses MS x64 convention, native C uses SysV AMD64 — ALL IL2CPP hooks UNUSABLE without assembly trampoline
- [x] **All IL2CPP hooks removed** (set_content crashed startup)
- [x] **Pipeline versioned:** v0.50 — central VERSION file + script display
- [x] **Changelogs created:** CHANGELOG-PLUGIN.md + CHANGELOG-PIPELINE.md
- [x] **CI_RELEASE.md created:** Release instructions extracted from CI workflow
- [x] **Calling convention fixed:** `__attribute__((ms_abi))` on all IL2CPP hooks (Exp 123)
- [x] **get_preview_hook rewritten:** reads field at offset 0x98 directly, augments 1→3 preview sets
- [x] **set_content hook re-added:** hooks song selection entry point
- [ ] **Phase 4:** Test ms_abi hooks — verify get_preview fires and returns augmented array → mode selector shows 3 buttons
- [ ] **Phase 5:** Add song info patching (modify BeatmapLevelSO _songName, _songAuthorName, etc.)
- [ ] **Phase 6:** Resolve BeatmapCharacteristicSO PIDs for correct OneSaber/90Degree labels

## M5 — Polishing (Future)
- [ ] GUI for song management
- [ ] Batch deployment
- [ ] HEVAG/Vorbis encoder workaround for compressed audio
