#!/usr/bin/env python3
"""
Beat Saber PS4 Song Replacer
============================
Replaces songs in Beat Saber PS4 level data.
No plugin or PS4 debugging required!

Usage:
    python3 song_replacer.py add <source_ogg> <level_id>
    python3 song_replacer.py list
    python3 song_replacer.py info <level_id>
"""

import os
import sys
import struct
import json
import argparse
import shutil
from pathlib import Path

# Paths
DUMP_PATH = Path("/workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData")
OUTPUT_PATH = Path("/workspace/beat-saber-ps4-custom-songs/modded_levels")

# Beat Saber level metadata template
LEVEL_METADATA = {
    "_levelID": "",
    "_songName": "",
    "_songSubName": "",
    "_songAuthorName": "",
    "_levelAuthorName": "",
    "_beatsPerMinute": 120.0,
    "_songTimeOffset": 0.0,
    "_shuffle": 0.0,
    "_shufflePeriod": 0.5,
    "_previewDuration": 30.0,
    "_environmentName": "DefaultEnvironment",
    "_allDirectionsEnvironmentName": "GlassDesert",
    "_difficultyBeatmapSets": [],
    "_difficultyBeatmaps": []
}

DIFFICULTY_NAMES = {
    1: "Easy",
    3: "Normal",
    5: "Hard",
    7: "Expert",
    9: "ExpertPlus"
}

DIFFICULTY_COLORS = {
    "Easy": {"colorA": [1.0, 0.0, 0.5, 1.0], "colorB": [0.0, 1.0, 0.5, 1.0]},
    "Normal": {"colorA": [1.0, 0.5, 0.0, 1.0], "colorB": [0.0, 0.5, 1.0, 1.0]},
    "Hard": {"colorA": [1.0, 0.0, 0.0, 1.0], "colorB": [0.0, 0.0, 1.0, 1.0]},
    "Expert": {"colorA": [1.0, 0.0, 1.0, 1.0], "colorB": [1.0, 1.0, 0.0, 1.0]},
    "ExpertPlus": {"colorA": [1.0, 0.3, 0.0, 1.0], "colorB": [0.0, 1.0, 1.0, 1.0]}
}


def ensure_dir(path):
    """Ensure directory exists."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_audio_info(ogg_path):
    """Get info about an audio file."""
    path = Path(ogg_path)
    if not path.exists():
        return None
    
    return {
        "filename": path.name,
        "size": path.stat().st_size,
        "size_mb": path.stat().st_size / 1024 / 1024
    }


def list_levels():
    """List all existing levels."""
    print("\n=== Available Levels ===\n")
    
    if not DUMP_PATH.exists():
        print(f"Level path not found: {DUMP_PATH}")
        return
    
    levels = sorted(DUMP_PATH.iterdir())
    print(f"Found {len(levels)} levels:\n")
    
    for level in levels:
        size = level.stat().st_size if level.is_file() else 0
        size_mb = size / 1024 / 1024
        print(f"  {level.name:30} {size_mb:>6.2f} MB")
    
    print()


def show_level_info(level_id):
    """Show info about a specific level."""
    level_path = DUMP_PATH / level_id
    
    if not level_path.exists():
        print(f"Level not found: {level_id}")
        return
    
    size = level_path.stat().st_size if level_path.is_file() else 0
    print(f"\n=== Level: {level_id} ===")
    print(f"Path: {level_path}")
    print(f"Size: {size:,} bytes ({size/1024/1024:.2f} MB)")
    
    # Try to extract strings
    with open(level_path, 'rb') as f:
        data = f.read()
    
    # Extract readable strings
    strings = []
    current = b''
    for byte in data:
        if 32 <= byte < 127:
            current += bytes([byte])
        else:
            if len(current) >= 4:
                strings.append(current.decode('ascii'))
            current = b''
    
    # Filter for meaningful strings
    meaningful = [s for s in strings if len(s) > 3 and not s.startswith('-')]
    print(f"\nFound {len(meaningful)} readable strings")
    
    # Show sample
    if meaningful:
        print("\nSample strings:")
        for s in meaningful[:20]:
            print(f"  {s}")


def create_metadata_template(song_name, artist, bpm=120.0, level_id=None):
    """Create a metadata template for a new level."""
    
    if level_id is None:
        # Generate level ID from song name
        level_id = song_name.lower().replace(' ', '_').replace('-', '_')
    
    # Create difficulty beatmaps for all difficulties
    difficulty_beatmaps = []
    for rank, name in DIFFICULTY_NAMES.items():
        njms = {1: 10, 3: 12, 5: 14, 7: 16, 9: 18}[rank]
        colors = DIFFICULTY_COLORS[name]
        
        difficulty_beatmaps.append({
            "_difficulty": name,
            "_difficultyRank": rank,
            "_noteJumpMovementSpeed": njms,
            "_noteJumpStartBeatTime": 0.0,
            "_beatmapFilename": f"{name}.dat",
            "_colorScheme": {
                "_colorA": colors["colorA"],
                "_colorB": colors["colorB"]
            },
            "_environmentColourScheme": {
                "_overrideColorA": False,
                "_overrideColorB": False,
                "_colorA": [1.0, 1.0, 1.0, 1.0],
                "_colorB": [1.0, 1.0, 1.0, 1.0]
            }
        })
    
    metadata = {
        **LEVEL_METADATA,
        "_levelID": level_id,
        "_songName": song_name,
        "_songAuthorName": artist,
        "_levelAuthorName": "BeatSaberDX",
        "_beatsPerMinute": bpm,
        "_difficultyBeatmaps": difficulty_beatmaps
    }
    
    return metadata


def save_metadata_template(level_id, metadata):
    """Save metadata to a JSON file."""
    output_dir = ensure_dir(OUTPUT_PATH / level_id)
    metadata_file = output_dir / "metadata.json"
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Created metadata: {metadata_file}")
    return metadata_file


def plan_replacement(source_ogg, level_id):
    """Plan a song replacement - shows what would happen without modifying files."""
    
    if not Path(source_ogg).exists():
        print(f"Error: Audio file not found: {source_ogg}")
        return
    
    audio_info = get_audio_info(source_ogg)
    
    print(f"\n=== Replacement Plan ===\n")
    print(f"Source audio: {source_ogg}")
    print(f"  Size: {audio_info['size_mb']:.2f} MB")
    print(f"Target level ID: {level_id}")
    print()
    print("Steps required:")
    print("1. Copy 'beatsaber' level as template")
    print("2. Use UABEA to import new audio")
    print("3. Use UABEA to edit BeatSaberBeatmapLevelData fields")
    print("4. Add modified level to PKG")
    print()
    print("Note: This script provides guidance. Manual UABEA work is required")
    print("      because Unity AssetBundles require the Unity editor to modify.")
    print()
    print("See MANUAL_UNITY_WORKFLOW.md for detailed UABEA instructions.")


def create_replacement_guide(source_ogg, target_level_id):
    """Create a detailed guide for manual replacement."""
    
    output_dir = ensure_dir(OUTPUT_PATH / target_level_id)
    
    guide = f"""# Song Replacement Guide: {target_level_id}

