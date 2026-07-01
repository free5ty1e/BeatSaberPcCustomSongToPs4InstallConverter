---
name: ps4-fsb5-audio
description: "PS4 FSB5 audio format for Beat Saber song audio, structure and replacement approach"
metadata:
  type: reference
---

# PS4 FSB5 Audio Format

> **Note:** Audio replacement is NOT yet implemented. This page documents what we know about the format for future work.

## Audio File Location

Each song's audio is stored in the song's AssetBundle as a TextAsset:
- Object class: 49 (TextAsset)
- Name: `<LevelId>.audio.gz` (e.g., `StartMeUp.audio.gz`)
- Contains: Gzip-compressed data with song metadata (checksum, sample count, frequency)

The actual audio stream is stored externally in an **FSB5** file embedded in the resources.assets archive.

## FSB5 Format

FSB5 (FMOD Studio Bank v5) is a proprietary audio format by Firelight Technologies. It stores:
- Multiple audio samples (compressed or uncompressed)
- Sample metadata (frequency, channels, loop points)
- Optional streaming data

## AudioClip Reference

The AudioClip object (class 83) in the bundle points to:
- `m_Resource` → external resource file + offset
- The resource file is part of the game's main assets archive (resources.assets or similar)

## Current State

We are NOT replacing audio yet. The current pipeline:
1. Replaces beatmap data (notes, obstacles) — ✅ Working
2. Keeps template audio — ✅ Verified (Start Me Up audio plays)
3. Audio replacement requires FSB5 creation tooling (fsbank or similar FMOD tools)

## Future Approach

To replace audio, we would need to:
1. Create FSB5-encoded audio from the custom song's audio file
2. Replace the AudioClip's `m_Resource` reference to point to the new FSB5 data
3. Update the AudioClip metadata (length, sample rate)
4. Potentially modify the `.audio.gz` TextAsset with updated song metadata

See also: [[assetbundle-structure]], [[beatmap-conversion-pipeline]]
