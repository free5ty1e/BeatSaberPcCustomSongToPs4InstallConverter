# Installing Custom Songs Over the Britney Spears Music Pack

This document provides step-by-step, self-contained pipeline commands to replace all 11 songs
in the official Britney Spears DLC music pack with custom community songs from BeatSaver.

Pipeline: v0.5328 — fully automated, no manual song_metadata.json editing required.
All custom songs deploy with 4 selectable modes (Standard, OneSaber, NoArrows, 90Degree).

## Target: Britney Spears Official DLC Pack

- **Pack key**: `britneyspears`
- **Pack bundle**: `britneyspears_pack_assets_all_18d2741e11e15c97493346b2797ea847.bundle`
- **11 songs** (each with 5 difficulties: Easy, Normal, Hard, Expert, ExpertPlus):
  1. Baby One More Time → Custom: Blinding Lights (The Weeknd)
  2. Circus → Custom: Shape of You (Ed Sheeran)
  3. Gimme More → Custom: Gangnam Style (PSY)
  4. I'm a Slave 4 U → Custom: Believer (Imagine Dragons)
  5. Me Against The Music → Custom: Mr. Blue Sky (Electric Light Orchestra)
  6. Oops!...I Did It Again → Custom: Rap God (Eminem)
  7. Overprotected → Custom: Dancing On My Own (Robyn)
  8. Scream & Shout → Custom: Levitating (Dua Lipa)
  9. Till The World Ends → Custom: Dance Monkey (Tones and I)
  10. Toxic → Custom: Toxic (Britney Spears) - Emir's map
  11. Womanizer → Custom: Womanizer (Britney Spears) - 12bd8 map

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
# Song: Blinding Lights - The Weeknd
# Custom Song: Blinding Lights
# Artist: The Weeknd
# Album: After Hours
# Year: 2019
# BeatSaver MAP_ID: 8553
# BeatSaver Link: https://beatsaver.com/maps/8553
# Genre: Synth-pop / R&B
# BPM: 171
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 8553     --target BabyOneMoreTime     --pcm16     --no-pad     --convert-to-v3     --deploy
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
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1672a     --target Circus     --pcm16     --no-pad     --convert-to-v3     --deploy
```

```bash
# Song: Gangnam Style - PSY
# Custom Song: Gangnam Style
# Artist: PSY
# Album: Psy 6 (Six Rules), Part 1
# Year: 2012
# BeatSaver MAP_ID: 141
# BeatSaver Link: https://beatsaver.com/maps/141
# Genre: K-Pop / Dance / Comedy
# BPM: 132
# Difficulties: 3/5 (Normal, Hard, Expert) [Ranked]
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 141     --target GimmeMore     --pcm16     --no-pad     --convert-to-v3     --deploy
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
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1fef     --target ImASlave4U     --pcm16     --no-pad     --convert-to-v3     --deploy
```

```bash
# Song: Mr. Blue Sky - Electric Light Orchestra
# Custom Song: Mr. Blue Sky
# Artist: Electric Light Orchestra
# Album: Out of the Blue
# Year: 1977
# BeatSaver MAP_ID: 570
# BeatSaver Link: https://beatsaver.com/maps/570
# Genre: Progressive Pop / Rock
# BPM: 180
# Difficulties: 5/5 (Easy through Expert+) [Ranked, greatyazer]
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 570     --target MeAgainstTheMusic     --pcm16     --no-pad     --convert-to-v3     --deploy
```

```bash
# Song: Rap God - Eminem
# Custom Song: Rap God
# Artist: Eminem
# Album: The Marshall Mathers LP 2
# Year: 2013
# BeatSaver MAP_ID: 46d4
# BeatSaver Link: https://beatsaver.com/maps/46d4
# Genre: Hip Hop / Rap
# BPM: 148
# Difficulties: 5/5 (Easy through Expert+) [Ryger, highest rated 0.959]
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 46d4     --target OopsIDidItAgain     --pcm16     --no-pad     --convert-to-v3     --deploy
```

```bash
# Song: Dancing On My Own - Robyn (Buzz Junkies Remix)
# Custom Song: Dancing On My Own (Buzz Junkies Remix)
# Artist: Robyn
# Album: Body Talk (Remixes)
# Year: 2010
# BeatSaver MAP_ID: (varies - check latest)
# BeatSaver Link: https://beatsaver.com/maps/ (search "Dancing On My Own Robyn")
# Genre: Electropop / Dance
# BPM: 128
# Difficulties: 2/5 (Hard, Expert) [constroyr]
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song <MAP_ID>     --target Overprotected     --pcm16     --no-pad     --convert-to-v3     --deploy
```

```bash
# Song: Levitating - Dua Lipa
# Custom Song: Levitating
# Artist: Dua Lipa
# Album: Future Nostalgia
# Year: 2020
# BeatSaver MAP_ID: (varies - check latest)
# BeatSaver Link: https://beatsaver.com/maps/ (search "Levitating Dua Lipa")
# Genre: Disco-pop / Dance-pop
# BPM: 103
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song <MAP_ID>     --target Scream&Shout     --pcm16     --no-pad     --convert-to-v3     --deploy
```

```bash
# Song: Dance Monkey - Tones and I
# Custom Song: Dance Monkey
# Artist: Tones and I
# Album: The Kids Are Coming
# Year: 2019
# BeatSaver MAP_ID: 6cc2
# BeatSaver Link: https://beatsaver.com/maps/6cc2
# Genre: Pop / Dance
# BPM: 98
# Difficulties: 5/5 (Easy through Expert+) [Most upvoted 7,791]
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 6cc2     --target TillTheWorldEnds     --pcm16     --no-pad     --convert-to-v3     --deploy
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
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 21540     --target Toxic     --pcm16     --no-pad     --convert-to-v3     --deploy
```

```bash
# Song: Womanizer - Britney Spears
# Custom Song: Womanizer
# Artist: Britney Spears
# Album: Circus
# Year: 2008
# BeatSaver MAP_ID: 12bd8
# BeatSaver Link: https://beatsaver.com/maps/12bd8
# Genre: Electropop / Dance-pop
# BPM: 140
# Difficulties: 5/5 (Easy through Expert+)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 12bd8     --target Womanizer     --pcm16     --no-pad     --convert-to-v3     --deploy
```