# Beat Saber Deluxe 🎵⚡

## What Do?

**Custom song replacement for PlayStation 4 Beat Saber (CUSA12878)**

Replace any Rolling Stones song's audio and beatmaps with custom community songs — no game modding required. Works via GoldHEN's file redirection hook.

> **⚠️ Current limitation:** The plugin's 13-song redirect table is hardcoded as a C array. Making it dynamic is on the [roadmap](.agent/roadmap.md) (M1.5). Hence why this is currently only for the Rolling Stones album for the moment.

## Status

🏆 **v0.53 ALPHA** — All 13 Rolling Stones slots replaced. Every song perfectly synchronized, both colors working.

### What Works

- ✅ Plugin hooks `open()` and redirects `BeatmapLevelsData/<song_id>` to custom bundles on PS4 data partition
- ✅ PCM16 FSB5 (codec=2) audio — lossless, any length (`--no-pad`)
- ✅ Beatmap replacement with V3 conversion (notes, bombs, walls, arcs, chains)
- ✅ BPM sync fixed — bpmData computed from beatmap's actual last note, not Info.dat BPM
- ✅ bpmEvents populated — game no longer falls back to BPM=60
- ✅ Note colors work — `c` field set for V3.3.0+ compatibility
- ✅ Debug/release plugin builds (`make` / `make DEBUG=1`)
- ✅ GoldHEN AFR logging (no jailbreak needed for write access)
- ✅ Pipeline auto-deploy to PS4 + idempotent `plugins.ini` management

### Known Issues

