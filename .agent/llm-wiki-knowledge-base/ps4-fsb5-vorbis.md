---
name: ps4-fsb5-vorbis
description: "Original PS4 Beat Saber audio uses VORBIS FSB5, but PCM16 is the working replacement format"
metadata:
  type: reference
---

# PS4 FSB5 Vorbis Format

## Summary

The **original** PS4 Beat Saber audio uses Vorbis (mode=15) in FSB5 containers. However, custom audio replacement uses **PCM16 (codec=2, lossless)** which is simpler and works perfectly. Vorbis replacement is blocked due to codebook mismatch.

| Format | Status | Reason |
|--------|--------|--------|
| **PCM16 (codec=2)** | ✅ **WORKS** | Lossless, no codebooks, any size | 
| Vorbis (mode=15) | ❌ Blocked | FMOD/libvorbis codebook incompatibility |
| HEVAG (mode=9) | ❌ Blocked | Sony proprietary coefficients (predictors 5-15) |

**Use [[ps4-fsb5-pcm16-format]] for custom audio.**

## Original FSB5 Vorbis Discovery (Exp 86)

The `fsb5` Python module parsed the original Start Me Up FSB5 and reported:
- `mode=SoundFormat.VORBIS (15)`
- Metadata chunk type: `VORBISDATA`
- Sample PCM frames: 9,425,916 (213.7s at 44100Hz)

This was surprising — we'd assumed HEVAG. The original game uses Vorbis, not HEVAG.

## Vorbis FSB5 Structure (Original Game)

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
Offset 0x44+: Metadata chunks (VORBISDATA with CRC32 + header data)
Offset 0x6D4 (1748): OGG Vorbis audio data
```

## Why Vorbis Replacement is Blocked

The FSB5 Vorbis format stores only a **CRC32 (setup_id)** of the Vorbis setup header, not the header itself. The decoder looks up the setup packet (codebooks) from a pre-compiled table using this CRC32. If the audio was encoded with different codebooks (e.g., libvorbis vs FMOD fsbank), the decoder fails after decoding 1-2 packets.

**Experiment 90**: First ~1/8 second decoded correctly, then failed — confirming codebook mismatch between libvorbis-encoded audio and FMOD's built-in codebook table.

Potential solution: Use FMOD's `fsbank` tool, but this requires a paid license.

## PCM16 FSB5 Success (Exp 92+)

See [[ps4-fsb5-pcm16-format]] for the working PCM16 approach:
- FSB5 codec=2 = PCM16LE, interleaved
- Build from scratch with sample_header_size=65
- 44 bytes alignment padding between header and PCM data
- Metadata chunks: CHANNELS + FREQUENCY (not VORBISDATA)
- Bit-identical round-trip verified via vgmstream
- PS4 FMOD accepts without issues
