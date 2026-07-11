---
name: beatmap-audio-sync
description: "How PS4 Beat Saber synchronizes beatmap notes to audio, and the bpmData root cause of progressive desync"
metadata:
  type: reference
---

# Beatmap ↔ Audio Synchronization

## Overview

PS4 Beat Saber synchronizes visual note blocks with audio using a **beat→time mapping** derived from the song's BPM data. Beatmap `b` values are in **beats** (not seconds), and the game converts them to sample positions using `bpmData` in `audio.gz`.

## The bpmData Structure

The `audio.gz` TextAsset in each song's bundle contains JSON with a `bpmData` array:

```json
"bpmData": [
    {"si": 0, "ei": 9425915, "sb": 0.0, "eb": 436.16}
]
```

Each region maps a sample range to a beat range:
- `si` — start sample index (at 44100 Hz)
- `ei` — end sample index
- `sb` — start beat (at the start sample)
- `eb` — end beat (at the end sample)

The game linearly interpolates within each region: a note at beat `b` maps to sample position:
```
sample = si + (b - sb) * (ei - si) / (eb - sb)
```

## CRITICAL: eb/sb Must Be in Beats, NOT Seconds

### ❌ WRONG (The Bug — What We Had)
```python
# Pipeline line 273 (BEFORE fix):
"bpmData": [{"si": 0, "ei": sample_count, "sb": 0.0, "eb": duration}]
```
`eb = duration` (seconds) instead of beats. For a 120 BPM song:
- eb = 135.6 (seconds) instead of 271.2 (beats)
- Game computes BPM = 135.59 beats / 135.6s = 1.0 beats/s = **60 BPM instead of 120**
- Notes placed at DOUBLE the correct time position
- **Progressive desync**: A note at beat 30 arrives at 30s instead of 15s (15s late)
- Desync grows linearly: beat 60 → 60s instead of 30s (30s late)

### ✅ CORRECT (The Fix)
```python
# Use BPMInfo.dat from BeatSaver (preferred):
# BPMInfo.dat has _regions with _startSampleIndex, _endSampleIndex,
# _startBeat, _endBeat — maps directly to bpmData

# Fallback: compute from Info.dat _beatsPerMinute:
bpm = info["_beatsPerMinute"]  # e.g. 120.0
total_beats = duration * bpm / 60.0
"bpmData": [{"si": 0, "ei": sample_count, "sb": 0.0, "eb": total_beats}]
```

## Source of BPM Data

### 1. BPMInfo.dat (Preferred — 19/96 songs in songs_repo)
Contains exact sample-to-beat mappings with multiple regions for BPM changes:
```json
{
    "_version": "2.0.0",
    "_songSampleCount": 5979572,
    "_songFrequency": 44100,
    "_regions": [
        {"_startSampleIndex": 0, "_endSampleIndex": 6407677,
         "_startBeat": 0, "_endBeat": 445.583038},
        ...
    ]
}
```
Directly maps to PS4 bpmData format — just rename fields.

### 2. Info.dat (Fallback)
Has `_beatsPerMinute` (constant BPM for the song). For songs with BPM changes,
use `_customData._BPMInfo` if available.

### 3. Manual Fallback
If neither exists, assume 120 BPM and compute:
```python
eb = sample_count / 44100 * bpm / 60.0
```

## Implementation

In `full_custom_song_pipeline.py`, the `load_bpm_regions()` function (added in v0.50)
reads BPMInfo.dat first, falls back to Info.dat BPM computation:

```python
def load_bpm_regions(song_dir, sample_count):
    bpm_path = os.path.join(song_dir, "BPMInfo.dat")
    if os.path.exists(bpm_path):
        regions = json.load(open(bpm_path))["_regions"]
        return [{"si": r["_startSampleIndex"], "ei": r["_endSampleIndex"],
                 "sb": r["_startBeat"], "eb": r["_endBeat"]} for r in regions]
    # Fallback: compute from Info.dat BPM
    ...
    total_beats = duration * bpm / 60.0
    return [{"si": 0, "ei": sample_count, "sb": 0.0, "eb": total_beats}]
```

## Other Sync-Related Fields

### songSampleCount and songFrequency
Must match the actual audio duration:
```python
sample_count = int(audio_duration * 44100)
```
These define total audio length. If wrong, the game's beat→time mapping
at the song boundaries will be incorrect (notes may extend beyond song end).

### _songTimeOffset (Info.dat)
Usually 0.0. If non-zero, this offset is applied to the audio start time.
Not currently handled by the pipeline (not needed for standard BeatSaver songs).

### BPM Changes in BeatSaver Songs
Some songs have variable BPM (intro at half tempo, etc.). The BPMInfo.dat
captures these with multiple `_regions`. The pipeline handles this correctly
when BPMInfo.dat is present. For songs without BPMInfo.dat, only a constant
BPM from Info.dat is used, which may cause minor desync if the song has
significant tempo variations.

## Testing Sync

To verify sync on PS4:
1. Deploy a song with known BPM
2. Play the song, observe first note timing
3. If the first note is off, check bpmData eb value vs expected total beats
4. If desync worsens progressively, the bpmData beat→sample ratio is wrong
5. If notes end before/after audio, check songSampleCount

### bpmEvents Empty (Root Cause #2)

**Bug (v0.50-0.51):** The V2→V3 beatmap converter set `bpmEvents: []` (empty).
The PS4 game's `BeatmapDataLoader` requires bpmEvents to determine tempo.
Without them, the game defaults to BPM=60, making notes at ~120 BPM appear 
at roughly 2× the correct time ("very very late" user reports).

**Fix (v0.52):** `convert_v2_to_v3()` now reads BPM from Info.dat and sets:
```json
"bpmEvents": [{"b": 0, "m": <BPM>}]
```

### V3.0.0 Beatmaps With Empty bpmEvents (Root Cause #3)

**Bug (v0.52):** Some BeatSaver songs are already V3.0.0 format (`colorNotes`,
not `_notes`) but still have `bpmEvents: []`. The `--convert-to-v3` flag only
processed V2 beatmaps (detected by `_notes` key), so V3 beatmaps were passed
through unchanged — same BPM=60 fallback.

**Fix (v0.52c):** Pipeline now patches `bpmEvents` on ANY beatmap that lacks
them:
```python
if not data.get('bpmEvents'):
    data['bpmEvents'] = [{"b": 0, "m": bpm}]
```

### Note Color Field: `c` vs `a` (Root Cause #4)

**Bug (v0.50-0.52):** V2→V3 converter set `"a": nt` for note color.
The PS4 game uses the `c` field for color (V3.3.0+ format), not `a`.
Without `c`, the game defaults to `c: 0` (Red), making all notes appear
Red regardless of beatmap color data.

**Evidence from Espresso (V3.3.0, WORKING):**
- `a: 0` for ALL 262 notes (constant — NOT the actual color field)
- `c: 0` or `c: 1` alternating — this IS the color field

**Fix (v0.53):** Both `a` and `c` are set from V2 `_type`:
```python
base["a"] = nt   # standard V3 field
base["c"] = nt   # PS4 game uses this for color (V3.3.0+)
```

The PS4 port shipped with V4.0.0 format bundles where note color is stored
in `colorNotesData[].c`, so the parser expects `c` as the color source.

## Related
- [[beatmap-conversion-pipeline]]
- [[ps4-fsb5-pcm16-format]]
- [[note-color-field-version-differences]]
- [[development-workflow]]
