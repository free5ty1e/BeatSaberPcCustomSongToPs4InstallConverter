---
name: ps4-unityfs-compression-requirements
description: PS4 Beat Saber requires LZ4HC (flag=3) for all UnityFS blocks. LZ4 (flag=2) causes CE-34878-0.
metadata: 
  node_type: memory
  type: reference
  originSessionId: bc573f12-ef2e-43e2-9a5a-f79fefc465a0
---

# PS4 UnityFS Compression Requirements

The PS4 version of Beat Saber (Unity 2022.3) requires ALL data blocks in UnityFS bundles to use **LZ4HC** compression with **flag=3**. Using LZ4 (flag=2) causes CE-34878-0 crash at startup.

## Evidence
- All 65 blocks in the original Rolling Stones pack bundle use flag=3 (LZ4HC)
- Every rebuilt bundle using LZ4 flag=2 crashes immediately at startup (Exp 134b, Exp 132, Exp 127)
- UnityPy can READ flag=2 blocks correctly (same LZ4 decompression), but the PS4 game engine rejects them

## Python Implementation
```python
import lz4.block

# WRONG — produces LZ4 (flag=2), rejected by PS4:
comp = lz4.block.compress(data, store_size=False)

# CORRECT — produces LZ4HC (flag=3), accepted by PS4:
comp = lz4.block.compress(data, mode='high_compression', compression=9, store_size=False)
```

## Per-Block Flags
When building the blocks info in a UnityFS bundle, set per-block flags:
```python
# For LZ4HC blocks:
(block_decompressed_size, block_compressed_size, 3)
```

The original bundle uses:
- Per-block flag: 3 (LZ4HC)
- Bundle `data_flags`: 0x0243 (LZ4HC for blocks info, BlockInfoNeedPaddingAtStart)
- Blocks info compression: uses the bundle's data_flags & 0x3F value

## Decompression (Both flags work)
The LZ4 decompression algorithm is identical regardless of whether the data was compressed with LZ4 or LZ4HC:
```python
# Works for both flag=2 and flag=3:
decomp = lz4.block.decompress(compressed_data, uncompressed_size=N)
```

The PS4's Unity runtime likely checks the flag value against an allowed list and rejects anything other than 3 for LZ4 blocks.

## Bundle Size Comparison
| Compression | Bundle Size | Blocks Info | Per-Block Flag | PS4 Result |
|-------------|-------------|-------------|----------------|------------|
| Original (LZ4HC) | 7,902,803 | 199 bytes | 3 (LZ4HC) | ✅ Works |
| Rebuilt (LZ4) | 8,022,936 | 213 bytes | 2 (LZ4) | ❌ Crash |
| Rebuilt (LZ4HC) | 7,905,246 | 198 bytes | 3 (LZ4HC) | ⏳ Untested |

See [[pack-bundle-patching]] for the full patching approach.
