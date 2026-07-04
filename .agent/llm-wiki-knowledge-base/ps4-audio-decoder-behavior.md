---
name: ps4-audio-decoder-behavior
description: "Root cause analysis of audio-related freezes on PS4 Beat Saber"
metadata:
  type: reference
---

# PS4 Audio Decoder Behavior

## The "Silence Freeze" Phenomenon
Tests with a correctly formed FSB5 containing either all-zero frames (silence) or simplified HEVAG encoding (predictors 0-4) resulted in a hard freeze of the game logic after ~1 second of playback.

## Root Cause
The PS4's hardware HEVAG decoder is highly sensitive to encoding patterns. Analysis of original FSB5 files reveals that they use the **full 4-bit range** for both predictor indices (0-15) and shift values (0-15).

Our simplified encoder produced a limited subset of these parameters, which caused the decoder to enter an error state or hang after a short period of processing.

## Key Findings
- **Structure is Valid:** A bundle containing original audio but custom beatmaps works perfectly. This proves that the AssetBundle structure, the `.resource` file placement, and the `AudioClip` metadata (m_Resource.m_Size, m_Length) are all correct.
- **Data Fidelity Matters:** The PS4 decoder does not just need valid FSB5 format; it needs audio data encoded with high-fidelity parameters (utilizing the full coefficient table).
- **Symptom:** A freeze at ~1 second indicates the decoder processed the initial buffer but failed upon reaching a specific state or boundary.

## Implementation Guide
To replace audio without freezing:
1. Use a professional HEVAG encoder (like FMOD's `fsbank`) or a tool that supports the full 16-predictor coefficient set.
2. Ensure the audio data matches the `m_Resource.m_Size` declared in the `AudioClip`.
3. Update `audio.gz` metadata to match the new audio's duration and sample count.

[[ps4-hevag-fsb5-audio]]
[[experiment-78]]
