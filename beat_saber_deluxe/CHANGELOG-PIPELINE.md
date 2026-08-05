# Pipeline Changelog

## v0.5309 (2026-08-04)
- **Beatmap Mode Generators (In Progress):**
  - Added procedural beatmap generator logic for `NoArrows` mode (automatically strips direction arrows from Standard beatmaps).
  - Placeholder implementations added for `OneSaber` and `90Degree` generators.
  - Integration: Pipeline now generates missing mode-specific `.dat` files procedurally during bundle construction if they are enabled via flag.

## v0.5308 (2026-08-04)
- **360Degree Mode Purge:**
  - Removed all `360Degree` mode support from pipeline (`full_custom_song_pipeline.py`), tools, and tests as 360° gameplay is physically unsupported on PS4 single-camera ~90° tracking.
  - Restricted supported modes to 4: `Standard`, `OneSaber`, `NoArrows`, `90Degree`.
  - Updated all test suites and pipeline defaults to 4 modes.

## v0.5307 (2026-07-28)
- **Beatmap mode mapping (Phase 1):**
  - Added `detect_song_modes(song_dir)` — auto-detects characteristic modes from beatmap .dat/.json filename patterns. Handles suffix-style (`ExpertPlusOneSaber.dat`), prefix-style (`OneSaberExpert.dat`), bare (`Expert.dat` → Standard), and `.beatmap.dat` variants. Aliases: `SingleSaber`→`OneSaber`, `Lawless`→`NoArrows`, `Legacy`→`Standard`. Excludes `Info.dat`, `BPMInfo.dat`, `Lightshow`, `AudioData`. Returns canonically-ordered difficulty lists per mode.
  - Added `build_mode_mapping(detected_modes, fallback_mode_map)` — resolves the 5 game characteristic slots using detected modes with configurable fallback chain. Default: `360Degree→NoArrows→Standard`, `NoArrows→Standard`, `90Degree→Standard`, `OneSaber→Standard`. Custom overrides via `SRC=DEST` format.
  - Added `apply_mode_mapping(cab, enabled_modes)` — calls existing `add_mode_characteristics()` to inject new mode sets into the per-song bundle's BeatmapLevel.
  - New CLI flags: `--enable-beatmap-mode-mapping`, `--fallback-mode-map SRC=DEST`.
  - Feature flag `enable_beatmap_mode_mapping` added to `DEFAULT_FEATURES` (default `True`) and `features.json`.
  - 22 new unit tests + 4 new integration tests — 361 total.
  - `beat_saber_song_ids.json` enriched with `characteristicModes` field for all 305 songs (94 multi-mode) from bundle scan.

## v0.5306 (2026-07-28)
- **Integration testing:**
  - Expanded `test_integration.py` from 1 test to 34 tests covering: PCM16 FSB5 build, V2→V3 beatmap conversion, beatmap file selection priority, redirect config management, song metadata management, song ID lookup, config loading, and metadata file handling.
  - Fixed 7 pre-existing test failures in `test_pipeline_bugfixes.py::TestManageSongMetadata` — tests updated to match current `manage_song_metadata()` behavior (combined "SongName / Artist" format, original author blanking).
  - Total test suite: 335 tests across 10 files (up from 302).
- **Agent context:**
  - Added `.agent/context.yml` — compact quick-reference file for giving project context to another agent with minimal token usage.
  - Added context.yml update rule to both `CLAUDE.md` and `.opencode/rules.md` (Section 1 item 7, Section 3.1 item F2).
  - Synced missing Section 0 (Rule Synchronization) to `.opencode/rules.md`.

## v0.5305 (2026-07-27)
- **CI/CD Infrastructure:**
  - Fixed failing lint check in CI pipeline. Ruff configuration was using incompatible `--output-format=github` and `--statistics` flags simultaneously. Removed `--statistics` to fix the pipeline error.

## v0.5304 (2026-07-27)
- **Bug fixes:**
  - Fixed `info.dat` case sensitivity — BeatSaver uses lowercase `info.dat`, pipeline now falls back to lowercase when uppercase `Info.dat` is not found. Affects `main()` pre-load, Step 6.5 re-read, and `replace_beatmaps()`.
  - Fixed undefined variables in `main()` — `bpm`, `song_name`, `song_artist`, and `note_count_standard` were referenced before being defined. Now initialized from Info.dat before Step 0.
  - Fixed `manage_song_metadata()` passthrough — When `--song-name`/`--artist` not provided via CLI, resolved values from Info.dat are now passed through to metadata management.
