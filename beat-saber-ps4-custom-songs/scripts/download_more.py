#!/usr/bin/env python3
"""
Beat Saver Additional Song Downloader
Scrape songs from search results and download more
"""
import requests
import json
import gzip
import zipfile
import os
import time
import re
from pathlib import Path
from bs4 import BeautifulSoup

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
SONGS_DIR = WORK_DIR / "songs"
TEMP_DIR = WORK_DIR / "temp"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/html, */*',
}

def search_beatsaver(query, limit=10):
    """Search BeatSaver for songs"""
    try:
        url = f"https://beatsaver.com/search?q={query}&sortOrder=Rating"
        resp = requests.get(url, timeout=15, headers=headers)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            links = soup.find_all('a', href=re.compile(r'/maps/[a-zA-Z0-9]+'))
            songs = []
            for link in links[:limit]:
                href = link.get('href', '')
                key = href.split('/maps/')[-1].split('?')[0]
                if key and len(key) == 5 and key not in [d.name for d in SONGS_DIR.iterdir()]:
                    songs.append({'key': key, 'name': query})
            return songs
    except Exception as e:
        print(f"Search error for {query}: {e}")
    return []

def try_api_download(song):
    """Try downloading via API"""
    try:
        resp = requests.get(f"https://api.beatsaver.com/maps/id/{song['key']}", timeout=10, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            versions = data.get('versions', [])
            if versions:
                download_url = versions[0].get('downloadURL')
                if download_url:
                    return download_from_url(song, download_url)
    except:
        pass
    return False

def try_cdn_download(song):
    """Try direct CDN"""
    try:
        resp = requests.get(f"https://cdn.beatsaver.com/{song['key']}.zip", timeout=30, stream=True, headers=headers)
        if resp.status_code == 200:
            return download_from_url(song, f"https://cdn.beatsaver.com/{song['key']}.zip")
    except:
        pass
    return False

def download_from_url(song, url):
    """Download song"""
    try:
        resp = requests.get(url, timeout=60, stream=True, headers=headers)
        if resp.status_code == 200:
            filepath = TEMP_DIR / f"{song['key']}.zip"
            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            if filepath.stat().st_size > 5000:
                return extract_song(filepath, song)
            os.remove(filepath)
    except:
        pass
    return False

def extract_song(zip_path, song_info):
    """Extract song"""
    try:
        song_dir = SONGS_DIR / song_info['key']
        song_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(song_dir)
        os.remove(zip_path)
        if any(song_dir.iterdir()):
            print(f"  ✓ {song_info['name']}")
            return True
    except:
        pass
    return False

def main():
    SONGS_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Search terms - popular community songs
    searches = [
        "Crab Rave", "Crystallized", "Believer", "Bad Guy",
        "Purple People Eater", "Gangnam Style", "Final Boss",
        "Metal Gear Alert", "Feel Good Inc", "Vampire",
        "Bones", "Stronger", "Renegade", "Level Insane",
        "Killers", "Glide", "Technologic", "Get Lucky",
        "Around The World", "Harder Better Faster"
    ]

    # Already downloaded keys
    downloaded = {d.name for d in SONGS_DIR.iterdir() if d.is_dir()}
    print(f"Already have: {len(downloaded)} songs")

    new_songs = []

    for query in searches:
        # Search for song
        results = search_beatsaver(query, 3)
        for song in results:
            if song['key'] not in downloaded:
                new_songs.append(song)
                downloaded.add(song['key'])

    print(f"Found {len(new_songs)} new songs to try")

    success = 0
    for song in new_songs[:30]:
        print(f"\n[{song['key']}] {song['name']}")
        if try_api_download(song):
            success += 1
        elif try_cdn_download(song):
            success += 1
        else:
            print(f"  ✗ Failed")
        time.sleep(0.5)

    print(f"\nDownloaded {success} additional songs")

    # Final count
    all_songs = [d for d in SONGS_DIR.iterdir() if d.is_dir()]
    print(f"Total songs: {len(all_songs)}")

if __name__ == "__main__":
    main()