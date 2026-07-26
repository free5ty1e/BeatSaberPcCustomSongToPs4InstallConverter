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
DEFAULT_CONFIG_PATH = os.path.join(PROJECT_ROOT, 'ps4_config.json')
sys.path.insert(0, TOOLS_DIR)


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------
def load_config(config_path: str) -> dict:
    """
    Load PS4 configuration from a JSON file.
    Falls back to a sensible default if file is missing.
    """
    default_config = {
        "ps4": {"ip": "192.168.100.117", "ftp_port": 2121,
                "ftp_user": "anonymous", "ftp_password": ""},
        "title": {"id": "CUSA12878", "patch_suffix": "-patch"},
        "paths": {
            "afr_base": "/data/GoldHEN/AFR",
            "afr_target_suffix": "_v3",
            "game_dump_dir": "/workspace/ps4_dump/CUSA12878-patch",
            "template_dir": "Media/StreamingAssets/BeatmapLevelsData",
            "output_dir": "/workspace/beat_saber_deluxe/custom_songs"
        },
        "pipeline": {"default_target": "startmeup", "sample_rate": 44100}
    }
    if config_path and os.path.isfile(config_path):
        try:
            with open(config_path) as f:
                user_config = json.load(f)
            # Deep-merge user config over defaults
            def deep_merge(base, override):
                result = base.copy()
                for k, v in override.items():
                    if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                        result[k] = deep_merge(result[k], v)
                    else:
                        result[k] = v
                return result
            merged = deep_merge(default_config, user_config)
            log.info(f"Loaded config from {config_path}")
            return merged
        except Exception as e:
            log.warning(f"Failed to load config {config_path}: {e}")
            return default_config
    return default_config

# ---------------------------------------------------------------------------
# Imports from our toolchain
# ---------------------------------------------------------------------------
import UnityPy
from UnityPy.streams import EndianBinaryReader
import soundfile as sf

try:
    from hevag_encoder import (pcm_to_hevag, fast_pcm_to_hevag,
                                build_fsb5, build_vorbis_fsb5,
                                build_pcm16_fsb5)
except ImportError:
    # Fallback: try to import directly
    sys.path.insert(0, os.path.join(PROJECT_ROOT, 'tools'))
    from hevag_encoder import (pcm_to_hevag, fast_pcm_to_hevag,
                                build_fsb5, build_vorbis_fsb5,
                                build_pcm16_fsb5)

try:
    from lapped_audio import lap_audio_if_needed, detect_lapped, lap_audio
except ImportError:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, 'tools'))
    from lapped_audio import lap_audio_if_needed, detect_lapped, lap_audio

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ORIGINAL_RESOURCE_SIZE = 12305632   # size of original startmeup .resource (12MB)
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

    # soundfile returns numpy array, convert to list of ints (normalized)
    from hevag_encoder import read_audio_normalized
    data, framerate = read_audio_normalized(audio_path)
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
    fsb5_bytes = build_fsb5(hevag_data, framerate, nchannels,
                            pcm_frames=len(data))
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

    # Auto-detect CAB name from bundle files
    cab_key = None
    for key in bf.files:
        if key.startswith("CAB-") and not key.endswith(".resource"):
            cab_key = key
            break
    if cab_key is None:
        raise RuntimeError("No CAB file found in bundle")

    resource_key = f"{cab_key}.resource"
    if resource_key not in bf.files:
        raise RuntimeError(f"Resource file '{resource_key}' not found in bundle")

    cab = bf.files[cab_key]

    log.info(f"  Bundle loaded: CAB={cab_key} ({len(cab.objects)} objects), "
             f"Resource={resource_key} ({bf.files[resource_key].Length} bytes)")

    return bf, cab, cab_key, resource_key


# ============================================================================
# Step 2: Replace .resource data
# ============================================================================

def replace_resource(bf, fsb5_bytes: bytes, resource_key: str):
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

def _scan_beatmap_max_beat(song_dir: str) -> float:
    """Scan all beatmap .dat files and return the highest _time/b value found."""
    import glob as _glob
    max_beat = 0.0
    bm_files = _glob.glob(os.path.join(song_dir, "*.dat"))
    for bm_path in bm_files:
        fname = os.path.basename(bm_path).lower()
        if fname in ('info.dat', 'bpminfo.dat'):
            continue
        try:
            with open(bm_path) as f:
                data = json.load(f)
            notes = data.get('_notes', data.get('colorNotes', []))
            for note in notes:
                t = note.get('_time', note.get('b', 0))
                if isinstance(t, (int, float)) and t > max_beat:
                    max_beat = t
        except:
            pass
    return max_beat


def load_bpm_regions(song_dir: str, sample_count: int) -> list:
    """
    Load BPM region data from BPMInfo.dat (preferred) or compute from beatmap data.

    The bpmData maps sample ranges to beat ranges. This is CRITICAL for sync:
    the game converts beatmap 'b' values (in beats) to time positions using
    these regions. If eb is in seconds instead of beats, the tempo is halved
    at 120 BPM, causing progressive desync.

    IMPORTANT: Many BeatSaver mappers use a BPM slightly different from Info.dat's
    _beatsPerMinute when placing notes. We detect this by scanning the beatmap
    files for the highest _time/b value and using it to compute the effective BPM.

    Returns list of {"si": startSampleIndex, "ei": endSampleIndex,
                     "sb": startBeat, "eb": endBeat} dicts.
    """
    bpm_path = os.path.join(song_dir, "BPMInfo.dat")
    if os.path.exists(bpm_path):
        with open(bpm_path) as f:
            bpm_data = json.load(f)
        regions = bpm_data.get("_regions", [])
        if regions:
            # Still scan beatmaps to check if BPMInfo.dat's eb is too small
            max_beat = _scan_beatmap_max_beat(song_dir)
            if max_beat > regions[-1]["_endBeat"]:
                log.info(f"  Beatmap max beat ({max_beat:.1f}) > BPMInfo.dat eb ({regions[-1]['_endBeat']:.1f}) — using beatmap value")
                regions[-1]["_endBeat"] = max_beat
            return [
                {"si": r["_startSampleIndex"], "ei": r["_endSampleIndex"],
                 "sb": r["_startBeat"], "eb": r["_endBeat"]}
                for r in regions
            ]

    # Scan beatmap files to find the highest beat value (mapper's actual timing)
    max_beat = _scan_beatmap_max_beat(song_dir)

    # If we found beatmap data, use the max beat to compute the effective BPM
    duration = sample_count / SAMPLE_RATE
    if max_beat > 0:
        # total_beats = the beatmap's last beat value
        total_beats = max_beat
        eff_bpm = total_beats * 60.0 / duration
        log.info(f"  Beatmap-based BPM: {eff_bpm:.1f} (from last beat={total_beats:.1f}, audio={duration:.1f}s)")
    else:
        # Absolute fallback: use Info.dat BPM
        info_path = os.path.join(song_dir, "Info.dat")
        bpm = 120.0
        if os.path.exists(info_path):
            with open(info_path) as f:
                info = json.load(f)
            bpm = float(info.get("_beatsPerMinute", 120.0))
        total_beats = duration * bpm / 60.0
        log.info(f"  Info.dat BPM fallback: {bpm} (total_beats={total_beats:.1f})")

    return [{"si": 0, "ei": sample_count, "sb": 0.0, "eb": total_beats}]


