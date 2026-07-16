---
name: v22plus-cab-header-format
description: Unity 2022.3 SerializedFile CAB header layout — unique big-endian metadata_size and file_size fields at different offsets than v21-and-earlier.
metadata: 
  node_type: memory
  type: reference
  originSessionId: bc573f12-ef2e-43e2-9a5a-f79fefc465a0
---

# v22+ CAB Header Format (Unity 2022.3 SerializedFile)

The Unity 2022.3 (SerializedFile version 22+) CAB header has a unique format that differs significantly from v9-v21:

## Header Layout (48 bytes total)

| Offset | Size | Endian | Field | Value (Original) |
|--------|------|--------|-------|------------------|
| 0x00 | 4 | LE | Unknown/Reserved | 0 |
| 0x04 | 4 | LE | Unknown/Reserved | 0 |
| 0x08 | 4 | LE | SerializedFile version | 0x16000000 (correctly read as 22 when BE?) |
| 0x0C | 4 | LE | Unknown/Reserved | 0 |
| 0x10 | 4 | BE? | Unknown | 0 |
| **0x14** | **4** | **BE** | **metadata_size** | **53401** |
| 0x18 | 4 | BE? | Unknown | 0 |
| **0x1C** | **4** | **BE** | **file_size (total CAB size)** | **89180** |
| 0x20-0x2F | 16 | — | Remaining header | 0 |

**Key finding:** metadata_size and file_size are stored as BIG ENDIAN uint32 at unusual offsets. This differs from the standard LE uint32 at bytes 0 and 4 for v9-v21.

## Derived Values
```
data_offset = align16(48 + metadata_size)
            = align16(48 + 53401)
            = 53456
```

## Object Table Entries

Each object in the CAB has an entry in the object table, stored in the metadata section (between byte 48 and data_offset):

```
Format: pathID(int64 LE) + offset(int64 LE relative to data_offset) + size(int32 LE)
```

| Field | Type | Offset from entry start | 
|-------|------|------------------------|
| pathID | int64 (LE) | +0 |
| offset (relative to data_offset) | int64 (LE) | +8 |
| size | int32 (LE) | +16 |

The offset is a **relative offset** from data_offset, NOT an absolute file offset:
```
absolute_byte_start = data_offset + stored_offset
```

To search for an object's entry in the raw CAB:
1. Compute `stored_offset = byte_start - data_offset`
2. Search for `struct.pack('<q', path_id) + struct.pack('<Q', stored_offset)` in bytes [48..data_offset)
3. Update `stored_offset += delta` when blob size changes
4. The size field is at entry_start + 16

## Updating Object Table After Blob Size Change

When modifying an object that changes size (e.g., adding mode entries to _pds):

```python
# For each object with byte_start > original_blob_end:
# 1. Compute old_stored = byte_start - data_offset
# 2. new_stored = old_stored + delta
# 3. Find entry via pathID + old_stored pattern
# 4. Update offset at entry + 8 to new_stored
# 5. Update blob's own SIZE at entry + 16
# 6. Update file_size at 0x1C-0x1F (BE uint32)
```

Tested: 26/26 object entries found and updated correctly with delta=817 in Exp 134.

## First Object Structure
- Object 0 (pathID=-9019344038381174240)
  - byte_start = 53456 (= data_offset)
  - stored_offset = 0
  - size = 2984
  - The data section starts at data_offset (53456), and the first object's data starts immediately

## BeatmapLevelSO (Target Object)
- pathID = 2287600824654271910
- byte_start = 79920
- stored_offset = 79920 - 53456 = 26464 (0x6760)
- original size = 440 bytes

## References
- [[pack-bundle-patching]] — Full patching guide
- [[unitypy-serialization-limitations]] — Why UnityPy serialization is incompatible
