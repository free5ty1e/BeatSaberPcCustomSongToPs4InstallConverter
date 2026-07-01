---
name: surrogateescape-encoding
description: "Why surrogateescape must be used instead of latin-1 for binary data in string round-trips"
metadata:
  type: reference
---

## Fix: Use `surrogateescape` Not `latin-1` for Binary Data

**The Bug:** Using `.decode('latin-1')` on binary data before storing it in a UnityPy string field (m_Script) corrupts bytes > 127 because `save_typetree` encodes strings as `utf-8` (not `latin-1`), and `utf-8` encodes characters U+0080-U+00FF as 2-byte sequences (0xC2 0x80+).

**Symptoms:**
- Gzip data that contains bytes > 127 becomes ~50% larger after save_typetree round-trip
- The gzip CRC or data is corrupted, causing decompression failures
- Only affects binary data with byte values > 127 (most gzip data has these)

**Fix:** Use `surrogateescape` for both decoding and encoding:
```python
# ❌ WRONG — latin-1 decoded, then utf-8 encoded → doubled bytes
tt['m_Script'] = binary_data.decode('latin-1')

# ✅ CORRECT — surrogateescape preserves all bytes
tt['m_Script'] = binary_data.decode('utf-8', 'surrogateescape')
```

**Why surrogateescape works:** Python's `surrogateescape` codec maps individual non-UTF-8 bytes to Unicode surrogate characters (U+DC80-U+DCFF). When encoding back with `utf-8` + `surrogateescape`, these surrogate characters map back to the exact original single byte. This is a lossless round-trip for binary data.

**Why latin-1 fails:** `latin-1` encodes bytes 128-255 as Unicode characters U+0080-U+00FF. When these are subsequently encoded as `utf-8` (which UnityPy's `write_aligned_string` does), characters U+0080-U+00FF become 2 bytes each (0xC2 0x80+). This doubles the size and corrupts the data.

**See also:** Python docs on `surrogateescape`, [[m-script-gzip-only]]
