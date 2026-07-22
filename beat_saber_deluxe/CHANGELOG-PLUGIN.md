# Plugin Changelog — Beat Saber Deluxe

All notable changes to the GoldHEN plugin (`beat_saber_deluxe.prx`) are documented here.

**Version scheme:** Increment by **0.0001** per experiment (e.g. v0.80 → v0.8001 → v0.8002). This gives ample room to iterate before reaching v1.00.

## [v0.8017] — 2026-07-21
### Fixed
- **Removed background thread** — `scePthreadCreate` inside `open_hook` callback causes CE-34878-0 crash. Replaced with synchronous `patch_strings_by_content()` call with signal handlers installed around it. No thread creation in hook context.
- **5-second scan timeout** — The synchronous scan uses `sceKernelGetProcessTime()` inside `patch_strings_by_content` to abort after 5 seconds if no strings found. Prevents indefinite hook blocking.

## [v0.8016] — 2026-07-21
### Changed
- **String content search via background thread** — Complete pivot from klass-pointer approach (broken after 10+ versions). Now searches for exact UTF-16LE song name strings ("Start Me Up", "The Rolling Stones") directly in memory. Runs in a background thread via `sceKernelStartThread` (non-blocking, scans every 100ms for up to 30 seconds). Gated behind `enable_song_metadata_modification` feature flag.
- **Removed klass-based scanning** — The klass pointer `0x2012007E0` was NEVER found as the first 8 bytes of any page in 4GB–17GB (262K pages). PS4 IL2CPP uses compressed/indirect klass pointers. Do not pursue further.

## [v0.8015] — 2026-07-21
### Fixed
- **Wide-range heap scan** — Scan range expanded from 8GB–8.25GB (256MB) to 4GB–17GB (13GB). The BeatmapLevelSO objects were never in the 256MB window — diagnostics confirmed 0 raw matches across 4,380 pages. The wider range covers the full possible IL2CPP heap on PS4.
- **Restored pack bundle detection** — Re-added `pack_assets_all` detection in `open_hook` so the scan fires at startup when the pack loads (before song list UI reads metadata). `memory_inject_try_patch` has internal guard — only scans once.
- **Disabled string content search** — The fallback string content search scanned 4GB–16GB (12GB) and caused the multi-minute freeze. Skipped entirely — the wider klass-based scan should find objects directly.
- **60-second scan timeout** — Hard limit prevents indefinite freezes even with the wider range.

## [v0.8014] — 2026-07-20
### Fixed
- **Removed pack bundle detection** — `strstr("pack_assets_all")` was matching bundles loaded at game startup (before user agreement screen), triggering a full scan immediately and causing a multi-minute black screen. Reverted to redirect-only triggering.
- **Scan timeout** — 30-second hard limit on the klass-based scan. Aborts gracefully and logs elapsed time. Prevents indefinite freezes.
- **Enhanced scan diagnostics** — Logs page addresses and first8 bytes every 256 pages, logs every raw klass match with exact address, and logs range boundaries at scan start. Will help diagnose why 0 objects were found in v0.8013.

## [v0.8013] — 2026-07-20
### Added
- **Pack bundle detection** — `open_hook` now triggers `memory_inject_try_patch()` when `pack_assets_all` bundles are opened (user selects a pack), not just on per-song redirects. This fires the scan when BeatmapLevelSO objects are actually loaded into RAM.
- **String length offset probing** — Pattern matcher now tries offsets 0x10, 0x14, 0x18, 0x1C to find `_stringLength` in System_String objects, instead of hardcoding 0x10. Handles PS4's non-standard mono layout (16-byte monitor field). Logs which offset succeeds.

## [v0.8012] — 2026-07-19
### Added
- **Feature flags system** — Reads `/data/GoldHEN/AFR/CUSA12878/features.json` at plugin startup. Two flags:
  - `enable_custom_song_replacements` (default: `false` if missing) — Gates all song redirects in `open_hook`. When OFF, the plugin loads but no bundle redirects fire, so the game plays original songs.
  - `enable_song_metadata_modification` (default: `false` if missing) — Gates memory injection (`register_song_metadata` + `memory_inject_init`). When OFF, no RAM patching occurs.
- **Pipeline integration** — `--set-feature key=value` flag in the pipeline writes features.json locally and deploys it to PS4 via FTP.

## [v0.8011] — 2026-07-19
### Changed
- **Optimized string search** — 8× faster: uses 8-byte granularity with a uint32 length lookup table instead of 2-byte granularity with 13-length loops. Target: ~200ms instead of ~18s for the GC heap scan.
- **Dual-format string matching** — Now checks BOTH UTF-16LE (standard .NET) AND UTF-8 (possibly used by PS4) patterns in a single pass. Each string has two uint64 fingerprints checked at every 8-byte aligned position.
- **Expanded search range** — Covers from 0x200000000 (GC heap start) to `metadata_base + 64MB` (~0x297280000), covering the full 2.3GB range including the gap that was previously unscannable. Single pass, no separate metadata range scan needed.
- **Gap scan remains disabled** — No separate gap scan; the single large-range pass uses try_read_mem at 64KB granularity, which quickly skips unmapped pages.

