# Project Summary: Beat Saber PS4 Custom Song Support
**Last Updated:** 2026-07-21
**Status:** 🟡 **Memory injection v0.8015 deployed — wide-range heap scan (4GB–17GB).** The klass-based scan found 0 objects in the 256MB window (8GB–8.25GB). v0.8015 expands the range to cover the full possible IL2CPP heap (4GB–17GB = 13GB). The multi-minute freeze was caused by the string content search fallback scanning 12GB — now disabled. Pack bundle detection restored for correct startup timing. Feature flags system fully implemented and tested (v0.8012).

## Current Approach: Memory Injection (v0.66+)

The plugin patches BeatmapLevelSO objects in RAM after Addressables loads the pack bundle, bypassing catalog CRC/size validation entirely:

1. **Hook trigger** — `open_hook` detects pack bundle load (pack_assets_all) at startup OR per-song redirect → calls `memory_inject_try_patch()`
2. **Find klass** — Three attempts:
   - String search in Il2CppUserAssemblies module (fast path — KNOWN TO FAIL: class names are in global-metadata.dat, not module)
   - Pattern-based scan of GC heap (wide range 4GB–17GB, 64KB pages) — finds objects by klass pointer
   - Extract klass pointer from first validated object → use for targeted re-scan
3. **Scan heap** — Search 0x40000000–0x440000000 range for objects with matching klass pointer (64KB page scanning, 60s timeout)
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
| Feature flag gating | All memory injection behind `enable_song_metadata_modification` flag (default: false) |
| Pack bundle detection | Scan fires at startup when pack_assets_all loads, before song list UI |
| String content search disabled | Was scanning 12GB causing multi-minute hang; klass-based scan preferred |

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
| 188 | v0.8009 | Gap scan between GC heap and metadata | ❌ 60-second soft lock — gap scan disabled |
| 189 | v0.8010 | Direct string content search (no klass needed) | 🔄 Pivoted to string search approach |
| 128 | v0.8012 | Feature flags system | ✅ Implemented and tested on PS4 |
| 129 | v0.8013 | Pack bundle detection + offset probing | ❌ Fired at startup (multi-min freeze), 0 objects found in 256MB |
| 130 | v0.8014 | Diagnostic logging + scan timeout | ❌ Timing wrong (fires on song start), objects not in 8GB–8.25GB |
| **131** | **v0.8015** | **Wide-range scan 4GB–17GB + timing fix** | **🔄 Deployed, awaiting test** |

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

## Next Steps

1. **Test v0.8015 on PS4** — Verify wide-range scan (4GB–17GB) finds BeatmapLevelSO objects
2. **If objects found:** Confirm klass pointer, scan for all objects, patch metadata before song list displays
3. **If objects NOT found:** Investigate alternative approaches:
   - Objects may use a derived class with different klass pointer
   - Objects may have klass pointer at offset 0x08 instead of 0x00
   - Try scanning for known string content ("The Rolling Stones", song names) across wider range
   - Consider hooking UI display function instead of patching objects
4. **Optimize scan** — Once objects are found, narrow the scan range to their actual memory region for sub-second performance
5. **Expand metadata table** — Register metadata for all 32 DLC slots
6. **Cover image patching** — Replace Sprite* at BeatmapLevelSO offset 0x70

## Active Knowledge Gaps

1. ~~CRC validation blocked~~ → **SOLVED** via memory injection (bypasses CRC entirely)
2. ~~Size validation blocked~~ → **SOLVED** via memory injection (bypasses size entirely)
3. ~~Class string not found~~ → **SOLVED**: Class name strings in global-metadata.dat (v0.75)
4. **IL2CPP heap address on PS4** — **PARTIALLY KNOWN**: Klass struct at 0x2012007E0 (8GB), metadata at 0x293280000 (16.6GB). Objects NOT in 8GB–8.25GB window. v0.8015 scans 4GB–17GB.
5. **Field offsets (version=0x18, levelID=0x20, etc.)** — **UNVERIFIED**: from il2cpp.h dump, may differ on PS4
6. **Timing** — **PARTIALLY SOLVED**: Pack bundle detection fires at startup (before song list UI). If objects are found, metadata can be patched before display.
7. **Memory injection** — **IN PROGRESS**: v0.8015 deployed, wide-range scan 4GB–17GB

## References

- [[memory-injection-addressables-bypass]] — Full memory injection architecture
- [[ps4-memory-layout-for-module-scanning]] — Memory layout and bounds check details
- [[ps4-file-system-redirects]] — Deploy paths (plugins vs AFR)
- [[plugin-architecture]] — Build system and component overview
- [[development-workflow]] — Edit-build-deploy-test cycle
