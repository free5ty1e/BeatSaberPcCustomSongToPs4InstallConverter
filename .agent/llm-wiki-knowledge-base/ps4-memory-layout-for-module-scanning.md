---
name: ps4-memory-layout-for-module-scanning
description: "PS4 process memory layout: where modules, IL2CPP heap, and other regions map — critical for memory scanning bounds"
metadata:
  type: reference
---

# PS4 Memory Layout — Module Scanning

## Summary

PS4 modules (PRX shared libraries loaded by GoldHEN) map at **~0x80000000 (~2 GB)**, NOT above 4 GB as one might expect on a 64-bit system. This was the root cause of the "Class string not found" bug that affected v0.66 through v0.71.

## Memory Regions on PS4 (Beat Saber)

| Region | Address Range | Contents |
|--------|--------------|----------|
| **Module segments** | ~0x80000000 (~2 GB) | PRX code (.text), read-only data (.rodata), writable data (.data) — returned by `sceKernelGetModuleInfo` |
| **IL2CPP managed heap** | ~0x0200000000 (8 GB) — ~0x0400000000 (16 GB) | Unity/IL2CPP GC heap objects, including BeatmapLevelSO instances |
| **Near-null** | < 0x1000000 (16 MB) | Invalid/unmapped — use as lower bound for safety |

## The Bounds Check Bug (v0.66–v0.71)

The original bounds check in `try_read_mem()` used `0x100000000` (4 GB) as the lower bound:

```c
// WRONG — rejects module segments at ~2 GB
if (addr < 0x100000000ULL || addr > 0x8000000000ULL) return 0;
```

PS4 module segments from `sceKernelGetModuleInfo` returned addresses like `0x806C0000` (~2 GB). These were rejected by the bounds check **before any probing method could execute**, causing ALL module segment reads to silently return 0.

### Impact

| Version | Probing Method | Bounds Check | Actual Failure |
|---------|---------------|--------------|----------------|
| v0.66–v0.68 | Direct `memcpy` | Rejected ~2 GB | Never tested — bounds check |
| v0.69 | `mincore()` | Rejected ~2 GB | mincore never called for segments |
| v0.70 | `msync(MS_ASYNC)` | Rejected ~2 GB | msync never called for segments |
| v0.71 | `sigaction`+`sigsetjmp`/`siglongjmp` | Rejected ~2 GB | Signal handlers never installed for segments |

### The Fix

```c
// CORRECT — accepts module segments at ~2 GB AND IL2CPP heap at ~8-16 GB
if (addr < 0x1000000ULL || addr > 0x2000000000ULL) return 0;
```

- **Lower bound**: `0x1000000` (16 MB) — well below any module segment, safe from null pointers
- **Upper bound**: `0x2000000000` (128 GB) — generous safety margin above IL2CPP heap range

## Lesson for Future Memory Scanning

When writing memory scanning code for PS4:

1. **Always check bounds before spending time on probing** — VERBOSE_LOG the actual segment addresses first
2. **Module segments can be anywhere** — Don't assume they're above 4 GB on a 64-bit FreeBSD variant
3. **Use VERBOSE_LOG in debug builds** `(DEBUG=1)` to dump segment addresses, sizes, and per-chunk read status
4. **Signal handling works for safe probing** — `sigaction(SIGSEGV)` + `sigaction(SIGBUS)` + `sigsetjmp/siglongjmp` does work on PS4 for catching page faults from `memcpy`
5. **Syscall stubs are common** — On PS4's stripped FreeBSD kernel, many syscalls like `mincore` and potentially `msync` are stubs. Don't rely on them for memory validation.

## See Also

- [[memory-injection-addressables-bypass]] — The memory injection system that uses this layout
- [[plugin-architecture]] — How modules are loaded and how to find their segments
