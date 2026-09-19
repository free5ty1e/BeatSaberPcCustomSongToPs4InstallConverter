# Installing Custom Songs Over the Lizzo Music Pack

This document provides step-by-step, self-contained pipeline commands to replace all 9 songs
in the official Lizzo DLC music pack with custom community songs from BeatSaver.

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



## Target: Lizzo Official DLC Pack

- **Pack key**: `lizzo`
- **Pack bundle**: `lizzo_pack_assets_all_8bf3db217732cc18af0b9a2a32d13a9a.bundle`
- **9 songs** (each with 5 difficulties: Easy, Normal, Hard, Expert, ExpertPlus):
  1. 2 Be Loved (Am I Ready) → Custom: Yes I'm A Mess (AJR)
  2. About Damn Time → Custom: The Middle (Jimmy Eat World)
  3. Cuz I Love You → Custom: Bring It On (Giga-P)
  4. Everybody's Gay → Custom: Queencard ((G)I-DLE)
  5. Good As Hell → Custom: Do You Wanna Taste It (Wig Wam)
  6. Juice → Custom: One More (SG Lewis feat. Nile Rodgers)
  7. Tempo → Custom: Bruises (Fox Stevenson)
  8. Truth Hurts → Custom: Genie In A Bottle (DisasterTheory)
  9. Worship → Custom: Best Day Of My Life (American Authors)

## Where Target Metadata Lives

The song slot IDs and difficulty modes for the Lizzo pack are defined in:
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
# 1. 2 Be Loved → Yes I'm A Mess (AJR)
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

# 2. About Damn Time → The Middle (Jimmy Eat World)
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

# 3. Cuz I Love You → Bring It On (Giga-P)
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

# 4. Everybody's Gay → Queencard ((G)I-DLE)
# Custom Song: Queencard
# Artist: (G)I-DLE
# Album: I Feel
# Year: 2023
# BeatSaver MAP_ID: 40a53
# BeatSaver Link: https://beatsaver.com/maps/40a53
# Genre: K-Pop / Pop
# BPM: 130
# Difficulties: 5/5 (Easy through Expert+) [Ranked]
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 40a53     --target EverybodysGay     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 5. Good As Hell → Do You Wanna Taste It (Wig Wam)
# Custom Song: Do You Wanna Taste It
# Artist: Wig Wam
# Album: Non Stop Rock'n Roll (Peacemaker Intro)
# Year: 2010
# BeatSaver MAP_ID: 25411
# BeatSaver Link: https://beatsaver.com/maps/25411
# Genre: Glam Rock / Hard Rock
# BPM: 184
# Difficulties: 5/5 native (Easy, Normal, Hard, Expert, ExpertPlus) — mapper TetsuBeats; full 179s version (the old 212c5 map was an 80s Hard-only clip)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 25411     --target GoodAsHell     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 6. Juice → One More (SG Lewis feat. Nile Rodgers)
# Custom Song: One More
# Artist: SG Lewis feat. Nile Rodgers
# Album: (single)
# Year: 2019
# BeatSaver MAP_ID: 27140
# BeatSaver Link: https://beatsaver.com/maps/27140
# Genre: Nu-disco / Funk
# BPM: 120
# Difficulties: 5/5 native (Easy, Normal, Hard, Expert, ExpertPlus) — mapper DaftMaple (the old 5758 Blame map was Expert-only)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 27140     --target Juice     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 7. Tempo → Bruises (Fox Stevenson)
# Custom Song: Bruises
# Artist: Fox Stevenson
# Album: Killjoy
# Year: 2019
# BeatSaver MAP_ID: ae3c
# BeatSaver Link: https://beatsaver.com/maps/ae3c
# Genre: Drum & Bass / Electronic
# BPM: 174
# Difficulties: 5/5 (Easy through Expert+) + 90/360
# Note: Previously had desync issues; may need lapped audio handling
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song ae3c     --target Tempo     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 8. Truth Hurts → Genie In A Bottle (DisasterTheory)
# Custom Song: Genie In A Bottle
# Artist: DisasterTheory
# Album: (original)
# Year: 2023
# BeatSaver MAP_ID: 50a08
# BeatSaver Link: https://beatsaver.com/maps/50a08
# Genre: Electronic / Dubstep
# BPM: 177
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 50a08     --target TruthHurts     --pcm16     --no-pad     --convert-to-v3     --deploy-full

# 9. Worship → Best Day Of My Life (American Authors)
# Custom Song: Best Day Of My Life
# Artist: American Authors
# Album: Oh, What a Life
# Year: 2013
# BeatSaver MAP_ID: 86e9
# BeatSaver Link: https://beatsaver.com/maps/86e9
# Genre: Indie Pop / Folk Pop
# BPM: 100
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 86e9     --target Worship     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```