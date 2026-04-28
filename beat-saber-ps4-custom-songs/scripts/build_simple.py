#!/usr/bin/env python3
"""
Beat Saber PS4 Custom Songs - Build PKG with available beatmaps
Creates a DLC PKG even if audio files are missing
"""
import json
import gzip
import shutil
import struct
import os
from pathlib import Path

WORK_DIR = Path("/workspace/beat-saber-ps4-custom-songs")
SONGS_DIR = WORK_DIR / "songs"
OUTPUT_DIR = WORK_DIR / "output"
DLC_DIR = OUTPUT_DIR / "dlc_package"

GAME_ID = "CUSA12878"
CONTENT_ID = f"UP8802-{GAME_ID}_00-BSCUSTOMSONGS01"

class PS4PKGBuilder:
    """Simple PS4 PKG Builder for DLC"""

    MAGIC = b'\x7F\xD8\xCF\x63'

    def __init__(self, content_id):
        self.content_id = content_id
        self.files = []

    def add_file(self, path, data):
        self.files.append((path, data))

    def build(self):
        import io
        import hashlib

        header_size = 0xC0
        toc_size = len(self.files) * 0x20
        data_start = header_size + toc_size

        # Align data start
        if data_start % 0x10 != 0:
            data_start = (data_start // 0x10 + 1) * 0x10

        buf = io.BytesIO()

        # Header
        buf.write(self.MAGIC)
        buf.write(b'\x01\x00\x00\x00')  # Version
        buf.write(b'\x00\x00\x00\x00')  # Type
        buf.write(struct.pack('<I', 0x00480000))  # Data offset
        buf.write(struct.pack('<I', 0))  # Data size (placeholder)
        buf.write(struct.pack('<I', len(self.files)))  # Entry count
        buf.write(b'\x00' * 0x10)  # Unknown
        buf.write(struct.pack('<I', 0))  # Metadata offset
        buf.write(struct.pack('<I', 0))  # Metadata size
        buf.write(b'\x00' * 0x3C)  # Padding

        # Content ID
        cid = self.content_id.encode('utf-8').ljust(48, b'\x00')
        buf.write(cid)
        buf.write(struct.pack('<Q', 0))  # Title ID
        buf.write(struct.pack('<Q', 0))  # Type
        buf.write(struct.pack('<Q', 0x05005000))  # System version
        buf.write(struct.pack('<Q', 0x00010030))  # App version
        buf.write(b'\x00' * 0x18)  # Padding

        # Ensure we're at header_size
        while buf.tell() < header_size:
            buf.write(b'\x00')

        # TOC entries
        data_offset = data_start
        for path, data in self.files:
            path_bytes = path.replace('\\', '/').encode('utf-8')
            buf.write(struct.pack('<Q', 0))  # Flags
            buf.write(struct.pack('<Q', data_offset))  # Offset
            buf.write(struct.pack('<I', len(data)))  # Size
            buf.write(struct.pack('<I', len(path_bytes) + 1))  # Name size
            buf.write(path_bytes)
            buf.write(b'\x00')
            # Pad to 0x20
            while buf.tell() % 0x20 != 0:
                buf.write(b'\x00')
            data_offset += len(data)
            if data_offset % 0x10 != 0:
                data_offset = (data_offset // 0x10 + 1) * 0x10

        # Data
        while buf.tell() < data_start:
            buf.write(b'\x00')

        for path, data in self.files:
            buf.write(data)
            # Align
            while buf.tell() % 0x10 != 0:
                buf.write(b'\x00')

        return buf.getvalue()

    def save(self, path):
        data = self.build()
        with open(path, 'wb') as f:
            f.write(data)
        print(f"Created PKG: {path} ({len(data):,} bytes)")

def create_paramsfo(content_id, title):
    """Create PARAM.SFO"""
    paramsfo = bytearray(0x400)
    paramsfo[0:4] = b'PSF\x00'
    # Add minimal content
    content_id_bytes = content_id.encode('utf-8')
    paramsfo[0x6C:0x6C+len(content_id_bytes)] = content_id_bytes
    return bytes(paramsfo)

def convert_beatmap(pc_dat_path, output_name):
    """Convert PC beatmap to PS4 gzipped JSON v4.0.0 format"""
    try:
        with open(pc_dat_path, 'r') as f:
            pc_data = json.load(f)

        # Convert to v4.0.0 format
        ps4 = {"version": "4.0.0"}

        # Notes
        if "_notes" in pc_data:
            color_notes = [{"b": n["_time"]} for n in pc_data["_notes"]]
            ps4["colorNotes"] = color_notes
            ps4["colorNotesData"] = []
        else:
            ps4["colorNotes"] = []
            ps4["colorNotesData"] = []

        # Bombs
        if "_bombs" in pc_data:
            ps4["bombNotes"] = [{"b": b["_time"]} for b in pc_data["_bombs"]]
        else:
            ps4["bombNotes"] = []
        ps4["bombNotesData"] = []

        # Obstacles
        if "_obstacles" in pc_data:
            ps4["obstacles"] = [{"b": o["_time"]} for o in pc_data["_obstacles"]]
            ps4["obstaclesData"] = []
        else:
            ps4["obstacles"] = []
            ps4["obstaclesData"] = []

        ps4["chains"] = []
        ps4["arcs"] = []
        ps4["spawnRotations"] = []
        ps4["spawnRotationsData"] = []

        # Write gzipped JSON
        output_path = str(output_name).replace('.dat', '.beatmap.gz')
        with gzip.open(output_path, 'wt', encoding='utf-8') as f:
            json.dump(ps4, f)
        return output_path
    except Exception as e:
        print(f"  Error converting: {e}")
        return None

def main():
    SONGS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DLC_DIR.mkdir(parents=True, exist_ok=True)
    (DLC_DIR / "sce_sys").mkdir(exist_ok=True)
    (DLC_DIR / "StreamingAssets").mkdir(exist_ok=True)
    (DLC_DIR / "StreamingAssets/BeatmapLevelsData").mkdir(exist_ok=True)

    print("=" * 60)
    print("BEAT SABER PS4 - BUILD CUSTOM SONGS PKG")
    print("=" * 60)
    print(f"Content ID: {CONTENT_ID}")

    # Find songs with beatmap files
    songs = [d for d in SONGS_DIR.iterdir() if d.is_dir()]
    print(f"Found {len(songs)} song folders")

    if not songs:
        print("No songs found!")
        return

    # Process songs
    total_beatmps = 0
    for song_dir in songs:
        print(f"\nProcessing: {song_dir.name}")

        # Read info
        info_path = None
        for fn in ["info.dat", "Info.dat"]:
            if (song_dir / fn).exists():
                info_path = song_dir / fn
                break

        if info_path:
            try:
                with open(info_path) as f:
                    info = json.load(f)
                print(f"  Song: {info.get('_songName', 'Unknown')}")
            except:
                print(f"  Song: (parsing failed)")

        # Find and convert beatmaps
        beatmaps = list(song_dir.glob("*.dat")) + list(song_dir.glob("*.json"))
        print(f"  Found {len(beatmaps)} beatmap files")

        for bm in beatmaps:
            converted = convert_beatmap(bm, DLC_DIR / "StreamingAssets/BeatmapLevelsData" / f"{song_dir.name}_{bm.name}")
            if converted:
                total_beatmps += 1

        # Copy cover if exists
        for cover_name in ["cover.jpg", "cover.png"]:
            cover = song_dir / cover_name
            if cover.exists():
                shutil.copy(cover, DLC_DIR / "StreamingAssets/BeatmapLevelsData" / f"{song_dir.name}_cover.jpg")
                break

    print(f"\nTotal beatmaps converted: {total_beatmps}")

    # Create PARAM.SFO
    paramsfo_path = DLC_DIR / "sce_sys" / "param.sfo"
    paramsfo = create_paramsfo(CONTENT_ID, "Beat Saber Custom Songs")
    with open(paramsfo_path, 'wb') as f:
        f.write(paramsfo)
    print(f"Created: {paramsfo_path}")

    # Build PKG
    print("\n=== Building PKG ===")
    builder = PS4PKGBuilder(CONTENT_ID)

    # Add all files from DLC directory
    for file_path in DLC_DIR.rglob("*"):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(DLC_DIR))
            with open(file_path, 'rb') as f:
                builder.add_file(rel_path, f.read())

    pkg_path = OUTPUT_DIR / f"{CONTENT_ID}.pkg"
    builder.save(str(pkg_path))

    # Create unlocker
    unlocker_path = OUTPUT_DIR / f"{CONTENT_ID}-unlock.pkg"
    unlocker = PS4PKGBuilder(CONTENT_ID)
    unlocker.add_file("sce_sys/param.sfo", paramsfo)
    unlocker.save(str(unlocker_path))

    print("\n" + "=" * 60)
    print("BUILD COMPLETE!")
    print("=" * 60)
    print(f"""
Files created:
  - DLC PKG: {pkg_path}
  - Unlocker: {unlocker_path}

Installation:
  1. Copy both PKG files to USB drive root
  2. On PS4: GoldHEN > Install Package
  3. Install unlocker FIRST, then DLC
  4. Launch Beat Saber
  5. Look for songs in: Extras menu or song selection
""")

if __name__ == "__main__":
    main()