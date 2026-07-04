#!/usr/bin/env python3
"""
Full Custom Song Pipeline for PS4 Beat Saber
=============================================
Takes a community custom song (WAV + beatmap .dat files) and produces a
drop-in AssetBundle replacement for a target song (e.g., startmeup).

Usage:
    python3 full_custom_song_pipeline.py \\
        --song-dir ./my_custom_song \\
        --target startmeup \\
        [--deploy]

Example:
    python3 full_custom_song_pipeline.py \\
        --song-dir /workspace/beat-saber-ps4-custom-songs/songs_repo/249ed7fe4b66b339af8322d6e054567bcf7c1b07 \\
        --target startmeup \\
        --deploy

Pipeline Steps:
    1. Load the target song's original AssetBundle (template)
    2. Convert custom WAV audio to HEVAG -> FSB5 (with 12MB padding)
    3. Replace .resource data in the bundle with new FSB5
    4. Update AudioClip metadata (m_Length, m_Resource.m_Size)
    5. Update audio.gz metadata (songSampleCount, bpmData)
    6. Replace all 5 difficulty beatmaps (.dat -> gzip -> TextAsset)
    7. Save the modified bundle with LZ4 compression
    8. Deploy to PS4 via FTP (optional)
"""

import os
import sys
import json
import gzip
import struct
import argparse
import wave
import logging

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, TOOLS_DIR)

# ---------------------------------------------------------------------------
# Imports from our toolchain
# ---------------------------------------------------------------------------
import UnityPy
from UnityPy.streams import EndianBinaryReader
import soundfile as sf

try:
    from hevag_encoder import pcm_to_hevag, fast_pcm_to_hevag, build_fsb5
except ImportError:
    # Fallback: try to import directly
    sys.path.insert(0, os.path.join(PROJECT_ROOT, 'tools'))
    from hevag_encoder import pcm_to_hevag, fast_pcm_to_hevag, build_fsb5

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ORIGINAL_RESOURCE_SIZE = 12305632   # size of original startmeup .resource (12MB)
ORIGINAL_CAB_NAME = "CAB-6c9e66546e3e23434517417298a18b91"
SAMPLE_RATE = 44100
CHANNELS = 2

# Beatmap difficulty names expected in the template
DIFFICULTIES = ['Easy', 'Normal', 'Hard', 'Expert', 'ExpertPlus']

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger('pipeline')


# ============================================================================
# Step 0: Audio -> PCM -> HEVAG -> FSB5 (with padding)
# Supports .wav AND .ogg via soundfile
# ============================================================================

def audio_to_fsb5(audio_path: str, pad_to_size: int = ORIGINAL_RESOURCE_SIZE) -> bytes:
    """
    Convert an audio file (.wav or .ogg) to a PS4-compatible FSB5 file.

    1. Read audio via soundfile (handles WAV, OGG, FLAC, etc.)
    2. Encode PCM to HEVAG frames
    3. Build FSB5 container
    4. Pad to match original .resource size (required by PS4 decoder)

    Returns:
        Complete FSB5 bytes (padded to pad_to_size if smaller)
    """
    log.info(f"Reading audio: {audio_path}")

    # soundfile returns numpy array, convert to list of ints
    data, framerate = sf.read(audio_path, dtype='int16')
    if data.ndim == 1:
        # Mono -> convert to interleaved for encoder
        pcm_data = data.tobytes()
        nchannels = 1
    else:
        nchannels = data.shape[1]
        pcm_data = data.tobytes()

    duration = len(data) / framerate

    log.info(f"  Frames: {len(data)}, Rate: {framerate}Hz, "
             f"Channels: {nchannels}, Duration: {duration:.1f}s")

    # Encode to HEVAG (using fast encoder for speed)
    log.info("Encoding PCM -> HEVAG (fast mode)...")
    hevag_data = fast_pcm_to_hevag(pcm_data, channels=nchannels)
    log.info(f"  HEVAG frames: {len(hevag_data)} bytes")

    # Build FSB5
    log.info("Building FSB5 container...")
    fsb5_bytes = build_fsb5(hevag_data, framerate, nchannels)
    log.info(f"  FSB5 size: {len(fsb5_bytes)} bytes")

    # Pad to match original resource size (CRITICAL for PS4)
    if len(fsb5_bytes) < pad_to_size:
        padding = bytes(pad_to_size - len(fsb5_bytes))
        fsb5_bytes = fsb5_bytes + padding
        log.info(f"  Padded to {len(fsb5_bytes)} bytes (+{len(padding)} bytes)")

    return fsb5_bytes


