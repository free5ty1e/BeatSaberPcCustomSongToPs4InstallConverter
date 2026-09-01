# Project Summary: Beat Saber PS4 Custom Song Support
**Last Updated:** 2026-08-25
**Status:** 🟢 **EXP 202 (v0.5328): Britney Spears Pack Replacement Complete.** All 11 songs in the official Britney Spears DLC music pack replaced with custom community songs from BeatSaver, each with 4 selectable modes (Standard, OneSaber, NoArrows, 90Degree). Per-song pipeline commands using `--download-beat-saver-song MAP_ID --target SLOT_ID --pcm16 --no-pad --convert-to-v3 --deploy` deployed all 11 songs individually, then `build_deploy_all38.py` consolidated pack metadata, catalog, and redirects. Mode selectors confirmed driven by PACK bundle preview sets. Pipeline v0.5328 fully operational with Britney Spears pack deployment.ng at gameplay load (log ends right after level-file open, before environment/audio opens). v0.5328 adds normalize_v3_schema() at both injection points + empty-difficulty rescue via populated Standard donor; 571/571 tests incl. Roni-source regression. Full rebuild+redeploy running via build_deploy_all38.py. Next: user re-tests Chromeo, then fresh-pack generalization test.
- **EXP 192 (v0.5323): OneSaber mode FIXED** — notes were forced to the WRONG (LEFT/red) saber; now RIGHT/blue (2026-08-16). User did real in-headset play: **90° and No-Arrows are fun and working**; OneSaber was broken because `_generate_one_saber` used `_ONE_SABER_COLOR = 0` (LEFT/red) while OneSaber is played with the RIGHT (blue) saber — so every red note was unplayable. **FIXED:** flipped `_ONE_SABER_COLOR = 1` (RIGHT/blue) in `tools/full_custom_song_pipeline.py`; regenerated all 33 buggy red OneSaber `.dat` files from their Standard sources via `development/scripts/regenerate_onesaber_blue.py` (15 already-blue/mapper-authored maps untouched; **0 red OneSaber files remain**). Captured durable knowledge in new KB page [[saber-colors-and-one-saber]] (LEFT=Red, RIGHT=Blue; OneSaber is RIGHT/blue-only). 451/451 tests. **SOURCE `.dat` FIXED — NEXT: rebuild + redeploy the 38 custom-song bundles** so the corrected blue OneSaber notes reach the PS4 (pack bundles are unaffected — pack OneSaber clones Standard, not generated).
- **EXP 191 (v0.5322) context:** "STILL crashes" was root-caused to the fixed catalog NEVER being deployed (stale broken build on PS4). Deployed fixed catalog (md5 `975bacca…`, 0 invalid) + hardened `--verify-ps4` (check #7 validates deployed catalog dataIndex integrity + md5 + per-pack CRC/size). Removed legacy `pack_bundle` prototype from default config.
- v0.8040 `open()` hook redirects `aa/catalog.json` (OPEN #58 confirmed in Exp 178)
- Fresh `catalog_startmeup_modes.json` with correct dec-stream CRC (`0xe9e40bd3`) + size (7,905,425)
- Patched `startmeup_pack_modes.bundle` adds 3 preview sets (OneSaber/NoArrows/90Degree) to StartMeUp BeatmapLevelSO — all 4 now point at correct characteristics
- In-game mode selector for Start Me Up shows **Standard / OneSaber / NoArrows / 90Degree** (90Degree visible pending boot test)
- **Pipeline v0.5315:** standard command now produces full-length, lossless, all-modes bundles with zero flags; `--hevag`/`--vorbis`/`--pad-fsb5`/`--disable-beatmap-mode-mapping`/`--no-convert-to-v3`/`--skip-mode-generation` opt out; `--features-only` deploys runtime flags standalone; `features.json` holds only the 2 runtime flags the v0.8040 plugin reads

**Key findings since last summary:**
1. **Catalog redirect avenue CONFIRMED (Exp 178):** byte-identical `catalog_test.json` + `"aa/catalog.json": "catalog_test.json"` redirect → boot stable, `[OPEN #62] ... -> REDIRECTED` confirmed.
2. **CRC root cause SOLVED (Exp 179):** catalog `m_Crc` = `zlib.crc32` of the bundle's **DECOMPRESSED stream**, not the compressed file (original file CRC `0x63520032` vs catalog `0xdc8b314f` = dec-stream CRC). GF(2) padding forcing obsolete — just write actual values into fresh catalog.
3. **Exp 179 patched pack bundle BUILT + DEPLOYED + CONFIRMED:** `startmeup_pack_modes.bundle` (7,905,425 B, dec-stream CRC `0x8e1f8937`) — StartMeUp BeatmapLevelSO blob 440→1,028 B with 4 preview sets; identity preserved; 81/81 objects parse. Fresh `catalog_startmeup_modes.json` differs from original ONLY in rolling-stones entry. Build tool: `development/scripts/build_startmeup_pack_modes.py`.

**Known issue (2026-08-08 → FIXED 2026-08-09):** NoArrows bug ROOT-CAUSED + FIXED (Exp 181): two bugs in `_create_text_asset_object()` — `type_id=0` mapped new TextAssets to MonoScript(115) instead of TextAsset(49), and manual `struct.pack` used null terminators + `len+1` instead of Unity's `write_aligned_string` format (int32 length + data + 4-byte alignment). Fix: use `EndianBinaryWriter.write_aligned_string()` for `m_Name` and `write_int(len) + write(bytes) + align_stream(4)` for `m_Script`; set `type_id` to actual index from `cab.types`. All 381 tests pass; NoArrows verified to have dots (d=8) at all 5 difficulty levels.

**New finding (Exp 182, 2026-08-09):** Characteristic pathIDs were mislabeled across the whole codebase. Verified real BeatmapCharacteristicSO PIDs from `sharedassets_assets_all_068cd59e9a6fba13da706dc9269bf759.bundle` (CAB `cb38b3e2985c65d4cf8a63437da74a89`): Standard=`-7286399427822119286`, OneSaber=`-5623662769225589684`, NoArrows=`-8583864861369561029`, 90Degree=`-5995858427784384822`, 360Degree=`4533580413116749821`. The 90Degree preview slot previously pointed at the 360Degree characteristic (`requires360=1`) → game hid the button. OneSaber/NoArrows swap was cosmetic (each pid drives its own button AND gameplay lookup). All maps fixed, pack bundle rebuilt + deployed.

## Current Approach: MoveNext() Data Source Modification + Song ID Pipeline + Beatmap Mode Mapping (pipeline v0.5312 / plugin v0.8040)

**The old string-content memory injection (v0.66–v0.8024) is DEAD** — 0 strings found across 16MB–17GB.

**Working approach (metadata):** Hook `MoveNext()` of the `SetDataFromLevelAsync` state machine (RVA 0x1D377C0). Modifies `BeatmapLevel.songName`/`songAuthorName` in-place before the original code reads them. Pipeline reads exact game strings from `beat_saber_song_ids.json` to ensure correct casing.

**Mode mapping (Phase 1):**
- **Phase 1 (pipeline v0.5307):** Per-song bundle `_difficultyBeatmapSets` injected with 5 modes (Standard, OneSaber, NoArrows, 90Degree) via `--enable-beatmap-mode-mapping`. Controls gameplay data. ✅ Deployed and playing.
- **Phase 2 (Plugin runtime RAM scanning):** Concluded DEAD END (Exp 170–173) due to asynchronous Addressables unloading, multi-minute UI freezing, and PS4 tracking constraints. Abandoned in favor of Phase 1 pipeline bundle patching.

### Known Limitation (v0.8040)
- **Artist blanking is global** — "The Rolling Stones" → " " affects all songs with that artist string. Works for single-artist packs (Rolling Stones, Billie Eilish, Lizzo) but would be inaccurate for multi-artist packs. Currently only single-artist packs are targeted.

### Key Breakthroughs

1. **Module discovery timing**: At `module_start()` only 3 modules visible. IL2CPP loads later. Defer to `open_hook()`, retry until found (open #10-11).
2. **DetourMode**: Use `DetourMode_x64`, NOT x32. x32 splits IL2CPP instructions → crash.
3. **Signal-protected extraction — REVISED (v0.8045)**: Signal handlers are process-wide and Unity's GC throws page-protection SIGSEGV/SIGBUS faults during UI rendering — installing handlers while rendering crashes the game (v0.8043/44). Safe reads now use **`sceKernelQueryMemoryProtection`** (no faults). Reserve signal probing for quiescent moments (song-start redirect hook, v0.74–v0.8008).
4. **String replacement works**: `create_il2cpp_string()` with klass pointer copy creates valid replacement strings.
5. **External metadata**: `song_metadata.json` replaces hardcoded C array. Same JSON pattern as `redirects.json`.

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Hook TMP_Text.set_text (not memory scan) | Memory injection failed across ALL regions after 14+ versions |
| DetourMode_x64 (14-byte JMP) | IL2CPP instructions are variable-length; x32 mode splits instructions |
| SysV AMD64 calling convention | PS4 uses SysV, not MS ABI — `this` in RDI, `value` in RSI |
| Feature flag gating | `enable_song_metadata_modification` controls hook installation + metadata loading |
| External JSON config | Same pattern as `redirects.json` — `parse_json_pairs()` for flat key/value |
| "Name / Artist" combined format | Single replacement field for both song name and artist — works for single-artist packs |

### TextMeshPro Hook Architecture

- **Hook 1:** `TMP_Text.set_text(string)` — RVA `0x2D35BE0` (virtual Slot 66 property setter) — catches details panel, pause menu
- **Hook 2:** `TMP_Text.SetText(string, bool)` — RVA `0x2D3E1D0` (non-virtual, explicit bool overload) — catches song list names (but replacement overwritten)
- **Hook mode:** `DetourMode_x64` (14-byte JMP)
- **Calling convention:** SysV AMD64 — `this` in RDI, `value` in RSI, `method` in RDX
- **Module discovery:** `sceKernelGetModuleList` with 256-module buffer
- **Metadata source:** `/data/GoldHEN/AFR/CUSA12878/song_metadata.json`
- **Metadata format:** `{"song_names": {"original": "replacement"}, "song_artists": {"original": "replacement"}}`

## Key Technical Findings

### 🔴 Klass Pointer Approach is BROKEN (v0.8015 — CRITICAL)

After 10+ versions of trying different ranges, diagnostic logging, and timing strategies:

- **Klass struct found at `0x2012007E0`** — verified via metadata search (global-metadata.dat magic `0xFAB11BAF`)
- **0 objects found with this klass as first 8 bytes** — scanned 4GB–17GB (262K pages, 41K mapped), zero matches
- **Root cause:** PS4 IL2CPP likely uses compressed pointers (32-bit offsets) or indirect klass references instead of raw 64-bit pointers
- **Alternative:** Objects may not be instantiated at scan time (lazy loading — only created when song list UI displays)

**Do not pursue klass-based scanning further.** The evidence is conclusive.

### Bounds Check Bug (v0.66–v0.71 — Real Root Cause)

**The bug was NOT mincore, msync, or signal handlers.** It was a bounds check rejection:

```c
// WRONG — 0x100000000 = 4GB, but PS4 modules load at ~2GB
if (addr < 0x100000000ULL || ...) return 0;  // Rejected ALL module reads!
```

PS4 module segments from `sceKernelGetModuleInfo` return addresses like `0x806C0000` (~2GB). These were rejected by the bounds check before any probing method could execute.

**Fix (v0.72):** Lower bound changed to `0x1000000` (16MB) — accepts all valid user-space addresses while rejecting null pointers.

See [[ps4-memory-layout-for-module-scanning]] for full details.

### Plugin Deploy Path

Plugins MUST go to `/data/GoldHEN/plugins/` (configured by `/data/GoldHEN/plugins.ini`). The AFR directory `/data/GoldHEN/AFR/CUSA12878/` is for asset bundles only. Uploading to the wrong path cost several test cycles (v0.71).

See [[ps4-file-system-redirects]] for deploy path details.

## Recent Experiment Timeline

| Exp | Version | What | Result |
|-----|---------|------|--------|
| 167 | v0.66 | Initial memory injection implementation | ✅ Code complete, PC prototype verified |
| 168 | v0.67 | Thread removed → hook-triggered, mincore added | ✅ CE-34878-0 fixed, but "Class string not found" |
| 169 | v0.68 | Static log_write, removed pack bundle redirect | ✅ Boots fine, still "Class string not found" |
| 170 | v0.69 | Guard timer removed, trigger widened, mincore→msync | Same error — syscall stubs suspected |
| 171 | v0.70 | msync deployed and tested | Same error — but bounds check was the real issue |
| 172 | v0.70 test | User tested 2 songs | ❌ "Class string not found" |
| 173 | v0.71 | Signal handlers + VERBOSE_LOG + deploy path fix | 🔍 **VERBOSE_LOG revealed bounds check bug** |
| 174 | v0.72 | Bounds check fixed (4GB→16MB) | ✅ try_read_mem works, but string NOT in module |
| 175 | v0.73 | Pattern matcher (full heap scan) | ❌ Black screen hang — scan too slow |
| 176 | v0.74–v0.75 | Optimized scan + dump analysis | 🔵 **Class names in global-metadata.dat discovery** |
| **177** | **v0.76** | **String ptr validation threshold 4GB→16MB** | **✅ Consistent bounds — real fix for "found nothing"** |
| **178** | **v0.77–v0.79** | **Stack overflow fix + STRDEBUG** | **✅ 1MB→64KB stack, finds 17 candidates. String layout mismatch** |
| 188 | v0.8009 | Gap scan between GC heap and metadata | ❌ 60-second soft lock — gap scan disabled |
| 189 | v0.8010 | Direct string content search (no klass needed) | 🔄 Pivoted to string search approach |
| 128 | v0.8012 | Feature flags system | ✅ Implemented and tested on PS4 |
| 129 | v0.8013 | Pack bundle detection + offset probing | ❌ Fired at startup (multi-min freeze), 0 objects found in 256MB |
| 130 | v0.8014 | Diagnostic logging + scan timeout | ❌ Timing wrong (fires on song start), objects not in 8GB–8.25GB |
| **131** | **v0.8015** | **Wide-range scan 4GB–17GB + timing fix** | **❌ FAILED — 2min black screen, 0 objects. Klass approach ABANDONED** |
| **132** | **v0.8016** | **String content search + background thread** | **❌ CRASH — scePthreadCreate in hook unsafe** |
| **133** | **v0.8017** | **Synchronous string scan, 5s timeout** | **❌ 160s hang — 32 redirects × 5s retry storm** |
| **134** | **v0.8018** | **2s timeout, no retry** | **⚠️ No hang, but strings not in memory at pack load** |
| **135** | **v0.8019** | **Diagnostic redirect logging** | **⚠️ No hang, but scan range too large, strings not reached** |
| **136** | **v0.8020** | **Metadata region scan (±256MB)** | **❌ Strings NOT in metadata mmap. Found full file-open sequence** |
| **137** | **v0.8021** | **Trigger at Rolling Stones pack load** | **❌ Strings not in metadata mmap** |
| **138** | **v0.8022** | **Scan both GC heap AND metadata** | **❌ 5275 pages, 0 strings** |
| **139** | **v0.8023** | **Trigger at BeatmapLevelsData redirect** | **❌ 5276 pages, 0 strings** |
| **140** | **v0.8024** | **Scan four memory ranges (16MB–8GB)** | **❌ 7021 pages, 0 strings. Strings not in any region** |
| **142** | **v0.8027** | **TMP_Text hook + 256-module buffer** | **❌ Only 3 modules at module_start()** |
| **143** | **v0.8028** | **Deferred hook to open_hook()** | **❌ Still 3 modules at first open** |
| **144** | **v0.8029** | **Retry module discovery** | **❌ Hook installed but double-hook crash** |
| **145** | **v0.8030** | **Stop retry + DetourMode_x32** | **❌ Crash — DetourMode_x32 splits instructions** |
| **146** | **v0.8031** | **DetourMode_x64, minimal callback** | **✅ Hook fires correctly, no crash** |
| **147** | **v0.8032** | **Add string reading back** | **❌ Crash — extract_utf16_string on invalid pointer** |
| **148** | **v0.8033** | **Signal-protected extraction** | **✅ Matches found! Rolling Stones → Sabrina Carpenter** |
| **149** | **v0.8034** | **Phase 3 string replacement** | **✅ Pause menu PERFECT, song list partially works** |
| **150** | **v0.8035** | **use-after-free fix, 13-entry replacement table** | **✅ Details panel, pause menu, artist blanking all work** |
| **151** | **v0.8036** | **External song_metadata.json** | **✅ Works. Song details/pause menu correct, artist blanking in song list** |
| **152** | **v0.8037** | **SetText hook for song list names** | **⚠️ Hook fires, replacement applied, but song list re-renders from data model — names still original** |
| **153** | **v0.8038** | **SetDataFromLevelAsync hook (data source mod)** | **❌ Hook never fired — async wrapper inlined by builder. Zero log entries.** |
| **154** | **v0.8039** | **Hook MoveNext() instead** | **✅ WORKS! Song list names replaced for 21/32 songs. Missing 11 had case mismatches.** |
| **155** | **v0.8040** | **Case fix + song IDs pipeline** | **✅ ALL 32 SONGS CONFIRMED WORKING. Pipeline reads exact game strings from beat_saber_song_ids.json.** |
| **156** | **v0.8040** | **Full validation: 32/32 songs replaced correctly** | **✅ SUCCESS — Camellia Music Pack replacement identified as next test target.** |
| **157** | **v0.5304** | **CI/CD Infrastructure fix** | **✅ Fixed failing Ruff lint pipeline error.** |
| **158** | **v0.5305** | **Camellia Pack Replacement** | **✅ SUCCESS — All 6 Camellia DLC songs replaced with custom songs and deployed.** |
| 160 | v0.5307+v0.8041 | Beatmap Mode Mapping Phase 1 (pipeline) | ✅ 361 tests pass; detects modes, injects 5 _difficultyBeatmapSets per song |
| 161 | v0.5307 | drop pop candy build (modes) | 🔲 Bundle built with 5 mode sets, awaiting deploy |
| 162 | v0.8042 | Phase 2: BeatmapLevelSO memory injection | 🔲 Plugin built; mode selector UI patch via RAM |
| 163 | v0.8042 | Deploy + user test | ❌ Song shows/metadata fine, mode selector still Standard-only; old plugin ran |
| 164 | v0.8043 | Fix scan trigger + filter + worker thread | 🔲 Scan never fired (levelID not "custom/"); now fires on any MoveNext, structural klass find, worker thread. Deployed — awaiting test |
| **165** | **v0.8043 test** | **User test — Solo entry** | **❌ INSTANT CRASH — worker thread's process-wide SIGSEGV handlers hijacked the game's GC page-protection faults on the main thread (siglongjmp to worker stack)** |
| **166** | **v0.8044** | **Synchronous scan (revert worker)** | **❌ CRASH AGAIN — same last-[MODE] log; proved handlers during song-list render crash regardless of thread. Root cause confirmed.** |
| **167** | **v0.8045** | **Signal-free scan (sceKernelQueryMemoryProtection)** | **✅ NO CRASH — syscall works (prot=0x3), but ❌ klass not found: mode_extract_string bug + range too narrow** |
| **168** | **v0.8046 test** | **Wide scan + string fix + diagnostics** | **✅ NO CRASH — but arrfail=25443 strfail=0: all candidates (0x1C2–0x1D5xxxxx, lid=packed floats) are pack-bundle data, not managed objects** |
| **169** | **v0.8047** | **Tighten pointer window + reorder checks + stage breakdown + raw64 dumps** | **🔲 Build 105,120 bytes, 361/361 pytest pass, deployed. Awaiting user test — expect diag to show whether ptrs drops (bundle data killed) or objects found** |
| **170** | **v0.8047 test** | **Full log re-analysis — root cause CONFIRMED: scan TIMING** | **✅ NO CRASH. Scan fired from first MoveNext (open #731) before any pack BSL deserialized; pack bundle re-opened at [OPEN #792] after all 22 cells rendered. ptrs=1984 strfail=1980 arrfail=4 — objects simply didn't exist. Offsets verified correct (dump.cs TypeDefIndex 11680).** |
| **171** | **v0.8048** | **Trigger timing fix: pack-data gate + retryable scans + song-start fallback** | **🔲 Built 105,120 bytes, 361/361 pytest pass. PS4 unreachable — deploy deferred. Awaiting deploy + user test.** |
| 172–174 | v0.8049–v0.8050 | Phase 2 scan refinement (dead end continued) | ❌ Scan timing/structural issues; PS4 tracking constraints → Phase 2 ABANDONED |
| 175 | v0.5308+v0.8050 | 360Degree purge → 4 modes | ✅ 360Degree removed pipeline-wide (PS4 ~90° camera can't do 360); 4 modes (Standard/OneSaber/NoArrows/90Degree), 229 tests pass |
| **176** | **v0.8050/51** | **STARTUP CRASH — root cause + restore** | **✅ ROOT CAUSED (`e18921b` manual memcpy hook + `hooks.cpp` re-enabled) → plugin restored to stable v0.8040 baseline (`a8a06f0`); 365 tests pass; redeployed; user-confirmed stable** |
| **177** | **v0.5310** | **Real mode generators + default fill-in** | **✅ Generators implemented (no-arrows/one-saber/90-degree, non-mutating, V2+V3); mode generation now Step 5a default fill-in; 17 generator tests (365 total pass); fresh `startmeup_v3` bundle (12,405,290 B) deployed. User test: clean boot + song loads, selector still Standard-only (expected). ⚠️ NEW: log proves catalog.json passes through open_hook → catalog redirect avenue re-opened.** |
| **178** | **v0.8040 (plugin) / 0.5310 (pipeline)** | **Catalog-redirect proof (byte-identical copy)** | **🔲 DEPLOYED + VERIFIED ON-DEVICE — awaiting user boot test. `catalog_test.json` (793,186 B, md5 `dc6e9303...`) + `"aa/catalog.json": "catalog_test.json"` redirect in place; confirm `[OPEN #58] ... -> REDIRECTED` + stable boot.** |
| **179** | **v0.8040 (plugin) / 0.5310 (pipeline)** | **Pack preview-set injection (4 modes)** | **🔲 BUILT + LOCALLY VERIFIED — `startmeup_pack_modes.bundle` (7,905,425 B, dec-stream CRC `0x8e1f8937`) + `catalog_startmeup_modes.json` (only rolling-stones entry changed). CRC root cause SOLVED: catalog `m_Crc` = zlib.crc32 of DECOMPRESSED stream. Deploy gated on Exp 178 boot confirmation.** |
| **180** | **v0.8040 / v0.5310** | **Exp 179 DEPLOYED + USER TEST — Mode Selector Gap CLOSED** | **✅ MODE SELECTOR GAP CLOSED (2026-08-08). All 4 modes visible (Standard/OneSaber/NoArrows/90Degree). 🔴 ISSUE FOUND: NoArrows mode shows arrows instead of dots — generator/injection bug. OneSaber/90Degree untested.** |
| **181** | **v0.8040 / v0.5311** | **NoArrows bug ROOT-CAUSED + FIXED** | **✅ FIXED (2026-08-09). Two bugs in `_create_text_asset_object()`: `type_id=0` → MonoScript(115) instead of TextAsset(49); manual `struct.pack` (null term + len+1) vs Unity's `write_aligned_string` (int32 len + data + 4-byte align). Fixed + verified: all 5 NoArrows diffs have dots (d=8). 381 tests pass. Deployed; on-device confirmed NoArrows+OneSaber working.** |
| **182** | **v0.8040 / v0.5312** | **90Degree root cause + pid correction + pack rebuild** | **✅ ROOT-CAUSED (2026-08-09): 90Degree had NEVER been visible — pack bundle's 90Degree preview slot pointed at the 360Degree characteristic (`requires360=1`, hidden by game). Characteristic pids mislabeled repo-wide; corrected all maps to verified values (Standard=`-7286399427822119286`, OneSaber=`-5623662769225589684`, NoArrows=`-8583864861369561029`, 90Degree=`-5995858427784384822`, 360Degree=`4533580413116749821`). Pack bundle rebuilt (7,905,425 B) + catalog regenerated (CRC 3924036563) + deployed. Regression test added. AWAITING BOOT TEST.** |
| **183** | **v0.8040 / v0.5314→0.5315** | **Safe defaults baked in + idempotency fix + full-audio rebuild** | **✅ (2026-08-11) v0.5314: PCM16 + no-pad + mode mapping + V2→V3 all default ON (each with oppose flags), `--features-only` mode added, `enable_beatmap_mode_mapping` removed from runtime features.json (build-time CLI feature). v0.5315: FIXED mode-mapping idempotency bug — re-running on a source dir with pre-existing generated mode `.dat` files silently fell back to cloning Standard refs instead of injecting TextAssets (gate required `song_dir AND generated_files`; now just `song_dir`). 405/405 tests. Regenerated stale 90Degree source files (`t`→`et` lighting fix, BPM 130). Rebuilt `startmeup_v3.bundle` (39,697,727 B, full 224.31s audio, all 22 TextAssets semantic-identical to verified bundle). 🔴 DEPLOY BLOCKED — PS4 FTP down.** |
| **184** | **v0.8040 / v0.5315** | **Chromeo source recovery from deployed PS4 bundles** | **✅ (2026-08-12) All 6 deleted Chromeo slots recovered: bundles pulled → TextAssets (gzip via `surrogateescape` decode) + audio (.resource subfile) extracted → V4 beatmaps decoded to V3.2.0 (`/tmp/opencode/reconstruct_chromeo_src.py`, merges `colorNotesData` via `i` index) → pipeline-ready `chromeo_backout/` dirs with `audio.fsb` + `Info.dat` (per-slot songName/artist/BPM). All 6 rebuilt via pipeline (Crystallized 59.2MB → WhatTheCat 37.8MB); `bpmData[0].eb` corrected, full audio preserved (Crystallized 14.9M samples ≈ 339s). CycleHit/Ghost kept original 3 OneSaber files.** |
| **185** | **v0.8040 / v0.5316** | **Mass re-run all 38 songs + generator V3-field fix** | **✅ (2026-08-12) 38/38 bundles built + verified (Standard 5/5 + 3 generated modes each). FIXED v0.5316: mode generators crashed with KeyError `'y'` on V3 beatmaps omitting `x`/`y`/`b` (valid V3, default 0) — "Take Me to the Beach" source (`livebythesword` + `IDidntChangeMyNumber`) + Oxytocin source. All generator field reads now `.get(..., 0)`. 407/407 tests (+2 regressions). `redirects.json` regenerated (39 redirects); `deploy_all38.sh` written. `deploy_all.sh` confirmed OUTDATED (13-slot, no mode mapping). 🔴 DEPLOY BLOCKED — PS4 FTP unreachable.** |
| **186** | **v0.8040 / v0.5316** | **Mass deploy all 38 songs to PS4** | **✅ (2026-08-12) `deploy_all38.sh` ran — all 38 bundles uploaded (sizes match local exactly), `redirects.json` (39 entries) verified on-device via cat+parse, `song_metadata.json` verified byte-identical. Plugin v0.8040 confirmed in `/data/GoldHEN/plugins/`. bs_log.txt absent (fresh reboot). AWAITING USER TEST: 6 Chromeo slots, new Billie songs (Oxytocin/NDA/ThereforeIAm), 90Degree across songs, full audio lengths.** |
| **187** | **v0.8040 / v0.5318** | **Redirect naming bug — VALUES pointed at stale `_v3`, not deployed `.bundle`** | **✅ FIXED + DEPLOYED (2026-08-13). Aug-13 redeploy uploaded 38 fresh builds as `<slot>_v3.bundle` (lowercase) but generated `redirects.json` still held `_v3` titlecase values → game opens VALUE verbatim (case-sensitive) → stale builds served. Single source of truth: `_deployed_bundle_name()` (canonical slot casing + `paths.afr_target_suffix`, default now `_v3.bundle`) + `_ensure_mass_song_redirects()` heals every per-song value on config save (keeps keys, fixes values, drops stale pre-`.bundle` entries, adds missing slots). `deploy_mass_bundles` uploads under `os.path.basename(local_path)`; `manage_redirect_config` dropped `bundle_suffix` param. Corrected `redirects.json` deployed + verified on PS4 (40 redirects, byte-match on-device). PS4 cleaned: `cleanup_ps4_stale.sh --yes` removed 58 stale files (old `_v3` builds, titlecase Camellia, old dirs, test artifacts, stale pack variants) — AFR dir 98→44 files. New `TestDeployedBundleNaming` (6 tests) — 419/419 pass. Pre-existing bs_log archived (v0.5316_preexisting_bs_log_2026-08-12.txt: 2 stable boots, pack REDIRECTED, no crashes). AWAITING USER BOOT TEST.** |

## Memory Injection Versions

| Version | Date | Key Changes |
|---------|------|-------------|
| v0.66 | 07-17 | Initial implementation (thread-based, direct memcpy) |
| v0.67 | 07-17 | Thread removed → hook-triggered, mincore safe reads |
| v0.68 | 07-17 | Removed pack bundle redirect (was causing boot crash) |
| v0.69 | 07-17 | Guard timer removed, trigger widened, mincore→msync |
| v0.70 | 07-17 | msync tested — same error (bounds check was real issue) |
| v0.71 | 07-19 | Signal handlers + VERBOSE_LOG + deploy path fix |
| v0.72 | 07-19 | Bounds check fixed: 4GB→16MB lower bound, signal handlers proved working |
| v0.73 | 07-19 | Pattern-based klass finding (full 8GB scan) — ❌ hang, too slow |
| v0.74 | 07-19 | Persistent signal handlers (once per scan), 256MB range — no klass found |
| v0.75 | 07-19 | Wide-range scan (1GB–32GB, coarse). Class names in metadata NOT module |
| v0.76 | 07-19 | String ptr threshold 4GB→16MB, scan 16MB–64GB |
| v0.77 | 07-19 | Per-check diagnostic counters (klass/ver/ptrs/strlen) |
| v0.78 | 07-19 | Fixed 1MB stack buffer → 64KB (was crashing every try_read_mem) |
| v0.79 | 07-19 | STRDEBUG logging for System_String layout on PS4 |
| v0.8008 | 07-19 | Close hook retry mechanism |
| v0.8009 | 07-19 | Gap scan between GC heap and metadata — ❌ 60s hang, disabled |
| v0.8010 | 07-19 | Direct string content search (no klass needed) |
| v0.8011 | 07-19 | Optimized string search (8× faster, dual-format) |
| v0.8012 | 07-19 | Feature flags system (features.json) |
| v0.8013 | 07-20 | Pack bundle detection + string length offset probing |
| v0.8014 | 07-20 | Diagnostic logging + scan timeout |
| **v0.8015** | **07-21** | **Wide-range scan 4GB–17GB, pack bundle timing, string search disabled** |
| **v0.8016** | **07-21** | **String content search + background thread — CRASH (thread in hook unsafe)** |
| **v0.8017** | **07-22** | **Synchronous string scan, 5s timeout, retry on failure** |
| **v0.8018** | **07-22** | **2s timeout, no retry, scan once** |
| **v0.8019** | **07-22** | **Diagnostic redirect logging — 288 pack_assets_all detections, only 2 redirects** |
| **v0.8020** | **07-22** | **Metadata region scan (±256MB), comprehensive file-open logging** |
| **v0.8021** | **07-23** | **Scan trigger moved to therollingstones_pack_assets_all (OPEN #738)** |
| **v0.8022** | **07-23** | **Scan both GC heap AND metadata mmap** |
| **v0.8023** | **07-23** | **Trigger at BeatmapLevelsData redirect (OPEN #740)** |
| **v0.8024** | **07-23** | **Scan four memory ranges (16MB–8GB + metadata), 15s timeout** |

## Next Steps

1. **Exp 178 boot test (COMPLETED):** user boots PS4; pull `bs_log.txt`, confirm `[OPEN #58] ... -> REDIRECTED` and stable boot. Archive log + clear file. ✅ DONE.
2. **Exp 179 deploy + test (COMPLETED):** ✅ DONE — mode selector gap closed. NoArrows bug found.
3. **Exp 181 fix deploy (COMPLETED):** ✅ DONE — NoArrows dots + OneSaber confirmed on-device (Aug 9).
4. **Exp 182 boot test (COMPLETED):** ✅ DONE — user confirmed 90Degree + all 4 modes working on Hard; 90Degree Expert source lane behavior confirmed (Aug 11 Espresso boot test).
5. **Exp 183 deploy + Espresso test (COMPLETED):** ✅ Espresso → `startmeup` deployed as `startmeup_v3` (30,889,589 B); user boot test PASSED (full 224.31s audio, 4 modes on Hard, 90Degree Expert, lighting `et` events — "worked perfectly, exactly as I envisioned").
6. **Exp 184/185 deploy (COMPLETED):** ✅ `deploy_all38.sh` ran 2026-08-12 — all 38 bundles + config on PS4, verified. **USER TEST PENDING** (Chromeo slots, new Billie songs, 90Degree, full audio). After test: pull + archive `bs_log.txt`, record results in song_testing_log.md.
7. **Exp 187 PS4 deploy + cleanup (COMPLETED):** ✅ Deployed corrected `redirects.json` (verified on-device), cleaned 58 stale PS4 files (AFR dir 98→44), re-verified all 40 targets + pack pair. Pre-existing log archived + cleared. **USER BOOT TEST PENDING** — confirm all 38 songs load NEW `.bundle` builds (Chromeo slots, new Billie songs, 90Degree, full audio). After test: pull + archive `bs_log.txt`, record results in song_testing_log.md.
8. **Generalized pack patch into production pipeline (COMPLETED + CRASH FIXED + REPRODUCIBLE + DEPLOYED):** ✅ v0.5319 (Exp 188) — `tools/build_pack_mode_bundles.py` + `pack_modes` config block + CLI flags; all 36 packs patched (303 BeatmapLevelSOs, 4 modes × 5 diffs), manifest + merged catalog; 440/440 tests. **DEPLOYED to PS4 (2026-08-14)** — 4 packs (rollingstones/billieeilish/lizzo/camellia) + merged catalog + 43-redirect config. **❌ USER BOOT TEST CRASHED** (Exp 189, v0.5320): stale `m_EntryDataString` dataIndexes (rec[4] byte offsets into m_ExtraDataString not shifted when lizzo's block grew +6 B → 70/2251 garbage). Fixed in `update_catalog_entry()` + `_parse_catalog_block()` regex; 444/444 tests. **✅ REPRODUCIBILITY (Exp 190, v0.5321):** all 36 packs rebuild byte-identical from the production module (leftover `"360Degree"` pid in `CHAR_PATH_IDS` removed); 445/445 tests. **✅ EXP 191 (v0.5322, 2026-08-16): "STILL crashes" root cause = the fixed catalog was NEVER deployed** — the PS4 still ran the broken v0.5319 catalog (70/2251 invalid dataIndexes, md5 `0eb8a27d…`; fixed = `975bacca…`), same crash signature (OPEN #58/#74 after catalog redirect). Deployed the fixed catalog (verified on-device: 0 invalid, all 4 pack CRCs/sizes OK), deleted stale prototype files (`catalog_startmeup_modes.json`, `startmeup_pack_modes.bundle`), **hardened `--verify-ps4` with catalog content validation (check #7**: dataIndex integrity + md5 + per-pack CRC/size — the broken/fixed catalogs are same byte size, so size checks alone can never catch a stale catalog), and removed the legacy `pack_bundle` prototype from the DEFAULT config. 451/451 tests. **USER BOOT TEST PENDING** — boot should now be stable through the catalog redirect + pack scan.
9. **Expand mode generation coverage** — confirm `--skip-mode-generation`, `--one-saber-min-gap`, `--rotation-cycle-beats` behavior end-to-end.

## Active Knowledge Gaps

1. ~~CRC validation blocked~~ → **SOLVED** via memory injection (bypasses CRC entirely)
2. ~~Size validation blocked~~ → **SOLVED** via memory injection (bypasses size entirely)
3. ~~Class string not found~~ → **SOLVED**: Class name strings in global-metadata.dat (v0.75)
4. ~~IL2CPP heap address on PS4~~ → **KNOWN**: Klass at 0x2012007E0, metadata at 0x293280000. Objects NOT in 4GB–17GB (klass pointer approach broken)
5. ~~Field offsets~~ → **UNVERIFIED** but may not matter if string content search works
6. ~~Timing~~ → **TESTED**: Scanned at pack load (OPEN #738) and BeatmapLevelsData redirect (OPEN #740). Strings not found at either time.
7. ~~String location~~ → **NOT FOUND**: Strings NOT in any scanned region (16MB–8GB + metadata). Memory injection approach abandoned.
8. ~~Memory injection~~ → **🔴 DEAD END**: Failed across all memory regions after 14+ versions. Code removed in v0.8025.
9. ~~TextMeshPro hook~~ → **✅ PROVEN WORKING**: Hook fires, strings read, replacements displayed in pause menu (v0.8034).
10. **Song details "?" issue** → **IN PROGRESS**: `create_il2cpp_string()` works for pause menu but shows "?" for song details name. Possible encoding or klass mismatch.
11. **Selective replacement** → **TODO**: Currently replaces in ALL TMP_Text calls. Need Phase 2 pointer tracking to identify song name vs artist fields.

## References

- [[memory-injection-addressables-bypass]] — Full memory injection architecture
- [[ps4-memory-layout-for-module-scanning]] — Memory layout and bounds check details
- [[ps4-file-system-redirects]] — Deploy paths (plugins vs AFR)
- [[plugin-architecture]] — Build system and component overview
- [[development-workflow]] — Edit-build-deploy-test cycle
