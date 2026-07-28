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
- [x] Song metadata management (`--song-name`/`--artist` flags, combined "Name / Artist" format)
- [x] BeatSaver slot ID resolution via `beat_saber_song_ids.json`
- [x] Integration test suite (34 tests covering FSB5, V2→V3, redirect config, metadata, song IDs)

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

### TextMeshPro UI Hooking (PROVEN WORKING — v0.8040)
- [x] **(v0.8026–v0.8031)** Hook infrastructure — module discovery, DetourMode_x64, retry logic
- [x] **(v0.8031)** Hook fires correctly, no crash
- [x] **(v0.8033)** Signal-protected string extraction — matches found!
- [x] **(v0.8034)** Phase 3 string replacement — pause menu PERFECT, song list partially works
- [x] **(v0.8035)** Fix song details "?" issue — removed free() on replacement strings (use-after-free fix)
- [x] **(v0.8036)** External `song_metadata.json` — replaces hardcoded replacement table, loaded from PS4
- [x] **(v0.8037)** SetText hook — second hook for `TMP_Text.SetText(string, bool)` at RVA `0x2D3E1D0`
- [x] **(v0.8038)** SetDataFromLevelAsync hook — FAILED: async wrapper inlined, never fires
- [x] **(v0.8039)** MoveNext() hook — WORKS! Modifies BeatmapLevel fields before state machine reads them. 21/32 songs correct, 11 had case mismatches.
- [x] **(v0.8040)** Case fix + song IDs pipeline — **ALL 32 SONGS CONFIRMED WORKING** ✅
- [x] **Camellia Music Pack replacement** — First full pack replacement (6 songs) ✅ (v0.5305)
- [ ] **(Future)** Multi-artist pack metadata — Currently blanks original artist globally; need per-field tracking

### Song Metadata Feature — COMPLETE (v0.8040)
- [x] **Evaluate current implementation** — TMP_Text hooks work for details/pause menu, artist blanking works.
- [x] **SetText hook attempt** (v0.8037) — Hook fires and replaces, but song list re-renders from BeatmapLevelSO, overwriting replacement.
- [x] **SetDataFromLevelAsync hook** (v0.8038) — Hook target was async trampoline, never fired. Inlined by AsyncVoidMethodBuilder.Start<T>().
- [x] **MoveNext() hook** (v0.8039) — Modifies BeatmapLevel fields before state machine reads them. 21/32 correct.
- [x] **Case sensitivity fix** (v0.8040) — Pipeline reads exact game strings from `beat_saber_song_ids.json`. All 32 songs confirmed working.
- [x] **Camellia Music Pack replacement** — First full pack replacement (6 songs) via pipeline (v0.5305) ✅
- [ ] **(Future)** Multi-artist pack metadata — Need per-field tracking instead of global artist blanking

## M5 — Beatmap Mode Generators (Pipeline, Planned)

### Objective
Generate mode-specific beatmaps from Standard source files by applying algorithmic transformations.
These run as pipeline steps, producing dedicated `.dat` files that feed into the mode mapping feature.

### "No Arrows" Mode Generator
Take a Standard beatmap and convert all arrow notes (`_cutDirection`/`d` > 0) to dot notes
(`d` = 8, any direction). Walls, bombs, chains, sliders pass through unchanged.

- [ ] Pipeline function: `convert_to_no_arrows(beatmap_data) -> beatmap_data`
- [ ] CLI flag: `--generate-no-arrows` (outputs e.g. `ExpertNoArrows.dat`)
- [ ] Must run AFTER Standard beatmaps are created, BEFORE mode mapping

### "One Saber" Mode Generator
Take a Standard beatmap and convert all notes to single-saber (left color only, `a`=0/`c`=0).
Detect note pairs with overlapping timing windows that are impossible to hit with a single
saber and remove one note of each conflicting pair.

Detection heuristic:
- Notes within < 1 beat of each other on different columns → conflict
- If notes have opposing cut directions in close succession → conflict
- When conflict detected: remove the later note (preserves flow)

- [ ] Pipeline function: `convert_to_one_saber(beatmap_data) -> beatmap_data`
- [ ] Conflict detection algorithm: spatial + temporal window analysis per note pair
- [ ] CLI flag: `--generate-one-saber` (outputs e.g. `ExpertPlusOneSaber.dat`)
- [ ] Optional: `--one-saber-remove-threshold <beats>` (default: 1.0)

### "90 Degree" Mode Generator
Take a Standard beatmap and insert rotation events (`rotationEvents`) that cycle through
lane angles every N measures. Provides configurable cycle rate and randomization.

Rotation scheme:
- Cycle sequence: 0° → 90° → 180° → 270° or any subset
- Insert `{"b": start_beat, "e": rotation_degrees}` at interval boundaries
- Wrap around after each full cycle

- [ ] Pipeline function: `generate_90_degree_rotations(beatmap_data, ...) -> beatmap_data`
- [ ] CLI flag: `--generate-90-degree` (outputs e.g. `ExpertPlus90Degree.dat`)
- [ ] `--90-degree-cycle <beats>` — fixed cycle length (default: 8 beats = 2 measures)
- [ ] `--90-degree-random` — randomize interval length between min/max
- [ ] `--90-degree-min-cycle <beats>` (default: 4)
- [ ] `--90-degree-max-cycle <beats>` (default: 16)
- [ ] `--90-degree-angles 0,90,180,270` — custom rotation angle sequence

### Implementation Order
1. No Arrows (simplest — pure note filter, no timing analysis)
2. One Saber (requires conflict detection algorithm)
3. 90 Degree (requires UI testing for rotation event compatibility)
