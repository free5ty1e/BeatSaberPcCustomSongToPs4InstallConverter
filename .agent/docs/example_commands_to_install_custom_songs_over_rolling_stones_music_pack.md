# Installing Custom Songs Over the Rolling Stones Music Pack

This document provides step-by-step, self-contained pipeline commands to replace all 11 songs
in the official Rolling Stones DLC music pack with custom community songs from BeatSaver.

Pipeline: v0.5328 — fully automated, no manual song_metadata.json editing required.
All custom songs deploy with 4 selectable modes (Standard, OneSaber, NoArrows, 90Degree).

## Target: Rolling Stones Official DLC Pack

- **Pack key**: `therollingstones`
- **Pack bundle**: `therollingstones_pack_assets_all_a99482a8a3da9e991e5ae36f2fea209c.bundle`
- **11 songs** (each with 5 difficulties: Easy, Normal, Hard, Expert, ExpertPlus):
  1. Angry  — BeatSaver MAP_ID: `angry` (Pegboard Nerds)
  2. Bite My Head Off  — BeatSaver MAP_ID: `bitemyheadoff` (Escaping the Ruins / Gareth Coker)
  3. Can't You Hear Me Knocking  — BeatSaver MAP_ID: `cantyouhearmeknocking` (Spicy / aespa)
  4. Gimme Shelter  — BeatSaver MAP_ID: `gimmeshelter` (Yes I'm A Mess / AJR)
  5. (I Can't Get No) Satisfaction  — BeatSaver MAP_ID: `satisfaction` (Dreams Come True / aespa)
  6. Live by the Sword  — BeatSaver MAP_ID: `lbythesword` (Take Me to the Beach / Imagine Dragons)
  7. Mess it Up  — BeatSaver MAP_ID: `messitup` (Powersnake / Brothers of Metal)
  8. Paint It Black  — BeatSaver MAP_ID: `paintitblack` (Time Lapse / TheFatRat)
  9. Sugar Soaker  — BeatSaver MAP_ID: `sugarsoaker` (Venom of Venus / Powerwolf)
  10. Sympathy For The Devil  — BeatSaver MAP_ID: `sympathyforthedevil` (LIT / Polyphia)
  11. Whole Wide World  — BeatSaver MAP_ID: `wholewideworld` (VOLUPTE / Tare)

## Where Target Metadata Lives

The song slot IDs and difficulty modes for the Rolling Stones pack are defined in:
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
# 1. Angry (Pegboard Nerds)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song angry     --target Angry     --pcm16     --no-pad     --convert-to-v3     --deploy

# 2. Bite My Head Off (Gareth Coker)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song bitemyheadoff     --target BiteMyHeadOff     --pcm16     --no-pad     --convert-to-v3     --deploy

# 3. Can't You Hear Me Knocking (aespa)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song cantyouhearmeknocking     --target CantYouHearMeKnocking     --pcm16     --no-pad     --convert-to-v3     --deploy

# 4. Gimme Shelter (AJR)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song gimmeshelter     --target GimmeShelter     --pcm16     --no-pad     --convert-to-v3     --deploy

# 5. Satisfaction (aespa)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song satisfaction     --target Satisfaction     --pcm16     --no-pad     --convert-to-v3     --deploy

# 6. Live by the Sword (Imagine Dragons)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song lbythesword     --target LiveByTheSword     --pcm16     --no-pad     --convert-to-v3     --deploy

# 7. Mess it Up (Brothers of Metal)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song messitup     --target MessItUp     --pcm16     --no-pad     --convert-to-v3     --deploy

# 8. Paint It Black (TheFatRat)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song paintitblack     --target PaintItBlack     --pcm16     --no-pad     --convert-to-v3     --deploy

# 9. Sugar Soaker (Powerwolf)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song sugarsoaker     --target SugarSoaker     --pcm16     --no-pad     --convert-to-v3     --deploy

# 10. LIT (Polyphia)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song sympathyforthedevil     --target SympathyForTheDevil     --pcm16     --no-pad     --convert-to-v3     --deploy

# 11. Whole Wide World (REZZ / Tare)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song wholewideworld     --target WholeWideWorld     --pcm16     --no-pad     --convert-to-v3     --deploy
```
