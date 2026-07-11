# Beat Saber Deluxe — Pipeline & Plugin

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
```

### Pipeline Flags

| Flag | Purpose |
|------|---------|
| `--song-dir` | Directory with song audio + beatmap .dat files |
| `--target` | Rolling Stones slot (startmeup, angry, etc.) |
| `--pcm16` | PCM16 FSB5 audio (lossless) |
| `--no-pad` | Don't extend audio (use when PCM16 > original resource size) |
| `--convert-to-v3` | Auto-convert V2 beatmaps to V3.2.0 |
| `--deploy` | Upload bundle to PS4 via FTP |
| `--deploy-plugin` | Build + deploy plugin PRX |
| `--debug-logging` | Verbose PS4 logging (DEBUG=1 build) |

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

Deploys plugin + all 13 custom song bundles to PS4. Also clears PS4 log.

## Documentation

- **[Main README](../README.md)** — Full project docs, knowledge base links, roadmap
- **[Knowledge Base](../.agent/llm-wiki-knowledge-base/)** — Technical details (audio, beatmaps, plugin, PS4 env)
- **[Song Replacements](../.agent/current-song-replacements-on-chris-ps4.md)** — Current PS4 deployment state
- **[Legacy Scripts](development/scripts/)** — Archived old pipeline scripts
- **[Historical Docs](development/docs/)** — Archived research and PKG-method documentation
