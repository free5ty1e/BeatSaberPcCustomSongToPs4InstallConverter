---
name: m-script-gzip-only
description: "Root cause: m_Script in beatmap TextAssets is just gzip data, NOT decompressed_size + gzip"
metadata:
  type: reference
---

## Root Cause: m_Script = Just Gzip (No Decompressed Size Prefix)

**The Bug:** The conversion pipeline was adding a 4-byte `decompressed_size` prefix before the gzip data in the `m_Script` field of beatmap TextAssets. The correct format is **just gzip data** — no prefix.

**Symptoms:**
- Game showed brief black screen then returned to menu
- UnityPy could read the bundle (it reads `m_Script` as a string, ignoring the format)
- The game's Unity runtime looked for gzip magic (`1f 8b`) at offset 0 but found `dc 06 00 00` (the fake decompressed_size) instead
- This happened EVERY time a beatmap was replaced, regardless of V2 vs V3 format

**Fix:** Changed from:
```python
# ❌ WRONG — added 4-byte prefix before gzip
new_script = struct.pack('<I', len(new_json)) + gzip.compress(new_json)
tt['m_Script'] = new_script.decode('utf-8', 'surrogateescape')
```
to:
```python
# ✅ CORRECT — just gzip data, no prefix
new_script = gzip.compress(new_json)
tt['m_Script'] = new_script.decode('utf-8', 'surrogateescape')
```

**Why it was wrong:** The original BeatmapLevelData on PS4 uses a Unity SerializedFile format where `m_Script` is written as an aligned string via `write_aligned_string()`. The string length is already tracked by the SerializedFile's object table — adding a second length field inside the string just corrupts the gzip stream.

**Why UnityPy didn't catch it:** UnityPy's `read_typetree()` reads `m_Script` as a generic string — it doesn't validate that it's valid gzip data. The string round-trip preserved the corrupted bytes, so UnityPy showed no errors.

**Why it blocked us for N experiments:** Every single test since the first beatmap replacement had this bug. The unmodified bundle test (v0.39diag) worked because it didn't touch `m_Script` at all. Any modification via `save_typetree` with the extra prefix would corrupt the gzip stream.

**Related experiments:** [[experiment-71]]
**Related fixes:** [[save-typetree-over-set-raw-data]], [[surrogateescape-encoding]]
