#!/usr/bin/env python3
"""
Build Proper DLC PKG using LibOrbisPkg PkgTool
Based on working ez_dlc.py format
"""
import gzip
import json
import shutil
import subprocess
import os
from pathlib import Path
import sys
import datetime

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
OUTPUT_DIR = WORK_DIR / "output"
PKGTOOL = WORK_DIR / "LibOrbisPkg/PkgTool.Core/bin/Debug/net8.0/PkgTool.Core.dll"

# Content ID must be EXACTLY 36 characters
# Format: UP(2) + 4 digits + -(1) + CUSA + 5 digits +(1) + _(2) + -(1) + 14 chars = 36
GAME_ID = "CUSA12878"
CONTENT_ID = "UP4882-CUSA12878_00-P1S5XXXXXXXXXXXX"  # 36 chars exactly

def run_pkgtool(args):
    """Run PkgTool with dotnet."""
    env = os.environ.copy()
    env["DOTNET_SYSTEM_GLOBALIZATION_INVARIANT"] = "1"
    cmd = ["dotnet", str(PKGTOOL)] + args
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    return result

def build_pkg(songs_dir, output_name="custom_songs.pkg"):
    """Build PKG using proper GP4 project format."""
    
    # Clean and create work directory
    work_dir = OUTPUT_DIR / "dlc_build"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "sce_sys").mkdir()
    
    # Get songs
    songs_dir = Path(songs_dir)
    songs = [d for d in songs_dir.iterdir() if d.is_dir()]
    
    if not songs:
        print("No songs found!")
        return False
    
    print(f"Building PKG with {len(songs)} songs...")
    
    # Create param.sfo using PkgTool
    print("Creating param.sfo...")
    paramsfo_path = work_dir / "sce_sys/param.sfo"
    run_pkgtool(["sfo_new", str(paramsfo_path)])
    run_pkgtool(["sfo_setentry", "--value", "ac", "--type", "utf8", "--maxsize", "4", str(paramsfo_path), "CATEGORY"])
    run_pkgtool(["sfo_setentry", "--value", CONTENT_ID, "--type", "utf8", "--maxsize", "48", str(paramsfo_path), "CONTENT_ID"])
    run_pkgtool(["sfo_setentry", "--value", "obs", "--type", "utf8", "--maxsize", "4", str(paramsfo_path), "FORMAT"])
    run_pkgtool(["sfo_setentry", "--value", "Beat Saber Custom Songs", "--type", "utf8", "--maxsize", "128", str(paramsfo_path), "TITLE"])
    run_pkgtool(["sfo_setentry", "--value", GAME_ID, "--type", "utf8", "--maxsize", "12", str(paramsfo_path), "TITLE_ID"])
    run_pkgtool(["sfo_setentry", "--value", "01.00", "--type", "utf8", "--maxsize", "8", str(paramsfo_path), "VERSION"])
    
    # Copy or create icon0.png
    icon_path = work_dir / "sce_sys/icon0.png"
    ref_icon = WORK_DIR / "ref_extract/sce_sys/icon0.png"
    if ref_icon.exists():
        shutil.copy(ref_icon, icon_path)
    else:
        # Create minimal 1x1 PNG
        icon_path.write_bytes(bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
            0x89, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x44, 0x41,
            0x54, 0x08, 0xD7, 0x63, 0x00, 0x00, 0x00, 0x82,
            0x00, 0x81, 0x4B, 0x2E, 0x0E, 0x00, 0x00, 0x00,
            0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
        ]))
    
    # Generate GP4 project file
    gen_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    gp4_content = f'''<?xml version="1.0"?>
<psproject xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" fmt="gp4" version="1000">
  <volume>
    <volume_type>pkg_ps4_ac_data</volume_type>
    <volume_ts>{gen_time}</volume_ts>
    <package content_id="{CONTENT_ID}" passcode="00000000000000000000000000000000" entitlement_key="00000000000000000000000000000000" />
  </volume>
  <files img_no="0">
    <file targ_path="sce_sys/icon0.png" orig_path="sce_sys\\icon0.png" />
    <file targ_path="sce_sys/param.sfo" orig_path="sce_sys\\param.sfo" />
  </files>
  <rootdir>
    <dir targ_name="sce_sys" />
  </rootdir>
</psproject>'''
    
    gp4_path = work_dir / "fake_dlc.gp4"
    gp4_path.write_text(gp4_content)
    print(f"Created GP4: {gp4_path}")
    
    # Build PKG using PkgTool
    print("Building PKG...")
    output_pkg_dir = work_dir / "output_pkg"
    output_pkg_dir.mkdir()
    
    result = run_pkgtool(["pkg_build", str(gp4_path), str(output_pkg_dir)])
    
    if result.returncode != 0:
        print(f"Build error: {result.stderr}")
        return False
    
    print(result.stdout)
    
    # Find the generated PKG
    pkg_files = list(output_pkg_dir.glob("*.pkg"))
    if not pkg_files:
        print("No PKG generated!")
        return False
    
    # Copy to output
    final_pkg = OUTPUT_DIR / output_name
    shutil.copy(str(pkg_files[0]), str(final_pkg))
    
    print(f"\nCreated: {final_pkg}")
    print(f"Size: {final_pkg.stat().st_size:,} bytes")
    
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/build_pkg.py <songs_folder> [--output <name>]")
        return
    
    songs_dir = sys.argv[1]
    output_name = "custom_songs.pkg"
    
    if len(sys.argv) > 2 and sys.argv[2] == "--output":
        output_name = sys.argv[3]
    
    build_pkg(songs_dir, output_name)


if __name__ == "__main__":
    main()