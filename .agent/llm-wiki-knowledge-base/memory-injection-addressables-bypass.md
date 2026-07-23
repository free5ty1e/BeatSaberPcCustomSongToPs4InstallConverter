---
name: memory-injection-addressables-bypass
description: "Memory injection approach to bypass Addressables catalog CRC validation by patching BeatmapLevelSO in RAM — implemented as hook-triggered, signal-handler-based scanning with wide-range heap sweep"
metadata:
  type: reference
---

# Memory Injection — Addressables Catalog Bypass Approach

## Summary

When pack bundle modification is blocked by dual validation (m_BundleSize AND m_Crc), fallback to **memory injection**: patch BeatmapLevelSO objects in RAM after Addressables loads and validates the pack bundle. This bypasses catalog CRC validation entirely.

**Key Insight:** Addressables validates CRC LAZILY (when contents accessed, not during LoadFromFile). This gives us a window to patch objects in RAM before the game reads their metadata.

**Status:** 🔴 **Memory injection string search FAILED across all memory regions (v0.8024).** After 14+ versions scanning 16MB–8GB + metadata mmap, 0 strings found. Approach likely not viable. Need fundamentally different strategy.

## 🔴 CRITICAL: Klass Pointer Approach is Broken

After 10+ versions of trying different ranges, diagnostic logging, and timing strategies, the klass pointer search approach **fundamentally does not work on PS4 IL2CPP**:

- **Klass struct found at `0x2012007E0`** — verified via metadata search (global-metadata.dat magic `0xFAB11BAF`, class string at `0x2934BCB6E`)
- **0 objects found with this klass as first 8 bytes** — scanned 4GB–17GB (262K pages, 41K mapped), zero matches
- **Root cause:** PS4 IL2CPP likely uses compressed pointers (32-bit offsets) or indirect klass references instead of raw 64-bit pointers
- **Alternative:** Objects may not be instantiated at scan time (lazy loading — only created when song list UI displays)

**New approach (v0.8017):** Search for exact UTF-16LE song name strings ("Start Me Up", "The Rolling Stones") in memory and patch them in-place. Synchronous execution with 5-second timeout (no threads — unsafe in PS4 hook context). Retry on failure.

## Implementation — Current Architecture (v0.8024)

### Component Overview

```
open_hook (detects BeatmapLevelsData redirect at OPEN #740)
    │
    ▼
memory_inject_try_patch()  [gated behind g_feature_song_metadata_modification]
    │
    ├── [1] Install signal handlers (once per scan)
    │
    ├── [2] patch_strings_by_content() — scans FOUR ranges:
    │       │   Range 0: Low memory (16MB–4GB) — pack bundles, assemblies
    │       │   Range 1: GC heap (8–8.25GB) — IL2CPP objects
    │       │   Range 2: Metadata mmap (10.5–10.8GB) — string literals
    │       │   Range 3: Extended heap (4–8GB) — additional allocations
    │       │
    │       ├── Build lookup tables (UTF-16LE + UTF-8 patterns from metadata)
    │       ├── Scan memory at 64KB granularity with 15s timeout
    │       │   └── try_read_mem() with signal handlers for safe probing
    │       ├── Match string content against known original song names
    │       └── Patch matched strings in-place (UTF-16LE or UTF-8)
    │
    └── [3] Restore signal handlers
         └── Set g_patching_done = -1 on failure (permanent stop)
```

### Hook-Triggered Execution (Synchronous, No Threads)

