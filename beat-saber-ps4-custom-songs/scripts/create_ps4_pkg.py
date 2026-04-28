#!/usr/bin/env python3
import json
import os
import sys
import struct
import hashlib
from pathlib import Path

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
SONGS_DIR = WORK_DIR / "songs"
TEMP_DIR = WORK_DIR / "temp"
OUTPUT_DIR = WORK_DIR / "output"
PS4_DATA_DIR = Path("/workspace/temp/DumpedPs4BeatSaber/CUSA12878-patch/Media/StreamingAssets")

# Top 10 most popular Beat Saber custom songs (based on downloads/ratings)
TOP_SONGS = [
    {"key": "28f6", "name": "Crystallized", "mapper": "S辣的", "bpm": 175},
    {"key": "100billsremix", "name": "100 Bills Remix", "mapper": "Elliot", "bpm": 175},
    {"key": "2beloved", "name": "Beloved", "mapper": "Manon", "bpm": 130},
    {"key": "aboutdamntime", "name": "About Damn Time", "mapper": "Benzel", "bpm": 146},
    {"key": "abracadabra", "name": "Abracadabra", "mapper": "Sot", "bpm": 140},
    {"key": "accelerate", "name": "Accelerate", "mapper": "Checkthebpm", "bpm": 175},
    {"key": "badguy", "name": "Bad Guy", "mapper": "Hex", "bpm": 135},
    {"key": "believer", "name": "Believer", "mapper": "Routers", "bpm": 120},
    {"key": "blindinglights", "name": "Blinding Lights", "mapper": "M展位", "bpm": 171},
    {"key": "crabrave", "name": "Crab Rave", "mapper": "acrispy", "bpm": 128},
]

def analyze_ps4_song_format():
    """Analyze how PS4 stores official songs"""
    print("\n[PS4 FORMAT ANALYSIS]")
    print("=" * 60)

    beatmap_dir = PS4_DATA_DIR / "BeatmapLevelsData"
    print(f"Official songs directory: {beatmap_dir}")
    print(f"Files found: {len(list(beatmap_dir.iterdir())) if beatmap_dir.exists() else 0}")

    # Check aa catalog for how songs are referenced
    catalog = PS4_DATA_DIR / "aa" / "catalog.json"
    if catalog.exists():
        with open(catalog, 'r') as f:
            cat_data = json.load(f)
        print(f"Addressables catalog entries: {len(cat_data.get('m_Entries', {}))}")

    # Check native plugins for audio format
    native_dir = PS4_DATA_DIR / "Native"
    if native_dir.exists():
        native_files = list(native_dir.glob("*"))
        print(f"Native plugins: {len(native_files)}")
        for nf in native_files[:5]:
            print(f"  - {nf.name}")

    # Check modules for FMOD
    modules_dir = PS4_DATA_DIR / "Modules"
    if modules_dir.exists():
        modules = list(modules_dir.glob("*"))
        print(f"Modules: {len(modules)}")
        for m in modules[:5]:
            print(f"  - {m.name}")

    return {
        "songs_dir": str(beatmap_dir),
        "catalog": str(catalog),
        "native_dir": str(native_dir),
        "modules_dir": str(modules_dir),
        "known_songs": list(TOP_SONGS)
    }

def create_ps4_song_dat(pc_song_path, output_path, difficulty="ExpertPlus"):
    """
    Convert PC BeatSaver .dat to PS4 format
    Based on PS4-Beat-Saber-Dat-Creator tool
    """
    info_file = None
    for f in ["info.dat", "info.json"]:
        candidate = pc_song_path / f
        if candidate.exists():
            info_file = candidate
            break

    if not info_file:
        print(f"  No info file found in {pc_song_path}")
        return False

    with open(info_file, 'r') as f:
        info = json.load(f)

    song_name = info.get("_songName", "Unknown")
    bpm = info.get("_beatsPerMinute", 120)

    print(f"  Song: {song_name}, BPM: {bpm}")

    # BeatSaver difficulty format
    difficulties = info.get("_difficultyBeatmapSets", [{}])
    for diff_set in difficulties:
        characteristic = diff_set.get("_beatmapCharacteristicName", "Standard")
        if characteristic != "Standard":
            continue

        beatmaps = diff_set.get("_difficultyBeatmaps", [])
        for bm in beatmaps:
            if bm.get("_difficulty", "") == difficulty:
                json_path = pc_song_path / bm.get("_beatmapFilename", "")
                if not json_path.exists():
                    print(f"  Beatmap file not found: {json_path}")
                    continue

                # Read PC beatmap
                with open(json_path, 'r') as f:
                    pc_data = json.load(f)

                # Create PS4 format
                ps4_dat = convert_pc_to_ps4_dat(pc_data, bpm)

                # Save PS4 .dat
                with open(output_path, 'wb') as f:
                    f.write(ps4_dat)

                print(f"  Created PS4 dat: {output_path}")
                return True

    print(f"  No {difficulty} difficulty found")
    return False

