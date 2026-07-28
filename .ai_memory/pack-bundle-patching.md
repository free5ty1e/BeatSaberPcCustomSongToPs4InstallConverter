---
name: pack-bundle-patching
description: "How to patch UnityFS pack bundles for PS4 AFR redirect. Includes LZ4HC requirement, CAB format, UnityPy limitations."
metadata: 
  node_type: memory
  type: reference
  originSessionId: bc573f12-ef2e-43e2-9a5a-f79fefc465a0
---

# Pack Bundle Patching (Rolling Stones Pack)

The Rolling Stones pack bundle (`therollingstones_pack_assets_all_*.bundle`) is a UnityFS-format AssetBundle. It contains a single CAB (SerializedFile) with 81 objects including a BeatmapLevelSO (pathID=2287600824654271910) that stores song metadata and mode preview data.

## State of Approaches

| Approach | Status | Result |
|----------|--------|--------|
| UnityPy `bf.save("original")` | **DEAD** | Produces incompatible CAB (CE-34878-0) |
| UnityPy `cab.save()` + manual bundle | **DEAD** | UnityPy CAB serialization differs from original (+4 bytes) |
| UnityPy `save_typetree()` | **DEAD** | Ignores modifications for BeatmapLevelSO in Unity 2022.3 |
| Byte-level text patching + rebuild (LZ4) | **CRASHED** | LZ4 flag=2 rejected by PS4 (needs LZ4HC flag=3) |
| Byte-level text patching + rebuild (LZ4HC) | **UNTESTED** | Exp 135 just deployed |

## Why UnityPy Approaches Fail

### `cab.save()` produces incompatible CAB
Even with NO modifications, `cab.save()` produces a CAB 4 bytes larger than the original (89184 vs 89180). The PS4 Unity runtime rejects this. The difference is in UnityPy's SerializedFile metadata serialization — alignment padding, type tree format, or externals table differ from the original.

### `save_typetree()` ignores modifications for BeatmapLevelSO
UnityPy's TypeTreeHelper serializer in Unity 2022.3 doesn't properly write back modified tree data for BeatmapLevelSO. Even changing `_songName` from "Start Me Up" to "A" (single char) produced the identical 440-byte blob. The TypeTree serializer is read-only for this object type in this Unity version. See [[unitypy-serialization-limitations]].

## PS4 Bundle Compression Requirements

**CRITICAL:** PS4 UnityFS bundles require LZ4HC (flag=3) for ALL data blocks, not LZ4 (flag=2).

- All 65 blocks in the original bundle use flag=3 (LZ4HC)
- The Python `lz4.block.compress()` defaults to LZ4 (flag=2), which is REJECTED
- Must use: `lz4.block.compress(data, mode='high_compression', compression=9, store_size=False)`
- Per-block flag must be set to 3

See [[ps4-unityfs-compression-requirements]] for details.

## Current Approach: Byte-Level Text Patching + Bundle Rebuild

Since UnityPy serialization is incompatible, use direct byte manipulation:

```python
# 1. Decompress original bundle
# 2. Read CAB from decompressed stream
# 3. Patch text at known offsets in BeatmapLevelSO blob
orig_blob = cab_raw[79920:79920+440]  # BeatmapLevelSO blob is at offset 79920
patched = bytearray(orig_blob)
patched[80:91] = b'Espresso\0\0\0'     # _songName: 11 bytes
patched[100:118] = b'Sabrina Carpenter\0'  # _songAuthorName: 18 bytes
# 4. Rebuild bundle with LZ4HC (flag=3)
# 5. Deploy via redirect
```

### String Positions in 440-byte BeatmapLevelSO Blob
| Field | Offset | Size | Original | New |
|-------|--------|------|----------|-----|
| m_Name | 32 | 21 chars | "StartMeUpBeatmapLevel" | Keep original |
| _songName | 80 | 11 chars | "Start Me Up" | "Espresso\0\0\0" |
| _songAuthorName | 100 | 18 chars | "The Rolling Stones" | "Sabrina Carpenter\0" |

## Bundle Building Requirements (FIXED)
- **Use SEPARATE `f.write()` calls** — concatenated `b'...'+b'...'` causes alignment/padding bugs
- **Use explicit padding** `b'\x00' * ((16 - tell % 16) % 16)` — `while tell%16:` is unreliable after concatenated writes
- **Call `f.flush()`** after header writes to ensure correct file position
- **Use LZ4HC** (mode='high_compression') with per-block flag=3

## v22+ CAB Header Format

For Unity 2022.3 CABs (SerializedFile version 22+):
- Header size: 48 bytes
- Bytes 0x14-0x17: metadata_size (BIG ENDIAN uint32) = 53401
- Bytes 0x1C-0x1F: file_size (BIG ENDIAN uint32) = 89180
- data_offset = align16(48 + metadata_size) = 53456
- Object table entries: pathID(int64 LE) + offset(int64 LE relative to data_offset) + size(int32 LE)

See [[v22plus-cab-header-format]] for details.

## Deployment
1. Place patched bundle in `/data/GoldHEN/AFR/CUSA12878/`
2. Add redirect in `redirects.json`:
   ```json
   "therollingstones_pack_assets_all_<hash>": "rollingstones_pack_patched.bundle"
   ```
3. The plugin uses `strstr` substring matching for redirect lookup

## Quick Build Command
```bash
python3 /workspace/beat_saber_deluxe/tools/build_patched_pack_bundle.py
```
