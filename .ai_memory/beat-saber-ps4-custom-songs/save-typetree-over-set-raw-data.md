---
name: save-typetree-over-set-raw-data
description: "Why save_typetree must be used instead of set_raw_data for beatmap TextAssets"
metadata:
  type: reference
---

## Fix: Use `save_typetree` Instead of `set_raw_data`

**The Bug:** `set_raw_data(data)` causes internal serialization inconsistencies for some objects in the SerializedFile. Specifically, the same 3 beatmap objects (Normal, Expert, ExpertPlus) out of 5 would consistently fail `read_typetree()` after save, while others (Hard, Easy) passed.

**Symptoms:**
- `Objects: 8 OK, 3 FAILED` — same 3 objects failed every time regardless of data content
- The failures were deterministic by path_id position in the serialized file
- Only occurred with `set_raw_data`; `save_typetree` worked for all 11 objects

**Fix:** Use `save_typetree` to write the modified typetree:
```python
# ❌ WRONG — causes serialization inconsistency
reader.set_raw_data(bytes(new_raw))

# ✅ CORRECT — proper serialization, all objects pass
tt = reader.read_typetree()
tt['m_Script'] = new_script.decode('utf-8', 'surrogateescape')
reader.save_typetree(tt)
```

**Why `save_typetree` works:** It serializes the ENTIRE object via UnityPy's TypeTree serializer, which handles string alignment, field ordering, and byte padding correctly. `set_raw_data` bypasses this and injects raw bytes that might not match the expected format.

**Why `set_raw_data` failed for some objects:** The underlying cause is related to how `write_aligned_string` handles alignment for names that aren't multiples of 4 bytes. `save_typetree` uses `write_aligned_string` correctly; `set_raw_data` requires the caller to construct perfectly formatted data.
