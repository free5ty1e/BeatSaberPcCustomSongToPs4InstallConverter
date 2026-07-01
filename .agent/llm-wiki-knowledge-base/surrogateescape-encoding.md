---
name: surrogateescape-encoding
description: "Why surrogateescape must be used instead of latin-1 for binary data in string round-trips"
metadata:
  type: reference
---

# Surrogateescape Encoding for Binary Data

## Core Problem

When storing binary data (like gzip-compressed beatmap JSON) in UnityPy string fields (m_Script), the data must survive a decode→encode round-trip. Python's `latin-1` codec corrupts bytes > 127 because UnityPy's `save_typetree` encodes strings as `utf-8` with surrogateescape, not `latin-1`.

## Why latin-1 Fails

```python
binary_data = b'\x80\x81\x82...'  # Bytes > 127
as_string = binary_data.decode('latin-1')
# → Characters U+0080, U+0081, U+0082...

# UnityPy saves string as UTF-8:
# UTF-8 encodes U+0080 as 0xC2 0x80 (2 bytes)
# Result: data becomes 2x larger, CRC corrupted!
```

**Latin-1 encodes bytes 128-255 as Unicode characters U+0080-U+00FF.** When these are subsequently encoded as `utf-8` (which UnityPy's `write_aligned_string` does), characters U+0080-U+00FF become 2 bytes each (0xC2 0x80+). This:
1. Doubles the size of all bytes > 127
2. Corrupts gzip checksums
3. Makes the data unreadable by the game's decompressor

## Why surrogateescape Works

```python
binary_data = b'\x80\x81\x82...'  # Bytes > 127
as_string = binary_data.decode('utf-8', 'surrogateescape')
# → Characters U+DC80, U+DC81, U+DC82...

# UnityPy saves string as UTF-8 with surrogateescape:
# Surrogate characters U+DC80+ encode back to single byte 0x80+
# Result: EXACT original bytes preserved!
```

Python's `surrogateescape` codec maps individual non-UTF-8 bytes to Unicode surrogate characters (U+DC80-U+DCFF). When encoding back with `utf-8` + `surrogateescape`, these surrogate characters map back to the exact original single byte. This is a **lossless round-trip** for binary data through string fields.

## Fixed Pattern

```python
# ✅ CORRECT — always use surrogateescape for binary data in string fields
tt['m_Script'] = binary_data.decode('utf-8', 'surrogateescape')
reader.save_typetree(tt)
```

## Rule of Thumb
- **Text data**: Use regular UTF-8 encoding/decoding
- **Binary data in string fields**: Always use `utf-8` + `surrogateescape`
- **Never use `latin-1`** when the writer will encode as `utf-8`

See also: [[unitypy-serialization]], [[m-script-gzip-format]], [[beatmap-conversion-pipeline]]
