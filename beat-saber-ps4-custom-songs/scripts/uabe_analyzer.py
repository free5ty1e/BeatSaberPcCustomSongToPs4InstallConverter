#!/usr/bin/env python3
"""
UABE Asset Bundle Analyzer
Analyzes PS4 Unity asset bundles to understand exact format needed
"""
import struct
import json
import os
import sys
from pathlib import Path

PS4_DATA = Path("/workspace/temp/DumpedPs4BeatSaber/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData")
UABE_DOWNLOAD = "https://github.com/AssetRipper/AssetRipper/releases/download/0.2.0.0-alpha/AssetRipper_0.2.0.0-alpha.zip"

class UABEAnalyzer:
    def __init__(self):
        self.bundle_magic = b'UnityF'  # Unity FS (Serialized File)

    def analyze_bundles(self):
        """Analyze all PS4 song bundles"""
        print("=" * 60)
        print("UABE PS4 ASSET BUNDLE ANALYSIS")
        print("=" * 60)

        bundles = list(PS4_DATA.glob("*"))
        print(f"\nFound {len(bundles)} asset bundles")

        if len(bundles) == 0:
            print("No bundles found!")
            return

        # Analyze first few bundles
        sample_size = min(3, len(bundles))
        print(f"\nAnalyzing {sample_size} sample bundles...\n")

        for i, bundle_path in enumerate(bundles[:sample_size]):
            self.analyze_bundle(bundle_path)

        # Try to extract one bundle for format study
        self.extract_sample_bundle(bundles[0])

    def analyze_bundle(self, bundle_path):
        """Analyze a single bundle"""
        print(f"\n--- {bundle_path.name} ---")

        with open(bundle_path, 'rb') as f:
            header = f.read(32)

        # Check magic
        magic = header[:6]
        print(f"Magic: {magic}")

        if magic == self.bundle_magic:
            print("Type: Unity FS (Serialized File)")

            # Parse header
            try:
                version = struct.unpack('<I', header[6:10])[0]
                print(f"Version: {version}")

                # Version-specific parsing
                if version >= 6:
                    # Unity 2017+
                    flags = struct.unpack('<I', header[10:14])[0]
                    print(f"Flags: {flags:#x}")
            except:
                pass

            # Calculate file size
            file_size = bundle_path.stat().st_size
            print(f"File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")

        else:
            print(f"Unknown format: {magic.hex()}")

    def extract_sample_bundle(self, bundle_path):
        """Extract a sample bundle using UABE or manual parsing"""
        print(f"\n--- EXTRACTION PREP for {bundle_path.name} ---")
        print(f"""
To extract and analyze this bundle:

1. Download UABE (AssetRipper):
   {UABE_DOWNLOAD}

2. Open AssetRipper and load: {bundle_path}

3. Export to: /workspace/beat-saber-ps4-custom-songs/extracted/

4. Analyze the exported Unity assets to understand:
   - AudioClip format (FMOD/HMX?)
   - Sprite/Texture format for covers
   - Custom class serialization

For PS4 Beat Saber:
- Audio must be in HMX (Harman) format
- Beatmaps stored as custom ScriptableObjects
- Level info as serialized JSON-like binary
""")

    def create_extraction_guide(self):
        """Create detailed extraction guide"""
        guide = """
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
"""
        with open("/workspace/beat-saber-ps4-custom-songs/EXTRACTION_GUIDE.md", "w") as f:
            f.write(guide)
        print("\nCreated: EXTRACTION_GUIDE.md")

def main():
    analyzer = UABEAnalyzer()
    analyzer.analyze_bundles()
    analyzer.create_extraction_guide()

if __name__ == "__main__":
    main()