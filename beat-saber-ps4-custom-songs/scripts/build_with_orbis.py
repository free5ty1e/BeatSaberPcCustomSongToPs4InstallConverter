#!/usr/bin/env python3
"""
Build PKG using orbis-pub-gen via Wine.

Prerequisites (after devcontainer rebuild):
1. Wine + wine-mono installed
2. orbis-pub-gen files copied to ~/.wine/drive_c/orbis-pub-gen/
3. sc.exe copied to ~/.wine/drive_c/windows/system32/

NOTE: orbis-pub-cmd.exe requires sc.exe to pass version check.
If "[Error] The version of sc.exe is invalid or missing.", 
the sc.exe from PS4 Fake PKG Tools v7 is not being found properly.
"""
import os
import subprocess
import sys
from pathlib import Path

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
WINDOWS_BUILD = WORK_DIR / "windows_build"
ORBIS_DIR = WORK_DIR / "orbis-pub-gen"
WINE_ORBIS = Path.home() / ".wine/drive_c/orbis-pub-gen"
OUTPUT_DIR = WORK_DIR / "output"

def run_wine(cmd, cwd=None, timeout=300):
    """Run Wine command with xvfb"""
    env = os.environ.copy()
    env["WINEDEBUG"] = "fixme-all"
    env["WINEPREFIX"] = str(Path.home() / ".wine")
    
    result = subprocess.run(
        cmd,
        cwd=cwd or str(WINE_ORBIS),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env
    )
    return result

def build():
    """Build PKG using orbis-pub-cmd"""
    
    # Check prerequisites
    if not WINE_ORBIS.exists():
        print("ERROR: Wine orbis-pub-gen folder not set up")
        print("Run: mkdir -p ~/.wine/drive_c/orbis-pub-gen && cp orbis-pub-gen/* ~/.wine/drive_c/orbis-pub-gen/")
        return False
    
    # Copy GP4 to Wine folder
    gp4_src = WINDOWS_BUILD / "Project.gp4"
    if not gp4_src.exists():
        print(f"ERROR: GP4 not found: {gp4_src}")
        return False
    
    import shutil
    shutil.copy(gp4_src, WINE_ORBIS / "Project.gp4")
    
    # Run orbis-pub-cmd
    print("Running orbis-pub-cmd img_create...")
    
    result = run_wine([
        "wine", "C:\\\\orbis-pub-gen\\\\orbis-pub-cmd.exe",
        "img_create", "C:\\\\orbis-pub-gen\\\\Project.gp4",
        "C:\\\\orbis-pub-gen\\\\custom.pkg"
    ])
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr[:500])
    
    # Check for output
    pkg = WINE_ORBIS / "custom.pkg"
    if pkg.exists():
        shutil.copy(pkg, OUTPUT_DIR / "custom_songs_orbis.pkg")
        print(f"SUCCESS: Generated {OUTPUT_DIR / 'custom_songs_orbis.pkg'}")
        return True
    
    return False

if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)