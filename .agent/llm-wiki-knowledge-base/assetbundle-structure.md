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

## UnityFS BundleFile Format (Pack Bundles)

The Rolling Stones pack bundle (`therollingstones_pack_assets_all_*.bundle`) uses the **UnityFS** wrapper format, not the plain SerializedFile format used by per-song bundles. Key differences:

| Feature | SerializedFile (`.assets`) | BundleFile (UnityFS) |
|---------|---------------------------|---------------------|
| Header starts with | metadata size (int32) | `"UnityFS\0"` |
| Compression | None (per-object options) | LZ4/LZ4HC blocks |
| Contains | Objects directly | CAB- entries (each a SerializedFile) |
| Used by | Per-song bundles | Pack bundles (shared assets) |

### UnityFS Header Structure (all big-endian)

| Offset | Size | Field | Value (v8) |
|--------|------|-------|-----------|
| 0x00 | 8 | Signature | `"UnityFS\0"` |
| 0x08 | 4 | Version (BE int32) | 8 |
| 0x0C | 6 | Player version string | `"5.x.x\0"` |
| 0x12 | 12 | Engine version string | `"2022.3.33f1\0"` |
| 0x1E | 8 | File size (BE int64) | Total bundle size |
| 0x26 | 4 | Compressed blocks info size (BE int32) | Size of LZ4-compressed blocks info |
| 0x2A | 4 | Decompressed blocks info size (BE int32) | Always 859 for this bundle |
| 0x2E | 4 | Data flags (BE int32) | `0x243` (see below) |
| 0x32 | padding | Align to 16 | 0x00 bytes |

### Flag 0x243 Breakdown

- `0x03` (bits 0-1) = LZ4HC compression
- `0x40` (bit 6) = BlocksAndDirectoryInfoCombined (blocks info at file start)
- `0x200` (bit 9) = BlockInfoNeedPaddingAtStart (16-byte align between blocks info and data)

**Critical:** The `BlockInfoNeedPaddingAtStart` flag requires 16-byte alignment BETWEEN the compressed blocks info and the start of the data blocks. Without this padding, UnityPy's reader fails with `read_str out of bounds`.

### Blocks Info Format (after decompression)

| Offset | Size | Field |
|--------|------|-------|
| 0x00 | 16 | Hash (zeros) |
| 0x10 | 4 | Block count (BE uint32) |
| 0x14 | block_count × 10 | Block entries |
| Block entry | 4 + 4 + 2 | Uncompressed size (BE uint32) + Compressed size (BE uint32) + Flags (BE uint16) |
| After blocks | 4 | Node count (BE int32) |
| Nodes | node_count × variable | Node entries |

Each node entry:
- Offset (BE int64) — position in decompressed data stream
- Size (BE int64)
- Flags (BE int32)
- Path (null-terminated UTF-8, variable length, NOT 64-byte padded!)

### Patching with UnityPy

The only working patching method is `bf.save("original")`:

```python
env = Environment(original_bundle)
bf = list(env.files.values())[0]
# ... modify object via read_typetree() + save_typetree() ...
data = bf.save("original")  # returns bytes, NOT a file!
with open(output_path, "wb") as f:
    f.write(data)
```

**Why other approaches fail:**
- `bf.save(path)` treats the argument as packer type — `NotImplementedError`
- `save_fs(writer, ...)` skips the signature/version strings — invalid header
- `set_raw_data(new_blob)` returns `False` when sizes differ — can't resize
- Manual rebuilding has format edge cases (alignment, node count position, LZ4 flags)

See [[pack-bundle-patching]] for complete details and the 5-mode mode selector implementation.
