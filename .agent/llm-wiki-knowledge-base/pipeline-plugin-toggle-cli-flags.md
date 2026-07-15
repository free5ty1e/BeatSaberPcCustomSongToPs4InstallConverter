---
name: pipeline-plugin-toggle-cli-flags
description: "Pipeline --enable-plugin and --disable-plugin CLI flags for toggling the Beat Saber Deluxe plugin on PS4 without rebuilding or removing files"
metadata:
  type: reference
---

# Pipeline Plugin Toggle — --enable-plugin / --disable-plugin

## Overview

Experiment 128 added two CLI flags to `full_custom_song_pipeline.py` that let users enable/disable the Beat Saber Deluxe plugin on PS4 without recompiling, removing files, or editing plugins.ini manually.

```bash
python3 full_custom_song_pipeline.py --enable-plugin    # Enable plugin on PS4
python3 full_custom_song_pipeline.py --disable-plugin    # Disable plugin on PS4 (play original songs)
```

## How It Works

### --enable-plugin

1. Downloads the existing `plugins.ini` from `/data/GoldHEN/plugins.ini` via FTP
2. Parses sections into `[TITLE_ID] → [plugin_paths]` format
3. Ensures an uncommented entry for our `.prx` (e.g. `beat_saber_deluxe.prx`) exists under `[CUSA12878]`
4. If a commented version of the same entry exists, converts it to uncommented
5. Uploads the modified plugins.ini back to PS4

### --disable-plugin

1. Downloads the existing `plugins.ini` from `/data/GoldHEN/plugins.ini` via FTP
2. Parses sections into `[TITLE_ID] → [plugin_paths]` format
3. Finds any entries containing our `.prx` filename under `[CUSA12878]`
4. Prepends `#;` to those lines (commenting them out while preserving the path)
5. Uploads the modified plugins.ini back to PS4

### Key Details

- **Idempotent**: running enable/disable multiple times has no cumulative effect
- **Non-destructive**: preserves all other plugin entries in plugins.ini
- **Standalone**: works without `--song-dir` — no song processing happens
- **Plugin naming**: uses `beat_saber_deluxe.prx` (release) or `beat_saber_deluxe_debug.prx` (debug) depending on `--debug-logging`
- **Requires PS4 online**: FTP connection is mandatory; will timeout if PS4 is off

## Code Locations

| Component | File | Line Range |
|---|---|---|
| `enable_plugin()` | `tools/full_custom_song_pipeline.py` | ~1097-1208 |
| `disable_plugin()` | `tools/full_custom_song_pipeline.py` | ~1220-1320 |
| CLI flags (argparse) | `tools/full_custom_song_pipeline.py` | ~1751-1756 |
| Dispatch logic (main) | `tools/full_custom_song_pipeline.py` | ~1765-1774 |

## Use Cases

- **Switching between custom songs and originals**: Disable plugin to play unmodified Rolling Stones tracks, enable to test custom content
- **Quick toggle during testing**: No need to manually edit plugins.ini or delete files from PS4
- **Collaborative development**: Team member can disable plugin while another tests without file conflicts

## Known Limitations

- Does NOT build or deploy the .prx binary — that requires `--deploy-plugin`
- Does NOT delete the .prx from PS4 storage (just comments it out of plugins.ini)
- FTP connection must succeed; if PS4 is unreachable, the command will timeout (~30s)
- Game must be restarted or PS+Triangle pressed to reload plugin list after toggle

## Related

- [[ps4-file-system-redirects|PS4 File System & Redirects]] — GoldHEN AFR redirect system
- [[plugin-architecture|Plugin Architecture]] — PRX format and loading mechanism
- [[il2cpp-dump-mode-selector-hook|IL2CPP Dump Mode Selector Hook]] — previous IL2CPP hook attempts
