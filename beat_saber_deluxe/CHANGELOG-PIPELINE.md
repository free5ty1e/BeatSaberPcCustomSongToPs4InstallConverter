# Pipeline Changelog

## v0.5322 (2026-08-16)
### Fixed
- **"Beat Saber still crashes" after the v0.5320 dataIndex fix (Exp 191): the fixed catalog was never deployed.** The v0.5320/v0.5321 pipeline changes were all local — the PS4 still ran the broken v0.5319 `catalog_pack_modes.json` (70/2251 invalid entry dataIndexes, md5 `0eb8a27d…`), so every launch crashed right after the `aa/catalog.json` redirect (OPEN #58/#74) exactly as before. Downloaded the fresh crash log (`.ai_memory/experiment_logs/v0.5321_crash_after_redeploy.txt`), diffed the deployed catalog against the local fixed one (same byte size 795,783 — so size-only checks can never catch this), confirmed the deployed file was the stale broken build, then deployed the fixed catalog (md5 `975bacca…`, 0 invalid) and re-validated on-device.
- **`--verify-ps4` could not catch a stale catalog (root cause of "didn't notice the fix never deployed"):** size checks pass because the broken and fixed catalogs are byte-identical in size. Added check #7 to `verify_ps4_deployment()` that downloads the deployed `catalog_pack_modes.json` and (a) validates every `m_EntryDataString` dataIndex points at a type-7 block start via the new `validate_catalog_dataindexes()`, (b) compares the deployed md5 against the local build output, and (c) verifies every configured pack's catalog block carries the patched `m_Crc`/`m_BundleSize` via the new `validate_catalog_entries()`. A stale catalog now fails the post-deploy validation loudly instead of passing silently.
### Changed
- **Removed the legacy `pack_bundle` single-pack prototype from the DEFAULT config** (`startmeup_pack_modes.bundle` / `catalog_startmeup_modes.json`). It was fully superseded by the generalized `pack_modes` block (the rollingstones pack is in `pack_modes.packs`), its deployed files were cleaned off the PS4, and keeping it made `--verify-ps4` report phantom "MISSING on PS4" entries for the deleted prototype. The `pack_bundle` code path remains supported for configs that still define it (covered by existing tests); the default no longer does.
- Added `validate_catalog_dataindexes()`, `find_catalog_entry_js()`, `validate_catalog_entries()` to `tools/build_pack_mode_bundles.py` as reusable catalog-integrity helpers (byte-wise type-7 block walk — never whole-string UTF-16 alignment).
- Cleaned up stale experiment files on the PS4: deleted `catalog_startmeup_modes.json` and `startmeup_pack_modes.bundle` (legacy prototype, unreferenced by the 43-entry redirects.json).
- Pipeline version bumped 0.5321 → 0.5322.

## v0.5321 (2026-08-15)
### Fixed
- **Reproducibility: `build_pack_mode_bundles.py` kept a leftover `"360Degree"` entry in `CHAR_PATH_IDS`** (pid `4533580413116749821`) from before the Exp 175 360Degree purge. Because `build_modes_blob` extends *any* set whose pid is in `CHAR_PATH_IDS.values()` to `TARGET_DIFFS`, the production module padded the (PS4-unsupported, selector-hidden) 360Degree preview set 1→5 diffs (+144 B per patched blob) for every pack that ships one — producing bundles that did **not** byte-match the committed dev-built artifacts for 10/36 packs (ostvol1, ostvol2, ostvol3, extras, greenday, imaginedragons, monstercat, panicatthedisco, rocketleague, timbaland). Removed the stale entry; the module now reproduces all 36 committed bundles byte-identically (verified full rebuild, 0/36 mismatches). Regression test added (`test_unsupported_360degree_set_not_extended`).
### Changed
- Pipeline version bumped 0.5320 → 0.5321.

## v0.5320 (2026-08-15)
### Fixed
- **PS4 launch crash after pack_modes deploy (Exp 188 follow-up): entry dataIndexes in the merged catalog were stale.** `m_EntryDataString` is a binary array of 28-byte records whose 5th int32 (`rec[4]`) is a byte offset into `m_ExtraDataString` pointing at the start (type byte) of each per-entry block. When a patched block's JSON grows or shrinks (e.g. lizzo's `m_Crc` went 7 → 10 digits, +6 bytes), every later block shifts, so every entry dataIndex pointing *past* the patched block MUST be shifted by the same delta — otherwise the game reads garbage and crashes right after loading the catalog (v0.5319 PS4 crash at OPEN #74). `update_catalog_entry()` now rewrites `m_EntryDataString` shifting all affected dataIndexes whenever a block's byte length changes. 70 of 2251 entries were invalid before the fix (all after the lizzo block); 0 after.
- **`_parse_catalog_block()` token-split fragility:** `m_Crc`/`m_BundleSize` were extracted by splitting the block on `,` and taking the text after `:`. If a field is the last one in the JSON, the token includes the trailing `}` and the value-replace would strip the block's closing brace, corrupting the JSON. Now parsed with regex (`"m_Crc":\s*(\d+)`), robust to field order.
### Changed
- **Pack-mode tests are now fully config-driven — no hardcoded packs.** Real-artifact tests (`TestPackModesRealArtifacts`) derive the pack list from the live pipeline config (`cfg['pack_modes']['packs']`) and the build manifest, so they validate whatever subset of the 36 DLC packs a user configures, not the 4 defaulting packs. Synthetic fixture data was renamed to clearly-fake `demopacka`/`demopackb` so no test couples to real pack names. Added 5 regression tests (dataIndex shifting for single/multiple growing blocks, size growth, plus a real-artifact merge test asserting every dataIndex lands on a type-7 block start).
- Merged catalog regenerated from origin via `_regenerate_merged_catalog()` with the fixes (0 invalid dataIndexes, all 4 pack CRCs/sizes match the manifest).

## v0.5319 (2026-08-14)
### Added
- **Generalized pack patch (Exp 188): ALL DLC packs get 4 preview mode sets (Standard/OneSaber/NoArrows/90Degree) × 5 difficulties**, superseding the single-pack rollingstones prototype. New production module `tools/build_pack_mode_bundles.py` patches every replaced BeatmapLevelSO in a pack bundle (extending short mode sets to 5 diffs, cloning missing modes from Standard, preserving existing records byte-for-byte), rebuilds the UnityFS/LZ4 bundle with a corrected object table, and regenerates the Addressables catalog entry (`m_Crc` = crc32 of the *decompressed* stream + `m_BundleSize`) into a single **merged catalog** (`catalog_pack_modes.json`) built from the ORIGIN catalog.
- **`pack_modes` config block** (`packs`, `build_dir`, `song_ids_path`, `dump_dir`, shared `catalog_key`/`patched_catalog`) defaulting to the 4 packs already verified on-device: therollingstones, billieeilish, lizzo, camellia.
- **`_ensure_pack_mode_bundles()`** — builds any configured pack whose patched bundle is missing (skip-if-no-change), and regenerates the merged catalog to exactly match the current redirect set. **`--build-pack-modes`**, **`--force-pack-modes`**, **`--pack-modes-packs`**, **`--deploy-pack-modes`** CLI flags.
- **`adopt_pack_modes_manifest.py`** dev script — one-time adoption of the 36 bundles built by the old dev tooling into the production manifest (`pack_modes_bundles/manifest.json`, records per-pack size + dec-stream CRC + catalog bundle name) so the pipeline treats them as already-built.
- **Single source of truth for redirects:** `_get_pack_bundle_redirects()` now merges the single-pack prototype pair FIRST and the `pack_modes` redirects LAST, so pack_modes override the rollingstones/startmeup prototype (merged catalog carries the rollingstones entry too). Redirects for a pack are only emitted once its patched bundle exists locally, and the shared `aa/catalog.json` redirect only once the merged catalog exists — the pipeline never points a redirect at a file that isn't ready (Exp 180 crash rule).
- Tests: `tests/test_pack_mode_bundles.py` (21 tests) — synthetic-blob mode expansion, byte-wise catalog entry updates, deterministic entries/redirects, override semantics, and real-artifact CRC/size verification of the merged catalog against the built bundles. Full suite 440/440 pass.

### Fixed
- **Catalog `m_ExtraDataString` updates now walk the binary block structure byte-wise** instead of substring-searching a whole-string UTF-16 decode. The concatenated per-entry blocks (type byte + 1-byte-len assembly/class names + 4-byte JS length + UTF-16-LE JSON) can start at odd byte offsets, so a whole-buffer decode misaligns some blocks and the marker becomes unfindable — camellia's entry failed this way. `update_catalog_entry()` now parses each block (as the scan does), patches only the matching block's JSON in place, and resizes the length field when the digit count changes.
- **Object-table rebuild logic bugs in the pack patcher** (from `development/scripts/build_all_pack_modes.py`, now fixed in the production module): (1) cumulative offset deltas applied in a single pass (each object's stored offset shifts by the sum of deltas of patches *starting before it*; a patched blob's own offset is unchanged), (2) a patched blob's `byte_start` is no longer shifted by its own delta — only its size field updates, (3) the mode-set extension now checks `pid in CHAR_PATH_IDS.values()` (keys are mode names).

### Changed
- **Deploy ordering (Exp 188):** patched pack bundles + catalogs are deployed BEFORE `redirects.json` is generated (Step 9a before Step 9), so `pack_modes` redirects — which are only emitted for packs whose bundles exist locally — are picked up by redirect generation, and the redirected files are already on the PS4 when the game boots.
- `deploy_pack_bundle()` now also builds-if-missing + deploys `pack_modes` when configured; `verify_ps4_deployment()` steps 4–5 validate every pack redirect + the shared catalog redirect pair, not just the single-pack pair.

## v0.5318 (2026-08-13)
### Fixed
- **Redirect VALUES must match the exact deployed bundle filename (Exp 187).** The game opens the redirect VALUE verbatim and `open()` is case-sensitive, so a value like `Crystallized_v3` silently keeps serving the stale Jul/Aug build while the freshly mass-deployed bundle sits on the PS4 as `crystallized_v3.bundle`. The Aug-13 redeploy uploaded all 38 new bundles correctly, but the generated `redirects.json` still pointed at old `_v3` names (and titlecase Camellia names) — the game would never have loaded the new builds. The pipeline now has a single source of truth for deployed bundle naming: `_deployed_bundle_name()` builds `{slot}{afr_target_suffix}` using the canonical slot casing from `mass_deploy.slots`, and `_ensure_mass_song_redirects()` (run on every config save, like the pack/catalog pair) rewrites every per-song value to that exact filename, preserving known-good keys while healing stale values. Default `afr_target_suffix` is now `_v3.bundle` (was `_v3`) so single-song deploys, mass deploys, and redirect values all converge on the same filenames.
- **`deploy_mass_bundles` / `deploy_to_ps4` now upload under the exact filename the redirect will reference** (local file basename), so a future rename can never split "what's deployed" from "what the redirects point at".
### Changed
- `manage_redirect_config()` dropped its `bundle_suffix` parameter — target entries use `_deployed_bundle_name()` (canonical slot casing + suffix) instead of the caller-provided suffix string, eliminating the class of bug where the suffix used for uploading and the suffix used for redirects diverged.
### Added
- Regression tests: `TestDeployedBundleNaming` (6 tests) — slot-casing canonicalization, stale `_v3`/titlecase value healing, missing-slot insertion, default suffix fallback. Full suite 419/419 pass.

## v0.5317 (2026-08-13)
### Fixed
- **PS4 crash at boot when the pack bundle is redirected without the catalog (Exp 180 root cause).** Unity validates a bundle against the `m_Crc` in `aa/catalog.json` at load time (crc32 of the *decompressed* stream, Exp 179). The patched pack bundle (`startmeup_pack_modes.bundle`) has a different dec-stream CRC than the original, so serving it against the ORIGINAL catalog → CRC mismatch → crash during the pack scan (observed: died at ~[OPEN #591] with a 39-redirect config that dropped `aa/catalog.json` and pointed the pack at the stale `rollingstones_pack_patched.bundle`).
- **The pipeline now enforces the pack bundle + catalog redirect pair on every config save.** `manage_redirect_config` always calls `_ensure_pack_bundle_redirects()`, which (a) (re)inserts `aa/catalog.json -> catalog_startmeup_modes.json` and `therollingstones_pack_assets_all_*.bundle -> startmeup_pack_modes.bundle`, and (b) removes stale truncated-key variants that could shadow the canonical entry via the plugin's substring matching. A regenerated/synced/enforced `redirects.json` can no longer silently lose the pair that causes the boot crash. Regression tests: `TestPackBundleRedirectConsistency` (6 tests).
### Added
- **`--deploy-pack-bundle`** — uploads the patched pack bundle + patched `catalog_startmeup_modes.json` to the PS4 (both files must exist before `redirects.json` references them).
- **`--deploy-mass-bundles`** — deploys all custom song bundles from `mass_deploy.bundle_dir` (38 slots) to the PS4; replaces the manual `deploy_all38.sh` loop.
- **`--verify-ps4`** — post-deploy self-validation that reports PASS/FAIL for: PS4 reachability, deployed `redirects.json` matching local, every redirect target existing on the PS4, the pack bundle + catalog files present, the pack+catalog redirect pair intact, and redirect target sizes matching local files. **Auto-runs after any `--deploy*` invocation** (opt out with `--no-verify-ps4`), so a broken deploy is caught immediately instead of on the next console boot.
- **`mass_deploy` + `pack_bundle` config defaults** in `load_config` so the pipeline is all-inclusive with zero manual config steps.
### Changed
- `--deploy-mass-bundles`/`--deploy-pack-bundle`/`--verify-ps4` are usable standalone (no `--song-dir`) and automatically regenerate + deploy a consistent `redirects.json` first.

## v0.5316 (2026-08-12)
### Fixed
- **Mode generators crash on V3 beatmaps with omitted position fields.** Some BeatSaver sources (e.g. "Take Me to the Beach" for the `livebythesword` / `IDidntChangeMyNumber` slots) ship V3 notes with `y` (and sometimes `b`) omitted — valid per the V3 spec, where omitted fields default to 0. The OneSaber generator indexed `n["y"]`/`n["x"]` directly → `KeyError: 'y'`; the 90Degree generator indexed `n["b"]`/`obs["b"]`/`ev["b"]` directly. All generator field reads now use `.get(..., 0)` defaults for V3, matching the V2 branch. Regression tests: `test_v3_omitted_position_fields_default_to_zero` (OneSaber + NoArrows) and `test_v3_omitted_fields_in_90_degree`.

## v0.5315 (2026-08-11)
### Fixed
- **Idempotency bug in mode mapping:** re-running the pipeline on a source dir that already contains generated mode `.dat` files (e.g. a prior run's output, or hand-authored modes) silently skipped TextAsset injection and fell back to cloning Standard references — producing a *different, degraded* bundle than the first build. `apply_mode_mapping()` gated injection on `song_dir AND non-empty generated_files`, but `add_mode_characteristics()` already scans `song_dir` for ALL mode files (pre-existing included). The gate now only requires `song_dir`, so a rebuild of a previously-built song dir yields a byte-equivalent, fully-populated bundle. Regression test: `test_idempotent_injection_with_pre_existing_mode_files`.
- Tests: full suite pass (405/405; +1 idempotency regression).

## v0.5314 (2026-08-11)
### Changed
- **Safe-by-default pipeline — standard command now bakes in the previously-required flags.** PCM16 + no-pad are now the DEFAULT audio settings, beatmap mode mapping + generation is ON by default, and V2→V3 conversion is ON by default. A plain `--song-dir X --target Y` build now produces a full-length, lossless, all-modes-populated bundle — no partial songs from a forgotten flag.
- **Each new default has an oppose flag** (per project rule: any changed default needs a way to opt out):
  - `--hevag` / `--vorbis` — opt out of the PCM16 default codec.
  - `--pad-fsb5` — restore the old 12MB truncating padding (DANGER: produces partial songs; kept only for the rare case a slot needs exact-size resources).
  - `--disable-beatmap-mode-mapping` — Standard-only bundle (opposes the new default).
  - `--skip-mode-generation` — keep mode mapping but do not generate missing mode beatmaps.
  - `--no-convert-to-v3` — leave V2 beatmaps unconverted (opposes the new default).
  - The old flags (`--pcm16`, `--no-pad`, `--enable-beatmap-mode-mapping`, `--convert-to-v3`) are kept for backward compatibility and now match the defaults.
- **`--features-only` standalone mode added:** apply `--set-feature key=value` changes and deploy `features.json` to PS4, then exit — no song processing, no plugin rebuild, no redirects. Audit found no standalone features-only mode previously existed; `--set-feature` only ran via `--deploy-plugin` or as a step of a full song build.
- **`enable_beatmap_mode_mapping` removed from `features.json` / `DEFAULT_FEATURES`.** Mode mapping is a build-time pipeline feature (baked into the bundle), not a runtime plugin toggle — the v0.8040 plugin never parsed it. `features.json` now holds exactly the runtime flags the plugin reads at startup (`enable_custom_song_replacements`, `enable_song_metadata_modification`), so every flag in the file is handled the same way: read at runtime from the PS4 JSON, redeployable via `--features-only`.
- Flag resolution moved to testable pure helpers: `resolve_audio_codec()`, `resolve_pad_to_size()`, `resolve_mode_mapping()`, `resolve_convert_to_v3()`.
- Tests: +17 (default behavior resolution + runtime-only feature flags). Full suite 404/404 pass.

## v0.5313 (2026-08-10)
### Fixed
- **90° rotation events now survive V2→V3 conversion (source song's 90Degree Expert keeps its lane changes):** `convert_v2_to_v3()` no longer hardcodes `"rotationEvents": []`. V2 spawn-rotation events (types 14/early, 15/late) are converted to V3 `rotationEvents` (`e` 0/1) with the authoritative BSMG value table → signed degrees: `0=-60, 1=-45, 2=-30, 3=-15, 4=+15, 5=+30, 6=+45, 7=+60`. Values are relative deltas the game accumulates. Laser-speed events (types 12/13) correctly remain basic events.
- **V3 basic event type field corrected `t` → `et`:** The game's `BeatmapSaveDataVersion3.BasicEventData` serializes the event type as `et` (confirmed from the PS4 il2cpp dump). The converter previously wrote `t`, so every lighting event deserialized as type 0 (BackLasers). Lighting now uses its real event types.
- **`_generate_90_degree()` rewritten with correct 90° gameplay semantics** (previously swung the lane ±90° every cycle — perpendicular to the player and disorienting):
  - 90° mode confines the playfield to a 90° arc centered on the player's forward lane: positions 0° (center), ±15°, ±30°, ±45° (3 lanes left + 3 right).
  - One `rotationEvents` entry per `cycle_beats` (default 8.0), each moving a single 15° lane in the current sweep direction; the sweep starts at the center lane and reverses only after reaching a ±45° extreme — it never skips lanes or jumps the center.
  - Uses `e: 1` (late rotation) per BSMG best practice (chevron guides the player after the block hit).
  - Constants renamed: `_ROTATION_DEGREES` → `_ROTATION_STEP_DEGREES` (15) + `_ROTATION_MAX_DEGREES` (45).
- **Spec verified against two ground truths:** (1) BSMG wiki Extended Mapping / Map Format pages; (2) the community 90° map `Drop Pop Candy 90DegreeExpert.dat`, whose 340 rotation events (values 3/4 = ±15°, a few 2/5 = ±30°) accumulate to exactly [-45°, +45°] — confirming relative-delta semantics and the 90°-mode arc limit. The user's observed behavior (old generator alternating +90/-90 produced "center ↔ perpendicular" switching) independently confirms V3 `r` accumulates.

## v0.5312 (2026-08-09)
### Fixed
- **Characteristic path IDs corrected repo-wide (90Degree mode selector now enabled):** The BeatmapCharacteristicSO pathIDs were mislabeled in `_CHAR_PATH_IDS` / `CHAR_PATH_IDS` across `tools/full_custom_song_pipeline.py`, `tools/build_patched_pack_bundle.py`, `tools/build_per_song_metadata.py`, `tools/build_replacement_pack*.py`, `tools/inject_pack_bundle.py`, `tools/patch_pack_bundle.py`, and the `development/scripts/build_espresso*` dev scripts. Verified against the real BeatmapCharacteristicSO objects in `sharedassets_assets_all_068cd59e9a6fba13da706dc9269bf759.bundle` (CAB `cb38b3e2985c65d4cf8a63437da74a89`):
  - Standard `-7286399427822119286` (unchanged)
  - OneSaber/OneColor `-5623662769225589684` (was NoArrows)
  - NoArrows `-8583864861369561029` (was OneSaber)
  - 90Degree `-5995858427784384822` (was 360Degree's `4533580413116749821`)
  - 360Degree `4533580413116749821`
  - **Why it matters:** the 90Degree slot previously pointed at the 360Degree characteristic (`requires360=1`), so the game hid the selector button — 90Degree was never visible. The OneSaber/NoArrows swap was cosmetic (each PID drives its own button AND gameplay lookup) but is now also corrected for clarity.
- **Pack bundle rebuilt & redeployed:** `startmeup_pack_modes.bundle` now has all 4 preview sets pointing at the correct characteristics (Standard/OneSaber/NoArrows/90Degree); `catalog_startmeup_modes.json` regenerated with the new dec-stream CRC (0xe9e40bd3 → `3924036563`) and size (7,905,425 B). Deployed to PS4, `bs_log.txt` cleared.

## v0.5311 (2026-08-09)
### Changed
- **Test template shrunk 12 MB → 2.9 KB (no audio):** Added `development/scripts/build_test_template.py` which regenerates `tests/test_data/template_standard.bundle` from any per-song bundle. The template now contains ONLY a Standard-only BeatmapLevel + its 5 beatmap TextAssets + lightshow TextAsset + m_Script target — all audio (AudioClip, audio TextAsset, external `.resource` file) is stripped and beatmap/lightshow payloads are replaced with minimal placeholder JSON. This keeps the repo lean and avoids shipping 12 MB of song audio as test fixture.

### Fixed
- **TextAsset binary serialization:** Fixed `_create_text_asset_object()` to use UnityPy's `EndianBinaryWriter.write_aligned_string()` instead of manual `struct.pack`. The previous format added null terminators and used `len+1` for string lengths, which caused `read_typetree()` to fail with "read_str out of bounds" on the PS4 Unity runtime. The correct Unity format is: `int32 length + UTF-8 bytes + 4-byte alignment padding` (no null terminator in length, no null after data).
- **type_id for new TextAsset objects:** Fixed `_create_text_asset_object()` to use the correct type index from `cab.types` instead of hardcoded `type_id=0`. Previously, new objects were assigned `type_id=0` which mapped to MonoScript (class_id 115) instead of TextAsset (class_id 49), causing the game to misinterpret the object type.
- **Mode file matching:** Fixed gen_lookup matching in `add_mode_characteristics()` to handle both prefix (`90DegreeExpert.dat`) and suffix (`Expert90Degree.dat`) naming conventions. Previously, 90Degree Expert and ExpertPlus files with prefix-style naming were not detected, leaving those difficulty slots pointing to Standard beatmaps.
- **generated_files parameter usage:** Fixed `add_mode_characteristics()` to use the `generated_files` parameter in addition to scanning `song_dir`. Previously, generated files passed via the parameter were ignored if they weren't written to disk first.
- **Test fix:** Fixed `TestModeBeatmapInjection.test_injected_beatmaps_reference_new_textassets` to properly handle BundleFile format and save/reload the bundle before verifying typetree changes. Added `test_data/template_standard.bundle` for test isolation.

## v0.5310 (2026-08-07)
- **Beatmap Mode Generators — Fully Implemented (default when `--enable-beatmap-mode-mapping`):**
  - `_generate_no_arrows()` — real implementation, V2/V3-aware: converts every color note to a dot (`_cutDirection`/`d` = 8); bombs untouched.
  - `_generate_one_saber()` — real implementation (replaces placeholder): recolors all notes to a single saber (color 0), removes simultaneous notes (one saber can cut only one note per instant) and same-cell arrowed notes closer than `min_gap` (default 0.25 beats). Never mutates its input.
  - `_generate_90_degree()` — real implementation (replaces placeholder): converts V2 sources to V3, then adds `_rotationEvents` alternating +90/-90 every `cycle_beats` (default 8.0 beats = 2 measures) starting at the first note, swinging the lane back and forth. Never mutates its input.
  - Added `generate_missing_mode_beatmaps(song_dir, detected_modes, enabled_modes, ...)` — gap-filling: for each difficulty with a Standard source, generates `<Diff><Mode>.dat` for every enabled mode the song does NOT already provide (songs' own mode beatmaps are never overwritten).
  - **Integration fix:** mode generation now runs in Step 5a, BEFORE beatmap replacement (previously it ran after `replace_beatmaps` and wrote files too late to be consumed). Generation is the default behavior whenever `--enable-beatmap-mode-mapping` is passed.
  - New CLI flags: `--skip-mode-generation` (opt out), `--one-saber-min-gap` (default 0.25), `--rotation-cycle-beats` (default 8.0).
  - Expanded `tests/test_mode_generators.py` from 3 placeholder assertions to 17 tests (V2+V3, mutation-safety, gap-filling behavior). Full suite: 365 tests pass.

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
