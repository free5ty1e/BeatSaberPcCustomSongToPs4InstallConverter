# PS4 FSB5 PCM16 Format

## Overview
PCM16 (codec=2) in FSB5 format is the recommended approach for custom audio on PS4.
Lossless, bit-identical round-trip, no codebook issues.

## FSB5 Layout (PCM16)
| Offset | Size | Field | Value |
|--------|------|-------|-------|
| 0x00 | 4 | Magic | "FSB5" |
| 0x04 | 4 | Version | 1 |
| 0x08 | 4 | NumSamples | 1 |
| 0x0C | 4 | SampleHeaderSize | 65 (0x41) |
| 0x10 | 4 | NameTableSize | 0 |
| 0x14 | 4 | DataSize | PCM16 data size |
| 0x18 | 4 | Codec | 2 (PCM16) |
| 0x1C | 4 | Field1 | 1 |
| 0x20 | 4 | Flags | 0 |
| 0x24 | 16 | Hash | zeros |
| 0x34 | 8 | Dummy | zeros |
| 0x3C | 8 | SampleDescriptor | see below |
| 0x44 | 4 | CHANNELS chunk | type=1, next=1, size=1 |
| 0x48 | 1 | Channels | 2 |
| 0x49 | 4 | FREQUENCY chunk | type=2, next=0, size=4 |
| 0x4D | 4 | SampleRate | 44100 |
| 0x51 | 44 | Alignment padding | zeros |
| 0x7D | N | PCM16 data | interleaved L,R |

## Sample Descriptor (64-bit)
- bit 0: next_chunk (1 = metadata follows)
- bits 1-4: freq_idx (8 = 44100Hz)
- bit 5: channels (1 = stereo, stored as ch-1)
- bits 6-33: dataOffset (0 for single sample)
- bits 34-63: samples (PCM frame count)

## vgmstream Quirk
vgmstream uses `base_header_size = 60` for version 1 FSB5.
Audio offset = base_header_size + sampleHeaderSize = 60 + 65 = 125.
The actual header body ends at offset 81, requiring 44 bytes of alignment padding.


## Lapped-up Beatmaps and Audio
Lapped-up beatmaps are a modded feature where certain sections of the song are repeated.
In the beatmap JSON, this is indicated by lapped-up metadata in `_customData` (e.g., `_laps` array).
The official PS4 game does NOT support this natively. To sync lapped-up beatmaps with audio on PS4,
the audio file must be manually edited (lapped-up) to repeat the corresponding sections,
so that the audio duration matches the lapped-up beatmap duration.
