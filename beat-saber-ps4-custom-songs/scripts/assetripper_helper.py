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
    print(f"  Avg: {sum(sizes)//len(sizes):,} bytes ({sum(sizes)//len(sizes)/1024/1024:.1f} MB)")

    # Analyze header
    print("\n--- Bundle Header Analysis ---")
    with open(bundles[0], 'rb') as f:
        header = f.read(64)
    
    print(f"Magic: {header[:8].hex()}")
    print(f"First 64 bytes: {header.hex()}")

    # Parse Unity FS header
    print("\nUnity FS Header Parse:")
    if header[:6] == b'UnityF':
        print("  Format: UnityFS (Serialized File)")
        version = struct.unpack('<I', header[6:10])[0]
        print(f"  Version field: {version}")
        
        # Try different interpretations
        if version == 83:
            print("  -> Unity 2018.x format detected")
        
        # Check compressed size
        f.seek(0, 2)
        total_size = f.tell()
        print(f"  Total bundle size: {total_size:,} bytes")

    return bundles

def extract_bundle_metadata():
    """Try to extract metadata from bundles without full extraction"""
    print("\n" + "=" * 60)
    print("BUNDLE METADATA EXTRACTION")
    print("=" * 60)

    bundles_dir = PS4_DATA / "BeatmapLevelsData"
    
    # Sample a few bundles
    samples = list(bundles_dir.glob("*"))[:3]

    for bundle in samples:
        print(f"\n--- {bundle.name} ---")
        
        with open(bundle, 'rb') as f:
            # Read header
            header = f.read(256)
            
            # Look for readable strings
            text_regions = []
            current_text = []
            
            for byte in header:
                if 32 <= byte <= 126:  # Printable ASCII
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

def create_assetripper_config():
    """Create AssetRipper config for Beat Saber"""
    config = """
# AssetRipper Configuration for Beat Saber

## Export Settings
- Mesh export: NO
- Audio export: WAV
- Texture export: PNG  
- Script export: NO
- Shader export: NO

## Recommended Workflow
1. Open AssetRipper
2. File > Open Files
3. Select: `BeatmapLevelsData/100bills`
4. Export to: `extracted/100bills/`
5. Repeat for other songs

## What to Look For
After export, check for:
- `LevelInfo` or `BeatmapLevelInfo` - Song metadata
- `AudioClip` - Audio data (check format)
- `BeatmapData` or `DifficultyBeatmap` - Note timing
- `Sprite` or `Texture2D` - Cover images

## Important Notes
- PS4 uses HMX audio format (Harman)
- Audio may need special conversion
- Beatmaps stored as binary custom format
- Level metadata as ScriptableObject

## Extracted Structure Example
```
100bills/
├── info.json           (LevelInfo)
├── audio/              (AudioClip)
├── covers/             (Sprites)
├── beatmaps/           (DifficultyBeatmap)
│   ├── Easy.dat
│   ├── Normal.dat
│   ├── Hard.dat
│   ├── Expert.dat
│   └── ExpertPlus.dat
└── preview/            (Preview audio)
```
"""
    with open(OUTPUT_DIR / "ASSETRIPPER_CONFIG.txt", "w") as f:
        f.write(config)
    print("\nCreated: extracted/ASSETRIPPER_CONFIG.txt")

def download_tools():
    """Create download commands for remaining tools"""
    tools_info = """
# Tool Downloads

## FPKG Tools 3.87 (Correct URL)
URL: https://github.com/CyB1K/PS4-Fake-PKG-Tools-3.87/releases/tag/v7
File: PS4-Fake-PKG-Tools-3.87.7z
Save to: tools/FPKG-Tools/

## psDLC (Correct URL)
URL: https://github.com/codemasterv/psDLC-2.1-stooged-Mogi-PPSA-gui/releases
File: psDLC.zip or similar
Save to: tools/psDLC/

## Download Commands
```bash
# FPKG Tools
wget https://github.com/CyB1K/PS4-Fake-PKG-Tools-3.87/releases/download/v7/PS4-Fake-PKG-Tools-3.87.7z

# psDLC  
wget https://github.com/codemasterv/psDLC-2.1-stooged-Mogi-PPSA-gui/releases/download/latest/PsDLC.zip
```

## After Download
1. Extract FPKG Tools to: tools/FPKG-Tools/
2. Extract psDLC to: tools/psDLC/
3. Use orbis-pub-sfo.exe for PARAM.SFO
4. Use orbis-pub-gen.exe for PKG building
5. Use psDLC for unlocker
"""
    with open(TOOLS_DIR / "TOOL_DOWNLOADS.md", "w") as f:
        f.write(tools_info)
    print("Created: tools/TOOL_DOWNLOADS.md")

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("ASSETRIPPER HELPER FOR BEAT SABER PS4")
    print("=" * 60)

    # Analyze bundles
    bundles = analyze_bundle_format()

    # Extract metadata
    extract_bundle_metadata()

    # Create configs
    create_assetripper_config()
    download_tools()

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print("""
Next Steps:
1. Open AssetRipper on your Windows PC
2. Load: BeatmapLevelsData/100bills
3. Export to: extracted/100bills/
4. Analyze the exported structure
5. Tell me what you find so I can complete the conversion scripts
""")

if __name__ == "__main__":
    main()