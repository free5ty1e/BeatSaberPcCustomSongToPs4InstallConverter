#!/usr/bin/env python3
"""
Beat Saber PS4 Custom Song Converter
Converts PC BeatSaver songs to PS4 format
Based on analysis of exported 100bills song
"""
import json
import gzip
import os
import shutil
import struct
from pathlib import Path
import hashlib

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
SONGS_DIR = WORK_DIR / "songs"
OUTPUT_DIR = WORK_DIR / "output" / "converted_songs"
TEMPLATE_DIR = WORK_DIR / "templates"

class BeatSaberConverter:
    """Converts PC BeatSaver songs to PS4 format"""

    # PS4 Song structure (from 100bills analysis)
    PS4_SONG_STRUCTURE = {
        "name": "BeatmapLevelDataSO",  # Script class name
        "scriptGuid": "2e9d2a8ca85864f80409c28a1c68e82d",  # Script reference
        "beatmapVersion": "4.0.0",
        "audioFormat": ".ogg",
        "coverFormat": ".jpg",
    }

    # Difficulty mapping (PC -> PS4)
    DIFFICULTY_MAP = {
        "Easy": 0,
        "Normal": 1,
        "Hard": 2,
        "Expert": 3,
        "ExpertPlus": 4,
    }

    # Note types (PC -> PS4)
    # PC: 0=Red, 1=Blue, 2=Bomb
    # PS4: Uses colorNotesData with 'd' field for direction

    def __init__(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def convert_song(self, pc_song_path):
        """Convert a PC BeatSaver song to PS4 format"""
        song_name = pc_song_path.name
        print(f"\n{'='*60}")
        print(f"CONVERTING: {song_name}")
        print(f"{'='*60}")

        # Find info.dat
        info_path = self._find_file(pc_song_path, ["info.dat", "info.json"])
        if not info_path:
            print(f"  ERROR: No info.dat found")
            return False

        # Parse PC info
        with open(info_path, 'r') as f:
            pc_info = json.load(f)

        print(f"  Song: {pc_info.get('_songName', 'Unknown')}")
        print(f"  Author: {pc_info.get('_songAuthorName', 'Unknown')}")
        print(f"  Mapper: {pc_info.get('_levelAuthorName', 'Unknown')}")
        print(f"  BPM: {pc_info.get('_beatsPerMinute', 120)}")

        # Create output directory
        safe_name = self._make_safe_filename(song_name)
        output_dir = OUTPUT_DIR / safe_name
        output_dir.mkdir(parents=True, exist_ok=True)

        # Convert audio
        self._convert_audio(pc_song_path, output_dir)

        # Convert cover
        self._convert_cover(pc_song_path, output_dir)

        # Convert beatmaps
        self._convert_beatmaps(pc_song_path, output_dir, pc_info)

        # Create level data asset
        self._create_level_data(output_dir, pc_info)

        print(f"  SUCCESS: {output_dir}")
        return True

    def _find_file(self, directory, names):
        """Find a file by possible names"""
        for name in names:
            path = directory / name
            if path.exists():
                return path
        return None

    def _make_safe_filename(self, name):
        """Make filename safe for all systems"""
        safe = name.replace('/', '_').replace('\\', '_').replace('..', '_')
        return safe[:50]

    def _convert_audio(self, pc_path, output_path):
        """Convert audio - just copy OGG for now"""
        audio_path = self._find_file(pc_path, ["song.ogg", "song.wav", "audio.ogg", "audio.wav"])
        if audio_path:
            output_audio = output_path / "song.ogg"
            shutil.copy(audio_path, output_audio)
            print(f"  Audio: {audio_path.name} -> song.ogg")

            # Also create gzipped version like PS4
            with open(output_audio, 'rb') as f:
                audio_data = f.read()
            gz_path = output_path / "song.audio.gz"
            with gzip.open(gz_path, 'wb') as f:
                f.write(audio_data)
            print(f"  Audio (gz): song.audio.gz")
        else:
            print(f"  WARNING: No audio file found")

    def _convert_cover(self, pc_path, output_path):
        """Convert cover image"""
        cover_path = self._find_file(pc_path, ["cover.jpg", "cover.png", "album.jpg"])
        if cover_path:
            output_cover = output_path / "cover.jpg"
            if cover_path.suffix == '.png':
                print(f"  Cover: {cover_path.name} (PNG - may need conversion)")
            else:
                shutil.copy(cover_path, output_cover)
                print(f"  Cover: {cover_path.name} -> cover.jpg")

    def _convert_beatmaps(self, pc_path, output_path, pc_info):
        """Convert beatmaps from PC format to PS4 v4.0.0 JSON format"""
        print(f"  Beatmaps:")

        # Get difficulty files from info.dat
        difficulty_files = self._get_difficulty_files(pc_info)

        for pc_diff, diff_name in difficulty_files:
            pc_beatmap_path = pc_path / pc_diff
            if not pc_beatmap_path.exists():
                print(f"    SKIP: {pc_diff} not found")
                continue

            # Read PC beatmap
            with open(pc_beatmap_path, 'r') as f:
                pc_beatmap = json.load(f)

            # Convert to PS4 format
            ps4_beatmap = self._convert_beatmap(pc_beatmap)

            # Save as gzipped JSON
            ps4_filename = f"{pc_diff.split('.')[0]}.beatmap.gz"
            ps4_path = output_path / ps4_filename

            with gzip.open(ps4_path, 'wt', encoding='utf-8') as f:
                json.dump(ps4_beatmap, f)

            print(f"    {pc_diff} -> {ps4_filename}")

    def _get_difficulty_files(self, pc_info):
        """Extract difficulty file mappings from PC info.dat"""
        result = []

        # New format
        if "_difficultyBeatmapSets" in pc_info:
            for set_info in pc_info["_difficultyBeatmapSets"]:
                characteristic = set_info.get("_beatmapCharacteristicName", "Standard")
                if characteristic != "Standard":
                    continue
                for diff in set_info.get("_difficultyBeatmaps", []):
                    result.append((diff["_beatmapFilename"], diff["_difficulty"]))

        # Old format
        if "_difficultyBeatmaps" in pc_info:
            for diff in pc_info["_difficultyBeatmaps"]:
                result.append((diff["_beatmapFilename"], diff["_difficulty"]))

        return result

    def _convert_beatmap(self, pc_beatmap):
        """Convert PC beatmap to PS4 v4.0.0 format"""
        ps4 = {"version": "4.0.0"}

        # Convert notes
        if "_notes" in pc_beatmap:
            pc_notes = pc_beatmap["_notes"]
            color_notes = []
            color_notes_data = []

            # Track unique positions
            used_positions = set()
            position_map = {}

            for note in pc_notes:
                beat = note.get("_time", 0)
                line_index = note.get("_lineIndex", 0)
                line_layer = note.get("_lineLayer", 0)
                note_type = note.get("_noteType", 0)
                cut_direction = note.get("_cutDirection", 0)

                # Basic note entry with just timing
                color_notes.append({"b": beat})

                # Position data entry
                # Note type: 0=Red (left), 1=Blue (right), 2=Bomb, 3=Debris
                direction = self._map_cut_direction(cut_direction, note_type)

                # Track unique positions
                pos_key = (line_index, line_layer, note_type, direction)
                if pos_key not in used_positions:
                    used_positions.add(pos_key)
                    idx = len(color_notes_data)
                    position_map[pos_key] = idx
                    color_notes_data.append({"x": line_index, "d": direction})
                    if note_type == 0:  # Red note
                        color_notes_data[idx]["c"] = 0
                    elif note_type == 1:  # Blue note
                        color_notes_data[idx]["c"] = 1

            ps4["colorNotes"] = color_notes
            ps4["colorNotesData"] = color_notes_data

        # Convert bombs
        if "_bombs" in pc_beatmap:
            bombs = []
            bomb_data = []

            for bomb in pc_beatmap["_bombs"]:
                beat = bomb.get("_time", 0)
                line_index = bomb.get("_lineIndex", 0)
                line_layer = bomb.get("_lineLayer", 0)

                bombs.append({"b": beat})

                # Check if position already exists
                pos_key = ("bomb", line_index, line_layer)
                if pos_key not in bomb_data:
                    bomb_data.append({"x": line_index})

            ps4["bombNotes"] = bombs
            ps4["bombNotesData"] = bomb_data

        # Convert obstacles
        if "_obstacles" in pc_beatmap:
            obstacles = []
            obstacles_data = []

            for obs in pc_beatmap["_obstacles"]:
                beat = obs.get("_time", 0)
                duration = obs.get("_duration", 0)
                line_index = obs.get("_lineIndex", 0)
                line_layer = obs.get("_lineLayer", 0)
                width = obs.get("_width", 1)
                height = obs.get("_height", 1)

                obstacles.append({"b": beat})

                # Position data
                obstacles_data.append({
                    "x": line_index,
                    "d": duration,
                    "w": width,
                    "h": height
                })

            ps4["obstacles"] = obstacles
            ps4["obstaclesData"] = obstacles_data

        # Empty fields (required by format)
        ps4["chains"] = pc_beatmap.get("_chains", [])
        ps4["arcs"] = pc_beatmap.get("_sliders", [])
        ps4["spawnRotations"] = []

        return ps4

    def _map_cut_direction(self, cut_direction, note_type):
        """Map PC cut direction to PS4 direction value"""
        # PC cut directions: 0=Up, 1=Down, 2=Left, 3=Right, 4=UpLeft, 5=UpRight, 6=DownLeft, 7=DownRight, 8=Any
        # PS4 direction values need testing - using basic mapping

        if note_type == 2:  # Bomb
            return 0

        # Basic direction mapping
        direction_map = {
            0: 0,   # Up -> 0
            1: 1,   # Down -> 1
            2: 2,   # Left -> 2
            3: 3,   # Right -> 3
            4: 4,   # UpLeft -> 4
            5: 5,   # UpRight -> 5
            6: 6,   # DownLeft -> 6
            7: 7,   # DownRight -> 7
            8: 0,   # Any -> Up (default)
        }

        return direction_map.get(cut_direction, 0)

    def _create_level_data(self, output_path, pc_info):
        """Create Unity .asset file for level data"""
        song_name = pc_info.get("_songName", "Unknown")
        safe_name = self._make_safe_filename(song_name)

        # Create YAML asset file
        asset_content = f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!114 &11400000
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 0}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: 2e9d2a8ca85864f80409c28a1c68e82d, type: 3}}
  m_Name: {safe_name}BeatmapLevelData
  m_EditorClassIdentifier:
  _version: 1
  _audioClip: {{fileID: 0}}
  _audioDataAsset: {{fileID: 0}}
  _difficultyBeatmapSets:
