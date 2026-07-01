---
name: ps4-hevag-fsb5-audio
description: "PS4 Beat Saber audio pipeline: FSB5 containers with HEVAG ADPCM encoding"
metadata:
  type: reference
---

# PS4 Audio Format: FSB5 + HEVAG

The PS4 version of Beat Saber stores audio as **FSB5** (FMOD Sample Bank) containers with **HEVAG** (PS4 ADPCM) encoding. The audio pipeline involves multiple components in the AssetBundle, not just the raw audio bytes.

## Architecture

```
AudioClip (MonoBehaviour)
  └── m_Resource → CAB-xxx.resource (FSB5 file)
       └── Sample 0 → HEVAG ADPCM data
Audio Metadata (TextAsset: StartMeUp.audio.gz)
  └── JSON with songChecksum, songSampleCount, songFrequency, bpmData
```

## FSB5 Container Format

The PS4 FSB5 files use the following structure:

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0 | 4 | magic | "FSB5" |
| 4 | 4 | version | Always 1 for PS4 Beat Saber |
| 8 | 4 | num_samples | Number of audio samples (always 1) |
| 12 | 4 | sample_header_size | Total size of sample headers (900 bytes) |
| 16 | 900 | sample_header | DSP state + metadata (see below) |
| 916 | varies | audio_data | HEVAG-encoded ADPCM data |

### Sample Header (900 bytes)

The 900-byte sample header contains:
- **Bytes 0-3**: Name offset (0 = no name / default)
- **Bytes 4-7**: Audio data size (bytes of HEVAG data)
- **Bytes 8-11**: Offset (0 = start of audio data)
- **Bytes 12-13**: Format code (1 = HEVAG)
- **Bytes 14-31**: Various DSP coefficients and state
- **Bytes 32-899**: Additional DSP tables (reverb, filters, etc.)

The full 900-byte structure is not fully understood. We use a **template approach**: copy the header from an existing working FSB5 and update only the data size field (bytes 4-7).

## HEVAG ADPCM Encoding

HEVAG (PlayStation 4 Adaptive Differential Pulse Code Modulation) is the PS4's native audio compression format, similar to Sony's older VAG format but optimized for PS4.

### Frame Structure

Each HEVAG frame encodes **28 PCM16 samples** into **16 bytes** (3.5:1 compression):

| Bytes | Contents |
|-------|----------|
| 0-1 | Frame header: predictor (bits 0-3) + shift (bits 4-6) + flags (bits 7-15) |
| 2-15 | 28 ADPCM nibbles (4-bit signed values, 2 per byte) |

### Predictor Coefficients

Five coefficient sets are used for adaptive prediction:

| Index | c1 | c2 | Description |
|-------|----|----|-------------|
| 0 | 0 | 0 | Flat / no prediction |
| 1 | 60 | 0 | First-order prediction |
| 2 | 115 | -52 | Second-order prediction |
| 3 | 98 | -55 | Second-order prediction |
| 4 | 122 | -60 | Second-order prediction |

### Encoder Algorithm

The encoder finds the optimal predictor + shift for each 28-sample block by minimizing reconstruction error:

1. For each predictor (0-4) and shift (0-12):
   - Predict each sample: `predicted = ((h1 * c1 + h2 * c2) + 32) >> 6`
   - Calculate difference: `diff = sample - predicted`
   - Quantize to 4-bit nibble
   - Accumulate squared error
2. Select predictor+shift with lowest total error
3. Encode all 28 samples using the best configuration

## Unity AssetBundle Resource Handling

The FSB5 audio data lives in the AssetBundle as a **CAB-xxx.resource** file — a raw binary blob accessible through UnityPy. Key steps for audio replacement:

1. **Replace resource data**: Swap the CAB-xxx.resource bytes with a new FSB5 file containing custom audio
2. **Update AudioClip metadata**: Modify `m_Resource.m_Size`, `m_Length`, and `m_Frequency` on the AudioClip object
3. **Update audio.gz**: Regenerate the JSON metadata TextAsset with correct sample count, frequency, and BPM data

```python
# Audio replacement pattern
from UnityPy.streams import EndianBinaryReader
import gzip, json

# Create new FSB5
fsb5_bytes = build_fsb5(hevag_data, sample_rate, channels)

# Replace resource
new_res = EndianBinaryReader(fsb5_bytes)
new_res.flags = 0
bf.files['CAB-xxx.resource'] = new_res

# Update AudioClip
audio_clip['m_Resource']['m_Size'] = len(fsb5_bytes)
audio_clip['m_Length'] = duration_sec

# Update audio.gz
audio_meta = json.dumps({"version":"4.0.0","songSampleCount":count,...})
audio_gz['m_Script'] = gzip.compress(audio_meta.encode()).decode('utf-8', 'surrogateescape')
```

## Tool: hevag_encoder.py

Located at `beat_saber_deluxe/tools/hevag_encoder.py`

```bash
# Generate test tone
python3 hevag_encoder.py --generate-tone --duration 3 -o audio.fsb5

# Convert WAV to FSB5
python3 hevag_encoder.py -i song.wav -o audio.fsb5

# Info about existing FSB5
python3 hevag_encoder.py --info -i existing.fsb5
```

The tool can be imported as a Python module:
```python
from hevag_encoder import pcm_to_hevag, build_fsb5, generate_test_tone_pcm
```

## Known Limitations

- The 900-byte FSB5 sample header is **copied from a template** (an existing game FSB5). We only modify the data size field. The exact header structure is undocumented.
- HEVAG encoding is **computationally expensive** due to the brute-force search over 5 predictors × 13 shifts per frame. For real-time conversion of full-length songs, optimization may be needed.
- Only **PCM16 WAV** input is supported. Other formats must be converted first (e.g., with FFmpeg).

## Related
- [[ps4-environment-system]] — How songs are mapped to environments (separate from audio)
- [[beatmap-conversion-pipeline]] — The full custom song conversion pipeline
