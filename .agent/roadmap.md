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
- [x] `beat_saber_song_ids.json` — official songs cataloged (reference file)
- [x] Song name/artist/mapper extraction from `resources.assets` (22 base songs)
- [x] Song testing log document (`song_testing_log.md`)
- [ ] Difficulty metadata extraction from all 306 bundles
- [x] DLC song name extraction from addressables packs — BeatmapLevelSO objects found in `aa/PS4/therollingstones_pack_assets_all_*.bundle` (Exp 111)
- [ ] DLC song `BeatmapCharacteristicSO` references — need to locate OneSaber/90Degree PIDs in external CAB `CAB-cb38b3e2985c65d4cf8a63437da74a89` (Exp 111)
- [x] ~~Memory injection metadata patching~~ → **DEAD END** (v0.66–v0.8024, 14+ versions, 0 strings found)
- [x] **TextMeshPro UI hooking** — v0.8035 proven working, replaces text in pause menu, song details, song artist
- [x] **v0.8036** External `song_metadata.json` — replaces hardcoded replacement table

## M3 — Note Color Customization (Planned)
- [ ] Research how BeatmapLevel defines left/right note box colors
- [ ] Check `BeatmapLevelColorSchemeSaveData` in globalgamemanagers.assets
- [ ] Add `--left-color R G B` / `--right-color R G B` flags to pipeline
- [ ] Inject custom color scheme into the song's data structures
- [ ] Test color injection on PS4

## M4 — Advanced Song Manipulation (In Progress / Partially Blocked)

### Objective
Add mode selector buttons (OneSaber, 90Degree) and change song display info for custom songs on PS4.

### Completed
- [x] Per-song `_difficultyBeatmapSets` modification — `add_mode_characteristics()` function added to pipeline (Exp 110) ✅
- [x] **Root cause found — ALL pack bundle approaches blocked by CRC check (Exp 136):**
  - Addressables catalog `m_ExtraDataString` contains per-bundle CRC32 + file size + MD5 hash
  - `m_UseCrcForCachedBundles: true` enables validation at load time
  - Any modified bundle fails CRC check → CE-34878-0 crash
  - Catalog is plain JSON (not AssetBundle) → AFR plugin cannot redirect it
- [x] All IL2CPP hook approaches conclusively dead (Exp 117-131):
  - Constructor hook: never fires for Addressables-deserialized objects
  - `get_DisplayName`/`get_songName`: inlined by IL2CPP — hook never fires
  - `SetData`/`SetContent`: never reached or crashes
  - ms_abi calling convention fix applied — no improvement
- [x] UnityPy approaches all dead:
  - `bf.save("original")` — produces incompatible CAB format (+4 bytes)
  - `cab.save()` — same incompatibility
  - `save_typetree()` — silently ignores BeatmapLevelSO modifications
- [x] Manual bundle building code corrected (LZ4HC flag=3, separate writes, explicit alignment)
- [x] Per-song bundle mode selector built and deployed (`startmeup_custom_v3_modes.bundle` with OneSaber,90Degree)
- [x] **Modes bundle content verified:** 3 `_difficultyBeatmapSets` (Standard, OneSaber, 90Degree) each with 5 difficulties ✅
- [x] **Modes redirect fixed:** `BeatmapLevelsData/startmeup` now points to modes bundle (was pointing to non-modes bundle)

### Blocked — NOW UNBLOCKED by Memory Injection
- [x] ~~Song name/artist display change~~ → **SOLVED** via memory injection (patches BeatmapLevelSO in RAM, bypasses catalog CRC entirely)
- [x] ~~All pack bundle modification approaches~~ → **SOLVED** via memory injection (no pack bundle modification needed)
- [x] ~~IL2CPP hooks for display string interception~~ → **SOLVED** via heap scanning + klass pointer matching (not hooks)
- [x] ~~No known way to bypass or redirect the catalog~~ → **SOLVED** — lazy CRC validation gives window for RAM patching

