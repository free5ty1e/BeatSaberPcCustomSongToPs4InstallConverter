---
name: pack-bundle-patching
description: "Pack bundle modification attempts and why all approaches are blocked by Addressables catalog CRC validation"
metadata:
  type: reference
---

# Pack Bundle Patching — ALL APPROACHES BLOCKED

## Summary

**Modifying the Rolling Stones pack bundle (`therollingstones_pack_assets_all_*.bundle`) is currently IMPOSSIBLE due to the Addressables catalog's CRC validation.** Every approach tried produces a CE-34878-0 crash at startup.

## Blocking Root Cause: Addressables Catalog CRC Check

The game validates every loaded bundle's CRC32 against the catalog's `m_ExtraDataString`. The catalog (`aa/catalog.json`) contains:

```json
{"m_Hash":"a99482a8a3da9e991e5ae36f2fea209c","m_Crc":3700109647,
 "m_BundleSize":7902803,"m_UseCrcForCachedBundles":true,...}
```

Any modification to a bundle file changes its CRC → validation fails → crash. The catalog is loaded as plain JSON (not via `AssetBundle.LoadFromFile`), so the AFR plugin cannot redirect it.

See [[song-metadata-addressables-structure#Addressables Catalog CRC Validation]] for full details.

## All Failed Approaches

| Approach | Experiment | Why It Failed |
|----------|-----------|---------------|
| UnityPy `bf.save("original")` | Exp 132 | CAB format differs from original (+4 bytes) → CRC mismatch |
| UnityPy `cab.save()` + manual bundle | Exp 133 | CAB serialization incompatible (+4 bytes) → CRC mismatch |
| UnityPy `save_typetree()` | Exp 134 | Silently ignores modifications for BeatmapLevelSO |
| Byte-level text patch + LZ4 rebuild | Exp 134b | Recompression changes compressed bytes → CRC mismatch |
| Byte-level text patch + LZ4HC rebuild | Exp 135 | Recompression changes compressed bytes → CRC mismatch |
| Original bundle (diagnostic) | Exp 134a | ✅ WORKS — CRC unchanged, no crash |

## LZ4HC Requirement (Flag=3)

The original bundle uses `flag=3` (LZ4HC) for ALL blocks. When rebuilding, both blocks and blocks info must use LZ4HC:
```python
comp = lz4.block.compress(data, mode='high_compression', compression=9, store_size=False)
# Per-block flag must be 3
n_blocks.append((decomp_size, comp_size, 3))
```

Using LZ4 (flag=2) is also rejected by the PS4 Unity runtime.

## Bundle Building Requirements (for reference, even though blocked)

If the CRC issue is ever resolved, these are the requirements for manual bundle building:
- **Separate `f.write()` calls** — concatenated bytes cause alignment bugs
- **Explicit padding** — `b'\x00' * ((16 - tell % 16) % 16)` not `while tell%16:`
- **`f.flush()`** after header writes
- **LZ4HC** compression with per-block flag=3
- **BlockInfoNeedPaddingAtStart** (flag 0x200) requires alignment between blocks info and data blocks

## CAB Binary Format (v22+)

For Unity 2022.3 CABs (SerializedFile version 22+):
- Header: 48 bytes
- Offset 0x14: metadata_size (BE uint32) = 53401
- Offset 0x1C: file_size (BE uint32) = 89180
- data_offset = align16(48 + metadata_size) = 53456
- Object table entries: pathID(int64 LE) + offset(int64 LE, relative to data_offset) + size(int32 LE)

## m_Script PPtr Correction

The BeatmapLevelSO blob builder originally used `_CHAR_PATH_IDS["Standard"]` for m_Script PPtr (WRONG):
- **Correct m_Script pathID**: `2140275054477726686` (fileID=1)
- **Standard characteristic pathID**: `-7286399427822119286` (fileID=3)

## Current Best Alternative

Since pack bundle modification is blocked, the only viable path is modifying **per-song bundles** instead:
- `--enable-modes` adds characteristic modes to per-song bundles (Exp 138, awaiting test)
- Per-song bundles load per-song, not at startup, bypassing pack bundle CRC checks

### Quick Build Reference (for if/when CRC blocker is resolved)
```bash
python3 /workspace/beat_saber_deluxe/tools/build_patched_pack_bundle.py
```
