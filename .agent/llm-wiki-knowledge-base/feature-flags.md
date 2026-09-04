---
name: feature-flags
description: Managing feature flags for the Beat Saber Deluxe plugin.
metadata:
  type: architecture
---

# Feature Flags

The Beat Saber Deluxe plugin uses a `features.json` configuration file located in the AFR directory to control experimental features without requiring a plugin recompile.

## `features.json` Structure

Since v0.5314, `features.json` holds EXACTLY the runtime flags the v0.8040 plugin reads at startup (via `load_features()` in `main.cpp`):

```json
{
  "enable_custom_song_replacements": true,
  "enable_song_metadata_modification": true
}
```

`enable_beatmap_mode_mapping` was **REMOVED** from `features.json` / `DEFAULT_FEATURES` in v0.5314: the v0.8040 plugin never parsed it. Mode mapping is a **build-time pipeline feature** (baked into the bundle at build time), toggled by the pipeline CLI flags below — not a runtime plugin toggle. Keeping it in `features.json` implied a runtime knob that didn't exist.

## Flags

| Flag | Default (missing file) | Purpose |
|------|----------------------|---------|
| `enable_custom_song_replacements` | `false` | Gates all song redirects in `open_hook`. When OFF, no bundle redirects fire — game plays original songs. |
| `enable_song_metadata_modification` | `false` | Gates song name/artist metadata replacement (MoveNext hook + `song_metadata.json` + TMP_Text replacement). ON in production. |

## Build-Time Defaults (pipeline v0.5314+, all DEFAULT ON)

The pipeline's standard command bakes in behavior that previously required explicit flags. Each default has an **oppose flag** to opt out:

| Default behavior | Oppose flag |
|------------------|-------------|
| PCM16 audio codec (lossless) | `--hevag` / `--vorbis` |
| No FSB5 padding (full-length audio) | `--pad-fsb5` (**DANGER**: truncates to 12MB → partial songs) |
| Beatmap mode mapping ON | `--disable-beatmap-mode-mapping` (Standard-only bundle); `--skip-mode-generation` keeps mapping but skips gap-filling |
| V2→V3 conversion ON | `--no-convert-to-v3` |

Resolution lives in pure, testable helpers: `resolve_audio_codec()`, `resolve_pad_to_size()`, `resolve_mode_mapping()`, `resolve_convert_to_v3()`; constants `DEFAULT_AUDIO_CODEC='pcm16'`, `DEFAULT_PAD_TO_SIZE=0`, `DEFAULT_MODE_MAPPING=True`, `DEFAULT_CONVERT_TO_V3=True`.

## Standalone `--features-only` Mode

Since v0.5314, feature flags can be applied + deployed WITHOUT any song/plugin/redirect processing:

```bash
python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_custom_song_replacements=false
```

- Requires at least one `--set-feature key=value` (errors with `--features-only requires at least one --set-feature key=value`, exit 1).
- Writes `features.json` locally and uploads to PS4 via FTP, then exits 0.
- This is the correct way to toggle runtime flags between game launches.

## Pipeline Integration

The legacy `--set-feature` usage via `--deploy-plugin` still works (sets flags as a step of a full plugin deploy):

```bash
# Disable custom songs (play originals without rebooting):
python3 tools/full_custom_song_pipeline.py --deploy-plugin --set-feature enable_custom_song_replacements=false
```

## Implementation Rules
1. **Defaults:** All flags MUST default to `false` if not present in the configuration file (`DEFAULT_FEATURES` dict in `full_custom_song_pipeline.py`, plugin reads `features.json` at `module_start`).
2. **Path:** `features.json` is located at `/data/GoldHEN/AFR/<TITLE_ID>/features.json`.
3. **Synchronization:** If a new runtime feature flag is added, it must be added to the default `features.json` checked into the repository AND `DEFAULT_FEATURES` in the pipeline. Build-time pipeline features belong in CLI flags, NOT `features.json`.
4. **Reloading:** Plugin reads this file at `module_start` (startup). Restart the game to apply configuration changes.

## Plugin Source
- `main.cpp`: Reads `features.json` via `load_features()`, stores in `g_feature_custom_song_replacements`, `g_feature_song_metadata_modification` globals
- Gates: `open_hook` redirect logic, MoveNext metadata replacement

## See Also
- [[procedural-mode-generators]] — the build-time mode generators baked into bundles by default
- [[pipeline-plugin-toggle-cli-flags]] — CLI flag architecture
