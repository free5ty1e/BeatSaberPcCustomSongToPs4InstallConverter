#!/usr/bin/env python3
"""
AssetRipper Helper - Analyze PS4 Beat Saber song bundles
Extracts and analyzes the Unity asset structure
"""
import json
import os
import struct
import subprocess
import zipfile
from pathlib import Path

PS4_DATA = Path("/workspace/temp/DumpedPs4BeatSaber/CUSA12878-patch/Media/StreamingAssets")
OUTPUT_DIR = Path("/workspace/beat-saber-ps4-custom-songs/extracted")
TOOLS_DIR = Path("/workspace/beat-saber-ps4-custom-songs/tools")

def analyze_bundle_format():
    """Deep analyze PS4 bundle format"""
    print("=" * 60)
    print("PS4 BEAT SABER BUNDLE FORMAT ANALYSIS")
    print("=" * 60)

    bundles_dir = PS4_DATA / "BeatmapLevelsData"
    bundles = list(bundles_dir.glob("*"))

    print(f"\nFound {len(bundles)} song bundles")
    print(f"First few: {[b.name for b in bundles[:5]]}")

    # Analyze file sizes
    sizes = [b.stat().st_size for b in bundles]
    print(f"\nSize stats:")
    print(f"  Min: {min(sizes):,} bytes ({min(sizes)/1024/1024:.1f} MB)")
    print(f"  Max: {max(sizes):,} bytes ({max(sizes)/1024/1024:.1f} MB)")
    print(f"  Avg: {sum(sizes)//len(sizes):,} bytes ({sum(sizes)//len(bundles)/1024/1024:.1f} MB)")

    # Analyze header
    print("\n--- Bundle Header Analysis ---")
    bundle = bundles[0]
    with open(bundle, 'rb') as f:
        header = f.read(64)

    print(f"Magic: {header[:8].hex()}")
    print(f"First 64 bytes: {header.hex()}")

    # Parse Unity FS header
    print("\nUnity FS Header Parse:")
    if header[:6] == b'UnityF':
        print("  Format: UnityFS (Serialized File)")
        version = struct.unpack('<I', header[6:10])[0]
        print(f"  Version field: {version}")

        if version == 83:
            print("  -> Unity 2018.x format detected")

    return bundles

def extract_bundle_metadata():
    """Try to extract metadata from bundles without full extraction"""
    print("\n" + "=" * 60)
    print("BUNDLE METADATA EXTRACTION")
    print("=" * 60)

    bundles_dir = PS4_DATA / "BeatmapLevelsData"

    samples = list(bundles_dir.glob("*"))[:3]

    for bundle in samples:
        print(f"\n--- {bundle.name} ---")

        with open(bundle, 'rb') as f:
            header = f.read(256)

            text_regions = []
            current_text = []

            for byte in header:
                if 32 <= byte <= 126:
                    current_text.append(chr(byte))
                else:
                    if len(current_text) > 4:
                        text = ''.join(current_text)
                        if any(c.isalpha() for c in text):
                            text_regions.append(text)
                    current_text = []

            print("  Text found in header:")
            for text in text_regions[:10]:
                if len(text) > 3:
                    print(f"    - {text}")

