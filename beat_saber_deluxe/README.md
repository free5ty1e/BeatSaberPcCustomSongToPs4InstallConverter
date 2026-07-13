# Beat Saber Deluxe — Pipeline & Plugin (v0.57)

This is the core implementation directory for the **[Beat Saber Deluxe](../README.md)** project.

This document covers pipeline-specific details. See the **[main README](../README.md)** for project overview, requirements, and quick start.

## Pipeline

`tools/full_custom_song_pipeline.py` is the main entry point.

```bash
# Build a custom song bundle
python3 tools/full_custom_song_pipeline.py \
  --song-dir <song_directory> \
  --target <slot_name> --pcm16 --no-pad \
  --convert-to-v3 \
  --output custom_songs/<slot>_custom_v3.bundle

# Build + deploy to PS4
python3 tools/full_custom_song_pipeline.py \
  --song-dir <song_directory> \
  --target <slot_name> --pcm16 --no-pad \
  --convert-to-v3 --deploy --deploy-plugin --debug-logging

# Direct download from BeatSaver and deploy
python3 tools/full_custom_song_pipeline.py \
  --download-beat-saver-song <map_id> \
  --target <slot_name> --pcm16 --no-pad \
  --convert-to-v3 --deploy --deploy-plugin
```

### Pipeline Flags

| Flag | Purpose |
|------|---------|
| `--song-dir` | Directory with song audio + beatmap .dat files |
| `--download-beat-saver-song <id>` | Download map directly from BeatSaver using map ID |
| `--target` | Target slot (e.g. `startmeup`, `Oxytocin`, `2BeLoved`) |
| `--pcm16` | PCM16 FSB5 audio (lossless) |
| `--no-pad` | Don't extend audio (use when PCM16 > original resource size) |
| `--convert-to-v3` | Auto-convert V2 beatmaps to V3.2.0 |
| `--deploy` | Upload bundle to PS4 via FTP |
| `--deploy-plugin` | Build + deploy plugin PRX |
| `--debug-logging` | Verbose PS4 logging (DEBUG=1 build) |
| `--generate-config` | Update `redirects.json` config on PS4 |
| `--enable-modes` | Comma-separated list of extra beatmap modes to enable (e.g. `OneSaber,90Degree`). Clones Standard beatmaps into the new characteristics so they appear in the in-game mode selector. |

## Beatmap Mode Control

In addition to Standard mode, you can enable alternative beatmap characteristics (OneSaber, 90Degree, etc.) for your custom song bundles. The pipeline clones the Standard beatmap assets into entries for the requested characteristics so they appear in the in-game mode selector.

```bash
python3 tools/full_custom_song_pipeline.py \
  --song-dir <song_directory> \
  --target <slot_name> --pcm16 --no-pad \
  --convert-to-v3 --enable-modes OneSaber,90Degree \
  --deploy
```

This reuses the same beatmap notes as Standard mode. The game will automatically apply the mode modifier (e.g. one saber, 90-degree rotation) to the Standard notes. No separate mode-specific beatmap files are required.

## Dynamic Redirect Config

The plugin now uses a **dynamic redirect table** instead of hardcoded defaults. This allows adding new songs without recompiling the plugin.

- **Config Path:** `/data/GoldHEN/AFR/CUSA12878/redirects.json`
- **Format:** JSON mapping of `slot_id` → `bundle_filename`
- **Mechanism:** The plugin uses POSIX `open()` to read the config from the AFR path, ensuring compatibility with files uploaded via FTP.

## Plugin

GoldHEN PRX that hooks `open()` to redirect song file requests.

```bash
make           # Release build (no verbose logging)
make DEBUG=1   # Debug build (verbose per-file logging)
```

Version defined by `PLUGIN_VERSION` in `src/main.cpp`. Increment when plugin changes.

## Deploy All

```bash
./deploy_all.sh [--release|--debug]
```

Deploys plugin + all 32 custom song bundles (Rolling Stones, Billie Eilish, Lizzo) and `redirects.json` to PS4. Also clears PS4 log.

## Documentation

- **[Main README](../README.md)** — Full project docs, knowledge base links, roadmap
- **[Knowledge Base](../.agent/llm-wiki-knowledge-base/)** — Technical details (audio, beatmaps, plugin, PS4 env)
- **[Song Replacements](../.agent/current-song-replacements-on-chris-ps4.md)** — Current PS4 deployment state
- **[Legacy Scripts](development/scripts/)** — Archived old pipeline scripts
- **[Historical Docs](development/docs/)** — Archived research and PKG-method documentation
