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

## Beatmap Mode Control — CAUTION: EARLY STAGE (v0.57 experimental)

**NOTE:** This feature is currently experimental. Adding `_difficultyBeatmapSets` entries to the per-song bundle is only **half** of the solution — the in-game UI also requires modifying `_previewDifficultyBeatmapSets` in the `BeatmapLevelSO` (stored in the Addressables pack bundle, not the per-song bundle). See Experiment 111 for details.

### How It Works (Pipeline Side)

The pipeline's `add_mode_characteristics()` function finds the `BeatmapLevel` object (class_id 114) in the bundle's CAB and reads its TypeTree. It clones the existing `"Standard"` entries in the `_difficultyBeatmapSets` array, creating new entries for each requested characteristic:

```json
"_difficultyBeatmapSets": [
    {"_beatmapCharacteristicSerializedName": "Standard", ...},  // original, 5 diffs
    {"_beatmapCharacteristicSerializedName": "OneSaber", ...},  // cloned, same beatmap refs
    {"_beatmapCharacteristicSerializedName": "90Degree", ...}   // cloned, same beatmap refs
]
```

Each cloned entry references the **same** `.beatmap.gz` and `.lightshow.gz` assets as the Standard characteristic (same path IDs). The game's engine applies the mode modifier (one saber, 90-degree rotation) to the Standard notes at runtime.

### UI Reality (After Investigation)

The in-game mode selector is NOT controlled by the per-song bundle's `_difficultyBeatmapSets`. Instead:

| Data Source | Location | Controls |
|-------------|----------|----------|
| `_previewDifficultyBeatmapSets` | `BeatmapLevelSO` in Addressables pack bundle | What modes appear in the song selection UI |
| `_difficultyBeatmapSets` | `BeatmapLevel` in per-song bundle (`BeatmapLevelsData/{slot}`) | What beatmaps load when you select a mode |

**User UI description:** "I select a difficulty, and then the UI above the difficulty section shows the modes." The mode options appear as buttons/segments in a row above the difficulty list — NOT a dropdown.

**Known Beatmap Characteristic names:** `Standard`, `OneSaber`, `90Degree`, `NoArrows`, `OneColor`

### What's Required to Make Modes Visible

1. **Modify the `BeatmapLevelSO` in the pack bundle** — add `_previewDifficultyBeatmapSets` entries for each desired characteristic. Each entry needs a reference to a `BeatmapCharacteristicSO` object (located in an external CAB).
2. **Modify the per-song `BeatmapLevel` bundle** — add `_difficultyBeatmapSets` entries (done by `add_mode_characteristics()`).
3. **Deploy both bundles** to PS4 and use AFR to redirect the pack bundle load.
4. **Challenge:** The `BeatmapCharacteristicSO` references for OneSaber/90Degree are in an external CAB that couldn't be located. The current workaround uses the Standard BeatmapCharacteristicSO reference for all modes, which may show all modes as "Standard" in the UI.

### Utility Script

`development/scripts/modify_pack_bundle.py` — modifies the Addressables pack bundle to add `_previewDifficultyBeatmapSets` entries for a specific song. Usage:

```bash
python3 development/scripts/modify_pack_bundle.py
```

(Currently hardcoded for StartMeUp. Edit the script to target different songs.)

### CLI Flag

```bash
# Build a bundle with OneSaber and 90Degree characteristics
python3 tools/full_custom_song_pipeline.py \
  --song-dir <song_directory> \
  --target <slot_name> --pcm16 --no-pad \
  --convert-to-v3 --enable-modes OneSaber,90Degree \
  --deploy
```

### Verification

To verify a bundle has the new characteristics, the save+reload test confirms:
- Standard (5 diffs)
- OneSaber (5 diffs)
- 90Degree (5 diffs)

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
