---
name: feature-flags
description: Managing feature flags for the Beat Saber Deluxe plugin.
metadata:
  type: architecture
---

# Feature Flags

The Beat Saber Deluxe plugin uses a `features.json` configuration file located in the AFR directory to control experimental features without requiring a plugin recompile.

## `features.json` Structure

```json
{
  "enable_custom_song_replacements": true,
  "enable_song_metadata_modification": false
}
```

## Flags

| Flag | Default (missing file) | Purpose |
|------|----------------------|---------|
| `enable_custom_song_replacements` | `false` | Gates all song redirects in `open_hook`. When OFF, no bundle redirects fire — game plays original songs. |
| `enable_song_metadata_modification` | `false` | Gates song metadata modification. **Reserved for future use** — defaults to OFF until a new approach is implemented. |

## Pipeline Integration

Use `--set-feature key=value` to set flags and deploy them to PS4:

```bash
# Disable custom songs (play originals without rebooting):
python3 tools/full_custom_song_pipeline.py --deploy-plugin --set-feature enable_custom_song_replacements=false

# Enable song metadata modification (when new approach is ready):
python3 tools/full_custom_song_pipeline.py --deploy-plugin --set-feature enable_song_metadata_modification=true

# Set multiple flags at once:
python3 tools/full_custom_song_pipeline.py --deploy-plugin \
  --set-feature enable_custom_song_replacements=true \
  --set-feature enable_song_metadata_modification=true
```

The pipeline writes `features.json` locally and uploads it to PS4 via FTP.

## Implementation Rules
1. **Defaults:** All flags MUST default to `false` if not present in the configuration file.
2. **Path:** `features.json` is located at `/data/GoldHEN/AFR/<TITLE_ID>/features.json`.
3. **Synchronization:** If a new feature flag is added, it must be added to the default `features.json` checked into the repository.
4. **Reloading:** Plugin reads this file at `module_start` (startup). Restart the game to apply configuration changes.

## Plugin Source
- `main.cpp`: Reads `features.json` via `load_features()`, stores in `g_feature_custom_song_replacements` and `g_feature_song_metadata_modification` globals
- Gates: `open_hook` redirect logic

## Removed Code (Historical)
- ~~Memory injection code~~ — Removed in v0.8025. The `enable_song_metadata_modification` flag is preserved for future use when a new approach is implemented.
