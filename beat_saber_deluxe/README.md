# Beat Saber Deluxe 🎵⚡

**Custom song replacement for PlayStation 4 Beat Saber (CUSA12878)**

Replace any song's audio and beatmaps with your own content, all through a convenient pipeline — no game modding required. Works via GoldHEN's file redirection hook.

## Demo

✅ **Confirmed working:** PCM16 FSB5 (codec=2) custom audio plays on PS4. Custom beatmaps display and interact correctly. Tested with CUSA12878 patched (v1.29).

**Status:** 🏆 **v0.53 alpha** — 13-song redirect table (all Rolling Stones + Live By The Sword) + note color fix!

> **⚠️ Hardcoded Redirect Table:** The plugin currently has a hardcoded C array of 13 Rolling Stones song redirects. This is on the [roadmap](.agent/roadmap.md) (M1.5) to be made dynamic via JSON config.

## Documentation

Knowledge base and development docs are maintained alongside the code:

| Resource | Location | Description |
|----------|----------|-------------|
| 📚 **Knowledge Base** | [`.agent/llm-wiki-knowledge-base/`](.agent/llm-wiki-knowledge-base/) | Technical docs: audio sync, beatmap format, plugin architecture, PS4 environment |
| 🗺️ **Roadmap** | [`.agent/roadmap.md`](.agent/roadmap.md) | Current milestones and planned features |
| 📋 **Song Replacements** | [`.agent/current-song-replacements-on-chris-ps4.md`](.agent/current-song-replacements-on-chris-ps4.md) | Current PS4 deployment state |
| 📖 **Supported Songs** | [`.agent/llm-wiki-knowledge-base/supported-songs.md`](.agent/llm-wiki-knowledge-base/supported-songs.md) | Sync status and fix history |
| 🧪 **Experiment Log** | [`.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md`](.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md) | Full experiment/test history |
| 📦 **Song Catalog** | [`.agent/beat_saber_song_ids.json`](.agent/beat_saber_song_ids.json) | 306 official song IDs |
| 🔧 **Development** | [`development/`](development/) | Old scripts and historical docs (archived) |