# ============================================================================
# Step 1: Load template bundle
# ============================================================================

def load_target_bundle(template_path: str):
    """
    Load the target song's AssetBundle and return the BundleFile + CAB.
    """
    log.info(f"Loading target bundle: {template_path}")
    env = UnityPy.load(template_path)
    bundles = list(env.files.values())
    if not bundles:
        raise RuntimeError(f"No bundles found in {template_path}")

    bf = bundles[0]
    cab = bf.files[ORIGINAL_CAB_NAME]

    # Confirm the .resource file exists
    resource_key = f"{ORIGINAL_CAB_NAME}.resource"
    if resource_key not in bf.files:
        raise RuntimeError(f"Resource file '{resource_key}' not found in bundle")

    log.info(f"  Bundle loaded: CAB={len(cab.objects)} objects, "
             f"Resource={bf.files[resource_key].Length} bytes")

    return bf, cab


# ============================================================================
# Step 2: Replace .resource data
# ============================================================================

def replace_resource(bf, fsb5_bytes: bytes):
    """Replace the .resource file in the bundle with new FSB5 data."""
    resource_key = f"{ORIGINAL_CAB_NAME}.resource"
    new_res = EndianBinaryReader(fsb5_bytes)
    new_res.flags = 0
    new_res.BaseOffset = 0
    bf.files[resource_key] = new_res
    log.info(f"  .resource replaced ({len(fsb5_bytes)} bytes)")


# ============================================================================
# Step 3: Update AudioClip
# ============================================================================

def update_audioclip(cab, fsb5_bytes: bytes, duration: float, sample_rate: int = SAMPLE_RATE):
    """
    Update the AudioClip's metadata (m_Length, m_Frequency, m_Resource.m_Size).
    """

    for pid, reader in cab.objects.items():
        if reader.class_id == 83:
            tt = reader.read_typetree()
            tt['m_Resource']['m_Size'] = len(fsb5_bytes)
            tt['m_Length'] = duration
            tt['m_Frequency'] = sample_rate
            reader.save_typetree(tt)
            log.info(f"  AudioClip updated: length={duration:.1f}s, "
                     f"frequency={sample_rate}Hz, resource_size={len(fsb5_bytes)}")
            return

    raise RuntimeError("No AudioClip (class_id=83) found in bundle!")


# ============================================================================
# Step 4: Update audio.gz metadata
# ============================================================================

def update_audio_gz(cab, duration: float, sample_rate: int = SAMPLE_RATE):
    """
    Update the audio.gz TextAsset to reflect new audio duration/sample count.
    """
    sample_count = int(duration * sample_rate)

    meta = {
        "version": "4.0.0",
        "songChecksum": "custom",
        "songSampleCount": sample_count,
        "songFrequency": sample_rate,
        "bpmData": [
            {"si": 0, "ei": sample_count, "sb": 0.0, "eb": duration}
        ]
    }

    meta_json = json.dumps(meta, separators=(',', ':'))
    compressed = gzip.compress(meta_json.encode('utf-8'))

    for pid, reader in cab.objects.items():
        n = reader.peek_name() or ''
        if reader.class_id == 49 and 'audio.gz' in n:
            tt = reader.read_typetree()
            tt['m_Script'] = compressed.decode('utf-8', 'surrogateescape')
            reader.save_typetree(tt)
            log.info(f"  audio.gz updated: {sample_count} samples, "
                     f"{duration:.1f}s")
            return

    raise RuntimeError("No audio.gz TextAsset found in bundle!")


# ============================================================================
# Step 5: Replace beatmaps
# ============================================================================

