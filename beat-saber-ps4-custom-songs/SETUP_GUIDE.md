
# Beat Saber PS4 Custom Songs - Complete Setup Guide

## Prerequisites
- PS4 with GoldHEN jailbreak (required for PKG installation)
- Decrypted Beat Saber game dump (already provided)
- Windows PC (for Unity and some tools)

## Step 1: Download Required Tools

### Option A: Automatic Download (if tools are accessible)
Run: `python3 scripts/setup_tools.py`

### Option B: Manual Download

1. **AssetRipper** (for extracting PS4 assets)
   - URL: https://github.com/AssetRipper/AssetRipper/releases
   - Download: AssetRipper_0.2.0.0-alpha.zip
   - Save to: `tools/AssetRipper/`

2. **FPKG Tools 3.87** (for creating PKG files)
   - URL: https://github.com/CyB1K/PS4-Fake-PKG-Tools-3.87-Patched-For-FPKGs/releases
   - Download: PS4-Fake-PKG-Tools-3.87.7z
   - Extract to: `tools/FPKG-Tools/`

3. **psDLC** (for creating unlocker)
   - URL: https://github.com/Efrii/PsDlc.GUI/releases
   - Download: PsDlc.zip
   - Extract to: `tools/psDLC/`

4. **Unity 2018.1.6** (for building asset bundles)
   - URL: https://unity.com/releases/editor/whats-new/2018.1.6
   - Install with: Windows, Build Support (PS4)

## Step 2: Extract PS4 Song Bundles

1. Open AssetRipper
2. File > Open Files
3. Select: `CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/100bills`
4. Export to: `extracted/100bills/`
5. Analyze the structure

## Step 3: Download Custom Songs

1. Go to: https://beatsaver.com
2. Search for songs (popular ones: Crystallized, Crab Rave, etc.)
3. Download ZIP files
4. Extract to: `songs/`

## Step 4: Build Unity Project

1. Open: `unity-project/` in Unity 2018.1.6
2. Import your custom songs
3. Build Asset Bundles for PS4

## Step 5: Create PS4 PKG

1. Open FPKG Tools > orbis-pub-gen.exe
2. Create new project: Additional Content Package with Extra Data
3. Add your custom song asset bundles
4. Build PKG

## Step 6: Create Unlocker

1. Open psDLC
2. Enter Content ID: UP8802-CUSA12878_00-BSCUSTOMSONGS01
3. Create FPKG
4. Rename to: `-unlock.pkg`

## Step 7: Install on PS4

1. Copy both PKG files to USB drive
2. On PS4: GoldHEN > Install Package
3. Install unlocker FIRST, then DLC

## Directory Structure

```
beat-saber-ps4-custom-songs/
├── tools/
│   ├── AssetRipper/          # Asset extraction
│   ├── FPKG-Tools/           # PKG creation
│   └── psDLC/                # Unlocker creation
├── unity-project/            # Unity 2018.1.6 project
│   ├── Assets/Scripts/
│   └── ProjectSettings/
├── songs/                    # Downloaded custom songs
├── extracted/               # Extracted PS4 bundles
├── output/                   # Final PKG output
│   └── dlc_package/
└── scripts/                  # Python scripts
```

## Troubleshooting

### "BeatSaver API is down"
- BeatSaver periodically goes offline
- Check https://status.beatsaver.com
- Use manual download method

### "Unity build fails for PS4"
- Make sure to install PS4 build support
- Check Unity logs for errors

### "PKG won't install on PS4"
- Ensure PS4 is jailbroken with GoldHEN
- Check Content ID format matches game ID
- Install unlocker first