- **Unit testing infrastructure:**
  - Added `run_tests.py` test harness with `--fast`, `--coverage`, `--module`, `--lint`, `--ci` options
  - Added GitHub Actions CI workflow (`.github/workflows/ci.yml`) — runs all tests with coverage on push/PR
  - Added `requirements-test.txt` for CI dependency installation
  - Added 39 new tests in `test_pipeline_bugfixes.py` covering all three bug fixes
  - Fixed broken `test_hevag_audio_compatibility.py` (syntax errors, wrong function names)
  - Updated `pyproject.toml` with ruff linter config and improved coverage settings
- **Test suite:** 301 total tests across 8 test files (up from 262)

## v0.5303 (2026-07-26)
- **Song ID lookup** — Added `_load_song_ids()` and `_lookup_song_name()` functions. Pipeline now resolves slot IDs (e.g., "StartMeUp") to exact game strings via `beat_saber_song_ids.json`. Fixes case sensitivity issues where game uses different casing than expected.
- **`beat_saber_song_ids.json` added** — Copied from `.agent/beat_saber_song_ids.json` to `beat_saber_deluxe/` for pipeline access.
- **`manage_song_metadata()` updated** — Now resolves `target_name` to exact game song name before writing to `song_metadata.json`.

## v0.5302 (2026-07-26)
- **Song metadata management** — Added `manage_song_metadata()` function and `--song-name`/`--artist` CLI arguments. Generates/updates `song_metadata.json` with song name and artist replacements for the TMP_Text hook.
- **Auto-deploy on `--deploy`** — `song_metadata.json` is automatically deployed to PS4 alongside `redirects.json` and `features.json` when `--deploy` is used.
- **`deploy_all.sh` updated** — Step 3.5 now deploys `song_metadata.json` to `/data/GoldHEN/AFR/CUSA12878/song_metadata.json`.
- **Feature flag default updated** — `enable_song_metadata_modification` defaults to `false` in `DEFAULT_FEATURES`.

## v0.5301 (2026-07-19)
- **Feature flags support** — Added `--set-feature key=value` CLI argument. Writes `features.json` locally and deploys it to PS4 via FTP.
- **Supported flags:** `enable_custom_song_replacements` (default: false), `enable_song_metadata_modification` (default: false — preserved for future use)
- Usage: `--set-feature enable_song_metadata_modification=true` or `--set-feature enable_custom_song_replacements=false`
- **BeatSaver API override** — Added `--beatsaver-api-base` to override the default BeatSaver API URL (useful for mirrors/local servers).

## v1.49 (2026-07-17)
- **Uncompressed block independence test FAILED:** Critical finding that 49 uncompressed blocks (flag=0) are part of a shared decompressed stream, NOT independent storage. Modifying their content changes file_size by ~817-2,177 bytes due to cascading compression ratio effects.
- **Option B BLOCKED:** Uncompressed block injection approach cannot achieve zero size impact — blocks are not independent storage as initially hypothesized.
- **New fallback identified:** Memory injection (patch BeatmapLevelSO in RAM after Addressables load) as alternative to pack bundle modification.

## v1.48 (2026-07-17)
- **Size + CRC dual validation confirmed:** Both `m_BundleSize` and `m_Crc` in Addressables catalog must match simultaneously or game crashes with CE-34878-0
- **Root cause of size difference identified (Exp 155):** Decompressed stream grows by exactly the blob size delta (+817 bytes for Espresso blob replacing original BeatmapLevelSO). Remaining ~1,895 bytes from bundle rebuild overhead.
- **Viable approach identified:** Uncompressed block injection — 49 blocks (flag=0) are stored as fixed-size raw data; modifying content affects CRC but NOT file_size. Provides ~6.1 MB of free variables for CRC control.
- **Knowledge base updated** with detailed size analysis and Option B approach documentation.

## v1.47 (2026-07-17)
- **CRC correction via GF(2) linear algebra works:** Achieved exact CRC match `0xdc8b314f` using alignment padding bytes for correction. Bundle size differs by +2,712 bytes; `m_BundleSize` validation in catalog causes crash when size doesn't match.
- **New tool added:** `build_patched_pack_bundle.py` in `tools/` — proven working CRC correction via GF(2) linear algebra on 9 alignment padding bytes. Produces rollingstones_pack_patched.bundle (7,905,515 bytes).

## v1.46 and earlier
- See previous changelog entries for full history of pipeline development.
