
# PS4 Beat Saber Asset Extraction Guide

## Tools Needed

### 1. AssetRipper (Recommended - Open Source)
```
Download: https://github.com/AssetRipper/AssetRipper/releases
Version: 0.2.0.0-alpha or newer
```

### 2. UABE (Unity Asset Bundle Extractor)
```
Download: https://github.com/AssetRipper/UABE/releases
```

### 3. Unity 2018.1.6 (Same version as PS4 Beat Saber)
```
Download: https://unity.com/releases/editor/whats-new/2018.1.6
```

## Extraction Steps

### Step 1: Export Official Songs
1. Open AssetRipper
2. File > Open File(s) > Select: `BeatmapLevelsData/100bills`
3. Export options:
   - Mesh export: DISABLED (not needed)
   - Audio export: WAV
   - Texture export: PNG
   - Scripts: NO (will cause errors)
4. Export to: `extracted_official/`

### Step 2: Analyze Export Structure
Look for:
- `LevelInfo` or similar - song metadata
- `AudioClip` - audio data
- `BeatmapData` - note timing/positions
- `Sprite` or `Texture2D` - cover image

### Step 3: Map PC Format to PS4 Format
PC BeatSaver format:
```
song.zip/
├── info.dat       (JSON - song metadata)
├── Easy.dat       (JSON - beatmap)
├── Normal.dat
├── Hard.dat
├── Expert.dat
├── ExpertPlus.dat
├── song.ogg       (audio)
└── cover.jpg      (256x256 cover)
```

PS4 Unity format (to recreate):
```
CustomSong.assetbundle (UnityFS compressed)
├── CustomLevelInfo     (ScriptableObject)
├── AudioClip           (HMX/FMOD encoded)
├── CoverTexture        (PNG/DXT5)
└── BeatmapAssets      (Custom binary format)
```

### Step 4: Build Custom Asset Bundle
1. Create Unity 2018.1.6 project
2. Import audio and convert to HMX format
3. Create LevelInfo ScriptableObject
4. Build AssetBundle for PS4
5. Test with FPKG

## Audio Conversion Note
PS4 Beat Saber uses FMOD/HMX audio. To convert:
- Use FMOD Studio to create .hmx files
- OR use the Audica audio format as reference
