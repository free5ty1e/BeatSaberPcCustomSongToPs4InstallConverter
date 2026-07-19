---
name: memory-injection-addressables-bypass
description: "Memory injection approach to bypass Addressables catalog CRC validation by patching BeatmapLevelSO in RAM — implemented as hook-triggered, signal-handler-based scanning"
metadata:
  type: reference
---

# Memory Injection — Addressables Catalog Bypass Approach

## Summary

When pack bundle modification is blocked by dual validation (m_BundleSize AND m_Crc), fallback to **memory injection**: patch BeatmapLevelSO objects in RAM after Addressables loads and validates the pack bundle. This bypasses catalog CRC validation entirely.

**Key Insight:** Addressables validates CRC LAZILY (when contents accessed, not during LoadFromFile). This gives us a window to patch objects in RAM before the game reads their metadata for the song selection screen.

**Status:** 🔵 **v0.76 plugin** — Memory injection actively developed. After 10 versions (v0.66–v0.76), root causes addressed: bounds check (v0.72), class string in metadata not module (v0.75), string pointer validation mismatch with try_read_mem bounds (v0.76). Current approach: wide-range pattern-based heap scan (16MB–64GB) with signal-handler safe probing.

## Implementation — Current Architecture (v0.76)

### Component Overview

```
open_hook (detects per-song bundle open)
    │
    ▼
memory_inject_try_patch()
    │
    ├── [1] Install signal handlers (once per scan)
    │
    ├── [2] find_beatmap_level_so_klass()    ← tries string search in module (may fail)
    │       │
    │       ├── find_module_segments()       ← sceKernelGetModuleList + sceKernelGetModuleInfo
    │       └── search_for_string()          ← searches for "BeatmapLevelSO" in module
    │                                         NOTE: Class name NOT in module (see discovery below)
    │
    ├── [3] find_beatmap_level_objects_by_pattern()  ← FALLBACK when string not found
    │       │
    │       └── scan memory (16MB–64GB, 1MB pages, 32-byte stepping)
    │           for objects matching BeatmapLevelSO field layout:
    │           - klass ptr in [0x80000000, 0x90000000]
    │           - _version in [1, 50]
    │           - _levelID, _songName, _songAuthorName → valid System_String pointers
    │           - String length in [1, 255]
    │
    ├── [4] scan_for_beatmap_level_objects() ← scans heap (0x200000000–0x210000000)
    │       │                                    for objects matching discovered klass
    │       └── validate_beatmap_level_object() ← checks version, field pointers
    │
    └── [5] patch_beatmap_level_object()     ← in-place UTF-16LE string overwrite
         └── Restore signal handlers
```

### Hook-Triggered Execution (Removed Thread)

Originally implemented as a thread (pthread + 30s delay), but this caused CE-34878-0 crashes due to PS4/FreeBSD process initialization conflicts. Replaced in v0.67 with **hook-triggered scanning**:

1. `open_hook` fires when a per-song bundle redirect is detected
2. Calls `memory_inject_try_patch()` synchronously from hook context
3. No guard timer — objects exist by the time user selects a song
4. On success (objects patched), locks permanently. On failure, retries on next redirect.

### Safe Memory Probing (Signal Handler Approach)

PS4's FreeBSD kernel has many stripped syscalls. `mincore()` and potentially `msync()` are stubs. The current approach uses **signal handlers** for safe memory probing:

```c
static int try_read_mem(uint64_t addr, void* buf, size_t size) {
    // Bounds check — CRITICAL: module segments at ~2 GB, heap at ~8-16 GB
    if (addr < 0x1000000ULL || addr > 0x2000000000ULL) return 0;

    // Install SIGSEGV/SIGBUS handlers, try memcpy, catch faults via siglongjmp
    struct sigaction sa, old_segv, old_bus;
    sa.sa_handler = mem_fault_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sigaction(SIGSEGV, &sa, &old_segv);
    sigaction(SIGBUS, &sa, &old_bus);

    int result = 0;
    if (sigsetjmp(g_mem_jmpbuf, 1) == 0) {
        memcpy(buf, (void*)addr, size);
        result = 1;
    }
    // If fault occurs, handler longjmps here with non-zero → result stays 0

    sigaction(SIGSEGV, &old_segv, NULL);
    sigaction(SIGBUS, &old_bus, NULL);
    return result;
}
```

