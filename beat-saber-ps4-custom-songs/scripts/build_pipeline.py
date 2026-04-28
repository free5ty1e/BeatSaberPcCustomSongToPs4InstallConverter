#!/usr/bin/env python3
"""
Beat Saber PS4 Custom Songs - Complete Build Pipeline
Combines all steps: Download, Convert, Build PKG, Create Unlocker

Based on/Inspired by:
- orbis-pub-sfo.exe: https://github.com/CyB1K/PS4-Fake-PKG-Tools-3.87
- orbis-pub-gen.exe: https://github.com/CyB1K/PS4-Fake-PKG-Tools-3.87
- psDLC.exe: https://github.com/codemasterv/psDLC-2.1-stooged-Mogi-PPSA-gui
"""
import os
import sys
import json
import gzip
import shutil
import struct
from pathlib import Path

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
SONGS_DIR = WORK_DIR / "songs"
OUTPUT_DIR = WORK_DIR / "output"
DLC_DIR = OUTPUT_DIR / "dlc_package"

# PS4 Constants
GAME_ID = "CUSA12878"
CONTENT_ID_PREFIX = "UP8802-CUSA12878_00"

class BeatSaberPipeline:
    """Complete pipeline for creating PS4 custom songs"""

    def __init__(self, content_id_suffix="BSCUSTOMSONGS01"):
        self.content_id = f"{CONTENT_ID_PREFIX}-{content_id_suffix}"
        self.title = "Beat Saber Custom Songs"
        self.songs = []

    def step1_download_songs(self):
        """Download songs from BeatSaver"""
        print("\n" + "="*60)
        print("STEP 1: Download Songs from BeatSaver")
        print("="*60)

        if not SONGS_DIR.exists():
            SONGS_DIR.mkdir(parents=True, exist_ok=True)

        # Check if songs already downloaded
        existing = [d for d in SONGS_DIR.iterdir() if d.is_dir()]
        if existing:
            print(f"Found {len(existing)} songs already downloaded:")
            for song in existing:
                print(f"  - {song.name}")
            return True

        print("No songs found. Please download manually:")
        print(f"  1. Go to https://beatsaver.com")
        print(f"  2. Download song ZIP files")
        print(f"  3. Extract to: {SONGS_DIR}")
        return False

    def step2_convert_songs(self):
        """Convert PC songs to PS4 format"""
        print("\n" + "="*60)
        print("STEP 2: Convert Songs to PS4 Format")
        print("="*60)

        converted_dir = OUTPUT_DIR / "converted_songs"
        converted_dir.mkdir(parents=True, exist_ok=True)

        songs = [d for d in SONGS_DIR.iterdir() if d.is_dir()]
        if not songs:
            print("No songs found to convert")
            return False

        success_count = 0

        for song_dir in songs:
            print(f"\nConverting: {song_dir.name}")

            # Find info.dat
            info_path = song_dir / "info.dat"
            if not info_path.exists():
                info_path = song_dir / "info.json"

            if not info_path.exists():
                print(f"  WARNING: No info.dat found")
                continue

            # Parse PC info
            try:
                with open(info_path, 'r') as f:
                    pc_info = json.load(f)
            except:
                print(f"  ERROR: Failed to parse info.dat")
                continue

            song_name = pc_info.get("_songName", song_dir.name)
            print(f"  Song: {song_name}")

            # Create output directory
            out_dir = converted_dir / song_dir.name.lower().replace(' ', '_')
            out_dir.mkdir(parents=True, exist_ok=True)

            # Copy audio
            self._convert_audio(song_dir, out_dir)

            # Copy cover
            self._convert_cover(song_dir, out_dir)

            # Convert beatmaps
            self._convert_beatmaps(song_dir, out_dir, pc_info)

            success_count += 1

        print(f"\nConverted {success_count}/{len(songs)} songs")
        return success_count > 0

    def _convert_audio(self, src_dir, dst_dir):
        """Copy and gzip audio"""
        for name in ["song.ogg", "song.wav", "audio.ogg", "audio.wav"]:
            src = src_dir / name
            if src.exists():
                # Copy original
                shutil.copy(src, dst_dir / "song.ogg")

                # Create gzipped version
                with open(src, 'rb') as f:
                    data = f.read()
                with gzip.open(dst_dir / "song.audio.gz", 'wb') as f:
                    f.write(data)
                print(f"  Audio: {name} -> song.ogg, song.audio.gz")
                return True
        print(f"  WARNING: No audio found")
        return False

    def _convert_cover(self, src_dir, dst_dir):
        """Copy cover image"""
        for name in ["cover.jpg", "cover.png", "cover.jpeg"]:
            src = src_dir / name
            if src.exists():
                shutil.copy(src, dst_dir / "cover.jpg")
                print(f"  Cover: {name}")
                return True
        print(f"  Cover: Not found (optional)")
        return False

    def _convert_beatmaps(self, src_dir, dst_dir, pc_info):
        """Convert PC beatmaps to PS4 v4.0.0 format"""
        # Get difficulty mappings
        difficulties = []

        if "_difficultyBeatmapSets" in pc_info:
            for set_info in pc_info["_difficultyBeatmapSets"]:
                if set_info.get("_beatmapCharacteristicName") != "Standard":
                    continue
                for diff in set_info.get("_difficultyBeatmaps", []):
                    difficulties.append((diff["_beatmapFilename"], diff["_difficulty"]))

        if "_difficultyBeatmaps" in pc_info:
            for diff in pc_info["_difficultyBeatmaps"]:
                difficulties.append((diff["_beatmapFilename"], diff["_difficulty"]))

        # PC to PS4 difficulty mapping
        diff_map = {"Easy": 0, "Normal": 1, "Hard": 2, "Expert": 3, "ExpertPlus": 4}

        for filename, diff_name in difficulties:
            src_path = src_dir / filename
            if not src_path.exists():
                continue

            # Read PC beatmap
            try:
                with open(src_path, 'r') as f:
                    pc_beatmap = json.load(f)
            except:
                print(f"  ERROR: Failed to parse {filename}")
                continue

            # Convert to PS4 v4.0.0 format
            ps4_beatmap = self._convert_beatmap_to_v4(pc_beatmap)

            # Get output filename
            diff_rank = diff_map.get(diff_name, 0)
            prefix = filename.split('.')[0]
            # Map to PS4 naming: Easy, Normal, Hard, Expert, ExpertPlus
            out_name = f"{prefix}.beatmap.gz"

            # Save gzipped JSON
            with gzip.open(dst_dir / out_name, 'wt', encoding='utf-8') as f:
                json.dump(ps4_beatmap, f, indent=None)

            print(f"  Beatmap: {filename} -> {out_name}")

    def _convert_beatmap_to_v4(self, pc_beatmap):
        """Convert PC beatmap JSON to PS4 v4.0.0 format"""
        ps4 = {"version": "4.0.0"}

        # Convert notes
        if "_notes" in pc_beatmap:
            color_notes = []
            color_notes_data = []
            seen_positions = set()

            for note in pc_beatmap["_notes"]:
                beat = note.get("_time", 0)
                x = note.get("_lineIndex", 0)
                y = note.get("_lineLayer", 0)
                note_type = note.get("_noteType", 0)
                direction = note.get("_cutDirection", 0)

                color_notes.append({"b": beat})

                pos_key = f"{x},{y},{note_type},{direction}"
                if pos_key not in seen_positions:
                    seen_positions.add(pos_key)
                    data = {"x": x, "d": direction}
                    if note_type == 0:
                        data["c"] = 0  # Red
                    elif note_type == 1:
                        data["c"] = 1  # Blue
                    color_notes_data.append(data)

            ps4["colorNotes"] = color_notes
            ps4["colorNotesData"] = color_notes_data
        else:
            ps4["colorNotes"] = []
            ps4["colorNotesData"] = []

        # Convert bombs
        if "_bombs" in pc_beatmap:
            bombs = []
            bombs_data = []
            for bomb in pc_beatmap["_bombs"]:
                bombs.append({"b": bomb.get("_time", 0)})
                bombs_data.append({"x": bomb.get("_lineIndex", 0)})
            ps4["bombNotes"] = bombs
            ps4["bombNotesData"] = bombs_data
        else:
            ps4["bombNotes"] = []
            ps4["bombNotesData"] = []

        # Convert obstacles
        if "_obstacles" in pc_beatmap:
            obstacles = []
            obstacles_data = []
            for obs in pc_beatmap["_obstacles"]:
                obstacles.append({"b": obs.get("_time", 0)})
                obstacles_data.append({
                    "x": obs.get("_lineIndex", 0),
                    "d": obs.get("_duration", 0),
                    "w": obs.get("_width", 1),
                    "h": obs.get("_height", 1)
                })
            ps4["obstacles"] = obstacles
            ps4["obstaclesData"] = obstacles_data
        else:
            ps4["obstacles"] = []
            ps4["obstaclesData"] = []

        # Empty required fields
        ps4["chains"] = []
        ps4["arcs"] = []
        ps4["spawnRotations"] = []
        ps4["spawnRotationsData"] = []

        return ps4

    def step3_create_dlc_structure(self):
        """Create DLC package directory structure"""
        print("\n" + "="*60)
        print("STEP 3: Create DLC Package Structure")
        print("="*60)

        # Create directories
        DLC_DIR.mkdir(parents=True, exist_ok=True)
        (DLC_DIR / "sce_sys").mkdir(exist_ok=True)
        (DLC_DIR / "StreamingAssets").mkdir(exist_ok=True)
        (DLC_DIR / "StreamingAssets/BeatmapLevelsData").mkdir(exist_ok=True)
        (DLC_DIR / "StreamingAssets/HmxAudioAssets/songs").mkdir(exist_ok=True)

        # Copy converted songs
        converted_dir = OUTPUT_DIR / "converted_songs"
        if converted_dir.exists():
            songs = list(converted_dir.iterdir())
            print(f"Copying {len(songs)} songs to DLC...")

            for song in songs:
                dst = DLC_DIR / "StreamingAssets/BeatmapLevelsData" / song.name
                shutil.copytree(song, dst, dirs_exist_ok=True)

        print(f"DLC structure created at: {DLC_DIR}")
        return True

    def step4_create_paramsfo(self):
        """Create PARAM.SFO file"""
        print("\n" + "="*60)
        print("STEP 4: Create PARAM.SFO")
        print("="*60)

        # Import the paramsfo module
        sys.path.insert(0, str(WORK_DIR / "scripts"))
        from create_paramsfo import create_dlc_paramsfo

        paramsfo_path = DLC_DIR / "sce_sys" / "param.sfo"
        create_dlc_paramsfo(self.content_id, self.title, str(paramsfo_path))

        return paramsfo_path.exists()

    def step5_build_pkg(self):
        """Build PS4 PKG"""
        print("\n" + "="*60)
        print("STEP 5: Build PS4 PKG")
        print("="*60)

        sys.path.insert(0, str(WORK_DIR / "scripts"))
        from create_pkg import create_dlc_pkg

        pkg_path = OUTPUT_DIR / f"{self.content_id}.pkg"
        create_dlc_pkg(str(DLC_DIR), self.content_id, str(pkg_path))

        return pkg_path.exists()

    def step6_create_unlocker(self):
        """Create DLC unlocker PKG"""
        print("\n" + "="*60)
        print("STEP 6: Create DLC Unlocker")
        print("="*60)

        sys.path.insert(0, str(WORK_DIR / "scripts"))
        from create_unlocker import create_unlocker

        unlocker_path = OUTPUT_DIR / f"{self.content_id}-unlock.pkg"
        create_unlocker(self.content_id, str(unlocker_path))

        return unlocker_path.exists()

    def run(self):
        """Run complete pipeline"""
        print("="*60)
        print("BEAT SABER PS4 CUSTOM SONGS - BUILD PIPELINE")
        print("="*60)
        print(f"Content ID: {self.content_id}")
        print(f"Title: {self.title}")
        print()

        results = {
            "Download Songs": self.step1_download_songs(),
            "Convert Songs": self.step2_convert_songs(),
            "Create DLC Structure": self.step3_create_dlc_structure(),
            "Create PARAM.SFO": self.step4_create_paramsfo(),
            "Build PKG": self.step5_build_pkg(),
            "Create Unlocker": self.step6_create_unlocker(),
        }

        print("\n" + "="*60)
        print("RESULTS")
        print("="*60)

        all_success = True
        for step, success in results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {step}")
            if not success and step != "Download Songs":
                all_success = False

        if all_success:
            print("\n" + "="*60)
            print("BUILD COMPLETE!")
            print("="*60)
            print(f"\nOutput files:")
            print(f"  DLC PKG: {OUTPUT_DIR}/{self.content_id}.pkg")
            print(f"  Unlocker: {OUTPUT_DIR}/{self.content_id}-unlock.pkg")
            print(f"\nCopy both files to USB and install on PS4 with GoldHEN")
        else:
            print("\nBuild completed with warnings. Check above.")

        return all_success

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Beat Saber PS4 Custom Songs Build Pipeline')
    parser.add_argument('--content-id', '-c', default='BSCUSTOMSONGS01',
                        help='Content ID suffix (default: BSCUSTOMSONGS01)')

    args = parser.parse_args()

    pipeline = BeatSaberPipeline(args.content_id)
    success = pipeline.run()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()