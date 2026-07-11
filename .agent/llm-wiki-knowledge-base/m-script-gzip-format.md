---
name: m-script-gzip-format
description: "Root cause: m_Script in beatmap TextAssets is just gzip data, not decompressed_size + gzip"
metadata:
  type: reference
---

# m_Script = Just Gzip (No Decompressed Size Prefix)

**This was the single biggest blocker for the entire project.**

## The Bug

The conversion pipeline was adding a 4-byte `decompressed_size` prefix before the gzip data in the `m_Script` field of beatmap TextAssets. The correct format is **just gzip data** — no prefix.

## Symptoms

- Game showed brief black screen (< 1 second) then returned to menu
- UnityPy could read the bundle (it reads `m_Script` as a string, ignoring format)
- The game's Unity runtime looked for gzip magic (`1f 8b` = 0x8B1F) at offset 0
- Found `dc 06 00 00` (0x000006DC = the fake decompressed_size as LE uint32) instead
- This happened EVERY time a beatmap was replaced regardless of V2 vs V3 format
- The unmodified bundle test (v0.39diag) worked because it didn't touch m_Script at all

## Why It Was Wrong

The original AssetBundle uses Unity's SerializedFile format where `m_Script` is written as an aligned string via `write_aligned_string()`. The string length is ALREADY tracked by:
1. The SerializedFile's object table (`byte_size` field)
2. The string's own 4-byte length prefix (part of `write_aligned_string`)

Adding a SECOND length field inside the string just shifts the gzip stream by 4 bytes, corrupting the magic header.

## Why UnityPy Didn't Catch It

UnityPy's `read_typetree()` reads `m_Script` as a generic Python string — it doesn't validate that the string content is valid gzip data. The string round-trip preserved the corrupted bytes perfectly. The user's test on PS4 was the only true validation.

## The Fix

```python
# ❌ WRONG — added 4-byte prefix before gzip
new_script = struct.pack('<I', len(new_json)) + gzip.compress(new_json)
tt['m_Script'] = new_script.decode('utf-8', 'surrogateescape')

# ✅ CORRECT — just gzip data, no prefix
new_script = gzip.compress(new_json)
tt['m_Script'] = new_script.decode('utf-8', 'surrogateescape')
```

## Why It Took So Long To Find

1. UnityPy doesn't validate gzip content — it treats m_Script as opaque bytes
2. Other serialization issues (save_typetree vs set_raw_data, surrogateescape encoding) masked the true root cause
3. Each bug had to be fixed independently before the final test worked

See also: [[assetbundle-structure]], [[unitypy-serialization]], [[beatmap-conversion-pipeline]]
