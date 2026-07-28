---
name: unitypy-serialization-limitations
description: UnityPy save_typetree() ignores BeatmapLevelSO modifications in Unity 2022.3. cab.save() produces incompatible CAB format.
metadata: 
  node_type: memory
  type: reference
  originSessionId: bc573f12-ef2e-43e2-9a5a-f79fefc465a0
---

# UnityPy Serialization Limitations (PS4 / Unity 2022.3)

## `save_typetree()` ignores modifications for BeatmapLevelSO

In Unity 2022.3, UnityPy's TypeTreeHelper serializer does NOT properly write back modified tree data for BeatmapLevelSO objects. Even trivial changes (changing `_songName` from "Start Me Up" to "A") produce an identical 440-byte blob.

**Evidence:**
- Modified tree shows 5 `_previewDifficultyBeatmapSets` entries → `get_raw_data()` still returns 440 bytes
- Changed `_songName` to "A" (single char) → `get_raw_data()` still returns 440 bytes, "A" not found in blob
- No modifications at all → `get_raw_data()` matches original exactly (byte-identical)

**Root cause:** The TypeTree serializer for BeatmapLevelSO is read-only in Unity 2022.3. It can parse the tree from bytes correctly, but when writing back, it uses the cached TypeTree structure (which has fixed array sizes, string lengths, etc.) rather than the modified Python dict values.

**Impact:** The `read_typetree()` → modify dict → `save_typetree()` round-trip ONLY works for objects where all fields serialize to the same byte layout as the original. Any change to field values that would change the byte layout is silently ignored.

## `cab.save()` produces incompatible CAB format

Even with NO modifications to any objects, `cab.save()` produces a CAB that differs from the original:

- Original CAB: 89180 bytes
- `cab.save()` CAB: 89184 bytes (+4)

The PS4 Unity runtime rejects the re-serialized CAB, causing CE-34878-0 at startup. The 4-byte difference appears in the header's metadata_size field.

**Root cause:** UnityPy's SerializedFile.save() serializes the metadata section (header, types, objects table, externals) slightly differently from the original — alignment padding, type tree format, or externals table differences. These differences match the original for SOME Unity versions but not for 2022.3 PS4.

**Workaround:** Never use `cab.save()` or `bf.save()` for PS4 Unity 2022.3 bundles. Instead:
1. Extract the original CAB bytes from the decompressed bundle stream
2. Use byte-level patching at known offsets
3. Rebuild the bundle manually with correct LZ4HC compression

See [[pack-bundle-patching]] and [[ps4-unityfs-compression-requirements]].
