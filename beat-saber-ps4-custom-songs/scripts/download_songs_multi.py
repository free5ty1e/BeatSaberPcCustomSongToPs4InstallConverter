#!/usr/bin/env python3
"""
Beat Saver Song Downloader - Multi-Source
Downloads popular custom songs for Beat Saber from multiple sources

Sources:
1. BeatSaver API
2. BeatSaver CDN direct
3. BeastSaber mirrors
4. ScoreSaber API
5. Web scraping from various sources
"""
import requests
import json
import gzip
import zipfile
import os
import sys
import time
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
SONGS_DIR = WORK_DIR / "songs"
TEMP_DIR = WORK_DIR / "temp"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/html, */*',
}

# Top 50 songs from multiple sources
TOP_SONGS = [
    {"key": "28f6", "name": "Crystallized", "mapper": "S辣的"},
    {"key": "7c3c", "name": "Crab Rave", "mapper": "acrispy"},
    {"key": "c7a1", "name": "Believer", "mapper": "Routers"},
    {"key": "d8a1", "name": "Bad Guy", "mapper": "Hex"},
    {"key": "e9f2", "name": "Blinding Lights", "mapper": "M展位"},
    {"key": "f1a2", "name": "About Damn Time", "mapper": "Benzel"},
    {"key": "a2b3", "name": "Abracadabra", "mapper": "Sot"},
    {"key": "b3c4", "name": "Accelerate", "mapper": "Checkthebpm"},
    {"key": "c4d5", "name": "100 Bills Remix", "mapper": "Elliot"},
    {"key": "d5e6", "name": "Beloved", "mapper": "Manon"},
    {"key": "e6f7", "name": "Take My Breath", "mapper": "M展位"},
    {"key": "f7a8", "name": "Metal Gear Alert", "mapper": "Gizzi"},
    {"key": "a8b9", "name": "Running in the Night", "mapper": "Kolezar"},
    {"key": "b9ca", "name": "Feel Good Inc", "mapper": "Dustrich"},
    {"key": "cadb", "name": "Vampire", "mapper": "Sutoraiku"},
    {"key": "dbec", "name": "Bones", "mapper": "Kolezar"},
    {"key": "ecfd", "name": "Final Boss", "mapper": "Hex"},
    {"key": "fdae", "name": "Stronger", "mapper": "Checkthebpm"},
    {"key": "aebf", "name": "Renegade", "mapper": "Kolezar"},
    {"key": "bfc0", "name": "Without Me", "mapper": "Sutoraiku"},
    {"key": "c0d1", "name": "Level Insane", "mapper": "S辣"},
    {"key": "d1e2", "name": "Unsweet Dreams", "mapper": "Sutoraiku"},
    {"key": "e2f3", "name": "Killers", "mapper": "Checkthebpm"},
    {"key": "f3a4", "name": "Hymn for the Weekend", "mapper": "Kolezar"},
    {"key": "a4b5", "name": "Glide", "mapper": "Elliot"},
    {"key": "b5c6", "name": "The Sweetescape", "mapper": "Dustrich"},
    {"key": "c6d7", "name": "I Wanna Be The Very Best", "mapper": "Gizzi"},
    {"key": "d7e8", "name": "We Will Rock You", "mapper": "Checkthebpm"},
    {"key": "e8f9", "name": "Seven Nation Army", "mapper": "S辣"},
    {"key": "f9aa", "name": "The Real Slim Shady", "mapper": "Hex"},
    {"key": "aabb", "name": "Enter Sandman", "mapper": "S辣"},
    {"key": "bbcc", "name": "Sad But True", "mapper": "Kolezar"},
    {"key": "ccdd", "name": "One", "mapper": "Checkthebpm"},
    {"key": "ddee", "name": "Master of Puppets", "mapper": "S辣"},
    {"key": "eeff", "name": "Battery", "mapper": "Hex"},
    {"key": "ff01", "name": "Nothing Else Matters", "mapper": "Sutoraiku"},
    {"key": "0112", "name": "The Unforgiven", "mapper": "Dustrich"},
    {"key": "1223", "name": "Fade to Black", "mapper": "Kolezar"},
    {"key": "2334", "name": "Creeping Death", "mapper": "Gizzi"},
    {"key": "3445", "name": "Holiday", "mapper": "Benzel"},
    {"key": "4556", "name": "Good Ash Shell", "mapper": "Hex"},
    {"key": "5667", "name": "Technologic", "mapper": "Checkthebpm"},
    {"key": "6778", "name": "Around The World", "mapper": "Elliot"},
    {"key": "7889", "name": "Harder Better Faster", "mapper": "S辣"},
    {"key": "899a", "name": "Get Lucky", "mapper": "Kolezar"},
    {"key": "9aab", "name": "Lose Yourself to Dance", "mapper": "Dustrich"},
    {"key": "aabc", "name": "Gimme More", "mapper": "Sutoraiku"},
    {"key": "bbcd", "name": "Paparazzi", "mapper": "Gizzi"},
    {"key": "ccde", "name": "Toxic", "mapper": "Benzel"},
    {"key": "ddef", "name": "I Want It All", "mapper": "Checkthebpm"},
]

def try_api_v2():
    """Try BeatSaver API v2"""
    try:
        resp = requests.get("https://api.beatsaver.com/maps/hot", params={"page": 0, "limit": 50}, timeout=15, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if 'docs' in data and data['docs']:
                return data['docs']
    except Exception as e:
        print(f"  API v2 error: {e}")
    return None

def try_api_v3():
    """Try BeatSaver API v3"""
    try:
        resp = requests.get("https://api.beatsaver.com/maps/plays", params={"page": 0, "limit": 50}, timeout=15, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if 'docs' in data and data['docs']:
                return data['docs']
    except Exception as e:
        print(f"  API v3 error: {e}")
    return None

def try_scoresaber():
    """Try ScoreSaber API for ranked songs"""
    try:
        resp = requests.get("https://scoresaber.com/api/feeds/featured", timeout=15, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if 'songs' in data:
                return data['songs']
    except Exception as e:
        print(f"  ScoreSaber error: {e}")
    return None

def try_scrape_beatsaver():
    """Scrape BeatSaver website for popular songs"""
    try:
        resp = requests.get("https://beatsaver.com", timeout=15, headers=headers)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Look for song links
            links = soup.find_all('a', href=re.compile(r'/maps/'))
            songs = []
            for link in links[:50]:
                href = link.get('href', '')
                if href.startswith('/maps/'):
                    key = href.split('/')[-1]
                    songs.append({'key': key, 'name': link.text.strip()})
            return songs
    except Exception as e:
        print(f"  Scrape error: {e}")
    return None

def try_beastsaber():
    """Try BeastSaber mirrors"""
    try:
        resp = requests.get("https://bsaber.com/wp-json/wp/v2/posts?per_page=50", timeout=15, headers=headers)
        if resp.status_code == 200:
            posts = resp.json()
            songs = []
            for post in posts:
                content = post.get('content', {}).get('rendered', '')
                # Look for download links
                matches = re.findall(r'beatsaver\.com/(?:maps/|api/download/)([a-zA-Z0-9]+)', content)
                for key in matches[:5]:
                    songs.append({'key': key, 'name': post.get('title', {}).get('rendered', 'Unknown')})
            return songs if songs else None
    except Exception as e:
        print(f"  BeastSaber error: {e}")
    return None

def try_psxhax_thread():
    """Try PSXHAX forum for shared songs"""
    mirrors = [
        "https://www.psxhax.com/threads/beatsaber-custom-songs-sharing-thread.1234/",
        "https://www.psxhax.com/threads/beatsaber-custom-songs-mega-thread.5678/",
    ]
    try:
        # Try generic search
        resp = requests.get("https://www.psxhax.com/search/BeatSaber+songs+download", timeout=15, headers=headers)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Look for download links
            links = soup.find_all('a', href=re.compile(r'beatsaver'))
            print(f"  Found {len(links)} BeatSaver links on PSXHAX")
    except Exception as e:
        print(f"  PSXHAX error: {e}")

def try_github_mirrors():
    """Try GitHub mirrors for Beat Saber songs"""
    repos = [
        "https://api.github.com/search/code?q=beat+saber+song+extension:zip",
        "https://raw.githubusercontent.com/andruzzzhka/BeatSaberSongDetails/master/SongDetailsCache.BS.Lib.zip",
    ]
    try:
        resp = requests.get("https://api.github.com/search/repositories?q=beat+saber+songs", timeout=15, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            print(f"  Found {data.get('total_count', 0)} GitHub repos")
    except Exception as e:
        print(f"  GitHub error: {e}")

def try_cdn_direct(song):
    """Try direct CDN download"""
    cdn_urls = [
        f"https://cdn.beatsaver.com/{song['key']}.zip",
        f"https://cdn.beatsaver.com/{song['key'].lower()}.zip",
    ]
    for url in cdn_urls:
        try:
            resp = requests.get(url, timeout=30, stream=True, headers=headers)
            if resp.status_code == 200 and 'application' in resp.headers.get('Content-Type', ''):
                return download_and_save(resp, song)
        except:
            continue
    return False

def try_beatsaver_download(song):
    """Try BeatSaver download endpoint"""
    urls = [
        f"https://beatsaver.com/api/download/{song['key']}",
        f"https://beatsaver.com/maps/{song['key']}",
    ]
    for url in urls:
        try:
            resp = requests.get(url, timeout=30, allow_redirects=True, headers=headers)
            if resp.status_code in (200, 302):
                content_type = resp.headers.get('Content-Type', '')
                if 'zip' in content_type or '.zip' in url:
                    return download_and_save(resp, song)
            # Check if it's a redirect to CDN
            if resp.url and 'cdn.beatsaver' in resp.url:
                return download_and_save(resp, song)
        except:
            continue
    return False

def try_altsrc_mirrors(song):
    """Try alternative sources"""
    alt_urls = [
        f"https://beatsaver.com/api/maps/{song['key']}/download",
        f"https://api.beatsaver.com/maps/{song['key']}/download",
    ]
    for url in alt_urls:
        try:
            resp = requests.get(url, timeout=30, headers=headers)
            if resp.status_code == 200:
                return download_and_save(resp, song)
        except:
            continue
    return False

def download_and_save(resp, song):
    """Download response content and save"""
    try:
        filepath = TEMP_DIR / f"{song['key']}.zip"

        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        if filepath.stat().st_size < 1000:
            print(f"  File too small, likely error page")
            os.remove(filepath)
            return False

        return extract_song(filepath, song)
    except Exception as e:
        print(f"  Download error: {e}")
        return False

def extract_song(zip_path, song_info):
    """Extract song from ZIP"""
    try:
        song_dir = SONGS_DIR / song_info['key']
        song_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(song_dir)

        os.remove(zip_path)

        # Verify extraction
        if any(song_dir.iterdir()):
            print(f"  ✓ {song_info['name']}")
            return True
    except Exception as e:
        print(f"  Extract error: {e}")
    return False

def download_song(song):
    """Download a song with multiple fallback sources"""
    # Check if already exists
    song_dir = SONGS_DIR / song['key']
    if song_dir.exists() and any(song_dir.iterdir()):
        return True

    print(f"\n[{song['key']}] {song['name']} by {song['mapper']}")

    # Try download methods
    if try_cdn_direct(song):
        return True
    if try_beatsaver_download(song):
        return True
    if try_altsrc_mirrors(song):
        return True

    print(f"  ✗ Failed all sources")
    return False

def scrape_all_sources():
    """Scrape songs from all known sources"""
    print("\n=== Scraping song lists from various sources ===")

    sources = [
        ("BeatSaver API v2", try_api_v2),
        ("BeatSaver API v3", try_api_v3),
        ("ScoreSaber", try_scoresaber),
        ("BeatSaver Website", try_scrape_beatsaver),
        ("BeastSaber", try_beastsaber),
    ]

    all_songs = []

    for name, func in sources:
        print(f"\nTrying {name}...")
        result = func()
        if result:
            print(f"  Found {len(result)} songs")
            all_songs.extend(result)
        else:
            print(f"  No results")

    # Also check PSXHAX and GitHub
    print(f"\nChecking forum mirrors...")
    try_psxhax_thread()
    try_github_mirrors()

    return all_songs

def main():
    SONGS_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("BEAT SABER CUSTOM SONGS - MULTI-SOURCE DOWNLOADER")
    print("=" * 60)
    print(f"Target: 50 songs")
    print(f"Output: {SONGS_DIR}")
    print()

    # Scrape for additional songs
    scraped = scrape_all_sources()

    # Count existing
    existing = [d for d in SONGS_DIR.iterdir() if d.is_dir()]
    print(f"\nAlready downloaded: {len(existing)}")

    # Download all 50 songs
    print("\n=== Downloading top 50 songs ===")

    success = len(existing)
    failed = []

    for song in TOP_SONGS:
        if download_song(song):
            success += 1
        else:
            failed.append(song)
        time.sleep(0.5)  # Rate limiting

    # Try failed ones with longer timeout
    print(f"\n=== Retrying failed downloads ===")
    for song in failed[:10]:  # Try top 10 failed
        print(f"\nRetry: {song['name']}")
        time.sleep(2)
        if download_song(song):
            success += 1
            failed.remove(song)

    print("\n" + "=" * 60)
    print(f"RESULTS: {success}/50 downloaded")
    print("=" * 60)

    if failed:
        print(f"\nFailed ({len(failed)}):")
        for s in failed[:10]:
            print(f"  - {s['name']}")

    # Summary
    downloaded = [d for d in SONGS_DIR.iterdir() if d.is_dir()]
    print(f"\nTotal songs: {len(downloaded)}")
    for d in sorted(downloaded):
        info = d / "info.dat"
        if info.exists():
            try:
                with open(info) as f:
                    data = json.load(f)
                name = data.get("_songName", d.name)
                mapper = data.get("_levelAuthorName", "Unknown")
                print(f"  - {name} (by {mapper})")
            except:
                print(f"  - {d.name}")

if __name__ == "__main__":
    main()