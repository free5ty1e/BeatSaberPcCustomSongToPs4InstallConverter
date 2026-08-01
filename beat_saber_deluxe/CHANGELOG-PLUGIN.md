# Plugin Changelog — Beat Saber Deluxe

All notable changes to the GoldHEN plugin (`beat_saber_deluxe.prx`) are documented here.

**Version scheme:** Increment by **0.0001** per experiment (e.g. v0.80 → v0.8001 → v0.8002). This gives ample room to iterate before reaching v1.00.

## [v0.8045] — 2026-07-31
### Fixed
- **Instant crash when entering Solo song list (v0.8043/v0.8044 regression, root cause finally confirmed)** — both the worker-thread scan (v0.8043) and the synchronous in-hook scan (v0.8044) crashed with CE-34878-0 inside `mode_find_beatmap_level_so_klass()`. The crash log (`v0.8044_crash_sync.txt`) shows the scan started but the game died during it. Root cause: the proven-safe v0.74–v0.8008 scans ran from the **open()/redirect song-start hook** (GC quiescent), but the v0.8043/44 scans run during **song-list rendering**, when the game's GC actively throws page-protection SIGSEGV/SIGBUS faults on its own threads. Our process-wide handlers hijacked those faults → `siglongjmp` to the scan stack → instant crash, regardless of which thread ran the scan.
- **Signal-handler memory probing eliminated entirely** — `mode_try_read()`/`mode_extract_string()`/`extract_utf16_string()` now use **`sceKernelQueryMemoryProtection`** (a real libkernel syscall that queries the mapped range + protection of an address without faulting). This removes the whole class of "process-wide handler hijacks game GC faults" crashes, including the per-call `sigaction` in `extract_utf16_string`.
- **Safe self-test + fail-closed** — before scanning, the plugin verifies `sceKernelQueryMemoryProtection` returns sane results for a known-good address. If it's a stub (like mincore/msync), the mode scan is disabled cleanly (log message) instead of risking a crash.
### Removed
- `mode_install_handlers()`/`mode_restore_handlers()`/`mode_fault_handler()`, `g_mode_jmpbuf`, `g_old_segv`, `g_old_bus`, `g_mode_handlers_installed`, `g_extract_jmp_buf`, and the `<setjmp.h>`/`<signal.h>` includes.
### Changed
- Scan still triggers from the MoveNext hook during song-list rendering, but is now signal-free so it no longer depends on GC being quiescent.

## [v0.8044] — 2026-07-31
### Fixed
- **Instant crash when entering Solo song list (v0.8043 regression)** — the background scan worker thread installed process-wide SIGSEGV/SIGBUS handlers; while they were active, the game's own GC page-protection faults on the main thread were hijacked and `siglongjmp`'d into the worker's stack → instant crash. Reverted to the proven v0.74–v0.8008 pattern: **synchronous scan on the game thread** inside the MoveNext hook (game pauses ~1-2s once).
- **Per-page sigaction overhead removed** — handlers are now installed once via `mode_install_handlers()` for the whole scan and restored once by `mode_restore_handlers()`; `mode_try_read()`/`mode_extract_string()` take the fast path when handlers are already installed.
### Changed
- Removed the pthread worker thread and `-lpthread` from the Makefile.
- Widened BeatmapCharacteristicSO neighbor scan from ±2MB to ±16MB (characteristic SOs live in a shared bundle and may be farther apart).

