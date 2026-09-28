---
name: unitypy-serialization
description: "UnityPy serialization best practices: save_typetree vs set_raw_data, surrogateescape encoding"
metadata:
  type: concept
---

# UnityPy Serialization

## save_typetree vs set_raw_data

**Always use `save_typetree` for modifying Unity objects, never `set_raw_data`.**

### set_raw_data — The Bug
`set_raw_data(data)` causes internal serialization inconsistencies for some objects in the SerializedFile. Specifically, the same 3 beatmap objects out of 5 consistently fail `read_typetree()` after save while others pass. The failures are deterministic by path_id position.

```python
# ❌ WRONG — causes serialization inconsistency
reader.set_raw_data(bytes(new_raw))
```

```python
# ✅ CORRECT — proper serialization, all objects pass
tt = reader.read_typetree()
tt['m_Script'] = new_script.decode('utf-8', 'surrogateescape')
reader.save_typetree(tt)
```

### Why save_typetree Works
It serializes the ENTIRE object via UnityPy's TypeTree serializer, which handles:
- String alignment (`write_aligned_string` adds padding to 4 bytes)
- Field ordering (matches what reader expects)
- Byte padding (ensures all data is properly aligned)

`set_raw_data` bypasses all of this and injects raw bytes directly, requiring the caller to construct perfectly formatted raw data (which must exactly match the serialized format including alignment padding).

## Surrogateescape Encoding for Binary Data

When storing binary data (like gzip streams) in UnityPy string fields:

**Use `surrogateescape` not `latin-1`.**

```python
# ❌ WRONG — latin-1 + subsequent utf-8 encoding DOUBLES bytes > 127
tt['m_Script'] = binary_data.decode('latin-1')

# ✅ CORRECT — surrogateescape preserves all bytes
tt['m_Script'] = binary_data.decode('utf-8', 'surrogateescape')
```

### Why
- `latin-1` encodes bytes 128-255 as Unicode characters U+0080-U+00FF
- UnityPy's `save_typetree` encodes strings as `utf-8` with surrogateescape
- UTF-8 encodes U+0080-U+00FF as 2-byte sequences (0xC2 0x80+)
- Result: binary data DOUBLES in size and CRC is corrupted
- `surrogateescape` maps each non-UTF-8 byte to a surrogate character (U+DC80-U+DCFF)
- These map back to exact single bytes on encoding — a lossless round-trip

## Modified Object Write Flow

The full modification pattern for beatmap TextAssets:

```python
import UnityPy, gzip

env = UnityPy.load(template_path)
bf = list(env.files.values())[0]
cab = next(v for v in bf.files.values() if hasattr(v, 'objects'))

for pid in sorted(cab.objects.keys()):
    reader = cab.objects[pid]
    if reader.class_id != 49: continue  # TextAsset only
    name = reader.peek_name()
    if not name or '.beatmap' not in name: continue
    
    # 1. Read existing typetree
    tt = reader.read_typetree()
    
    # 2. Build new m_Script (just gzip, no prefix!)
    new_script = gzip.compress(new_json_bytes)
    
    # 3. Set with surrogateescape encoding
    tt['m_Script'] = new_script.decode('utf-8', 'surrogateescape')
    
    # 4. Save via typetree (not set_raw_data)
    reader.save_typetree(tt)

# 5. Save modified bundle
result = bf.save(packer="none")
```

## Creating New TextAsset Objects from Scratch

When adding new objects to an existing CAB (e.g., injecting generated beatmaps for additional game modes), two critical fields must be set correctly in the `ObjectReader`:

### type_id Must Match the Types Table Index

The `type_id` field is an index into the CAB's `types` array (a serialized type lookup table). Do NOT hardcode `type_id=0`. Unity assigns types based on position in this table, and `type_id=0` typically maps to MonoScript (class_id 115), not TextAsset (class_id 49).

```python
# ❌ WRONG — type_id=0 may map to MonoScript
new_obj = ObjectReader(
    ...,
    type_id=0,
    class_id=49,
    ...
)

# ✅ CORRECT — find the actual index of the TextAsset type
text_asset_type = None
text_asset_type_index = 0
for i, t in enumerate(cab.types):
    if t.class_id == 49:
        text_asset_type = t
        text_asset_type_index = i
        break

new_obj = ObjectReader(
    ...,
    type_id=text_asset_type_index,
    class_id=49,
    ...
)
```

### Binary Data Format Must Use UnityPy's Writer (Not Manual struct.pack)

Unity's string format for `m_Name` and `m_Script` fields uses `write_aligned_string`:
- `int32 length` (string byte count, NOT including null terminator)
- `UTF-8 bytes` (the string itself)
- `4-byte alignment padding` (if needed)

There is NO null terminator appended after the string data. The `m_Script` field (MetaFlag `0x04000001`, "string as array") stores raw binary bytes using the same length-prefixed format.

```python
# ❌ WRONG — manual serialization with null terminators + len+1
import struct
name_bytes = name.encode('utf-8')
name_field = struct.pack('<i', len(name_bytes) + 1) + name_bytes + b'\x00'
script_field = struct.pack('<i', len(gz_data) + 1) + gz_data + b'\x00'
raw_data = name_field + script_field

# ✅ CORRECT — use UnityPy's EndianBinaryWriter
from UnityPy.streams.EndianBinaryWriter import EndianBinaryWriter
writer = EndianBinaryWriter(endian=endian)
writer.write_aligned_string(name)
writer.write_int(len(gz_data))
writer.write(gz_data)
writer.align_stream(4)
raw_data = writer.bytes
```

### Why the Wrong Format Breaks the Game

When UnityPy serializes with the wrong format (null terminators, wrong lengths):
1. The object's `byte_size` in the metadata table may differ from the actual data size
2. After save+reload, `read_typree()` fails with "read_str out of bounds" because the reader position doesn't match expected field boundaries
3. The PS4 Unity runtime silently skips the object, causing the game to fall back to Standard beatmaps for that mode

### ObjectReader Data Field

For newly created objects, set `data=raw_data` so the `write()` method uses the pre-computed bytes directly instead of trying to read from a non-existent reader position:

```python
new_obj = ObjectReader(
    assets_file=cab,
    reader=EndianBinaryReader(raw_data, endian),
    path_id=new_path_id,
    type_id=text_asset_type_index,
    serialized_type=text_asset_type,
    class_id=49,
    type=49,
    byte_start=0,
    byte_size=len(raw_data),
    is_destroyed=0,
    is_stripped=0,
    data=raw_data,  # ← Critical for new objects
)
```

See also: [[m-script-gzip-format]], [[assetbundle-structure]], [[beatmap-conversion-pipeline]]