def replace_beatmaps(cab, beatmap_dir: str):
    """
    Replace all 5 difficulty beatmaps with custom ones.

    Matches difficulty by name (Easy, Normal, Hard, Expert, ExpertPlus).
    Custom .dat or .json files are loaded, re-encoded as gzipped V3 JSON,
    and written to the corresponding TextAsset in the CAB.
    """
    beatmap_files = [f for f in os.listdir(beatmap_dir)
                     if f.endswith(('.json', '.dat'))]

    if not beatmap_files:
        log.warning("  No .json or .dat beatmap files found!")
        return 0

    replaced = 0
    for pid, reader in cab.objects.items():
        if reader.class_id == 49:
            name = reader.peek_name() or ''
            # Only target .beatmap.gz files (NOT lightshow, NOT info, NOT audio.gz)
            if '.beatmap.gz' not in name and 'Beatmap' not in name:
                continue

            # Try to match this TextAsset to a custom beatmap by difficulty
            matched_file = None
            for diff in DIFFICULTIES:
                # Exact match: the TextAsset name contains the difficulty as a word
                # e.g., "StartMeUpEasy.beatmap.gz" matches "Easy"
                if diff in name:
                    # Find matching custom file by difficulty
                    for f in beatmap_files:
                        if diff in f and 'Info' not in f and 'Lightshow' not in f:
                            matched_file = f
                            break
                    if matched_file:
                        break

            if matched_file:
                path = os.path.join(beatmap_dir, matched_file)
                with open(path, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)

                # Encode as gzipped JSON
                json_bytes = json.dumps(data, separators=(',', ':')).encode('utf-8')
                compressed = gzip.compress(json_bytes)

                # Update the TextAsset
                tt = reader.read_typetree()
                tt['m_Script'] = compressed.decode('utf-8', 'surrogateescape')
                reader.save_typetree(tt)
                replaced += 1
                log.info(f"  Beatmap '{name}' <- '{matched_file}'")
            else:
                log.debug(f"  Skipping '{name}' (no matching beatmap file)")

    return replaced


# ============================================================================
# Step 6: Save bundle
# ============================================================================

def save_bundle(bf, output_path: str):
    """
    Save the modified bundle with LZ4 compression (matching original PS4 format).
    """
    log.info(f"Saving bundle with LZ4 compression...")
    result = bf.save(packer="lz4")
    with open(output_path, 'wb') as f:
        f.write(result)
    log.info(f"  Saved: {output_path} ({len(result)} bytes)")

    # Verify the saved bundle can be re-loaded
    try:
        UnityPy.load(output_path)
        log.info("  Verified: bundle loads correctly")
    except Exception as e:
        log.warning(f"  Verify failed (may still work): {e}")


# ============================================================================
# Step 7: Deploy to PS4
# ============================================================================

