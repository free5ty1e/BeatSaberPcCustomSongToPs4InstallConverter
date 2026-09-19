# Installing Custom Songs Over the Billie Eilish Music Pack

This document provides step-by-step, self-contained pipeline commands to replace all 10 songs
in the official Billie Eilish DLC music pack with custom community songs from BeatSaver.

Pipeline: v0.5334 — fully automated, no manual song_metadata.json editing required.
All custom songs deploy with 4 selectable modes (Standard, OneSaber, NoArrows, 90Degree).

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
python3 tools/full_custom_song_pipeline.py --download-beat-saver-song 4a901 --target AllTheGoodGirlsGoToHell --pcm16 --no-pad --convert-to-v3 --deploy-full
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
Requires plugin v0.8043+. On boot the plugin shows ONE combined toast — "BS Deluxe v<ver> (ON) / By Chris Primeish / (N/3 features ON)" or "BS Deluxe v<ver> (OFF) / By Chris Primeish / (official songs only)" — the (ON/OFF) is the global kill-switch state (single toast because PS4VR headset switch-over can swallow a second toast; v0.8045+).

## 🔧 NEW: Clear Target Song (`--clear-target-song`)

Revert a single custom song slot back to its stock state WITHOUT a full PS4 clean slate:

```bash
python3 tools/full_custom_song_pipeline.py --clear-target-song AllTheGoodGirlsGoToHell
```

This removes:
- The custom song bundle from PS4 AFR directory
- The redirect entry from `redirects.json`
- The song/artist metadata from `song_metadata.json`
- Deploys updated configs to PS4

Useful for: testing a different custom song in the same slot, debugging, or partial rollback.

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


## Target: Billie Eilish Official DLC Pack

- **Pack key**: `billieeilish`
- **Pack bundle**: `billieeilish_pack_assets_all_ba4a0db5570760b21ebcbb2ec7a8d321.bundle`
- **10 songs** (each with 5 difficulties: Easy, Normal, Hard, Expert, ExpertPlus):
  1. all the good girls go to hell → Custom: Mirror (Ado)
  2. bad guy → Custom: Odo (Ado)
  3. bellyache → Custom: ATTITUDE (IVE)
  4. bury a friend → Custom: Baddie (IVE)
  5. happier than ever → Custom: Cosmic (Red Velvet)
  6. n da → Custom: Duvet (Bôa — Shiki Miyoshino cover)
  7. therefore i am → Custom: Who's Laughing Now (Ava Max)
  8. 2 be loved (am i ready) → Custom: Yes I'm A Mess (AJR)
  9. about damn time → Custom: The Middle (Jimmy Eat World)
  10. cuz i love you → Custom: Bring It On (Giga-P)

## Where Target Metadata Lives

The song slot IDs and difficulty modes for the Billie Eilish pack are defined in:
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
# 1. all the good girls go to hell → Mirror (Ado)
# Custom Song: Mirror
# Artist: Ado
# Album: Kyōgen
# Year: 2022
# BeatSaver MAP_ID: 4a901
# BeatSaver Link: https://beatsaver.com/maps/4a901
# Genre: J-Pop / Rock
# BPM: 114
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 4a901     --target AllTheGoodGirlsGoToHell     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 2. bad guy → Odo (Ado)
# Custom Song: Odo
# Artist: Ado
# Album: Utattemita (cover) / Original by Ado
# Year: 2021
# BeatSaver MAP_ID: 1dbb9
# BeatSaver Link: https://beatsaver.com/maps/1dbb9
# Genre: J-Pop / Rock
# BPM: 128
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1dbb9     --target BadGuy     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 3. bellyache → ATTITUDE (IVE)
# Custom Song: ATTITUDE
# Artist: IVE
# Album: I've IVE
# Year: 2023
# BeatSaver MAP_ID: 44218
# BeatSaver Link: https://beatsaver.com/maps/44218
# Genre: K-Pop / Pop
# BPM: 118
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 44218     --target Bellyache     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 4. bury a friend → Baddie (IVE)
# Custom Song: Baddie
# Artist: IVE
# Album: I've IVE
# Year: 2023
# BeatSaver MAP_ID: 36ab4
# BeatSaver Link: https://beatsaver.com/maps/36ab4
# Genre: K-Pop / Pop
# BPM: 160
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 36ab4     --target BuryAFriend     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 5. happier than ever → Cosmic (Red Velvet)
# Custom Song: Cosmic
# Artist: Red Velvet
# Album: Cosmic (EP)
# Year: 2024
# BeatSaver MAP_ID: 3e192
# BeatSaver Link: https://beatsaver.com/maps/3e192
# Genre: K-Pop / R&B Pop
# BPM: 106
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 3e192     --target HappierThanEver     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 6. nda → Duvet (Bôa — Shiki Miyoshino cover)
# Custom Song: Duvet
# Artist: Bôa (Shiki Miyoshino cover)
# Album: Twilight (Serial Experiments Lain opening / cover release)
# Year: 1998 / 2023
# BeatSaver MAP_ID: 22c4e
# BeatSaver Link: https://beatsaver.com/maps/22c4e
# Genre: Alternative Rock / Indie
# BPM: 186
# Difficulties: 5/5 native (Easy, Normal, Hard, Expert, ExpertPlus) — mapper shad; Shiki Miyoshino cover version (the old 4b107 original-Bôa map was Hard/Expert+ only)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 22c4e     --target NDA     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 7. therefore i am → Who's Laughing Now (Ava Max)
# Custom Song: Who's Laughing Now
# Artist: Ava Max
# Album: Heaven & Hell
# Year: 2020
# BeatSaver MAP_ID: f91e
# BeatSaver Link: https://beatsaver.com/maps/f91e
# Genre: Dance Pop / Electropop
# BPM: 92
# Difficulties: 5/5 (Easy through Expert+) [Ranked]
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song f91e     --target ThereforeIAm     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 8. 2 be loved (am i ready) → Yes I'm A Mess (AJR)
# Custom Song: Yes I'm A Mess
# Artist: AJR
# Album: The Maybe Man
# Year: 2023
# BeatSaver MAP_ID: 35ca9
# BeatSaver Link: https://beatsaver.com/maps/35ca9
# Genre: Indie Pop / Alternative
# BPM: 184
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 35ca9     --target 2BeLoved     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 9. about damn time → The Middle (Jimmy Eat World)
# Custom Song: The Middle
# Artist: Jimmy Eat World
# Album: Bleed American
# Year: 2001
# BeatSaver MAP_ID: 27a13
# BeatSaver Link: https://beatsaver.com/maps/27a13
# Genre: Alternative Rock / Emo
# BPM: 162
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 27a13     --target AboutDamnTime     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 10. cuz i love you → Bring It On (Giga-P)
# Custom Song: Bring It On
# Artist: Giga-P
# Album: (single)
# Year: 2014
# BeatSaver MAP_ID: 2475
# BeatSaver Link: https://beatsaver.com/maps/2475
# Genre: Vocaloid / Electronic
# BPM: 160
# Difficulties: 4/5 native (Easy, Normal, Hard, Expert) — Expert+ auto-filled
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 2475     --target CuzILoveYou     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```