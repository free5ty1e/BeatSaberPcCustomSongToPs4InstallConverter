# Project Summary: Beat Saber PS4 Custom Song Support
**Last Updated:** 2026-07-23
**Status:** 🔴 **Memory injection approach may not be viable (v0.8024).** After 14+ versions and scanning every memory region (16MB–8GB + metadata mmap), 0 strings found. Strings don't exist in scannable memory at scan time. Need fundamentally different approach.

## Current Approach: Synchronous String Content Search (v0.8024)

**The klass pointer approach is broken.** After 10+ versions, we know:
- Klass struct found at `0x2012007E0` via metadata search
- 0 objects found with this klass as first 8 bytes in 4GB–17GB range
- PS4 IL2CPP uses compressed/indirect klass pointers

**String content search also appears broken.** After 6+ versions scanning different ranges, 0 strings found:
- GC heap (8–8.25GB): 0 strings
- Metadata mmap (10.5–10.8GB): 0 strings
- Low memory (16MB–4GB): 0 strings
- Extended heap (4–8GB): 0 strings

**Root cause hypothesis:** Strings are loaded on-demand when song list UI renders, not during startup when scan fires. The scan runs at BeatmapLevelsData redirect (OPEN #740) but the song list UI may not render until much later.

1. **Synchronous scan** — Runs in hook callback with 15-second timeout (no threads — unsafe in PS4 hook context)
2. **Search for strings** — Scan for UTF-16LE/UTF-8 patterns matching original song names
3. **Patch in-place** — Overwrite string content with custom names
4. **Feature flag gated** — All behind `enable_song_metadata_modification`
5. **Scan once** — On failure, `g_patching_done = -1` (permanent stop)

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| String content search (not klass) | Klass pointer approach broken after 10+ versions |
| Synchronous scan (not thread) | `scePthreadCreate` in hook callback causes CE-34878-0 crash (v0.8016) |
| 10-second timeout | Enough for 512MB scan, prevents indefinite hook blocking |
| Scan once, no retry | Prevents multi-minute hang from retry storm (v0.8017) |
| UTF-16LE pattern matching | Direct — search for WHAT we want to modify |
| Feature flag gating | All memory injection behind `enable_song_metadata_modification` flag |
| Trigger at Rolling Stones pack | Scan must fire AFTER pack bundle loads (OPEN #738), not at first pack_assets_all (OPEN #207) |

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

1. **🔴 Reconsider approach** — Memory injection string search has failed across ALL memory regions after 14+ versions. Strings not found in 16MB–8GB or metadata mmap.
2. **Alternative: Hook Unity rendering** — Intercept string display at the UI rendering level
3. **Alternative: Modify pack bundle directly** — Patch pack bundle file contents before Addressables loads it
4. **Alternative: Trigger scan later** — Hook into song list UI population to fire scan when strings are actually in memory
5. **Expand metadata table** — Register metadata for all 32 DLC slots (if approach is viable)

## Active Knowledge Gaps

1. ~~CRC validation blocked~~ → **SOLVED** via memory injection (bypasses CRC entirely)
2. ~~Size validation blocked~~ → **SOLVED** via memory injection (bypasses size entirely)
3. ~~Class string not found~~ → **SOLVED**: Class name strings in global-metadata.dat (v0.75)
4. ~~IL2CPP heap address on PS4~~ → **KNOWN**: Klass at 0x2012007E0, metadata at 0x293280000. Objects NOT in 4GB–17GB (klass pointer approach broken)
5. ~~Field offsets~~ → **UNVERIFIED** but may not matter if string content search works
6. ~~Timing~~ → **TESTED**: Scanned at pack load (OPEN #738) and BeatmapLevelsData redirect (OPEN #740). Strings not found at either time.
7. **String location** → **NOT FOUND**: Strings NOT in any scanned region (16MB–8GB + metadata). After 14+ versions, strings are conclusively not in scannable memory at scan time.
8. **Memory injection** — **🔴 LIKELY NOT VIABLE**: String content search failed across all memory regions. Need fundamentally different approach.

## References

- [[memory-injection-addressables-bypass]] — Full memory injection architecture
- [[ps4-memory-layout-for-module-scanning]] — Memory layout and bounds check details
- [[ps4-file-system-redirects]] — Deploy paths (plugins vs AFR)
- [[plugin-architecture]] — Build system and component overview
- [[development-workflow]] — Edit-build-deploy-test cycle