## [v0.8010] — 2026-07-19
### Changed
- **DIRECT STRING SEARCH APPROACH** — Completely new method: instead of finding BeatmapLevelSO objects by klass pointer, search for song name/author strings by their UTF-16LE content in memory and patch them directly. This bypasses the need to find BeatmapLevelSO objects entirely.
- **Removed gap scan** — The 2GB gap scan (v0.8009) caused 60-second soft lock. Replaced with the much faster string search in the GC heap and metadata ranges.
- Added original song names/artists to SongMetadataEntry (`orig_song_name`, `orig_song_author_name`) for content-based search.
- Added `patch_strings_by_content()` function that scans memory for known UTF-16LE strings and overwrites them with replacement text.

### Files Changed
- memory_inject.h — Added `orig_song_name`, `orig_song_author_name` to SongMetadataEntry
- memory_inject.cpp — Added `patch_strings_by_content()`, forward declaration, integration into `memory_inject_try_patch()`
- main.cpp — Updated `register_song_metadata()` with original names

## [v0.8009] — 2026-07-19
### Added
- **Gap scan on retry** — When the close hook retries the object scan, it now also searches the 2GB gap between the primary GC heap range (0x200000000-0x210000000) and the metadata address (~0x293280000). BeatmapLevelSO objects may be allocated on the GC heap at addresses above 0x210000000, which wasn't covered by any previous scan range.
- Added `g_wide_scan` flag that enables the gap scan range (SCAN_END_ADDR → metadata_base) only during retry, avoiding extra delay on the initial scan.

## [v0.8008] — 2026-07-19
### Added
- **Close hook retry mechanism** — Added a `close()` hook that retries the MEMINJ object scan after a file is closed. When the initial scan (triggered by `open()`) finds the BeatmapLevelSO_c klass but 0 BeatmapLevelSO objects, it caches the klass address and schedules a retry. The retry uses the cached klass (skipping the ~9s metadata magic search) and only runs the object scanner, which should find the BeatmapLevelSO objects that were created between the open() and close() calls.

### Changed
- **Memory injection retry support** — `memory_inject_try_patch()` now detects retry calls via `g_cached_klass`, skipping the klass search and pattern matcher entirely on retry.

## [v0.8007] — 2026-07-19
### Added
- **Il2CppClass struct hex dump** — When the broader search finds the BeatmapLevelSO name pointer in memory, dumps the 32 bytes at the suspected klass struct start: `[0x00]=klass [0x08]=image [0x10]=name [0x18]=ns/td`. This will verify whether the `name` field is actually at offset 0x10 or at a different position in the struct. 0 raw matches in v0.8006 suggests either a timing issue or wrong offset assumption.

## [v0.8006] — 2026-07-19
### Added
- **Diagnostic klass match counter** — `scan_for_beatmap_level_objects()` now logs the number of raw klass pointer matches found (even those that fail validation) via `[MEMINJ] Klass diag: N raw matches, M validated`. This will tell us if BeatmapLevelSO objects exist but are being rejected by validation.
- **Extended object scan range** — Added a second scan range around the metadata address (±2MB to +16MB) when `g_metadata_base` is known. BeatmapLevelSO objects may be allocated in memory near the metadata rather than in the main GC heap range.
- Added `g_metadata_base` static global to persist metadata address across the klass search and object scanner.

## [v0.8005] — 2026-07-19
### Added
- **Broader klass pointer search fallback** — After module segment search fails, searches the GC heap range (0x200000000-0x210000000) and memory near the metadata itself for 8-byte pointers to the "BeatmapLevelSO" string. The Il2CppClass struct may be dynamically allocated outside the module data segment.
- **metadata_base now function-scoped** — Saved at function scope so it's available for both the string address computation and the broader fallback search.

## [v0.8004] — 2026-07-19
### Fixed
- **Klass pointer search now scans ALL module segments** — Removed `if (!segs[s].is_readable) continue;` filter that was skipping the data segment (Seg[1] at 0x84AC0000). The data segment is where Il2CppClass structs live, but it's incorrectly flagged as `is_readable=0` in sceKernelGetModuleInfo results. `try_read_mem` with signal handlers can safely read from any segment.
- **Metadata magic search confirmed working** — v0.8003 found patch global-metadata.dat at 0x293280000 (version 31), but the klass pointer search couldn't find the string reference because it never scanned the data segment.

