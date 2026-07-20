# Plugin Changelog — Beat Saber Deluxe

All notable changes to the GoldHEN plugin (`beat_saber_deluxe.prx`) are documented here.

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
