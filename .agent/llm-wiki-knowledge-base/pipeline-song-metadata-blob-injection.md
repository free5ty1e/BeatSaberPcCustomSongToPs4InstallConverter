---
name: pipeline-song-metadata-blob-injection
description: "BeatmapLevelSO serialized blob builder for injecting custom song metadata (name, artist, duration, BPM) into per-song CAB bundles"
metadata:
  type: reference
---

# BeatmapLevelSO Serialized Blob Builder

## Overview

Experiment 128 added a BeatmapLevelSO serialized blob builder (`_build_beatmap_level_so_blob()`) to `full_custom_song_pipeline.py`. This function constructs an IL2CPP-compatible serialized data blob containing custom song metadata that the game's Addressables system can resolve by `_levelID` when the per-song bundle is loaded.

## Serialized Format (Verified Against Pack Bundle)

The blob format was verified byte-by-byte against a real BeatmapLevelSO extracted from the therollingstones pack bundle (`rollingstones_pack_full.bundle`). Key finding: **the serialized blob does NOT include klassID/classID** — those are stored in the SerializedFile's type map and resolved by IL2CPP at deserialization time.

### Structure

```
Offset  Size    Field                              Notes
------  ----    -----                              -----
0x00    12      Padding/placeholder                Zero-filled; type info in SerializedFile map
0x0C    4       m_Script fileID (PPtr)             = 2 (m_Metadata->m_Script)
0x10    8       m_Script pathID (PPtr)             = -1 (base class = ScriptableObject)

Instance fields (order verified from pack bundle):
------  ----    -----                              -----
0x18    var     _levelID string                    Unity UTF-16LE + int32 length prefix
                Example: "custom/espresso"           blob_len=32 (includes trailing null)

0x?     var     _songName string                   Unity UTF-16LE + int32 length prefix
                Example: "Espresso"                  blob_len=30

0x?     var     _songSubName string                Unity UTF-16LE + int32 length prefix
                Example: "Sabrina Carpenter"         blob_len=18

0x?     var     _songAuthorName string             Unity UTF-16LE + int32 length prefix
                Example: (derived from above)        

0x?     var     _levelAuthorName string            Unity UTF-16LE + int32 length prefix
                Example: (usually same as song_author)

0x?     8       BPM (double/float64)               IEEE 754 double precision

Preview array (starts after BPM):
------  ----    -----                              -----
var      4      count = int32(5)                   Always 5 modes for custom songs
var      12     PPtr(fileID=2, pathID=<char_id>)   Each mode's BeatmapCharacteristicSO ref
var      4      diff_count (int32)
var      36*N    difficulty data                    36 bytes per entry
(×5 modes: Standard, OneSaber, NoArrows, 90Degree, 360Degree)
```

### Characteristic Path IDs for BeatmapCharacteristicSO References

| Mode | pathID |
|---|---|
| Standard | -7286399427822119286 |
| OneSaber | -5623662769225589684 |
| NoArrows | -8583864861369561029 |
| 90Degree | -5995858427784384822 |
| 360Degree | 4533580413116749821 |

> **Warning:** These pathIDs were historically swapped/mislabeled (OneSaber↔NoArrows,
> 90Degree pointed at the 360Degree characteristic). The table above was verified
> against the BeatmapCharacteristicSO objects in
> `sharedassets_assets_all_068cd59e9a6fba13da706dc9269bf759.bundle`
> (CAB `cb38b3e2985c65d4cf8a63437da74a89`). 90Degree (`containsRotation=1, requires360=0`,
> sortingOrder=5) MUST point to `-5995858427784384822`; pointing it at the 360Degree
> characteristic (`4533580413116749821`) hides the button because 360Degree requires
> the 360-degree gameplay feature. See [[pack-bundle-patching]].

## Usage in Pipeline

The pipeline calls `inject_beatmap_level_so()` after beatmap replacement (Step 6) and before bundle save (Step 7):