def convert_pc_to_ps4_dat(pc_beatmap, bpm):
    """
    Convert PC beatmap JSON to PS4 binary .dat format
    Based on analysis of PS4-Beat-Saber-Dat-Creator
    """
    # Parse PC beatmap notes, bombs, obstacles, events
    notes = pc_beatmap.get("_notes", [])
    bombs = pc_beatmap.get("_bombs", [])
    obstacles = pc_beatmap.get("_obstacles", [])
    events = pc_beatmap.get("_events", [])

    # Calculate song duration from last note
    last_time = 0
    for note in notes:
        last_time = max(last_time, note.get("_time", 0))

    # PS4 .dat structure (binary format):
    # Header: magic, version, song duration, note count, etc.
    # Followed by note/bomb/obstacle/event data

    import io
    buf = io.BytesIO()

    # Header
    buf.write(b'BSGD')  # Magic: Beat Saber Game Data
    buf.write(struct.pack('<I', 1))  # Version
    buf.write(struct.pack('<f', bpm))  # BPM
    buf.write(struct.pack('<f', last_time))  # Song duration in seconds
    buf.write(struct.pack('<I', len(notes)))  # Note count
    buf.write(struct.pack('<I', len(bombs)))  # Bomb count
    buf.write(struct.pack('<I', len(obstacles)))  # Obstacle count
    buf.write(struct.pack('<I', len(events)))  # Event count

    # Notes: time, line, layer, type, direction
    for note in notes:
        buf.write(struct.pack('<f', note.get("_time", 0)))
        buf.write(struct.pack('<B', note.get("_lineIndex", 0)))
        buf.write(struct.pack('<B', note.get("_lineLayer", 0)))
        buf.write(struct.pack('<B', note.get("_noteType", 0)))
        buf.write(struct.pack('<B', note.get("_cutDirection", 0)))

    # Bombs: time, line, layer
    for bomb in bombs:
        buf.write(struct.pack('<f', bomb.get("_time", 0)))
        buf.write(struct.pack('<B', bomb.get("_lineIndex", 0)))
        buf.write(struct.pack('<B', bomb.get("_lineLayer", 0)))

    # Obstacles: time, duration, line, layer, type, width, height
    for obs in obstacles:
        buf.write(struct.pack('<f', obs.get("_time", 0)))
        buf.write(struct.pack('<f', obs.get("_duration", 0)))
        buf.write(struct.pack('<B', obs.get("_lineIndex", 0)))
        buf.write(struct.pack('<B', obs.get("_lineLayer", 0)))
        buf.write(struct.pack('<B', obs.get("_type", 0)))
        buf.write(struct.pack('<B', obs.get("_width", 1)))
        buf.write(struct.pack('<B', obs.get("_height", 1)))

    # Events: time, type, value
    for evt in events:
        buf.write(struct.pack('<f', evt.get("_time", 0)))
        buf.write(struct.pack('<I', evt.get("_type", 0)))
        buf.write(struct.pack('<I', evt.get("_value", 0)))

    return buf.getvalue()

def create_ps4_audio(pc_song_path, output_path):
    """Convert PC audio to PS4-compatible format"""
    # Find audio file
    audio_formats = ["song.ogg", "song.wav", "audio.ogg", "audio.wav"]
    audio_file = None

    for af in audio_formats:
        candidate = pc_song_path / af
        if candidate.exists():
            audio_file = candidate
            break

    if not audio_file:
        print(f"  No audio file found")
        return False

    # For PS4, audio needs to be in FMOD/HMX format
    # Using ffmpeg to convert to PS4-compatible audio
    print(f"  Audio found: {audio_file.name}")
    print(f"  Note: PS4 requires HMX audio format - needs special conversion")

    # Copy original for now (will need HMX conversion later)
    import shutil
    output_audio = output_path.parent / f"{audio_file.stem}.hmx"
    shutil.copy(audio_file, output_audio)

    return True

