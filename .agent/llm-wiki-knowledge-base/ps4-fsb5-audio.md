---
name: ps4-fsb5-audio
description: "Landing page redirecting to the correct audio format documentation"
metadata:
  type: redirect
---

# PS4 FSB5 Audio Format

> ⚠️ **This page is a redirect hub.** The audio replacement landscape:

| Format | Status | Reference |
|--------|--------|-----------|
| **PCM16 (codec=2)** | ✅ **WORKING — use this** | [[ps4-fsb5-pcm16-format]] |
| Vorbis (mode=15) | ❌ Blocked (codebook mismatch) | [[ps4-fsb5-vorbis]] |
| HEVAG (mode=9) | ❌ Blocked (Sony proprietary coefficients) | [[ps4-hevag-fsb5-audio]] |

## Key Facts

- Original PS4 Beat Saber audio: **Vorbis** in FSB5 containers
- Custom replacement: **PCM16** FSB5 (codec=2) — lossless, no padding required
- HEVAG was a dead end (no access to Sony's full 16-predictor coefficient table)

## In the Bundle

| Component | Class | Description |
|-----------|-------|-------------|
| AudioClip (e.g. `StartMeUp`) | 83 | References FSB5 via `m_Resource` |
| CAB-xxx.resource | binary | FSB5 audio data (PCM16 for custom songs) |
| audio.gz (TextAsset) | 49 | Gzip JSON: sample count, frequency, BPM |

### Replacement Pattern
```python
# Replace CAB resource
bf.files['CAB-xxx.resource'] = EndianBinaryReader(fsb5_bytes)
# Update AudioClip
audio_clip['m_Resource']['m_Size'] = len(fsb5_bytes)
audio_clip['m_Length'] = dur_sec
# Update audio.gz metadata
audio_gz['m_Script'] = gzip.compress(json.dumps({...}).encode()).decode('utf-8', 'surrogateescape')
```