The knowledge base can be visualized in **[Obsidian](https://obsidian.md)** — open the `.agent/llm-wiki-knowledge-base/` folder as a vault. The `index.md` file serves as the entry point.

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
| Max duration | No hard limit! With `--no-pad`, full song fits (tested: 146s, 25.8MB) |
| Pipeline flag | `--pcm16` |

PCM16 is the reliable format — it's simple, lossless, and the PS4's FMOD handles it natively.

> **Important:** When using PCM16 with `--no-pad`, the bundle size increases beyond the original 12MB. The pipeline updates the AudioClip metadata accordingly. A 146-second song produces a 25.8MB FSB5 (LZ4 bundle: 25.4MB), which deployed successfully on PS4.

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
                                     [--ignore-non-standard-beatmaps]
                                     [--config CONFIG]

Options:
  --song-dir SONG_DIR            Song directory with .wav/.ogg and .dat files
  --audio FSB5                   Use pre-encoded FSB5 file (skip encoding)
  --pcm16                        Use PCM16 format (lossless, codec=2)
  --vorbis                       Use Vorbis format (experimental, codec=15)
  --target TARGET                Game bundle target (default from config)
  --template TEMPLATE            Path to template bundle (default from config)
  --output OUTPUT                Save bundle locally (default from config)
  --deploy                       Upload bundle to PS4 via FTP
  --target-ip TARGET_IP          PS4 IP address (overrides config)
  --no-pad                       Skip padding FSB5 to original resource size
  --preserve-metadata            Don't update AudioClip/audio.gz metadata
  --ignore-non-standard-beatmaps Only match "Standard" beatmaps (skip 360/90/OneSaber)
  --config CONFIG                Path to PS4 config JSON (default: ./ps4_config.json)
```

## PS4 Configuration

The pipeline uses a JSON config file (`ps4_config.json`) for PS4-specific settings. 
Create your own by copying the example:

```bash
cp ps4_config.example.json ps4_config.json
```

Then edit `ps4_config.json` with your PS4 details:

```json
{
    "ps4": {
        "ip": "192.168.100.117",
        "ftp_port": 2121,
        "ftp_user": "anonymous",
        "ftp_password": ""
    },
    "title": {
        "id": "CUSA12878",
        "patch_suffix": "-patch"
    },
    "paths": {
        "afr_base": "/data/GoldHEN/AFR",
        "afr_target_suffix": "_v3",
        "game_dump_dir": "/workspace/ps4_dump/CUSA12878-patch",
        "template_dir": "Media/StreamingAssets/BeatmapLevelsData",
        "output_dir": "/workspace/beat_saber_deluxe/custom_songs"
    },
    "pipeline": {
        "default_target": "startmeup",
        "sample_rate": 44100
    }
}
```

**Config is optional.** The pipeline works with CLI flags alone. If a config file
exists, its values are used as defaults, and CLI flags override them.

**`ps4_config.json` is gitignored** — your PS4 IP and paths are never committed.

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

## Targeting a Specific Song

### Do I need the decrypted game dump?

**Yes.** The pipeline works by **replacing the .resource** inside an existing game bundle. To do this, we need a copy of the bundle file from the game's decrypted PS4 dump.

You need:
1. **A decrypted dump of your Beat Saber game** (CUSA12878) — dumped from your own PS4 using a tool like FTP or a PS4 dumper payload
2. **The specific bundle file** for the song you want to replace, located at:
   ```
   Media/StreamingAssets/BeatmapLevelsData/<song_id>
   ```
   Example: `Media/StreamingAssets/BeatmapLevelsData/startmeup`

### How to get the game dump

The process:
1. Use GoldHEN's built-in FTP to browse the game's decrypted install directory:
   ```
   /mnt/sandbox/CUSA12878_<random>/app0/Media/StreamingAssets/BeatmapLevelsData/
   ```
   Or dump the game PKG to your PC and extract with a PS4 PKG tool
2. Copy the entire `BeatmapLevelsData` directory to your workspace
3. The pipeline defaults to looking for bundles at:
   ```
   /workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/<song_id>
   ```
   Configure this with `--template` if your dump is at a different location

### Finding the file size limit

The original game bundles have a **fixed resource size** baked into their header. This is the original audio file's size. When we replace it, **we can make it larger or smaller** — the bundle format supports variable resource sizes.

There is **no hard 12MB limit**. The 12MB figure was just the size of the original Start Me Up resource file. If your custom audio is larger:
- Use `--no-pad` to skip padding to the original size
- The pipeline updates the AudioClip metadata (`m_Resource.m_Size`) to match your new audio
- The bundle is saved with LZ4 compression

**Successful test:** A 25.8MB PCM16 FSB5 (146 seconds of stereo audio) was deployed and loaded correctly on PS4. Larger files work.

### Step-by-step: Targeting a new song

1. **Identify the song ID** from the game's `BeatmapLevelsData` directory. The directory contains files named by the song ID (e.g., `startmeup`, `breezer`, `angelties`). See the Song ID Reference table above.

2. **Copy the template bundle** to your workspace:
   ```bash
   cp /path/to/dump/Media/StreamingAssets/BeatmapLevelsData/<song_id> /workspace/beat_saber_deluxe/tests/reference/<song_id>
   ```

3. **Set up your song directory** with audio + beatmaps:
   ```
   songs/my_song/
   ├── song.wav
   ├── EasyStandard.dat
   ├── NormalStandard.dat
   ├── HardStandard.dat
   ├── ExpertStandard.dat
   └── ExpertPlusStandard.dat
   ```

4. **Run the pipeline** with the target:
   ```bash
   python3 /workspace/beat_saber_deluxe/tools/full_custom_song_pipeline.py \
     --song-dir /workspace/songs/my_song \
     --pcm16 \
     --target <song_id> \
     --deploy
   ```

5. **Play the song** in Beat Saber — select the original song from the menu. Your custom audio and beatmaps will play.

### Advanced: Custom paths

If your game dump is in a different location, you have two options:

**Option A: Use `--template` (per-command):**

```bash
python3 tools/full_custom_song_pipeline.py \
  --song-dir /workspace/songs/my_song \
  --pcm16 \
  --template /custom/path/BeatmapLevelsData/startmeup \
  --target startmeup \
  --deploy
```

**Option B: Edit `ps4_config.json` (persistent):**

```json
{
    "paths": {
        "game_dump_dir": "/custom/path/to/dump",
        "output_dir": "/custom/path/output"
    }
}
```

## Troubleshooting

### "Notes appear all one color (only red or only blue)"

**Fixed in v0.53.** The V2→V3 converter was only setting the `a` field for note color. The PS4 game's Beat Saber uses the `c` field (V3.3.0+ format) for note color, NOT `a`. Without the `c` field, all notes default to Red.

**Fix:** The converter now sets both `"a"` and `"c"` fields from the V2 `_type` value (0=Red, 1=Blue). Songs need to be rebuilt and redeployed after this pipeline change.

### "Audio stops early / level freezes"

**This should be fixed in the latest version.** The pipeline now:
- Builds a full-length PCM16 FSB5 with no clipping (use `--no-pad`)
- Updates AudioClip metadata (`m_Length`, `m_Frequency`, `m_Resource.m_Size`) to match your audio
- Updates audio.gz metadata with the correct sample count

If the audio still freezes after playing through, it may be a timing sync issue between the beatmaps and the audio. Try using beatmaps that match the song's length.

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
├── beat_saber_deluxe_debug.prx  # Plugin (debug build)
├── README.md                  # This file
├── ps4_config.example.json    # Example PS4 configuration
├── ps4_config.json            # Your PS4 configuration (gitignored)
├── deploy_all.sh              # Deploy plugin + all 13 bundles to PS4
├── tools/
│   ├── full_custom_song_pipeline.py  # Main pipeline (use this!)
│   ├── hevag_encoder.py            # Audio encoder (PCM16/HEVAG)
│   ├── lapped_audio.py             # Lapped audio detection/generation
│   └── download_beatsaver_songs.py # BeatSaver song downloader
├── development/
│   ├── scripts/               # Old/unused scripts (archived)
│   └── docs/                   # Historical documentation (archived)
├── custom_songs/               # Output directory (gitignored)
├── src/                        # Plugin source (main.cpp + Makefile)
└── Makefile                    # Plugin build system
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v0.53 | 2026-07-10 | **Note color fix (c field):** V2→V3 converter now sets `c` field (PS4 game uses `c` for color, not `a`). All songs rebuilt. |
| v0.52 | 2026-07-09 | **bpmEvents/bpmData sync fix:** Pipeline now populates bpmEvents with correct BPM (was empty → BPM=60 fallback). bpmData eb computed from beatmap's actual last note instead of Info.dat BPM. |
| v0.51 | 2026-07-08 | 12-song Rolling Stones redirect table. Priority-based beatmap fallback. |
| v0.50 | 2026-07-01 | Proof of concept. Plugin hook on `open()`. PCM16 FSB5 audio. |

## License and Credits

This project is for educational purposes. Beat Saber is © Beat Games. FMOD is © Firelight Technologies.

Built with ❤️ by the modding community.