## [v0.8003] — 2026-07-19
### Added
- **global-metadata.dat magic search** — New function `search_for_patch_metadata()` that finds the patch global-metadata.dat in memory by searching for its magic bytes (`0xFAB11BAF`) across all readable memory. When found (version 31, string count > 1M), computes the runtime address of the "BeatmapLevelSO" string within it and uses the existing Il2CppClass pointer search to locate the BeatmapLevelSO_c klass in the data segment. This solves the root problem: "BeatmapLevelSO" is only stored in the patch global-metadata.dat, not in the module text/data segments.

## [v0.8002] — 2026-07-19
### Changed
- **Hex dump of lid pointer header** — Replaced int32 STRDEBUG with full 32-byte hex dump of the object at `lid` (4 × uint64_t). Shows klass pointer, monitor field, and suspected _stringLength field at all potential offsets. Enables definitive identification of System_String layout on PS4 by inspection.

## [v0.8001] — 2026-07-19
### Changed
- **STRDEBUG expanded to ALL pointer-level candidates** — Removed `chk_ptrs <= 3` limit. Now logs every candidate that passes klass+version+pointers checks, providing full diagnostic data for the 45 candidates found in v0.80.
- **Enhanced candidate logging** — Added candidate object address (`obj=0x...`) and `lid+0x18` value to STRDEBUG output for deeper System_String layout analysis on PS4.

## [v0.80] — 2026-07-19
### Fixed
- **False positive rejection in pattern matcher** — Added `klass != lid/sn/an` check to reject 17 false positives found at 0x802Axxxx (kernel/system memory below module base). These garbage structs coincidentally matched the BeatmapLevelSO field layout but had klass == lid, which a real object never has.
- **Widened klass range check** — Accept klass in both module space (0x80000000-0x90000000) and GC heap (0x200000000+). Il2CppClass structs may be allocated on the GC heap in some configurations.
- **Extended pattern scan to GC heap range** — Added second scan loop covering 0x200000000-0x210000000 (8GB-8.25GB) where the IL2CPP GC heap is typically mapped on PS4. Previously the pattern scan only searched 16MB-4GB, missing the GC heap entirely.

## [v0.79] — 2026-07-19
### Added
- **STRDEBUG logging in pattern matcher** — Dumps raw values at `lid+0x10` and `lid+0x14` for the first 3 candidates that reach `chk_ptrs` level. Used to determine the correct System_String._stringLength offset on PS4 (may differ from standard IL2CPP layout).

## [v0.78] — 2026-07-19
### Fixed
- **Pattern matcher stack buffer overflow** — Changed `PATTERN_SCAN_STEP` from 0x100000 (1MB) to 0x10000 (64KB). The 1MB `uint8_t page[PATTERN_SCAN_STEP]` stack buffer exceeded the PS4 thread's ~256KB stack limit. Every `try_read_mem` call faulted on the invalid stack destination buffer, resulting in "0 mapped pages" across the entire scan range. The original code used 64KB pages (SCAN_STEP) — this was safe. The pattern matcher inherited the wrong constant.
- **Max scan range reduced** — PATTERN_SCAN_MAX from 64GB to 4GB (still covers module segments and likely heap regions).

## [v0.77] — 2026-07-19
### Added
- **Pattern matcher diagnostic counters** — Added per-check failure counters (klass, version, ptrs, strlen) to identify which field validation check is rejecting BeatmapLevelSO candidates. Output: `[MEMINJ] Pattern diag: N pages (M mapped). klass=K ver=V ptrs=P strlen=S`

## [v0.76] — 2026-07-19
### Fixed
- **String pointer validation threshold lowered from 4GB to 16MB** — The IL2CPP heap on PS4 may be below 4GB. The pattern matcher's validation rejected ALL objects because their string field pointers (lid, sn, an) were below the 0x100000000 (4GB) threshold. Changed to 0x1000000 (16MB) to match try_read_mem bounds.
- **Scan range expanded** — PATTERN_SCAN_MIN lowered from 1GB to 16MB, PATTERN_SCAN_MAX raised from 32GB to 64GB. Previous range may have missed heap locations below 1GB.

## [v0.75] — 2026-07-19
### Changed
- **Pattern matcher scan range expanded** — Changed from limited heap (64MB at 0x200000000) to wide range (1GB-32GB, 1MB pages, 32-byte granularity). The IL2CPP heap address on PS4 is unverified; previous range may have missed objects entirely.
- **Key discovery** — "BeatmapLevelSO" class name string is NOT in Il2CppUserAssemblies module; it's only in global-metadata.dat loaded at runtime. Confirmed via PS4 game dump analysis.

