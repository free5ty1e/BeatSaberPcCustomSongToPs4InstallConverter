---
name: pipeline-afr-base-fix-clean-slate
description: "Fixed pipeline default AFR base path and backup script clean to target /data/GoldHEN/AFR instead of /user/app"
metadata:
  type: reference
---

# Pipeline AFR Base Path Fix + Clean Slate Workflow (v0.5333)

**Introduced:** v0.5333 (Exp 215, 2026-09-11)

## The Problem

The pipeline's default config already had the correct `afr_base: "/data/GoldHEN/AFR"`, but the user's local `ps4_config.json` had a stale value `/user/app`. The plugin hardcodes `AFR_BASE = "/data/GoldHEN/AFR"` (main.cpp:23) and reads `redirects.json`, `features.json`, `song_metadata.json` from `/data/GoldHEN/AFR/CUSA12878/`. However:

1. **Deploy was going to wrong location** — bundles, `redirects.json`, `features.json`, `song_metadata.json`, `catalog_pack_modes.json` were deployed to `/user/app/CUSA12878/` instead of `/data/GoldHEN/AFR/CUSA12878/`
2. **Backup clean didn't touch AFR dir** — `backup --clean-ps4` only cleaned `/user/app/CUSA12878/`, leaving stale BSD files in the AFR dir where the plugin actually reads from
3. **ps4_state.py reported false clean slate** — it only checked the game dir, not the AFR dir

Result: Game showed "original songs" because plugin couldn't find config, and `ps4_state.py` falsely reported clean slate.

## The Fixes

### 1. Pipeline Default Config (Already Correct)
The pipeline's built-in default config at line 63 already has:
```json
"afr_base": "/data/GoldHEN/AFR"
```
The `--generate-config` flag produces this correct default. The user's local `ps4_config.json` was stale.

### 2. Backup Script Clean (Fixed)
Updated `backup-beat-saber-deluxe-files.py` `clean_ps4()` to surgically clean BOTH locations:

**AFR directory (`/data/GoldHEN/AFR/CUSA12878/`)** — NEW:
- Removes `*_v3.bundle`, `*_custom_v3.bundle`, `*_pack_modes_assets_all_*.bundle`
- Removes `catalog_pack_modes.json`, `redirects.json`, `song_metadata.json`, `features.json`, `bs_log.txt`
- Preserves `/AFR/test/` and `/AFR/bs_log/` directories

**Game directory (`/user/app/CUSA12878/`)** — existing:
- Removes custom bundles/config jsons
- Preserves base game files (`app.pkg`, `app.json`, `app.pbm`, `app.xml`) and system mount points

**Plugin directory** — existing:
- Removes `beat_saber_deluxe.prx`, `afr.prx`, `game_patch.prx`

**plugins.ini** — existing:
- Removes `[CUSA12878]` section with `beat_saber_deluxe.prx` entry

**Local caches** — existing:
- Clears `song_metadata.json`, `redirects.json`, `catalog_pack_modes.json`

### 3. ps4_state.py (Fixed)
Updated to check the AFR directory for actual plugin state:
- Lists bundles/configs from `/data/GoldHEN/AFR/CUSA12878/`
- Parses `redirects.json` from AFR dir for accurate song/redirect counts
- Shows game dir separately for base game files
- Reports accurate summary: custom songs, redirects, modified packs, plugin

## Clean Slate Workflow

```bash
# 1. Full clean slate (removes all BSD files from AFR + game dir + plugins.ini + local caches)
python3 /workspace/backup-beat-saber-deluxe-files.py backup --clean-ps4

# 2. Verify clean slate
python3 /workspace/beat_saber_deluxe/development/scripts/ps4_state.py
# Output:
# 🧹  PS4 is in CLEAN SLATE state for Beat Saber Deluxe.
#     No custom songs, no redirects, no modified music packs, no plugin.

# 3. Single-song deploy (self-contained)
python3 tools/full_custom_song_pipeline.py \
  --download-beat-saver-song <MAP_ID> \
  --target <slot_name> \
  --deploy-full

# 4. Verify deploy
python3 /workspace/beat_saber_deluxe/development/scripts/ps4_state.py
# Output:
# 🎵  Beat Saber Deluxe currently installed with 1 custom songs, 3 redirects, 1 modified music packs.
#   Custom songs: AllTheGoodGirlsGoToHell_v3.bundle
#   Redirects: AllTheGoodGirlsGoToHell
#   Modified music packs: billieeilish_pack_modes_assets_all_*.bundle
#   Plugin: registered + present
```

## Verified End-to-End

After the fixes:
- Clean slate verified: AFR dir empty, game dir clean, plugins.ini clean, local caches clear
- Fresh deploy: 1 custom song, 1 modified pack (billieeilish), 3 redirects, plugin registered, validation PASSED
- All 581 tests pass

## Key Lessons

1. **Config drift happens** — local `ps4_config.json` can diverge from pipeline defaults. Always run `--generate-config` to reset.
2. **Plugin reads from hardcoded path** — `AFR_BASE = "/data/GoldHEN/AFR"` in main.cpp; deploy must match.
3. **Clean must match deploy location** — if you deploy to AFR, clean must clean AFR.
4. **State inspection must check the right place** — `ps4_state.py` was checking the wrong directory.

See also: `[[pipeline-deploy-full-orchestration]]`, `[[pipeline-deploy-full-download-guard-ordering]]`, `[[backup-script-catastrophic-clean-bug]]`, `[[ps4-zero-byte-system-files]]`.