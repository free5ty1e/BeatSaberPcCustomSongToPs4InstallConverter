---
name: ps4-hevag-fsb5-audio
description: "⚠️ BLOCKED — HEVAG (PS4 ADPCM) is not usable. PCM16 is the working approach."
metadata:
  type: reference
  status: blocked
---

# ⚠️ BLOCKED: PS4 Audio Format: FSB5 + HEVAG

## HEVAG is NOT Usable for Custom Audio

HEVAG (PS4's native ADPCM format used in the original game FSB5 files) cannot be encoded by our toolchain. **Use PCM16 (codec=2) instead** — see [[ps4-fsb5-pcm16-format]].

## Why HEVAG is Blocked

Sony's professional HEVAG encoder uses a **proprietary coefficient table with 16 predictors** (indices 0-15). Our encoder only implements predictors 0-4 (the standard 5-coefficient set):

| Source | Predictors | Result |
|--------|-----------|--------|
| Original PS4 FSB5 | 0-15 (uses 14, 4, 11, etc.) | Works |
| Our encoder | 0-4 only | Freezes after ~1s |

Predictors 5-15 are Sony-proprietary with no publicly documented coefficient values. Without the full coefficient table, the PS4 hardware decoder enters an error state.

See [[encoder-decoder-inconsistency]] for the detailed analysis.

## What This Page Used To Document

Previously, this page documented:
- HEVAG frame structure (28 samples → 16 bytes, 3.5:1 compression)
- 5-predictor encoder algorithm (opt_encode_frame)
- FSB5 container structure with sample_header_size=1732
- Encoder optimizations (silence fast path, early termination)

The **FSB5 container structure** information (sample_header_size=1732, header template matching) is still valid but applies to PCM16 FSB5 as well. See [[ps4-fsb5-pcm16-format]] for the working PCM16 FSB5 layout.

## Related

- [[ps4-fsb5-pcm16-format]] — **WORKING** audio format (PCM16, codec=2)
- [[encoder-decoder-inconsistency]] — Detail on why HEVAG fails
- [[fsb5-padding-required]] — Historical note (padding was a HEVAG-era artifact)
- [[ps4-fsb5-vorbis]] — Vorbis FSB5 (also blocked, codebook mismatch)
