---
name: pack-bundle-patching
description: How to patch UnityFS pack bundles with UnityPy save() for PS4 AFR
metadata: 
  node_type: memory
  type: reference
  originSessionId: bc573f12-ef2e-43e2-9a5a-f79fefc465a0
---

# Pack Bundle Patching via UnityPy `save("original")`

The Rolling Stones pack bundle (`therollingstones_pack_assets_all_*.bundle`) is a UnityFS-format AssetBundle. To patch objects inside it (e.g., adding mode selector preview data to BeatmapLevelSO), use UnityPy's `save("original")` method.

## The Working Approach

```python
from UnityPy import Environment

env = Environment(original_bundle_path)
bf = list(env.files.values())[0]

# Find the CAB (SerializedFile)
cab_key = next(k for k in bf.files if k.startswith('CAB-') and '.res' not in k)
cab = bf.files[cab_key]

# Get the object and modify its TypeTree
obj = cab.objects[<path_id>]
tree = obj.read_typetree()
# ... modify tree data ...
obj.save_typetree(tree)

# Save the bundle with UnityPy's save("original")
data = bf.save("original")  # <-- KEY: use "original" packer, not a file path!
with open(output_path, 'wb') as f:
    f.write(data)
```

## Why Other Approaches Fail

| Approach | Result |
|----------|--------|
| `set_raw_data()` with larger blob | Returns False — sizes must match |
| `set_raw_data()` with same-size blob | Works only when exact size match |
| `save_typetree()` + `bf.save(path)` | `NotImplementedError("UnityFS - Packer")` on save |
| Manual UnityFS bundle building | Multiple LZ4/alignment/node-format bugs |
| `save_fs(writer, ...)` | Missing header strings (signature, version) |

## The m_Script PPtr Bug

The original `build_beatmap_levelso_blob()` in `inject_pack_bundle.py` used `_CHAR_PATH_IDS["Standard"]` for the **m_Script PPtr pathID**. This is WRONG:

- **Correct m_Script pathID**: `2140275054477726686` (fileID=1)
- **Standard characteristic pathID**: `-7286399427822119286` (fileID=3)

These are completely different values. The m_Script PPtr must point to the MonoScript, not to the BeatmapCharacteristicSO.

## The BlockInfoNeedPaddingAtStart Headache

The pack bundle uses flags `0x243`:
- `0x200` = BlockInfoNeedPaddingAtStart → align to 16 after blocks info BEFORE data blocks
- `0x40` = BlocksAndDirectoryInfoCombined → blocks info at start of file
- `0x03` = LZ4HC compression

When rebuilding manually, you MUST add 16-byte alignment padding between the blocks info and data blocks, or UnityPy's reader fails with `read_str out of bounds`.

## Deployment

1. Place patched bundle in `/data/GoldHEN/AFR/CUSA12878/rollingstones_pack_patched.bundle`
2. Add redirect in `/data/GoldHEN/AFR/CUSA12878/redirects.json`:
   ```json
   "therollingstones_pack_assets_all_<hash>": "rollingstones_pack_patched.bundle"
   ```
3. The plugin uses `strstr` substring matching (case-insensitive), so a partial key works.

## 5 Mode Characteristic PPtrs

Standard:  fileID=3, pathID=-7286399427822119286
OneSaber:  fileID=3, pathID=-8583864861369561029
NoArrows:  fileID=3, pathID=-5623662769225589684
90Degree:  fileID=3, pathID=4533580413116749821
360Degree: fileID=3, pathID=1189643819550092755
