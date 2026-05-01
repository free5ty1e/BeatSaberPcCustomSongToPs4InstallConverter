#!/usr/bin/env python3
"""
Beat Saber PS4 AssetBundle Tool
==============================
This script provides utilities for working with Beat Saber level data.
Requires Unity 2022.3 to be installed for actual AssetBundle creation.

Usage:
    python3 beatsaber_asset_tool.py <command> [options]

Commands:
    analyze     - Analyze a Beat Saber AssetBundle
    template    - Generate a custom level template
    convert     - Convert BS+ format to Beat Saber PS4 format
    verify      - Verify a custom level is compatible
"""

import struct
import os
import sys
import json
import argparse
from pathlib import Path

# Unity type IDs (partial list for Beat Saber levels)
UNITY_TYPE_IDS = {
    0x01: "GameObject",
    0x02: "Component",
    0x04: "MonoBehaviour",
    0x05: "Transform",
    0x1C: "AudioClip",
    0x1D: "AudioSource",
    0x23: "Material",
    0x30: "Texture2D",
    0x31: "Shader",
    0x32: "TextAsset",
    0x33: "Behaviour",
    0x44: "Sprite",
    0x57: "Texture",
    0x6C: "Cubemap",
    0x72: "AnimationClip",
    0x74: "AnimationCurve",
    0x75: "Keyframe",
    0x7D: "MonoScript",
    0x7E: "MonoAssembly",
    0x7F: "EditorExtension",
}

# Beat Saber specific types
BEATSABER_TYPES = {
    "BeatmapLevelData": 0x80000000 | 0x1234,  # Placeholder
    "BeatmapData": 0x80000000 | 0x1235,
    "DifficultyBeatmap": 0x80000000 | 0x1236,
    "AudioClip": 0x1C,
    "Texture2D": 0x30,
    "Sprite": 0x44,
}

# Level metadata structure
LEVEL_METADATA = {
    "levelId": "",
    "levelName": "",
    "songName": "",
    "songSubName": "",
    "songAuthorName": "",
    "levelAuthorName": "",
    "beatsPerMinute": 120.0,
    "songTimeOffset": 0.0,
    "shuffle": 0.0,
    "shufflePeriod": 0.0,
    "previewDuration": 30.0,
    "coverImageFilename": "",
    "difficultyBeatmaps": []
}

DIFFICULTY_TEMPLATE = {
    "difficulty": "Easy",
    "difficultyRank": 1,
    "noteJumpMovementSpeed": 10.0,
    "noteJumpStartBeatTime": 0.0,
    "beatmapFilename": "Easy.dat",
    "colorScheme": {
        "colorA": [1.0, 0.0, 0.0, 1.0],
        "colorB": [0.0, 0.0, 1.0, 1.0]
    },
    "environmentColourScheme": {
        "environmentColor0": [0.0, 1.0, 0.0, 1.0],
        "environmentColor1": [1.0, 1.0, 0.0, 1.0]
    }
}


def analyze_assetbundle(path):
    """Analyze a Beat Saber AssetBundle file."""
    
    if not os.path.exists(path):
        print(f"Error: File not found: {path}")
        return None
    
    with open(path, 'rb') as f:
        data = f.read()
    
    print(f"\n=== AssetBundle Analysis: {os.path.basename(path)} ===")
    print(f"File size: {len(data):,} bytes\n")
    
    # Check header
    # UnityFS magic is bytes 0-6, with possible null at 6
    if data[:6] == b'UnityF' or data[:7] == b'UnityFS' or data[:7].startswith(b'UnityF'):
        print("Format: UnityFS")
        
        # Parse Unity version
        # Unity version string starts at offset 16 (32-byte aligned)
        unity_version = data[16:32].rstrip(b'\x00').decode('ascii', errors='replace')
        print(f"Unity Version: {unity_version}")
        
        # Flags at offset 8
        flags = struct.unpack('<I', data[8:12])[0]
        print(f"Flags: 0x{flags:08x}")
        
        # Compression type
        # Note: Unity 2022.3 uses LZ4HAM which may show as 0 in flags
        compression = flags & 0x3F
        print(f"Compression: {compression}", end="")
        if compression == 0:
            # LZ4HAM often shows as 0 in Unity 2022.3
            print(" (LZ4HAM compressed - requires Unity 2022.3 to decompress)")
        elif compression == 1:
            print(" (stored/uncompressed)")
        elif compression == 1:
            print(" (LZ4)")
        elif compression == 2:
            print(" (LZ4HC)")
        elif compression == 4:
            print(" (LZ4HAM)")
        else:
            print(f" (unknown)")
        
        # Check for CAB ID
        cab_offset = data.find(b'CAB-')
        if cab_offset > 0:
            cab_id = data[cab_offset:cab_offset+32].split(b'\x00')[0].decode('ascii')
            print(f"CAB ID: {cab_id}")
        
        # Search for embedded strings
        print("\n--- Embedded Strings ---")
        strings = extract_strings(data)
        meaningful = [s for s in strings if any(p in s.lower() for p in 
            ['beat', 'saber', 'level', 'song', 'note', 'audio', 'easy', 'hard'])]
        print(f"Found {len(meaningful)} relevant strings:")
        for s in meaningful[:50]:
            print(f"  {s}")
        
        return {
            'unity_version': unity_version,
            'flags': flags,
            'compression': compression,
            'strings': strings
        }
    else:
        print("Unknown format")
        return None


