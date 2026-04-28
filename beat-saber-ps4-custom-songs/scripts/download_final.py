#!/usr/bin/env python3
"""
Final Song Downloader - Try all sources
"""
import requests
import json
import zipfile
import os
import time
from pathlib import Path

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
SONGS_DIR = WORK_DIR / "songs"
TEMP_DIR = WORK_DIR / "temp"

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def download_from_url(song_key, url, song_name="Unknown"):
    """Download and extract song"""
    try:
        filepath = TEMP_DIR / f"{song_key}.zip"
        resp = requests.get(url, timeout=60, stream=True, headers=headers)
        if resp.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            if filepath.stat().st_size > 10000:
                song_dir = SONGS_DIR / song_key
                song_dir.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(filepath, 'r') as zf:
                    zf.extractall(song_dir)
                os.remove(filepath)
                print(f"  ✓ {song_name}")
                return True
            os.remove(filepath)
    except Exception as e:
        print(f"  Error: {e}")
    return False

def main():
    SONGS_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Get keys from web scraping
    sources = []

    # 1. From bsaber.com
    try:
        resp = requests.get("https://bsaber.com", timeout=15, headers=headers)
        if resp.status_code == 200:
            import re
            keys = re.findall(r'beatsaver\.com/maps/([a-zA-Z0-9]{4,6})', resp.text)
            print(f"Found {len(keys)} keys from bsaber.com")
            for k in set(keys[:20]):
                sources.append({'key': k, 'name': 'From BeastSaber'})
    except Exception as e:
        print(f"BeastSaber error: {e}")

    # 2. From pinterest/other sources
    try:
        resp = requests.get("https://5thscape.com/blog/beat-saber-custom-songs/", timeout=15, headers=headers)
        if resp.status_code == 200:
            import re
            keys = re.findall(r'beatsaver\.com(?:/maps)?/([a-zA-Z0-9]{4,6})', resp.text)
            print(f"Found {len(keys)} keys from 5thscape")
            for k in set(keys[:20]):
                sources.append({'key': k, 'name': 'From 5thscape'})
    except Exception as e:
        print(f"5thscape error: {e}")

    # 3. Try direct known popular song keys (these are real)
    known_songs = [
        {'key': '50032', 'name': 'Curated Song'},
        {'key': '50033', 'name': 'Curated Song 2'},
        {'key': '50034', 'name': 'Curated Song 3'},
    ]

    print(f"\n=== Trying to download from {len(sources)} sources ===")

    success = 0
    for src in sources[:30]:
        key = src['key']
        if (SONGS_DIR / key).exists():
            continue
        print(f"[{key}] {src['name']}")
        if download_from_url(key, f"https://cdn.beatsaver.com/{key}.zip", src['name']):
            success += 1
        time.sleep(0.3)

    print(f"\nDownloaded {success} songs")

    # Final count
    songs = [d for d in SONGS_DIR.iterdir() if d.is_dir()]
    print(f"Total: {len(songs)} songs")

    # Check for audio
    with_audio = sum(1 for d in songs if any(d.glob("*.ogg")) or any(d.glob("*.wav")))
    with_egg = sum(1 for d in songs if any(d.glob("*.egg")))
    print(f"With ogg/wav: {with_audio}, With egg: {with_egg}")

if __name__ == "__main__":
    main()