## Audio File
- **Source:** {source_ogg}
- **Size:** {get_audio_info(source_ogg)['size_mb']:.2f} MB

## Steps

### Step 1: Copy Template Level
1. Copy `beatsaber` from your dump:
   ```
   Copy: CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/beatsaber
   To:   CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/{target_level_id}
   ```

### Step 2: Open in UABEA
1. Open UABEA
2. File → Open → Select `{target_level_id}`
3. You should see:
   - BeatSaberBeatmapLevelData
   - AudioClip
   - Other assets

### Step 3: Replace Audio
1. In left panel, click on **AudioClip**
2. In right panel, find **AudioClip Import** section
3. Click the import button
4. Select your audio file: `{Path(source_ogg).name}`
5. Click OK

### Step 4: Edit Level Metadata
1. In left panel, click on **BeatSaberBeatmapLevelData**
2. In right panel, expand the fields
3. Edit these values:
   - `_levelID`: `{target_level_id}`
   - `_songName`: Your Song Name
   - `_songAuthorName`: Artist Name
   - `_beatsPerMinute`: 120 (adjust to actual BPM)
   - `_previewDuration`: 30

### Step 5: Save AssetBundle
1. Click **File** → **Save**
2. Save the modified AssetBundle

### Step 6: Add to PKG
1. Add `{target_level_id}` to your project
2. Build PKG with PkgToolBox
3. Install on PS4

## Result
Your song will appear in the game automatically!
"""
    
    guide_file = output_dir / "REPLACEMENT_GUIDE.md"
    with open(guide_file, 'w') as f:
        f.write(guide)
    
    print(f"Created guide: {guide_file}")
    
    # Also create metadata template
    metadata = create_metadata_template(
        song_name="TODO: Song Name",
        artist="TODO: Artist Name",
        bpm=120.0,
        level_id=target_level_id
    )
    save_metadata_template(target_level_id, metadata)
    
    return guide_file


def main():
    parser = argparse.ArgumentParser(
        description="Beat Saber PS4 Song Replacer - No plugin needed!",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List levels
    list_parser = subparsers.add_parser('list', help='List available levels')
    
    # Show info
    info_parser = subparsers.add_parser('info', help='Show level info')
    info_parser.add_argument('level_id', help='Level ID to inspect')
    
    # Add new song
    add_parser = subparsers.add_parser('add', help='Plan/add a new song')
    add_parser.add_argument('source', help='Source OGG audio file')
    add_parser.add_argument('level_id', nargs='?', help='Level ID (optional)')
    
    # Create guide
    guide_parser = subparsers.add_parser('guide', help='Create replacement guide')
    guide_parser.add_argument('source', help='Source OGG audio file')
    guide_parser.add_argument('level_id', help='Target level ID')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_levels()
    elif args.command == 'info':
        show_level_info(args.level_id)
    elif args.command == 'add':
        # Generate level_id from audio filename if not provided
        level_id = args.level_id
        if level_id is None:
            audio_name = Path(args.source).stem
            level_id = audio_name.lower().replace(' ', '_').replace('-', '_')
        
        print(f"\n=== Adding Song: {args.source} ===")
        plan_replacement(args.source, level_id)
        
        # Offer to create guide
        response = input("\nCreate detailed UABEA guide? (y/n): ").strip().lower()
        if response == 'y':
            create_replacement_guide(args.source, level_id)
    elif args.command == 'guide':
        create_replacement_guide(args.source, args.level_id)
    else:
        parser.print_help()
        print("\n=== Quick Start ===")
        print("1. List available levels:")
        print("   python3 song_replacer.py list")
        print()
        print("2. Add a new song:")
        print("   python3 song_replacer.py add /path/to/song.ogg mysong")
        print()
        print("3. Get detailed guide:")
        print("   python3 song_replacer.py guide /path/to/song.ogg mysong")


if __name__ == '__main__':
    main()