- HEVAG encoder produces garbage (lacks Sony's proprietary coefficient table)
- Vorbis FSB5 codec mismatch (libvorbis vs FMOD codebook incompatibility)
- 360-degree beatmaps unplayable on PS4 VR (single camera ~90-degree tracking arc)

## Prerequisites

| Item                    | Required | Notes                                               |
| ----------------------- | -------- | --------------------------------------------------- |
| PS4 with GoldHEN        | ✅       | v2.4b+ recommended                                  |
| FTP server on PS4       | ✅       | Enable in GoldHEN settings                          |
| Network connection      | ✅       | Between PC and PS4                                  |
| Beat Saber installed    | ✅       | CUSA12878 (patched), any region                     |
| OpenOrbis PS4 Toolchain | ✅       | For building the plugin PRX                         |
| Python 3.10+            | ✅       | With `pip install soundfile numpy pyfmodex UnityPy` |

## Quick Start

### 1. Deploy Everything to PS4

```bash
cd beat_saber_deluxe
./deploy_all.sh --debug
```

This builds the plugin with verbose logging, uploads it to PS4, uploads all 13 custom song bundles, and clears the PS4 log.

### 2. Build a Single Custom Song

```bash
python3 tools/full_custom_song_pipeline.py \
  --song-dir /path/to/song_directory \
  --target startmeup --pcm16 --no-pad \
  --convert-to-v3 \
  --output custom_songs/startmeup_custom_v3.bundle
```

### 3. Build and Deploy Directly

```bash
python3 tools/full_custom_song_pipeline.py \
  --song-dir ./custom_songs/espresso_prepped \
  --target startmeup --pcm16 --no-pad \
  --convert-to-v3 \
  --deploy --deploy-plugin --debug-logging
```

### 4. Download PS4 Logs

```bash
lftp -u anonymous, -p 2121 <PS4_IP> \
  -e "get /data/GoldHEN/AFR/CUSA12878/bs_log.txt -o bs_log.txt; quit"
```

## Plugin Build System

```bash
cd beat_saber_deluxe
make                    # Release build (no verbose PS4 logging)
make DEBUG=1            # Debug build (verbose per-file logging)
```

The plugin source is in `beat_saber_deluxe/src/main.cpp`. Version is defined by `PLUGIN_VERSION` macro.

## Pipeline

`beat_saber_deluxe/tools/full_custom_song_pipeline.py` is the main entry point.

Key flags:
| Flag | Purpose |
|------|---------|
| `--song-dir` | Directory with song audio + .dat beatmap files |
| `--target` | Rolling Stones slot name (e.g. startmeup, angry) |
| `--pcm16` | PCM16 FSB5 audio (lossless, best quality) |
| `--no-pad` | Don't extend audio — use when PCM16 exceeds resource size |
| `--convert-to-v3` | Auto-convert V2 beatmaps to V3.2.0 |
| `--deploy` | Upload bundle to PS4 via FTP after building |
| `--deploy-plugin` | Build plugin PRX and deploy to PS4 |
| `--debug-logging` | Build plugin with `DEBUG=1` (verbose PS4 logs) |

## Documentation

| Resource                 | Location                                                                                                                                                                                  |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 📚 **Knowledge Base**    | [`.agent/llm-wiki-knowledge-base/`](.agent/llm-wiki-knowledge-base/) — Technical docs (audio sync, beatmap format, plugin architecture). Visualizable in [Obsidian](https://obsidian.md). |
| 🗺️ **Roadmap**           | [`.agent/roadmap.md`](.agent/roadmap.md) — Current milestones and planned features                                                                                                        |
| 📋 **Song Replacements** | [`.agent/current-song-replacements-on-chris-ps4.md`](.agent/current-song-replacements-on-chris-ps4.md) — Current PS4 deployment state                                                     |
| 📖 **Sync Knowledge**    | [`.agent/llm-wiki-knowledge-base/beatmap-audio-sync.md`](.agent/llm-wiki-knowledge-base/beatmap-audio-sync.md) — All sync root causes and fixes                                           |
| 🧪 **Experiment Log**    | [`.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md`](.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md) — Full experiment/test history                                     |
| 📦 **Song Catalog**      | [`.agent/beat_saber_song_ids.json`](.agent/beat_saber_song_ids.json) — 306 official song IDs                                                                                              |
| 🔧 **Legacy Docs**       | [`beat_saber_deluxe/development/docs/`](beat_saber_deluxe/development/docs/) — Archived historical documentation and research                                                             |

## Project Structure

```
workspace/
├── README.md                 # This file
├── CLAUDE.md                 # AI agent guardrails
├── .agent/                   # Project configuration & knowledge base
│   ├── llm-wiki-knowledge-base/  # Technical knowledge (Obsidian vault)
│   ├── roadmap.md            # Development roadmap
│   └── current-song-replacements-on-chris-ps4.md
├── beat_saber_deluxe/        # Main project directory
│   ├── beat_saber_deluxe.prx # Plugin (release build)
│   ├── beat_saber_deluxe_debug.prx # Plugin (debug build)
│   ├── deploy_all.sh         # Deploy plugin + all 13 bundles to PS4
│   ├── tools/                # Pipeline tools
│   │   ├── full_custom_song_pipeline.py  # Main pipeline
│   │   ├── hevag_encoder.py              # Audio encoder
│   │   ├── lapped_audio.py               # Lapped audio detection
│   │   └── download_beatsaver_songs.py   # BeatSaver downloader
│   ├── development/          # Archived scripts & docs
│   │   ├── scripts/          # Old/unused scripts
│   │   └── docs/             # Historical documentation
│   ├── src/main.cpp          # Plugin source
│   └── Makefile              # Plugin build system
├── beat-saber-ps4-custom-songs/  # Song repository
│   └── songs_repo/           # Downloaded custom song files
└── ps4_dump/                 # Game dump (gitignored)
```

## How It Works

```
[Custom .wav] → FSB5 encoder → .resource replacement → PS4 deployment → Plays!
[Custom .dat] → Beatmap     → .beatmap.gz replacement  → PS4 deployment → Plays!

Plugin hooks open():
  BeatmapLevelsData/startmeup
    → /data/GoldHEN/AFR/CUSA12878/startmeup_v3  (custom bundle)
```

The plugin intercepts file open requests from Beat Saber and redirects them to custom AssetBundles stored on the PS4's data partition. The bundles contain:

- **Audio:** PCM16 FSB5 format, lossless quality
- **Beatmaps:** Up to 5 difficulties (Easy → Expert+) in V3 format
- **Metadata:** bpmData for audio→beat mapping, bpmEvents for note timing

## Version History

| Version | Date       | Highlights                                              |
| ------- | ---------- | ------------------------------------------------------- |
| v0.53   | 2026-07-10 | Note color fix (c field), full repo cleanup             |
| v0.52   | 2026-07-09 | bpmEvents/bpmData sync fix, V3 empty bpmEvents patch    |
| v0.51   | 2026-07-08 | 12-song redirect table, priority-based beatmap fallback |
| v0.50   | 2026-07-01 | Proof of concept, PCM16 FSB5 audio, plugin hook working |