Since v0.8017, the scan runs synchronously inside the `open_hook()` callback. Since v0.8023, the trigger is the first `BeatmapLevelsData` redirect (OPEN #740) — when the game actually reads song data:

- **Primary trigger:** `open_hook` detects BeatmapLevelsData redirect → calls `memory_inject_try_patch()`
- **Re-entrancy guard:** `g_patching_done` flag prevents multiple simultaneous scans
- **Scan once:** On failure, `g_patching_done = -1` (permanent stop, no retry)
- **Feature flag:** All memory injection gated behind `g_feature_song_metadata_modification`
- **Signal handlers:** Installed once at scan start, restored at end
- **Timeout:** 15-second hard limit for wider scan range

### Memory Probing (try_read_mem)

```c
static int try_read_mem(uint64_t addr, void* buf, size_t size) {
    // Bounds: accept 16MB–128GB (modules ~2GB, IL2CPP heap may be below 4GB)
    if (addr < 0x1000000ULL || addr > 0x2000000000ULL) return 0;
    if (addr + size > 0x2000000000ULL || addr + size < addr) return 0;

    int result = 0;
    if (sigsetjmp(g_mem_jmpbuf, 1) == 0) {
        memcpy(buf, (void*)addr, size);
        result = 1;
    }
    return result;
}
```

Signal handlers are installed once at the start of `memory_inject_try_patch()` — not per-call (v0.74). The handler does `siglongjmp(g_mem_jmpbuf, 1)` to safely recover from page faults.

### Stack Buffer Requirement

PS4 threads have a stack limit of ~256KB. All page buffers used for reading memory must fit within this limit:
- `SCAN_STEP = 0x10000` (64KB) — used by `scan_for_beatmap_level_objects()` — safe
- `PATTERN_SCAN_STEP = 0x10000` (64KB) — used by pattern matcher — safe
- `PATTERN_SCAN_STEP = 0x100000` (1MB) — v0.75–v0.77 bug: **overflowed stack, crashed all reads** (fixed v0.78)

## Field Offsets (from il2cpp dump)

```c
BeatmapLevelSO_o:
  0x00: klass (BeatmapLevelSO_c*)
  0x08: monitor (void*)
  0x10: m_CachedPtr (intptr_t)     — from UnityEngine.Object
  0x18: _version (int32_t)
  0x20: _levelID (System_String_o*)
  0x28: _songName (System_String_o*)
  0x30: _songSubName (System_String_o*)
  0x38: _songAuthorName (System_String_o*)
  0x40: _levelAuthorName (System_String_o*)
```

**Note:** These offsets are from an il2cpp.h dump and may differ from the actual PS4 layout. The v0.78 diagnostic found 17 candidates matching these offsets (klass range, version 1-50, 3 valid pointers), but ALL fail the string length check at `lid+0x10`. The System_String._stringLength may be at offset **0x14** on PS4 (with padding at 0x10), or may use a different encoding.

## Pattern Matcher Diagnostic Output (v0.77+)

The pattern matcher logs per-check failure counters:

```
[MEMINJ] Pattern diag: 65280 pages (1745 mapped). klass=128982 ver=78 ptrs=17 strlen=0
```

- **pages:** Total 64KB pages scanned (from 16MB to 4GB)
- **mapped:** Pages successfully read by try_read_mem
- **klass:** Candidates with klass ptr in [0x80000000, 0x90000000]
- **ver:** Candidates passing version check (1-50 at offset 0x18)
- **ptrs:** Candidates with 3 valid string pointers at offsets 0x20/0x28/0x38
- **strlen:** Candidates passing string length check at lid+0x10 (v0.78: **0 out of 17** — indicates wrong offset)

## Discovery: Class Name Strings NOT in Module (v0.75)

**Key finding from PS4 game dump analysis:** The "BeatmapLevelSO" class name is NOT compiled into the Il2CppUserAssemblies PRX as a C string. It exists only in `global-metadata.dat` (patch version, offset 0x23CB6E).

This means the string-search approach (v0.66–v0.71) searched the wrong memory region. The klass struct's `name` field points into the metadata buffer, NOT into the module's data section.

See [[ps4-il2cpp-metadata-loading]] for full analysis.

## Heap Address Is Unverified

The IL2CPP GC heap was assumed to be at `0x200000000–0x400000000` (8GB–16GB) based on typical PS4 Unity layout. The klass struct was found at `0x2012007E0` (8GB), but scanning 4GB–17GB (262K pages) found 0 objects with this klass as first 8 bytes. **The klass pointer approach is fundamentally broken on PS4 IL2CPP.**

## History — The Debugging Saga

| Version | Change | Result |
|---------|--------|--------|
| v0.66 | Initial memory injection (thread-based, direct memcpy) | Tested on PC prototype only |
| v0.67 | Thread removed → hook-triggered, mincore safe reads | CE-34878-0 fixed, but "Class string not found" |
| v0.68 | Removed pack bundle redirect (was causing boot crash) | Boots fine, still "Class string not found" |
| v0.69 | Guard timer removed, trigger widened, mincore→msync | Same error |
| v0.70 | msync tested | Same error — REAL issue: bounds check rejected all reads |
| v0.71 | Signal handlers + VERBOSE_LOG + deploy path fix | **Found bounds check bug** via verbose log |
| v0.72 | Bounds check fixed (4GB→16MB) | ✅ try_read_mem works! But **"Class string not found"** — string NOT in module |
| v0.73 | Pattern matcher added (full 8GB heap scan) | ❌ **Black screen hang** — scan too slow for hook callback |
| v0.74 | Optimized: persistent handlers, 256MB range | ✅ No hang. **Pattern found NOTHING** in 64MB heap range |
| v0.75 | Wide scan 1GB–32GB, coarse stepping | 🔵 **Pattern found NOTHING** — string ptr bounds mismatch |
| v0.76 | Fixed string ptr threshold 4GB→16MB, scan 16MB–64GB | ✅ Consistent bounds, but still found NOTHING (bug was 1MB stack) |
| v0.77 | Added per-check diagnostic counters (klass/ver/ptrs/strlen) | 🔍 **65280 pages, 1745 mapped, klass=128K ver=78 ptrs=17 strlen=0** |
| v0.78 | Fixed 1MB stack buffer → 64KB (was crashing every try_read_mem) | ✅ **Stack fix: try_read_mem now works! Pattern finds 17 candidates** |
| v0.79 | STRDEBUG logging for System_String layout on PS4 | 🔵 String length offset likely 0x18 on PS4 (16-byte monitor) |
| v0.8008 | Close hook retry mechanism | ✅ Retry fires on file close, but still 0 objects found |
| v0.8009 | Gap scan between GC heap and metadata | ❌ 60-second soft lock — gap scan disabled |
| v0.8010 | Direct string content search (no klass needed) | 🔄 Pivoted to string search approach |
| v0.8011 | Optimized string search (8× faster, dual-format) | 🔵 String search deployed, awaiting test |
| v0.8012 | Feature flags system | ✅ Implemented and tested on PS4 |
| v0.8013 | Pack bundle detection + offset probing | ❌ Fired at startup (multi-min freeze), 0 objects in 256MB |
| v0.8014 | Diagnostic logging + scan timeout | ❌ Objects not in 8GB–8.25GB, string search caused hang |
| **v0.8015** | **Wide-range scan 4GB–17GB + timing fix** | **❌ FAILED — 2min black screen, 0 objects found. Klass pointer approach ABANDONED** |
| **v0.8016** | **String content search + scePthreadCreate** | **❌ CRASH — thread creation in hook callback causes CE-34878-0** |
| **v0.8017** | **Synchronous string scan, 5s timeout, retry** | **❌ 160s hang — 32 redirects × 5s retry storm** |
| **v0.8018** | **2s timeout, no retry** | **⚠️ No hang, but strings not in memory at pack load** |
| **v0.8019** | **Diagnostic redirect logging** | **⚠️ 288 pack_assets_all detections, only 2 redirects logged** |
| **v0.8020** | **Metadata region scan (±256MB)** | **❌ Strings NOT in metadata mmap. Found full file-open sequence** |
| **v0.8021** | **Trigger at Rolling Stones pack load (OPEN #738)** | **❌ Strings not in metadata mmap** |
| **v0.8022** | **Scan both GC heap AND metadata** | **❌ 5275 pages, 0 strings. Strings not in GC heap or metadata** |
| **v0.8023** | **Trigger at BeatmapLevelsData redirect (OPEN #740)** | **❌ 5276 pages, 0 strings. Strings not found at redirect time** |
| **v0.8024** | **Scan four memory ranges (16MB–8GB + metadata)** | **❌ 7021 pages, 0 strings. Strings not in any scanned region** |

## Build & Deploy

### Building
```bash
make clean all          # release build
make clean DEBUG=1 all  # debug build (with VERBOSE_LOG)
```

### Deploy Path
The plugin MUST be deployed to `/data/GoldHEN/plugins/` (NOT `/data/GoldHEN/AFR/`):

```bash
# CORRECT deploy path
lftp -u anonymous, -p 2121 192.168.100.117 \
  -e "put beat_saber_deluxe_debug.prx -o /data/GoldHEN/plugins/beat_saber_deluxe.prx; quit"
```

### Log Retrieval
Log written to `/data/GoldHEN/AFR/CUSA12878/bs_log.txt`:
```bash
lftp -u anonymous, -p 2121 192.168.100.117 \
  -e "get /data/GoldHEN/AFR/CUSA12878/bs_log.txt -o bs_log.txt; quit"
```

### Clear Log
```bash
lftp -u anonymous, -p 2121 192.168.100.117 \
  -e "rm /data/GoldHEN/AFR/CUSA12878/bs_log.txt; quit"
```

## Key Lessons Learned

1. **🔴 Klass pointer approach is BROKEN on PS4 IL2CPP** — After 10+ versions, scanning 4GB–17GB (262K pages) found 0 objects with klass `0x2012007E0` as first 8 bytes. PS4 IL2CPP uses compressed/indirect klass pointers, or objects aren't instantiated until song list UI loads. **Do not pursue klass-based scanning further.**
2. **Always check bounds before probing** — VERBOSE_LOG the actual segment addresses first
3. **Module segments can be anywhere** — Don't assume they're above 4 GB
4. **Signal handling works for safe probing** — `sigaction` + `sigsetjmp`/`siglongjmp` works on PS4
5. **Syscall stubs are common** — `mincore` and `msync` are stubs on PS4; use signal handlers instead
6. **Keep all bounds checks in sync** — Changing `try_read_mem()` bounds requires updating ALL validation functions
7. **Stack buffer size matters** — PS4 thread stack ~256KB. 1MB buffers overflow silently (every try_read_mem faults)
8. **Class name strings in global-metadata.dat** — NOT in compiled module PRX
9. **System_String layout may differ on PS4** — `_stringLength` offset may not be at standard 0x10; dynamic probing added (0x10/0x14/0x18/0x1C)
10. **String content search is too slow for large ranges** — Scanning 12GB for string patterns causes multi-minute hangs; disable or cap range
11. **Pack bundle detection fires at startup** — `pack_assets_all` matches bundles loaded during game init, not just when user navigates to pack
12. **Feature flags essential for iteration** — All experimental features gated behind `features.json` flags for safe testing
13. **Search for WHAT you want to modify, not HOW it's stored** — Instead of searching for klass pointers (which are compressed/indirect), search for the actual song name strings we want to modify. This is more direct and avoids the klass pointer issue entirely.
14. **🔴 Thread creation in hook callbacks is UNSAFE on PS4** — Both `pthread_create` (v0.66) and `scePthreadCreate` (v0.8016) inside `open_hook` cause CE-34878-0 crashes. Hook callbacks run in a restricted context. Use synchronous execution with timeout instead.
15. **🔴 Scan timing is critical** — Scan must fire AFTER the target pack bundle loads, not at first pack_assets_all detection. The Rolling Stones pack loads at OPEN #738, but scan was firing at OPEN #207 (500+ file opens too early). By the time scan completes, the target pack hasn't loaded yet.
16. **🔴 Strings NOT in metadata mmap** — v0.8020 scanned ±256MB around 0x293280000, found 0 matches. String literals are heap-allocated System.String objects, not stored in global-metadata.dat region.
17. **Pack bundles load BEFORE song bundles** — The game opens hundreds of pack_assets_all files (OPEN #207-738) before opening individual BeatmapLevelsData files (OPEN #740+). BeatmapLevelSO objects with song names are in pack bundles, not individual song files.
18. **File-open sequence is predictable** — OPEN #1-206 (system), OPEN #207-738 (pack bundles), OPEN #738-739 (therollingstones_pack_assets_all), OPEN #740-741 (song redirects), OPEN #742+ (scenes/shaders/resources).
19. **🔴 String content search FAILED across all memory regions** — After 14+ versions (v0.66–v0.8024), scanning 16MB–8GB + metadata mmap, 0 strings found. Strings are NOT in: GC heap (8–8.25GB), metadata mmap (10.5–10.8GB), low memory (16MB–4GB), or extended heap (4–8GB). The memory injection approach for string patching is likely not viable on PS4.
20. **🔴 Pack bundles load BEFORE song data is used** — The Rolling Stones pack loads at OPEN #738, but BeatmapLevelsData redirects fire at OPEN #740. Even scanning at the redirect time finds 0 strings. The game may load BeatmapLevelSO objects lazily when the song list UI renders, not during startup.
21. **Deploy path matters** — Plugin goes to `/data/GoldHEN/plugins/`, NOT `/data/GoldHEN/AFR/CUSA12878/Plugins/`. Wrong path cost test cycles (v0.8021).

## See Also

- [[ps4-memory-layout-for-module-scanning]] — PS4 memory layout and bounds check details
- [[ps4-il2cpp-metadata-loading]] — How class name strings are loaded from global-metadata.dat at runtime
- [[plugin-architecture]] — Plugin build system, hook system, CRT init
- [[ps4-file-system-redirects]] — AFR redirects vs plugin deploy paths
- [[development-workflow]] — Full edit-build-deploy-test cycle
