# Installing Custom Songs Over the Britney Spears Music Pack

This document provides step-by-step, self-contained pipeline commands to replace all 11 songs
in the official Britney Spears DLC music pack with custom community songs from BeatSaver.

Pipeline: v0.5328 — fully automated, no manual song_metadata.json editing required.
All custom songs deploy with 4 selectable modes (Standard, OneSaber, NoArrows, 90Degree).

## Target: Britney Spears Official DLC Pack

- **Pack key**: `britneyspears`
- **Pack bundle**: `britneyspears_pack_assets_all_18d2741e11e15c97493346b2797ea847.bundle`
- **11 songs** (each with 5 difficulties: Easy, Normal, Hard, Expert, ExpertPlus):
  1. Baby One More Time  — BeatSaver MAP_ID: 8553 (The Weeknd)
  2. Circus               — BeatSaver MAP_ID: 1672a (Ed Sheeran)
  3. Gimme More           — BeatSaver MAP_ID: 141  (PSY)
  4. I'm a Slave 4 U      — BeatSaver MAP_ID: 1fef (Imagine Dragons - Believer)
  5. Me Against The Music — BeatSaver MAP_ID: 570 (Electric Light Orchestra - Mr. Blue Sky)
  6. Oops!...I Did It Again — BeatSaver MAP_ID: 46d4 (Eminem - Rap God)
  7. Overprotected         — BeatSaver MAP_ID: 11cf8 (Robyn - Up & Down)
  8. Scream & Shout        — BeatSaver MAP_ID: bd45 ( artist TBD )
  9. Till The World Ends   — BeatSaver MAP_ID: 6cc2 (Tones and I - Dance Monkey)
  10. Toxic                — (selected BeatSaver map, MAP_ID to be determined)
  11. Womanizer            — (selected BeatSaver map, MAP_ID to be determined)

## Where Target Metadata Lives

The song slot IDs and difficulty modes for the Britney Spears pack are defined in:
  `/workspace/beat_saber_deluxe/beat_saber_song_ids.json`

Key structure (read from the JSON):

```json
{
  "pack": "britneyspears",
  "songs": [
    {"songName": "...Baby One More Time", "songID": "BabyOneMoreTime", ...},
    {"songName": "Circus", "songID": "Circus", ...},
    ...
  ]
}
```

Each song has a `songID` that maps to the pipeline `--target` parameter (slot name).

## Where Local Song Metadata JSON is Stored

The local installed-song metadata file is at:
  `/workspace/beat_saber_deluxe/song_metadata.json`

This file maps display names to source hash IDs and is **NOT included in the repository**.
It is automatically managed by the pipeline (build_deploy_all38.py). 
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
# BeatSaver: https://beatsaver.com/maps/8553
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 8553     --target BabyOneMoreTime     --pcm16     --no-pad     --convert-to-v3     --deploy
```

```bash
# Song: Shape of You - Ed Sheeran
# BeatSaver: https://beatsaver.com/maps/1672a
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1672a     --target Circus     --pcm16     --no-pad     --convert-to-v3     --deploy
```

```bash
# Song: Gangnam Style - PSY
# BeatSaver: https://beatsaver.com/maps/141
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 141     --target GimmeMore     --pcm16     --no-pad     --convert-to-v3     --deploy
```

```bash
# Song: Believer - Imagine Dragons
# BeatSaver: https://beatsaver.com/maps/1fef
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1fef     --target ImASlave4U     --pcm16     --no-pad     --convert-to-v3     --deploy
```

```bash
# Song: Mr. Blue Sky - Electric Light Orchestra
# BeatSaver: https://beatsaver.com/maps/570
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 570     --target MeAgainstTheMusic     --pcm16     --no-pad     --convert-to-v3     --deploy
```

```bash
# Song: Rap God - Eminem
# BeatSaver: https://beatsaver.com/maps/46d4
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 46d4     --target OopsIDidItAgain     --pcm16     --no-pad     --convert-to-v3     --deploy
```

```bash
# Song: Up & Down - Robyn
# BeatSaver: https://beatsaver.com/maps/11cf8
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 11cf8     --target Overprotected     --pcm16     --no-pad     --convert-to-v3     --deploy
```

```bash
# Song: [TBD] - [artist]
# BeatSaver: https://beatsaver.com/maps/bd45
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song bd45     --target Scream&Shout     --pcm16     --no-pad     --convert-to-v3     --deploy
```

```bash
# Song: Dance Monkey - Tones and I
# BeatSaver: https://beatsaver.com/maps/6cc2
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 6cc2     --target TillTheWorldEnds     --pcm16     --no-pad     --convert-to-v3     --deploy
```

```bash
# Song: Toxic - [artist]
# BeatSaver: https://beatsaver.com/maps/<TOXIC_MAP_ID>
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song <TOXIC_MAP_ID>     --target Toxic     --pcm16     --no-pad     --convert-to-v3     --deploy
```

```bash
# Song: Womanizer - [artist]
# BeatSaver: https://beatsaver.com/maps/<WOMANIZER_MAP_ID>
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song <WOMANIZER_MAP_ID>     --target Womanizer     --pcm16     --no-pad     --convert-to-v3     --deploy
```
