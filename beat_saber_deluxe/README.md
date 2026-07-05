# Beat Saber Deluxe 🎵⚡

**Custom song replacement for PlayStation 4 Beat Saber (CUSA12878)**

Replace any song's audio and beatmaps with your own content, all through a convenient pipeline — no game modding required. Works via GoldHEN's file redirection hook.

## Demo

✅ **Confirmed working:** PCM16 FSB5 (codec=2) custom audio plays on PS4. Custom beatmaps display and interact correctly. Tested with CUSA12878 patched (v1.29).

**Status:** 🏆 **v0.50 Alpha** — Basic song replacement pipeline operational!

## How It Works

```
[Custom .wav] → FSB5 encoder → .resource replacement → PS4 deployment → Plays!
[Custom .dat] → Beatmap     → .beatmap.gz replacement     → PS4 deployment → Plays!
```

The plugin hooks file open operations and redirects `BeatmapLevelsData/<song_id>` to a custom bundle on the PS4's data partition. No original game files are modified.

## Prerequisites

| Item | Required | Notes |
|------|----------|-------|
| PS4 with GoldHEN | ✅ | v2.4b+ recommended |
| FTP server on PS4 | ✅ | Enable in GoldHEN settings |
| Network connection | ✅ | Between PC and PS4 |
| Beat Saber installed | ✅ | CUSA12878 (patched), any region |
| Linux/macOS/Windows | ✅ | Python 3.10+ required |
| Python packages | ✅ | `pip install soundfile numpy pyfmodex` |

## Quick Start (5 minutes)

### 1. Install the Plugin on PS4

Connect to your PS4 via FTP (default: port 1337, or 2121 via lftp):

```bash
# Copy the PRX plugin
lftp -u anonymous, -p 1337 192.168.100.117 -e "put /workspace/beat_saber_deluxe/beat_saber_deluxe.prx -o /data/GoldHEN/plugins/beat_saber_deluxe.prx; quit"
```

### 2. Configure plugins.ini (Nondestructive)

> **Important:** This approach preserves any existing plugins (like RB4DX). Only the Beat Saber Deluxe entry is added.

Connect to your PS4's FTP, then download and edit `plugins.ini`:

```bash
# Download current plugins.ini
lftp -u anonymous, -p 2121 192.168.100.117 -e "get /data/GoldHEN/config/plugins.ini -o /tmp/plugins.ini; quit"

# Edit to add the plugin (or use the script below)
```

**Minimum plugins.ini configuration:**

```ini
# GoldHEN Plugin Configuration
# Append this section — don't remove existing entries!

beat_saber_deluxe=/data/GoldHEN/plugins/beat_saber_deluxe.prx
```

**Scripted approach (recommended):** Use the `prepare_binary_patch.py` tool to nondestructively add the entry:

```bash
python3 /workspace/beat_saber_deluxe/tools/prepare_binary_patch.py \
  --add-plugin /data/GoldHEN/plugins/beat_saber_deluxe.prx
```

Or manually using lftp:

```bash
# Append to plugins.ini on PS4 (preserves existing entries)
printf '\n# Beat Saber Deluxe\ndev=/data/GoldHEN/plugins/beat_saber_deluxe.prx\n' > /tmp/add_bdlx
lftp -u anonymous, -p 2121 192.168.100.117 -e "put /tmp/add_bdlx -o /data/GoldHEN/config/plugins.ini; quit"
```

### 3. Create the Target Directory

```bash
lftp -u anonymous, -p 2121 192.168.100.117 -e "mkdir -p /data/GoldHEN/AFR/CUSA12878/startmeup_v3; quit"
```

> The AFR directory path is: `/data/GoldHEN/AFR/<TITLE_ID>/<TARGET_NAME>/`

### 4. Restart PS4

Reboot your PS4 to load the new plugin. GoldHEN will automatically enable it.

### 5. Find Your Song

The pipeline expects a song directory with:
- An audio file (`.wav`, `.ogg`, `.flac`, `.mp3`, `.aiff`)
- Beatmap files (`.dat` format, one per difficulty)

Your song directory should look like:

```
songs/my_song/
├── song.wav                # Your audio file
├── EasyStandard.dat        # Beatmap: Easy
├── NormalStandard.dat      # Beatmap: Normal  
├── HardStandard.dat        # Beatmap: Hard
├── ExpertStandard.dat      # Beatmap: Expert
└── ExpertPlusStandard.dat  # Beatmap: Expert+
```

