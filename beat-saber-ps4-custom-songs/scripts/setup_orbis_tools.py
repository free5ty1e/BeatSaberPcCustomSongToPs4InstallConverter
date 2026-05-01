#!/usr/bin/env python3
"""
Setup PS4 Fake PKG Tools (orbis-pub-gen) for building custom songs.

This script downloads and extracts PS4 Fake PKG Tools v7 from CyB1K's GitHub.
Can run in devcontainer (Linux) or on Windows (with appropriate tools).

Usage:
    python3 scripts/setup_orbis_tools.py        # Default installation
    python3 scripts/setup_orbis_tools.py --check # Check for updates only
    python3 scripts/setup_orbis_tools.py --path /custom/path # Custom install location
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Configuration
ORBIS_VERSION = "v7"
ORBIS_REPO = "CyB1K/PS4-Fake-PKG-Tools-3.87"
ORBIS_URL = f"https://github.com/{ORBIS_REPO}/releases/download/{ORBIS_VERSION}/PS4_Fake_PKG_Tools_3.87_V7.rar"

# Install locations
DEVCONTAINER_PATH = Path("/workspace/beat-saber-ps4-custom-songs/orbis-pub-gen")
DEFAULT_LOCAL_PATH = Path("./orbis-pub-gen")

def check_for_updates(current_version=ORBIS_VERSION):
    """Check GitHub for newer releases."""
    try:
        import urllib.request
        import json
        
        url = f"https://api.github.com/repos/{ORBIS_REPO}/releases/latest"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Python')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            latest = data.get('tag_name', 'unknown')
            
        print(f"Current version: {current_version}")
        print(f"Latest version: {latest}")
        
        if latest != current_version:
            print(f"UPDATE AVAILABLE: {latest}")
            return latest
        else:
            print("No update available")
            return current_version
            
    except Exception as e:
        print(f"Error checking for updates: {e}")
        return current_version

def download_tools(url=ORBIS_URL, dest_path=DEFAULT_LOCAL_PATH):
    """Download and extract PS4 Fake PKG Tools."""
    import urllib.request
    import tempfile
    
    print(f"Downloading from: {url}")
    print(f"Destination: {dest_path}")
    
    # Create temp file
    with tempfile.NamedTemporaryFile(suffix=".rar", delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Download
        print("Downloading...")
        urllib.request.urlretrieve(url, temp_path)
        print("Download complete")
        
        # Create destination
        dest_path.mkdir(parents=True, exist_ok=True)
        
        # Extract based on OS
        print("Extracting...")
        if sys.platform == "win32":
            # Try using 7zip or WinRAR
            try:
                subprocess.run(["7z", "x", temp_path, f"-o{dest_path}", "-y"], check=True)
            except FileNotFoundError:
                # Fall back to PowerShell expand
                subprocess.run(["powershell", "-Command", f"Expand-Archive -Path '{temp_path}' -DestinationPath '{dest_path}'"], check=True)
        else:
            # Linux - use unrar
            subprocess.run(["unrar", "x", temp_path, str(dest_path)], check=True)
        
        print(f"Extracted to: {dest_path}")
        
        # List contents
        print("\nFiles installed:")
        for f in dest_path.iterdir():
            print(f"  {f.name}")
            
    finally:
        # Cleanup
        os.unlink(temp_path)
    
    return dest_path

def setup_wine_integration(orbis_path):
    """Set up Wine integration for devcontainer."""
    wine_prefix = Path.home() / ".wine"
    wine_orbis = wine_prefix / "drive_c" / "orbis-pub-gen"
    
    # Create Wine folder
    wine_orbis.mkdir(parents=True, exist_ok=True)
    
    # Copy files
    for item in orbis_path.iterdir():
        shutil.copy2(item, wine_orbis / item.name)
    
    # Copy ext folder
    if (orbis_path / "ext").exists():
        wine_ext = wine_orbis / "ext"
        wine_ext.mkdir(parents=True, exist_ok=True)
        for item in (orbis_path / "ext").iterdir():
            shutil.copy2(item, wine_ext / item.name)
    
    print(f"Wine integration set up at: {wine_orbis}")
    print("To run: wine {wine_orbis}/orbis-pub-gen.exe")

def main():
    parser = argparse.ArgumentParser(description="Setup PS4 Fake PKG Tools")
    parser.add_argument("--check", action="store_true", help="Check for updates only")
    parser.add_argument("--path", type=Path, help="Custom installation path")
    parser.add_argument("--wine", action="store_true", help="Also set up Wine integration")
    parser.add_argument("--force", action="store_true", help="Force re-download even if exists")
    
    args = parser.parse_args()
    
    # Check for updates
    latest = check_for_updates(ORBIS_VERSION)
    
    if args.check:
        sys.exit(0)
    
    # Determine path
    install_path = args.path if args.path else DEFAULT_LOCAL_PATH
    
    # Check if already exists
    if install_path.exists() and not args.force:
        print(f"Already installed at: {install_path}")
        if args.wine:
            setup_wine_integration(install_path)
        return
    
    # Download and extract
    download_tools(dest_path=install_path)
    
    # Wine integration if requested
    if args.wine:
        setup_wine_integration(install_path)
    
    print("\n=== SETUP COMPLETE ===")
    print(f"Tools installed at: {install_path}")
    print(f"Latest version available: {latest}")
    
    if sys.platform != "win32":
        print("\nTo use with Wine:")
        print(f"  wine {install_path}/orbis-pub-gen.exe")

if __name__ == "__main__":
    main()