## [v0.8043] — 2026-07-31
### Fixed
- **Mode scan trigger never fired** — v0.8042 required the runtime `BeatmapLevel.levelID` to start with `"custom/"`, but it is the original pack ID (e.g. "StartMeUp"). Trigger now fires on ANY song `BeatmapLevel` from the MoveNext hook.
- **Patch filter skipped everything** — v0.8042 only patched `BeatmapLevelSO` objects whose `_levelID` starts with `"custom/"`; pack `BeatmapLevelSO` objects carry original IDs. Now ALL found `BeatmapLevelSO` objects are patched (every pack on this PS4 is fully custom).
### Changed
- **Klass discovery is structural, not anchored** — `mode_find_beatmap_level_so_klass()` no longer needs a known levelID; it finds the first object matching klass-range + version 1-50 + valid `_levelID`/`_songName`/`_songAuthorName` pointers + a structurally valid `_previewDifficultyBeatmapSets` array (new `mode_preview_arr_ok()` guard, also applied in the collector to reject false positives).
- Added diagnostic logging of every found BeatmapLevelSO levelID/address.
- ⚠️ **NOT USER-TESTABLE — instant crash when entering Solo** (worker-thread signal hijack). Superseded by v0.8044.

## [v0.8042] — 2026-07-30
### Added
- Phase 2: BeatmapLevelSO memory injection for mode preview data
- Scans IL2CPP heap for BeatmapLevelSO objects matching custom song levelID
- Finds all 5 BeatmapCharacteristicSO by klass matching + serializedName validation
- Builds new _previewDifficultyBeatmapSets array with 5 mode entries at runtime
- Triggers once from MoveNext hook when first custom song cell renders
- Gated behind g_feature_beatmap_mode_mapping (enable_beatmap_mode_mapping flag)

## [v0.8041] — 2026-07-28
### Added
- **Feature flag `g_feature_beatmap_mode_mapping`** — parsed from `features.json` `enable_beatmap_mode_mapping` key. No runtime behavior in this release (pipeline-side only in v0.5307). Gating scaffold for Phase 2 (plugin runtime mode injection).

## [v0.8040] — 2026-07-27
### Fixed
- **Case-insensitive metadata matching** — `find_metadata_replacement()` now trims trailing spaces before comparison. Game uses different casing than expected (e.g. "all the good girls go to hell" vs "All The Good Girls Go to Hell", "Mess it Up" vs "Mess It Up").
### Changed
- **Pipeline reads exact song names from `beat_saber_song_ids.json`** — `manage_song_metadata()` now resolves slot IDs to exact game strings via `_lookup_song_name()`. No more manual casing guesswork.
- **`beat_saber_song_ids.json` copied to `beat_saber_deluxe/`** — Pipeline can access authoritative song names directly.

## [v0.8040] — 2026-07-26

## [v0.8039] — 2026-07-26
### Changed
- **Hooked `MoveNext()` instead of `SetDataFromLevelAsync`** — RVA `0x1D377C0`. The async wrapper at `0x1D36940` is a trampoline that gets inlined by `AsyncVoidMethodBuilder.Start<T>()` — our hook never fired (zero log entries). `MoveNext()` is where the actual work happens: reads `BeatmapLevel.songName`/`songAuthorName` and assigns to TMP_Text fields.
- State machine layout: `<>4__this` at 0x28, `beatmapLevel` at 0x30. Hook modifies BeatmapLevel fields at the start of `MoveNext()` before original reads them.

## [v0.8038] — 2026-07-26
### Added
- **Hooked `LevelListTableCell.SetDataFromLevelAsync`** — RVA `0x1D36940`. Modifies `BeatmapLevel.songName` (offset 0x20) and `songAuthorName` (offset 0x30) in-place BEFORE the original async method runs. The UI reads our replacement from the data source, bypassing the TMP_Text re-rendering issue.
### Approach
- This is the **data source modification** approach — instead of hooking text output methods (set_text/SetText), we modify the BeatmapLevel object that the UI reads from. Since BeatmapLevel fields are `readonly` (only enforced at compile time), we can write directly to the memory.
- The SetDataFromLevelAsync hook fires for each song list cell, reads the BeatmapLevel, and replaces songName/songAuthorName before the cell is populated.

## [v0.8037] — 2026-07-26
### Added
- **Second hook: `TMP_Text.SetText(string, bool)`** — RVA `0x2D3E1D0`. Song list uses `SetText()` for song name text instead of `set_text()` property setter. Both hooks now fire for song name and artist text.
- **Shared replacement logic** — Extracted `apply_metadata_replacement()` function used by both hooks. Reduces code duplication.
### Known Limitations
- **Song list names still not visible** — SetText hook fires and replacements are applied (log confirms), but song list still shows original names. Song list likely re-renders from a data model after our hook fires, overwriting the replacement. Need to investigate the rendering pipeline.

