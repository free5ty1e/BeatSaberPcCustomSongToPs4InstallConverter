---
name: encoder-decoder-inconsistency
description: "HISTORICAL — HEVAG encoder/decoder inconsistency analysis. Resolved — PCM16 works."
metadata:
  type: reference
  status: historical
---

# HEVAG Encoder/Decoder Inconsistency (HISTORICAL)

> ⚠️ **This issue is resolved.** HEVAG has been abandoned in favor of PCM16 (codec=2), which works perfectly. This page is kept for historical reference.

## The Problem (HEVAG Era)
When decoding the original working FSB5 (professionally encoded HEVAG) to PCM, then re-encoding with our `fast_pcm_to_hevag()` using `opt_encode_frame()`, the resulting HEVAG produced DIFFERENT PCM output when decoded again.

**Original first 5 PCM samples:** [192, 0, 8032, 224, 0]
**Our re-encoded first 5:** [0, 0, 0, 6144, 0]

Original used predictors 14, 0, 4, 11, 14 across frames; our encoder used pred=0 almost exclusively.

## Root Cause: Missing Sony Coefficients

The core issue wasn't our encoder implementation per se — it was the **incomplete predictor coefficient table**. Sony's professional HEVAG encoder uses 16 predictors (0-15), with predictors 5-15 using proprietary coefficients that were never publicly documented.

Our encoder's 5-predictor set (0-4) could never produce matching output.

## Why Silence Worked
All-zero HEVAG frames (pred=0, shift=0, nibbles=0) produced matching decode output because pred=0 with coefficients (0,0) always produces predicted=0 regardless.

## Resolution: PCM16 FSB5

The fix was to abandon HEVAG entirely and use **PCM16 (codec=2)** FSB5:

- No codec dependency — raw PCM16 samples stored directly in FSB5
- Bit-identical round-trip verified with vgmstream
- PS4 FMOD decoder accepts without any issues
- No codebooks, no coefficient tables, no compression artifacts
- Works at any file size (`--no-pad`)

## What Was Attempted (HEVAG Fixes, None Worked)

1. Predictor-0-only encoding (fast_encode_frame)
2. 5-predictor optimized encoding (opt_encode_frame)
3. 12MB padding to match original .resource size
4. Preserving original AudioClip/audio.gz metadata

All failed because the PS4 decoder requires the full 16-predictor coefficient set.

## Related

- [[ps4-fsb5-pcm16-format]] — **The working solution**
- [[ps4-hevag-fsb5-audio]] — HEVAG is blocked
- [[fsb5-padding-required]] — Historical note (padding was a HEVAG-era artifact)
- [[ps4-audio-decoder-behavior]] — Decoder freeze analysis
