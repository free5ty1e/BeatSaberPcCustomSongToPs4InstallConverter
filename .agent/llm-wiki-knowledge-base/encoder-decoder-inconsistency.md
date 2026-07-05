---
name: encoder-decoder-inconsistency
description: "Our HEVAG encoder produces output that doesn't match the decoder, causing PS4 audio decoder to hang"
metadata:
  type: reference
---

# HEVAG Encoder/Decoder Inconsistency

## The Problem
When decoding the original working FSB5 (professionally encoded HEVAG) to PCM, then re-encoding with our `fast_pcm_to_hevag()` (which uses `opt_encode_frame()`), the resulting HEVAG produces DIFFERENT PCM output when decoded again.

**Test result: First 100 samples match (decode->encode->decode): FALSE**

- Original first 5 PCM samples: [192, 0, 8032, 224, 0]
- Our re-encoded first 5: [0, 0, 0, 6144, 0]
- Original uses pred=14, 0, 4, 11, 14 across frames
- Our encoder uses pred=0 almost exclusively

## Root Cause
The `opt_encode_frame()` function in `hevag_encoder.py` has a fundamental flaw in its shift calculation:
- It recalculates the `shift` value **for each sample** in the 28-sample frame
- The final shift used for encoding is only the value calculated for the **last sample**
- This means the first 27 samples are encoded with a shift that doesn't match the error calculation

Additionally, the per-frame state tracking between the encoder's optimization pass (`opt_encode_frame`) and the final encoding pass (`_encode_with`) may diverge because `_encode_with` starts from fresh history (`h1`, `h2`) but `opt_encode_frame` used modified history (`hh1`, `hh2`) during its search.

## Symptoms on PS4
- Audio decoder plays 1-2 samples then freezes
- No beatmap objects rendered (game logic hangs on audio decode thread)
- Clean exit (PlayerData saves work, game doesn't crash)
- Reproducible across ALL our HEVAG-encoded bundles (pred-0, 5-pred, with/without metadata changes)

## Why Silence Worked
The silence test (all-zero HEVAG frames: pred=0, shift=0, nibbles=0) got notes moving for 1 second because:
- pred=0 with coeffs (0,0) produces predicted=0 regardless of the coefficient table
- All-zero nibbles means dequant=0, reconstructed=0
- The state doesn't diverge because all values are 0

## Attempted Fixes (none worked)
1. Predictor-0-only encoding (fast_encode_frame)
2. 5-predictor optimized encoding (opt_encode_frame) 
3. 12MB padding to match original .resource size
4. Preserving original AudioClip/audio.gz metadata

## Next Approaches
1. **PCM FSB5** — Set byte 8 of sample header to 0, use raw PCM16 data. Needs investigation of correct format byte.
2. **External encoder** — Find a working PS4 HEVAG encoder (Sony SDK tools, FMOD fsbank, etc.)
3. **FSB5 template patching** — Keep original FSB5 structure, only replace audio data in-place

## Related
- [[fsb5-padding-required]]
- [[ps4-audio-decoder-behavior]]


## Update: The Vorbis Red Herring
- The `fsb5` Python module reported mode=VORBIS (15) for the original FSB5
- This was MISLEADING — on PS4 FMOD, mode=15 means HEVAG, not Vorbis
- The fsb5 module's header struct (`4s 6I 8s 16s 8s` = 60 bytes) does not match
  the PS4 FSB5 field layout at offsets 28-59
- The audio data bytes at offset 1748 confirm HEVAG frame headers (0x5E = pred=14, shift=5)