To download a song from BeatSaver, use:

```bash
# Download a song by key (e.g., key "1abcd")
python3 /workspace/beat_saber_deluxe/tools/convert_song.py --download 1abcd -o /workspace/songs/my_song
```

Or extract from a custom song zip:

```bash
# Extract a BeatSaver .zip
unzip song.zip -d /workspace/songs/my_song
```

### 6. Deploy Your Song

Use the custom song pipeline to process and deploy in one command:

```bash
python3 /workspace/beat_saber_deluxe/tools/full_custom_song_pipeline.py \
  --song-dir /workspace/songs/my_song \
  --pcm16 \
  --target startmeup \
  --deploy
```

**What this does:**
1. Reads your audio file (resamples to 44100Hz if needed)
2. Encode as PCM16 FSB5 (lossless, bit-identical round-trip)
3. Loads the target game bundle
4. Replaces the audio resource
5. Replaces all 5 difficulty beatmaps
6. Saves the bundle with LZ4 compression
7. Uploads to PS4 via FTP

### 7. Play!

1. Launch Beat Saber on your PS4
2. Select **Start Me Up** (the original song is being replaced)
3. Play with your custom audio and beatmaps! 🎮

> **Note:** PCM16 at 44100Hz stereo fills the 12MB PS4 resource limit at ~70 seconds. Songs longer than this are automatically clipped to fit. For full-length songs, see Advanced Configuration below.

## Audio Format Details

### PCM16 (Recommended — Works!) ✅

| Property | Value |
|----------|-------|
| Codec | 2 (PCM16LE) |
| Sample rate | 44100 Hz |
| Channels | 2 (stereo) |
| Quality | Lossless (bit-identical) |
| Max duration | ~70 seconds (12MB limit) |
| Pipeline flag | `--pcm16` |

PCM16 is the reliable format — it's simple, lossless, and the PS4's FMOD handles it natively.

### Vorbis (Experimental) ⚠️

| Property | Value |
|----------|-------|
| Codec | 15 (Vorbis) |
| Pipeline flag | `--vorbis` |

Vorbis is currently blocked by a codebook mismatch between libvorbis (oggenc) and the FMOD Vorbis decoder lookup table. The PS4's FMOD expects Vorbis data encoded with FMOD's fsbank tool.

### HEVAG (In Development) 🔧

| Property | Value |
|----------|-------|
| Codec | 9 (HEVAG) |
| Compression | ~10:1 (fits full song in 12MB) |

HEVAG ADPCM encoder works structurally but produces incorrect decoded output. Being investigated.

## Pipeline Options

```
usage: full_custom_song_pipeline.py [-h] --song-dir SONG_DIR [--audio AUDIO]
                                     [--pcm16] [--vorbis]
                                     [--target TARGET] [--output OUTPUT]
                                     [--deploy] [--target-ip TARGET_IP]
                                     [--no-pad] [--preserve-metadata]

Options:
  --song-dir SONG_DIR       Song directory with .wav/.ogg and .dat files
  --audio FSB5              Use pre-encoded FSB5 file (skip encoding)
  --pcm16                   Use PCM16 format (lossless, codec=2)
  --vorbis                  Use Vorbis format (experimental, codec=15)
  --target TARGET           Game bundle target (default: startmeup)
  --output OUTPUT           Save bundle locally (default: auto)
  --deploy                  Upload bundle to PS4 via FTP
  --target-ip TARGET_IP     PS4 IP address (default: 192.168.100.117)
  --no-pad                  Skip 12MB padding (may freeze on PS4)
  --preserve-metadata       Don't update AudioClip/audio.gz metadata
```

## Plugin Installation Details

### Required Files

| File | Purpose |
|------|---------|
| `beat_saber_deluxe.prx` | Full plugin (recommended) |
| `beat_saber_deluxe_minimal.prx` | Minimal build for testing |
| `plugins.ini` | GoldHEN plugin config |

### Plugin Installation Path

```
PS4 data partition:
/data/GoldHEN/
├── plugins/
│   └── beat_saber_deluxe.prx   <-- Copy here
├── config/
│   └── plugins.ini              <-- Add entry here
└── AFR/
    └── CUSA12878/
        └── startmeup_v3/        <-- Custom bundle target
```

### Coexist with Other Plugins

