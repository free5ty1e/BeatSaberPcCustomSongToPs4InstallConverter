#!/usr/bin/env python3
"""
Beat Saber PS4 Custom Songs Pipeline Wrapper
=========================================
Generates both Python-built fPKGs and Windows-ready build folder.

Usage:
    python3 pipeline.py                    # Use defaults
    python3 pipeline.py --songs-path ./my_songs  # Custom songs folder
    python3 pipeline.py --clean             # Clean output first

Output:
    - output/custom_songs_v6.pkg      (Python-built DLC)
    - output/custom_unlocker_v3.pkg  (Python-built unlocker)
    - windows_build/                (Ready for orbis-pub-gen.exe)
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
DEFAULT_SONGS_REPO = WORK_DIR / "songs_repo"
DEFAULT_OUTPUT = WORK_DIR / "output"
DEFAULT_WINDOWS_BUILD = WORK_DIR / "windows_build"

# Default Content ID (matches working DLC format)
DEFAULT_CONTENT_ID = "UP4882-CUSA12878_00-P1S5XXXXXXXXXXXX"
DEFAULT_TITLE_ID = "CUSA12878"
DEFAULT_TITLE = "Custom Songs"

# ════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ════════════════════════════════════════════════════════════════════════════

def print_banner():
    banner = r"""
    ╔══════════════════════════════════════════════════════════════════╗
    ║   Beat Saber PS4 Custom Songs Pipeline                        ║
    ║   Generates fPKGs + Windows build folder                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_config(songs_path, output_path, windows_path, content_id):
    print("\n" + "═" * 60)
    print("CONFIGURATION")
    print("═" * 60)
    print(f"Songs folder:    {songs_path}")
    print(f"Output path:    {output_path}")
    print(f"Windows build:  {windows_path}")
    print(f"Content ID:   {content_id}")
    print(f"Title ID:     {DEFAULT_TITLE_ID}")
    print(f"Title:        {DEFAULT_TITLE}")
    print("═" * 60 + "\n")

def print_usage():
    print("""
USAGE:
    python3 pipeline.py [OPTIONS]

OPTIONS:
    --songs-path PATH    Songs folder (default: ./songs_repo)
    --output-path PATH  Output folder (default: ./output)  
    --content-id ID    Content ID (default: UP4882-CUSA12878_00-P1S5XXXXXXXXXXXX)
    --clean           Clean output before building
    --python-only     Only build Python fPKGs
    --windows-only   Only prepare Windows folder
    --help          Show this help

EXAMPLES:
    python3 pipeline.py                          # Default run
    python3 pipeline.py --clean                 # Clean + rebuild
    python3 pipeline.py --songs-path ./my_songs   # Custom songs folder
    python3 pipeline.py --python-only           # Just fPKGs
    python3 pipeline.py --windows-only       # Just Windows folder
""")

