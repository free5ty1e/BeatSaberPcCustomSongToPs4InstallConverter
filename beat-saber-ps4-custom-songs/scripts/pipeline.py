#!/usr/bin/env python3
"""
Beat Saber PS4 - CLI Pipeline
Usage: python3 scripts/pipeline.py <songs_folder> [--output <name>]

Examples:
  python3 scripts/pipeline.py songs_repo/                    # Build all 94 songs
  python3 scripts/pipeline.py songs_test/ --output test.pkg   # Build specific folder
"""
import sys
import shutil
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/pipeline.py <songs_folder> [--output <name>]")
        print("")
        print("Arguments:")
        print("  songs_folder   Folder containing downloaded BeatSaver songs")
        print("  --output    Optional output filename (default: custom_songs.pkg)")
        return
    
    songs_dir = Path(sys.argv[1])
    output_name = "custom_songs.pkg"
    
    # Parse args
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--output" and i + 1 < len(sys.argv):
            output_name = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    if not songs_dir.exists():
        print(f"Error: Folder not found: {songs_dir}")
        return
    
    # Create working songs folder
    WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
    work_songs = WORK_DIR / "songs"
    
    if work_songs.exists():
        shutil.rmtree(work_songs)
    work_songs.mkdir()
    
    # Copy songs
    songs = [d for d in songs_dir.iterdir() if d.is_dir()]
    print(f"Building PKG with {len(songs)} songs...")
    
    for s in songs:
        shutil.copytree(s, work_songs / s.name)
    
    # Build PKG
    from scripts.build_pkg import build_pkg
    build_pkg(work_songs, output_name)
    
    print("\n=== DONE ===")
    print(f"Output: {WORK_DIR / 'output' / output_name}")


if __name__ == "__main__":
    main()