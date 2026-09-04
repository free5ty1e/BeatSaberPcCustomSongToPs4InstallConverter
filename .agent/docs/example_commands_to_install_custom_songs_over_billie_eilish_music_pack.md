# Installing Custom Songs Over the Billie Eilish Music Pack

This document provides step-by-step, self-contained pipeline commands to replace all 10 songs
in the official Billie Eilish DLC music pack with custom community songs from BeatSaver.

Pipeline: v0.5328 — fully automated, no manual song_metadata.json editing required.
All custom songs deploy with 4 selectable modes (Standard, OneSaber, NoArrows, 90Degree).

## Target: Billie Eilish Official DLC Pack

- **Pack key**: `billieeilish`
- **Pack bundle**: `billieeilish_pack_assets_all_ba4a0db5570760b21ebcbb2ec7a8d321.bundle`
- **10 songs** (each with 5 difficulties: Easy, Normal, Hard, Expert, ExpertPlus):
  1. all the good girls go to hell → Custom: Mirror (Ado)
  2. bad guy → Custom: Odo (Ado)
  3. bellyache → Custom: ATTITUDE (IVE)
  4. bury a friend → Custom: Baddie (IVE)
  5. happier than ever → Custom: Cosmic (Red Velvet)
  6. n da → Custom: Duvet (Bôa)
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

# 6. nda → Duvet (Bôa)
# Custom Song: Duvet
# Artist: Bôa
# Album: Race of a Thousand Camels
# Year: 1998
# BeatSaver MAP_ID: 4b107
# BeatSaver Link: https://beatsaver.com/maps/4b107
# Genre: Alternative Rock / Indie
# BPM: 186
# Difficulties: 5/5 (Easy through Expert+) [Noodle walls]
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 4b107     --target NDA     --pcm16     --no-pad     --convert-to-v3     --deploy-full

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
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 2475     --target CuzILoveYou     --pcm16     --no-pad     --convert-to-v3     --deploy-full
```