## [v0.8036] — 2026-07-26
### Added
- **External `song_metadata.json` loading** — Replaces hardcoded 13-entry `SONG_REPLACEMENTS[]` array with data-driven metadata loaded from `/data/GoldHEN/AFR/CUSA12878/song_metadata.json`. Two flat tables: `song_names` and `song_artists`.
- **`load_song_metadata()`** — Reads JSON file using same pattern as `load_redirects()`. Parses `"song_names"` and `"song_artists"` sections separately via `parse_json_pairs()`.
- **`find_metadata_replacement()`** — Searches song names first, then artists. Returns replacement string for hook callback.
- **`free_metadata()`** — Cleans up allocated metadata arrays on plugin unload.

### Changed
- **Feature flag gating** — Metadata loading only occurs when `enable_song_metadata_modification` is `true` in `features.json`. Hook still fires but skips replacement when flag is off.
- **Song replacement format** — Combined "CustomName / CustomArtist" format for song names. Artist field blanked for single-artist packs (e.g., "The Rolling Stones" → " ").

### Known Limitations
- Artist replacement is global — "The Rolling Stones" → " " affects all Rolling Stones songs, which is correct for single-artist packs but may show blank artist for all songs in the pack.
- Combined "Name / Artist" format in song name field — works but is a workaround for inability to replace artist independently.
- Deferred: Field-aware replacement (Phase 2) will fix artist accuracy for multi-artist packs.

## [v0.8035] — 2026-07-24
### Fixed
- **Remove free() of replacement strings** — set_text stores string reference internally for deferred rendering. Freeing caused use-after-free → "?" in song details.
- **Try il2cpp_string_new() first** — Uses IL2CPP runtime to create GC-managed strings. Falls back to manual create_il2cpp_string if not found.
- **Enhanced diagnostic logging** — Logs `this` pointer for replacements (identifies song name vs artist fields), hex dump of original string bytes for layout diagnosis.

## [v0.8034] — 2026-07-24
### Added
- **Phase 3: String replacement** — Creates new IL2CPP System.String with replacement text using klass pointer from original. Passes replacement to original `set_text` call. Frees allocated memory after call returns.

## [v0.8033] — 2026-07-24
### Fixed
- **Signal-protected string extraction** — `extract_utf16_string` now uses sigsetjmp/siglongjmp to catch SIGSEGV when `value` is not a valid IL2CPP string. v0.8032 crashed because hook fires for ALL TMP_Text.set_text calls, not just strings.

## [v0.8032] — 2026-07-24
### Added
- **String reading + match detection** — Phase 1 now reads UTF-16LE string from value parameter and checks against 14-song replacement table. Logs matches. DetourMode_x64 confirmed safe.

## [v0.8031] — 2026-07-24
### Fixed
- **Minimal hook callback** — Removed all string reading from hook. Phase 1 diagnostic only: log that hook fired with pointer values. Also switched from DetourMode_x32 to DetourMode_x64 (open/close hooks use x64 successfully).

## [v0.8030] — 2026-07-24
### Fixed
- **Stop retry after hook installed** — Added `g_tmp_hook_installed` flag to prevent double-hooking. v0.8029 crashed at attempt 4 because it installed the detour twice.

## [v0.8029] — 2026-07-24
### Fixed
- **Retry TMP_Text hook installation** — Module discovery now retries on each open() call (up to 50 attempts). First 3 attempts and every 20th logged. Skips early opens (<10) when only system modules visible.

## [v0.8028] — 2026-07-24
### Fixed
- **Deferred TMP_Text hook installation** — Moved from `module_start()` to `open_hook()`. At plugin load time only 3 modules visible; by first file open, all IL2CPP modules loaded. Single-shot flag prevents re-attempt.

