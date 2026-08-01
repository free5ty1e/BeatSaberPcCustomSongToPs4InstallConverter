# Project Summary: Beat Saber PS4 Custom Song Support
**Last Updated:** 2026-07-31
**Status:** 🏗️ **Beatmap Mode Mapping Phase 2 IN PROGRESS (pipeline v0.5307 / plugin v0.8046).** v0.8045 test: NO crash (signal-free `sceKernelQueryMemoryProtection` works), but `klass not found` — a `mode_extract_string` length-selection bug + too-narrow scan range. v0.8046 fixes both + adds scan diagnostics. Deployed, awaiting user test.

## Current Approach: MoveNext() Data Source Modification + Song ID Pipeline + Beatmap Mode Mapping (v0.5307)

**The old string-content memory injection (v0.66–v0.8024) is DEAD** — 0 strings found across 16MB–17GB.

**Working approach (metadata):** Hook `MoveNext()` of the `SetDataFromLevelAsync` state machine (RVA 0x1D377C0). Modifies `BeatmapLevel.songName`/`songAuthorName` in-place before the original code reads them. Pipeline reads exact game strings from `beat_saber_song_ids.json` to ensure correct casing.

**Mode mapping (Phase 1 + Phase 2):**
- **Phase 1 (pipeline v0.5307):** Per-song bundle `_difficultyBeatmapSets` injected with 5 modes (Standard, OneSaber, NoArrows, 90Degree, 360Degree). Controls gameplay data. ✅ Deployed and playing.
- **Phase 2 (plugin v0.8046):** Mode selector UI reads `BeatmapLevelSO._previewDifficultyBeatmapSets` (offset 0x98) from the pack bundle — blocked by Addressables CRC. Revived a **targeted** memory injection: scan 16MB–64GB + 8–8.25GB for BeatmapLevelSO objects (klass-range + version 1-50 + valid string ptrs + valid preview array), then atomically replace the preview array with 5 mode entries at runtime. Runs synchronously in the MoveNext hook. **v0.8046 = signal-free**: safe reads via `sceKernelQueryMemoryProtection` (v0.8045 test PROVED no crash + syscall works). v0.8046 widens the range to 16MB–64GB @1MB pages (v0.77-proven coverage), fixes a `mode_extract_string` length bug, and logs per-check scan diagnostics.

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
| **168** | **v0.8046** | **Fix string bug + widen range + diagnostics** | **🔲 string-len fix, 16MB-64GB@1MB scan, Scan diag counters. Deployed — awaiting test** |

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

1. **Test v0.8046 mode selector** — restart game, open Start Me Up, check for OneSaber/NoArrows/90Degree/360Degree. Pull `bs_log.txt` (now cleared after each pull) for `[MODE]` entries: `cand klass=...` lines + `Scan diag: ok=... klass=... ver=... ptrs=... arrfail=... strfail=...` will pinpoint which check rejects candidates and where they live. If `klass=0` for all checks, adjust scan range/stride.
2. **If klass found but 0 BSL collected** — collector same range as finder; check `mode_preview_arr_ok` strictness.
3. **If BSLs found but no 5 BeatmapCharacteristicSO** — widen the ±16MB neighbor scan or find charSOs from a known pack.
4. **If mode selector appears** — test 90Degree/360Degree gameplay (Phase 1 uses Standard patterns; unique .dat beatmap data still needs per-mode TextAsset compilation — roadmap M5).
5. **Expand replacement table** — Register metadata for additional DLC packs beyond the current 38 slots.
6. **CI integration test wiring** — Wire `test_integration.py` mock dump structure into `.github/workflows/ci.yml` for automated integration testing.

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