def update_audio_gz(cab, duration: float, sample_rate: int = SAMPLE_RATE,
                    bpm_regions: list = None):
    """
    Update the audio.gz TextAsset to reflect new audio duration/sample count.
    """
    sample_count = int(duration * sample_rate)

    if bpm_regions is None:
        bpm_regions = [{"si": 0, "ei": sample_count, "sb": 0.0,
                         "eb": duration * 2.0}]  # fallback: assume 120 BPM

    meta = {
        "version": "4.0.0",
        "songChecksum": "custom",
        "songSampleCount": sample_count,
        "songFrequency": sample_rate,
        "bpmData": bpm_regions
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
# V2 → V3/V4 beatmap converter
# ============================================================================

def is_v2_beatmap(data: dict) -> bool:
    """Check if a beatmap dict is in V2 format (needs conversion)."""
    ver = data.get("version") or data.get("_version") or ""
    if ver.startswith("2"):
        return True
    if "_notes" in data and "colorNotes" not in data:
        return True
    return False


def convert_v2_to_v3(v2_data: dict, default_bpm: float = 120.0) -> dict:
    """
    Convert a V2 beatmap dict to V3.2.0 format.

    V2 beatmaps store notes as _notes[] with _time/_lineIndex/_lineLayer/
    _type/_cutDirection.  V3 uses colorNotes[] plus bombNotes[] with
    b/x/y/a/d fields.  Obstacles, events, and sliders are converted
    similarly, and the result is a minimal V3 structure the PS4 game
    can parse without crashing on unknown keys.

    default_bpm: BPM to use for bpmEvents (from Info.dat, not beatmap file).
    """
    # Pass through if already V3/V4
    if not is_v2_beatmap(v2_data):
        return v2_data

    # -- notes -----------------------------------------------------------------
    color_notes = []
    bomb_notes = []
    for note in v2_data.get("_notes", []):
        nt = int(note.get("_type", 0))
        base = {
            "b": float(note["_time"]),
            "x": int(note.get("_lineIndex", 0)),
            "y": int(note.get("_lineLayer", 0)),
        }
        if nt == 3:
            base["d"] = int(note.get("_cutDirection", 0))
            bomb_notes.append(base)
        else:
            base["a"] = nt
            base["c"] = nt  # PS4 game uses 'c' for color (V3.3.0+), not 'a'
            base["d"] = int(note.get("_cutDirection", 0))
            color_notes.append(base)

    # -- obstacles -------------------------------------------------------------
    obstacles = []
    for obs in v2_data.get("_obstacles", []):
        ot = int(obs.get("_type", 0))
        obstacles.append({
            "b": float(obs["_time"]),
            "x": int(obs.get("_lineIndex", 0)),
            "y": 0,
            "d": float(obs.get("_duration", 0)),
            "w": int(obs.get("_width", 1)),
            "h": 3 if ot == 0 else 1,
        })

    # -- events (V2 $!$ basicBeatmapEvents) --------------------------------------
    basic_events = []
    for ev in v2_data.get("_events", []):
        basic_events.append({
            "b": float(ev["_time"]),
            "t": int(ev.get("_type", 0)),
            "i": int(ev.get("_value", 0)),
        })

    event_types = sorted(set(e["t"] for e in basic_events))

    # -- build V3 structure ----------------------------------------------------
    v3 = {
        "version": "3.2.0",
        "colorNotes": color_notes,
        "bombNotes": bomb_notes,
        "obstacles": obstacles,
        "sliders": [],
        "burstSliders": [],
        "basicBeatmapEvents": basic_events,
        "colorBoostBeatmapEvents": [],
        "bpmEvents": [{"b": 0, "m": default_bpm}],
        "rotationEvents": [],
        "basicEventTypesWithKeywords": {
            "d": [{"e": t, "n": f"EventType{t}"} for t in event_types]
        },
        "useNormalEventsAsCompatibleEvents": True,
        "customData": {},
    }
    return v3


# ============================================================================
# Step 5: Replace beatmaps
# ============================================================================

def _select_beatmap_file(diff: str, beatmap_files: list, ignore_non_standard: bool = False) -> str | None:
    """
    Select the best beatmap file for a given difficulty using a priority fallback chain.

    Priority order (highest to lowest):
      1. Standard mode:  <Diff>Standard.dat    (e.g. ExpertPlusStandard.dat)
      2. Bare difficulty: <Diff>.dat            (e.g. ExpertPlus.dat)
      3. Beatmap-dot:    <Diff>.beatmap.dat     (e.g. ExpertPlus.beatmap.dat)
      4. Other modes:    <Diff>90Degree.dat, <Diff>OneSaber.dat, <Diff>NoArrows.dat, etc.
                         (limited gameplay but functional on PS4)
      5. 360Degree:      <Diff>360Degree.dat    (absolute last resort — notes behind
                         the player are unplayable in PS4 VR, but better than nothing)

    The ignore_non_standard flag suppresses tiers 4 and 5 (alternate modes).
    Bare files (tier 2) are always included — they have no mode suffix.
    """
    # Tiers: 1=Standard, 2=bare, 3=.beatmap.dat, 4=other modes, 5=360Degree
    tier1, tier2, tier3, tier4, tier5 = [], [], [], [], []

    for f in beatmap_files:
        base = f
        if 'Info' in base or 'Lightshow' in base or 'AudioData' in base:
            continue
        if not base.endswith(('.dat', '.json')):
            continue
        # Must contain the difficulty name
        if diff not in base:
            continue
        # ExpertPlus guard: when matching "Expert" never pick an "ExpertPlus" file
        if diff == 'Expert' and 'ExpertPlus' in base:
            continue

        stem = base  # e.g. "ExpertPlusStandard.dat" or "ExpertPlus.dat"

        if f'{diff}Standard' in stem:
            tier1.append(f)
        elif stem == f'{diff}.dat' or stem == f'{diff}.json':
            tier2.append(f)
        elif f'{diff}.beatmap' in stem:
            tier3.append(f)
        elif '360Degree' in stem:
            # Absolute last resort — only if ignore_non_standard not set
            if not ignore_non_standard:
                tier5.append(f)
        else:
            # 90Degree, OneSaber, NoArrows, Legacy, etc.
            if not ignore_non_standard:
                tier4.append(f)

    for tier in (tier1, tier2, tier3, tier4, tier5):
        if tier:
            return tier[0]
    return None


def replace_beatmaps(cab, beatmap_dir: str, ignore_non_standard=False, auto_convert=False):
    """
    Replace all 5 difficulty beatmaps with custom ones.

    Matches difficulty by name (Easy, Normal, Hard, Expert, ExpertPlus).
    Custom .dat or .json files are loaded, re-encoded as gzipped V3 JSON,
    and written to the corresponding TextAsset in the CAB.

    File selection uses a priority fallback chain (see _select_beatmap_file):
      1. <Diff>Standard.dat   (preferred)
      2. <Diff>.dat           (bare, no mode suffix)
      3. <Diff>.beatmap.dat   (BeatSaver .beatmap.dat format)
      4. <Diff>90Degree.dat / OneSaber.dat / etc. (if not --ignore-non-standard)
      (360Degree files are always excluded — unplayable on PS4 VR)

    Args:
        cab: Unity CAB bundle
        beatmap_dir: Directory containing .dat beatmap files
        ignore_non_standard: If True, skip tier-4 fallback (90Degree, OneSaber, etc.)
    """
    # Read BPM from Info.dat for V2→V3 conversion (used in bpmEvents)
    bpm = 120.0
    info_path = os.path.join(beatmap_dir, "Info.dat")
    if os.path.exists(info_path):
        with open(info_path) as f:
            info = json.load(f)
        bpm = float(info.get("_beatsPerMinute", 120.0))

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

            # Determine which difficulty this TextAsset slot is for
            matched_file = None
            for diff in DIFFICULTIES:
                # IMPORTANT: exclude "ExpertPlus" when matching "Expert" (substring trap)
                if diff == 'Expert' and 'ExpertPlus' in name:
                    continue
                if diff not in name:
                    continue
                # Got the slot — now pick the best source file
                matched_file = _select_beatmap_file(diff, beatmap_files, ignore_non_standard)
                break

            if matched_file:
                path = os.path.join(beatmap_dir, matched_file)
                with open(path, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)

                # Auto-convert V2 → V3.2.0 if requested
                if auto_convert and is_v2_beatmap(data):
                    data = convert_v2_to_v3(data, default_bpm=bpm)
                    log.info(f"  Converted V2 -> V3: '{matched_file}'")

                # Fix V3/V4 beatmaps with empty/missing bpmEvents (same BPM=60 fallback bug)
                if not data.get('bpmEvents'):
                    data['bpmEvents'] = [{"b": 0, "m": bpm}]
                    log.info(f"  Added bpmEvents ({bpm} BPM) to '{matched_file}'")

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

def deploy_to_ps4(bundle_path: str, target_name: str, config: dict):
    """
    Upload the bundle to the PS4 via FTP.
    Target path: {afr_base}/{title_id}/{target_name}{suffix}
    All paths read from config.
    """
    import subprocess as sp

    ps4_cfg = config.get('ps4', {})
    title_cfg = config.get('title', {})
    paths_cfg = config.get('paths', {})

    afr_base = paths_cfg.get('afr_base', '/data/GoldHEN/AFR')
    title_id = title_cfg.get('id', 'CUSA12878')
    suffix = paths_cfg.get('afr_target_suffix', '_v3')
    ftp_host = ps4_cfg.get('ip', '192.168.100.117')
    ftp_port = ps4_cfg.get('ftp_port', 2121)
    ftp_user = ps4_cfg.get('ftp_user', 'anonymous')
    ftp_pass = ps4_cfg.get('ftp_password', '')

    remote_path = f"{afr_base}/{title_id}/{target_name}{suffix}"

    user_part = f"{ftp_user},{ftp_pass}" if ftp_pass else f"{ftp_user},"
    cmd = [
        "lftp", "-u", user_part, "-p", str(ftp_port),
        ftp_host,
        "-e", f"put {bundle_path} -o {remote_path}; quit"
    ]

    log.info(f"Deploying bundle to PS4: {remote_path}")
    result = sp.run(cmd, capture_output=True, text=True, timeout=600)

    if result.returncode == 0:
        log.info("  ✅ Bundle deployment successful")
    else:
        log.warning(f"  ⚠️ Bundle deploy failed (PS4 offline?): {result.stderr}")


def add_mode_characteristics(cab, enable_modes: list) -> int:
    """
    Add additional beatmap characteristics (OneSaber, 90Degree, etc.)
    to the BeatmapLevel object so they appear in the in-game mode selector.

    Each new characteristic set reuses the SAME beatmap assets as Standard.
    This means the song will be playable in those modes (e.g. playing
    Standard notes while in OneSaber mode) without requiring separate
    mode-specific .beatmap.gz files.

    Args:
        cab: Unity CAB bundle containing BeatmapLevel
        enable_modes: List of characteristic names (e.g. ["OneSaber", "90Degree"])

    Returns:
        Number of modes added
    """
    if not enable_modes:
        return 0

    added = 0
    for pid, reader in cab.objects.items():
        # BeatmapLevel = class_id 114
        if reader.class_id != 114:
            continue

        tt = reader.read_typetree()
        existing_sets = tt.get('_difficultyBeatmapSets', [])

        # Build a set of already-present characteristic names
        existing_chars = set()
        for s in existing_sets:
            ch = s.get('_beatmapCharacteristicSerializedName', '')
            existing_chars.add(ch)

        if 'Standard' not in existing_chars:
            log.warning("  No Standard characteristic found - cannot clone modes")
            return 0

        # Find the Standard set to clone
        standard_set = None
        for s in existing_sets:
            if s.get('_beatmapCharacteristicSerializedName') == 'Standard':
                standard_set = s
                break

        if not standard_set:
            log.warning("  Standard characteristic not found - cannot clone modes")
            return 0

        # Add each requested mode
        for mode in enable_modes:
            if mode in existing_chars:
                log.info(f"  Mode '{mode}' already exists - skipping")
                continue

            new_set = {
                '_beatmapCharacteristicSerializedName': mode,
                '_difficultyBeatmaps': []
            }
            for entry in standard_set.get('_difficultyBeatmaps', []):
                new_set['_difficultyBeatmaps'].append({
                    '_difficulty': entry['_difficulty'],
                    '_beatmapAsset': entry['_beatmapAsset'],
                    '_lightshowAsset': entry['_lightshowAsset'],
                })
            existing_sets.append(new_set)
            existing_chars.add(mode)
            added += 1
            log.info(f"  Added mode: {mode}")

        tt['_difficultyBeatmapSets'] = existing_sets
        reader.save_typetree(tt)
        break  # Only one BeatmapLevel per bundle

    log.info(f"  Modes added: {added}")
    return added


# ============================================================================
# Inject BeatmapLevelSO metadata into the per-song CAB bundle
# ============================================================================

# Characteristic path IDs for _previewDifficultyBeatmapSets
_CHAR_PATH_IDS = {
    "Standard":  -7286399427822119286,
    "OneSaber":  -8583864861369561029,
    "NoArrows":   -5623662769225589684,
    "90Degree":    4533580413116749821,
    "360Degree":  1189643819550092755,
}


def _encode_unity_string(s: str) -> bytes:
    """Encode a string for Unity serialized data (UTF-16LE + length prefix)."""
    if not s:
        return b'\x00\x00'  # null string
    utf16 = s.encode('utf-16-le')
    # Unity string format: int32 length of UTF-16 bytes (including trailing null)
    plen = len(utf16) + 2  # +2 for trailing null
    return struct.pack('<i', plen) + utf16 + b'\x00\x00'


def _build_beatmap_level_so_blob(
    song_name: str,
    song_sub_name: str,
    song_author: str,
    level_author: str,
    bpm: float,
    preview_diff_count: int,
    diff_data: bytes,
    level_id: str = "custom",
) -> bytes:
    """
    Construct a BeatmapLevelSO serialized blob (IL2CPP MonoBehavior layout).

    Based on pack bundle analysis of the Rolling Stones pack:
      0x0C: m_Script PPtr(fileID=2, pathID=-1) — base class script ref
            The first 12 bytes are padding/zeroed (type info is in SerializedFile map)
      Then per-instance data fields in order:
        _levelID        = string (song identifier like "therollingstones_startmeup")
        _songName       = string (display name, e.g. "Espresso")
        _songSubName    = string (subtitle with length/notes info)
        _songAuthorName = string (artist name)
        _levelAuthorName= string (custom song author)
        BPM             = double (8 bytes)

      Then preview arrays:
        count = int32(5)
        For each mode [Standard, OneSaber, NoArrows, 90Degree, 360Degree]:
          PPtr(fileID=2, pathID=char_path_id)
          diff_count = int32(n)
          difficulty_data (36 bytes per entry × n)

    The blob does NOT include klassID/classID — those are in the SerializedFile's
    types map and resolved by IL2CPP at deserialization time.
    """
    blob = bytearray()

    # ── Padding + m_Script PPtr (per pack bundle analysis) ───────────────
    blob += b'\x00\x00\x00\x00'  # bytes 0-3: padding/type info placeholder
    blob += b'\x00\x00\x00\x00'  # bytes 4-7: classID placeholder
    blob += b'\x00\x00\x00\x00'  # bytes 8-11: alignment

    # m_Script at offset 0xC (byte 12)
    blob += struct.pack('<i', 2)           # fileID = 2 (m_Metadata->m_Script)
    blob += struct.pack('<q', -1)          # pathID = -1 (base class = ScriptableObject)

    # ── Instance fields (verified order from pack bundle analysis) ───────
    # NOTE: m_Name is NOT in the serialized instance data — it's in the type info.
    # Only _levelID through BPM are per-instance serialized fields.
    blob.extend(_encode_unity_string(level_id))            # _levelID
    blob.extend(_encode_unity_string(level_id))            # _levelID
    blob.extend(_encode_unity_string(song_name))           # _songName
    blob.extend(_encode_unity_string(song_sub_name))       # _songSubName
    blob.extend(_encode_unity_string(song_author))         # _songAuthorName
    blob.extend(_encode_unity_string(level_author))        # _levelAuthorName
    blob += struct.pack('<d', bpm)                         # BPM (double)

    # ── _previewDifficultyBeatmapSets array ────────────────────────────
    modes = ["Standard", "OneSaber", "NoArrows", "90Degree", "360Degree"]
    blob += struct.pack('<i', 5)                          # count = 5 modes

    for mode in modes:
        path_id = _CHAR_PATH_IDS[mode]
        blob += struct.pack('<i', 2)                      # fileID (m_Script ref)
        blob += struct.pack('<q', path_id)                # pathID
        blob += struct.pack('<i', preview_diff_count)     # difficulty count
        # Difficulty data: 36 bytes per entry
        needed = preview_diff_count * 36
        if len(diff_data) >= needed:
            blob.extend(diff_data[:needed])
        else:
            blob.extend(diff_data + b'\x00' * (needed - len(diff_data)))

    return bytes(blob)


def inject_beatmap_level_so(
    bf,
    song_name: str,
    song_artist: str = "",
    duration_seconds: float = 0.0,
    bpm: float = 120.0,
    note_count_standard: int = 0,
    note_count_diff_data: bytes = b'',
) -> bool:
    """
    Inject a BeatmapLevelSO ScriptableObject into the CAB bundle so the
    song menu can display custom metadata (name, artist, length, etc.).

    APPROACH: Since UnityPy lacks type info for BeatmapLevelSO and cannot
    serialize IL2CPP-compatible data for it, we work by first building a
    raw serialized blob, then attempting to insert it into the bundle's
    CAB file via post-save modification.

    The game resolves BeatmapLevelSO objects by _levelID across all loaded
    AssetBundles. When the per-song bundle is redirected and loaded, the
    injected SO provides metadata to the UI.

    Currently this function logs what *would* be injected (the blob) so it
    can be inspected. The actual CAB file injection requires UnityPy
    serialization support for BeatmapLevelSO and is tracked as a future
    task — see .agent/llm-wiki-knowledge-base/plans/song-list-metadata.md

    Args:
        bf: UnityPy BundleFile (the outer AssetBundle, not the CAB)
        song_name: Display song name (overrides original)
        song_artist: Artist name
        duration_seconds: Song length in seconds
        bpm: Beats per minute for timing
        note_count_standard: Note count for display purposes
        note_diff_data: Pre-encoded difficulty data (36B × N entries, or empty)

    Returns:
        True if the blob was constructed (injection itself needs UnityPy fix)
    """
    log.info("  Building BeatmapLevelSO metadata blob...")

    # ── Build the serialized blob ───────────────────────────────────────
    level_id = f"custom/{song_name.lower().replace(' ', '_')}"

    blob = _build_beatmap_level_so_blob(
        song_name=song_name,
        song_sub_name=f"{duration_seconds:.0f}s / {note_count_standard} notes",
        song_author=song_artist if song_artist else "Unknown Artist",
        level_author=song_artist if song_artist else "Custom",
        bpm=bpm,
        preview_diff_count=5,  # always 5 modes
        diff_data=note_count_diff_data or b'\x00' * (5 * 36),
        level_id=level_id,
    )

    log.info(f"    BeatmapLevelSO blob: {len(blob)} bytes")
    log.info(f"    _levelID={level_id} _songName={song_name} _songAuthorName={song_artist}")

    # Dump a hex sample for debugging (first 128 bytes)
    hex_sample = blob[:128].hex()
    log.info(f"    Hex[0:128]: {hex_sample}")

    # Write the blob to a temp file for inspection
    blob_path = os.path.join(PROJECT_ROOT, f"_beatmap_level_so_{song_name}.blob")
    with open(blob_path, 'wb') as f:
        f.write(blob)
    log.info(f"    ✅ Blob saved to {blob_path}")

    # Future work: inject this blob into the CAB file by:
    # 1. Parsing the UnityFS header of the saved CAB
    # 2. Finding free space or appending a new object entry
    # 3. Updating the manifest table with the new object's offset/size
    log.info("    ⚠️ Blob not yet injected into CAB (needs UnityPy type support)")
    return True


def build_plugin(project_root: str, debug: bool = False) -> str:
    """
    Build the GoldHEN plugin.
    
    Args:
        project_root: Path to the plugin project root (contains Makefile)
        debug: If True, builds with VERBOSE_LOG enabled
        
    Returns:
        Path to the built .prx file
        
    Raises:
        RuntimeError: If the build fails
    """
    import subprocess as sp

    log.info(f"Building plugin (debug={'yes' if debug else 'no'})...")
    env = os.environ.copy()
    if debug:
        env['DEBUG'] = '1'

    result = sp.run(['make', 'clean'], capture_output=True, text=True, timeout=120, cwd=project_root, env=env)
    result = sp.run(['make', '-B'], capture_output=True, text=True, timeout=300, cwd=project_root, env=env)

    if result.returncode != 0:
        log.error(f"Plugin build failed:\n{result.stdout}\n{result.stderr}")
        raise RuntimeError("Plugin build failed")

    # Determine output filename based on debug flag
    prx_name = "beat_saber_deluxe_debug.prx" if debug else "beat_saber_deluxe.prx"
    prx_path = os.path.join(project_root, prx_name)

    if not os.path.isfile(prx_path):
        log.error(f"Build succeeded but {prx_path} not found")
        raise RuntimeError(f"Plugin binary not found: {prx_path}")

    log.info(f"  ✅ Plugin built: {prx_path} ({os.path.getsize(prx_path)} bytes)")
    return prx_path


def _ftp_run(host: str, port: int, user: str, password: str, commands: list, timeout: int = 120):
    """
    Run a series of lftp commands and return (returncode, stdout, stderr).
    """
    import subprocess as sp
    user_part = f"{user},{password}" if password else f"{user},"
    # Build a single -e script with ; between commands
    script = "; ".join(commands) + "; quit"
    cmd = ["lftp", "-u", user_part, "-p", str(port), host, "-e", script]
    result = sp.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.returncode, result.stdout, result.stderr


def ensure_plugins_ini(config: dict, plugin_remote_path: str):
    """
    Read the existing plugins.ini from PS4, ensure our plugin entry exists
    under [CUSA12878], then re-upload. Idempotent — preserves other plugins.
    """
    import subprocess as sp
    import tempfile

    ps4_cfg = config.get('ps4', {})
    title_cfg = config.get('title', {})
    title_id = title_cfg.get('id', 'CUSA12878')
    host = ps4_cfg.get('ip', '192.168.100.117')
    port = ps4_cfg.get('ftp_port', 2121)
    user = ps4_cfg.get('ftp_user', 'anonymous')
    password = ps4_cfg.get('ftp_password', '')

    ini_remote = "/data/GoldHEN/plugins.ini"
    log.info(f"Ensuring plugin entry in {ini_remote}...")

    with tempfile.TemporaryDirectory() as tmpdir:
        local_ini = os.path.join(tmpdir, "plugins.ini")

        # Try to download existing plugins.ini
        rc, out, err = _ftp_run(host, port, user, password,
                                [f"get {ini_remote} -o {local_ini}"],
                                timeout=30)
        if rc != 0:
            log.info("  No existing plugins.ini found — creating new one")
            lines = []
        else:
            with open(local_ini) as f:
                lines = f.read().splitlines()
            log.info(f"  Downloaded plugins.ini ({len(lines)} lines)")

        # Parse and rebuild
        # Format: section header [TITLE_ID], followed by plugin paths
        sections = {}  # title_id -> list of plugin paths
        current_section = None
        for line in lines:
            stripped = line.strip()
            # GoldHEN supports both ; and # as comment markers
            if not stripped or stripped.startswith('#') or stripped.startswith(';'):
                continue
            if stripped.startswith('[') and stripped.endswith(']'):
                current_section = stripped[1:-1]
                if current_section not in sections:
                    sections[current_section] = []
            elif current_section and stripped:
                sections.setdefault(current_section, []).append(stripped)

        # Ensure our section exists with our plugin
        current_plugins = sections.setdefault(title_id, [])
        if plugin_remote_path not in current_plugins:
            current_plugins.append(plugin_remote_path)
            log.info(f"  Added plugin to [{title_id}]: {plugin_remote_path}")
        else:
            log.info(f"  Plugin already registered in [{title_id}]")

        # Rebuild the ini content
        new_lines = []
        for sid, plugins in sections.items():
            new_lines.append(f"[{sid}]")
            for p in plugins:
                new_lines.append(p)
            new_lines.append("")

        with open(local_ini, 'w') as f:
            f.write('\n'.join(new_lines) + '\n')

        # Upload the updated plugins.ini
        rc, out, err = _ftp_run(host, port, user, password,
                                [f"put {local_ini} -o {ini_remote}"],
                                timeout=30)
        if rc == 0:
            log.info("  ✅ plugins.ini updated")
        else:
            log.warning(f"  ⚠️ Failed to upload plugins.ini: {err}")


# ============================================================================
# Plugin Toggle — enable / disable the Beat Saber Deluxe plugin on PS4
# ============================================================================

PLUGIN_PRX_NAME = "beat_saber_deluxe.prx"
DEBUG_PRX_NAME = "beat_saber_deluxe_debug.prx"


def _find_prx_name(config: dict, debug: bool = False) -> str:
    """Return the current prx filename (handles debug toggle)."""
    return DEBUG_PRX_NAME if debug else PLUGIN_PRX_NAME


def _prx_remote_path(plugin_remote: str) -> str:
    """Extract directory from a plugin remote path."""
    return os.path.dirname(plugin_remote) or "/data/GoldHEN/plugins"


def enable_plugin(config: dict, debug: bool = False):
    """
    Enable the Beat Saber Deluxe plugin on PS4.

    Steps:
      1. Ensure plugins.ini has an uncommented entry for our .prx under [CUSA12878]
      2. If no existing entry, also upload the .prx file (build required separately)
    """
    ps4_cfg = config.get('ps4', {})
    title_cfg = config.get('title', {})
    paths_cfg = config.get('paths', {})

    title_id = title_cfg.get('id', 'CUSA12878')
    host = ps4_cfg.get('ip', '192.168.100.117')
    port = ps4_cfg.get('ftp_port', 2121)
    user = ps4_cfg.get('ftp_user', 'anonymous')
    password = ps4_cfg.get('ftp_password', '')

    prx_name = _find_prx_name(config, debug)
    plugin_remote = f"/data/GoldHEN/plugins/{prx_name}"
    ini_remote = "/data/GoldHEN/plugins.ini"

    log.info(f"Enabling Beat Saber Deluxe plugin ({prx_name}) on PS4...")

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        local_ini = os.path.join(tmpdir, "plugins.ini")

        # Download existing plugins.ini
        rc, out, err = _ftp_run(host, port, user, password,
                                [f"get {ini_remote} -o {local_ini}"],
                                timeout=30)
        if rc != 0:
            log.info("  No existing plugins.ini — creating fresh")
            lines = []
        else:
            with open(local_ini) as f:
                lines = f.read().splitlines()
            log.info(f"  Downloaded plugins.ini ({len(lines)} lines)")

        # Parse INI into sections (title_id -> list of plugin paths)
        sections = {}
        current_section = None
        for line in lines:
            stripped = line.strip()
            # Skip blank lines and comment lines (both # and ;)
            if not stripped or stripped.startswith('#') or stripped.startswith(';'):
                continue
            if stripped.startswith('[') and stripped.endswith(']'):
                current_section = stripped[1:-1]
                if current_section not in sections:
                    sections[current_section] = []
            elif current_section:
                sections.setdefault(current_section, []).append(stripped)

        # Ensure our section exists
        current_plugins = sections.setdefault(title_id, [])

        # Check if our prx already has a valid (uncommented) entry
        found = False
        for p in current_plugins:
            if p == plugin_remote:
                found = True
                break

        if not found:
            current_plugins.append(plugin_remote)
            log.info(f"  Added [{title_id}] entry: {plugin_remote}")

        # Rebuild INI content — filter out old commented/duplicate entries for our prx
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                new_lines.append(line)
                continue
            # Skip any line that is solely a comment for our prx (; or #)
            if (stripped.startswith(';') or stripped.startswith('#')):
                bare = stripped.lstrip(';#').strip()
                if bare == plugin_remote:
                    log.info(f"  Uncommented existing entry: {stripped}")
                    continue  # skip the commented version; will add uncommented below
            new_lines.append(line)

        # Now add the uncommented entry under the correct section (only if not already present)
        if not found:
            section_header = f"[{title_id}]"
            inserted = False
            merged = []
            for line in new_lines:
                merged.append(line)
                if not inserted and line.strip() == section_header:
                    merged.append(plugin_remote)
                    inserted = True
        else:
            merged = new_lines

        with open(local_ini, 'w') as f:
            f.write('\n'.join(merged) + '\n')

        # Upload updated plugins.ini
        rc, out, err = _ftp_run(host, port, user, password,
                                [f"put {local_ini} -o {ini_remote}"],
                                timeout=30)
        if rc == 0:
            log.info(f"  ✅ plugins.ini updated — plugin ENABLED")
        else:
            log.warning(f"  ⚠️ Failed to upload plugins.ini: {err}")


def disable_plugin(config: dict):
    """
    Disable the Beat Saber Deluxe plugin on PS4.

    Steps:
      1. Comment out (or remove) our .prx entry in plugins.ini under [CUSA12878]
      2. Optionally download/delete the .prx file from PS4
    """
    ps4_cfg = config.get('ps4', {})
    title_cfg = config.get('title', {})

    title_id = title_cfg.get('id', 'CUSA12878')
    host = ps4_cfg.get('ip', '192.168.100.117')
    port = ps4_cfg.get('ftp_port', 2121)
    user = ps4_cfg.get('ftp_user', 'anonymous')
    password = ps4_cfg.get('ftp_password', '')

    ini_remote = "/data/GoldHEN/plugins.ini"

    log.info(f"Disabling Beat Saber Deluxe plugin on PS4...")

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        local_ini = os.path.join(tmpdir, "plugins.ini")

        # Download existing plugins.ini
        rc, out, err = _ftp_run(host, port, user, password,
                                [f"get {ini_remote} -o {local_ini}"],
                                timeout=30)
        if rc != 0:
            log.warning("  No existing plugins.ini found — nothing to disable")
            return

        with open(local_ini) as f:
            lines = f.read().splitlines()

        # Parse and modify
        new_lines = []
        current_section = None
        disabled_count = 0

        for line in lines:
            stripped = line.strip()

            # Track section headers
            if stripped.startswith('[') and stripped.endswith(']'):
                current_section = stripped[1:-1]
                new_lines.append(line)
                continue

            if current_section == title_id:
                # Check if this line references our plugin (handle both # and ; comments)
                bare = stripped.lstrip(';#').strip()
                if PLUGIN_PRX_NAME in bare or DEBUG_PRX_NAME in bare:
                    already_commented = stripped.startswith(';') or stripped.startswith('#')
                    if not already_commented:
                        new_lines.append(f'#;{line}')
                        disabled_count += 1
                        log.info(f"  Disabled: {stripped}")
                        continue
                    else:
                        # Already commented — keep as-is
                        new_lines.append(line)
                        continue

            new_lines.append(line)

        if disabled_count == 0:
            log.info("  Plugin already disabled (or not found in plugins.ini)")
        else:
            # Upload modified plugins.ini
            local_out = os.path.join(tmpdir, "plugins_disabled.ini")
            with open(local_out, 'w') as f:
                f.write('\n'.join(new_lines) + '\n')

            rc, out, err = _ftp_run(host, port, user, password,
                                    [f"put {local_out} -o {ini_remote}"],
                                    timeout=30)
            if rc == 0:
                log.info(f"  ✅ plugins.ini updated — plugin DISABLED ({disabled_count} entry(s))")
            else:
                log.warning(f"  ⚠️ Failed to upload plugins.ini: {err}")


def deploy_plugin(prx_path: str, config: dict, debug: bool = False):
    """
    Upload the plugin .prx to PS4 and ensure plugins.ini has our entry.
    """
    import subprocess as sp

    ps4_cfg = config.get('ps4', {})
    title_cfg = config.get('title', {})
    title_id = title_cfg.get('id', 'CUSA12878')

    host = ps4_cfg.get('ip', '192.168.100.117')
    port = ps4_cfg.get('ftp_port', 2121)
    user = ps4_cfg.get('ftp_user', 'anonymous')
    password = ps4_cfg.get('ftp_password', '')

    # Plugin remote path — name matches the binary type
    prx_name = os.path.basename(prx_path)
    plugin_remote = f"/data/GoldHEN/plugins/{prx_name}"

    log.info(f"Deploying plugin to PS4: {plugin_remote}")

    # Upload the .prx
    rc, out, err = _ftp_run(host, port, user, password,
                            [f"put {prx_path} -o {plugin_remote}"],
                            timeout=120)
    if rc != 0:
        log.warning(f"  ⚠️ Plugin deploy failed (PS4 offline?): {err}")
        return

    log.info("  ✅ Plugin uploaded")

    # Now ensure plugins.ini has our entry
    ensure_plugins_ini(config, plugin_remote)


# ============================================================================
# Redirect Config Management
# ============================================================================

REDIRECT_CONFIG_FILENAME = "redirects.json"

def _get_redirect_config_path(project_root: str = PROJECT_ROOT) -> str:
    """Return the local path to redirects.json in the project root."""
    return os.path.join(project_root, REDIRECT_CONFIG_FILENAME)

def _get_remote_redirect_path(config: dict) -> str:
    """Return the remote AFR path for redirects.json."""
    cfg_paths = config.get('paths', {})
    cfg_title = config.get('title', {})
    afr_base = cfg_paths.get('afr_base', '/data/GoldHEN/AFR')
    title_id = cfg_title.get('id', 'CUSA12878')
    return f"{afr_base}/{title_id}/{REDIRECT_CONFIG_FILENAME}"

def _load_local_redirects(local_path: str) -> dict:
    """Load a local redirects.json file. Returns default structure if missing."""
    default = {
        "titleId": "CUSA12878",
        "afrBase": "/data/GoldHEN/AFR",
        "redirects": {}
    }
    if not os.path.exists(local_path):
        return default
    try:
        with open(local_path, 'r') as f:
            data = json.load(f)
        if 'redirects' not in data:
            data['redirects'] = {}
        return data
    except (json.JSONDecodeError, IOError):
        log.warning(f"  ⚠️  Failed to parse {local_path}, starting fresh")
        return default

def _download_redirect_from_ps4(config: dict) -> dict | None:
    """
    Download redirects.json from PS4 via FTP.
    Returns the parsed JSON dict, or None if the file doesn't exist.
    """
    import tempfile
    import subprocess as sp

    ps4_cfg = config.get('ps4', {})
    host = ps4_cfg.get('ip', '192.168.100.117')
    port = ps4_cfg.get('ftp_port', 2121)
    user = ps4_cfg.get('ftp_user', 'anonymous')
    password = ps4_cfg.get('ftp_password', '')
    remote_path = _get_remote_redirect_path(config)

    user_part = f"{user},{password}" if password else f"{user},"

    with tempfile.TemporaryDirectory() as tmpdir:
        local_tmp = os.path.join(tmpdir, "redirects.json")
        cmd = ["lftp", "-u", user_part, "-p", str(port), host,
               "-e", f"get {remote_path} -o {local_tmp}; quit"]
        result = sp.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0 or not os.path.exists(local_tmp):
            return None
        try:
            with open(local_tmp, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

def _deploy_redirect_to_ps4(config: dict):
    """Upload the local redirects.json to PS4 via FTP."""
    import subprocess as sp

    ps4_cfg = config.get('ps4', {})
    host = ps4_cfg.get('ip', '192.168.100.117')
    port = ps4_cfg.get('ftp_port', 2121)
    user = ps4_cfg.get('ftp_user', 'anonymous')
    password = ps4_cfg.get('ftp_password', '')
    local_path = _get_redirect_config_path()
    remote_path = _get_remote_redirect_path(config)

    if not os.path.exists(local_path):
        log.warning(f"  ⚠️  Local redirects.json not found at {local_path}")
        return

    user_part = f"{user},{password}" if password else f"{user},"
    cmd = ["lftp", "-u", user_part, "-p", str(port), host,
           "-e", f"put {local_path} -o {remote_path}; quit"]
    log.info(f"  Deploying redirect config to PS4: {remote_path}")
    result = sp.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        log.info("  ✅ Redirect config deployed")
    else:
        log.warning(f"  ⚠️  Redirect config deploy failed: {result.stderr}")

def manage_redirect_config(
    config: dict,
    target_name: str | None = None,
    bundle_suffix: str | None = None,
    generate: bool = False,
    deploy: bool = False,
    sync: bool = False,
    enforce_local: bool = False,
):
    """
    Manage the redirects.json configuration file.

    Modes:
      generate=True:  Create/update local redirects.json with the current target.
      sync=True:      Download existing config from PS4, merge, save locally, redeploy.
      enforce_local=True: Use only the local redirects.json as truth, deploy it to PS4.
      deploy=True:    Deploy the local redirects.json to PS4.

    When called without any mode flags, auto-generates if local file is missing
    or if a deploy/sync is happening.
    """
    cfg_paths = config.get('paths', {})
    # Use same suffix as deploy_to_ps4() so redirect filenames match actual bundle filenames
    if bundle_suffix is None:
        bundle_suffix = cfg_paths.get('afr_target_suffix', '_v3')
    cfg_title = config.get('title', {})
    title_id = cfg_title.get('id', 'CUSA12878')
    afr_base = cfg_paths.get('afr_base', '/data/GoldHEN/AFR')
    local_path = _get_redirect_config_path()

    # Determine what to do
    should_generate = generate or (deploy and not os.path.exists(local_path))
    should_deploy = deploy or sync or enforce_local
    should_sync = sync

    redirect_data = None

    # SYNC mode: download from PS4 first
    if should_sync:
        log.info("🔄 Syncing redirect config from PS4...")
        ps4_data = _download_redirect_from_ps4(config)
        if ps4_data is not None:
            redirect_data = ps4_data
            log.info(f"  Downloaded config with {len(ps4_data.get('redirects', {}))} redirects")
        else:
            log.info("  No existing config on PS4, starting fresh")
            redirect_data = {
                "titleId": title_id,
                "afrBase": afr_base,
                "redirects": {}
            }
    else:
        # GENERATE mode: load local config or start fresh
        redirect_data = _load_local_redirects(local_path)

    # Update redirect_data with current title/afr settings
    redirect_data['titleId'] = title_id
    redirect_data['afrBase'] = afr_base

    # ENFORCE LOCAL mode: reload from local file, ignoring any PS4 data
    if enforce_local and os.path.exists(local_path):
        redirect_data = _load_local_redirects(local_path)
        log.info(f"  Enforcing local config ({len(redirect_data.get('redirects', {}))} redirects)")

    # If we have a target, add/update the entry
    if target_name and should_generate:
        bundle_name = f"{target_name}{bundle_suffix}"
        redirect_data.setdefault('redirects', {})[target_name] = bundle_name
        log.info(f"  Added redirect: {target_name} -> {bundle_name}")

    # Save updated config locally
    os.makedirs(os.path.dirname(local_path) or '.', exist_ok=True)
    with open(local_path, 'w') as f:
        json.dump(redirect_data, f, indent=2)
        f.write('\n')
    count = len(redirect_data.get('redirects', {}))
    log.info(f"  Saved redirects.json ({count} redirects)")

    # Deploy to PS4 if requested
    if should_deploy:
        _deploy_redirect_to_ps4(config)

    return redirect_data


# ============================================================================
# Feature Flags Management
# ============================================================================

FEATURES_FILENAME = "features.json"
DEFAULT_FEATURES = {
    "enable_custom_song_replacements": True,
    "enable_song_metadata_modification": True
}

def _get_local_features_path(project_root: str = PROJECT_ROOT) -> str:
    """Return the local path to features.json in the project root."""
    return os.path.join(project_root, FEATURES_FILENAME)

def _get_remote_features_path(config: dict) -> str:
    """Return the remote AFR path for features.json."""
    cfg_paths = config.get('paths', {})
    cfg_title = config.get('title', {})
    afr_base = cfg_paths.get('afr_base', '/data/GoldHEN/AFR')
    title_id = cfg_title.get('id', 'CUSA12878')
    return f"{afr_base}/{title_id}/{FEATURES_FILENAME}"

def _load_local_features(local_path: str) -> dict:
    """Load a local features.json file. Returns default structure if missing."""
    if not os.path.exists(local_path):
        return DEFAULT_FEATURES.copy()
    try:
        with open(local_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        log.warning(f"  ⚠️  Failed to parse {local_path}, using defaults")
        return DEFAULT_FEATURES.copy()

def _save_local_features(features: dict, local_path: str):
    """Save features dict to local features.json."""
    os.makedirs(os.path.dirname(local_path) or '.', exist_ok=True)
    with open(local_path, 'w') as f:
        json.dump(features, f, indent=2)
        f.write('\n')
    log.info(f"  Saved {local_path}")

def _deploy_features_to_ps4(config: dict):
    """Upload the local features.json to PS4 via FTP."""
    import subprocess as sp

    ps4_cfg = config.get('ps4', {})
    host = ps4_cfg.get('ip', '192.168.100.117')
    port = ps4_cfg.get('ftp_port', 2121)
    user = ps4_cfg.get('ftp_user', 'anonymous')
    password = ps4_cfg.get('ftp_password', '')
    local_path = _get_local_features_path()
    remote_path = _get_remote_features_path(config)

    if not os.path.exists(local_path):
        log.warning(f"  ⚠️  Local features.json not found at {local_path}")
        return

    user_part = f"{user},{password}" if password else f"{user},"
    cmd = ["lftp", "-u", user_part, "-p", str(port), host,
           "-e", f"put {local_path} -o {remote_path}; quit"]
    log.info(f"  Deploying features.json to PS4: {remote_path}")
    result = sp.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        log.info("  ✅ Features config deployed")
    else:
        log.warning(f"  ⚠️  Features config deploy failed: {result.stderr}")

def apply_feature_flags(set_features: list, config: dict):
    """
    Apply feature flag changes from --set-feature arguments.

    Args:
        set_features: List of "key=value" strings (e.g. ["enable_song_metadata_modification=false"])
        config: PS4 config dict
    """
    if not set_features:
        return

    local_path = _get_local_features_path()
    features = _load_local_features(local_path)

    for entry in set_features:
        if '=' not in entry:
            log.error(f"  ❌ Invalid --set-feature format: '{entry}' (expected key=true/false)")
            continue
        key, val_str = entry.split('=', 1)
        key = key.strip()
        val_str = val_str.strip().lower()
        if val_str in ('true', '1', 'yes', 'on'):
            val = True
        elif val_str in ('false', '0', 'no', 'off'):
            val = False
        else:
            log.error(f"  ❌ Invalid feature value: '{val_str}' (expected true/false)")
            continue
        features[key] = val
        log.info(f"  Feature flag: {key} = {val}")

    _save_local_features(features, local_path)
    _deploy_features_to_ps4(config)


# ============================================================================
# Song Metadata Management
# ============================================================================

SONG_METADATA_FILENAME = "song_metadata.json"

def _get_song_metadata_path(project_root: str = PROJECT_ROOT) -> str:
    """Return the local path to song_metadata.json in the project root."""
    return os.path.join(project_root, SONG_METADATA_FILENAME)

def _get_remote_song_metadata_path(config: dict) -> str:
    """Return the remote AFR path for song_metadata.json."""
    cfg_paths = config.get('paths', {})
    cfg_title = config.get('title', {})
    afr_base = cfg_paths.get('afr_base', '/data/GoldHEN/AFR')
    title_id = cfg_title.get('id', 'CUSA12878')
    return f"{afr_base}/{title_id}/{SONG_METADATA_FILENAME}"

def _load_local_song_metadata(local_path: str) -> dict:
    """Load a local song_metadata.json file. Returns default structure if missing."""
    default = {"song_names": {}, "song_artists": {}}
    if not os.path.exists(local_path):
        return default
    try:
        with open(local_path, 'r') as f:
            data = json.load(f)
        data.setdefault('song_names', {})
        data.setdefault('song_artists', {})
        return data
    except (json.JSONDecodeError, IOError):
        log.warning(f"  ⚠️  Failed to parse {local_path}, starting fresh")
        return default

def _deploy_song_metadata_to_ps4(config: dict):
    """Upload the local song_metadata.json to PS4 via FTP."""
    import subprocess as sp

    ps4_cfg = config.get('ps4', {})
    host = ps4_cfg.get('ip', '192.168.100.117')
    port = ps4_cfg.get('ftp_port', 2121)
    user = ps4_cfg.get('ftp_user', 'anonymous')
    password = ps4_cfg.get('ftp_password', '')
    local_path = _get_song_metadata_path()
    remote_path = _get_remote_song_metadata_path(config)

    if not os.path.exists(local_path):
        log.warning(f"  ⚠️  Local song_metadata.json not found at {local_path}")
        return

    user_part = f"{user},{password}" if password else f"{user},"
    cmd = ["lftp", "-u", user_part, "-p", str(port), host,
           "-e", f"put {local_path} -o {remote_path}; quit"]
    log.info(f"  Deploying song_metadata.json to PS4: {remote_path}")
    result = sp.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        log.info("  ✅ Song metadata deployed")
    else:
        log.warning(f"  ⚠️  Song metadata deploy failed: {result.stderr}")

def manage_song_metadata(
    config: dict,
    song_name: str | None = None,
    artist: str | None = None,
    target_name: str | None = None,
    deploy: bool = False,
):
    """
    Manage the song_metadata.json configuration file.

    When song_name and target_name are provided, adds/updates the song_names entry.
    When artist and target_name are provided, adds/updates the song_artists entry.
    Always deploys to PS4 when deploy=True.
    """
    local_path = _get_song_metadata_path()
    metadata = _load_local_song_metadata(local_path)

    if song_name and target_name:
        metadata['song_names'][target_name] = song_name
        log.info(f"  Song metadata: '{target_name}' -> '{song_name}'")
    if artist and target_name:
        metadata['song_artists'][target_name] = artist
        log.info(f"  Artist metadata: '{target_name}' -> '{artist}'")

    os.makedirs(os.path.dirname(local_path) or '.', exist_ok=True)
    with open(local_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        f.write('\n')
    count_names = len(metadata.get('song_names', {}))
    count_artists = len(metadata.get('song_artists', {}))
    log.info(f"  Saved song_metadata.json ({count_names} names, {count_artists} artists)")

    if deploy:
        _deploy_song_metadata_to_ps4(config)

    return metadata

BEATSAVER_API_BASE = "https://api.beatsaver.com"

def download_beat_saver_song(map_id: str, output_dir: str | None = None,
                             api_base: str | None = None) -> str:
    """
    Download a song from BeatSaver by its map key and extract it.

    Args:
        map_id: The BeatSaver map key (e.g. '1d6c7c2' from beatsaver.com/maps/1d6c7c2)
        output_dir: Directory to extract into. If None, uses a temp directory.
        api_base: Override BeatSaver API base URL (default: https://api.beatsaver.com)

    Returns:
        Path to the extracted song directory containing info.dat/Easy.dat/etc.
    """
    import urllib.request
    import urllib.error
    import tempfile
    import zipfile
    import shutil

    base = api_base or BEATSAVER_API_BASE
    download_url = f"{base}/maps/id/{map_id}/download"
    info_url = f"{base}/maps/id/{map_id}"

    log.info(f"Downloading BeatSaver song: {map_id}")
    log.info(f"  API: {info_url}")

    # Try to fetch song info first (extracts download URL from the API response)
    song_name = map_id
    cdn_url = None
    try:
        req = urllib.request.Request(info_url, headers={"User-Agent": "BeatSaberDeluxe/0.54"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            info_data = json.loads(resp.read().decode('utf-8'))
            if info_data.get('name'):
                song_name = info_data['name']
                log.info(f"  Song: {song_name} by {info_data.get('metadata', {}).get('songAuthorName', '?')}")
            # Check if it has the required beatmap characteristics
            versions = info_data.get('versions', [])
            if versions:
                v0 = versions[0]
                diffs = v0.get('diffs', [])
                has_standard = any(d.get('characteristic','').lower() == 'standard' for d in diffs)
                if not has_standard:
                    log.warning("  ⚠️  Song has no Standard characteristic beatmaps (may not work)")
                # Extract download URL — BeatSaver uses CDN: cdn.beatsaver.com/<hash>.zip
                cdn_url = v0.get('downloadURL')
                if not cdn_url and v0.get('hash'):
                    cdn_url = f"https://cdn.beatsaver.com/{v0['hash']}.zip"
                if cdn_url:
                    log.info(f"  Download URL: {cdn_url}")
    except Exception as e:
        log.warning(f"  ⚠️  Could not fetch song info: {e}")

    if not cdn_url:
        # Fallback: try the direct download endpoint
        cdn_url = download_url
        log.warning("  Using fallback download URL (may not work)")

    # Download the zip
    tmp_dir = output_dir or tempfile.mkdtemp(prefix="beatsaver_")
    zip_path = os.path.join(tmp_dir, f"{map_id}.zip")

    try:
        req = urllib.request.Request(cdn_url, headers={"User-Agent": "BeatSaberDeluxe/0.54"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            total_size = int(resp.headers.get('Content-Length', 0))
            log.info(f"  Downloading ({total_size / 1024 / 1024:.1f} MB)...")
            with open(zip_path, 'wb') as f:
                f.write(resp.read())
    except urllib.error.HTTPError as e:
        log.error(f"  ❌ Download failed (HTTP {e.code}): {e.reason}")
        raise RuntimeError(f"BeatSaver download failed for map {map_id}")
    except Exception as e:
        log.error(f"  ❌ Download failed: {e}")
        raise

    # Extract
    extract_dir = os.path.join(tmp_dir, map_id)
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)

    os.unlink(zip_path)  # Remove zip to save space
    log.info(f"  ✅ Extracted to {extract_dir}")

    # Show found beatmap files
    files = [f for f in os.listdir(extract_dir) if f.endswith(('.dat', '.json'))]
    log.info(f"  Found {len(files)} beatmap files")

    return extract_dir


# ============================================================================
# Main
# ============================================================================

def main():
    # Print pipeline version
    ver_path = os.path.join(PROJECT_ROOT, 'VERSION')
    if os.path.exists(ver_path):
        with open(ver_path) as f:
            ver = f.read().strip()
    else:
        ver = "unknown"
    print(f"🎵 Beat Saber Deluxe Pipeline {ver}")
    print(f"   Project: {PROJECT_ROOT}")
    print()

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

  # Build & deploy plugin (release — no verbose logging on PS4):
  python3 full_custom_song_pipeline.py --song-dir ./my_song --target startmeup --deploy-plugin

  # Build & deploy plugin (debug — verbose PS4 logging for development):
  python3 full_custom_song_pipeline.py --song-dir ./my_song --target startmeup --deploy-plugin --debug-logging

  # Just build & deploy plugin (song-dir still required for config):
  python3 full_custom_song_pipeline.py --song-dir ./my_song --target startmeup --deploy-plugin --preserve-metadata --no-pad

  # Build song AND generate/update redirects.json:
  python3 full_custom_song_pipeline.py --song-dir ./my_song --target startmeup --generate-config

  # Build song, update redirects.json, deploy both bundle + config to PS4:
  python3 full_custom_song_pipeline.py --song-dir ./my_song --target startmeup --deploy --deploy-config

  # Sync redirect config from PS4, merge with current build, redeploy:
  python3 full_custom_song_pipeline.py --song-dir ./my_song --target startmeup --sync-config

  # Enforce local redirects.json as truth and deploy to PS4 (no merge):
  python3 full_custom_song_pipeline.py --enforce-config --deploy

  # Download a song from BeatSaver and deploy to PS4 in one command:
  python3 full_custom_song_pipeline.py --download-beat-saver-song 1d6c7c2 --target BadGuy --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config
        """
    )
    parser.add_argument('--song-dir', default=None,
                        help='Folder containing the custom song (WAV + .dat/.json beatmaps)')
    parser.add_argument('--audio', default=None,
                        help='Pre-encoded FSB5 file (optional: skips WAV->FSB5 conversion)')
    parser.add_argument('--config', default=DEFAULT_CONFIG_PATH,
                        help='Path to PS4 config JSON (default: ./ps4_config.json)')
    parser.add_argument('--target', default=None,
                        help='Target song name (default from config: startmeup)')
    parser.add_argument('--template', default=None,
                        help='Path to the target song template bundle (default from config)')
    parser.add_argument('--output', default=None,
                        help='Output bundle path (default from config)')
    parser.add_argument('--deploy', action='store_true',
                        help='Deploy to PS4 via FTP after building')
    parser.add_argument('--target-ip', default=None,
                        help='PS4 IP address for FTP deployment (overrides config)')
    parser.add_argument('--no-pad', action='store_true',
                        help='Skip padding FSB5 to 12MB')
    parser.add_argument('--preserve-metadata', action='store_true',
                        help='Do NOT update AudioClip or audio.gz metadata (uses original values)')
    parser.add_argument('--ignore-non-standard-beatmaps', action='store_true',
                        help='Only match beatmap files containing "Standard" in name '
                             '(ignores 360Degree, 90Degree, OneSaber variants)')
    parser.add_argument('--enable-modes', type=str, default=None,
                        help='Comma-separated list of additional beatmap characteristics to enable '
                             '(e.g. "OneSaber,90Degree,Degree"). Makes the song playable in those '
                             'modes by cloning the Standard beatmaps.')
    parser.add_argument('--vorbis', action='store_true',
                        help='Use Vorbis format (mode=15) instead of HEVAG for the FSB5 audio')
    parser.add_argument('--pcm16', action='store_true',
                        help='Use PCM16 format (codec=2) instead of HEVAG for the FSB5 audio (lossless)')
    parser.add_argument('--deploy-plugin', action='store_true',
                        help='Build and deploy the GoldHEN plugin to PS4')
    parser.add_argument('--debug-logging', action='store_true',
                        help='Build plugin with verbose logging (VERBOSE_LOG define). '
                             'Only meaningful with --deploy-plugin.')
    parser.add_argument('--convert-to-v3', action='store_true',
                        help='Auto-convert V2 beatmaps (_notes/_time) to V3.2.0 format (colorNotes/b). '
                             'Use if custom songs use V2 format.')

    # Plugin toggle flags
    parser.add_argument('--enable-plugin', action='store_true',
                        help='Enable the Beat Saber Deluxe plugin on PS4 '
                             '(uncomment .prx entry in plugins.ini)')
    parser.add_argument('--disable-plugin', action='store_true',
                        help='Disable the Beat Saber Deluxe plugin on PS4 '
                             '(comment out .prx entry in plugins.ini — play original songs)')

    # Redirect config management flags
    parser.add_argument('--generate-config', action='store_true',
                        help='Generate/update redirects.json with the current --target entry '
                             '(creates file if missing)')
    parser.add_argument('--deploy-config', action='store_true',
                        help='Deploy the local redirects.json to PS4 via FTP')
    parser.add_argument('--sync-config', action='store_true',
                        help='Download config from PS4, merge with current target, save, redeploy')
    parser.add_argument('--enforce-config', action='store_true',
                        help='Use only the local redirects.json as truth and deploy it to PS4')

    # BeatSaver song download
    parser.add_argument('--download-beat-saver-song', default=None, metavar='MAP_ID',
                        help='Download a song from BeatSaver by map key (e.g. "1d6c7c2") '
                             'and run the full pipeline. Requires --target to specify the PS4 slot.')
    parser.add_argument('--beatsaver-api-base', default=None,
                        help='Override BeatSaver API base URL (default: https://api.beatsaver.com). '
                             'Useful for testing against a mirror or local server.')

    # Song metadata override for BeatmapLevelSO injection into CAB bundle
    parser.add_argument('--song-name', default=None,
                        help='Override song display name (default: extracted from Info.dat or BeatSaver)')
    parser.add_argument('--artist', default=None,
                        help='Override artist/song-author name (default: extracted from Info.dat or BeatSaver)')

    # Feature flags
    parser.add_argument('--set-feature', action='append', default=None,
                        help='Set a feature flag (format: feature_name=true/false). '
                             'Can be used multiple times. Flags are written to features.json '
                             'on PS4 at /data/GoldHEN/AFR/CUSA12878/features.json.')

    args = parser.parse_args()

    # Load PS4 config first
    config = load_config(args.config)
    cfg_ps4 = config.get('ps4', {})
    cfg_title = config.get('title', {})
    cfg_paths = config.get('paths', {})

    # Plugin-only mode: deploy plugin and exit
    if args.deploy_plugin and not args.song_dir:
        deploy_plugin(
            os.path.join(PROJECT_ROOT, 'beat_saber_deluxe.prx'),
            {'ps4': cfg_ps4, 'title': cfg_title},
            debug=args.debug_logging
        )
        log.info("Plugin deployment complete (no song processed)")

        # Handle redirect config in plugin-only mode
        if args.generate_config or args.deploy_config or args.sync_config or args.enforce_config or args.deploy:
            manage_redirect_config(
                {'ps4': cfg_ps4, 'title': cfg_title, 'paths': cfg_paths},
                target_name=None,
                generate=args.generate_config,
                deploy=(args.deploy_config or args.sync_config or args.enforce_config),
                sync=args.sync_config,
                enforce_local=args.enforce_config,
            )

        # Handle feature flags in plugin-only mode
        if args.set_feature:
            apply_feature_flags(args.set_feature, {'ps4': cfg_ps4, 'title': cfg_title, 'paths': cfg_paths})

        sys.exit(0)

    # Plugin toggle mode: enable/disable without processing any song
    if args.enable_plugin and not args.disable_plugin:
        enable_plugin(config, debug=args.debug_logging)
        log.info("Plugin enabled. Restart the game or press PS+Triangle to reload plugins.")
        sys.exit(0)
    if args.disable_plugin:
        disable_plugin(config)
        log.info("Plugin disabled. Restart the game or press PS+Triangle to reload plugins.")
        sys.exit(0)

    # Auto-download from BeatSaver if requested (sets args.song_dir before the dir check)
    if args.download_beat_saver_song and not args.song_dir:
        log.info("Downloading song from BeatSaver...")
        extracted_dir = download_beat_saver_song(args.download_beat_saver_song,
                                                  api_base=args.beatsaver_api_base)
        args.song_dir = extracted_dir
    elif args.download_beat_saver_song and args.song_dir:
        log.info(f"Using local song directory: {args.song_dir} (ignoring --download-beat-saver-song)")

    # --song-dir is required for song processing
    if not args.song_dir:
        parser.error('--song-dir is required (or use --deploy-plugin to deploy plugin only)')
    cfg_pipe = config.get('pipeline', {})

    if args.target is None:
        args.target = cfg_pipe.get('default_target', 'startmeup')
    if args.template is None:
        game_dump = cfg_paths.get('game_dump_dir', '/workspace/ps4_dump/CUSA12878-patch')
        tmpl_dir = cfg_paths.get('template_dir', 'Media/StreamingAssets/BeatmapLevelsData')
        args.template = f"{game_dump}/{tmpl_dir}/{args.target}"
    if args.output is None:
        out_dir = cfg_paths.get('output_dir', '/workspace/beat_saber_deluxe/custom_songs')
        args.output = f"{out_dir}/{args.target}_custom.bundle"
    if args.target_ip is None:
        args.target_ip = cfg_ps4.get('ip', '192.168.100.117')
    # Override config IP with --target-ip if explicitly provided
    cfg_ps4['ip'] = args.target_ip

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
        # Extract duration from sample descriptor (works for all codecs)
        sd_raw = struct.unpack_from('<Q', fsb5_bytes, 60)[0]
        total_frames = (sd_raw >> 34) & ((1 << 30) - 1)
        # Try to get sample rate from FREQUENCY metadata chunk (offset 77)
        freq = struct.unpack_from('<I', fsb5_bytes, 77)[0]
        actual_sample_rate = freq if 8000 < freq < 192000 else SAMPLE_RATE
        duration = total_frames / float(actual_sample_rate) if actual_sample_rate > 0 else 0
    else:
        log.info("Searching for audio file in song directory (.wav, .ogg, ...)...")
        audio_files = [f for f in os.listdir(args.song_dir)
                       if f.endswith(('.wav', '.ogg', '.flac', '.mp3', '.aiff', '.egg'))]
        if not audio_files:
            log.error(f"No audio files found in {args.song_dir}")
            sys.exit(1)

        audio_path = os.path.join(args.song_dir, audio_files[0])
        # Get sample rate via soundfile before full conversion
        info = sf.info(audio_path)

        # -------------------------------------------------------------------
        # Step 0b: Detect & handle lapped-up audio
        # -------------------------------------------------------------------
        lap_info = detect_lapped(args.song_dir, info.duration)
        if lap_info['is_lapped']:
            audio_path = lap_audio(audio_path, lap_info)
            info = sf.info(audio_path)

        if args.vorbis:
            log.info("Using VORBIS format (mode=15) for FSB5")
            actual_sample_rate = min(info.samplerate, 44100)
            fsb5_bytes = build_vorbis_fsb5(audio_path,
                                            clip_seconds=30,
                                            pad_to_size=ORIGINAL_RESOURCE_SIZE)
            # Get PCM frame count from FSB5 sample descriptor
            sd_raw = struct.unpack_from('<Q', fsb5_bytes, 60)[0]
            total_frames = (sd_raw >> 34) & ((1 << 30) - 1)
            duration = total_frames / float(actual_sample_rate) if actual_sample_rate > 0 else 0
            log.info(f"  Vorbis FSB5: {len(fsb5_bytes)} bytes, {duration:.1f}s")
        elif args.pcm16:
            log.info("Using PCM16 format (codec=2) for FSB5 (lossless)")
            actual_sample_rate = min(info.samplerate, 44100)
            pad_to = 0 if args.no_pad else ORIGINAL_RESOURCE_SIZE
            fsb5_bytes = build_pcm16_fsb5(audio_path, pad_to_size=pad_to)
            # Get frame count from FSB5 sample descriptor
            sd_raw = struct.unpack_from('<Q', fsb5_bytes, 60)[0]
            total_frames = (sd_raw >> 34) & ((1 << 30) - 1)
            duration = total_frames / float(actual_sample_rate) if actual_sample_rate > 0 else 0
            log.info(f"  PCM16 FSB5: {len(fsb5_bytes)} bytes, {duration:.1f}s")
        else:
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

    bf, cab, cab_key, resource_key = load_target_bundle(args.template)
    log.info(f"Target: {args.target}")

    # -----------------------------------------------------------------------
    # Step 2: Replace .resource
    # -----------------------------------------------------------------------
    replace_resource(bf, fsb5_bytes, resource_key)

    if args.preserve_metadata:
        log.info("  --preserve-metadata: Skipping AudioClip and audio.gz updates")
    else:
        # -----------------------------------------------------------------------
        # Step 3: Update AudioClip
        # -----------------------------------------------------------------------
        update_audioclip(cab, fsb5_bytes, duration, actual_sample_rate)

        # -----------------------------------------------------------------------
        # Step 4: Update audio.gz (with correct BPM region data)
        # -----------------------------------------------------------------------
        sample_count = int(duration * actual_sample_rate)
        bpm_regions = load_bpm_regions(args.song_dir, sample_count)
        update_audio_gz(cab, duration, actual_sample_rate, bpm_regions)

    # -----------------------------------------------------------------------
    # Step 5: Replace beatmaps
    # -----------------------------------------------------------------------
    replaced = replace_beatmaps(cab, args.song_dir,
                                  ignore_non_standard=args.ignore_non_standard_beatmaps,
                                  auto_convert=args.convert_to_v3)
    log.info(f"Beatmaps replaced: {replaced}/5")

    # -----------------------------------------------------------------------
    # Step 6: Add mode characteristics (OneSaber, 90Degree, etc.)
    # -----------------------------------------------------------------------
    enable_modes = args.enable_modes.split(',') if args.enable_modes else None
    if enable_modes:
        add_mode_characteristics(cab, [m.strip() for m in enable_modes if m.strip()])

    # -----------------------------------------------------------------------
    # Step 6.5: Inject BeatmapLevelSO metadata for song menu display
    # -----------------------------------------------------------------------
    # Resolve song name and artist — from CLI args, Info.dat, or BeatSaver
    info_bpm = bpm  # already loaded above if available
    custom_name = args.song_name
    custom_artist = args.artist

    if not custom_name and os.path.isfile(os.path.join(args.song_dir, "Info.dat")):
        with open(os.path.join(args.song_dir, "Info.dat")) as f:
            info = json.load(f)
        custom_name = custom_name or info.get("_songName", song_name)
        if not custom_artist:
            custom_artist = info.get("_songAuthorName", song_artist)

    # BeatmapLevelSO injection (experimental — needs PS4 testing)
    inject_level_so = True  # always try to inject; game should just ignore unknown SOs
    if inject_level_so:
        note_data = b''  # empty diff data — the preview array will use Standard's data
        inject_beatmap_level_so(
            cab,
            song_name=custom_name or song_name,
            song_artist=custom_artist or song_artist,
            duration_seconds=duration,
            bpm=info_bpm,
            note_count_standard=note_count_standard,
            note_count_diff_data=note_data,
        )

    # -----------------------------------------------------------------------
    # Step 7: Save bundle
    # -----------------------------------------------------------------------
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    save_bundle(bf, args.output)

    # -----------------------------------------------------------------------
    # Step 7: Deploy bundle to PS4
    # -----------------------------------------------------------------------
    if args.deploy:
        deploy_to_ps4(args.output, args.target, config)

    # -----------------------------------------------------------------------
    # Step 8: Build & deploy plugin to PS4
    # -----------------------------------------------------------------------
    if args.deploy_plugin:
        prx_path = build_plugin(PROJECT_ROOT, debug=args.debug_logging)
        deploy_plugin(prx_path, config, debug=args.debug_logging)

    # -----------------------------------------------------------------------
    # Step 9: Manage redirect config (redirects.json)
    # -----------------------------------------------------------------------
    # Auto-generate and auto-deploy config when deploying bundles
    should_generate = args.generate_config or args.deploy_config or args.sync_config or args.deploy
    should_deploy = args.deploy_config or args.sync_config or args.enforce_config or args.deploy
    if should_generate or should_deploy or args.sync_config or args.enforce_config:
        manage_redirect_config(
            config,
            target_name=args.target,
            generate=should_generate,
            deploy=should_deploy,
            sync=args.sync_config,
            enforce_local=args.enforce_config,
        )

    # -----------------------------------------------------------------------
    # Step 10: Feature flags
    # -----------------------------------------------------------------------
    if args.set_feature:
        apply_feature_flags(args.set_feature, config)

    # -----------------------------------------------------------------------
    # Step 11: Song metadata (song_metadata.json)
    # -----------------------------------------------------------------------
    if args.song_name or args.artist or args.deploy:
        manage_song_metadata(
            config,
            song_name=args.song_name,
            artist=args.artist,
            target_name=args.target,
            deploy=args.deploy,
        )

    log.info("Pipeline complete!")
    log.info(f"  Bundle: {args.output}")
    log.info(f"  Size: {os.path.getsize(args.output)} bytes")
    log.info(f"  Audio: {len(fsb5_bytes)} bytes, {duration:.1f}s")
    log.info(f"  Beatmaps: {replaced}/5 replaced")


if __name__ == "__main__":
    main()
