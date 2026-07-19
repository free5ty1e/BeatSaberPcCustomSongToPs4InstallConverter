# Project Summary: Beat Saber PS4 Custom Song Support
**Last Updated:** 2026-07-19
**Status:** 🟡 **v0.72 plugin** — Memory injection: All known bugs fixed. Bounds check root cause identified (v0.66–v0.71). Signal-handler-based memory probing implemented. **v0.72 deployed, awaiting PS4 hardware test results.**

## Current Approach: Memory Injection (v0.66+)

The plugin patches BeatmapLevelSO objects in RAM after Addressables loads the pack bundle, bypassing catalog CRC/size validation entirely:

1. **Hook trigger** — `open_hook` detects per-song bundle redirect → calls `memory_inject_try_patch()`
2. **Find klass** — Search Il2CppUserAssemblies module for "BeatmapLevelSO" string → locate il2cpp class metadata
3. **Scan heap** — Search 0x0200000000–0x0400000000 range for objects with matching klass pointer (64KB page scanning)
4. **Validate** — Check _version in range [1,100], verify _levelID/_songName are valid string pointers
5. **Patch** — Overwrite string fields in-place (UTF-16LE): song name, artist, level ID, level author

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Hook-triggered (not thread) | Threads caused CE-34878-0 on PS4 (v0.67+ removed thread) |
| Signal-handler safe probing | `mincore`/`msync` are stubs on PS4 kernel; `sigaction`+`sigsetjmp` works for any memory type |
| In-place string patching | Avoids GC complexity — new text MUST fit within original capacity |
| Level ID matching | Match by `_levelID` string against registered metadata table |
| External metadata table | 13 Rolling Stones slots defined in SongMetadataEntry array, expandable to 32+ |

## Key Technical Findings

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
| **174** | **v0.72** | **Bounds check fixed (16MB–128GB)** | **🟡 Deployed, awaiting test** |

## Memory Injection Versions

| Version | Date | Key Changes |
|---------|------|-------------|
| v0.66 | 07-17 | Initial implementation (thread-based, direct memcpy) |
| v0.67 | 07-17 | Thread removed → hook-triggered, mincore safe reads |
| v0.68 | 07-17 | Removed pack bundle redirect (was causing boot crash) |
| v0.69 | 07-17 | Guard timer removed, trigger widened, mincore→msync |
| v0.70 | 07-17 | msync tested — same error (bounds check was real issue) |
| v0.71 | 07-19 | Signal handlers + VERBOSE_LOG + deploy path fix |
| **v0.72** | **07-19** | **Bounds check fixed — awaiting test** |

## Next Steps

1. **Test v0.72 on PS4** — Verify `[MEMINJ] Found BeatmapLevelSO klass at 0x...` in log
2. **Verify object patching** — Confirm `[MEMINJ] Patched N/13 objects`
3. **Verify metadata display** — Check custom song names/artists in song selection
4. **Expand metadata table** — Register metadata for all 32 DLC slots
5. **Cover image patching** — Replace Sprite* at BeatmapLevelSO offset 0x70

## Active Knowledge Gaps

1. ~~CRC validation blocked~~ → **SOLVED** via memory injection (bypasses CRC entirely)
2. ~~Size validation blocked~~ → **SOLVED** via memory injection (bypasses size entirely)
3. ~~Class string not found~~ → **SOLVED** v0.72: bounds check fixed (real root cause)
4. Memory injection — **IN PROGRESS**: v0.72 deployed, awaiting test
5. Song metadata display verification — Not yet tested on PS4
6. Cover image patching — Not yet implemented

## References

- [[memory-injection-addressables-bypass]] — Full memory injection architecture
- [[ps4-memory-layout-for-module-scanning]] — Memory layout and bounds check details
- [[ps4-file-system-redirects]] — Deploy paths (plugins vs AFR)
- [[plugin-architecture]] — Build system and component overview
- [[development-workflow]] — Edit-build-deploy-test cycle
