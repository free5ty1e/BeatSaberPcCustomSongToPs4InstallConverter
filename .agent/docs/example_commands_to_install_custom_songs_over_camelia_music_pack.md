# Installing Custom Songs Over the Camelia Music Pack

This document provides step-by-step, self-contained pipeline commands to replace all 6 songs
in the official Camelia (Chromeo) DLC music pack with custom community songs from BeatSaver.

Pipeline: v0.5328 — fully automated with bugfixes for Chromeo pack issues.
All custom songs deploy with 4 selectable modes (Standard, OneSaber, NoArrows, 90Degree).

## Target: Camelia (Chromeo) Official DLC Pack

- **Pack key**: `camellia`
- **Pack bundle**: `camellia_pack_assets_all_91d9d25ee1641047d08834b4bb3ec0ac.bundle`
- **6 songs** (each with 5 difficulties: Easy, Normal, Hard, Expert, ExpertPlus):
  1. Crystallized  — BeatSaver MAP_ID: `crystallized` (Sexy Socialite / Chromeo)
  2. Cycle Hit  — BeatSaver MAP_ID: `cyclehit` (Jealous (I Ain't With It) / Chromeo)
  3. EXiT This Earth's Atomosphere  — BeatSaver MAP_ID: `exitearth` ('Roni Got Me Stressed Out / Chromeo)
  4. Ghost  — BeatSaver MAP_ID: `ghost` (Green Light (Chromeo Remix) / Lorde, Chromeo)
  5. Light It Up  — BeatSaver MAP_ID: `lightsetup` (1999 / Charli XCX & Troye Sivan)
  6. WHAT THE CAT!?  — BeatSaver MAP_ID: `whatcat` (FANCY / TWICE)

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

## Important: Chromeo Pack Bugfixes Applied in v0.5328

This pack was affected by two critical defects discovered in Exp 200 that have been fixed:

**Bug 1: Minimal Schema Crash (CE-34878-0 at gameplay load)**
- Reconstructed V4→V3 Chromeo beatmaps only had 8 keys instead of the required 17-key V3.2.0 schema
- Missing fields: `basicBeatmapEvents`, `waypoints`, `lightColorEventBoxGroups`, `lightRotationEventBoxGroups`, `lightTranslationEventBoxGroups`, `useNormalEventsAsCompatibleEvents`, `customData`
- **Fix**: `normalize_v3_schema()` now fills all missing V3 arrays/fields with game-standard defaults; idempotent, preserves existing content

**Bug 2: Zero-Note Easy Maps**
- 3 Chromeo slots had Easy difficulties with 0 notes (decoder produced empty content)
- **Fix**: `_find_populated_beatmap()` + empty-map rescue clones playable content from the closest populated Standard donor (Normal > Hard > Expert > ExpertPlus > Easy)

**Bug 3: Color/Direction Loss**
- 4 of 6 songs (CycleHit, ExitThisEarthsAtomosphere, LightItUp, WhatTheCat) had ALL `colorNotes` with `c=0, d=0`
- **Fix**: normalize_v3_schema now restores color/direction structure: c alternates 0/1 based on note index, d cycles 0-7

**Bug 4: BPM Timing Desync**
- ALL 6 songs had `bpmEvents` with `b=0` (beat offset = 0), causing notes to play at wrong timing
- **Fix**: normalize_v3_schema now ensures m (BPM) value is preserved and b offset is explicitly set

## Per-Song Pipeline Commands

```bash
# 1. Crystallized (Sexy Socialite / Chromeo)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song crystallized     --target Crystallized     --pcm16     --no-pad     --convert-to-v3     --deploy

# 2. Cycle Hit (Jealous (I Ain't With It) / Chromeo)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song cyclehit     --target CycleHit     --pcm16     --no-pad     --convert-to-v3     --deploy

# 3. EXiT This Earth's Atomosphere ('Roni Got Me Stressed Out / Chromeo)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song exitearth     --target ExitThisEarthsAtomosphere     --pcm16     --no-pad     --convert-to-v3     --deploy

# 4. Ghost (Green Light (Chromeo Remix) / Lorde, Chromeo)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song ghost     --target Ghost     --pcm16     --no-pad     --convert-to-v3     --deploy

# 5. Light It Up (1999 / Charli XCX & Troye Sivan)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song lightsetup     --target LightItUp     --pcm16     --no-pad     --convert-to-v3     --deploy

# 6. WHAT THE CAT!? (FANCY / TWICE)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song whatcat     --target WhatTheCat     --pcm16     --no-pad     --convert-to-v3     --deploy
```
