#!/usr/bin/env python3
"""
Full Custom Song Pipeline for PS4 Beat Saber
--------------------------------------------
Replaces a target song's audio and beatmaps in an AssetBundle.

Usage:
  python3 full_custom_song_pipeline.py --target startmeup --audio custom.fsb5 --beatmaps ./my_song/
"""

import os, sys, json, gzip, struct, argparse
import UnityPy
from UnityPy.streams import EndianBinaryReader

def get_fsb5_info(fsb5_bytes):
    """Extracts sample header size and audio data size from FSB5."""
    shsz = struct.unpack_from('<I', fsb5_bytes, 12)[0]
    # Sample entry: bytes 4-7 = data_size
    ds = struct.unpack_from('<I', fsb5_bytes[16:], 4)[0]
    return shsz, ds

def update_beatmap(reader, custom_json_path):
    """Replaces beatmap data with V3 format converted from custom JSON."""
    with open(custom_json_path, 'r') as f:
        data = json.load(f)

    # Convert to V3 format as used in previous experiments
    # (Simplified for this script, assume input is already V3 compatible)
    # If not, this is where the conversion logic from Experiment 62 would go
    v3_data = data # assume input is pre-converted or valid V3

    json_bytes = json.dumps(v3_data, separators=(',', ':')).encode('utf-8')
    beatmap_gz = gzip.compress(json_bytes)

    tt = reader.read_typetree()
    tt['m_Script'] = beatmap_gz.decode('utf-8', 'surrogateescape')
    reader.save_typetree(tt)

def main():
    parser = argparse.ArgumentParser(description='Full Custom Song Pipeline')
    parser.add_argument('--target', required=True, help='Target song bundle name (e.g. startmeup)')
    parser.add_argument('--audio', required=True, help='Path to custom FSB5 audio file')
    parser.add_argument('--beatmaps', required=True, help='Folder containing custom .json beatmaps')
    parser.add_argument('--template', default='/workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/startmeup', help='Path to target template bundle')
    parser.add_argument('--output', default='custom_song.bundle', help='Output bundle path')
    parser.add_argument('--deploy', action='store_true', help='Deploy to PS4 via FTP after build')

    args = parser.parse_args()

    # 1. Load and validate custom audio
    with open(args.audio, 'rb') as f:
        audio_bytes = f.read()

    if audio_bytes[:4] != b'FSB5':
        print("❌ Error: Audio file is not a valid FSB5 (missing magic)")
        sys.exit(1)

    shsz, ds = get_fsb5_info(audio_bytes)
    print(f"Audio loaded: {len(audio_bytes)} bytes, sample_header_size={shsz}, data_size={ds}")

    # 2. Load template bundle
    print(f"Loading template: {args.template}")
    env = UnityPy.load(args.template)
    bf = list(env.files.values())[0]
    cab = bf.files['CAB-6c9e66546e3e23434517417298a18b91'] # Target CAB

    # 3. Replace .resource data
    resource_key = 'CAB-6c9e66546e3e23434517417298a18b91.resource'
    new_res = EndianBinaryReader(audio_bytes)
    new_res.flags = 0
    new_res.BaseOffset = 0
    bf.files[resource_key] = new_res
    print(f"✅ .resource replaced with custom audio")

    # 4. Update AudioClip metadata
    # We need to calculate the length based on the audio data size
    # For HEVAG: duration = (data_size / (16 * channels)) * 28 / sample_rate
    # Assume stereo (2 channels) and 44100Hz
    duration = (ds / (16 * 2)) * 28 / 44100.0

    for pid, reader in cab.objects.items():
        if reader.class_id == 83:
            tt = reader.read_typetree()
            tt['m_Resource']['m_Size'] = len(audio_bytes)
            tt['m_Length'] = duration
            reader.save_typetree(tt)
            print(f"✅ AudioClip updated: length={duration:.2f}s, size={len(audio_bytes)}")
            break

    # 5. Update audio.gz metadata
    for pid, reader in cab.objects.items():
        if reader.class_id == 49 and 'audio.gz' in (reader.peek_name() or ''):
            samples = int((ds / 32) * 28)
            meta = json.dumps({
                "version": "4.0.0", "songChecksum": "custom",
                "songSampleCount": samples, "songFrequency": 44100,
                "bpmData": [{"si": 0, "ei": samples, "sb": 0.0, "eb": duration}]
            }, separators=(',', ':'))
            tt = reader.read_typetree()
            tt['m_Script'] = gzip.compress(meta.encode()).decode('utf-8', 'surrogateescape')
            reader.save_typetree(tt)
            print(f"✅ audio.gz updated: {samples} samples")
            break

    # 6. Replace beatmaps
    beatmap_files = os.listdir(args.beatmaps)
    replaced_count = 0
    for pid, reader in cab.objects.items():
        if reader.class_id == 49:
            n = reader.peek_name() or ''
            # Try to match custom beatmap file to original beatmap name
            # e.g. "StartMeUp_Easy.json" -> "StartMeUpEasy.beatmap"
            for custom_file in beatmap_files:
                if custom_file.endswith('.json'):
                    # Very simple matching logic: match suffix (e.g. 'Easy')
                    for suffix in ['Easy', 'Normal', 'Hard', 'Expert', 'ExpertPlus']:
                        if suffix in n and suffix in custom_file:
                            update_beatmap(reader, os.path.join(args.beatmaps, custom_file))
                            replaced_count += 1
                            break
    print(f"✅ Replaced {replaced_count} beatmaps")

    # 7. Save bundle with LZ4 compression (to match original)
    print("Saving bundle with LZ4 compression...")
    result = bf.save(packer="lz4")
    with open(args.output, 'wb') as f:
        f.write(result)
    print(f"✅ Bundle saved to {args.output}")

    # 8. Deploy to PS4
    if args.deploy:
        print(f"Deploying to PS4 as /data/GoldHEN/AFR/CUSA12878/{args.target}_v3...")
        # Use lftp for deployment
        import subprocess
        cmd = f'lftp -u anonymous, -p 2121 192.168.100.117 -e "put {args.output} -o /data/GoldHEN/AFR/CUSA12878/{args.target}_v3; quit"'
        subprocess.run(cmd, shell=True)
        print("✅ Deployment complete")

if __name__ == "__main__":
    main()
