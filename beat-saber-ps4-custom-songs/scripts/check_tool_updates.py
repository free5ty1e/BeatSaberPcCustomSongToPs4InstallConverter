#!/usr/bin/env python3
"""
Check for updates to build tools.

Usage:
    python3 scripts/check_tool_updates.py
"""
import json
import urllib.request
from pathlib import Path

TOOLS = {
    "orbis-pub-gen": {
        "repo": "CyB1K/PS4-Fake-PKG-Tools-3.87",
        "current": "v7",
        "url_pattern": "https://github.com/{repo}/releases/download/{version}/"
    },
    "wine-mono": {
        "repo": "winehq/wine",
        "current": "8.1.0",
        "url": "https://dl.winehq.org/wine/wine-mono/"
    }
}

def check_orbis_updates():
    """Check for orbis-pub-gen updates."""
    repo = TOOLS["orbis-pub-gen"]["repo"]
    try:
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Python')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            latest = data.get('tag_name', 'unknown')
            
        current = TOOLS["orbis-pub-gen"]["current"]
        print(f"orbis-pub-gen: {current} -> {latest}")
        
        return latest != current
        
    except Exception as e:
        print(f"Error checking orbis: {e}")
        return False

def check_all_updates():
    """Check all tools for updates."""
    print("=" * 50)
    print("CHECKING FOR TOOL UPDATES")
    print("=" * 50)
    
    has_updates = False
    
    print("\n--- ORBIS TOOLS ---")
    if check_orbis_updates():
        has_updates = True
    
    # Add more tools as needed
    
    print("\n" + "=" * 50)
    if has_updates:
        print("⚠️  UPDATES AVAILABLE")
    else:
        print("✓ All tools up to date")
    print("=" * 50)
    
    return has_updates

if __name__ == "__main__":
    check_all_updates()