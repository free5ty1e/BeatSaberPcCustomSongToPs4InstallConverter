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
  "enable_song_metadata_modification": false
}
```

## Implementation Rules
1. **Defaults:** All flags MUST default to `false` if not present in the configuration file.
2. **Path:** `features.json` is located at `/data/GoldHEN/AFR/<TITLE_ID>/features.json`.
3. **Synchronization:** If a new feature flag is added, it must be added to the default `features.json` checked into the repository.
4. **Reloading:** Plugin reads this file at `module_start` (startup). Restart the game to apply configuration changes.
