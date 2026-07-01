---
name: ps4-fsb5-audio
description: "PS4 FSB5 audio format for Beat Saber song audio, structure and replacement approach"
metadata:
  type: reference
---

# PS4 FSB5 Audio Format (Legacy Reference)

> **⚠️ This page is superseded.** Audio replacement IS implemented. See the authoritative page: [[ps4-hevag-fsb5-audio]]

## Quick Summary

The PS4 version of Beat Saber stores audio in **FSB5 containers** with **HEVAG ADPCM** encoding.

### Components in the Bundle

| Component | Class | Description |
|-----------|-------|-------------|
| AudioClip (e.g. `StartMeUp`) | 83 | References the FSB5 audio data via `m_Resource` |
| CAB-xxx.resource | binary blob | Raw FSB5 file containing HEVAG-encoded audio |
| audio.gz (TextAsset) | 49 | Gzip-compressed JSON with song metadata |

### Audio Replacement Pipeline

```python
# 1. Encode PCM to HEVAG
hevag = pcm_to_hevag(pcm_data, channels=2)

# 2. Wrap in FSB5 container (uses song-specific header template)
fsb5 = build_fsb5(hevag, sample_rate=44100)

# 3. Replace CAB resource in bundle
new_res = EndianBinaryReader(fsb5)
bf.files['CAB-xxx.resource'] = new_res

# 4. Update AudioClip
audio_clip['m_Resource']['m_Size'] = len(fsb5)
audio_clip['m_Length'] = dur_sec

# 5. Update audio.gz metadata
audio_gz['m_Script'] = gzip.compress(json.dumps({...}).encode())
```

### ⚠️ Critical: Header Template Must Match the Song

The 900-byte FSB5 sample header contains **song-specific DSP coefficients**. Using a header from a different song causes the game to **freeze/hang** when audio starts playing. Always use the header from the SAME song the bundle is based on.

### Tool

```bash
python3 beat_saber_deluxe/tools/hevag_encoder.py --generate-tone --duration 3 -o audio.fsb5
python3 beat_saber_deluxe/tools/hevag_encoder.py -i song.wav -o audio.fsb5
```

See [[ps4-hevag-fsb5-audio]] for full documentation.