The plugin system is additive. Other plugins (RB4DX, etc.) are loaded from their own entries in `plugins.ini`. Beat Saber Deluxe only hooks file opens that match the `BeatmapLevelsData/<song_id>` pattern — it won't interfere with other plugins.

If RB4DX is installed, keep its entries in `plugins.ini` and simply add the Beat Saber Deluxe line:

```ini
# Existing RB4DX entry (keep)
RB4DX=/data/GoldHEN/plugins/RB4DX_PS4.sprx

# Beat Saber Deluxe entry (add)
beat_saber_deluxe=/data/GoldHEN/plugins/beat_saber_deluxe.prx
```

> **Note:** The target song used by the AFR path must NOT conflict between plugins. Beat Saber Deluxe uses `startmeup` (the first song in the base game), while RB4DX uses the game's full level data.

## Song ID Reference

The `--target` parameter specifies which game song to replace. Here are common targets for CUSA12878:

| Target | Song |
|--------|------|
| `startmeup` | Start Me Up (first song — default) |
| `angelties` | Angel Ties |
| `breezer` | Breezer |
| `escape` | Escape |
| `legend` | Legend |
| `lvlinsane` | Level Insane |
| `weareone` | We Are One |
| `gottagofast` | Gotta Go Fast |
| `mythbusters` | Mythbusters |
| `overdrive` | Overdrive |
| `paintitblack` | Paint It Black |
| `retro` | Retro |
| `signal` | Signal |

> Full list available in the game's `BeatmapLevelsData` directory.

## Troubleshooting

### "Audio stops early / level freezes"

The 12MB FSB5 resource limit is the constraint. PCM16 at 44100Hz stereo fits ~70 seconds. Solutions:
- Use shorter songs (under 70 seconds)
- The game freezes after audio ends because the AudioClip metadata expects full duration. Use `--preserve-metadata` to skip AudioClip updates, or update it manually.

### "Plugin not loading"

1. Verify `plugins.ini` syntax (no typos, path is correct)
2. Check PS4 GoldHEN version (v2.4b+ recommended)
3. The PRX must be on `data` partition, not `user`
4. Reboot PS4 after changes

### "Custom audio plays but I hear static"

This indicates a codec incompatibility. The PCM16 codec (`--pcm16`) is the most reliable. If you hear static with other codecs, use PCM16.

### "Can't connect to PS4 via FTP"

1. Enable FTP in GoldHEN settings (Settings → GoldHEN → FTP)
2. Default port is 1337; some FTP clients use port 2121
3. Ensure PS4 and PC are on the same network
4. Try `ping 192.168.100.117` to verify connectivity

### "Bundle doesn't load / game crashes on song select"

1. Verify the FSB5 file starts with `FSB5` magic bytes
2. Make sure the .resource size matches the expected size (12,305,632 bytes)
3. Run without `--no-pad` (padding is required for PS4)

## Architecture

```
                  ┌──────────────────┐
                  │  GoldHEN Plugin  │
                  │  (file redirect) │
                  └────────┬─────────┘
                           │ hooks: open()
                  ┌────────▼─────────┐
                  │  BeatmapLevels-  │
                  │  Data/startmeup  │
                  │     → /.afr/     │
                  └────────┬─────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
     ┌────────▼────────┐      ┌────────▼────────┐
     │  Audio (.resource) │      │  Beatmaps (.dat) │
     │  PCM16 FSB5       │      │  5 difficulties   │
     └───────────────────┘      └───────────────────┘
```

## Project Structure

```
beat_saber_deluxe/
├── beat_saber_deluxe.prx      # Plugin (release build)
├── beat_saber_deluxe_minimal.prx  # Plugin (minimal build)
├── README.md                  # This file
├── tools/
│   ├── full_custom_song_pipeline.py  # Main pipeline (use this!)
│   ├── hevag_encoder.py            # Audio encoder
│   ├── convert_song.py             # Song download/conversion
│   └── prepare_binary_patch.py     # Binary patch utility
├── custom_songs/               # Output directory
├── tests/                      # Test files
│   └── reference/
│       └── original_audio.fsb5 # Original game FSB5
├── src/                        # Plugin source
├── Makefile                    # Plugin build system
└── build.sh                    # Build script
```

## License and Credits

This project is for educational purposes. Beat Saber is © Beat Games. FMOD is © Firelight Technologies.

Built with ❤️ by the modding community.
