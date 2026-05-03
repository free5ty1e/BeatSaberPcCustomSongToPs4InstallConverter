# Unity Beat Saber Level Creator

A Unity 2022.3 project for creating custom Beat Saber PS4 levels with audio replacement.

## Setup Instructions

### 1. Open Unity Hub

1. Launch Unity Hub
2. Click **Open** → Navigate to this folder
3. Select the `unity_project` folder
4. Unity will open the project

### 2. Install Required Components

If prompted, install:
- **PS4 Build Support** (required for PS4 AssetBundles)
- **Linux Build Support** (recommended)

### 3. Get Test Audio

1. Place any OGG/WAV audio file in `Assets/TestAudio/`
2. Name it `test_song.ogg` or similar

## Creating a Custom Level

### Method A: Using the Menu (Easiest)

1. **Import Audio**
   - Place your OGG file in `Assets/Audio/`
   - Unity will import it automatically

2. **Create Level**
   - Unity menu: **BeatSaber** → **Create Custom Level**
   - A new level GameObject will be created in the scene

3. **Configure Level**
   - Select the `CustomBeatmapLevel` object in the Hierarchy
   - In the Inspector, fill in:
     - **Level ID**: Unique name (e.g., `mysong`)
     - **Song Name**: Display name
     - **Artist**: Artist name
     - **BPM**: Song tempo
     - **Audio Clip**: Drag your imported audio here

4. **Build AssetBundle**
   - Unity menu: **BeatSaber** → **Build for PS4**
   - AssetBundle will be saved to `../output/`

### Method B: Manual

1. Create empty GameObject
2. Add `CustomBeatmapLevel.cs` script
3. Configure fields
4. Mark as AssetBundle in Inspector
5. Build via **BeatSaber** → **Build for PS4**

## Project Structure

```
unity_project/
├── Assets/
│   ├── Scripts/
│   │   ├── CustomBeatmapLevel.cs    # Main level component
│   │   ├── BeatSaberLevelCreator.cs # Menu items
│   │   └── AudioImporter.cs          # Audio import helper
│   ├── Editor/
│   │   └── BuildTool.cs             # PS4 AssetBundle builder
│   └── Audio/                        # Put your OGG files here
└── ProjectSettings/                  # Unity settings
```

## Level Configuration

### Required Fields
| Field | Description | Example |
|-------|-------------|---------|
| levelID | Unique identifier | `mysong` |
| songName | Song title | `My Custom Song` |
| artistName | Artist name | `Artist` |
| bpm | Beats per minute | `120.0` |
| audioClip | Audio file | (drag audio) |

### Optional Fields
| Field | Description | Default |
|-------|-------------|---------|
| levelAuthorName | Mapper name | `CustomMapper` |
| songTimeOffset | Audio offset (sec) | `0.0` |
| previewDuration | Preview length | `30.0` |

## Output

The build process creates:
- `../output/CustomLevels/` - Custom level AssetBundles
- `../output/metadata.json` - Level metadata for reference

## Notes

- Audio must be OGG Vorbis format
- Recommended: 44100Hz, Stereo, 192-320kbps
- Level will be saved as `CustomLevel_{levelID}`