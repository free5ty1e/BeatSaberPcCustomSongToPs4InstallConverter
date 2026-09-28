# PR Description: Self-Contained Single-Song `--deploy-full` with Clean Slate Workflow

## Summary
This branch implements a complete, self-contained single-song deployment workflow (`--deploy-full`) that enables users to deploy one custom song at a time with full feature support, backed by a true clean-slate backup/restore system. The pipeline now correctly targets the PS4's AFR directory (`/data/GoldHEN/AFR/`) where the plugin reads configuration, and includes comprehensive post-deploy validation.

## Problem Solved
Previously, single-song deployments had several critical issues:
1. **Wrong deploy location** — Files deployed to `/user/app/CUSA12878/` but plugin reads from `/data/GoldHEN/AFR/CUSA12878/`
2. **Silent song conversion failure** — `--download-beat-saver-song` ran AFTER the plugin-only early-exit guard, routing `--deploy-full` to "plugin-only mode" (never downloading/converting the song)
3. **Validation checked all packs** — Post-deploy validation iterated all 4 configured packs instead of just the deployed one
4. **No clean slate** — Backup clean only touched game dir, leaving stale files in AFR dir
5. **False state reporting** — `ps4_state.py` checked wrong directory, reporting clean slate when AFR had stale files

## Changes

### Core Pipeline (`tools/full_custom_song_pipeline.py`)
- **Moved BeatSaver download before early-exit guards** — Fixes Exp 214: `--download-beat-saver-song` now resolves `song_dir` before any mode guard can fire
- **Validation scoping** — `verify_ps4_deployment()` now accepts `packs` filter and threads it through all helper functions (`_get_remote_pack_paths`, `_get_pack_bundle_redirects`, `_get_pack_modes_entries`)
- **Size check priority** — Prefers fresh `custom_songs/` builds over stale `mass_bundles/` for song bundles
- **Default config** — Already correct `afr_base: "/data/GoldHEN/AFR"`; `--generate-config` produces correct config

### Backup Script (`backup-beat-saber-deluxe-files.py`)
- **Added AFR directory clean** — Surgically removes BSD files from `/data/GoldHEN/AFR/CUSA12878/` while preserving `/AFR/test/` and `/AFR/bs_log/`
- **Updated clean logic** — Now cleans both AFR dir and game dir, plus plugins.ini and local caches
- **Fixed plugin removal** — Added `beat_saber_deluxe.prx` to plugin removal list

### State Inspection (`development/scripts/ps4_state.py`)
- **Checks AFR directory** — Lists bundles/configs from `/data/GoldHEN/AFR/CUSA12878/` where plugin actually reads
- **Parses redirects from AFR** — Accurate song/redirect/pack counts
- **Shows game dir separately** — Base game files only
- **Clean slate detection** — Correctly reports "🧹 PS4 is in CLEAN SLATE state" when both AFR and game dir are clean

### Feature Flags (Already Gated)
All runtime features in the plugin are gated behind `features.json`:
- `enable_custom_song_replacements` — Gates song redirects in `open_hook`
- `enable_song_metadata_modification` — Gates MoveNext metadata replacement
- **Defaults to OFF** when missing — Plugin logs "features.json not found — all feature flags OFF"

Pipeline defaults (`DEFAULT_FEATURES`) set both to `true` for production use.

### Documentation Updates
- `README.md` (root & `beat_saber_deluxe/`) — Updated version, clean slate workflow, feature flag rules
- All 10 example docs (5 `.md` + 5 `.sh`) — Added optional clean slate step at top
- Knowledge base — Added `pipeline-afr-base-fix-clean-slate.md`, updated index and feature-flags

## Testing
- **581/581 tests pass** (including new regression tests for download guard ordering)
- **Verified end-to-end**: Clean slate → fresh deploy → validation PASSED
- **PS4 state verified**: 1 custom song, 3 redirects, 1 modified pack, plugin registered

## Example Usage
```bash
# Clean slate (optional but recommended for first song)
python3 /workspace/backup-beat-saber-deluxe-files.py backup --clean-ps4

# Deploy single song (self-contained)
python3 tools/full_custom_song_pipeline.py \
  --download-beat-saver-song 4a901 \
  --target AllTheGoodGirlsGoToHell \
  --pcm16 --no-pad --convert-to-v3 --deploy-full
```

## Version Bumps
- **Pipeline**: v0.5331 → v0.5332 (download guard fix) → v0.5333 (validation scoping + AFR clean)
- **Plugin**: v0.8040 → v0.8041 (build timestamp)

## Files Changed
- `beat_saber_deluxe/tools/full_custom_song_pipeline.py` — Core fixes
- `backup-beat-saber-deluxe-files.py` — AFR clean + plugin removal
- `beat_saber_deluxe/development/scripts/ps4_state.py` — Correct AFR inspection
- `beat_saber_deluxe/ps4_config.json` — Corrected afr_base
- `beat_saber_deluxe/tests/test_pipeline_bugfixes.py` — New regression tests
- `README.md` + `beat_saber_deluxe/README.md` — Updated workflow docs
- 10 example docs/scripts — Added clean slate step
- Knowledge base — New page + index updates
- Experiment log — Exp 214, 215 entries

## Migration Notes
Users with existing local `ps4_config.json` should either:
- Run `--generate-config` to reset to correct defaults, OR
- Manually update `paths.afr_base` to `"/data/GoldHEN/AFR"`

The pipeline default config already has the correct value.