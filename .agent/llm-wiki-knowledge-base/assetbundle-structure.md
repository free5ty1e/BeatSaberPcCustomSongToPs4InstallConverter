---
name: assetbundle-structure
description: "Unity AssetBundle structure for PS4 Beat Saber, SerializedFile format, TextAsset anatomy"
metadata:
  type: entity
---

# AssetBundle Structure

Beat Saber on PS4 stores its song data as Unity AssetBundles (`.bundle` files) in:
```
/app0/Media/StreamingAssets/BeatmapLevelsData/<level_id>
```
Each bundle corresponds to one song (one `BeatmapLevelData`).

## Bundle Contents (11 Objects)

A typical Beat Saber song bundle contains exactly 11 Unity objects:

| # | Class | Object | Description |
|---|-------|--------|-------------|
| 1 | TextAsset (49) | `Easy.beatmap.gz` | Beatmap difficulty data (gzip-compressed JSON) |
| 2 | TextAsset (49) | `Normal.beatmap.gz` | Beatmap difficulty data |
| 3 | TextAsset (49) | `Hard.beatmap.gz` | Beatmap difficulty data |
| 4 | TextAsset (49) | `Expert.beatmap.gz` | Beatmap difficulty data |
| 5 | TextAsset (49) | `ExpertPlus.beatmap.gz` | Beatmap difficulty data |
| 6 | TextAsset (49) | `Easy.lightshow.gz` | Lightshow/event data |
| 7 | TextAsset (49) | `<level_id>.audio.gz` | Audio metadata |
| 8 | MonoBehaviour (114) | `BeatmapLevelDataSO` | ScriptableObject wrapper |
| 9 | MonoBehaviour (114) | `<LevelId>BeatmapLevelData` | Main data container with PPtr references |
| 10 | MonoBehaviour (114) | `<LevelId>` | BeatmapLevelDataSO (ScriptableObject) |
| 11 | AudioClip (83) | `$<LevelId>` | Audio clip reference (FSB5) |

## TextAsset Raw Format (CRITICAL)

TextAssets store their data in m_Script field. The **exact** raw byte layout is:

```
[4 bytes: m_Name length (LE uint32)]
[N bytes: m_Name string content]
[4 bytes: m_Script length (LE uint32)]
[M bytes: m_Script content]
```

There is NO `m_GameObject` or `m_Enabled` prefix in the raw data — these fields are implicit for class_id=49 (TextAsset). The m_Script is **exclusively gzip data** with no decompressed_size prefix.

### m_Script = Just Gzip ⚠️
This was the root cause blocker for many experiments. The m_Script content is:
```
[gzip compressed JSON data]
```
NOT:
```
[decompressed_size (4 bytes)] [gzip compressed JSON data]  ← WRONG
```

The game's Unity runtime checks for gzip magic bytes (`1f 8b`) at offset 0 of m_Script. Any leading bytes before the gzip stream cause the game to reject the data.

## SerializedFile Format

Unity stores AssetBundles in a custom SerializedFile format:
- Header: metadata size, file size, version, endianness, reserved
- Object table: path_id → (byte_start, byte_size) for each object
- TypeTree: class definitions for serialization
- Data section: actual object data at offsets specified in object table

### Alignment
The SerializedFile writer aligns each object's data to 8 bytes. The `write_aligned_string` function aligns strings to 4 bytes. These alignments are internal to the save process and must be consistent.

See also: [[m-script-gzip-format]], [[unitypy-serialization]], [[beatmap-format-v3]]