def deploy_to_ps4(bundle_path: str, target_name: str):
    """
    Upload the bundle to the PS4 via FTP.
    Target path: /data/GoldHEN/AFR/CUSA12878/{target_name}_v3
    """
    import subprocess as sp

    remote_path = f"/data/GoldHEN/AFR/CUSA12878/{target_name}_v3"
    cmd = [
        "lftp", "-u", "anonymous,", "-p", "2121",
        "192.168.100.117",
        "-e", f"put {bundle_path} -o {remote_path}; quit"
    ]

    log.info(f"Deploying to PS4: {remote_path}")
    result = sp.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode == 0:
        log.info("  ✅ Deployment successful")
    else:
        log.warning(f"  ⚠️ Deploy failed (PS4 offline?): {result.stderr}")


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Full Custom Song Pipeline for PS4 Beat Saber",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline: WAV + beatmaps -> bundle -> deploy
  python3 full_custom_song_pipeline.py --song-dir ./my_song --target startmeup --deploy

  # Just build the bundle (no deploy):
  python3 full_custom_song_pipeline.py --song-dir ./my_song --target startmeup

  # Use pre-encoded FSB5 (skip audio conversion):
  python3 full_custom_song_pipeline.py --audio custom.fsb5 --song-dir ./my_song --target startmeup
        """
    )
    parser.add_argument('--song-dir', required=True,
                        help='Folder containing the custom song (WAV + .dat/.json beatmaps)')
    parser.add_argument('--audio', default=None,
                        help='Pre-encoded FSB5 file (optional: skips WAV->FSB5 conversion)')
    parser.add_argument('--target', default='startmeup',
                        help='Target song name (default: startmeup)')
    parser.add_argument('--template',
                        default='/workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/startmeup',
                        help='Path to the target song template bundle')
    parser.add_argument('--output',
                        default='/workspace/beat_saber_deluxe/custom_songs/custom_song.bundle',
                        help='Output bundle path')
    parser.add_argument('--deploy', action='store_true',
                        help='Deploy to PS4 via FTP after building')
    parser.add_argument('--target-ip', default='192.168.100.117',
                        help='PS4 IP address for FTP deployment')
    parser.add_argument('--no-pad', action='store_true',
                        help='Skip padding FSB5 to 12MB (will likely freeze on PS4)')

    args = parser.parse_args()

    if not os.path.isdir(args.song_dir):
        log.error(f"Song directory not found: {args.song_dir}")
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Step 0: Audio conversion (WAV -> FSB5)
    # -----------------------------------------------------------------------
    actual_sample_rate = SAMPLE_RATE
    if args.audio:
        log.info(f"Using pre-encoded FSB5: {args.audio}")
        with open(args.audio, 'rb') as f:
            fsb5_bytes = f.read()
        if fsb5_bytes[:4] != b'FSB5':
            log.error("File does not start with FSB5 magic!")
            sys.exit(1)
        # Extract duration from FSB5 header
        shsz = struct.unpack_from('<I', fsb5_bytes, 12)[0]
        ds = struct.unpack_from('<I', fsb5_bytes[16:], 4)[0]
        # Try to get sample rate from FSB5 sample header
        freq = struct.unpack_from('<I', fsb5_bytes[16:], 16)[0]
        actual_sample_rate = freq if freq > 0 else SAMPLE_RATE
        duration = (ds / (16 * 2)) * 28 / float(actual_sample_rate)
    else:
        log.info("Searching for audio file in song directory (.wav, .ogg, ...)...")
        audio_files = [f for f in os.listdir(args.song_dir)
                      if f.endswith(('.wav', '.ogg', '.flac', '.mp3', '.aiff'))]
        if not audio_files:
            log.error(f"No audio files found in {args.song_dir}")
            sys.exit(1)

        audio_path = os.path.join(args.song_dir, audio_files[0])
        # Get sample rate via soundfile before full conversion
        info = sf.info(audio_path)
        actual_sample_rate = info.samplerate
        pad_to = 0 if args.no_pad else ORIGINAL_RESOURCE_SIZE
        fsb5_bytes = audio_to_fsb5(audio_path, pad_to_size=pad_to)
        # Get data_size from FSB5 header (before padding)
        ds = struct.unpack_from('<I', fsb5_bytes[16:], 4)[0]
        duration = (ds / (16 * 2)) * 28 / float(actual_sample_rate)

    # -----------------------------------------------------------------------
    # Step 1: Load template bundle
    # -----------------------------------------------------------------------
    if not os.path.isfile(args.template):
        log.error(f"Template bundle not found: {args.template}")
        sys.exit(1)

    bf, cab = load_target_bundle(args.template)
    log.info(f"Target: {args.target}")

    # -----------------------------------------------------------------------
    # Step 2: Replace .resource
    # -----------------------------------------------------------------------
    replace_resource(bf, fsb5_bytes)

    # -----------------------------------------------------------------------
    # Step 3: Update AudioClip
    # -----------------------------------------------------------------------
    update_audioclip(cab, fsb5_bytes, duration, actual_sample_rate)

    # -----------------------------------------------------------------------
    # Step 4: Update audio.gz
    # -----------------------------------------------------------------------
    update_audio_gz(cab, duration, actual_sample_rate)

    # -----------------------------------------------------------------------
    # Step 5: Replace beatmaps
    # -----------------------------------------------------------------------
    replaced = replace_beatmaps(cab, args.song_dir)
    log.info(f"Beatmaps replaced: {replaced}/5")

    # -----------------------------------------------------------------------
    # Step 6: Save bundle
    # -----------------------------------------------------------------------
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    save_bundle(bf, args.output)

    # -----------------------------------------------------------------------
    # Step 7: Deploy to PS4
    # -----------------------------------------------------------------------
    if args.deploy:
        deploy_to_ps4(args.output, args.target)

    log.info("Pipeline complete!")
    log.info(f"  Bundle: {args.output}")
    log.info(f"  Size: {os.path.getsize(args.output)} bytes")
    log.info(f"  Audio: {len(fsb5_bytes)} bytes, {duration:.1f}s")
    log.info(f"  Beatmaps: {replaced}/5 replaced")


if __name__ == "__main__":
    main()