## [v0.74] — 2026-07-19
### Changed
- **Signal handlers installed once per scan** — Moved from per-`try_read_mem` call (5 syscalls per read) to once at start of `memory_inject_try_patch()` and restored at end. ~524K fewer syscalls per full heap scan.
- **Heap scan range reduced** — SCAN_END_ADDR changed from 0x400000000 (8GB) to 0x210000000 (256MB). Reduces iterations from 131K pages × 8192 checks to 4K pages × 8192 checks. ~33M vs ~1B checks.
- **Pattern matcher limited to first 64MB** — Only scans first 64MB of heap (not full 8GB) to find klass via field layout.
- **Double scan eliminated** — Combined klass discovery and object scanning logic. String search is tried first, fallback to pattern matcher in limited range, then object scan only once with klass.
### Fixed
- **Black screen hang on song select (v0.73)** — Caused by scanning the full 8GB heap range synchronously in the hook callback (~1B checks per scan, double-scanned). Now completes in ~33M checks with optimized signal handler setup.

## [v0.73] — 2026-07-19
### Fixed
- **Class string "BeatmapLevelSO" not found in Il2CppUserAssemblies** — The string is NOT present in the module's .text segment (only segment returned by `sceKernelGetModuleInfo`). Added `find_beatmap_level_objects_by_pattern()` as fallback: scans the IL2CPP GC heap for objects matching BeatmapLevelSO field layout (version range, valid pointer ranges) instead of requiring klass string search. Extracts klass pointer from the first validated object.
### Added
- **Pattern-based klass finding** — New function `find_beatmap_level_objects_by_pattern()` searches heap objects by struct field layout signature rather than by class name string. This bypasses the need for the "BeatmapLevelSO" C string in module data.

## [v0.72] — 2026-07-19
### Fixed
- **REAL root cause of "Class string not found"** — `try_read_mem()` had a bounds check rejecting addresses below 0x100000000 (4GB). PS4 modules (Il2CppUserAssemblies) are loaded at ~0x80000000 (2GB), so ALL segment reads were rejected by the bounds check before any probing method could be tested. This affected v0.66 through v0.71.
- **Lower bound changed** from 0x100000000 (4GB) to 0x1000000 (16MB) to accept module segment addresses (~2GB) while still rejecting near-null pointers.
- **Upper bound changed** from 0x8000000000 (32GB) to 0x2000000000 (128GB) for safety margin.
- **Signal-handler approach retained** from v0.71 — `sigaction`/`sigsetjmp`/`siglongjmp` remain the memory probing mechanism once address passes bounds check.
### Changed
- Bounds check constants in `try_read_mem()`.

## [v0.71] — 2026-07-19
### Changed
- **Signal-handler-based memory probing** — Replaced `msync()` / `mincore()` with `sigaction(SIGSEGV)` + `sigaction(SIGBUS)` + `sigsetjmp`/`siglongjmp`. Installs handlers per call, tries `memcpy`, restores original handlers. Faults are caught by the handler and longjmp back safely.
- **`#ifdef VERBOSE_LOG` diagnostics** — Build with `DEBUG=1` to log segment addresses, sizes, protections, and per-chunk read status.
- **Fixed plugin deploy path** — Plugin was being uploaded to `/data/GoldHEN/AFR/CUSA12878/` (asset redirect directory) instead of `/data/GoldHEN/plugins/` (where `plugins.ini` points).

## [v0.70] — 2026-07-17
### Changed
- Replaced `mincore()` with `msync(MS_ASYNC)` for memory validation. msync returns 0 if all pages are mapped, -1 with ENOMEM otherwise. Also fixes anonymous page checking.

## [v0.69] — 2026-07-17
### Fixed
- Guard timer removed from memory injection. Trigger now fires on ANY redirect.
- Lock released on failure so retry is possible.
- Memory injection now called correctly in hook.

## [v0.68] — 2026-07-17
### Fixed
- Removed `pack bundle` redirect from `redirects.json` (was causing CE-34878-0 boot crash).
- Log write now uses static buffer (was using stack garbage).
- Thread removed, memory injection runs inside hook context (not pthread).

## [v0.67] — 2026-07-17
### Fixed
- CE-34878-0 crash: Removed `pthread_create`/`pthread_detach` (FreeBSD init race).
- Memory injection now runs synchronously inside `open_hook` callback.
- `mincore()` guards memory reads for safe page probing.

## [v0.66] — 2026-07-17
### Added
- **Memory injection module** — New `src/memory_inject.cpp` + `src/memory_inject.h` patches BeatmapLevelSO objects in RAM after Addressables load, bypassing catalog size + CRC validation.
- **Architecture:** Worker thread waits 30s for game init, scans Il2CppUserAssemblies module for "BeatmapLevelSO" string → finds klass pointer → scans GC heap for objects → patches string fields in-place.
- **Metadata table:** 13 Rolling Stones replacement songs with custom names, artists, and level IDs.
- **String field patching:** In-place UTF-16LE overwrite of song name, artist, level ID. New text must fit within original capacity.
