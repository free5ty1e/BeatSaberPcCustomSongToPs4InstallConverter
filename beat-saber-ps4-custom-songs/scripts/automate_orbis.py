#!/usr/bin/env python3
"""Automate orbis-pub-gen GUI using pyautogui"""
import subprocess
import time
import os
from pathlib import Path
import pyautogui

os.environ["DISPLAY"] = ":99"

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
ORBIS_WINE = Path.home() / ".wine/drive_c/orbis-pub-gen"
ORBIS_EXE = "C:\\orbis-pub-gen\\orbis-pub-gen.exe"

def get_env():
    env = os.environ.copy()
    env["WINEDEBUG"] = "fixme-all"
    env["DISPLAY"] = ":99"
    env["WINEPREFIX"] = str(Path.home() / ".wine")
    return env

def build_pkg(gp4_path):
    import shutil
    gp4_src = Path(gp4_path)
    if gp4_src.exists():
        shutil.copy(gp4_src, ORBIS_WINE / "Project.gp4")
    
    print("Starting orbis-pub-gen...")
    proc = subprocess.Popen(
        ["wine", ORBIS_EXE],
        cwd=str(ORBIS_WINE),
        env=get_env()
    )
    print(f"Started PID: {proc.pid}")
    
    time.sleep(3)
    print("Pressing F5...")
    try:
        pyautogui.press("F5")
        time.sleep(5)
        pyautogui.press("enter")
        time.sleep(5)
    except Exception as e:
        print(f"pyautogui error: {e}")
    
    # Wait longer for build (PKG building can take time)
    print("Waiting for build to complete...")
    time.sleep(120)
    
    if proc.poll() is None:
        proc.terminate()
    
    pkg = ORBIS_WINE / "custom.pkg"
    if pkg.exists():
        shutil.copy(pkg, WORK_DIR / "output/custom_songs_orbis.pkg")
        print("SUCCESS: custom_songs_orbis.pkg created")
        return True
    return False

if __name__ == "__main__":
    build_pkg(WORK_DIR / "windows_build/Project.gp4")