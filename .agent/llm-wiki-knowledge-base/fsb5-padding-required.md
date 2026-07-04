---
name: fsb5-padding-required
description: "PS4 audio decoder requires FSB5 padded to 12MB to avoid immediate freeze"
metadata:
  type: reference
---

# FSB5 12MB Padding Fix

## The Problem
When the FSB5 .resource file is smaller than the original (e.g., 152KB silence instead of 12MB original audio), the PS4's audio decoder freezes immediately on the first frame. The game shows the initial level frame but no audio plays and the game logic hangs.

## The Fix
Pad the FSB5 to exactly 12,305,632 bytes (matching the original Start Me Up .resource file size) using trailing zero bytes:

```python
if len(fsb5_bytes) < ORIGINAL_RESOURCE_SIZE:
    padding = bytes(ORIGINAL_RESOURCE_SIZE - len(fsb5_bytes))
    fsb5_bytes = fsb5_bytes + padding
```

This is implemented in `audio_to_fsb5()` in `full_custom_song_pipeline.py`.

## Why It Works
The PS4's Unity runtime pre-allocates a fixed-size buffer for audio resource data based on the original .resource size. If the new FSB5 is smaller than this buffer, Unity may read beyond the end of the data or the decoder may fail to initialize properly. Padding ensures the buffer is fully populated with valid (or at least non-fatal) data.

## Limitations
- Padding alone is NOT sufficient — the audio content must be valid HEVAG (not all zeros)
- All-zero silence with 12MB padding allowed notes to move for ~1 second before freezing (Experiment 80)
- The decoder requires real audio content using at least the 5 standard HEVAG predictors
- Optimal: 5-predictor encoder (opt_encode_frame) + 12MB padding

## Related
- [[ps4-audio-decoder-behavior]]
