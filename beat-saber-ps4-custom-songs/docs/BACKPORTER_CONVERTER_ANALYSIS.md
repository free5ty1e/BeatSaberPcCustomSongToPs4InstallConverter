# Backporter PS4 Beat Saber Converter - Analysis

## Date: 2026-05-01

## Repository
https://github.com/Backporter/PS4-Beat-Saber-Converter

## Tool: PS4-Beat-Saber-Dat-Creator.exe

### Binary Analysis
- **Size**: 75,776 bytes
- **Type**: .NET 4.0 executable (C#/VisualBasic)
- **Project Name**: PS4_unity_beatmap_data_creator
- **Source Path**: C:\Users\Kernel\source\repos\Other\PS4_unity_beatmap_data_creator\...

### Usage (from README)
```
PS4-Beat-Saber-Dat-Creator.exe PCdat.dat PS4Dat.dat save.dat map_difficulty
```

### Arguments
| Argument | Description |
|----------|-------------|
| PCdat.dat | PC format beatmap (JSON .dat file) |
| PS4Dat.dat | Output PS4 binary format |
| save.dat | Save file (likely config/state) |
| map_difficulty | Difficulty level (0-4?) |

## How It Works (from TUT.txt)

### Step 1: Beatmap Conversion
The tool converts PC JSON beatmap format to PS4 binary format.

**PC Format (JSON v2/v3):**
```json
{
  "_version": "2.0.0",
  "_notes": [
    {"_time": 8.0, "_lineIndex": 1, "_lineLayer": 0, "_type": 0, "_cutDirection": 1},
    ...
  ],
  "_obstacles": [...],
  "_events": [...]
}
```

**PS4 Format (Binary):**
- Notes: 9 bytes each (time float + position + type + direction)
- Compact binary serialization

### Step 2: Audio Conversion (via UABE)
1. Create Unity 2018.1.6 project
2. Import audio files with same names as originals ($100Bills, etc.)
3. Build project
4. Use UABE to export AudioClip as .resource file
5. Replace in Beat Saber's sharedassets

### Step 3: Asset Injection
1. Open Beat Saber's sharedassets0.assets in UABE
2. Select "U2019.2.0f1" type
3. Import converted audio/beatmap dumps
4. Save and replace original file

## Key Requirements

| Component | Version | Purpose |
|-----------|---------|---------|
| Unity | 2018.1.6 | Build audio assets |
| UABE | Latest | Extract/import asset dumps |
| PS4-Beat-Saber-Dat-Creator | 1.0 | Convert beatmap format |

## Limitations

1. **Unmaintained**: No updates since 2021
2. **Replaces songs**: Does not ADD songs, only replaces existing ones
3. **Unity version mismatch**: TUT says 2018.1.6, but our dump uses Unity 2022.3.x
4. **No source code**: Cannot modify/fix the tool

## For Our Project

We need to create our own converter that:
1. Converts PC beatmap JSON → PS4 Unity 2022 binary format
2. Creates new levels (not just replace)
3. Works with current Beat Saber version

## Alternative Approaches

Since Backporter's tool is unmaintained and designed for song replacement (not addition), we need:

1. **Understand Beat Saber PS4's Unity Asset format** (v2022, not v2018)
2. **Create AssetBundle with custom songs** that can be loaded
3. **Either**:
   - Create a plugin to load external songs (like RB4DX)
   - Inject songs into game assets (complex, game updates break it)

## Next Steps

1. Analyze existing DLC packages to understand level format
2. Look for any Unity 2022 asset extraction tools
3. Consider building a custom plugin for Beat Saber

## References

- GitHub: https://github.com/Backporter/PS4-Beat-Saber-Converter
- Releases: https://github.com/Backporter/PS4-Beat-Saber-Converter/releases/tag/1.0
- PSXHAX Thread: https://www.psxhax.com/threads/adding-custom-songs-to-audica-psvr-tutorial-ps4-beat-saber-converter.11034/