def extract_strings(data, min_length=4):
    """Extract ASCII strings from binary data."""
    strings = []
    current = b''
    
    for byte in data:
        if 32 <= byte < 127:
            current += bytes([byte])
        else:
            if len(current) >= min_length:
                try:
                    strings.append(current.decode('ascii'))
                except:
                    pass
            current = b''
    
    return strings


def generate_level_template(output_dir=None, level_id="custom_mysong"):
    """Generate a template for a custom Beat Saber level."""
    
    if output_dir is None:
        output_dir = Path.cwd() / "output"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create level metadata JSON
    level_data = {
        **LEVEL_METADATA,
        "levelId": level_id,
        "levelName": "Custom Song",
        "songName": "My Custom Song",
        "songAuthorName": "Artist Name",
        "levelAuthorName": "Mapper Name",
        "beatsPerMinute": 120.0,
        "difficultyBeatmaps": [
            {**DIFFICULTY_TEMPLATE, "difficulty": "Easy", "difficultyRank": 1},
            {**DIFFICULTY_TEMPLATE, "difficulty": "Normal", "difficultyRank": 3},
            {**DIFFICULTY_TEMPLATE, "difficulty": "Hard", "difficultyRank": 5},
            {**DIFFICULTY_TEMPLATE, "difficulty": "Expert", "difficultyRank": 7},
            {**DIFFICULTY_TEMPLATE, "difficulty": "ExpertPlus", "difficultyRank": 9},
        ]
    }
    
    # Save metadata
    metadata_path = output_dir / f"{level_id}_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(level_data, f, indent=2)
    
    print(f"Created level template: {metadata_path}")
    
    # Create beatmap templates for each difficulty
    for diff in ["Easy", "Normal", "Hard", "Expert", "ExpertPlus"]:
        beatmap = generate_beatmap_template(diff, level_data['beatsPerMinute'])
        beatmap_path = output_dir / f"{level_id}_{diff}.dat"
        with open(beatmap_path, 'w') as f:
            json.dump(beatmap, f, indent=2)
        print(f"Created beatmap template: {beatmap_path}")
    
    # Create README
    readme = f"""# Custom Level: {level_id}

## Files Needed

1. `{level_id}_metadata.json` - Level metadata (edit this)
2. `{level_id}_Easy.dat` through `{level_id}_ExpertPlus.dat` - Beatmap data
3. `audio.ogg` - Song audio (320kbps OGG format)
4. `cover.png` - Cover image (512x512 PNG)

## Metadata Fields

| Field | Description | Example |
|-------|-------------|---------|
| levelId | Unique identifier | {level_id} |
| levelName | Display name | My Custom Song |
| songName | Song title | My Custom Song |
| songAuthorName | Artist | Artist Name |
| levelAuthorName | Mapper | Mapper Name |
| beatsPerMinute | BPM | 120.0 |
| previewDuration | Preview length (sec) | 30.0 |

## Difficulty Settings

| Difficulty | Rank | NJMS | Notes |
|------------|------|------|-------|
| Easy | 1 | 10 | Beginner |
| Normal | 3 | 12 | Medium |
| Hard | 5 | 14 | Hard |
| Expert | 7 | 16 | Expert |
| ExpertPlus | 9 | 18 | Expert+ |

## Next Steps

1. Edit the metadata JSON
2. Create beatmap data (use Beat Saber Editor or tools)
3. Add audio and cover art
4. Use Unity 2022.3 to package into AssetBundle
5. Test with the plugin
"""
    
    readme_path = output_dir / f"{level_id}_README.md"
    with open(readme_path, 'w') as f:
        f.write(readme)
    
    print(f"Created README: {readme_path}")
    print(f"\nTemplate created in: {output_dir}")


