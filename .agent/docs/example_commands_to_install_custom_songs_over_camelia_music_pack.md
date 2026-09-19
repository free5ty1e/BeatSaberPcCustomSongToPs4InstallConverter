# Installing Custom Songs Over the Camelia (Chromeo) Music Pack

This document provides step-by-step, self-contained pipeline commands to replace all 6 songs
in the official Camelia (Chromeo) DLC music pack with custom community songs from BeatSaver.

Pipeline: v0.5338 — fully automated, no manual song_metadata.json editing required.

**Song selection rule (v0.5338+):** every custom song below ships native Easy, Normal AND Hard
difficulties from its mapper (per `user_preferences.md` — Expert-only maps lock out lower-skilled
players and do not qualify for the collection). Songs missing Expert/Expert+ are filled from the
map's own closest difficulty by the pipeline; Easy/Normal/Hard are NEVER clones.

---

## ⚠️ NEW: Partial Pack Deployment Safety (v0.5334+)

**Problem:** When deploying custom songs one at a time, the pack bundle previously added extra mode buttons (OneSaber, NoArrows, 90Degree) for ALL songs in the pack — even unmodified stock songs. Selecting a stock song and trying to play a non-Standard mode would crash the game.

**Solution (automatic in `--deploy-full`):**
1. **Surgical pack bundle patching:** The pipeline now builds the pack bundle with extra modes ONLY for the custom song(s) being deployed. Stock songs in the same pack keep only Standard mode.
2. **Runtime feature flag `enable_beatmap_mode_mapping`** (in `features.json`): Gates visibility of extra mode sets in the mode selector UI.
   - **OFF (safe default for partial deploys):** All songs show only Standard mode, regardless of pack bundle content. No crashes possible.
   - **ON (when pack is complete):** Custom songs with patched mode sets show all 4 modes; stock songs show only Standard.

**Recommended workflow for partial pack deploys:**
```bash
# Option A: Keep feature flag OFF until pack is complete (safest)
python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_beatmap_mode_mapping=false
# ... deploy songs one at a time ...
python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_beatmap_mode_mapping=true

# Option B: Let automatic surgical patching handle it (default in v0.5334+)
# Each --deploy-full only adds extra modes for THAT song in the pack bundle
python3 tools/full_custom_song_pipeline.py --download-beat-saver-song <MAP_ID> --target <SLOT> --pcm16 --no-pad --convert-to-v3 --deploy-full
```

---

---

## 🔌 Global Plugin Kill Switch (`enable_plugin`)

Play the **official Beat Saber songs** (100% stock behavior) without editing `plugins.ini`
or clearing anything on the PS4 — the plugin simply goes fully inert (no redirects, no
metadata swaps) on the next game boot:

```bash
# Disable everything — official songs only:
python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_plugin=false

# Re-enable your custom songs:
python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_plugin=true
```

Takes effect on the next game boot (`features.json` is read at plugin startup).
Requires plugin v0.8043+.

## 🔧 NEW: Clear Target Song (`--clear-target-song`)

Revert a single custom song slot back to its stock state WITHOUT a full PS4 clean slate:

```bash
python3 tools/full_custom_song_pipeline.py --clear-target-song <SLOT_NAME>
```

This removes:
- The custom song bundle from PS4 AFR directory
- The redirect entry from `redirects.json`
- The song/artist metadata from `song_metadata.json`
- Deploys updated configs to PS4

Useful for: testing a different custom song in the same slot, debugging, or partial rollback.


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
- **6 songs** (each custom map ships ALL 5 difficulties natively: Easy, Normal, Hard, Expert, ExpertPlus —
  meeting the collection rule that every song must be playable by lower-skilled players on Easy/Normal/Hard;
  Expert+ is always the mapper's own chart, never a clone):
  1. Crystallized → Custom: Le Freak (Chic)
  2. CycleHit → Custom: 24K Magic (Bruno Mars)
  3. ExitThisEarthsAtomosphere → Custom: Fireball (Pitbull feat. John Ryan)
  4. Ghost → Custom: Around The World (Niklas Dee)
  5. LightItUp → Custom: Daft Punk Megamix 1 (Daft Punk)
  6. WhatTheCat → Custom: Stayin' Alive (Bee Gees)

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
# 1. Crystallized → Le Freak (Chic)
# Custom Song: Le Freak
# Artist: Chic
# Album: C'est Chic
# Year: 1978
# BeatSaver MAP_ID: 1760d
# BeatSaver Link: https://beatsaver.com/maps/1760d
# Genre: Disco / Funk
# BPM: 120
# Difficulties: 5/5 native (Easy, Normal, Hard, Expert, Expert+) — mapper XYNie
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1760d     --target Crystallized     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 2. CycleHit → 24K Magic (Bruno Mars)
# Custom Song: 24K Magic
# Artist: Bruno Mars
# Album: 24K Magic
# Year: 2016
# BeatSaver MAP_ID: 16726
# BeatSaver Link: https://beatsaver.com/maps/16726
# Genre: Funk / Disco-Pop
# BPM: 107
# Difficulties: 5/5 native (Easy, Normal, Hard, Expert, Expert+) — mapper ETAN (NoodleJams Vol.1)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 16726     --target CycleHit     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 3. ExitThisEarthsAtomosphere → Fireball (Pitbull feat. John Ryan)
# Custom Song: Fireball
# Artist: Pitbull feat. John Ryan
# Album: Globalization
# Year: 2014
# BeatSaver MAP_ID: 9c05
# BeatSaver Link: https://beatsaver.com/maps/9c05
# Genre: Dance / Electronic
# BPM: 123
# Difficulties: 5/5 native (Easy, Normal, Hard, Expert, Expert+) — mapper Toadally
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 9c05     --target ExitThisEarthsAtomosphere     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 4. Ghost → Around The World (Niklas Dee)
# Custom Song: Around The World
# Artist: Niklas Dee
# Album: (single)
# Year: 2024
# BeatSaver MAP_ID: 40201
# BeatSaver Link: https://beatsaver.com/maps/40201
# Genre: Dance / Electronic
# BPM: 150
# Difficulties: 5/5 native (Easy, Normal, Hard, Expert, Expert+) — mapper Najoko
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 40201     --target Ghost     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 5. LightItUp → Daft Punk Megamix 1 (Daft Punk)
# Custom Song: Megamix 1
# Artist: Daft Punk
# Album: (megamix)
# Year: 2001
# BeatSaver MAP_ID: 242e9
# BeatSaver Link: https://beatsaver.com/maps/242e9
# Genre: Electronic / House
# BPM: 126
# Difficulties: 5/5 native (Easy, Normal, Hard, Expert, Expert+) — mapper P90KILLR
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 242e9     --target LightItUp     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 6. WhatTheCat → Stayin' Alive (Bee Gees)
# Custom Song: Stayin' Alive
# Artist: Bee Gees
# Album: Saturday Night Fever
# Year: 1977
# BeatSaver MAP_ID: 3cfe9
# BeatSaver Link: https://beatsaver.com/maps/3cfe9
# Genre: Disco
# BPM: 104
# Difficulties: 5/5 native (Easy, Normal, Hard, Expert, Expert+) — mappers Undeceiver & steeak
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 3cfe9     --target WhatTheCat     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```