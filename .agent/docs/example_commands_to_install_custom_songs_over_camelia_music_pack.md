# Installing Custom Songs Over the Camelia (Chromeo) Music Pack

This document provides step-by-step, self-contained pipeline commands to replace all 6 songs
in the official Camelia (Chromeo) DLC music pack with custom community songs from BeatSaver.

Pipeline: v0.5328 — fully automated, no manual song_metadata.json editing required.
All custom songs deploy with 4 selectable modes (Standard, OneSaber, NoArrows, 90Degree).

## Target: Camelia (Chromeo) Official DLC Pack

- **Pack key**: `camelia`
- **Pack bundle**: `camelia_pack_assets_all_<hash>.bundle`
- **6 songs** (each with 5 difficulties: Easy, Normal, Hard, Expert, ExpertPlus):
  1. Crystallized → Custom: Sexy Socialite (Chromeo)
  2. Cyclehit → Custom: Jealous (I Ain't With It) (Chromeo)
  3. Exit Earth → Custom: 'Roni Got Me Stressed Out (Chromeo)
  4. Ghost → Custom: Green Light (Chromeo Remix) (Lorde, Chromeo)
  5. Lightsetup → Custom: 1999 (Charli XCX & Troye Sivan)
  6. Whatcat → Custom: FANCY (TWICE)

## Where Target Metadata Lives

The song slot IDs and difficulty modes for the Camelia pack are defined in:
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
# 1. Crystallized → Sexy Socialite (Chromeo)
# Custom Song: Sexy Socialite
# Artist: Chromeo
# Album: Head Over Heels
# Year: 2018
# BeatSaver MAP_ID: 6f1f
# BeatSaver Link: https://beatsaver.com/maps/6f1f
# Genre: Funk / Disco / Electronic
# BPM: 142
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 6f1f     --target Crystallized     --pcm16     --no-pad     --convert-to-v3     --deploy

# 2. Cyclehit → Jealous (I Ain't With It) (Chromeo)
# Custom Song: Jealous (I Ain't With It)
# Artist: Chromeo
# Album: Head Over Heels
# Year: 2018
# BeatSaver MAP_ID: 111fd
# BeatSaver Link: https://beatsaver.com/maps/111fd
# Genre: Funk / Disco / Electronic
# BPM: 129
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 111fd     --target Cyclehit     --pcm16     --no-pad     --convert-to-v3     --deploy

# 3. Exit Earth → 'Roni Got Me Stressed Out (Chromeo)
# Custom Song: 'Roni Got Me Stressed Out
# Artist: Chromeo
# Album: Head Over Heels
# Year: 2018
# BeatSaver MAP_ID: 115ba
# BeatSaver Link: https://beatsaver.com/maps/115ba
# Genre: Funk / Disco / Electronic
# BPM: 117
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 115ba     --target ExitEarth     --pcm16     --no-pad     --convert-to-v3     --deploy

# 4. Ghost → Green Light (Chromeo Remix) (Lorde, Chromeo)
# Custom Song: Green Light (Chromeo Remix)
# Artist: Lorde, Chromeo
# Album: Melodrama (Remixes)
# Year: 2017
# BeatSaver MAP_ID: 37d5
# BeatSaver Link: https://beatsaver.com/maps/37d5
# Genre: Electropop / Remix
# BPM: 121
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 37d5     --target Ghost     --pcm16     --no-pad     --convert-to-v3     --deploy

# 5. Lightsetup → 1999 (Charli XCX & Troye Sivan)
# Custom Song: 1999
# Artist: Charli XCX & Troye Sivan
# Album: (single)
# Year: 2018
# BeatSaver MAP_ID: 5352
# BeatSaver Link: https://beatsaver.com/maps/5352
# Genre: Pop / Synth-pop
# BPM: 124
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 5352     --target Lightsetup     --pcm16     --no-pad     --convert-to-v3     --deploy

# 6. Whatcat → FANCY (TWICE)
# Custom Song: FANCY
# Artist: TWICE
# Album: Fancy You
# Year: 2019
# BeatSaver MAP_ID: 47f3
# BeatSaver Link: https://beatsaver.com/maps/47f3
# Genre: K-Pop / Pop
# BPM: 132
# Difficulties: 5/5 (Easy through Expert+) [Normal, Hard, Expert, Expert+]
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 47f3     --target Whatcat     --pcm16     --no-pad     --convert-to-v3     --deploy
```