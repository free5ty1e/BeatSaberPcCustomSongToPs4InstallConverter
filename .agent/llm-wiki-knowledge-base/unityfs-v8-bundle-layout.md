---
name: unityfs-v8-bundle-layout
description: "Exact offset map of UnityFS v8 bundle format used by PS4 Beat Saber — header, blocks info, raw block data, compressed vs uncompressed blocks"
metadata:
  type: reference
---

# UnityFS v8 Bundle Layout (PS4 Beat Saber)

**Unity version:** 2022.3.33f1
**Bundle format version:** 8 (UnityFS magic `UnityFS\0`, major version field at offset 7 = 0x08)
**Source bundle:** `therollingstones_pack_assets_all_a99482a8a3da9e991e5ae36f2fea209c.bundle` (7,902,803 bytes)

## Complete Offset Map

```
Offset  Range        Size       Content
─────── ──────────── ────────── ─────────────────────────────────────
0x00    0-49          50         Header
                                                        Magic: "UnityFS\0" (7 bytes)
                                                        Version major: uint32 BE at offset 7
                                                        Unity version string + null at offset 11
                                                        file_size: uint64 BE at offset 30 (= 7,902,803)
                                                        Flags: uint32 BE at offset 46 (0x243 = BlocksAndDirectoryInfoCombined + LZ4HC)

0x50    50-63         14         Alignment padding (all zeros)

0x64    64-262        199        Blocks info — COMPRESSED
                                                        Contains: block count, per-block specs, object table
                                                        Decompressed size: 859 bytes
                                                        LZ4HC compressed (flag in blocks_info = 3)

0xFF   263+           variable   Raw block data (uncompressed stream)
                                                        First block starts at offset 263
                                                        Blocks are stored sequentially — no gaps between them
```

## Block Specs (from decompressed blocks info)

The decompressed blocks info contains:
1. **Block count** (uint32 BE at offset 0 of decompressed stream) = 65
2. **Per-block specs** (12 bytes each): `decompressed_size(4) + compressed_size(4) + flags(2)`
   - Flag bit 1 (value 2): set = LZ4HC compressed, clear = uncompressed (raw copy)
3. **Object table count** (int32 LE) followed by variable-length entries

### Block Distribution
| Type | Count | Per-block decompressed size | Total decompressed | Stored as |
|------|-------|---------------------------|-------------------|-----------|
| LZ4HC compressed (flag=3) | 16 | varies (25K-131K) | ~8.5MB total | Compressed bytes in raw data |
| Uncompressed (flag=0) | 49 | 131,072 (fixed) | 6,422,528 bytes | Raw copy — stored as-is in file |

### Block Layout in File

```
Offset Range          Content                              Size
───────────────────── ──────────────────────────────────── ─────────────
263 - ~1,488,718      16 LZ4HC compressed blocks           ~1,488,455 bytes (compressed)
~1,488,719 - end     49 uncompressed blocks               6,422,528 bytes (raw)
```

**Critical finding:** Blocks 16-62 are ALL uncompressed. They contribute their FULL decompressed size directly to the file — no compression applied because LZ4HC cannot compress them (ratio >100%, would expand).

## Key Implications for Pack Bundle Modification

### Why CRC Correction Was Partially Successful (Exp 142)
- The 9 alignment padding bytes used for CRC correction were in an uncompressed region → their contribution to CRC is **linear and predictable** over GF(2)
- CRC matched `0xdc8b314f` exactly using GF(2) linear algebra
- But file_size changed by +2,712 bytes due to alignment shifts when injecting larger BeatmapLevelSO blob

### Size + CRC Co-Solver Problem (Priority A — In Progress)
The 49 uncompressed blocks provide massive degrees of freedom:
- Each contributes exactly 131,072 bytes to file_size AND its raw content contributes linearly to CRC
- If we could compress some of these blocks, we'd shrink file_size while keeping CRC controllable
- **But LZ4HC cannot compress them** (ratio >100%) — they were stored uncompressed by the original author because compression would make them larger

### The Fundamental Constraint
```
Original bundle: 7,902,803 bytes total
Modified bundle (Exp 142): 7,905,515 bytes (+2,712) — CRC matched but size wrong
Target: match BOTH file_size AND CRC simultaneously

If all uncompressed blocks stay uncompressed: ~7,911,246 bytes (8,443 over target)
LZ4HC can't compress them further → no way to shrink without changing block flags
Changing flag from 0→3 would require recompression which changes both size AND CRC unpredictably
```

### Available Free Bytes for CRC Control
| Region | Location | Size | Notes |
|--------|----------|------|-------|
| Alignment padding (header→blocks_info) | offset 50-63 | 14 bytes | All zeros, contributes to CRC linearly |
| Uncompressed blocks (flag=0) | offset ~1.5M+ | 6.4MB | Raw data, full control over content AND size |
| Alignment between compressed/uncompressed boundary | varies | small | May have padding at block boundaries |

## Decompression Verification

To verify the bundle structure:
```python
import lz4.block

# Read blocks info (199 bytes of LZ4HC-compressed data starting at offset 64)
with open(bundle_path, 'rb') as f:
    buf = f.read()

blocks_info_comp = buf[64:263]  # 199 bytes compressed
blocks_info = lz4.block.decompress(blocks_info_comp, uncompressed_size=859)

# Parse block specs from decompressed stream
r = 0
block_count = struct.unpack('>I', blocks_info[r:r+4])[0]; r += 4
for i in range(block_count):
    decomp_sz = struct.unpack('>I', blocks_info[r:r+4])[0]; r += 4
    comp_sz = struct.unpack('>I', blocks_info[r:r+4])[0]; r += 4
    flags = struct.unpack('>H', blocks_info[r:r+2])[0]; r += 2
    is_compressed = bool(flags & 2)
```

## Related Pages
- [[pack-bundle-patching]] — CRC blocking problem and all approach results
- [[v22plus-cab-header-format]] — CAB (SerializedFile v22+) internal format
- [[unitypy-serialization]] — UnityPy limitations for PS4 bundle manipulation
- [[song-metadata-addressables-structure]] — How metadata is stored in pack bundles