def create_complete_step_by_step_guide():
    """Create comprehensive step-by-step guide"""
    guide = """# Beat Saber PS4 Custom Songs - Complete Step-by-Step Guide

## Your Setup
- PS4 with GoldHEN jailbreak
- Decrypted Beat Saber game (CUSA12878) at `/workspace/temp/DumpedPs4BeatSaber/`
- Windows PC with Unity 2018.1.6 and AssetRipper installed

---

# PHASE 1: Analyze PS4 Song Format (AssetRipper)

## Step 1.1: Extract Sample PS4 Song

1. **Open AssetRipper** on Windows

2. **File > Open Files** (or drag and drop)

3. **Navigate to** your dumped game folder:
   ```
   CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/
   ```

4. **Select one song bundle** to analyze first:
   - Choose `100bills` (8.4 MB) or any smaller song
   - Double-click to load

5. **Export Settings** (in AssetRipper menu):
   ```
   [ ] Export Dependencies
   [ ] Exportable Properties
   [x] Audio Export: WAV
   [ ] Combine Asset Sets
   [ ] Include Used Assets Only
   [ ] Include Esoteric Assets
   [x] Dump Fern Flower
   ```

6. **Export to folder**:
   ```
   C:\\beat-saber-ps4\\extracted\\100bills\\
   ```

7. **Click Export** and wait for completion

## Step 1.2: Analyze Extracted Structure

After export, check the extracted folder for:

### Expected Files:
```
100bills/
├── LevelInfo/                    (or similar - metadata)
│   └── *.dat, *.json, *.bytes   (serialized data)
├── Audio/
│   └── *.wav, *.ogg             (audio file)
├── Cover/
│   └── *.png, *.jpg             (cover image)
├── Beatmaps/                     (difficulty files)
│   └── *.dat, *.bytes           (note timing)
└── Other/                        (textures, materials, etc.)
```

### Important: Look for these Unity types:
- `LevelInfo` - Song metadata (name, BPM, author)
- `BeatmapData` - Note/block timing and positions
- `AudioClip` - Audio file (check what format)
- `Sprite` or `Texture2D` - Cover image

## Step 1.3: Document What You Find

**Tell me what you see!** I need to know:
1. What file types were exported?
2. What are the exact Unity class names?
3. Is the audio WAV, OGG, or something else?
4. What does the beatmap data look like?

---

# PHASE 2: Download Custom Songs (PC Format)

## Step 2.1: Download Popular Songs

1. **Go to**: https://beatsaver.com

2. **Search for popular songs**:
   - "Crystallized" by S辣的
   - "Crab Rave" by acrispy
   - "Believer" by Routers
   - "Bad Guy" by Hex
   - "Blinding Lights" by M展位
   - "100 Bills Remix" by Elliot
   - Or browse "Top Rated" / "Most Downloaded"

3. **Download ZIP** for each song:
   - Click song > Download button > "Download Zip"

4. **Extract each ZIP** to:
   ```
   C:\\beat-saber-ps4\\songs\\
   ```

5. **Expected structure** (PC format):
   ```
   songs/
   ├── crystallized/
   │   ├── info.dat
   │   ├── Easy.dat
   │   ├── Normal.dat
   │   ├── Hard.dat
   │   ├── Expert.dat
   │   ├── ExpertPlus.dat
   │   ├── song.ogg
   │   └── cover.jpg
   ├── crabrave/
   │   └── ...
   ```

---

# PHASE 3: Convert PC Songs to PS4 Format

(This step I can help with once we know the exact PS4 format)

## Step 3.1: Wait for Format Analysis

After Phase 1, tell me:
- What Unity classes are used?
- What audio format?
- What beatmap structure?

I will then create the conversion script.

---

# PHASE 4: Build PS4 PKG

## Step 4.1: Download FPKG Tools

1. **Go to**: https://github.com/CyB1K/PS4-Fake-PKG-Tools-3.87/releases/tag/v7

2. **Download**: `PS4-Fake-PKG-Tools-3.87.7z`

3. **Extract** to:
   ```
   C:\\beat-saber-ps4\\tools\\FPKG-Tools\\
   ```

4. **Contents**:
   ```
   FPKG-Tools/
   ├── orbis-pub-sfo.exe     (Create PARAM.SFO)
   ├── orbis-pub-gen.exe     (Build PKG)
   └── ...
   ```

## Step 4.2: Download psDLC (Unlocker)

1. **Go to**: https://github.com/codemasterv/psDLC-2.1-stooged-Mogi-PPSA-gui/releases

2. **Download** the latest release (psDLC.zip)

3. **Extract** to:
   ```
   C:\\beat-saber-ps4\\tools\\psDLC\\
   ```

## Step 4.3: Create PARAM.SFO (DLC Metadata)

1. **Open** `orbis-pub-sfo.exe`

2. **Category**: Select `(PS4) Additional Content`

3. **Content ID**:
   ```
   UP8802-CUSA12878_00-BSCUSTOMSONGS
   ```
   (Last 7 digits can be anything, e.g., `BSCUSTOMPACK01`)

4. **Title**:
   ```
   Beat Saber Custom Songs
   ```

5. **Save As**: Navigate to your DLC folder:
   ```
   C:\\beat-saber-ps4\\output\\dlc_package\\sce_sys\\param.sfo
   ```

## Step 4.4: Create DLC Package Structure

Create this folder structure:
```
C:\\beat-saber-ps4\\output\\dlc_package\\
├── sce_sys/
│   └── param.sfo              (from Step 4.3)
└── StreamingAssets/
    ├── BeatmapLevelsData/     (converted beatmaps)
    └── HmxAudioAssets/
        └── songs/             (converted audio)
```

## Step 4.5: Build PKG with orbis-pub-gen.exe

1. **Open** `orbis-pub-gen.exe`

2. **File > New Project > Additional Content Package with Extra Data**

3. **Drag folders** to Image0:
   - Drag `sce_sys` folder
   - Drag `StreamingAssets` folder

4. **Click Project Settings** (or Command > Project Settings)

5. **Package Tab**:
   - **Content ID**: `UP8802-CUSA12878_00-BSCUSTOMSONGS01`
   - **Passcode**: `00000000000000000000000000000000` (32 zeros)

6. **Click OK**

7. **Build**:
   - Click Build
   - Check "Skip digest"
   - Select save location
   - Click Build again

8. **Output**: `UP8802-CUSA12878_00-BSCUSTOMSONGS01.pkg`

## Step 4.6: Create Unlocker PKG

1. **Open** `psDLC.exe`

2. **Select Manual Input tab**

3. **Content ID**: Same as above:
   ```
   UP8802-CUSA12878_00-BSCUSTOMSONGS01
   ```

4. **Click Create FPKG**

5. **Output**: `fake_dlc_pkg/UP8802-CUSA12878_00-BSCUSTOMSONGS01-A0000-V0100.pkg`

6. **Rename** to:
   ```
   UP8802-CUSA12878_00-BSCUSTOMSONGS01-unlock.pkg
   ```

---

# PHASE 5: Install on PS4

## Step 5.1: Prepare USB Drive

1. **Format USB** as FAT32

2. **Copy both PKG files** to root:
   ```
   F:/
   ├── UP8802-CUSA12878_00-BSCUSTOMSONGS01.pkg
   └── UP8802-CUSA12878_00-BSCUSTOMSONGS01-unlock.pkg
   ```

## Step 5.2: Install on PS4

1. **Connect USB** to PS4

2. **Launch GoldHEN**

3. **Game > Install Package > / Packages**

4. **Install unlocker FIRST**:
   - Select `*-unlock.pkg`
   - Confirm installation

5. **Install DLC SECOND**:
   - Select `*.pkg` (non-unlock)
   - Confirm installation

6. **Launch Beat Saber**

7. **Check Extras** or song list for new songs

---

# TROUBLESHOOTING

## "PKG won't install"
- Make sure PS4 is jailbroken
- Content ID must match game (CUSA12878)
- Unlocker must be installed FIRST

## "Songs don't appear"
- Songs may be in "Extras" category
- Check if audio format is correct
- Beatmaps may need conversion

## "Audio issues"
- PS4 may require specific audio format
- Try converting to WAV
- Check Unity audio import settings

## "Game crashes"
- Wrong Unity version for asset bundles
- Audio format incompatible
- Beatmap data corrupted

---

# QUICK REFERENCE

| Item | Value |
|------|-------|
| Game ID | CUSA12878 |
| Title | Beat Saber |
| Content ID Format | UP8802-CUSA12878_00-XXXXXXXX |
| DLC Folder | StreamingAssets/ |
| Audio Folder | HmxAudioAssets/songs/ |
| Beatmap Folder | BeatmapLevelsData/ |
| Unity Version | 2018.1.6f1 |
"""
    with open(OUTPUT_DIR / "COMPLETE_STEP_BY_STEP_GUIDE.md", "w") as f:
        f.write(guide)
    print("Created: COMPLETE_STEP_BY_STEP_GUIDE.md")

