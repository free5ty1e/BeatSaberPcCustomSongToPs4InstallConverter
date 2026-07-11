---
name: alpha-release-pcm16
description: "Beat Saber Deluxe v0.50 Alpha — PCM16 FSB5 custom song pipeline confirmed working on PS4"
metadata:
  type: project
---

# Beat Saber Deluxe v0.50 Alpha

The first working custom song replacement pipeline for Beat Saber on PS4.
Uses PCM16 FSB5 (codec=2) for lossless audio. Bit-identical round-trip verified.

## Key facts
- PCM16 FSB5 from scratch (no template) — codec=2, sample_header_size=65, 44-byte alignment
- PS4 FMOD accepts PCM16 FSB5 natively
- 12MB resource cap limits audio to ~70 seconds at 44100Hz stereo
- HEVAG encoder produces incorrect decoded output (160% NRMSE)
- Vorbis codebook mismatch between libvorbis and FMOD lookup table

## Working commands
python3 tools/full_custom_song_pipeline.py --song-dir <dir> --pcm16 --target startmeup --deploy

## Why this approach won
- No FMOD-specific encoding needed (unlike Vorbis)
- No codebooks or setup tables (unlike HEVAG testing issues)
- Simple from-scratch FSB5 builder avoids template zeroing bugs
- Bit-identical round-trip verifiable with vgmstream

**Why:** PCM16 is the only format that produced correct audio on PS4.
**How to apply:** Always use --pcm16 for new deployments. Avoid --vorbis and HEVAG until codebook issues are resolved.