def build_python_pkg(songs_path, output_path, content_id):
    """Build Python fPKGs (DLC + unlocker)"""
    print("\n" + "─" * 40)
    print("BUILDING PYTHON fPKGs")
    print("─" * 40)
    
    # Run build script
    print("\n[1/2] Building custom songs DLC...")
    result = subprocess.run([
        "python3", 
        str(WORK_DIR / "scripts/build_pkg_v6.py")
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
        
    print(result.stdout)
    
    # Run unlocker script
    print("\n[2/2] Building unlocker...")
    result = subprocess.run([
        "python3",
        str(WORK_DIR / "scripts/create_unlocker_v3.py")
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
        
    print(result.stdout)
    
    return True

def prepare_windows_folder(songs_path, windows_path, content_id):
    """Prepare Windows build folder for orbis-pub-gen"""
    print("\n" + "─" * 40)
    print("PREPARING WINDOWS BUILD FOLDER")
    print("─" * 40)
    
    # Create folder structure
    app_folder = windows_path / "CUSA12878-app"
    sce_sys = app_folder / "sce_sys"
    
    # Clean if exists
    if windows_path.exists():
        print(f"Cleaning existing: {windows_path}")
        shutil.rmtree(windows_path)
    
    # Create directories
    sce_sys.mkdir(parents=True)
    (app_folder / "songs").mkdir(parents=True)
    
    # Copy files from reference
    ref_icon = WORK_DIR / "ref_extract/sce_sys/icon0.png"
    ref_sfo = WORK_DIR / "ref_extract/sce_sys/param.sfo"
    
    if ref_icon.exists():
        shutil.copy(ref_icon, sce_sys / "icon0.png")
        print(f"Copied: icon0.png")
    else:
        print("WARNING: icon0.png not found!")
        
    if ref_sfo.exists():
        shutil.copy(ref_sfo, sce_sys / "param.sfo")
        print(f"Copied: param.sfo")
    else:
        print("WARNING: param.sfo not found!")
    
    # Copy songs
    if songs_path.exists():
        song_count = 0
        for item in songs_path.iterdir():
            if item.is_dir():
                dest = app_folder / "songs" / item.name
                shutil.copytree(item, dest)
                song_count += 1
        print(f"Copied: {song_count} songs")
    else:
        print(f"WARNING: Songs folder not found: {songs_path}")
    
    # Create GP4 project
    gp4_content = f'''<?xml version="1.0" encoding="utf-8"?>
<psproject xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" fmt="gp4" version="1000">
  <volume>
    <volume_type>pkg_ps4_ac_data</volume_type>
    <volume_ts>2024-01-01 00:00:00</volume_ts>
    <package content_id="{content_id}" passcode="00000000000000000000000000000000" entitlement_key="00000000000000000000000000000000" c_date="2024-01-01" />
  </volume>
  <files img_no="0">
    <file targ_path="sce_sys/param.sfo" orig_path="sce_sys/param.sfo" />
    <file targ_path="sce_sys/icon0.png" orig_path="sce_sys/icon0.png" />
  </files>
  <rootdir>
    <dir targ_name="sce_sys" />
  </rootdir>
</psproject>'''
    
    gp4_path = windows_path / "Project.gp4"
    gp4_path.write_text(gp4_content)
    print(f"Created: Project.gp4")
    
    # Create instructions
    instructions = f'''# Beat Saber PS4 Custom Songs - Windows Build Guide

## Files

This folder contains {song_count} custom songs ready for orbis-pub-gen.exe.

## Build Steps

1. Run `orbis-pub-gen.exe` (from PS4 Fake PKG Tools 3.87)
2. Open `Project.gp4`
3. Press F5 to build
4. Save as `custom_songs.pkg`

## Content ID

{content_id}

## Notes

- Songs should be in `CUSA12878-app/songs/`
- System files in `CUSA12878-app/sce_sys/`
- Uses same format as working reference DLC
'''
    
    (windows_path / "INSTRUCTIONS.md").write_text(instructions)
    print(f"Created: INSTRUCTIONS.md")
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Beat Saber PS4 Custom Songs Pipeline",
        add_help=False
    )
    
    parser.add_argument('--songs-path', type=Path, default=DEFAULT_SONGS_REPO,
                        help='Songs folder to convert')
    parser.add_argument('--output-path', type=Path, default=DEFAULT_OUTPUT,
                        help='Output folder for fPKGs')
    parser.add_argument('--content-id', default=DEFAULT_CONTENT_ID,
                        help='Content ID (36 chars)')
    parser.add_argument('--clean', action='store_true',
                        help='Clean output before building')
    parser.add_argument('--python-only', action='store_true',
                        help='Only build Python fPKGs')
    parser.add_argument('--windows-only', action='store_true',
                        help='Only prepare Windows folder')
    parser.add_argument('--help', action='store_true',
                        help='Show this help')
    
    args = parser.parse_args()
    
    if args.help:
        print_banner()
        print_usage()
        return 0
    
    print_banner()
    print_config(args.songs_path, args.output_path, DEFAULT_WINDOWS_BUILD, args.content_id)
    
    # Clean if requested
    if args.clean and args.output_path.exists():
        print("Cleaning output folder...")
        shutil.rmtree(args.output_path)
    
    # Ensure output exists
    args.output_path.mkdir(parents=True, exist_ok=True)
    
    # Build what was requested
    success = True
    
    if not args.windows_only:
        if not build_python_pkg(args.songs_path, args.output_path, args.content_id):
            success = False
            
    if not args.python_only:
        if not prepare_windows_folder(args.songs_path, DEFAULT_WINDOWS_BUILD, args.content_id):
            success = False
    
    print("\n" + "═" * 60)
    if success:
        print("PIPELINE COMPLETE!")
    else:
        print("PIPELINE FAILED!")
    print("═" * 60)
    
if success:
        print(f"\nPython fPKGs:")
        print(f"  - {args.output_path / 'custom_songs_v6.pkg'}")
        print(f"  - {args.output_path / 'custom_unlocker_v3.pkg'}")
        print(f"\nWindows folder:")
        print(f"  - {DEFAULT_WINDOWS_BUILD / 'Project.gp4'}")
        print(f"  - {DEFAULT_WINDOWS_BUILD / 'CUSA12878-app/'}")
        print("\n" + "─" * 60)
        print("Done! All outputs generated successfully.")

if __name__ == "__main__":
    sys.exit(main())