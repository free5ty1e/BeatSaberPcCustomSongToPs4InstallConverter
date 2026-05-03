# FSB5 Audio Format Discovery

## Date: 2026-05-02

## Key Finding

Beat Saber PS4 stores audio in **FSB5 format**, not raw OGG!

## Technical Details

### FSB5 Structure
```
Offset 0x00: "FSB5" magic (4 bytes)
Offset 0x04: Version (1)
Offset 0x08: Number of samples (1)
Offset 0x0C: Headers size (900 bytes / 0x384)
Offset 0x10: Data size (0 for embedded)
Offset 0x14: Sample info block
...
Offset 0x384: Audio data (after headers)
```

### Audio Format
- **Header size**: 900 bytes (0x384)
- **Audio data size**: 7,268,412 bytes (6.93 MB)
- **Internal format**: FSB5 proprietary (NOT raw OGG)
- **Export format**: UABEA exports as OGG wrapper

### Comparison
| Metric | FSB5 Resource | OGG Export |
|--------|---------------|-------------|
| Size | 7,268,412 bytes | 7,302,385 bytes |
| Header | FSB5 (900 bytes) | OGG (34,973 bytes) |
| Start | `61276800...` | `OggS` |

### Format Type
Sample mode: `0x3dd0c3ca`
Format type: `202` (CELT/FMOD specific)

## Why This Matters

To replace audio, we need to:
1. Convert new audio to FSB5 format (FMOD tool)
2. OR rebuild the .resource file with correct headers
3. Replace in AssetBundle

## Options for Audio Replacement

### Option A: FMOD Studio
Use FMOD Studio to create FSB5 sound banks:
1. Import audio into FMOD Studio
2. Export as FSB5 format
3. Extract headers from original .resource
4. Combine with new audio data

### Option B: Custom FSB5 Tool
Build a Python/C# tool to:
1. Parse existing FSB5 headers
2. Convert new audio to FSB5 format
3. Rebuild .resource file

### Option C: Hex Replacement (if sizes match)
If new audio is same size, try header-only replacement

## UABEA Import Test

When importing .resource file back into UABEA:
- It asks: "Is this asset serialized?"
- **Yes**: Treats as serialized FSB5 format
- **No**: Treats as raw audio data

This suggests we might be able to:
1. Modify audio in the .resource file
2. Re-import with correct flags

## Next Steps

1. Test UABEA import of .resource file (try both options)
2. Research FSB5 format specification
3. Find/create FSB5 encoder tool
4. Build audio replacement pipeline

## References

- FMOD FSB5 format: https://fmod.com/docs/2.00/api/core-api.html
- FSB5 decoder sample code: Various open source projects on GitHub