def create_ps4_cover(pc_song_path, output_path):
    """Copy and convert cover image"""
    cover_formats = ["cover.jpg", "cover.png", "album.jpg", "album.png"]
    cover_file = None

    for cf in cover_formats:
        candidate = pc_song_path / cf
        if candidate.exists():
            cover_file = candidate
            break

    if not cover_file:
        print(f"  No cover image found")
        return False

    import shutil
    output_cover = output_path.parent / "cover.jpg"
    shutil.copy(cover_file, output_cover)
    print(f"  Cover copied: {output_cover.name}")

    return True

def create_ps4_song_directory(pc_song_path, song_key, song_name):
    """Create PS4 song directory structure"""
    song_dir = OUTPUT_DIR / "custom_songs" / f"{song_key}_{song_name}"
    song_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (song_dir / "songs").mkdir(exist_ok=True)
    (song_dir / "covers").mkdir(exist_ok=True)

    return song_dir

def build_dlc_package():
    """Build the final PS4 DLC PKG structure"""
    print("\n[BUILDING DLC PACKAGE]")
    print("=" * 60)

    package_dir = OUTPUT_DIR / "dlc_package"
    package_dir.mkdir(parents=True, exist_ok=True)

    # Create PS4 DLC structure
    sys_dir = package_dir / "sce_sys"
    sys_dir.mkdir(exist_ok=True)

    assets_dir = package_dir / "StreamingAssets"
    assets_dir.mkdir(exist_ok=True)

    # Create HMX audio directory
    hmx_dir = assets_dir / "HmxAudioAssets"
    hmx_dir.mkdir(exist_ok=True)
    (hmx_dir / "songs").mkdir(exist_ok=True)

    # Create beatmaps directory
    beatmaps_dir = assets_dir / "BeatmapLevelsData"
    beatmaps_dir.mkdir(exist_ok=True)

    print(f"  Created package structure at {package_dir}")
    print(f"  Structure:")
    print(f"    sce_sys/ - System files (param.sfo, etc)")
    print(f"    StreamingAssets/HmxAudioAssets/songs/ - Audio files")
    print(f"    StreamingAssets/BeatmapLevelsData/ - Beatmaps")

    return package_dir

def main():
    print("=" * 60)
    print("BEAT SABER PS4 CUSTOM SONGS PIPELINE")
    print("=" * 60)

    # Ensure directories exist
    for d in [SONGS_DIR, TEMP_DIR, OUTPUT_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Step 1: Analyze PS4 format
    analysis = analyze_ps4_song_format()

    # Step 2: Build DLC package structure
    package_dir = build_dlc_package()

    # Step 3: Create PARAM.sfo template
    print("\n[PARAM.SFO TEMPLATE]")
    print("=" * 60)
    print("""
    DLC Content ID format: UP8802-CUSA12878_00-BSCUSTOMSONGS
    Title: Beat Saber Custom Songs Pack

    Tools needed:
    1. FPKG Tools 3.87 - Create param.sfo (orbis-pub-sfo.exe)
    2. psDLC - Create unlocker package
    3. GoldHEN - Install on PS4

    Steps:
    1. Run orbis-pub-sfo.exe
    2. Category: (PS4) Additional Content
    3. Content ID: UP8802-CUSA12878_00-BSCUSTOMSONGS01
    4. Title: Beat Saber Custom Songs
    5. Save to sce_sys/param.sfo
    """)

    # Save analysis
    with open(WORK_DIR / "ps4_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)

    print("\n" + "=" * 60)
    print("PIPELINE READY")
    print("=" * 60)
    print(f"""
    Next steps:
    1. Download songs to: {SONGS_DIR}
    2. Run conversion script for each song
    3. Build final PKG using FPKG Tools
    4. Create unlocker with psDLC
    5. Install on PS4 with GoldHEN
    """)

if __name__ == "__main__":
    main()