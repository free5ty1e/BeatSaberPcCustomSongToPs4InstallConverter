# Beat Saber PS4 - Asset Format Analysis

## Date: 2026-05-01

## Game Structure

### Location
`/workspace/ps4_dump/CUSA12878-patch/Media/`

### Key Folders

| Folder | Description |
|--------|-------------|
| `StreamingAssets/BeatmapLevelsData/` | **All song levels are here!** |
| `StreamingAssets/aa/` | Addressable asset bundles |
| `globalgamemanagers*` | Global game metadata |
| `level*` | Scene/level data |

## BeatmapLevelsData Structure

### Contents
Each song has a folder in `BeatmapLevelsData/`:
```
BeatmapLevelsData/
├── 100bills/
├── 100billsremix/
├── 2beloved/
├── aboutdamntime/
├── abracadabra/
├── accelerate/
├── ... (many more songs)
└── beatsaber/
```

### File Format
Each folder contains an AssetBundle with format:
- **Header**: `UnityFS` (LZ4HAM compression)
- **Size**: ~7MB for the base "beatsaber" level

### Example: beatsaber.asset
```
Size: 7,280,960 bytes (7.1 MB)
Format: Unity AssetBundle (LZ4HAM)
Magic: 0x556e697479465300 ("UnityFS")
```

## Unity Version

Based on eboot.bin analysis:
- **Unity 2022.3.x** (specifically 2022.3.33f1 based on COMPLETE_STEP_BY_STEP_GUIDE.md)
- LZ4HAM compression for AssetBundles

## AssetBundle Extraction

### Tools Required

1. **UABEA (UABE Avalon)**
   - GitHub: https://github.com/nesrak1/UABEA
   - Supports Unity 2022 with LZ4HAM
   - Cross-platform (Windows/Linux)
   - Download: Latest release or nightly builds

2. **AssetRipper** (for full extraction)
   - GitHub: https://github.com/AssetRipper/AssetRipper
   - Best for extracting complete asset structure
   - Supports Unity 2022

### Extraction Steps

1. Download UABEA from releases
2. Open `BeatmapLevelsData/beatsaber/` folder
3. Extract the AssetBundle contents
4. Analyze internal structure (MonoBehaviours, audio clips, beatmaps)

## Internal Structure of a Level

Based on typical Beat Saber Unity structure, each level contains:

1. **BeatmapLevelData (MonoBehaviour)**
   - Song name, artist, BPM
   - Difficulty configurations
   - Audio reference
   - Cover image reference

2. **AudioClip**
   - Song audio file (ogg/opus)
   - Preview clip

3. **BeatmapData (per difficulty)**
   - Note positions
   - Obstacles
   - Events (lighting)

4. **Cover Image**
   - PNG image

## Song Format Conversion Requirements

### PC Format (BeatSaver)
```
song_folder/
├── info.dat (or info.json)
│   ├── _songName
│   ├── _songAuthorName
│   ├── _beatsPerMinute
│   ├── _difficultyBeatmapSets[]
│   ├── _songFilename (audio)
│   └── _coverImageFilename
├── Easy.dat / Normal.dat / Hard.dat / Expert.dat / ExpertPlus.dat
│   ├── _notes[]
│   ├── _obstacles[]
│   └── _events[]
├── song.ogg
└── cover.jpg
```

### PS4 Format (Unity AssetBundle)
```
level_folder/
├── BeatmapLevelData.asset (MonoBehaviour)
├── audio (AudioClip reference)
├── cover (Texture2D)
└── difficulties/
    ├── Easy.beatmap.gz.bytes
    ├── Normal.beatmap.gz.bytes
    ├── Hard.beatmap.gz.bytes
    └── Expert.beatmap.gz.bytes
```

## Key Discovery

**BeatmapLevelsData folder has ~200+ songs pre-installed!**

This suggests Beat Saber already ships with many songs. Custom songs would need to be ADDED to this folder or use a different mechanism.

## Option 3: "Extras" Album Approach

From goal.md, Option 3 is to insert songs into an existing album like "Extras".

### Analysis Needed
1. Find where "Extras" album is defined
2. Understand how songs are categorized into albums
3. Find if there's a way to add custom songs to existing categories

### Next Steps
1. Extract and analyze a level's internal structure with UABEA
2. Find the level list/catalog structure
3. Understand album/category organization
4. Determine if songs can be added without game code modification

## References

- UABEA: https://github.com/nesrak1/UABEA
- AssetRipper: https://github.com/AssetRipper/AssetRipper
- Unity 2022 AssetBundle format: LZ4HAM