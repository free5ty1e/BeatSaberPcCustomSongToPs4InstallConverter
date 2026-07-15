---
name: pack-bundle-patching
description: "How to patch UnityFS pack bundles using UnityPy's save('original') method — BundleFile save internals, flags, structure"
metadata:
  type: reference
---

# Pack Bundle Patching via UnityPy save()

## Core Finding

UnityPy's `bf.save("original")` produces valid UnityFS bundles that the game can read. The key is calling `save()` with the **packer string** `"original"` (not a file path):

```python
data = bf.save("original")
with open(output_path, "wb") as f:
    f.write(data)
```

This was discovered in Experiment 132 (2026-07-15). All prior bundle patching approaches failed for specific technical reasons:

| Approach | Failure |
|----------|---------|
| `bf.save(path)` | Treats argument as packer type → `NotImplementedError("UnityFS - Packer:")` |
| `save_fs(writer, ...)` | Skips UnityFS signature + version strings header |
| Manual binary building | Alignment bug: missing BlockInfoNeedPaddingAtStart padding between blocks info and data blocks; wrong node_count position (after nodes instead of before); wrong per-block compression flags |
| `set_raw_data(new_blob)` | Returns False when blob sizes differ |

## m_Script PPtr Bug

The blob builder in `inject_pack_bundle.py` was using `_CHAR_PATH_IDS["Standard"]` (-7286399427822119286) for m_Script's pathID instead of the correct MonoScript pathID (2140275054477726686). These are completely different objects:

- **Correct:** MonoScript = pathID 2140275054477726686 (fileID=1)
- **Buggy:** Standard BeatmapCharacteristicSO = pathID -7286399427822119286 (fileID=3)

## 5-Mode Mode Selector

The StartMeUp BeatmapLevelSO in the Rolling Stones pack bundle was modified to expose 5 preview difficulty modes:

| Mode | BeatmapCharacteristicSO pathID |
|------|-------------------------------|
| Standard | -7286399427822119286 |
| OneSaber | -8583864861369561029 |
| NoArrows | -5623662769225589684 |
| 90Degree | 4533580413116749821 |
| 360Degree | 1189643819550092755 |

All use fileID=3 (references CAB-d32c... resource file).

## Detailed Reference

For complete format details, flags breakdown, and step-by-step patching procedure, see the memory file:
[pack-bundle-patching.md](/home/vscode/.claude/projects/-workspace/memory/pack-bundle-patching.md)
