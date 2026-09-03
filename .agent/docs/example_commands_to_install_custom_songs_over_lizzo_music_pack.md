# Installing Custom Songs Over the Lizzo Music Pack

This document provides step-by-step, self-contained pipeline commands to replace all 9 songs
in the official Lizzo DLC music pack with custom community songs from BeatSaver.

Pipeline: v0.5328 — fully automated, no manual song_metadata.json editing required.
All custom songs deploy with 4 selectable modes (Standard, OneSaber, NoArrows, 90Degree).

## Target: Lizzo Official DLC Pack

- **Pack key**: `lizzo`
- **Pack bundle**: `lizzo_pack_assets_all_8bf3db217732cc18af0b9a2a32d13a9a.bundle`
- **9 songs** (each with 5 difficulties: Easy, Normal, Hard, Expert, ExpertPlus):
  1. 2 Be Loved (Am I Ready) → Custom: Yes I'm A Mess (AJR)
  2. About Damn Time → Custom: The Middle (Jimmy Eat World)
  3. Cuz I Love You → Custom: Bring It On (Giga-P)
  4. Everybody's Gay → Custom: Queencard ((G)I-DLE)
  5. Good As Hell → Custom: Do You Wanna Taste It (Wig Wam)
  6. Juice → Custom: Blame (Calvin Harris feat. John Newman)
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
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 35ca9     --target 2BeLoved     --pcm16     --no-pad     --convert-to-v3     --deploy

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
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 27a13     --target AboutDamnTime     --pcm16     --no-pad     --convert-to-v3     --deploy

# 3. Cuz I Love You → Bring It On (Giga-P)
# Custom Song: Bring It On
# Artist: Giga-P
# Album: (single)
# Year: 2014
# BeatSaver MAP_ID: 2475
# BeatSaver Link: https://beatsaver.com/maps/2475
# Genre: Vocaloid / Electronic
# BPM: 160
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 2475     --target CuzILoveYou     --pcm16     --no-pad     --convert-to-v3     --deploy

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
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 40a53     --target EverybodysGay     --pcm16     --no-pad     --convert-to-v3     --deploy

# 5. Good As Hell → Do You Wanna Taste It (Wig Wam)
# Custom Song: Do You Wanna Taste It
# Artist: Wig Wam
# Album: Non Stop Rock'n Roll (Peacemaker Intro)
# Year: 2010
# BeatSaver MAP_ID: 212c5
# BeatSaver Link: https://beatsaver.com/maps/212c5
# Genre: Glam Rock / Hard Rock
# BPM: 184
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 212c5     --target GoodAsHell     --pcm16     --no-pad     --convert-to-v3     --deploy

# 6. Juice → Blame (Calvin Harris feat. John Newman)
# Custom Song: Blame
# Artist: Calvin Harris feat. John Newman
# Album: Motion
# Year: 2014
# BeatSaver MAP_ID: 5758
# BeatSaver Link: https://beatsaver.com/maps/5758
# Genre: EDM / Pop
# BPM: 128
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 5758     --target Juice     --pcm16     --no-pad     --convert-to-v3     --deploy

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
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song ae3c     --target Tempo     --pcm16     --no-pad     --convert-to-v3     --deploy

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
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 50a08     --target TruthHurts     --pcm16     --no-pad     --convert-to-v3     --deploy

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
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 86e9     --target Worship     --pcm16     --no-pad     --convert-to-v3     --deploy
```