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
Requires plugin v0.8043+. On boot, the plugin now also toasts its flag status — "BSD Plugin enabled — N/3 feature flags ON" or "BSD Plugin DISABLED — Official songs only" (v0.8044+).

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
  1. Baby One More Time → Custom: Take on Me (a-ha)
  2. Circus → Custom: Shape of You (Ed Sheeran)
  3. Gimme More → Custom: That That (PSY ft. SUGA of BTS)
  4. I'm a Slave 4 U → Custom: Believer (Imagine Dragons)
  5. Me Against The Music → Custom: Mr. Blue Sky (Electric Light Orchestra) [ARCS]
  6. Oops!...I Did It Again → Custom: Oops!... I Did It Again (Britney Spears) [DITR4]
  7. Overprotected → Custom: Shut Up And Dance (Walk The Moon)
  8. Scream & Shout → Custom: Cold Heart (PNAU Remix) (Elton John & Dua Lipa)
  9. Till The World Ends → Custom: Dance Monkey (metal cover) (Leo Moracchioli)
  10. Toxic → Custom: Toxic (Britney Spears) - Emir's map
  11. Womanizer → Custom: Radar (Britney Spears)

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
# Song: Take on Me - a-ha
# Custom Song: Take on Me
# Artist: a-ha
# Album: Hunting High and Low
# Year: 1985
# BeatSaver MAP_ID: 6d63
# BeatSaver Link: https://beatsaver.com/maps/6d63
# Genre: Synth-pop / New Wave
# BPM: 169
# Difficulties: 4/5 native (Easy, Normal, Hard, Expert) — Expert+ auto-filled from Expert
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 6d63     --target BabyOneMoreTime     --pcm16     --no-pad     --convert-to-v3     --deploy-full
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
# Song: That That - PSY (prod. & ft. SUGA of BTS)
# Custom Song: That That
# Artist: PSY
# Album: PSY 9th
# Year: 2022
# BeatSaver MAP_ID: 250b5
# BeatSaver Link: https://beatsaver.com/maps/250b5
# Genre: K-Pop / Dance
# BPM: 130
# Difficulties: 5/5 native (Easy, Normal, Hard, Expert, ExpertPlus) — mapper rodysan
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 250b5     --target GimmeMore     --pcm16     --no-pad     --convert-to-v3     --deploy-full
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
# Song: Mr. Blue Sky - Electric Light Orchestra [ARCS]
# Custom Song: Mr. Blue Sky
# Artist: Electric Light Orchestra
# Album: Out of the Blue
# Year: 1977
# BeatSaver MAP_ID: 2fa04
# BeatSaver Link: https://beatsaver.com/maps/2fa04
# Genre: Classic Rock / Pop
# BPM: 174
# Difficulties: 4/5 native (Easy, Normal, Hard, Expert) — mappers JRE_McNuggies & symphonic; Expert+ auto-filled
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 2fa04     --target MeAgainstTheMusic     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# Song: Oops!... I Did It Again - Britney Spears [DITR4]
# Custom Song: Oops!... I Did It Again
# Artist: Britney Spears
# Album: Oops!... I Did It Again
# Year: 2000
# BeatSaver MAP_ID: 28566
# BeatSaver Link: https://beatsaver.com/maps/28566
# Genre: Pop
# BPM: 95
# Difficulties: 5/5 native (Easy, Normal, Hard, Expert, ExpertPlus) — mapper chriscrow3
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 28566     --target OopsIDidItAgain     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# Song: Shut Up And Dance - Walk The Moon
# Custom Song: Shut Up And Dance
# Artist: Walk The Moon
# Album: Talking Is Hard
# Year: 2014
# BeatSaver MAP_ID: 285e8
# BeatSaver Link: https://beatsaver.com/maps/285e8
# Genre: Indie Pop / Dance Rock
# BPM: 128
# Difficulties: 5/5 native (Easy, Normal, Hard, Expert, ExpertPlus) — mappers Syndicate, OneSpookyBoi, TheCzar1994
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 285e8     --target Overprotected     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# Song: Cold Heart (PNAU Remix) - Elton John & Dua Lipa
# Custom Song: Cold Heart
# Artist: Elton John & Dua Lipa
# Album: The Lockdown Sessions
# Year: 2021
# BeatSaver MAP_ID: 1d9fd
# BeatSaver Link: https://beatsaver.com/maps/1d9fd
# Genre: Dance-pop / Nu-disco
# BPM: 116
# Difficulties: 5/5 native (Easy, Normal, Hard, Expert, ExpertPlus) — mappers Faded 99 & Z-ANESaber
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1d9fd     --target Scream&Shout     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# Song: Dance Monkey (metal cover) - Leo Moracchioli
# Custom Song: Dance Monkey (metal cover)
# Artist: Leo Moracchioli
# Album: YouTube cover
# Year: 2020
# BeatSaver MAP_ID: 13f31
# BeatSaver Link: https://beatsaver.com/maps/13f31
# Genre: Metal / Pop cover
# BPM: 120
# Difficulties: 4/5 native (Easy, Normal, Hard, Expert) — Expert+ auto-filled
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 13f31     --target TillTheWorldEnds     --pcm16     --no-pad     --convert-to-v3     --deploy-full
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
# Song: Radar - Britney Spears
# Custom Song: Radar
# Artist: Britney Spears
# Album: Circus
# Year: 2008
# BeatSaver MAP_ID: 1e2f7
# BeatSaver Link: https://beatsaver.com/maps/1e2f7
# Genre: Dance-pop
# BPM: 128
# Difficulties: 5/5 native (Easy, Normal, Hard, Expert, ExpertPlus)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1e2f7     --target Womanizer     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```