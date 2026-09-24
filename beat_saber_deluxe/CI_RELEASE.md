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
- `pip install UnityPy` (see `requirements-test.txt`)
- A PS4 with GoldHEN, FTP enabled (port 2121), configured in `ps4_config.json`

**Quick Start — one command per song (recommended):**

```bash
# Download from BeatSaver, convert, and deploy song + its music pack + plugin +
# feature flags + redirects + catalog, then self-validate — all in ONE command:
python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song <MAP_ID> \
    --target <SLOT_NAME> \
    --deploy-full
```

Each `--deploy-full` is self-contained: it builds and deploys the latest plugin,
deploys only that song's bundle, surgically patches that song's music pack (with
a matching Addressables catalog so the pack passes Unity's CRC check), regenerates
`redirects.json` scoped to exactly what is deployed (existing custom songs in
other packs are preserved), and runs post-deploy validation. **A failed validation
aborts the deploy with a non-zero exit** — the game never boots into a broken
state silently.

Useful variants:

```bash
# Temporarily play only OFFICIAL songs (kill switch — no uninstall, next boot):
python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_plugin=false
# ...and back to custom songs:
python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_plugin=true

# Skip building/deploying the plugin (pin a specific plugin build on the PS4):
python3 tools/full_custom_song_pipeline.py ... --deploy-full --skip-plugin-deployment

# Revert a single song slot to stock without a full clean slate:
python3 tools/full_custom_song_pipeline.py --clear-target-song <SLOT_NAME>
```

See the main `README.md` for full pipeline documentation.

## Runtime Feature Flags (`features.json`)

| Flag | Default | Purpose |
|------|---------|---------|
| `enable_plugin` | `true` (when absent) | Global kill switch — `false` = fully inert plugin, 100% official songs on next boot |
| `enable_custom_song_replacements` | `false` | Gates all bundle redirects |
| `enable_song_metadata_modification` | `false` | Gates song name/artist swaps in the UI |
| `enable_beatmap_mode_mapping` | `false` | Gates extra game modes (OneSaber/NoArrows/90Degree) — OFF serves stock pack bundles + catalog |

On boot the plugin shows one combined toast with its state:
`BS Deluxe vX (ON) / By Chris Primeish / (3/3 features ON)` — or
`BS Deluxe vX (OFF) / By Chris Primeish / (official songs only)`.

## Plugin Installation

1. Copy `beat_saber_deluxe.prx` to `/data/GoldHEN/plugins/` on your PS4
2. Copy `features.json` to `/data/GoldHEN/AFR/CUSA12878/features.json`
3. Add `/data/GoldHEN/plugins/beat_saber_deluxe.prx` under `[CUSA12878]` in `/data/GoldHEN/plugins.ini`
4. Deploy songs with the pipeline (it manages `redirects.json` for you — the
   bundled copy is an empty template)
5. Launch Beat Saber — the boot toast confirms the plugin state
<!-- END_PROTECTED -->
