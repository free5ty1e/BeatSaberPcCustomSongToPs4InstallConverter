# Camellia Music Pack Replacement: Example Workflow

This document records the exact steps taken to replace the official Camellia Music Pack with 6 custom community songs.

## Target Pack: Camellia
- **Replacement Slots:** Crystallized, CycleHit, ExitThisEarthsAtomosphere, Ghost, LightItUp, WhatTheCat

## Workflow Execution Log

### 1. Crystallized (Bloom - ID: 12a)
**Command:**
```bash
python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song 12a \
    --target Crystallized \
    --song-name "Bloom" \
    --artist "ODESZA" \
    --deploy --generate-config --deploy-config
```
**Result:** ✅ Success. Pipeline converted, metadata injected, and deployed to PS4.

### 2. Cycle Hit (Powerful - ID: 133)
**Command:**
```bash
python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song 133 \
    --target CycleHit \
    --song-name "Powerful" \
    --artist "Major Lazer" \
    --deploy --generate-config --deploy-config
```
**Result:** ✅ Success. Pipeline converted, metadata injected, and deployed to PS4.

### 3. EXiT This Earth's Atmosphere (Red Lips - ID: 156)
**Command:**
```bash
python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song 156 \
    --target ExitThisEarthsAtomosphere \
    --song-name "Red Lips" \
    --artist "GTA / Mendus" \
    --deploy --generate-config --deploy-config
```
**Result:** ✅ Success. Pipeline converted, metadata injected, and deployed to PS4.

### 4. Ghost (Lone Digger - ID: 1bf)
**Command:**
```bash
python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song 1bf \
    --target Ghost \
    --song-name "Lone Digger" \
    --artist "Caravan Palace" \
    --deploy --generate-config --deploy-config
```
**Result:** ✅ Success. Pipeline converted, metadata injected, and deployed to PS4.

### 5. Light it up (Batshit - ID: 7e)
**Command:**
```bash
python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song 7e \
    --target LightItUp \
    --song-name "Batshit" \
    --artist "Sofi Tukker" \
    --deploy --generate-config --deploy-config
```
**Result:** ✅ Success. Pipeline converted, metadata injected, and deployed to PS4.

### 6. WHAT THE CAT!? (G.O.M.D - ID: 7f)
**Command:**
```bash
python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song 7f \
    --target WhatTheCat \
    --song-name "G.O.M.D" \
    --artist "Sickick" \
    --deploy --generate-config --deploy-config
```
**Result:** ✅ Success. Pipeline converted, metadata injected, and deployed to PS4.
