# Feature: Beatmap Mode Mapping

Auto-detect custom song beatmap files and map them to the game's 5 characteristic
mode slots (Standard, OneSaber, NoArrows, 90Degree, 360Degree) with configurable
fallback logic for slots without dedicated files.

## Requirements

1. **Feature flag enabled** — `enable_beatmap_mode_mapping` must be `true` in `/data/GoldHEN/AFR/CUSA12878/features.json` (default: `true`)
2. **Pipeline v0.5307+** — CLI flags `--enable-beatmap-mode-mapping` and `--fallback-mode-map`

## How It Works

### Phase 1 (Pipeline-side, v0.5307)

The pipeline performs three steps when `--enable-beatmap-mode-mapping` is passed:

1. **`detect_song_modes(song_dir)`**
   Scans all `.dat` and `.json` files in the song directory, classifies them by
   mode using filename patterns:

   | Pattern | Example | Mode Detected |
   |---------|---------|---------------|
   | Bare difficulty | `Expert.dat` | Standard |
   | Standard suffix | `ExpertPlusStandard.dat` | Standard |
   | Mode suffix | `ExpertPlusOneSaber.dat` | OneSaber |
   | Mode prefix | `OneSaberExpert.dat` | OneSaber |
   | Beatmap dot | `ExpertPlus.beatmap.dat` | Standard |
   | Legacy | `EasyLegacy.dat` | Standard (alias) |
   | SingleSaber | `ExpertSingleSaber.dat` | OneSaber (alias) |
   | Lawless | `ExpertLawless.dat` | NoArrows (alias) |

2. **`build_mode_mapping(detected_modes, fallback_map)`**
   Resolves the 5 game characteristic slots against the detected modes.
   Default fallback chain (each mode falls back to the next if not detected):

   ```
   360Degree → NoArrows → Standard
   90Degree → Standard
   NoArrows → Standard
   OneSaber → Standard
   Standard (always present)
   ```

   Custom fallbacks override defaults: `--fallback-mode-map 360Degree=Standard`
   skips the `NoArrows` fallback for 360Degree.

3. **`apply_mode_mapping(cab, enabled_modes)`**
   Injects new `_difficultyBeatmapSets` entries into the per-song bundle's
   `BeatmapLevel` object by cloning Standard's beatmap asset references.
   Each enabled mode gets its own entry in the array.

### Mode Slot Ordering

The 5 game characteristic slots are always processed in this order:

```python
GAME_CHARACTERISTIC_MODES = [
    "Standard", "OneSaber", "NoArrows", "90Degree", "360Degree"
]
```

### CLI Examples

```bash
# Auto-detect modes with default fallback chain:
python3 full_custom_song_pipeline.py \
  --song-dir ./my_song \
  --target startmeup \
  --enable-beatmap-mode-mapping

# Custom fallback: 360Degree falls to Standard directly (skip NoArrows):
python3 full_custom_song_pipeline.py \
  --song-dir ./my_song \
  --target startmeup \
  --enable-beatmap-mode-mapping \
  --fallback-mode-map 360Degree=Standard

# Multiple custom fallbacks:
python3 full_custom_song_pipeline.py \
  --song-dir ./my_song \
  --target startmeup \
  --enable-beatmap-mode-mapping \
  --fallback-mode-map NoArrows=Standard \
  --fallback-mode-map 360Degree=90Degree
```

## Relationship to `--enable-modes`

| Flag | Behavior |
|------|----------|
| `--enable-modes` | Manually specify which modes to add (e.g. `OneSaber,90Degree`). All use cloned Standard beatmaps. |
| `--enable-beatmap-mode-mapping` | Auto-detect modes from files. Falls back through chain for undetected modes. May be combined with `--enable-modes` for explicit additions. |

When both are present, `--enable-beatmap-mode-mapping` runs after `--enable-modes`
and adds any modes it detects that weren't manually enabled.

## Known Limitations

- **Phase 1 only injects mode sets in the per-song bundle** (`_difficultyBeatmapSets`).
  The pack bundle's `_previewDifficultyBeatmapSets` (in BeatmapLevelSO) is not
  modified — that requires Phase 2 (plugin runtime injection).
- **All modes use Standard's beatmap assets** in Phase 1. Per-mode unique beatmaps
  (e.g. actual OneSaber `.dat` content mapped to OneSaber mode) requires Phase 2.
- **The 360Degree→NoArrows fallback** is the default because NoArrows gameplay is
  closer to 360Degree than Standard is (both use modified note mechanics).

## Testing

```bash
# Unit tests for detect/build/map functions:
python3 -m pytest tests/test_pipeline.py -v -k "TestDetectSongModes or TestBuildModeMapping"

# Integration tests (detect→build chain):
python3 -m pytest tests/test_integration.py -v -k "TestBeatmapModeMappingIntegration"

# Full suite:
python3 -m pytest tests/
```
