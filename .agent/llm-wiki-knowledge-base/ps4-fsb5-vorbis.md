---
name: ps4-fsb5-vorbis
description: "PS4 Beat Saber uses VORBIS audio in FSB5 containers, not HEVAG"
metadata:
  type: reference
---

# PS4 FSB5 Audio Format: VORBIS (not HEVAG)

## Critical Discovery (Exp 86 — 2026-07-04)
The original Start Me Up FSB5 file uses **SoundFormat.VORBIS (mode=15)**, NOT HEVAG (mode=9).

This was discovered using the `fsb5` Python module (`pip install fsb5`), which successfully parsed the original FSB5 and revealed:
- `mode=SoundFormat.VORBIS (15)` 
- Metadata chunk type: `VORBISDATA`
- Sample PCM frames: 9,425,916 (213.7s at 44100Hz)

## Impact on Audio Replacement
All previous tests were misguided because they assumed HEVAG format:
- Our HEVAG encoder (pred-0, 5-pred) produced data in the wrong format
- The PCM test (byte 8 = 0) used an incorrect format code
- The correct approach is to replace the VORBIS audio data within the FSBS container

## FSB5 Structure for VORBIS
```
Offset 0x00: "FSB5" magic (4 bytes)
Offset 0x04: Version (1, uint32)
Offset 0x08: Num samples (1, uint32)
Offset 0x0C: Sample header size (1732, uint32)
Offset 0x10: Name table size (0, uint32)
Offset 0x14: Data size (OGG size, uint32)
Offset 0x18: Mode (15 = VORBIS, uint32)
...
Offset 0x3C: Sample descriptor (64-bit packed)
  Bit 0: next_chunk flag
  Bits 1-4: frequency index (8=44100Hz)
  Bit 5: channels (-1, 1=stereo)
  Bits 6-33: dataOffset (in 16-byte units)
  Bits 34-63: PCM sample count
Offset 0x44+: Metadata chunks (VORBISDATA chunk with CRC32 + header data)
Offset 0x6D4 (1748): OGG Vorbis audio data
```

## How to Create a Custom Vorbis FSB5
1. Read original FSB5 header through audio offset (16 + sampleHeaderSize = 1748)
2. Encode custom WAV to OGG Vorbis using `soundfile.write(buf, data, sr, format='OGG', subtype='VORBIS')`
3. Copy header bytes 0-1747 from original
4. Update data_size at offset 20 (uint32) to OGG size
5. Keep mode at offset 24 = 15 (VORBIS)
6. Update sample count in descriptor at offset 60 (bits 34-63)
7. Append OGG data
8. Pad to 12,305,632 bytes with zeros

## Decoded PCM WAV
Original Start Me Up audio decoded from FSB5 → PCM16:
- File: `/workspace/beat_saber_deluxe/custom_songs/startmeup_decoded_30s.wav`
- 30 seconds, stereo, 44100Hz, 864KB
- Created by decoding HEVAG frames using the encoder's decode function

## Related
- [[encoder-decoder-inconsistency]]
- [[fsb5-padding-required]]
- [[ps4-audio-decoder-behavior]]
