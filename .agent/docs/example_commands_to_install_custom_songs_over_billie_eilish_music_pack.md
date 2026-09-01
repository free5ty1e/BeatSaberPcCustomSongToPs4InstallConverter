# Installing Custom Songs Over the Billie Eilish Music Pack

This document provides step-by-step, self-contained pipeline commands to replace all 10 songs
in the official Billie Eilish DLC music pack with custom community songs from BeatSaver.

Pipeline: v0.5328 — fully automated, no manual song_metadata.json editing required.
All custom songs deploy with 4 selectable modes (Standard, OneSaber, NoArrows, 90Degree).

## Target: Billie Eilish Official DLC Pack

- **Pack key**: `billieeilish`
- **Pack bundle**: `billieeilish_pack_assets_all_ba4a0db5570760b21ebcbb2ec7a8d321.bundle`
- **10 songs** (each with 5 difficulties: Easy, Normal, Hard, Expert, ExpertPlus):
  1. all the good girls go to hell  — BeatSaver MAP_ID: `allthegoodgirlsgo to hell` (Mirror / Ado)
  2. bad guy  — BeatSaver MAP_ID: `badguy` (Odo / Ado)
  3. bellyache  — BeatSaver MAP_ID: `bellyache` (ATTITUDE / IVE)
  4. bury a friend  — BeatSaver MAP_ID: `buryafriend` (Baddie / IVE)
  5. happier than ever  — BeatSaver MAP_ID: `happierthanever` (Cosmic / Red Velvet)
  6. n da  — BeatSaver MAP_ID: `nda` (Duvet / Bôa)
  7. therefore i am  — BeatSaver MAP_ID: `thereforeiam` (Who's Laughing Now / Ava Max)
  8. 2 be loved (am i ready)  — BeatSaver MAP_ID: `2beloved` (Yes I'm A Mess / AJR)
  9. about damn time  — BeatSaver MAP_ID: `aboutdamntime` (The Middle / Jimmy Eat World)
  10. cuz i love you  — BeatSaver MAP_ID: `cuziloveyou` (Bring It On / Giga-P)

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
# 1. all the good girls go to hell - Ado
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song allthegoodgirlsgothell     --target AllTheGoodGirlsGoToHell     --pcm16     --no-pad     --convert-to-v3     --deploy

# 2. bad guy - Ado
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song badguy     --target BadGuy     --pcm16     --no-pad     --convert-to-v3     --deploy

# 3. bellyache - IVE
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song bellyache     --target Bellyache     --pcm16     --no-pad     --convert-to-v3     --deploy

# 4. bury a friend - IVE
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song buryafriend     --target BuryAFriend     --pcm16     --no-pad     --convert-to-v3     --deploy

# 5. happier than ever - Red Velvet
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song happierthanever     --target HappierThanEver     --pcm16     --no-pad     --convert-to-v3     --deploy

# 6. nda - Bôa
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song nda     --target NDA     --pcm16     --no-pad     --convert-to-v3     --deploy

# 7. therefore i am - Ava Max
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song thereforeiam     --target ThereforeIAm     --pcm16     --no-pad     --convert-to-v3     --deploy

# 8. 2 be loved (am i ready) - AJR
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 2beloved     --target 2BeLoved     --pcm16     --no-pad     --convert-to-v3     --deploy

# 9. about damn time - Jimmy Eat World
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song aboutdamntime     --target AboutDamnTime     --pcm16     --no-pad     --convert-to-v3     --deploy

# 10. cuz i love you - Giga-P
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song cuziloveyou     --target CuzILoveYou     --pcm16     --no-pad     --convert-to-v3     --deploy
```
