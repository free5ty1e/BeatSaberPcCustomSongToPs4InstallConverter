#!/usr/bin/env python3
"""
Beat Saber PS4 Custom Songs - Manual Download Script
Since BeatSaver API is down, use direct CDN downloads
"""
import requests
import zipfile
import os
import sys
from pathlib import Path

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
SONGS_DIR = WORK_DIR / "songs"
TEMP_DIR = WORK_DIR / "temp"

# Direct download URLs for popular songs (from CDN)
# Format: key -> (hash, name, download_url)
POPULAR_SONGS = {
    "crystallized": {
        "hash": "28f6",
        "name": "Crystallized",
        "mapper": "S辣的",
        "bpm": 175,
        "url": "https://cdn.beatsaver.com/28f6.zip"
    },
    "crabrave": {
        "hash": "crabrave",
        "name": "Crab Rave",
        "mapper": "acrispy",
        "bpm": 128,
        "url": "https://cdn.beatsaver.com/crabrave.zip"
    },
}

def download_song(key, info):
    """Download a song from CDN"""
    name = info['name']
    url = info['url']

    print(f"Downloading: {name}")

    try:
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200:
            zip_path = TEMP_DIR / f"{key}.zip"
            with open(zip_path, 'wb') as f:
                f.write(resp.content)

            extract_dir = SONGS_DIR / key
            extract_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)

            os.remove(zip_path)
            print(f"  ✓ Downloaded: {name}")
            return extract_dir
        else:
            print(f"  ✗ Failed: HTTP {resp.status_code}")
            return None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None

def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    SONGS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("BEAT SABER PS4 CUSTOM SONG DOWNLOADER")
    print("=" * 60)
    print("\nNote: BeatSaver API appears to be down.")
    print("Trying direct CDN downloads...\n")

    downloaded = []
    for key, info in POPULAR_SONGS.items():
        result = download_song(key, info)
        if result:
            downloaded.append(result)

    if downloaded:
        print(f"\n✓ Downloaded {len(downloaded)} songs!")
    else:
        print("\n✗ No songs downloaded.")
        print("\nManual download instructions:")
        print("1. Go to beatsaver.com")
        print("2. Search for songs")
        print("3. Download zip files")
        print(f"4. Extract to: {SONGS_DIR}")

if __name__ == "__main__":
    main()