"""

        # Add difficulty beatmaps
        difficulty_files = self._get_difficulty_files(pc_info)
        beatmap_guids = [
            "608e1eaaf602afb408cba284159bb38f",  # Easy
            "35b0a9136f5d02948a1360b638618842",  # Normal
            "36ba0224237857343b012cac90192e18",  # Hard
            "64d67198674331f438803d31912102c7",  # Expert
            "19e89385ca153da4fbf363d827e58dca",  # ExpertPlus
        ]

        asset_content += """  - _beatmapCharacteristicSerializedName: Standard
    _difficultyBeatmaps:
"""

        for i, diff in enumerate(difficulty_files[:5]):
            difficulty = self._get_difficulty_rank(diff[1])
            beatmap_guid = beatmap_guids[i] if i < len(beatmap_guids) else beatmap_guids[0]
            asset_content += f"""    - _difficulty: {difficulty}
      _beatmapAsset: {{fileID: 4900000, guid: {beatmap_guid}, type: 3}}
      _lightshowAsset: {{fileID: 4900000, guid: 4572c48a560d9ff479c0aa9405afe3f5, type: 3}}
"""

        asset_path = output_path / f"{safe_name}BeatmapLevelData.asset"
        with open(asset_path, 'w') as f:
            f.write(asset_content)

        print(f"  Level Data: {asset_path.name}")

    def _get_difficulty_rank(self, difficulty):
        """Get PS4 difficulty rank from name"""
        return self.DIFFICULTY_MAP.get(difficulty, 0)

    def convert_all_songs(self):
        """Convert all songs in songs directory"""
        print("=" * 60)
        print("BATCH CONVERSION - PC to PS4")
        print("=" * 60)

        if not SONGS_DIR.exists():
            print(f"ERROR: Songs directory not found: {SONGS_DIR}")
            print("Place downloaded songs in this directory")
            return

        songs = [d for d in SONGS_DIR.iterdir() if d.is_dir()]
        print(f"Found {len(songs)} songs to convert")

        success = 0
        failed = 0

        for song in songs:
            if self.convert_song(song):
                success += 1
            else:
                failed += 1

        print(f"\n{'='*60}")
        print(f"RESULTS: {success} succeeded, {failed} failed")
        print(f"{'='*60}")
        print(f"Output: {OUTPUT_DIR}")

def create_test_song():
    """Create a minimal test song to verify format"""
    print("\n" + "=" * 60)
    print("CREATING TEST SONG")
    print("=" * 60)

    test_dir = OUTPUT_DIR / "test_song"
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create minimal beatmap
    test_beatmap = {
        "version": "4.0.0",
        "colorNotes": [{"b": 8.0}, {"b": 12.0}, {"b": 16.0}],
        "colorNotesData": [
            {"x": 0, "d": 0, "c": 0},
            {"x": 2, "d": 1, "c": 1},
            {"x": 1, "d": 3, "c": 0}
        ],
        "bombNotes": [],
        "bombNotesData": [],
        "obstacles": [],
        "obstaclesData": [],
        "chains": [],
        "arcs": [],
        "spawnRotations": [],
        "spawnRotationsData": []
    }

    with gzip.open(test_dir / "test.beatmap.gz", 'wt') as f:
        json.dump(test_beatmap, f)

    print(f"  Created test song at: {test_dir}")

def main():
    print("=" * 60)
    print("BEAT SABER PS4 CUSTOM SONG CONVERTER")
    print("=" * 60)

    converter = BeatSaberConverter()

    import sys
    if len(sys.argv) > 1:
        # Convert specific song
        song_path = Path(sys.argv[1])
        converter.convert_song(song_path)
    else:
        # Convert all songs
        converter.convert_all_songs()

    # Create test song for reference
    create_test_song()

if __name__ == "__main__":
    main()