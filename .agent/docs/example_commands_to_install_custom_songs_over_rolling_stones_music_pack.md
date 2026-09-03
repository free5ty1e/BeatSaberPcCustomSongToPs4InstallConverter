# Installing Custom Songs Over the Rolling Stones Music Pack

This document provides step-by-step, self-contained pipeline commands to replace all 11 songs
in the official Rolling Stones DLC music pack with custom community songs from BeatSaver.

Pipeline: v0.5328 — fully automated, no manual song_metadata.json editing required.
All custom songs deploy with 4 selectable modes (Standard, OneSaber, NoArrows, 90Degree).

## Target: Rolling Stones Official DLC Pack

- **Pack key**: `therollingstones`
- **Pack bundle**: `therollingstones_pack_assets_all_a99482a8a3da9e991e5ae36f2fea209c.bundle`
- **11 songs** (each with 5 difficulties: Easy, Normal, Hard, Expert, ExpertPlus):
  1. Angry → Custom: Rhythm Is A Dancer (Pegboard Nerds)
  2. Bite My Head Off → Custom: Escaping the Ruins (MDK / Gareth Coker)
  3. Can't You Hear Me Knocking → Custom: Spicy (aespa)
  4. Gimme Shelter → Custom: Yes I'm A Mess (AJR)
  5. (I Can't Get No) Satisfaction → Custom: Dreams Come True (aespa)
  6. Live by the Sword → Custom: Take Me to the Beach (Imagine Dragons feat. Ado)
  7. Mess it Up → Custom: Powersnake (Brothers of Metal)
  8. Paint It Black → Custom: Time Lapse (TheFatRat)
  9. Sugar Soaker → Custom: Venom of Venus (Powerwolf)
  10. Sympathy For The Devil → Custom: LIT (Polyphia)
  11. Whole Wide World → Custom: VOLUPTE (Tare)

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
# 1. Angry → Rhythm Is A Dancer (Pegboard Nerds)
# Custom Song: Rhythm Is A Dancer
# Artist: Pegboard Nerds
# Album: (single)
# Year: 2021
# BeatSaver MAP_ID: c213
# BeatSaver Link: https://beatsaver.com/maps/c213
# Genre: Electronic / Drum & Bass
# BPM: 128
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song c213     --target Angry     --pcm16     --no-pad     --convert-to-v3     --deploy

# 2. Bite My Head Off → Escaping the Ruins (MDK / Gareth Coker)
# Custom Song: Escaping the Ruins
# Artist: MDK / Gareth Coker
# Album: Ori and the Blind Forest OST
# Year: 2015
# BeatSaver MAP_ID: 8c2a
# BeatSaver Link: https://beatsaver.com/maps/8c2a
# Genre: Orchestral / Video Game Music
# BPM: 160
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 8c2a     --target BiteMyHeadOff     --pcm16     --no-pad     --convert-to-v3     --deploy

# 3. Can't You Hear Me Knocking → Spicy (aespa)
# Custom Song: Spicy
# Artist: aespa
# Album: Savage (EP)
# Year: 2021
# BeatSaver MAP_ID: 32c7a
# BeatSaver Link: https://beatsaver.com/maps/32c7a
# Genre: K-Pop / Pop
# BPM: 115
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 32c7a     --target CantYouHearMeKnocking     --pcm16     --no-pad     --convert-to-v3     --deploy

# 4. Gimme Shelter → Yes I'm A Mess (AJR)
# Custom Song: Yes I'm A Mess
# Artist: AJR
# Album: The Maybe Man
# Year: 2023
# BeatSaver MAP_ID: 35ca9
# BeatSaver Link: https://beatsaver.com/maps/35ca9
# Genre: Indie Pop / Alternative
# BPM: 184
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 35ca9     --target GimmeShelter     --pcm16     --no-pad     --convert-to-v3     --deploy

# 5. Satisfaction → Dreams Come True (aespa)
# Custom Song: Dreams Come True
# Artist: aespa
# Album: Hot Mess (EP)
# Year: 2024
# BeatSaver MAP_ID: 21a3f
# BeatSaver Link: https://beatsaver.com/maps/21a3f
# Genre: K-Pop / Pop
# BPM: 99
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 21a3f     --target Satisfaction     --pcm16     --no-pad     --convert-to-v3     --deploy

# 6. Live by the Sword → Take Me to the Beach (Imagine Dragons feat. Ado)
# Custom Song: Take Me to the Beach
# Artist: Imagine Dragons feat. Ado
# Album: LOOM (Japanese Edition)
# Year: 2024
# BeatSaver MAP_ID: 42a0a
# BeatSaver Link: https://beatsaver.com/maps/42a0a
# Genre: Pop Rock / Alternative
# BPM: 105
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 42a0a     --target LiveByTheSword     --pcm16     --no-pad     --convert-to-v3     --deploy

# 7. Mess it Up → Powersnake (Brothers of Metal)
# Custom Song: Powersnake
# Artist: Brothers of Metal
# Album: Emblas Saga
# Year: 2020
# BeatSaver MAP_ID: 15db5
# BeatSaver Link: https://beatsaver.com/maps/15db5
# Genre: Power Metal / Symphonic Metal
# BPM: 175
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 15db5     --target MessItUp     --pcm16     --no-pad     --convert-to-v3     --deploy

# 8. Paint It Black → Time Lapse (TheFatRat)
# Custom Song: Time Lapse
# Artist: TheFatRat
# Album: TheFatRat Music Pack / Jackpot (EP)
# Year: 2015
# BeatSaver MAP_ID: a909
# BeatSaver Link: https://beatsaver.com/maps/a909
# Genre: Electronic / Glitch Hop
# BPM: 127
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song a909     --target PaintItBlack     --pcm16     --no-pad     --convert-to-v3     --deploy

# 9. Sugar Soaker → Venom of Venus (Powerwolf)
# Custom Song: Venom of Venus
# Artist: Powerwolf
# Album: The Sacrament of Sin
# Year: 2018
# BeatSaver MAP_ID: b7aa
# BeatSaver Link: https://beatsaver.com/maps/b7aa
# Genre: Power Metal / Heavy Metal
# BPM: 164
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song b7aa     --target SugarSoaker     --pcm16     --no-pad     --convert-to-v3     --deploy

# 10. Sympathy For The Devil → LIT (Polyphia)
# Custom Song: LIT
# Artist: Polyphia
# Album: New Levels New Devils
# Year: 2018
# BeatSaver MAP_ID: 1b457
# BeatSaver Link: https://beatsaver.com/maps/1b457
# Genre: Progressive Metal / Math Rock
# BPM: 99
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1b457     --target SympathyForTheDevil     --pcm16     --no-pad     --convert-to-v3     --deploy

# 11. Whole Wide World → VOLUPTE (Tare)
# Custom Song: VOLUPTE
# Artist: Tare
# Album: VOLUPTE (single)
# Year: 2023
# BeatSaver MAP_ID: a692
# BeatSaver Link: https://beatsaver.com/maps/a692
# Genre: Electronic / Bass Music
# BPM: 128
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song a692     --target WholeWideWorld     --pcm16     --no-pad     --convert-to-v3     --deploy
```