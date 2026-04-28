#!/usr/bin/env python3
"""Download songs from BeatSaver API that match user preferences.

User criteria:
- Must have Easy, Normal, AND Hard difficulties
- User plays Hard, friends play Medium/Easy
"""

import os
import json
import requests
import zipfile
import hashlib
from pathlib import Path

REPO_DIR = Path("/workspace/beat-saber-ps4-custom-songs/songs_repo")
REPO_DIR.mkdir(exist_ok=True)

DOWNLOADED_FILE = REPO_DIR / "downloaded_songs.json"

def load_downloaded():
    if DOWNLOADED_FILE.exists():
        with open(DOWNLOADED_FILE) as f:
            return json.load(f)
    return {}

def save_downloaded(data):
    with open(DOWNLOADED_FILE, 'w') as f:
        json.dump(data, f, indent=2)

BASE_URL = "https://api.beatsaver.com"

def get_popular_songs(page=0, query="*", page_size=50):
    """Get popular songs from BeatSaver - works via /search/text/{page}"""
    params = {
        "q": query if query != "*" else "",
        "sortOrder": "Downloads",
        "pageSize": page_size,
    }
    resp = requests.get(f"{BASE_URL}/search/text/{page}", params=params)
    if resp.status_code == 500:
        # Fallback: no query for hot listings
        resp = requests.get(f"{BASE_URL}/search/text/{page}")
    resp.raise_for_status()
    return resp.json().get("docs", [])

def get_song_by_hash(song_hash):
    """Get song details by hash."""
    resp = requests.get(f"{BASE_URL}/maps/hash/{song_hash}")
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()

def check_difficulties(versions):
    """Check if song has at least Easy, Normal, and Hard difficulties.
    
    User requirement: Must NOT be Expert+ only.
    We need at least Easy AND Normal AND Hard.
    """
    if not versions:
        return False
    
    latest = versions[0]
    diffs = latest.get("diffs", [])
    
    difficulties = set()
    for diff in diffs:
        difficulties.add(diff.get("difficulty", "").lower())
    
    has_easy = any("easy" in d for d in difficulties)
    has_normal = any("normal" in d for d in difficulties)
    has_hard = any("hard" in d for d in difficulties)
    
    # Must have at least Easy+Normal+Hard (not Expert+ only)
    return has_easy and has_normal and has_hard

def download_song(hash_key, download_url, song_name):
    """Download a song from BeatSaver CDN."""
    try:
        print(f"  Downloading {song_name}...")
        resp = requests.get(download_url, timeout=120)
        resp.raise_for_status()
        
        filename = f"{hash_key}.zip"
        zip_path = REPO_DIR / filename
        
        with open(zip_path, 'wb') as f:
            f.write(resp.content)
        
        extract_path = REPO_DIR / hash_key
        extract_path.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_path)
        
        os.remove(zip_path)
        
        print(f"  Extracted to {hash_key}/")
        return True
    except Exception as e:
        print(f"  Error downloading {song_name}: {e}")
        return False

def get_all_difficulties(versions):
    """Get list of all difficulties in a song."""
    if not versions:
        return []
    latest = versions[0]
    diffs = latest.get("diffs", [])
    return [d.get("difficulty", "") for d in diffs]

def main():
    print("=" * 60)
    print("BeatSaver Song Downloader")
    print("=" * 60)
    print(f"\nDownloading songs to: {REPO_DIR}")
    print(f"Criteria: Must have Easy, Normal, AND Hard difficulties\n")
    
    downloaded = load_downloaded()
    print(f"Already downloaded: {len(downloaded)} songs\n")
    
    total_downloaded = 0
    
    for page in range(0, 20):
        print(f"\n--- Fetching page {page} (top downloaded) ---")
        songs = get_popular_songs(page=page)
        
        if not songs:
            print("No more songs found!")
            break
        
        print(f"Found {len(songs)} songs, checking difficulties...")
        
        for song in songs:
            song_id = song.get("id", "")
            versions = song.get("versions", [])
            
            if not versions:
                continue
            
            latest = versions[0]
            hash_key = latest.get("hash", "")
            download_url = latest.get("downloadURL", "")
            song_name = song.get("metadata", {}).get("songName", "Unknown")
            key = song.get("id", "")
            
            if not hash_key or not download_url:
                continue
            
            if key in downloaded:
                print(f"  [{key}] {song_name} - already downloaded, skipping")
                continue
            
            if not check_difficulties(versions):
                diffs = get_all_difficulties(versions)
                print(f"  [{key}] {song_name} - missing Easy/Normal/Hard, has {diffs}, skipping")
                continue
            
            print(f"  [{key}] {song_name} - has Easy+Normal+Hard, downloading...")
            
            if download_song(hash_key, download_url, song_name):
                downloaded[key] = {
                    "name": song_name,
                    "hash": hash_key,
                    "downloaded_at": str(Path(__file__).stat().st_mtime)
                }
                save_downloaded(downloaded)
                total_downloaded += 1
        
        if total_downloaded >= 100:
            print("\n--- Reached 100 songs, stopping ---")
            break
    
    print(f"\n{'=' * 60}")
    print(f"Download complete! Total new songs: {total_downloaded}")
    print(f"Total in repository: {len(downloaded)}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()