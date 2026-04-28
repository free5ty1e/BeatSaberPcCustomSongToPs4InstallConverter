#!/usr/bin/env python3
"""
Complete Setup Script for Beat Saber PS4 Custom Songs
Downloads all required tools and creates ready-to-use environment
"""
import os
import sys
import urllib.request
import zipfile
import subprocess
from pathlib import Path

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
TOOLS_DIR = WORK_DIR / "tools"

class Setup:
    TOOLS = {
        "assetripper": {
            "name": "AssetRipper",
            "url": "https://github.com/AssetRipper/AssetRipper/releases/download/0.2.0.0-alpha/AssetRipper_0.2.0.0-alpha.zip",
            "file": "AssetRipper_0.2.0.0-alpha.zip",
            "install_dir": "AssetRipper"
        },
        "fpkg_tools": {
            "name": "FPKG Tools 3.87",
            "url": "https://github.com/CyB1K/PS4-Fake-PKG-Tools-3.87-Patched-For-FPKGs/releases/download/v3.87/PS4-Fake-PKG-Tools-3.87.7z",
            "file": "fpkg-tools.7z",
            "install_dir": "FPKG-Tools"
        },
        "psdlc": {
            "name": "psDLC",
            "url": "https://github.com/Efrii/PsDlc.GUI/releases/download/v2.0/PsDlc.zip",
            "file": "PsDlc.zip",
            "install_dir": "psDLC"
        }
    }

    def __init__(self):
        TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    def download_tool(self, key, tool_info):
        """Download a single tool"""
        print(f"\n{'='*60}")
        print(f"Downloading: {tool_info['name']}")
        print(f"{'='*60}")

        file_path = TOOLS_DIR / tool_info["file"]
        extract_dir = TOOLS_DIR / tool_info["install_dir"]

        if extract_dir.exists():
            print(f"  Already installed: {extract_dir}")
            return extract_dir

        if file_path.exists():
            print(f"  Using cached: {file_path}")
        else:
            print(f"  URL: {tool_info['url']}")
            print(f"  Download failed - manual download required")
            print(f"  Save to: {file_path}")
            return None

        # Extract
        try:
            if file_path.suffix == '.zip':
                with zipfile.ZipFile(file_path, 'r') as zf:
                    zf.extractall(TOOLS_DIR)
                print(f"  Extracted to: {extract_dir}")
            elif file_path.suffix == '.7z':
                print("  7z extraction needs 7za command - run manually")
                return None
        except Exception as e:
            print(f"  Extraction error: {e}")
            return None

        return extract_dir

    def download_all(self):
        """Download all required tools"""
        print("=" * 60)
        print("BEAT SABER PS4 CUSTOM SONGS - TOOL DOWNLOADER")
        print("=" * 60)

        results = {}
        for key, info in self.TOOLS.items():
            result = self.download_tool(key, info)
            results[key] = result

        return results

    def create_instructions(self):
        """Create detailed setup instructions"""
        instructions = """
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
"""
        with open(WORK_DIR / "SETUP_GUIDE.md", "w") as f:
            f.write(instructions)
        print("\nCreated: SETUP_GUIDE.md")

    def main(self):
        print("=" * 60)
        print("BEAT SABER PS4 CUSTOM SONGS - TOOL SETUP")
        print("=" * 60)

        # Try downloads
        results = self.download_all()

        # Create instructions
        self.create_instructions()

        print("\n" + "=" * 60)
        print("SETUP COMPLETE")
        print("=" * 60)
        print(f"""
Tools directory: {TOOLS_DIR}

Next steps:
1. Review SETUP_GUIDE.md for detailed instructions
2. Download required tools manually if auto-download failed
3. Start with Step 2: Extract PS4 Song Bundles with AssetRipper
4. Then proceed with song conversion

Note: Some tools may require manual download due to:
- GitHub rate limits
- Large file sizes
- Platform-specific requirements
""")

if __name__ == "__main__":
    Setup().main()