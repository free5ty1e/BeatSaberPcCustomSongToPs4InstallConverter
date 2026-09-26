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
- [x] Mode selector UI visibility for procedurally generated modes — **✅ DONE (Exp 179/180 DEPLOYED + CONFIRMED): catalog-redirect + pack-bundle patch approach proven. Standard/OneSaber/NoArrows visible + working on-device.**
- [x] **90Degree selector visibility FIXED (Exp 182, 2026-08-09):** 90Degree had NEVER been visible — characteristic pathIDs were mislabeled repo-wide; the pack bundle's 90Degree preview slot pointed at the 360Degree characteristic (`requires360=1`) which the game hides. All pid maps corrected to verified values (90Degree=`-5995858427784384822`), pack bundle rebuilt + catalog regenerated + deployed. **BOOT TEST PASSED (2026-08-11): all 4 modes on Hard + 90Degree Expert — "worked perfectly, exactly as I envisioned."**

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
4. ✅ Close the selector gap (BeatmapLevelSO preview-set injection) so generated modes are visible/selectable in-game — **Exp 179 DEPLOYED + CONFIRMED WORKING (2026-08-08). Catalog-redirect + pack-bundle patch approach proven. OneSaber/NoArrows/90Degree now appear in selector.**

5. ✅ **NoArrows generator bug FIXED (Exp 181, 2026-08-09)** — root cause was in `_create_text_asset_object()` (wrong type_id → MonoScript instead of TextAsset + wrong binary serialization). Fixed in pipeline v0.5311, verified locally (all NoArrows difficulties have dot notes). Deployed + confirmed on-device: NoArrows dots + OneSaber work.
6. ✅ **90Degree selector FIXED (Exp 182, 2026-08-09)** — characteristic pids were mislabeled repo-wide; 90Degree preview slot pointed at 360Degree characteristic (`requires360=1`, hidden). All maps corrected to verified pids (90Degree=`-5995858427784384822`), pack bundle rebuilt + redeployed. **Boot test PASSED (2026-08-11).**
7. ✅ **Espresso boot test PASSED (2026-08-11)** — full 224.31s audio, 4 modes on Hard, 90Degree Expert, lighting `et` events. "Worked perfectly, exactly as I envisioned."
8. ✅ **Safe-by-default pipeline (v0.5314/5315, Exp 183)** — PCM16 + no-pad + mode mapping + V2→V3 all default ON (oppose flags exist); idempotency bug fixed; `--features-only` standalone mode.
 9. ✅ **Pack-patch generalized into production pipeline (v0.5319, Exp 188, 2026-08-14)** — `tools/build_pack_mode_bundles.py` + `pack_modes` config block + CLI flags; ALL 36 packs patched (303 BeatmapLevelSOs, 4 modes × 5 diffs), `pack_modes_bundles/manifest.json`, merged catalog `catalog_pack_modes.json`. 440/440 tests. **DEPLOYED (2026-08-14):** 4 packs (rollingstones/billieeilish/lizzo/camellia) + merged catalog + 43-redirect config on PS4, validation PASSED. ❌ **USER BOOT TEST CRASHED (2026-08-15).**
 10. ✅ **Pack-patch deploy crash FIXED (v0.5320, Exp 189, 2026-08-15)** — PS4 crashed right after launch (crash at OPEN #74 after catalog redirect). Root cause: stale `m_EntryDataString` dataIndexes (rec[4] byte offsets into m_ExtraDataString not shifted when lizzo's block grew +6 B → 70/2251 garbage). Fixed `update_catalog_entry()` (dataIndex shift on block delta) + `_parse_catalog_block()` (regex parse). Merged catalog regenerated (0 invalid), 444/444 tests (now config-driven, no hardcoded packs). 🔲 **REDEPLOY + USER BOOT TEST PENDING** — `--deploy-pack-modes --deploy-config --verify-ps4`, then 4 packs' mode selectors (4 modes on Hard+).
 11. ✅ **Pipeline reproducibility audit (v0.5321, Exp 190, 2026-08-15)** — confirmed the 36 committed bundles were originally dev-script-built + adopted (not production-built). Found prod module's leftover `"360Degree"` pid in `CHAR_PATH_IDS` (pre-Exp-175) padded 360Degree preview sets 1→5 → 10/36 packs rebuilt non-byte-identical (the 4 deployed packs were unaffected). Removed stale entry + regression test → **all 36 packs rebuild byte-identical from the production module (0/36)** — fresh users can reproduce the exact setup from the pipeline, zero manual steps. 445/445 tests.
 12. ✅ **"STILL crashes" root-caused + deployed + verify hardened (v0.5322, Exp 191, 2026-08-16)** — after Exp 189/190, the user booted and STILL crashed. Root cause: **the fixed catalog was never deployed** — the PS4 still ran the broken v0.5319 `catalog_pack_modes.json` (70/2251 invalid dataIndexes, md5 `0eb8a27d…`; local fixed `975bacca…`), same crash signature (OPEN #58/#74 right after the catalog redirect). Size-only verify can never catch this (broken/fixed catalogs are byte-identical in size). Deployed the fixed catalog (verified on-device: 0 invalid, all 4 pack CRCs/sizes OK), deleted stale prototype files on the PS4 (`catalog_startmeup_modes.json`, `startmeup_pack_modes.bundle`), hardened `--verify-ps4` with **check #7 (catalog content validation**: dataIndex integrity + md5 vs local build + per-pack CRC/size via new `validate_catalog_dataindexes()`/`validate_catalog_entries()`/`find_catalog_entry_js()`), removed the legacy `pack_bundle` single-pack prototype from the DEFAULT config (superseded by `pack_modes`). 451/451 tests (6 new). 🔲 **USER BOOT TEST PENDING** — boot Beat Saber; stable boot through catalog redirect + pack scan, then verify 4 packs' modes on Hard+.

## M6 — Chromeo Source Recovery + Mass Redeploy (In Progress — v0.5316, Exp 184/185)

### Objective
Recover the 6 deleted Chromeo slot sources from deployed PS4 bundles, rebuild all 38 custom songs through the v0.5316 pipeline (mode mapping + generators, full audio, V2→V3), and mass-redeploy to the PS4.

### Completed
- [x] **Chromeo bundle extraction** (Exp 184): pulled 6 bundles from PS4; TextAssets gzip via `surrogateescape` decode; audio = `.resource` subfile (`CAB-<hash>.resource`). Beatmap formats: 4 slots V4.0.0 (relative `colorNotes{b,i}` + `colorNotesData{x,y,c,d}`), CycleHit/Ghost mixed V3.2.0/V4.0.0.
- [x] **V4→V3.2.0 decoder** (`/tmp/opencode/reconstruct_chromeo_src.py`): merges data via `i` index with defaults, fills `bpmEvents` (per-slot BPM), validated decoded max beat vs audio.gz `bpmData[0].eb`.
- [x] **Reconstruction output**: `songs/chromeo_backout/{slot}/` with `<Diff><Mode>.dat`, `Info.dat` (2.1.0, per-slot metadata), `audio.fsb`.
- [x] **All 6 Chromeo rebuilt + verified** (Crystallized 59.2MB → WhatTheCat 37.8MB; full audio, corrected eb, generated modes).
- [x] **Slot→source mapping for all 32 non-Chromeo slots** resolved via `songs_repo/` Info.dat names.
- [x] **Mass re-run all 38 songs (v0.5316, Exp 185)**: 38/38 bundles in `/tmp/opencode/mass_build/` — every slot Standard 5/5 + OneSaber 5/5 + NoArrows 5/5 + 90Degree 5/5. 407/407 tests.
- [x] **Generator bug fixed (v0.5316)**: V3 beatmaps may omit `x`/`y`/`b` (default 0) — OneSaber/90Degree generators crashed with KeyError. All reads now `.get(..., 0)`.
- [x] **Deploy prep**: `redirects.json` regenerated (39 redirects), `deploy_all38.sh` written; `deploy_all.sh` (13-slot, pre-mode-mapping) confirmed OUTDATED.
- [x] **Deploy to PS4 (Exp 186, 2026-08-12):** ✅ `deploy_all38.sh` ran — all 38 bundles uploaded + verified on-device (sizes match), `redirects.json` (39) + `song_metadata.json` verified. Plugin v0.8040 confirmed.
- [ ] **User test**: Chromeo slots all 6, new Billie songs (Oxytocin/NDA/ThereforeIAm), 90Degree across songs, full audio lengths.

## M8 — Generalized Pack Modes: Full-Fleet Validation (COMPLETED — v0.5328, Exp 198-203)

### Objective
Prove the 4-mode pack patch + custom-song fleet end-to-end on hardware, entirely via pipeline automation: all 38 custom songs rebuilt through the current pipeline, all 4 replaced packs fully patched, every song showing Standard/OneSaber/NoArrows/90Degree.

### Completed
- [x] **Exp 198/199 (v0.5325→0.5326): boot-crash root cause INVERTED** — the v0.5325 "pathID fix" (all preview sets → Standard's pathID) was ITSELF fatal: CE-34878-0 at menu init with 4 identical PPtrs. Hardware-proven golden structure = DISTINCT `CHAR_PATH_IDS[mode]` pathIDs per set (+ ranks [0..4], rank-dedup padding kept). Reverted; lizzo rebuild byte-identical to known-good (`345d6a0e…`), RS rebuild identical to golden working bundle (`5ed23829…`); regression tests pin the invariant (562/562). Reference bundle archived (`development/reference_bundles/`). User VERIFIED: boot clean + No Arrows gameplay OK.
- [x] **User directive adopted:** everything through pipeline flags, fixes in pipeline code, no manual file manipulation (saved to agent memory).
- [x] **v0.5327 automation hardening:** stable `mass_deploy.bundle_dir` (`beat_saber_deluxe/mass_bundles/`, was /tmp); `build_deploy_all38.py` rewritten build-all→deploy-once with abort-on-unresolved; Chromeo backout source resolution + `--audio audio.fsb` pass-through; 2BeLoved metadata-key match fixed. All 36 pack bundles rebuilt with corrected structure.

### Completed (Exp 200)
- [x] **Full-fleet rebuild + one-shot deploy** — 38/38 song bundles built (Chromeo via `--audio audio.fsb`), 36 pack bundles rebuilt with golden structure, catalog + redirects.json (43) deployed via pipeline flags; **Post-deploy validation PASSED**.
- [x] **Selector mechanism identified** — mode selector comes from PACK preview sets; per-song template SOs are a different class (`*BeatmapLevelData`) and never carried mode sets (explains Standard-only customs under lizzo-only config).

### User acceptance (partial pass — Exp 200)
- [x] Boot clean; stock song OK; RS + lizzo + billieeilish customs play No Arrows fine; OneSaber-blue + full-audio untested this round.
- [x] **Chromeo crash root-caused (v0.5328):** reconstructed V4→V3 maps were minimal-schema (8 vs 17 required keys) + zero-note Easy maps in 3 slots → CE-34878-0 at gameplay load. Fixed with `normalize_v3_schema()` at both injection points + empty-difficulty donor rescue. 571/571 tests.

### Completed (Exp 202-207)
- [x] **Britney Spears pack replacement (Exp 202):** All 11 songs replaced with custom BeatSaver songs using `--download-beat-saver-song` pipeline, each with 4 selectable modes.
- [x] **All 5 music pack documentation complete (Exp 203):** Self-contained .md docs and .sh scripts for all 5 packs (Britney Spears, Rolling Stones, Lizzo, Billie Eilish, Camelia/Chromeo) with verified BeatSaver MAP IDs. Total 47 songs across 5 packs.
- [x] **Chromeo bugfixes in v0.5328:** V3 schema normalization (17 keys), zero-note Easy rescue, color/direction restoration (c alternates 0/1, d cycles 0-7), BPM timing fix (m preserved, b=0 explicit).
- [x] **BeatSaver MAP IDs corrected to use CUSTOM songs (Exp 204):** Fixed all documentation to use the actual custom song replacements' BeatSaver MAP IDs (the songs we're installing), not the target DLC song names. Added BeatSaver MAP_ID column to current-song-replacements-on-chris-ps4.md. Each pipeline command now has detailed comment with full custom song metadata (name, artist, album, year, MAP_ID, link, genre, BPM, difficulties).
- [x] **Unified --deploy-full flag (Exp 207):** Added `--deploy-full` to pipeline that handles complete orchestration in one command: song bundle + pack mode bundles + merged catalog + redirects.json + post-deploy validation. All docs/scripts updated to use `--deploy-full`.

### Completed (Exp 212-216) — Single-Song Scoping + Multi-Song Incremental Deploy
- [x] **Self-contained single-song `--deploy-full` (v0.5331, Exp 212):** Single-song deploy scopes to just the target song + its pack, deploys plugin + plugins.ini + features.json. Does NOT touch other packs.
- [x] **Pre-deploy PS4 state check (v0.5331, Exp 213):** `ps4_state.py` shows accurate PS4 state before each deploy, prompts for user confirmation.
- [x] **Download guard ordering fix (v0.5332, Exp 214):** `--download-beat-saver-song` resolution moved before early-exit guards so `--deploy-full` reaches song path.
- [x] **Validation scoping fix (v0.5333, Exp 214 follow-up):** `verify_ps4_deployment()` accepts `packs` filter and threads it through all helpers.
- [x] **AFR base path fix + clean slate (v0.5333, Exp 215):** Pipeline default config correct; backup script cleans AFR dir; `ps4_state.py` checks AFR dir.
- [x] **Multi-song incremental deploy + clear-target-song (v0.5334-v0.5336, Exp 216):**
  - **Second song overwrites first (v0.5336):** `deploy_slots` now downloads current `redirects.json` from PS4 to discover ALL existing custom songs in target pack, includes them in deployment scope.
  - **Artist name restored for entire pack on clear (v0.5335):** `--clear-target-song` only restores artist metadata when NO custom songs remain in the pack.
  - **`--clear-target-song` UnboundLocalError (v0.5335):** Fixed `other_custom_in_pack` initialization before conditional blocks.
  - **Pack bundle not incrementally patched (v0.5335):** `deploy_pack_bundle()` now downloads existing PS4 patched bundle before each deploy for incremental patching.
  - **Plugin v0.8042:** Added `enable_beatmap_mode_mapping` runtime feature flag gating visibility of extra mode sets.
  - **All 30 example scripts** fixed for syntax errors and verified running with PS4 state check + user confirmation prompt.

### Completed (Exp 217) — Multi-Pack Cross-Pack Deploy Fix
- [x] **Multi-pack deploys wiped other packs' custom songs (v0.5337):** Running one pack's install script deleted all other packs' custom songs (case-sensitive slot matching made every slot lookup fail → "empty slot scope" deleted all song redirects; deploy_slots also only scoped the target pack). Fixed: case-insensitive matching in `_ensure_mass_song_redirects` + `patch_pack_bundle`; `deploy_slots`/`deploy_packs` now collect ALL existing custom songs and their packs from the PS4 `redirects.json` so cross-pack state is preserved and re-deployed. Hardware-verified: 4 songs across 2 packs (Camelia + Billie Eilish), 7 redirects, catalog CRC/size OK for both packs, surgical patching intact. 581/581 tests.

### Completed (Exp 232) — CRITICAL: Chained Multi-Pack Deploy Keeps Only Last Pack
- [x] **Root cause:** stale-sweep validated pack redirects by LOCAL bundle existence; clean-slate wipe empties pack_modes_bundles/ → each script's deploy deleted the previous packs' redirects. Latent since Exp 226; exposed by the true clean slate. Fix: validity = current pair OR deployed-per-state-file (_resolve_deployed_packs).
- [x] **Live state repaired:** 5 pack pairs + catalog re-added, regenerated for all 5 packs, 2 ghost PATD song redirects (deadmanwalking/sugarsoaker) cleared via --clear-target-song. Validation PASSED (5 packs, 36 songs, catalog md5 match).
- [x] 3 regression tests (chain accumulation, deployed-survives-missing-bundle, true-stale removal). v0.5349.

### Completed (Exp 231) — V4 Columnar NoArrows Clobber + cwd-Dependent Wipe Bug
- [x] **'15 Minutes' NoArrows arrows root-caused:** v4 columnar rows' arrow d clobber the generator's d=8 events via the row-over-event merge at injection. Fix: NoArrows dot pass re-applied AFTER v4/v2 conversion (idempotent; 90Degree excluded — rotation-append not idempotent; OneSaber already post-merge). NOT a missing-difficulty failure — the auto-fill + generators + lookup all ran correctly.
- [x] **Both v4 songs redeployed live** (15 Minutes + Oxytocin): all 10 NoArrows charts verified all-dots in-bundle; PS4 bundles + pack + catalog live.
- [x] **The recurring 3-file deletion truly fixed:** Exp 229's preserve logic was cwd-dependent (git ls-files inherited the process cwd — any non-repo launch dir returned [] → wholesale rmtree). Now `git -C <script_dir>`; verified from /workspace, /tmp, /.
- [x] 5 regression tests (clobber documented, post-conversion pass, idempotency, source-audit ordering, tier-3 ExpertPlus). 639/639; ruff clean. v0.5348.

### Completed (Exp 230) — Lint Fixes In Code (v0.5347)
- [x] All 17 ruff findings fixed in `full_custom_song_pipeline.py` (2 dead stores, 3 unused imports AST-verified, 10 f-string prefixes, 2 import sorts). Zero functional changes — normalize_v3_schema byte-equivalence proven across 10 edge cases.
- [x] Exp 229's pyproject.toml per-file-ignores removed — file fully lint-enforced; `ruff check tools/` exit 0.
- [x] Version 0.5346 → 0.5347; plugin unchanged (v0.8047). User re-runs the QA test procedure for the stable release point.

### Completed (Exp 229) — CI Failure RCA + Release Artifact Audit
- [x] **214 CI test failures root-caused:** (1) hardcoded /workspace absolute paths in tests — repo-relative now; (2) hardware-environment tests (dump + built bundles) with no skip guards — HAS_DUMP/HAS_BUILT_ALL class gates added; (3) Unit Tests job green-lying via tee exit-code swallow — set -o pipefail.
- [x] **17 lint findings resolved via config** (pyproject.toml per-file-ignores for the QA-frozen pipeline file — zero code changes per user directive; ruff clean on tools/).
- [x] **Release zip audit:** all 69 example_*.* files bundled (docs/example-scripts/), beat_saber_song_ids.json, requirements.txt, ps4_config.example.json, both READMEs, feature docs, changelogs. **ps4_dump disclaimer in release notes + README**: user supplies their own decrypted dump (correct version + DLC loadout); no game data in the release.
- [x] **--clean-ps4 preserves git-tracked files** (git ls-files enumeration before the artifact wipe).
- [x] **PR #4 title/description updated** to the expanded scope (mode mapping + auto-fill + generators + hardening, Exps 160-229) via gh REST PATCH.

### Completed (Exp 228) — Unicode Metadata Matching + BeatSaver V4 Support
- [x] **'…Baby One More Time' title replacement fixed:** 3-part Unicode chain (ensure_ascii escapes → byte-verbatim plugin parse → UTF-16 '?' folding). song_metadata.json now raw UTF-8; plugin unescapes \uXXXX + folds keys through the extraction mirror (fold_utf8_to_ascii); create_il2cpp_string UTF-8→UTF-16LE. Backward compatible with already-deployed escaped files.
- [x] **BeatSaver V4 (v4.0.x) map support:** PS4-native columnar format (Standard charts play unconverted), but mode generators produced ambiguous mixed events on columnar input, and V4 Info.dat song.title/author/audio.bpm were unread (display names fell back to map IDs '4dea2'/'443f3'). New is_v4_beatmap/convert_v4_to_v3 in replace_beatmaps + mode-injection donors; _read_info_song_metadata/_read_info_bpm_from_dict; loud map-ID fallback warning.
- [x] **--metadata-only CLI mode** — surgical song_metadata.json add/update/deploy (no song processing/redirects/plugin). Used live to fix both v4 entries.
- [x] Both affected bundles regenerated + redeployed (v3.2.0 denormalized, full note geometry, no colorNotesData residue); plugin v0.8047 deployed + strings-verified on PS4. 18 new tests; 634/634.

### Completed (Exp 227) — Ghost Packs + True Clean Slate
- [x] **Ghost packs fixed:** the Exp 226 union pulled the local-bundle fallback into deploy scopes → clean-slate clear-song rebuilt 6 never-installed packs. New _resolve_deployed_packs (state-file-only) drives deploy unions; caller packs= authoritative in entries/ensure.
- [x] **--clean-ps4 now wipes ALL local state** (user directive): pack_modes_bundles/, custom_songs/, mass_bundles/, stray blobs — every local input a fallback could read. Verified 3+8+69+39+51 items cleared, full regenerability confirmed.
- [x] 3 ghost-pack regression tests + 5 scoping tests updated. 616/616.

### Completed (Exp 226) — Mode Buttons Per Pack + clear-target-song Wipe + Script Completion
- [x] **Pure-filter pack scoping fixed:** requested packs JOIN the active set in all 4 helpers (deployed-state discovery lags the deploy — britney/camellia/lizzo/RS patches were silently skipped; only the first pack got mode buttons). All 5 packs patched + validated live.
- [x] **--clear-target-song redirect wipe fixed** (empty scope = no-op; re-ensure scoped to existing redirects; unmatched scope preserves). Live state restored (44 songs + 5 packs + catalog), validation PASSED.
- [x] **RS script misplaced PATD slot (SugarSoaker) removed**; PATD deployment reverted; catalog regenerated for the 5 intended packs.
- [x] **Scripts completed:** BE +3 songs, RS +StartMeUp, britney Toxic/Womanizer → non-Britney songs (all download-verified). 5 wipe-safety + scoping regression tests; 613/613.

### Completed (Exp 225) — Clean-Slate Catalog Crash (Exp 224 Regression) Fixed
- [x] **Root cause:** two deploy gates checked the pinned pack_modes.packs list (always [] under auto-discovery) → clean-slate first-song deploy shipped the patched pack bundle WITHOUT the merged catalog or aa/catalog.json redirect → CRC crash CE-34878-0. Gates now use _resolve_active_packs.
- [x] **Failed validation now aborts** (exit 1 + CE-34878-0 warning) — a broken deploy can never print "Pipeline complete!" and exit 0 again.
- [x] **4 regression tests** pin the exact crash path (TestCleanSlateCatalogPair). Live PS4 repaired: catalog deployed, 3 redirects, validation PASSED. 607/607.

### Completed (Exp 224) — lftp `&` Path Bug + Zero Hardcoded Pack Expectations
- [x] **All FTP paths quoted** (_ftp_quote, 21 sites) — lftp's command language splits paths at `&` (Scream&Shout upload silently failed, lftp exit 0); deploy_to_ps4 now verifies uploads via remote listing, never trusting lftp's exit code. `--target "Scream&Shout"` quoted in docs; latent `--target Satisfaction` → ICantGetNoSatisfaction fixed in RS docs.
- [x] **Hardcoded pack list removed (user directive: ZERO pack expectations)** — pack_modes.packs default now []; `_resolve_active_packs` auto-discovers from the deployed state (pinned config list → redirects.json referenced packs → local built bundles only when no state file). Validation/catalog/enforcement follow reality; a never-deployed RS bundle no longer triggers failures.
- [x] **Scream&Shout_v3.bundle re-uploaded; full --verify-ps4 GREEN.** 603/603 tests.

### Completed (Exp 222) — Feature-Flag Gating Audit (Decorative Flag Fixed)
- [x] **enable_beatmap_mode_mapping was decorative** (assigned, logged, counted — gated nothing; explains mode selector working with flag absent). v0.8046: OFF → open-hook skips pack_assets + catalog redirects → stock packs, Standard-only modes; per-song customs still play. Catalog skip required (Exp 180 CRC invariant).
- [x] **Gating contract test suite** (5 tests): every g_feature_* must have a conditional use outside load_features; kill switch + each feature flag verified against their behavior paths.
- [x] **ps4_state.py "Extra data" parse fixed:** lftp banner chatter around cat output; both JSON reads use raw_decode on the first object.

### Completed (Exp 221) — Flag-Count Fix + Plugin-Deploy Enforcement + Compressed Toast
- [x] **"2/3 flags" root-caused:** stale local features.json missing enable_beatmap_mode_mapping deployed verbatim. Deploys now merge DEFAULT_FEATURES (explicit values preserved; file created from defaults when absent). 3 regression tests.
- [x] **--deploy-full always builds + deploys the latest plugin** (make clean + make -B); --skip-plugin-deployment opts out.
- [x] **One combined boot toast** (plugin v0.8045): "BS Deluxe v0.8045 (ON/OFF) / By Chris Primeish / (N/3 features ON | official songs only)" — second toast was swallowed by PS4VR headset switch-over.
- [x] **ps4_state.py reports feature flags** (enable_plugin + 3 flags + expected boot-toast text; MISSING keys flagged).

### Completed (Exp 220) — Startup Feature-Flag Status Notification
- [x] **Boot toast shows flag status (plugin v0.8044):** second notification after the version banner — "BSD Plugin enabled N/3 feature flags ON" or "BSD Plugin DISABLED Official songs only (0/3 flags active)". Deployed + strings-verified. (Deploy lesson: GoldHEN FTPD unpacks FSELF on download — verify .prx uploads by strings, not md5.)

### Completed (Exp 219) — Example-File Song-Quality Audit + Global Kill Switch
- [x] **Native Easy/Normal/Hard rule enforced across all 34 pack example docs (v0.5339):** audited all 44 unique BeatSaver MAP_IDs via live API; replaced 15 failing songs (camelia ×6, britney_spears ×8, lizzo ×2, billie_eilish ×1, rolling_stones ×1) with verified maps — each candidate downloaded and per-difficulty note counts checked for real progressions (flat/duplicate charts rejected). Difficulty comments now state the TRUE native diff set.
- [x] **Global plugin kill switch (plugin v0.8043):** `enable_plugin` runtime flag in features.json — explicit false makes the plugin fully inert on next boot (official songs only); defaults TRUE when absent. Pipeline: `--features-only --set-feature enable_plugin=false|true`. No plugins.ini edit needed.
- [ ] **User redeploy + boot test:** re-deploy Camelia via the updated script (new 5/5-native songs); test `enable_plugin=false` → official-only behavior, then `true` → customs restored.

### Completed (Exp 218) — Camelia Song Quality (Partial-Difficulty Maps, BPM Grid, OneSaber Dots)
- [x] **Stock beatmaps in unreplaced difficulty slots (v0.5338):** Maps providing fewer than 5 difficulties left the STOCK chart in missing slots — stock timing over custom audio = "BPM wayyy too slow, notes wayyy too late" on the user's played difficulty (Hard). New `fill_missing_standard_difficulties()` clones the map's own closest harder (else easier) difficulty into every missing slot before replacement and mode generation.
- [x] **v0.52 eff-BPM heuristic undershot trailing-tail maps (v0.5338):** `max_beat×60/audio_duration` stretched the mapper's beat grid across trailing silence ('Roni 112.1 vs the real 117 → notes 9s late by song end). Info.dat `_beatsPerMinute` is now the authoritative grid; the max-beat scan remains only as a beyond-grid guard. All six Camelia maps verified at exact mapper BPM.
- [x] **OneSaber arrows (v0.5338):** User-facing OneSaber is blue DOTS. `_generate_one_saber()` sets d=8 (same-cell gap rule removed), and every OneSaber injection in `add_mode_characteristics()` is normalized through the generator (mapper-authored charts included). Bombs pass through. 595/595 tests.
- [ ] **Redeploy the four broken Camelia songs + user retest** (Hard on-grid through song end; OneSaber dots-only).

### Next (M9 — Generalization)
- [ ] **Re-test Chromeo slots** (all 6) after v0.5328 redeploy with `--deploy-full`.
- [ ] **Generalization test**: target a FRESH music pack / song end-to-end via pipeline config only (user directive: support ANY song pack / song in the game).
