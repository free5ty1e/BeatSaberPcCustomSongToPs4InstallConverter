# Installing Custom Songs Over the Britney Spears Music Pack

This document provides step-by-step, self-contained pipeline commands to replace all 11 songs
in the official Britney Spears DLC music pack with custom community songs from BeatSaver.

Pipeline: v0.5331 — fully automated, no manual song_metadata.json editing required.

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



## Target: Britney Spears Official DLC Pack

- **Pack key**: `britneyspears`
- **Pack bundle**: `britneyspears_pack_assets_all_18d2741e11e15c97493346b2797ea847.bundle`
- **11 songs** (each with 5 difficulties: Easy, Normal, Hard, Expert, ExpertPlus):
  1. Baby One More Time → Custom: Blinding Lights (The Weeknd)
  2. Circus → Custom: Shape of You (Ed Sheeran)
  3. Gimme More → Custom: Gangnam Style (PSY)
  4. I'm a Slave 4 U → Custom: Believer (Imagine Dragons)
  5. Me Against The Music → Custom: Mr. Blue Sky (Electric Light Orchestra)
  6. Oops!...I Did It Again → Custom: Rap God (Eminem)
  7. Overprotected → Custom: Dancing On My Own (Robyn)
  8. Scream & Shout → Custom: Levitating (Dua Lipa)
  9. Till The World Ends → Custom: Dance Monkey (Tones and I)
  10. Toxic → Custom: Toxic (Britney Spears) - Emir's map
  11. Womanizer → Custom: Womanizer (Britney Spears) - 12bd8 map

## Where Target Metadata Lives

The song slot IDs and difficulty modes for the Britney Spears pack are defined in:
  `/workspace/beat_saber_deluxe/beat_saber_song_ids.json`

Each song has a `songID` that maps to the pipeline `--target` parameter (slot name).

## Where Local Song Metadata JSON is Stored

The local installed-song metadata file is at:
  `/workspace/beat_saber_deluxe/song_metadata.json`

This file maps display names to source hash IDs and is **NOT included in the repository**.
To exclude it from git tracking, add the following line to `.gitignore`:

```
song_metadata.json
```

(If not already present — it is currently NOT gitignored, so adding it prevents accidental commits.)

## Per-Song Pipeline Command Pattern with Song Info

Each custom song is downloaded from BeatSaver, converted to V3.2.0 schema, and deployed to PS4
using a single pipeline command. A comment above each command identifies the song:

```bash
# Song: Blinding Lights - The Weeknd
# Custom Song: Blinding Lights
# Artist: The Weeknd
# Album: After Hours
# Year: 2019
# BeatSaver MAP_ID: 8553
# BeatSaver Link: https://beatsaver.com/maps/8553
# Genre: Synth-pop / R&B
# BPM: 171
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 8553     --target BabyOneMoreTime     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# Song: Shape of You - Ed Sheeran
# Custom Song: Shape of You
# Artist: Ed Sheeran
# Album: ÷ (Divide)
# Year: 2017
# BeatSaver MAP_ID: 1672a
# BeatSaver Link: https://beatsaver.com/maps/1672a
# Genre: Pop / Tropical House
# BPM: 96
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1672a     --target Circus     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# Song: Gangnam Style - PSY
# Custom Song: Gangnam Style
# Artist: PSY
# Album: Psy 6 (Six Rules), Part 1
# Year: 2012
# BeatSaver MAP_ID: 141
# BeatSaver Link: https://beatsaver.com/maps/141
# Genre: K-Pop / Dance / Comedy
# BPM: 132
# Difficulties: 3/5 (Normal, Hard, Expert) [Ranked]
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 141     --target GimmeMore     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# Song: Believer - Imagine Dragons
# Custom Song: Believer
# Artist: Imagine Dragons
# Album: Evolve
# Year: 2017
# BeatSaver MAP_ID: 1fef
# BeatSaver Link: https://beatsaver.com/maps/1fef
# Genre: Pop Rock / Arena Rock
# BPM: 125
# Difficulties: 5/5 (Easy through Expert+) [100k Contest version]
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1fef     --target ImASlave4U     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# Song: Mr. Blue Sky - Electric Light Orchestra
# Custom Song: Mr. Blue Sky
# Artist: Electric Light Orchestra
# Album: Out of the Blue
# Year: 1977
# BeatSaver MAP_ID: 570
# BeatSaver Link: https://beatsaver.com/maps/570
# Genre: Progressive Pop / Rock
# BPM: 180
# Difficulties: 5/5 (Easy through Expert+) [Ranked, greatyazer]
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 570     --target MeAgainstTheMusic     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# Song: Rap God - Eminem
# Custom Song: Rap God
# Artist: Eminem
# Album: The Marshall Mathers LP 2
# Year: 2013
# BeatSaver MAP_ID: 46d4
# BeatSaver Link: https://beatsaver.com/maps/46d4
# Genre: Hip Hop / Rap
# BPM: 148
# Difficulties: 5/5 (Easy through Expert+) [Ryger, highest rated 0.959]
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 46d4     --target OopsIDidItAgain     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# Song: Dancing On My Own - Robyn (Buzz Junkies Remix)
# Custom Song: Dancing On My Own (Buzz Junkies Remix)
# Artist: Robyn
# Album: Body Talk (Remixes)
# Year: 2010
# BeatSaver MAP_ID: 189d
# BeatSaver Link: https://beatsaver.com/maps/189d
# Genre: Electropop / Dance
# BPM: 128
# Difficulties: 2/5 (Hard, Expert) [constroyr]
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 189d     --target Overprotected     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# Song: Levitating - Dua Lipa
# Custom Song: Levitating
# Artist: Dua Lipa
# Album: Future Nostalgia
# Year: 2020
# BeatSaver MAP_ID: 12355
# BeatSaver Link: https://beatsaver.com/maps/12355
# Genre: Disco-pop / Dance-pop
# BPM: 103
# Difficulties: 4/5 (Normal, Hard, Expert, Expert+) [yomama]
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 12355     --target Scream&Shout     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# Song: Dance Monkey - Tones and I
# Custom Song: Dance Monkey
# Artist: Tones and I
# Album: The Kids Are Coming
# Year: 2019
# BeatSaver MAP_ID: 6cc2
# BeatSaver Link: https://beatsaver.com/maps/6cc2
# Genre: Pop / Dance
# BPM: 98
# Difficulties: 5/5 (Easy through Expert+) [Most upvoted 7,791]
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 6cc2     --target TillTheWorldEnds     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# Song: Toxic - Britney Spears
# Custom Song: Toxic
# Artist: Britney Spears
# Album: In the Zone
# Year: 2003
# BeatSaver MAP_ID: 21540
# BeatSaver Link: https://beatsaver.com/maps/21540
# Genre: Dance-pop / Electropop
# BPM: 143
# Difficulties: 5/5 (Easy through Expert+) [Emir]
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 21540     --target Toxic     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# Song: Womanizer - Britney Spears
# Custom Song: Womanizer
# Artist: Britney Spears
# Album: Circus
# Year: 2008
# BeatSaver MAP_ID: 12bd8
# BeatSaver Link: https://beatsaver.com/maps/12bd8
# Genre: Electropop / Dance-pop
# BPM: 140
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 12bd8     --target Womanizer     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```