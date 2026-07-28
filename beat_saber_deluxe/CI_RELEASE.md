<!-- START_PROTECTED -->

# CI/CD Release Instructions

This document describes the CI/CD pipeline for Beat Saber Deluxe and serves as the release body reference. The release workflow is defined in `.github/workflows/plugin-build.yml`.

## Artifacts Per Release

### 📦 Plugin

| File                          | Description                                                        |
| ----------------------------- | ------------------------------------------------------------------ |
| `beat_saber_deluxe.prx`       | Release build — no verbose logging, minimal file size              |
| `beat_saber_deluxe_debug.prx` | Debug build — verbose ps4 logging (`bs_log.txt`), larger file size |
| `plugins.ini`                 | GoldHEN configuration for CUSA12878                                |
| `redirects.json`              | Song redirect config                                               |

### 🎵 Song Conversion Pipeline

| File                                 | Description                                      |
| ------------------------------------ | ------------------------------------------------ |
| `tools/full_custom_song_pipeline.py` | Main pipeline script for converting custom songs |
| `tools/*.py`                         | Supporting tools (downloader, audio encoder)     |
| `VERSION`                            | Pipeline version                                 |

## Running the Pipeline

**Prerequisites:**

- Python 3.8+
- `pip install UnityPy`
- .NET SDK (for Il2CppDumper, if regenerating class dump)
- `vgmstream-cli` (for audio preview generation)

**Quick Start:**

```bash
# Convert a custom song to replace "startmeup"
python3 tools/full_custom_song_pipeline.py \
    --song-dir ./my_custom_song \
    --target startmeup \
    --download-beat-saver-song myChosenSongId \
    --song-name "Song Name" \
    --artist "Artist Name" \
    --generate-config \
    --deploy-config \
    --deploy
```

See the main `README.md` for full pipeline documentation.

## Plugin Installation

1. Copy `beat_saber_deluxe.prx` to `/data/GoldHEN/plugins/` on your PS4
2. Copy `redirects.json` to `/data/GoldHEN/AFR/CUSA12878/redirects.json` (edit to customize)
3. Copy `plugins.ini` to `/data/GoldHEN/plugins.ini` (merge with existing entries)
4. Launch Beat Saber — notification confirms plugin loaded
<!-- END_PROTECTED -->