### In Progress — Memory Injection Testing
- [ ] ~~**(v0.75)** Wide-range pattern scan (1GB–32GB) finds BeatmapLevelSO klass~~ → **DEAD END** (v0.8024)
- [ ] ~~**(v0.75+)** Verify object patching~~ → **DEAD END** — strings not found in any memory region
- [ ] ~~**(v0.75+)** Address timing~~ → **DEAD END** — strings not in memory at any scan time
- [ ] ~~**(v0.75+)** Verify field offsets~~ → **DEAD END** — approach abandoned
- [ ] ~~**(Future)** Cover image patching~~ → **DEFERRED** — memory injection not viable
- [ ] ~~**(Future)** Expand metadata table~~ → **DEFERRED** — memory injection not viable

### Alternative: TextMeshPro UI Hooking (Current) — ⚠️ PARTIAL SUCCESS
- [x] **(v0.8026–v0.8031)** Hook infrastructure — module discovery, DetourMode_x64, retry logic
- [x] **(v0.8031)** Hook fires correctly, no crash
- [x] **(v0.8033)** Signal-protected string extraction — matches found!
- [x] **(v0.8034)** Phase 3 string replacement — pause menu PERFECT, song list partially works
- [x] **(v0.8035)** Fix song details "?" issue — removed free() on replacement strings (use-after-free fix)
- [x] **(v0.8036)** External `song_metadata.json` — replaces hardcoded replacement table, loaded from PS4
- [x] **(v0.8037)** SetText hook — second hook for `TMP_Text.SetText(string, bool)` at RVA `0x2D3E1D0`
- [ ] **(v0.8037 finding)** Song list re-renders from data model — SetText hook fires and replacement applied, but UI overwrites with original. Need to hook BeatmapLevel data source instead.
- [x] **(v0.8038)** SetDataFromLevelAsync hook attempt — **FAILED**: async wrapper at RVA 0x1D36940 is a trampoline inlined by `AsyncVoidMethodBuilder.Start<T>()`. Zero log entries.
- [ ] **(v0.8039)** Hook `MoveNext()` at RVA 0x1D377C0 — modifies BeatmapLevel fields before state machine reads them. DEPLOYED, awaiting test.
- [ ] **(Future)** Hook `BeatmapLevelSO` fields directly — modify `songName`/`songAuthorName` at the data model level before UI renders
- [ ] **(Future)** Expand replacement table to all 32 DLC slots

### Song Metadata Feature Iteration (Current)
- [x] **Evaluate current implementation** — TMP_Text hooks work for details/pause menu, artist blanking works. Song list names NOT modified (re-rendered from data model).
- [x] **SetText hook attempt** (v0.8037) — Hook fires and replaces, but song list re-renders from BeatmapLevelSO, overwriting replacement. Fundamental limitation of text-output hooking.
- [x] **SetDataFromLevelAsync hook attempt** (v0.8038) — Hook target was async trampoline, never fired. Inlined by AsyncVoidMethodBuilder.Start<T>().
- [ ] **MoveNext() hook** (v0.8039) — Hook state machine's MoveNext() at RVA 0x1D377C0. Modifies BeatmapLevel fields before original reads them. DEPLOYED, awaiting test.
- [ ] **Option A: Hook BeatmapLevelSO directly** — Use `il2cpp_class_get_method_from_name` to modify `songName`/`songAuthorName` fields on the data model objects before UI renders
- [ ] **Option B: Hook `SetDataFromLevelAsync`** — Intercept when song data is set on UI, identify TMP_Text pointers, replace in batch after data model is set
- [ ] **Option C: Hybrid** — Keep TMP_Text hook for details/pause menu (works), add data-model hook for song list names
- [ ] **Always have working v0.8036 release to fall back to** if newer approaches hit dead ends

## M5 — Polishing (Future)
- [ ] GUI for song management
- [ ] Batch deployment
- [ ] HEVAG/Vorbis encoder workaround for compressed audio
