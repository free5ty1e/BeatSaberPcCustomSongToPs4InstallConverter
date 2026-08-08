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

### Mode Selector UI — Structural BeatmapLevelSO RAM Patching (IN PROGRESS — v0.8048)
- [x] **(v0.8042)** Structural klass find (no levelID anchor) + BSL collector + patch logic implemented
- [x] **(v0.8043)** Trigger fixed to fire on any MoveNext; scan runs on worker thread → **❌ instant crash** (process-wide SIGSEGV handlers hijacked Unity GC page-protection faults)
- [x] **(v0.8044)** Synchronous game-thread scan → **❌ crash again at same point** — signal handlers during song-list rendering are the hazard regardless of thread. Root cause CONFIRMED via crash log.
- [x] **(v0.8045)** Signal-free scan via `sceKernelQueryMemoryProtection` → **✅ NO CRASH (syscall works, prot=0x3), but ❌ "klass not found"** — `mode_extract_string` length bug (picked garbage `len_14`) + scan range too narrow (16MB–4GB only)
- [x] **(v0.8046)** Fixed string-len selection, widened low range to 16MB–64GB @1MB pages (v0.77-proven), added `[MODE] Scan diag` counters. **TESTED (Exp 169): ✅ NO CRASH but arrfail=25443 strfail=0 — all candidates at 0x1C2–0x1D5xxxxx are serialized pack-bundle data (lid=packed floats), not managed objects. ~1min hang during scan (dev-only, warned).**
- [x] **(v0.8047)** Tightened diagnostics: v0.77 pointer window [16MB,512GB], string check before array check, `mode_preview_arr_ok` failure stages (1-8), raw64 dumps. **TESTED (Exp 170): ✅ NO CRASH. Root cause CONFIRMED = TRIGGER TIMING — scan fired from first MoveNext (open #731) before any pack BeatmapLevelSO deserialized; the pack bundle re-opened at [OPEN #792] AFTER all 22 cells rendered. Offsets verified correct (dump.cs TypeDefIndex 11680); BeatmapLevel has no BSL back-reference for the MoveNext hook to anchor on.**
- [x] **(v0.8048)** Trigger timing fix: `open_hook` records `*_pack_assets_all_*.bundle` opens after the first MoveNext (`g_mode_pack_last_open`); MoveNext scan fires only on fresh pack load since last scan; failures RETRYABLE (MODE_MAX_ATTEMPTS=4 — fixes the one-shot early-miss that permanently disabled the scan in v0.8047); song-start `BeatmapLevelsData` fallback trigger (v0.77-proven); `g_mode_scan_in_progress` re-entrancy guard; MoveNext hook installs when metadata OR mode-mapping feature on. **Built 105,120 B, 361/361 pytest. PS4 unreachable — deploy pending.**
- [x] **(v0.8049)** Lifted `g_mode_pack_last_open` gate so scan fires on first MoveNext. **TESTED (Exp 171): preview audio regression from in-open_hook trigger — trigger kept decoupled.**
- [x] **(v0.8050/v0.8051 — ⛔ CRASH REGRESSION, reverted Exp 176)** The "cleanup" rewrote `src/main.cpp` to use a **manual `memcpy` 12-byte jump hook** (`install_hook` on `sys_open`) and re-enabled `src/hooks.cpp` in the Makefile → **instant startup crash, no notification**. `mprotect` attempt also failed. **RESTORED to v0.8040 stable baseline (GoldHEN Detour API, hooks.cpp excluded). Deployed + all 365 tests pass.**
- [ ] **Mode selector shows 5 modes in UI** — Phase 2 RAM scan dead end; pursued via Phase 1 pipeline bundle patching + procedural generators (M5)
- [ ] **(Final UX)** Remove/reduce the ~1 min scan hang (acceptable for dev diagnostics only)
- [ ] **(M5)** Unique 360/90 `.dat` beatmap data per mode (Phase 1 currently clones Standard patterns)

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

## M5 — Procedural Mode Generators (In Progress — v0.5310)
- [x] Integrate generator framework into pipeline
- [x] Implement `_generate_no_arrows` (V2+V3, non-mutating, all notes → dots)
- [x] Implement `_generate_one_saber` (single-saber recolor, drops simultaneous + same-cell close arrowed notes)
- [x] Implement `_generate_90_degree` (V2→V3 conversion + alternating ±90° rotationEvents every cycle)
- [x] `generate_missing_mode_beatmaps()` — default gap-filling under `--enable-beatmap-mode-mapping`, runs Step 5a (before beatmap replacement), never overwrites songs' own mode files
- [x] CLI flags: `--skip-mode-generation`, `--one-saber-min-gap` (0.25), `--rotation-cycle-beats` (8.0)
- [x] Expanded generator test suite to 17 tests; full suite 365 pass (v0.5310, Exp 177)
- [x] Deployed fresh `startmeup_v3` bundle (12,405,290 B) with 14 generated mode beatmaps + 3 mode sets (Exp 177)
- [ ] Mode selector UI visibility for procedurally generated modes — **UNBLOCKED via catalog-redirect avenue (Exp 178/179): v0.8040 `open()` hook can redirect `aa/catalog.json`, so the Addressables catalog CRC+size dual-validation is controllable. Exp 179 built `startmeup_pack_modes.bundle` (7,905,425 B, dec-stream CRC `0x8e1f8937`) + `catalog_startmeup_modes.json` (only rolling-stones entry changed). KEY: catalog `m_Crc` = zlib.crc32 of the DECOMPRESSED stream (not file CRC) — GF(2) forcing obsolete. Exp 178 byte-identical catalog redirect deployed, awaiting boot confirmation, then deploy Exp 179.**

### "No Arrows" Mode Generator — ✅ DONE (v0.5310)
Take a Standard beatmap and convert all arrow notes (`_cutDirection`/`d` > 0) to dot notes
(`d` = 8, any direction). Walls, bombs, chains, sliders pass through unchanged.

- [x] Pipeline function: `_generate_no_arrows(beatmap_data)` — V2+V3 aware, non-mutating (deep-copies)
- [x] Integrated via `--enable-beatmap-mode-mapping` (default; no separate flag needed)
- [x] Runs in Step 5a (AFTER Standard beatmaps selected, BEFORE mode mapping replacement)

### "One Saber" Mode Generator — ✅ DONE (v0.5310)
Take a Standard beatmap and convert all notes to single-saber (left color only, `a`=0/`c`=0).
Remove notes that are impossible to hit with a single saber.

- [x] Pipeline function: `_generate_one_saber(beatmap_data, min_gap)` — recolors all notes to color 0
- [x] Drops simultaneous notes (one saber = one note at a time)
- [x] Drops same-cell arrowed notes closer than `min_gap` beats (default 0.25, `--one-saber-min-gap`); dots after arrows kept
- [x] V2+V3 aware, non-mutating

### "90 Degree" Mode Generator — ✅ DONE (v0.5310)
Take a Standard beatmap and insert rotation events (`rotationEvents`) that cycle the lane
angle back and forth every N beats.

- [x] Pipeline function: `_generate_90_degree(beatmap_data, cycle_beats)` — V2 sources converted to V3 first
- [x] Alternating ±90° rotation events every `cycle_beats` (default 8.0 = 2 measures, `--rotation-cycle-beats`)
- [x] V3 passthrough preserved; non-mutating

### Implementation Order
1. ✅ No Arrows (v0.5309)
2. ✅ One Saber (v0.5310)
3. ✅ 90 Degree (v0.5310)
4. 🔲 Close the selector gap (BeatmapLevelSO preview-set injection) so generated modes are visible/selectable in-game — **Exp 179 bundle + catalog BUILT/VERIFIED; deploy gated on Exp 178 catalog-redirect boot test**
