# Installing Custom Songs Over the Rock Mixtape Music Pack

This document provides step-by-step, self-contained pipeline commands to replace all 8 songs
in the official Rock Mixtape DLC music pack with custom community songs from BeatSaver.

Pipeline: v0.5333 — fully automated, no manual song_metadata.json editing required.
All custom songs deploy with 4 selectable modes (Standard, OneSaber, NoArrows, 90Degree).

---

## 🎯 QUICK REFERENCE: Finding Custom Songs & Target Slots

**Target Song Slots (from `beat_saber_song_ids.json`):**
The official song IDs that map to pipeline `--target` parameter:
```
BornToBeWild, EyeOfTheTiger, FreeBird, IWasMadeLovingYou, SevenNationArmy, SmellsLikeTeenSpirit, SweetChildOMine, ThePretender
```

**How to Find Custom Songs on BeatSaver:**
1. Go to https://beatsaver.com or https://bsaber.com
2. Search for songs with **Easy, Normal, Hard** difficulties (required!)
3. Copy the MAP ID from the URL (e.g., `beatsaver.com/maps/4a901` → MAP_ID: `4a901`)
4. Verify the song has at least 3 difficulties before using

**How to Use This File:**
- Each command below is a template — replace the `--download-beat-saver-song` MAP_ID with your chosen song
- Keep the `--target` value as shown (matches the official song slot)
- Run commands **one at a time**, test in-game after each

---

## How `--deploy-full` works (self-contained, one song at a time)

Each command below is **fully self-contained**. Run them **one at a time** — after each one,
boot the game and verify that song + its whole pack works before moving to the next. Each
`--download-beat-saver-song <MAP> --target <slot> --deploy-full` command:
- downloads the custom song from BeatSaver and converts to V3.2.0 with all 4 modes,
- deploys ONLY that song's bundle,
- resolves the song's DLC pack (via `beat_saber_song_ids.json`) and deploys ONLY that pack's
  mode bundle + a matching single-pack `catalog_pack_modes.json`,
- builds + deploys the GoldHEN plugin **and** ensures the `plugins.ini` `[CUSA12878]` entry,
- deploys `features.json` (runtime feature flags),
- regenerates `redirects.json` scoped to just that song + pack pair,
- runs post-deploy validation.

It does **NOT** deploy the other packs or other songs. On a clean PS4, run these commands one
at a time and test after each.

## Optional: Clean PS4 for a Fresh Clean-Slate State

If you want to start from a completely clean PS4 (no custom songs, no redirects,
no modified packs, no plugin entry), run the backup script with `--clean-ps4`:

```bash
python3 /workspace/backup-beat-saber-deluxe-files.py backup --clean-ps4
```

This will:
1. **Backup** the current PS4 state (plugins.ini, AFR/CUSA12878, AFR/test/, AFR/bs_log/, local pipeline caches) to a timestamped zip in `/workspace/ps4_backups/`
2. **Surgically clean** `/user/app/CUSA12878/` — removes only custom bundles (`*_v3.bundle`, `*_custom_v3.bundle`, `pack_modes_bundles/*.bundle`, `Plugins/*.prx`, config jsons) while preserving base game files (`app.pkg`, `app.json`, `app.pbm`, `app.xml`) and system mount points
3. **Remove** the BSD plugin entry from `plugins.ini` `[CUSA12878]` section (prevents "data corrupted" on game launch)
4. **Clear** local pipeline state caches (`song_metadata.json`, `redirects.json`, `catalog_pack_modes.json`) so the pipeline treats the PS4 as fresh

After this runs, `ps4_state.py` will report:
```
🧹  PS4 is in CLEAN SLATE state for Beat Saber Deluxe.
```

## Pre-Deploy PS4 State Check

Before running any command, verify the **current state of the PS4**. The scripts and
commands below start with this check automatically:

```bash
python3 /workspace/beat_saber_deluxe/development/scripts/ps4_state.py
```

The script reports a **conclusion**, e.g.:

- `🧹  PS4 is in CLEAN SLATE state for Beat Saber Deluxe.` — no custom songs, no redirects,
  no modified music packs, no plugin.
- `🎵  Beat Saber Deluxe currently installed with X custom songs, Y redirects, and Z modified
  music packs.` — followed by a human-readable list of the custom songs, redirects
  (`BeatmapLevelsData/...`), modified music packs (`*_pack_modes_assets_all_*.bundle`), and the
  plugin (`beat_saber_deluxe.prx` in `/data/GoldHEN/plugins/` + its `plugins.ini` `[CUSA12878]`
  entry).

In the `.sh` scripts this runs before the deployment loop and pauses with
**"Press Enter to continue"** so you can review the current PS4 state before proceeding.

---


## Target: Rock Mixtape Official DLC Pack

- **Pack key**: `rockmixtape`
- **Pack bundle**: `rockmixtape_pack_assets_all_1b6b0b3e14e56a26146ad0342f364741.bundle`
- **8 songs** (each with 5 difficulties: Easy, Normal, Hard, Expert, ExpertPlus):

---

## Per-Song Pipeline Commands

```bash
# 1. Born To Be Wild → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target BornToBeWild     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 2. Eye of the Tiger → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target EyeOfTheTiger     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 3. Free Bird → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target FreeBird     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 4. I Was Made For Lovin' You → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target IWasMadeLovingYou     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 5. Seven Nation Army → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target SevenNationArmy     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 6. Smells Like Teen Spirit → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target SmellsLikeTeenSpirit     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 7. Sweet Child O' Mine → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target SweetChildOMine     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 8. The Pretender → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target ThePretender     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

---

## Where Target Metadata Lives

The song slot IDs and difficulty modes for the Rock Mixtape pack are defined in:
  `/workspace/beat_saber_deluxe/beat_saber_song_ids.json`

Each song has a `songID` that maps to the pipeline `--target` parameter (slot name).

## Where Local Song Metadata JSON is Stored

The local installed-song metadata file is at:
  `/workspace/beat_saber_deluxe/song_metadata.json`

This file maps display names to source hash IDs and is **NOT included in the repository**.
To exclude it from git tracking, add to `.gitignore`:
```
song_metadata.json
```