def generate_beatmap_template(difficulty, bpm):
    """Generate a basic beatmap template."""
    
    # Beatmap data format based on Beat Saber
    return {
        "version": "2.0.0",
        "BPM": bpm,
        "notes": [
            # Example: [time, lineIndex (0-3), lineLayer (0-2), type (0=red, 1=blue), cutDirection]
            {"b": 0.0, "x": 0, "y": 0, "c": 0, "d": 1},  # Red note, left
            {"b": 0.5, "x": 3, "y": 0, "c": 1, "d": 2},  # Blue note, right
            {"b": 1.0, "x": 1, "y": 0, "c": 0, "d": 4},  # Red note, down
            {"b": 1.5, "x": 2, "y": 0, "c": 1, "d": 8},  # Blue note, up
        ],
        "obstacles": [
            # Example: [time, duration, x, y, width, height]
            {"b": 2.0, "d": 1.0, "x": 0, "y": 0, "w": 1, "h": 3},
        ],
        "events": [
            # Example: [time, type, value]
            {"b": 0.0, "et": 0, "i": 0},
        ]
    }


def verify_level(path):
    """Verify a custom level is properly formatted."""
    
    print(f"\n=== Level Verification: {os.path.basename(path)} ===")
    
    issues = []
    warnings = []
    
    # Check if metadata exists
    metadata_path = Path(path).parent / f"{Path(path).stem}_metadata.json"
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        print("✓ Metadata file found")
        
        # Check required fields
        required = ["levelId", "levelName", "songName", "beatsPerMinute"]
        for field in required:
            if field in metadata:
                print(f"  ✓ {field}: {metadata[field]}")
            else:
                issues.append(f"Missing required field: {field}")
    else:
        warnings.append("No metadata file found")
    
    # Check for beatmap files
    level_dir = Path(path).parent
    beatmaps = list(level_dir.glob("*Easy*.json")) + list(level_dir.glob("*Normal*.json"))
    if beatmaps:
        print(f"✓ Found {len(beatmaps)} beatmap files")
    else:
        warnings.append("No beatmap files found")
    
    # Check for audio
    if (level_dir / "audio.ogg").exists():
        print("✓ Audio file found")
    else:
        warnings.append("No audio file (audio.ogg)")
    
    # Check for cover
    if (level_dir / "cover.png").exists():
        print("✓ Cover image found")
    else:
        warnings.append("No cover image (cover.png)")
    
    # Report
    print(f"\n=== Results ===")
    if issues:
        print("ISSUES:")
        for issue in issues:
            print(f"  ✗ {issue}")
    if warnings:
        print("WARNINGS:")
        for warning in warnings:
            print(f"  ! {warning}")
    if not issues and not warnings:
        print("✓ Level appears valid")
    
    return len(issues) == 0


def main():
    parser = argparse.ArgumentParser(
        description="Beat Saber PS4 AssetBundle Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 beatsaber_asset_tool.py analyze /path/to/beatsaber
    python3 beatsaber_asset_tool.py template --level-id mysong
    python3 beatsaber_asset_tool.py verify /path/to/level
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze an AssetBundle')
    analyze_parser.add_argument('path', help='Path to AssetBundle file')
    
    # Template command
    template_parser = subparsers.add_parser('template', help='Generate level template')
    template_parser.add_argument('--output', '-o', help='Output directory')
    template_parser.add_argument('--level-id', help='Level ID')
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify a level')
    verify_parser.add_argument('path', help='Path to level directory or file')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert BS+ format')
    convert_parser.add_argument('input', help='Input BS+ level directory')
    convert_parser.add_argument('--output', '-o', help='Output directory')
    
    args = parser.parse_args()
    
    if args.command == 'analyze':
        analyze_assetbundle(args.path)
    elif args.command == 'template':
        generate_level_template(args.output, args.level_id or "custom_song")
    elif args.command == 'verify':
        verify_level(args.path)
    elif args.command == 'convert':
        print("Convert command requires BS+ level format - not yet implemented")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
