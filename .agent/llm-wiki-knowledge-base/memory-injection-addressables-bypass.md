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

**Status:** 🟡 **Memory injection v0.8015** — Wide-range heap scan (4GB–17GB) deployed. Previous scans found 0 objects in the 256MB window (8GB–8.25GB). The multi-minute freeze was caused by the string content search fallback scanning 12GB — now disabled. Pack bundle detection restored for correct startup timing. Feature flags system fully implemented (v0.8012).

## Implementation — Current Architecture (v0.8015)

### Component Overview

```
open_hook (detects pack_assets_all OR per-song redirect)
    │
    ▼
memory_inject_try_patch()  [gated behind g_feature_song_metadata_modification]
    │
    ├── [1] Install signal handlers (once per scan)
    │
    ├── [2] find_beatmap_level_so_klass()    ← tries string search in module (always fails)
    │       │
    │       ├── find_module_segments()       ← sceKernelGetModuleList + sceKernelGetModuleInfo
    │       └── search_for_string()          ← searches for "BeatmapLevelSO" in module
    │                                         NOTE: Class name NOT in module (see ps4-il2cpp-metadata-loading)
    │
    ├── [3] find_beatmap_level_objects_by_pattern()  ← FALLBACK when string not found
    │       │
    │       └── scan memory (16MB–4GB, 64KB pages, 32-byte stepping)
    │           for objects matching BeatmapLevelSO field layout:
    │           - klass ptr in [0x80000000, 0x90000000]
    │           - _version in [1, 50]
    │           - _levelID, _songName, _songAuthorName → valid System_String pointers
    │           - String length at lid+0x10/0x14/0x18/0x1C (probed dynamically)
    │
    ├── [4] scan_for_beatmap_level_objects() ← scans heap (4GB–17GB, 64KB pages, 60s timeout)
    │       │                                    for objects matching discovered klass
    │       └── validate_beatmap_level_object() ← checks version, field pointers
    │
    └── [5] patch_beatmap_level_object()     ← in-place UTF-16LE string overwrite
         └── Restore signal handlers
```

### Hook-Triggered Execution (Removed Thread)

The original v0.66 implementation used a 30-second pthread for deferred scanning. This caused CE-34878-0 crashes due to FreeBSD init race. Since v0.67, the scan runs synchronously inside the `open_hook()` callback:

- **Primary trigger:** `open_hook` detects pack bundle load (`pack_assets_all`) at startup → calls `memory_inject_try_patch()`
- **Secondary trigger:** `open_hook` detects per-song bundle redirect → calls `memory_inject_try_patch()`
- **Re-entrancy guard:** `g_patching_done` flag prevents multiple simultaneous scans
- **Feature flag:** All memory injection gated behind `g_feature_song_metadata_modification`
- **Signal handlers:** Installed once at scan start, restored at end (v0.74 optimization, saves ~524K sigaction syscalls)
- **Timing:** Primary trigger fires at startup when pack bundle loads (before song list UI reads metadata)

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

The IL2CPP GC heap was assumed to be at `0x200000000–0x400000000` (8GB–16GB) based on typical PS4 Unity layout. The klass struct was found at `0x2012007E0` (8GB), but scanning 8GB–8.25GB found 0 objects. v0.8015 expands the scan to 4GB–17GB to cover the full possible heap.

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
| **v0.8015** | **Wide-range scan 4GB–17GB + timing fix** | **🔄 Deployed, awaiting test** |

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

1. **Always check bounds before probing** — VERBOSE_LOG the actual segment addresses first
2. **Module segments can be anywhere** — Don't assume they're above 4 GB
3. **Signal handling works for safe probing** — `sigaction` + `sigsetjmp`/`siglongjmp` works on PS4
4. **Syscall stubs are common** — `mincore` and `msync` are stubs on PS4; use signal handlers instead
5. **Keep all bounds checks in sync** — Changing `try_read_mem()` bounds requires updating ALL validation functions
6. **Stack buffer size matters** — PS4 thread stack ~256KB. 1MB buffers overflow silently (every try_read_mem faults)
7. **Class name strings in global-metadata.dat** — NOT in compiled module PRX
8. **System_String layout may differ on PS4** — `_stringLength` offset may not be at standard 0x10; dynamic probing added (0x10/0x14/0x18/0x1C)
9. **String content search is too slow for large ranges** — Scanning 12GB for string patterns causes multi-minute hangs; disable or cap range
10. **Pack bundle detection fires at startup** — `pack_assets_all` matches bundles loaded during game init, not just when user navigates to pack
11. **Feature flags essential for iteration** — All experimental features gated behind `features.json` flags for safe testing
12. **Klass pointer may not match expected range** — Found klass at 8GB but objects not in 8GB–8.25GB window; scan entire possible heap (4GB–17GB)

## See Also

- [[ps4-memory-layout-for-module-scanning]] — PS4 memory layout and bounds check details
- [[ps4-il2cpp-metadata-loading]] — How class name strings are loaded from global-metadata.dat at runtime
- [[plugin-architecture]] — Plugin build system, hook system, CRT init
- [[ps4-file-system-redirects]] — AFR redirects vs plugin deploy paths
- [[development-workflow]] — Full edit-build-deploy-test cycle
