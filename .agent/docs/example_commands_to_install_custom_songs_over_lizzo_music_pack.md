# Installing Custom Songs Over the Lizzo Music Pack

This document provides step-by-step, self-contained pipeline commands to replace all 9 songs
in the official Lizzo DLC music pack with custom community songs from BeatSaver.

Pipeline: v0.5328 — fully automated, no manual song_metadata.json editing required.
All custom songs deploy with 4 selectable modes (Standard, OneSaber, NoArrows, 90Degree).

## Target: Lizzo Official DLC Pack

- **Pack key**: `lizzo`
- **Pack bundle**: `lizzo_pack_assets_all_8bf3db217732cc18af0b9a2a32d13a9a.bundle`
- **9 songs** (each with 5 difficulties: Easy, Normal, Hard, Expert, ExpertPlus):
  1. 2 Be Loved (Am I Ready)  — BeatSaver MAP_ID: `2beloved` (Yes I'm A Mess / AJR)
  2. About Damn Time  — BeatSaver MAP_ID: `aboutdamntime` (The Middle / Jimmy Eat World)
  3. Cuz I Love You  — BeatSaver MAP_ID: `cuziloveyou` (Bring It On / Giga-P)
  4. Everybody's Gay  — BeatSaver MAP_ID: `everybodysgay` (Queencard / (G)I-DLE)
  5. Good As Hell  — BeatSaver MAP_ID: `goodashell` (Do You Wanna Taste It / Wig Wam)
  6. Juice  — BeatSaver MAP_ID: `juice` (Blame / Calvin Harris)
  7. Tempo  — BeatSaver MAP_ID: `tempo` (Bruises / Fox Stevenson)
  8. Truth Hurts  — BeatSaver MAP_ID: `truthhurts` (Genie In A Bottle / DisasterTheory)
  9. Worship  — BeatSaver MAP_ID: `worship` (Best Day Of My Life / American Authors)

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
# 1. 2 Be Loved (Am I Ready) - AJR
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 2beloved     --target 2BeLoved     --pcm16     --no-pad     --convert-to-v3     --deploy

# 2. About Damn Time - Jimmy Eat World
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song aboutdamntime     --target AboutDamnTime     --pcm16     --no-pad     --convert-to-v3     --deploy

# 3. Cuz I Love You - Giga-P
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song cuziloveyou     --target CuzILoveYou     --pcm16     --no-pad     --convert-to-v3     --deploy

# 4. Everybody's Gay - (G)I-DLE
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song everybodysgay     --target EverybodysGay     --pcm16     --no-pad     --convert-to-v3     --deploy

# 5. Good As Hell - Wig Wam
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song goodashell     --target GoodAsHell     --pcm16     --no-pad     --convert-to-v3     --deploy

# 6. Juice - Calvin Harris
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song juice     --target Juice     --pcm16     --no-pad     --convert-to-v3     --deploy

# 7. Tempo - Fox Stevenson
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song tempo     --target Tempo     --pcm16     --no-pad     --convert-to-v3     --deploy

# 8. Truth Hurts - DisasterTheory
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song truthhurts     --target TruthHurts     --pcm16     --no-pad     --convert-to-v3     --deploy

# 9. Worship - American Authors
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song worship     --target Worship     --pcm16     --no-pad     --convert-to-v3     --deploy
```
