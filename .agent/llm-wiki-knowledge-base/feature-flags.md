---
name: feature-flags
description: Managing feature flags for the Beat Saber Deluxe plugin.
metadata:
  type: architecture
---

# Feature Flags

The Beat Saber Deluxe plugin uses a `features.json` configuration file located in the AFR directory to control experimental features without requiring a plugin recompile.

## `features.json` Structure

Since v0.5334, `features.json` holds the runtime flags the plugin reads at startup (via `load_features()` in `main.cpp`). Current shape (v0.8043 plugin / v0.5339 pipeline):

```json
{
  "enable_plugin": true,
  "enable_custom_song_replacements": true,
  "enable_song_metadata_modification": true,
  "enable_beatmap_mode_mapping": true,
  "enable_song_previews": true,
  "enable_in_game_plugin_toggle": false,
  "enable_game_data_extractor": false
}
```

**v0.5314–v0.5333:** `enable_beatmap_mode_mapping` was absent (mode mapping was build-time only).
**Since v0.5334:** `enable_beatmap_mode_mapping` is a **runtime feature flag** that gates the visibility of extra mode sets (OneSaber, NoArrows, 90Degree) in pack bundles. This enables partial pack deployments where only some songs are custom — stock songs won't show extra mode buttons, preventing crashes.

## Flags

| Flag | Default (missing file — Exp 281: ALL ON for fresh installs) | Purpose |
|------|----------------------|---------|
| `enable_plugin` | **`true`** (unique) | **Global kill switch (v0.8043+).** When explicitly `false`, the plugin is fully inert: no redirects fire AND all metadata hooks return stock values — the game plays 100% official content on next boot. Fresh-install defaults (Exp 281, user directive): ALL flags default TRUE when the file is absent — the flag list IS the product's feature set. Pipeline: `python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_plugin=false` to play official songs, `...=true` to restore customs. No plugins.ini edit, no PS4 clean. |
| `enable_custom_song_replacements` | **`true`** | Gates all song redirects in `open_hook`. When OFF, no bundle redirects fire — game plays original songs. |
| `enable_song_metadata_modification` | **`true`** | Gates song name/artist metadata replacement (MoveNext hook + `song_metadata.json` + TMP_Text replacement). ON in production. |
| `enable_beatmap_mode_mapping` | **`true`** | **Really gates since plugin v0.8046** (was decorative v0.5334–v0.8045): when OFF, the open-hook redirect loop skips `pack_assets` bundle redirects AND the `catalog` redirect — the game loads STOCK pack bundles, so every song shows only Standard mode; per-song custom bundles still redirect (custom audio + Standard beatmaps keep working). The catalog must be skipped with the packs: the patched catalog's m_Crc/m_BundleSize describe the PATCHED bundles, and serving it against stock bundles fails Unity's CRC check and crashes the pack scan ([[addressables-catalog-crc-validation]]). When ON, patched packs show all 4 mode sets. |
| `enable_song_previews` | **`true`** | **M10 (plugin v0.8048 / pipeline v0.5357):** gates the custom-song SONG PREVIEWS ([[song-previews]]) — highlighting a custom song in the menu plays its own ~10s audio instead of the stock clip. The preview AudioClips ride INSIDE the patched pack bundles, so this flag shares the mode-mapping gate: the patched pack+catalog pair is served when EITHER flag is ON (both OFF → stock bundles + origin catalog). The pipeline derives the bundle VARIANT (modes+previews vs modes-only) from the flag state at deploy time — redirects carry the variant filename as their VALUE. |
| `enable_game_data_extractor` | **`true`** | **M12 (plugin v0.8054 / pipeline v0.5364):** arms the **in-console game-data extractor** — the plugin copies the files the pipeline needs (per-slot templates, pack bundles, catalog) out of the game's own mounts during a normal boot; `--pull-game-data` mirrors them into the local `game_data/` cache (a drop-in for `ps4_dump/`). Console-maintenance tooling like the M11 hotkey: NOT gated by the kill switch. Idempotent (ERR lines retry next boot). |
| `enable_in_game_plugin_toggle` | **`true`** | **M11 (plugin v0.8049/v0.8050 / pipeline v0.5363):** arms the **Move-button + trigger 2-second hotkey** that flips `enable_plugin` inside features.json ([[in-game-plugin-toggle]] / [[ps4-controller-input-from-plugin]]). Persist-only: the flip applies at the NEXT boot (notification says "restart game to apply"); the current session never changes mid-game. **Deliberately NOT gated by the kill switch** — the hotkey must keep working when the plugin is toggled OFF, or a user could never re-enable without a PC (one-way-door prevention). Only this flag disables the hotkey. |

## Startup Notification (plugin v0.8045+)

On boot the plugin sends **one combined toast** — version + kill-switch state + flag count:

- Kill switch ON: `BS Deluxe v0.8045 (ON)` / `By Chris Primeish` / `(3/3 features ON)`
- Kill switch OFF: `BS Deluxe v0.8045 (OFF)` / `By Chris Primeish` / `(official songs only)`

Single toast by design (Exp 221): the PS4VR headset switch-over swallows a second
notification when the headset is already powered on at launch — the v0.8044
two-toast format was unreliable in exactly the common case.

**Deploy invariant (v0.5340+):** every pipeline deploy merges missing keys from
`DEFAULT_FEATURES` into the local features.json before upload — a stale file
written before a flag existed can never ship with that flag silently absent
(root cause of the user's "2/3 feature flags ON" report).

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

# Disable mode mapping UI (partial pack deploy safety):
python3 tools/full_custom_song_pipeline.py --deploy-plugin --set-feature enable_beatmap_mode_mapping=false
```

## Implementation Rules
1. **Defaults:** All flags MUST default to `false` if not present in the configuration file (`DEFAULT_FEATURES` dict in `full_custom_song_pipeline.py`, plugin reads `features.json` at `module_start`).
2. **Path:** `features.json` is located at `/data/GoldHEN/AFR/<TITLE_ID>/features.json`.
3. **Synchronization:** If a new runtime feature flag is added, it must be added to the default `features.json` checked into the repository AND `DEFAULT_FEATURES` in the pipeline. Build-time pipeline features belong in CLI flags, NOT `features.json`.
4. **Reloading:** Plugin reads this file at `module_start` (startup). Restart the game to apply configuration changes.

## Plugin Source
- `main.cpp`: Reads `features.json` via `load_features()`, stores in `g_feature_custom_song_replacements`, `g_feature_song_metadata_modification`, `g_feature_beatmap_mode_mapping` globals
- Gates: `open_hook` redirect logic, MoveNext metadata replacement, pack bundle mode set visibility

## See Also
- [[procedural-mode-generators]] — the build-time mode generators baked into bundles by default
- [[pipeline-plugin-toggle-cli-flags]] — CLI flag architecture
- [[pipeline-afr-base-fix-clean-slate]] — AFR base path fix and clean slate workflow