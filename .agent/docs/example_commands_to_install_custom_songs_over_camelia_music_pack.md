# Installing Custom Songs Over the Camelia (Chromeo) Music Pack

This document provides step-by-step, self-contained pipeline commands to replace all 6 songs
in the official Camelia (Chromeo) DLC music pack with custom community songs from BeatSaver.

Pipeline: v0.5331 — fully automated, no manual song_metadata.json editing required.
All custom songs deploy with 4 selectable modes (Standard, OneSaber, NoArrows, 90Degree).

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

```



## Target: Camelia (Chromeo) Official DLC Pack

- **Pack key**: `camelia`
- **Pack bundle**: `camellia_pack_assets_all_91d9d25ee1641047d08834b4bb3ec0ac.bundle`
- **6 songs** (each with 5 difficulties: Easy, Normal, Hard, Expert, ExpertPlus):
  1. Crystallized → Custom: Sexy Socialite (Chromeo)
  2. CycleHit → Custom: Jealous (I Ain't With It) (Chromeo)
  3. ExitThisEarthsAtomosphere → Custom: 'Roni Got Me Stressed Out (Chromeo)
  4. Ghost → Custom: Green Light (Chromeo Remix) (Lorde, Chromeo)
  5. LightItUp → Custom: 1999 (Charli XCX & Troye Sivan)
  6. WhatTheCat → Custom: FANCY (TWICE)

## Where Target Metadata Lives

The song slot IDs and difficulty modes for the Camelia pack are defined in:
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

## Per-Song Pipeline Commands

```bash
# 1. Crystallized → Sexy Socialite (Chromeo)
# Custom Song: Sexy Socialite
# Artist: Chromeo
# Album: Head Over Heels
# Year: 2018
# BeatSaver MAP_ID: 6f1f
# BeatSaver Link: https://beatsaver.com/maps/6f1f
# Genre: Funk / Disco / Electronic
# BPM: 142
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 6f1f     --target Crystallized     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 2. CycleHit → Jealous (I Ain't With It) (Chromeo)
# Custom Song: Jealous (I Ain't With It)
# Artist: Chromeo
# Album: Head Over Heels
# Year: 2018
# BeatSaver MAP_ID: 111fd
# BeatSaver Link: https://beatsaver.com/maps/111fd
# Genre: Funk / Disco / Electronic
# BPM: 129
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 111fd     --target CycleHit     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 3. ExitThisEarthsAtomosphere → 'Roni Got Me Stressed Out (Chromeo)
# Custom Song: 'Roni Got Me Stressed Out
# Artist: Chromeo
# Album: Head Over Heels
# Year: 2018
# BeatSaver MAP_ID: 115ba
# BeatSaver Link: https://beatsaver.com/maps/115ba
# Genre: Funk / Disco / Electronic
# BPM: 117
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 115ba     --target ExitThisEarthsAtomosphere     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 4. Ghost → Green Light (Chromeo Remix) (Lorde, Chromeo)
# Custom Song: Green Light (Chromeo Remix)
# Artist: Lorde, Chromeo
# Album: Melodrama (Remixes)
# Year: 2017
# BeatSaver MAP_ID: 37d5
# BeatSaver Link: https://beatsaver.com/maps/37d5
# Genre: Electropop / Remix
# BPM: 121
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 37d5     --target Ghost     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 5. LightItUp → 1999 (Charli XCX & Troye Sivan)
# Custom Song: 1999
# Artist: Charli XCX & Troye Sivan
# Album: (single)
# Year: 2018
# BeatSaver MAP_ID: 5352
# BeatSaver Link: https://beatsaver.com/maps/5352
# Genre: Pop / Synth-pop
# BPM: 124
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 5352     --target LightItUp     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 6. WhatTheCat → FANCY (TWICE)
# Custom Song: FANCY
# Artist: TWICE
# Album: Fancy You
# Year: 2019
# BeatSaver MAP_ID: 47f3
# BeatSaver Link: https://beatsaver.com/maps/47f3
# Genre: K-Pop / Pop
# BPM: 132
# Difficulties: 5/5 (Easy through Expert+) [Normal, Hard, Expert, Expert+]
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 47f3     --target WhatTheCat     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```