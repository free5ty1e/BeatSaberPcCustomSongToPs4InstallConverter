#!/usr/bin/env python3
"""
Beat Saber PS4 AssetBundle Converter v3
=======================================
Converts a BeatSaver custom song into a PS4-compatible AssetBundle.
Replaces beatmap data and renames assets. Audio stays as template audio
(needs FSB5 tools to replace).

Usage:
    python3 convert_song_v3.py <song_directory> <level_id>
"""

import os, sys, json, struct, gzip
from pathlib import Path

import UnityPy

DUMP_DIR = Path("/workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData")
TEMPLATE = "100bills"
OUTPUT_DIR = Path(__file__).parent / "custom_songs"

# Difficulty rank mapping (Beat Saber standard)
DIFFICULTY_RANKS = {0: "Easy", 1: "Normal", 2: "Hard", 3: "Expert", 4: "ExpertPlus"}

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    song_path = sys.argv[1]
    level_id = sys.argv[2] if len(sys.argv) > 2 else "custom001"

    print(f"Converting: {song_path}")
    print(f"Level ID: {level_id}")

    # ── Load custom song ────
    song_dir = Path(song_path)
    info_file = song_dir / "info.dat"
    if not info_file.exists():
        info_file = song_dir / "Info.dat"
    info = json.loads(info_file.read_bytes())

    song_name = info.get('_songName', '?')
    author = info.get('_songAuthorName', '?')
    print(f"  Song: {song_name} by {author}")

    # Load difficulties keyed by difficulty name (e.g., "Easy", "Normal")
    custom_diffs = {}
    for dm_set in info.get('_difficultyBeatmapSets', []):
        char_name = dm_set.get('_beatmapCharacteristicName', 'Standard')
        for dm in dm_set.get('_difficultyBeatmaps', []):
            diff_name = dm.get('_difficulty', 'Expert')
            diff_file = song_dir / dm.get('_beatmapFilename', f"{diff_name}{char_name}.dat")
            if diff_file.exists():
                custom_diffs[diff_name] = diff_file.read_bytes()
    print(f"  Difficulties: {sorted(custom_diffs.keys())}")

    # ── Load template ────
    template_path = DUMP_DIR / TEMPLATE
    print(f"  Template: {template_path}")
    env = UnityPy.load(str(template_path))
    bf = list(env.files.values())[0]
    cab = next(v for v in bf.files.values() if hasattr(v, 'objects'))

    # ── Modify objects ────
    changes = 0
    template_diffs_map = {}  # maps template diff name to path_id

    for path_id, reader in cab.objects.items():
        tt = reader.read_typetree()
        m_name = tt.get('m_Name', '')
        if not m_name:
            continue

        new_name = m_name

        # Rename: replace "100Bills" / "100bills" / "$100Bills" with level_id equivalent
        if m_name.startswith("100Bills"):
            new_name = m_name.replace("100Bills", level_id.capitalize(), 1)
        elif m_name.startswith("100bills"):
            new_name = m_name.replace("100bills", level_id, 1)
        elif m_name == "$100Bills" and reader.class_id == 83:
            new_name = f"${level_id}"

        if new_name != m_name:
            tt['m_Name'] = new_name
            reader.save_typetree(tt)
            changes += 1

        # Process beatmap data
        if reader.class_id == 49 and ('.beatmap' in m_name):
            raw = reader.get_raw_data()
            if len(raw) > 8:
                fn_len = struct.unpack_from('<I', raw, 0)[0]
                fn_end = 4 + fn_len + 1
                if fn_end + 4 <= len(raw):
                    decomp_size = struct.unpack_from('<I', raw, fn_end)[0]
                    gz_data = raw[fn_end + 4:]

                    if gz_data[:2] == b'\x1f\x8b':
                        # Extract difficulty name from the original file path
                        # Format: "100BillsEasy.beatmap.gz" -> "Easy"
                        orig_fn = raw[4:4 + fn_len].decode('ascii', errors='replace')
                        # Extract difficulty name: after "100Bills", before ".beatmap"
                        diff_key = orig_fn
                        for pfx in ['100Bills', '100bills']:
                            if diff_key.startswith(pfx):
                                diff_key = diff_key[len(pfx):]
                        diff_key = diff_key.split('.')[0]  # remove extension

                        # Map difficulty rank to name (from _difficulty field in BeatmapLevelData)
                        # The template uses numeric difficulty ranks (0-4)
                        # Custom songs use difficulty names ("Easy", "Normal", etc.)
                        template_diffs_map[diff_key] = path_id

    # ── Replace beatmaps for matching difficulties ────
    # The template has number-based difficulty references (0-4)
    # Custom songs have name-based difficulties
    # We need to match by difficulty name
    replaced = 0
    for path_id, reader in cab.objects.items():
        tt = reader.read_typetree()
        m_name = tt.get('m_Name', '')

        if reader.class_id == 49 and '.beatmap' in m_name:
            raw = reader.get_raw_data()
            if len(raw) > 8:
                fn_len = struct.unpack_from('<I', raw, 0)[0]
                fn_end = 4 + fn_len + 1

                orig_fn = raw[4:4 + fn_len].decode('ascii', errors='replace')
                diff_key = orig_fn
                for pfx in ['100Bills', '100bills']:
                    if diff_key.startswith(pfx):
                        diff_key = diff_key[len(pfx):]
                diff_key = diff_key.split('.')[0]

                # Map numeric difficulty rank to name
                if diff_key.isdigit():
                    diff_name = DIFFICULTY_RANKS.get(int(diff_key), diff_key)
                else:
                    diff_name = diff_key

                # Check if custom song has this difficulty
                if diff_name in custom_diffs:
                    custom_data = custom_diffs[diff_name]
                    compressed = gzip.compress(custom_data)

                    # Update filename part
                    new_fn = new_name = m_name
                    new_fn_bytes = new_fn.encode('ascii')

                    # Build new raw data
                    new_raw = bytearray()
                    new_raw += struct.pack('<I', len(new_fn_bytes))
                    new_raw += new_fn_bytes
                    new_raw += b'\x00'
                    new_raw += struct.pack('<I', len(custom_data))
                    new_raw += compressed

                    reader.set_raw_data(bytes(new_raw))
                    replaced += 1
                    print(f"  ✅ Replaced: {diff_name} ({orig_fn})")

    changes += replaced
    cab.mark_changed()

    # ── Save ────
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_DIR / f"{level_id}.bundle"
    result = bf.save()
    if isinstance(result, bytes):
        output.write_bytes(result)
        print(f"\n  Saved: {output} ({len(result):,} bytes)")
    else:
        print(f"\n  Save returned: {result}")

    print(f"\n=== Converted: {song_name} -> {level_id} ({changes} changes, {replaced} beatmaps) ===")

if __name__ == '__main__':
    main()
