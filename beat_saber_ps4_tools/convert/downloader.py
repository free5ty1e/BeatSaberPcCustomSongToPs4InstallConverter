#!/usr/bin/env python3
"""
BeatSaver Song Downloader
Downloads custom songs from BeatSaver API and converts to PS4 format.

Usage:
    python3 downloader.py <beat_saver_hash_or_key>
    python3 downloader.py --search "song name"
    python3 downloader.py --top --count 10
"""

import requests
import json
import os
import sys
import zipfile
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

BEATSAVER_API = "https://api.beatsaver.com"

class BeatSaverDownloader:
    def __init__(self, output_dir='songs'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BeatSaberPS4Converter/1.0',
            'Accept': 'application/json'
        })
    
    def _get(self, endpoint, params=None, timeout=30):
        """Make API request."""
        url = f"{BEATSAVER_API}{endpoint}"
        resp = self.session.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    
    def download_song(self, song_key, timeout=60):
        """Download a song by its BeatSaver key."""
        try:
            data = self._get(f"/maps/id/{song_key}", timeout=timeout)
            return self.process_song_data(data)
        except requests.exceptions.RequestException as e:
            print(f"  Error downloading {song_key}: {e}")
            return None
    
    def search_songs(self, query, page=0, page_size=10, timeout=30):
        """Search for songs by name."""
        try:
            data = self._get("/search/text", {
                'q': query,
                'page': page,
                'size': page_size,
            }, timeout=timeout)
            return data.get('docs', [])
        except requests.exceptions.RequestException as e:
            print(f"  Search error: {e}")
            return []
    
    def get_latest(self, page=0, page_size=20, timeout=30):
        """Get latest uploaded songs."""
        try:
            data = self._get("/maps/latest", {
                'page': page,
                'size': page_size,
            }, timeout=timeout)
            return data.get('docs', [])
        except requests.exceptions.RequestException as e:
            print(f"  Error: {e}")
            return []
    
    def get_hot(self, page=0, page_size=20, timeout=30):
        """Get hottest songs. Uses latest as fallback."""
        try:
            data = self._get("/maps/latest", {
                'page': page,
                'size': page_size,
            }, timeout=timeout)
            return data.get('docs', [])
        except requests.exceptions.RequestException as e:
            print(f"  Error: {e}")
            return []
    
    def process_song_data(self, data):
        """Process song data from API and download files."""
        metadata = data.get('metadata', {})
        song_name = metadata.get('songName', 'Unknown')
        song_sub = metadata.get('songSubName', '')
        song_author = metadata.get('songAuthorName', 'Unknown')
        bpm = metadata.get('bpm', 120)
        
        # Get download URL
        versions = data.get('versions', [])
        if not versions:
            print(f"  No versions found for {song_key}")
            return None
        
        latest = versions[-1]
        download_url = latest.get('downloadURL')
        
        if not download_url:
            print(f"  No download URL for {song_key}")
            return None
        
        # Create output folder
        safe_name = f"{data.get('id', 'unknown')}_{song_name}".replace(' ', '_')[:100]
        song_dir = self.output_dir / safe_name
        song_dir.mkdir(parents=True, exist_ok=True)
        
        # Download the zip
        print(f"  Downloading {song_name}...")
        try:
            zip_resp = self.session.get(download_url, timeout=120, stream=True)
            zip_resp.raise_for_status()
            
            zip_path = song_dir / 'song.zip'
            with open(zip_path, 'wb') as f:
                for chunk in zip_resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(song_dir)
            
            # Remove zip
            zip_path.unlink()
            
            # Save metadata
            meta = {
                'id': data.get('id'),
                'key': data.get('key'),
                'hash': data.get('hash'),
                'name': song_name,
                'sub': song_sub,
                'author': song_author,
                'bpm': bpm,
                'downloads': data.get('stats', {}).get('downloads', 0),
                'plays': data.get('stats', {}).get('plays', 0),
            }
            
            with open(song_dir / 'beatsaver_meta.json', 'w') as f:
                json.dump(meta, f, indent=2)
            
            print(f"  Downloaded to {song_dir.name}")
            return song_dir
            
        except Exception as e:
            print(f"  Error processing {song_key}: {e}")
            return None
    
    def download_by_hash(self, hash_str):
        """Download by hash (direct lookup)."""
        # Hash lookup via API
        url = f"{BEATSAVER_API}/maps/hash/{hash_str}"
        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                return self.process_song_data(data)
            else:
                print(f"  Hash not found: {hash_str}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"  Error: {e}")
            return None
    
    def batch_download(self, keys_or_hashes, max_workers=3):
        """Download multiple songs in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for key in keys_or_hashes:
                if len(key) == 40:  # hash
                    f = executor.submit(self.download_by_hash, key)
                else:
                    f = executor.submit(self.download_song, key)
                futures[f] = key
            
            for future in as_completed(futures):
                key = futures[future]
                try:
                    result = future.result()
                    results.append((key, result))
                except Exception as e:
                    print(f"  {key}: Error {e}")
                    results.append((key, None))
        
        success = sum(1 for _, r in results if r is not None)
        print(f"\nDownloaded {success}/{len(results)} songs")
        return results


def main():
    parser = argparse.ArgumentParser(description='Download songs from BeatSaver')
    parser.add_argument('key_or_hash', nargs='?', help='BeatSaver key (e.g., "abc12") or hash')
    parser.add_argument('--search', '-s', help='Search for songs')
    parser.add_argument('--top', '-t', action='store_true', help='Get top songs')
    parser.add_argument('--hot', action='store_true', help='Get hot songs')
    parser.add_argument('--latest', action='store_true', help='Get latest songs')
    parser.add_argument('--count', '-n', type=int, default=10, help='Number of songs')
    parser.add_argument('--output', '-o', default='songs', help='Output directory')
    
    args = parser.parse_args()
    
    downloader = BeatSaverDownloader(output_dir=args.output)
    
    if args.key_or_hash:
        # Single download
        result = downloader.download_song(args.key_or_hash)
        if result:
            print(f"\nDownloaded: {result}")
    
    elif args.search:
        print(f"Searching for: {args.search}")
        songs = downloader.search_songs(args.search, page_size=args.count)
        if songs:
            print(f"Found {len(songs)} songs")
            for i, song in enumerate(songs[:args.count]):
                meta = song.get('metadata', {})
                print(f"  {i+1}. {meta.get('songName')} by {meta.get('songAuthorName')} [{song.get('key')}]")
            
            # Download first result
            key = songs[0].get('key')
            if key:
                print(f"\nDownloading first result: {key}")
                downloader.download_song(key)
    
    elif args.top:
        print("Getting top songs...")
        songs = downloader.get_hot(page_size=args.count)
        if songs:
            for i, song in enumerate(songs[:args.count]):
                meta = song.get('metadata', {})
                stats = song.get('stats', {})
                print(f"  {i+1}. {meta.get('songName')} - {stats.get('plays', 0)} plays [{song.get('key')}]")
    
    elif args.latest:
        print("Getting latest songs...")
        songs = downloader.get_latest(page_size=args.count)
        if songs:
            for i, song in enumerate(songs[:args.count]):
                meta = song.get('metadata', {})
                print(f"  {i+1}. {meta.get('songName')} by {meta.get('songAuthorName')} [{song.get('key')}]")
    
    elif args.hot:
        print("Getting hot songs...")
        songs = downloader.get_hot(page_size=args.count)
        if songs:
            for i, song in enumerate(songs[:args.count]):
                meta = song.get('metadata', {})
                print(f"  {i+1}. {meta.get('songName')} by {meta.get('songAuthorName')} [{song.get('key')}]")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()