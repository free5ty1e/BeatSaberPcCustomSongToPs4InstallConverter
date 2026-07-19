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

**Status:** ✅ Memory injection implemented and running on PS4 since v0.66. The hook-triggered scanning finds BeatmapLevelSO klass pointer in Il2CppUserAssemblies module and scans the IL2CPP heap for matching objects. After a 3-version debugging saga (v0.69–v0.71), the real root cause was identified: a **bounds check that rejected module segment addresses** (see [[ps4-memory-layout-for-module-scanning]]).

## Implementation — Current Architecture (v0.72)

### Component Overview

```
open_hook (detects per-song bundle open)
    │
    ▼
memory_inject_try_patch()
    │
    ├── find_beatmap_level_so_klass()    ← searches Il2CppUserAssemblies module
    │       │
    │       ├── find_module_segments()   ← sceKernelGetModuleList + sceKernelGetModuleInfo
    │       └── search_for_string()      ← reads module data via try_read_mem (signal handler)
    │
    ├── scan_for_beatmap_level_objects() ← scans IL2CPP heap (0x0200000000–0x0400000000)
    │       │
    │       └── validate_beatmap_level_object() ← checks version, field pointers
    │
    └── patch_beatmap_level_object()     ← in-place UTF-16LE string overwrite
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

## History — The Debugging Saga

| Version | Change | Result |
|---------|--------|--------|
| v0.66 | Initial memory injection (thread-based, direct memcpy) | Tested on PC prototype only |
| v0.67 | Thread removed → hook-triggered, mincore safe reads | CE-34878-0 fixed, but "Class string not found" |
| v0.68 | Removed pack bundle redirect (was causing boot crash) | Boots fine, still "Class string not found" |
| v0.69 | Guard timer removed, trigger widened, mincore→msync | Same error — mincore/msync are stubs |
| v0.70 | msync retained, deployed for test | Same error — but bounds check was the real issue |
| v0.71 | Signal handlers + VERBOSE_LOG + fix deploy path | **Found bounds check bug** via verbose log |
| **v0.72** | **Bounds check fixed: 4GB→16MB lower bound** | **Should find klass — awaiting test!** |

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
- [[plugin-architecture]] — Plugin build system, hook system, CRT init
- [[ps4-file-system-redirects]] — AFR redirects vs plugin deploy paths
- [[development-workflow]] — Full edit-build-deploy-test cycle