def create_assetripper_config():
    """Create AssetRipper config for Beat Saber"""
    config = """# AssetRipper Configuration for Beat Saber

## Export Settings
- [ ] Mesh export: NO
- [x] Audio export: WAV  
- [x] Texture export: PNG
- [ ] Script export: NO (causes errors)
- [ ] Shader export: NO

## Export Options
- [x] Dump Fern Flower (for better decompilation)
- [ ] Export Dependencies
- [ ] Exportable Properties
- [ ] Combine Asset Sets
- [ ] Include Used Assets Only

## Workflow
1. Open AssetRipper
2. File > Open Files
3. Navigate to: BeatmapLevelsData/100bills
4. Set export settings above
5. Export to: extracted/100bills/
6. Analyze structure
"""
    with open(OUTPUT_DIR / "ASSETRIPPER_CONFIG.txt", "w") as f:
        f.write(config)
    print("Created: extracted/ASSETRIPPER_CONFIG.txt")

def create_song_download_helper():
    """Create list of top songs with direct links if available"""
    songs = """# Top 10 Songs to Download

## From beatsaver.com

1. **Crystallized** by S辣的
   - Search: "Crystallized"
   - Mapper: S辣的
   - BPM: 175
   - Difficulty: Expert+

2. **Crab Rave** by acrispy
   - Search: "Crab Rave"
   - Mapper: acrispy
   - BPM: 128
   - Difficulty: Expert+

3. **Believer** by Routers  
   - Search: "Believer"
   - Mapper: Routers
   - BPM: 120
   - Difficulty: Expert

4. **Bad Guy** by Hex
   - Search: "Bad Guy"
   - Mapper: Hex
   - BPM: 135
   - Difficulty: Expert+

5. **Blinding Lights** by M展位
   - Search: "Blinding Lights"
   - Mapper: M展位
   - BPM: 171
   - Difficulty: Expert+

6. **100 Bills Remix** by Elliot
   - Search: "100 Bills Remix"
   - Mapper: Elliot
   - BPM: 175
   - Difficulty: Expert+

7. **Beloved** by Manon
   - Search: "Beloved"
   - Mapper: Manon
   - BPM: 130
   - Difficulty: Expert+

8. **About Damn Time** by Benzel
   - Search: "About Damn Time"
   - Mapper: Benzel
   - BPM: 146
   - Difficulty: Expert+

9. **Abracadabra** by Sot
   - Search: "Abracadabra"
   - Mapper: Sot
   - BPM: 140
   - Difficulty: Expert+

10. **Accelerate** by Checkthebpm
    - Search: "Accelerate"
    - Mapper: Checkthebpm
    - BPM: 175
    - Difficulty: Expert+

## Download Instructions

1. Go to: https://beatsaver.com
2. Search for song name or mapper
3. Click on the song
4. Click "Download Zip" button
5. Extract to: C:\\beat-saber-ps4\\songs\\
6. Repeat for each song

## Expected Folder Structure

```
songs/
├── crystallized/
│   ├── info.dat
│   ├── Easy.dat
│   ├── Normal.dat
│   ├── Hard.dat
│   ├── Expert.dat
│   ├── ExpertPlus.dat
│   ├── song.ogg
│   └── cover.jpg
├── crabrave/
│   └── ...
```
"""
    with open(TOOLS_DIR / "SONGS_LIST.md", "w") as f:
        f.write(songs)
    print("Created: tools/SONGS_LIST.md")

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("PREPARING COMPLETE GUIDE FOR WINDOWS")
    print("=" * 60)

    analyze_bundle_format()
    extract_bundle_metadata()
    create_complete_step_by_step_guide()
    create_assetripper_config()
    create_song_download_helper()

    print("\n" + "=" * 60)
    print("ALL FILES READY")
    print("=" * 60)
    print("""
Files created:
- extracted/COMPLETE_STEP_BY_STEP_GUIDE.md (main guide)
- extracted/ASSETRIPPER_CONFIG.txt (AssetRipper settings)
- tools/SONGS_LIST.md (songs to download)

YOUR NEXT STEP:
1. Read COMPLETE_STEP_BY_STEP_GUIDE.md
2. Start with PHASE 1 (AssetRipper analysis)
3. Extract 100bills song bundle
4. Tell me what structure you find
5. I'll create the conversion scripts based on your findings
""")

if __name__ == "__main__":
    main()