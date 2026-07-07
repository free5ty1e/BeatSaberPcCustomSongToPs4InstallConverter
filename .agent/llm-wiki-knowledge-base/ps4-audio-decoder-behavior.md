---
name: ps4-audio-decoder-behavior
description: "PS4 audio decoder behavior analysis — resolved by PCM16 migration"
metadata:
  type: reference
---

# PS4 Audio Decoder Behavior

## The "Silence Freeze" Phenomenon (HISTORICAL)

During HEVAG experiments, FSB5 files containing correctly-formed HEVAG with simplified encoding (predictors 0-4 only) caused a hard freeze ~1 second into playback. This was the primary symptom that led us on a long debugging path.

## Root Cause

The freeze was caused by HEVAG encoding with an **incomplete predictor coefficient set**. The PS4 hardware HEVAG decoder expects 16 predictors (0-15), and our encoder only supplied 5 (0-4). Predictors 5-15 use Sony-proprietary coefficients that we don't have access to.

This was a **codec-level issue** — not a file size, padding, or metadata issue.

## ✅ The Real Solution: PCM16

Switching from HEVAG to **PCM16 (codec=2)** completely bypasses the decoder issue:

| Approach | Result | Why |
|----------|--------|-----|
| HEVAG with 5 predictors | ❌ Freeze at ~1s | Missing predictors 5-15 |
| HEVAG with all-zero frames | ⚠️ Notes moved 1s then froze | No real audio content |
| Vorbis replacement | ❌ First 1/8s then silence | Codebook mismatch |
| **PCM16 (codec=2)** | ✅ **Full song plays** | Lossless, no codec dependency |

## Key Findings That Still Apply

- **Structure is Valid:** A bundle containing original audio but custom beatmaps works perfectly. AssetBundle structure, `.resource` file placement, AudioClip metadata (`m_Resource.m_Size`, `m_Length`) are all correct.
- **The game does not need padding.** PCM16 with `--no-pad` works at any file size.

## Correct Implementation Guide

To replace audio on PS4 Beat Saber:

1. **Use PCM16 FSB5 (codec=2)** — build from scratch with `build_pcm16_fsb5()` in `hevag_encoder.py`
2. **Normalize audio** — read as float32, scale peak to 0.99, convert to int16 (prevents OGG encoder overshoot crackling)
3. **Use `--no-pad` for long songs** — PCM16 has no size limit
4. Update `AudioClip.m_Resource.m_Size` to match the new FSB5 size
5. Update `audio.gz` metadata with correct sample count and duration

See [[ps4-fsb5-pcm16-format]] for the full working pipeline.