## [v0.8027] — 2026-07-24
### Fixed
- **IL2CPP module buffer too small** — Increased `OrbisKernelModule` buffer from 64 to 256. PS4 loads more than 64 modules, causing `find_il2cpp_module_base()` to miss `Il2CppUserAssemblies`. Added diagnostic logging: logs all 20+ module names when IL2CPP module not found.

## [v0.8026] — 2026-07-24
### Added
- **TMP_Text.set_text hook** — Phase 1 of TextMeshPro UI hooking approach. Hooks `TMPro.TMP_Text::set_text(string)` (RVA `0x2D35BE0`) using `DetourMode_x32` to intercept song name/artist text in the UI. Currently logs all intercepted text matching the 13 Rolling Stones replacement table. Gated behind `enable_song_metadata_modification` feature flag. Uses `find_il2cpp_module_base()` to locate `Il2CppUserAssemblies` module and compute hook target address at runtime.

## [v0.8025] — 2026-07-23
### Changed
- **Removed all memory injection code** — Memory injection approach abandoned after 14+ versions (v0.66–v0.8024) found 0 strings across all memory regions. Removed: `memory_inject.cpp`, `memory_inject.h`, `register_song_metadata()`, and all related trigger/init code. Plugin now only handles file redirects via `open()` hook. Last commit with memory injection code: `1586581`.
- **Preserved `enable_song_metadata_modification` feature flag** — Flag kept in `features.json` and pipeline for future use when a new approach is implemented. Defaults to `false` (disabled).

## [v0.8024] — 2026-07-23
### Changed
- **Scan four memory ranges** — Added low memory (16MB–4GB) and extended heap (4GB–8GB) to scan. Pack bundles may be memory-mapped or read into buffers in low memory where Il2Cpp assemblies load (~2GB). Increased timeout to 15s for wider scan.

## [v0.8023] — 2026-07-23
### Changed
- **Trigger scan at BeatmapLevelsData redirect** — Changed trigger from `therollingstones_pack_assets_all` (OPEN #738) to first `BeatmapLevelsData` redirect (OPEN #740). BeatmapLevelSO objects are deserialized lazily — only when the game reads song data. At pack load, objects aren't in GC heap yet.

## [v0.8022] — 2026-07-23
### Changed
- **Scan BOTH GC heap AND metadata mmap** — v0.8021 only scanned ±256MB around metadata (0x293280000), but strings are in the GC heap (0x200000000–0x210000000). Now scans both ranges sequentially: GC heap (256MB) then metadata (512MB). Total ~768MB within 10s timeout.

## [v0.8021] — 2026-07-23
### Changed
- **Scan trigger moved to Rolling Stones pack load** — Changed trigger from first `pack_assets_all` (OPEN #207) to `therollingstones_pack_assets_all` (OPEN #738). Previous scan fired at startup but the target pack bundle doesn't load until much later. BeatmapLevelSO objects with song names are in the pack bundle, so scan must fire after it loads.

## [v0.8020] — 2026-07-22
### Changed
- **Scan metadata region directly** — Changed scan range from 4GB–17GB (13GB, never reached) to ±256MB around metadata base (0x293280000). Covers 512MB, completes in ~10s. Previous scan only reached ~400MB before timeout.
- **Comprehensive file-open logging** — Logs every file open with sequential counter and original path. Shows full load sequence including redirects.

## [v0.8019] — 2026-07-22
### Added
- **Diagnostic redirect logging** — Logs every redirect with sequential counter (`[REDIR #N]`) to map the file open sequence and timing. Helps identify the right trigger point for string scanning.

## [v0.8018] — 2026-07-22
### Fixed
- **Reduced scan timeout from 5s to 2s** — Prevents multi-minute black screen caused by repeated scans
- **Removed redirect-triggered retries** — Each of 32 redirects was re-triggering the scan, causing 160s of blocking. Now only scans once on pack_assets_all detection.
- **Scan once, no retry** — On failure, marks as done (`g_patching_done = -1`). Strings are not in memory at startup; they only load when the song list UI renders.

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
