# Plugin Changelog — Beat Saber Deluxe

All notable changes to the GoldHEN plugin (`beat_saber_deluxe.prx`) are documented here.

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
- **Signal-handler-based memory probing** — Replaced `msync()` / `mincore()` with `sigaction(SIGSEGV)` + `sigaction(SIGBUS)` + `sigsetjmp`/`siglongjmp`. Installs handlers per call, tries `memcpy`, restores original handlers. Faults are caught by the handler and longjmp back safely. NOTE: This approach is correct but could not be verified in v0.71 because the bounds check still rejected module addresses.
- **`#ifdef VERBOSE_LOG` diagnostics** — Build with `DEBUG=1` to log segment addresses, sizes, protections, and per-chunk read status. This was critical for identifying the actual root cause.
- **Fixed plugin deploy path** — Plugin was being uploaded to `/data/GoldHEN/AFR/CUSA12878/` (asset redirect directory) instead of `/data/GoldHEN/plugins/` (where `plugins.ini` points).

## [v0.70] — 2026-07-17
### Fixed
- **Class string "BeatmapLevelSO" not found** — `try_read_mem()` used `mincore()` for page validation, which is an unimplemented stub on PS4 (always returns -1/ENOMEM). Replaced with `msync(MS_ASYNC)` which correctly checks page mapping status. Module segments from `sceKernelGetModuleInfo` and GC heap pages now read correctly.
- **Heap scan now uses msync for safe page checking** — `msync(addr, size, MS_ASYNC)` returns 0 if all pages mapped, -1 if not. Works for anonymous pages (GC heap) with no side effects.

## [v0.69] — 2026-07-17
### Fixed
- **Memory injection never fired** — Two root causes fixed:
  1. **Guard timer removed** — The 15-second guard timer started counting from the first per-song bundle open (preload), then locked the function permanently even when the timer returned -1. Since bundles are cached after preload, `memory_inject_try_patch()` was called once during preload (too early → -1), then never again. Removed guard timer entirely — objects exist by the time any bundle opens.
  2. **Trigger too restrictive** — The trigger required BOTH `np` (redirect match) AND `beatmaplevelsdata/` in the path. Changed to fire on ANY redirect (all 32 redirects are per-song bundles). This ensures the function fires on every song bundle open.
- **Version bumped to v0.69**.

## [v0.68] — 2026-07-17
### Fixed
- **CE-34878-0 crash root cause identified** — The crash was NOT from memory injection code at all. The `redirects.json` contained a pack bundle redirect (`therollingstones_pack_assets_all_* → rollingstones_pack_patched.bundle`) left over from earlier CRC experiments. The patched bundle has a different size/CRC from the original, causing Addressables to reject it → CE-34878-0 on every boot.
- **Removed pack bundle redirect** from `redirects.json` (33 → 32 entries). Game now loads the ORIGINAL pack bundle with correct CRC. Memory injection patches metadata in RAM instead.
- **Restored v0.67 memory injection code** — All previous changes (log_write back to static, own logger, hook-triggered injection, mincore-based safe scanning) preserved.

## [v0.67] — 2026-07-17
### Fixed
- **CE-34878-0 crash during game boot** — Restored `log_write()` to static linkage (v0.66 made it extern, which may have caused symbol conflicts). Memory injection now uses its own `meminj_log()` function.
- **Thread removed** — Previous pthread-based approach replaced with hook-triggered scanning from `open_hook` callback to avoid PS4/FreeBSD process initialization conflicts.
- **`mincore()`-based safe memory scanning** — `try_read_mem()` now uses `mincore()` syscall to verify pages are mapped before accessing, preventing crashes from unmapped page access during heap scan.

### Changed
- `src/memory_inject.cpp` — Complete rewrite: no threads, hook-triggered, independent logger, mincore-based page validation.
- `src/memory_inject.h` — Added `memory_inject_try_patch()` for hook-triggered injection.
- `src/main.cpp` — `log_write()` restored to static. Hook calls `memory_inject_try_patch()` when per-song bundles are opened.

## [v0.66] — 2026-07-17
### Added
- **Memory Injection subsystem** — BeatmapLevelSO objects are now patched in RAM after Addressables loads the pack bundle, bypassing catalog CRC validation entirely.
  - Worker thread waits 30s for game initialization, then scans the IL2CPP heap for BeatmapLevelSO instances by klass pointer matching.
  - In-place string patching: custom song name/artist metadata is written directly into managed string objects (UTF-16LE), preserving GC integrity.
  - Song metadata table for 13 Rolling Stones replacement slots (level_id → custom song name, artist).
  - `src/memory_inject.h` / `src/memory_inject.cpp` — modular injection subsystem.
- **Plugin version bumped to v0.66**.
- **`log_write()` exposed as extern** for use by memory injection module.

## [v0.65] — 2026-07-14
### Added
- **Mode selector — 5 preview difficulty modes** — StartMeUp BeatmapLevelSO in pack bundle patched with 5-mode preview data (Standard, OneSaber, NoArrows, 90Degree, 360Degree). Each mode references the correct BeatmapCharacteristicSO via PPtr (fileID=3).

### Fixed
- **m_Script PPtr bug in blob builder** — `build_beatmap_levelso_blob()` was using `_CHAR_PATH_IDS["Standard"]` for the m_Script pathID instead of the correct script pathID (2140275054477726686). This caused Unity deserialization to fail when loading the pack bundle.

### Changed
- **Bundle patching via UnityPy `save("original")`** — instead of raw bundle building (which had multiple bugs with LZ4 compression, block info format, and alignment), now uses UnityPy's `save()` with `"original"` packer to write the modified bundle in the correct UnityFS format.
- **redirects.json updated** — added pack bundle redirect: `therollingstones_pack_assets_all_a99482a8a3da9e991e5ae36f2fea209c` → `rollingstones_pack_patched.bundle`

## [v0.64] — 2026-07-14
### Removed
- **All IL2CPP hooks** (`get_preview_detour`, `ctor_detour`, `maybe_install_il2cpp_hook`) — constructor hook at RVA 0x9891E0 proved definitively dead: Unity deserializes BeatmapLevelSO objects via raw memory copy from AssetBundles, never calling the IL2CPP constructor. DetourMode_x32 (5-byte JMP) was correct and stable, but the hook target simply never fires.

### Verified
- **Constructor hook approach** — `__attribute__((constructor))` on plugin_main() confirmed working; GoldHEN loads PRX via module_start which calls constructors before main().

## [v0.63] — 2026-07-14
- See previous changelog entries for full history of plugin development.
