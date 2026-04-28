# DLC Package Internal Format Analysis — 2026-04-24

## Source Files Examined
- `CUSA12878_Darude-Sandstorm.pkg` (1,048,576 bytes)
- `CUSA12878_Imagine.Dragons-Believer.pkg` (1,048,576 bytes)

## DLC Package Structure Overview

Each DLC song package (1 MB fixed size) contains these internal files:

| File ID | Size | Encrypted | Description |
|---------|------|----------|-------------|
| 0x0001 | 352 bytes | No | License/rights metadata (all zeros) |
| 0x0010 | 2,048 bytes | No | Encrypted content body (audio? beatmap?) — looks like random data |
| 0x0020 | 256 bytes | **Yes** | Encrypted header block |
| 0x0080 | 384 bytes | No | Config/file table header (`d2560100` magic) |
| 0x0100 | 352 bytes | No | **Main manifest** — describes all internal files |
| 0x0200 | 21 bytes | No | File reference table: `param.sfo\0icon0.png\0` |
| 0x0400 | 1,024 bytes | **Yes** | Encrypted block A |
| 0x0401 | 512 bytes | **Yes** | Encrypted block B |
| 0x0409 | 8,192 bytes | No | Spare/alignment (zeros) |
| 0x1000 | 972 bytes | No | `PARAM.SFO` — PS4-style metadata |
| 0x1200 | 290,247 bytes | No | **Cover PNG** (289 KB) |

## Key File: 0x0100 — Main Manifest (352 bytes)

This manifest describes the internal file layout. It appears to be a custom Opoisso893 format.

**Layout interpretation (Believer):**
```
struct DLCManifestEntry {
    uint32_t file_id;       // 0x0001, 0x0010, etc.
    uint32_t flags_offset;  // combined flags + data offset or size
}
```

The 352-byte manifest contains 22 entries (one per file ID), each 16 bytes describing:
- File ID (1-1033 range, not sequential)
- Offset/size values for each internal file
- Encrypted flag encoded in high bit of offset fields

## Key File: 0x0200 — File Reference Table (21 bytes)

```
00 param.sfo 00 icon0.png 00
```

This is a null-separated list of files the DLC provides: `param.sfo` and `icon0.png`. No audio file reference — confirming audio lives in the main game package, not the DLC.

## Key File: 0x1000 — PARAM.SFO (972 bytes)

Standard PS4 PARAM.SFO format but slightly modified:
- Magic: `\0PSF` (null-prefixed)
- Version: `0x00000101`
- Contains 972 bytes of song metadata

Note: Standard PSF parsers may fail due to the null byte prefix. The entry count in this PARAM.SFO appears to be very large (150M) when parsed with standard tools, suggesting a different internal format or padding.

## Key File: 0x1200 — Cover PNG

PNG image file, 290-301 KB per song. Standard cover art (square JPG/PNG like PC format).

## Key File: 0x0010 — Body Area (2,048 bytes, Unencrypted)

Contains what looks like encrypted/binary data. First bytes: `ef 4a 2d 2a 7f 80 55 18...`. This could be:
1. Compressed audio data (Ogg/Vorbis in a custom container)
2. Unity serialized beatmap metadata
3. Some other game asset format

The body is **NOT encrypted** in the DLC packages (unlike in the main game where many files are encrypted with NPDRM).

## Encrypted Blocks: 0x0400 (1,024 bytes) + 0x0401 (512 bytes)

Both blocks are encrypted with the PS4 NPDRM keys. Without a jailbroken PS4, these cannot be decrypted in the container. They likely contain:
- Audio data fragments
- Beatmap data references
- Song configuration

## Critical Insight: DLC Audio Lives in Main Game Package

The DLC packages **do NOT contain audio data** directly. They only provide:
1. Cover art (PNG)
2. Metadata (PARAM.SFO / manifest)
3. Presumably encrypted references to audio assets in the main game `sharedassets` files

This means a custom song conversion pipeline for PS4 must:
1. Find the matching audio slot in the main game's `sharedassets` files
2. Understand how the main game references DLC audio
3. Replace audio in the main game, or understand the DLC-to-main-game linking mechanism

## Next Steps

1. **Extract and examine actual `sharedassets` from the main game** (v1.79 or v2.04 full game PKG)
2. **Find how DLC audio is referenced** — likely a content ID table or audio asset index in the main game's data files
3. **Compare DLC body data (0x0010)** with actual audio from the main game to find the audio format
4. **Understand the manifest format** better — possibly similar to PlayStation EDAT/savedata formats