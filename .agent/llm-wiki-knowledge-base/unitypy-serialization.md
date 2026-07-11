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

See also: [[m-script-gzip-format]], [[assetbundle-structure]], [[beatmap-conversion-pipeline]]