```python
inject_beatmap_level_so(
    bf,                           # BundleFile from UnityPy.load()
    song_name=custom_name,        # Display name (from --song-name or Info.dat)
    song_artist=custom_artist,    # Artist name (from --artist or Info.dat)
    duration_seconds=duration,    # Song length in seconds
    bpm=info_bpm,                 # BPM from Info.dat or default 120.0
    note_count_standard=note_count,
    note_count_diff_data=b'',     # Pre-encoded difficulty data (36B x N)
)
```

### CLI Flags for Metadata Override

| Flag | Purpose |
|---|---|
| `--song-name NAME` | Override song display name |
| `--artist NAME` | Override artist/song-author name |

When these flags are not provided, values are auto-derived from Info.dat (local songs) or BeatSaver API (downloaded songs).

## Current Implementation Status

### What Works ✅
- **Blob construction**: Verified byte-for-byte against pack bundle data
- **String encoding**: UTF-16LE with int32 length prefix matches UnityPy's format
- **PPtr serialization**: 4-byte fileID + 8-byte pathID matches pack bundle layout
- **BPM double precision**: IEEE 754 double matches pack bundle output
- **Preview array layout**: count(4) + [16 bytes per mode x 5] correctly structured
- **Mode-aware blob (v0.5310, Exp 177)**: `_build_beatmap_level_so_blob()` now emits the preview array with ONLY the enabled modes (Standard, OneSaber, NoArrows, 90Degree — 360Degree purged). `drop pop candy` blob = 1,010 B, saved to `_beatmap_level_so_drop pop candy.blob` (not injected).

### UnityPy 1.25.0 Injection Blocker (Exp 177 — CONFIRMED)
Two read paths to inject the preview blob or construct a new TextAsset into the CAB are both blocked:

1. **`env.create_object` does not exist** in UnityPy 1.25.0 (the add-object API from newer versions is absent).
2. **`ObjectReader` constructed over a bare `EndianBinaryReader`** fails with `ValueError: read_str out of bounds` — `ObjectReader` is bound to the parent `SerializedFile`'s stream (bytePosition/byteSize offsets) and cannot read an independent blob.

Remaining candidate (next): byte-level SerializedFile surgery — append the object entry + update the object/type tables and m_Data offsets, then re-save the UnityFS with correct block layout. See Options A/B below.

### What's Needed Before PS4 Testing ⚠️
The blob can be constructed and written to disk (saved as `_beatmap_level_so_<song>.blob` for inspection), but **injection into the actual CAB file** requires:

1. **UnityPy type support for BeatmapLevelSO** — UnityPy's MonoBehavior class doesn't know about BeatmapLevelSO fields
2. **Alternative**: Raw CAB file manipulation (append new object entry to SerializedFile + update manifest table)
3. **Bundle external ref validation** — inserting objects may change serialization offsets requiring bundle-level offset recalculation

### Approach Options for Injection

**Option A: Post-save CAB patching**
- After `bf.save(packer="lz4")` produces the final bundle, parse the UnityFS header to find free space
- Append new object data and update the object table entries
- Risk: changing offsets may require updating all PPtr references within the bundle

**Option B: Pre-save SerializedFile manipulation**
- Modify UnityPy's internal type registry with BeatmapLevelSO serialization instructions
- Add objects through UnityPy's normal path with correct serialized data
- Requires understanding of how UnityPy resolves type info for unknown classes

**Option C: Separate Addressables entry**
- Create the BeatmapLevelSO as a separate asset in the pack bundle instead of per-song bundles
- Update catalog.json to map additional internal IDs to our modified pack bundle
- May not work — game may resolve _levelID only within the per-song bundle path

## Related

- [[song-metadata-addressables-structure|Song Metadata & Addressables Structure]] — how the game resolves BeatmapLevelSO objects
- [[assetbundle-structure|AssetBundle Structure]] — UnityFS format, object table, CAB internals
- [[unitypy-serialization|UnityPy Serialization]] — type registry, save_typetree, set_raw_data
