# Installing Custom Songs Over the Metallica Music Pack

This document provides step-by-step, self-contained pipeline commands to replace all 17 songs
in the official Metallica DLC music pack with custom community songs from BeatSaver.

Pipeline: v0.5333 — fully automated, no manual song_metadata.json editing required.

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

---

## 🎯 QUICK REFERENCE: Finding Custom Songs & Target Slots

**Target Song Slots (from `beat_saber_song_ids.json`):**
The official song IDs that map to pipeline `--target` parameter:
```
AtlasRise, Battery, Blackened, CreepingDeath, EnterSandman, FadeToBlack, ForWhomTheBellTolls, Fuel, HitTheLights, KingNothing, LuxAeterna, MasterOfPuppets, NothingElseMatters, One, SadButTrue, SeekAndDestroy, TheUnforgiven
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


## Target: Metallica Official DLC Pack

- **Pack key**: `metallica`
- **Pack bundle**: `metallica_pack_assets_all_30f6a060b08a18e2b9f1d422c3fbb05f.bundle`
- **17 songs** (each with 5 difficulties: Easy, Normal, Hard, Expert, ExpertPlus):

---

## Per-Song Pipeline Commands

```bash
# 1. Atlas, Rise! → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target AtlasRise     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 2. Battery → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target Battery     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 3. Blackened → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target Blackened     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 4. Creeping Death → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target CreepingDeath     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 5. Enter Sandman → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target EnterSandman     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 6. Fade to Black → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target FadeToBlack     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 7. For Whom the Bell Tolls → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target ForWhomTheBellTolls     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 8. Fuel → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target Fuel     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 9. Hit the Lights → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target HitTheLights     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 10. King Nothing → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target KingNothing     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 11. Lux Æterna → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target LuxAeterna     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 12. Master of Puppets → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target MasterOfPuppets     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 13. Nothing Else Matters → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target NothingElseMatters     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 14. One → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target One     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 15. Sad But True → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target SadButTrue     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 16. Seek & Destroy → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target SeekAndDestroy     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

```bash
# 17. The Unforgiven → [YOUR CUSTOM SONG HERE]
# Custom Song: [Song Name]
# Artist: [Artist Name]
# Album: [Album Name]
# Year: [Year]
# BeatSaver MAP_ID: [REPLACE_WITH_MAP_ID]
# BeatSaver Link: https://beatsaver.com/maps/[REPLACE_WITH_MAP_ID]
# Genre: [Genre]
# BPM: [BPM]
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID     --target TheUnforgiven     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```

---

## Where Target Metadata Lives

The song slot IDs and difficulty modes for the Metallica pack are defined in:
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
