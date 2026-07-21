# Project Summary: Beat Saber PS4 Custom Song Support
**Last Updated:** 2026-07-19
**Status:** 🟢 **Memory injection v0.8010 deployed — NEW APPROACH: Direct string content search.** The gap scan (v0.8009) caused a 60-second soft lock (too slow scanning unmapped pages via signal handlers). **v0.8010 completely pivots** from the klass-based approach to a **string content search**. Instead of finding BeatmapLevelSO objects and patching their fields, we now search for the actual song name strings in memory by their UTF-16LE content (length prefix + characters) and overwrite them in-place. This requires NO klass lookup, NO object scanning, and NO knowledge of object layout. The gap scan is DISABLED. Searches only the GC heap (0x200000000-0x210000000, ~80ms) and metadata area (~10ms).

## Current Approach: Memory Injection (v0.66+)

The plugin patches BeatmapLevelSO objects in RAM after Addressables loads the pack bundle, bypassing catalog CRC/size validation entirely:

1. **Hook trigger** — `open_hook` detects per-song bundle redirect → calls `memory_inject_try_patch()`
2. **Find klass** — Three attempts:
   - String search in Il2CppUserAssemblies module (fast path — KNOWN TO FAIL: class names are in global-metadata.dat, not module)
   - Pattern-based scan of GC heap (wide range 1GB–32GB, coarse granularity) — finds objects by field layout signature
   - Extract klass pointer from first validated object → use for targeted re-scan
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
| 174 | v0.72 | Bounds check fixed (4GB→16MB) | ✅ try_read_mem works, but string NOT in module |
| 175 | v0.73 | Pattern matcher (full heap scan) | ❌ Black screen hang — scan too slow |
| 176 | v0.74–v0.75 | Optimized scan + dump analysis | 🔵 **Class names in global-metadata.dat discovery** |
| **177** | **v0.76** | **String ptr validation threshold 4GB→16MB** | **✅ Consistent bounds — real fix for "found nothing"** |
| **178** | **v0.77–v0.79** | **Stack overflow fix + STRDEBUG** | **✅ 1MB→64KB stack, finds 17 candidates. String layout mismatch** |
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
| v0.72 | 07-19 | Bounds check fixed: 4GB→16MB lower bound, signal handlers proved working |
| v0.73 | 07-19 | Pattern-based klass finding (full 8GB scan) — ❌ hang, too slow |
| v0.74 | 07-19 | Persistent signal handlers (once per scan), 256MB range — no klass found |
| **v0.75** | **07-19** | **Wide-range scan (1GB–32GB, coarse). Class names discovered in metadata NOT module.** |
| **v0.72** | **07-19** | **Bounds check fixed — awaiting test** |

## Next Steps

1. **Test v0.75 on PS4** — Verify pattern matcher finds BeatmapLevelSO objects in 1GB–32GB range
2. **Verify klass found** — If objects found, confirm klass pointer and scan for all objects
3. **Address timing issue** — Memory injection fires on per-song redirect (during play), but song list metadata comes from pack bundle (loaded earlier). UI text caching may prevent display updates even if objects are patched. Options:
   a. Trigger injection on pack bundle open (not per-song redirect)
   b. Use frame callback for retry-based injection at song list time
   c. Accept that song list metadata display changes are not possible via late injection
4. **Implement Feature Flags** — Add `features.json` to allow toggling `enable_song_metadata_modification` (default: false)
5. **Verify field offsets** — Extract actual BeatmapLevelSO TypeTree from a LIVE PS4 dump (not truncated dump)
6. **Expand metadata table** — Register metadata for all 32 DLC slots
7. **Cover image patching** — Replace Sprite* at BeatmapLevelSO offset 0x70

## Active Knowledge Gaps

1. ~~CRC validation blocked~~ → **SOLVED** via memory injection (bypasses CRC entirely)
2. ~~Size validation blocked~~ → **SOLVED** via memory injection (bypasses size entirely)
3. ~~Class string not found~~ → **REFRAMED**: Class name strings are in global-metadata.dat, NOT in module (v0.75 discovery)
4. IL2CPP heap address on PS4 — **UNKNOWN**: Assumed 0x200000000, may be different. v0.75 scans 1GB–32GB
5. Field offsets (version=0x18, levelID=0x20, etc.) — **UNVERIFIED**: from il2cpp.h dump, may differ on PS4
6. Timing — **UNRESOLVED**: Per-song redirect fires during play, but song list metadata comes from earlier pack bundle load. UI text caching may prevent display updates from late patching.
7. Memory injection — **IN PROGRESS**: v0.75 deployed, awaiting test

## References

- [[memory-injection-addressables-bypass]] — Full memory injection architecture
- [[ps4-memory-layout-for-module-scanning]] — Memory layout and bounds check details
- [[ps4-file-system-redirects]] — Deploy paths (plugins vs AFR)
- [[plugin-architecture]] — Build system and component overview
- [[development-workflow]] — Edit-build-deploy-test cycle