This works for ANY memory type because it relies on the MMU for validation, not on kernel syscall stubs.

### Bounds Check — The Real Root Cause (v0.66–v0.71)

The original bounds check used `addr < 0x100000000` (4 GB) as the lower bound. PS4 module segments from `sceKernelGetModuleInfo` return addresses at **~0x80000000 (~2 GB)**, so ALL module reads were rejected before any probing method could execute. This was the real reason for "ERROR: Class string not found" across all versions.

See [[ps4-memory-layout-for-module-scanning]] for full details.

### Implementation Details

| Component | Approach |
|-----------|----------|
| Trigger | Hook callback from `open_hook` (not thread) |
| Klass finding | Search module data for "BeatmapLevelSO" C string via signal-handler-safe reads, find Il2CppClass_1 references via name pointer |
| Object scanning | 64KB page reads from 0x0200000000–0x0400000000, search for 8-byte klass ptr values |
| Validation | Check _version(0x18) in range [1,100], _levelID(0x20) is valid string ptr, _songName(0x28) valid |
| String patching | Write new length at +0x10, UTF-16LE chars at +0x14, zero-fill remainder |
| Metadata table | 13 Rolling Stones slots mapped to custom names/artists |
| Safe read | sigaction(SIGSEGV) + sigaction(SIGBUS) + sigsetjmp/siglongjmp |

### Field Layout (BeatmapLevelSO)

```
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

System_String_o:
  0x00: klass (System_String_c*)
  0x08: monitor (void*)
  0x10: _stringLength (int32_t)
  0x14: _firstChar (uint16_t) — rest follow contiguously
```

## Discovery: Class Name Strings NOT in Module (v0.75)

**Key finding from PS4 game dump analysis:** The "BeatmapLevelSO" class name is NOT compiled into the Il2CppUserAssemblies PRX as a C string. It exists only in `global-metadata.dat` (patch version, offset 0x23CB6E).

This means:
- The string-search approach (v0.66–v0.71) searched the wrong memory region
- The bounds check was never the real issue for the string search (though it was a real issue for the signal handler approach)
- IL2CPP on PS4 uses **dynamic metadata loading** — class names are loaded from the metadata file at runtime into a separately mapped memory region
- The klass struct's `name` field points into the metadata buffer, NOT into the module's data section

See [[ps4-il2cpp-metadata-loading]] for full analysis.

## Heap Address Is Unverified

The IL2CPP GC heap was assumed to be at `0x200000000–0x400000000` (8GB–16GB) based on typical PS4 Unity layout. This was UNVERIFIED. Scanning 64MB of this range found zero objects, suggesting the heap is at a different address or the field layout is wrong.

**Current approach (v0.76):** Wide-range scan from 16MB to 64GB at coarse granularity to locate objects.

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
| **v0.75** | **Wide scan 1GB–32GB, coarse stepping** | 🔵 **Pattern found NOTHING — string ptr bounds mismatch** |
| **v0.76** | **Fixed string ptr threshold 4GB→16MB, scan 16MB–64GB** | 🔵 **Consistent bounds in all validation** |

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
  -e "put beat_saber_deluxe.prx -o /data/GoldHEN/plugins/beat_saber_deluxe.prx; quit"
```

The AFR directory is for **asset/song bundles only**, not plugins. The `plugins.ini` at `/data/GoldHEN/plugins.ini` maps plugins to game title IDs.

## Next Steps (v0.72+)

1. **Verify klass found** — v0.72 test awaits: confirm `[MEMINJ] Found BeatmapLevelSO klass at 0x...`
2. **Verify object scanning** — confirm `[MEMINJ] Patched N/13 objects` 
3. **Verify metadata display** — check song name/artist in song selection screen
4. **Expand metadata table** — 32 slots (all DLC packs + base game)
5. **Cover image patching** — Replace `Sprite*` at offset 0x70 in BeatmapLevelSO

## See Also

- [[ps4-memory-layout-for-module-scanning]] — PS4 memory layout and bounds check details
- [[ps4-il2cpp-metadata-loading]] — How class name strings are loaded from global-metadata.dat at runtime (NOT in module)
- [[plugin-architecture]] — Plugin build system, hook system, CRT init
- [[ps4-file-system-redirects]] — AFR redirects vs plugin deploy paths
- [[development-workflow]] — Full edit-build-deploy-test cycle
