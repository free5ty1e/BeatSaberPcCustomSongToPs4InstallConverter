---
name: procedural-mode-generators
description: "Pipeline-side procedural generators for OneSaber, NoArrows, and 90Degree mode beatmaps (v0.5310)"
metadata:
  type: reference
---

# Procedural Mode Generators

Pipeline v0.5310 replaces the v0.5309 placeholder generators with full, **non-mutating**
implementations that fill in missing per-mode `.dat` beatmap files for custom songs.
They run automatically in **Step 5a (before `replace_beatmaps`)** whenever
`--enable-beatmap-mode-mapping` is passed. This is the **default** fill-in behavior —
a song that ships its own `<Diff><Mode>.dat` files is never overwritten.

## Design Rules

- **Non-mutating:** every generator deep-copies its input before modifying, so the
  Standard source map is never corrupted (a unit test caught the original NoArrows
  mutation bug in v0.5309).
- **Source selection:** `generate_missing_mode_beatmaps` uses
  `_select_beatmap_file(..., ignore_non_standard=True)` — only Standard maps are
  valid sources. Difficulties without a Standard source are skipped.
- **Never overwrite:** the `detected_modes` dict captured BEFORE generation is the
  pre-generation state; a song's own mode files are left untouched.

## Generator Details

### `_generate_no_arrows`
Converts every color note to a dot:
- V2: `_cutDirection = 8`
- V3: `d = 8`
Bombs keep their direction (they aren't cut). Only `_type` 0/1 color notes change.

### `_generate_one_saber`
Recolors every color note to the single saber color. **OneSaber is played
exclusively with the RIGHT (blue) saber** (see [[saber-colors-and-one-saber]]),
so the forced color is RIGHT/BLUE, never red:
- V2: `_type = 1`
- V3: `c = 1` / `a = 1`
The constant `_ONE_SABER_COLOR = 1` (it was `0`/red before v0.5323 — that bug
made generated OneSaber maps unplayable because red notes cannot be hit by the
right saber).
Then removes notes a single saber cannot hit:
- **Simultaneous notes** (same beat) — only the first survives.
- **Same-cell arrowed notes closer than `min_gap` beats** (default 0.25) — later
  note removed; dots after arrows are kept (a dot has no forced direction).
CLI: `--one-saber-min-gap` (default `_ONE_SABER_MIN_GAP = 0.25`).

### `_generate_90_degree`
- V2 sources are first converted to V3 via `convert_v2_to_v3` (bpm carried into
  `bpmEvents`); V3 input passes through unchanged.
- Adds `rotationEvents` alternating `{"b": beat, "e": 0, "r": ±90}` every
  `cycle_beats` from the first note through the last beat — the lane swings back
  and forth (90° → -90° → ...), never a full rotation.
CLI: `--rotation-cycle-beats` (default `_ROTATION_CYCLE_BEATS = 8.0` = 2 measures).

## Wiring

- `_MODE_GENERATORS` dict maps mode name → generator callable.
- `generate_missing_mode_beatmaps(song_dir, detected_modes, enabled_modes, bpm,
  min_gap, cycle_beats)` writes `<Diff><Mode>.dat` files into the song dir.
- Runs in Step 5a BEFORE `replace_beatmaps` so generated files reach the bundle.
- Opt-out flag: `--skip-mode-generation` (mapping still applies).
- Step 6a uses `mode_map_enabled_modes`.

## Verified Output (Exp 177, `drop pop candy`)

14 files generated (Easy–ExpertPlus × OneSaber/NoArrows/90Degree) except
`Expert90Degree.dat`, which the song already provides. OneSaber maps fully
recolored to RIGHT/BLUE, NoArrows maps all dots, 90Degree maps V3 with alternating rotations.
`detect_song_modes` correctly saw pre-generation state: `90Degree: ['Expert']`.

## Selector visibility (pack preview sets)

The generated per-song mode sets land in the per-song bundle, but the in-game
**mode selector reads pack-level `BeatmapLevelSO._previewDifficultyBeatmapSets`**.
That preview-set injection is performed by the production pack builder
`tools/build_pack_mode_bundles.py` (raw-blob surgery on the BeatmapLevelSO, since
UnityPy returns `UnknownObject` for it) — NOT by UnityPy. The remaining gap is
not "showing the button" but **pointing the OneSaber button at the per-song
bundle's blue OneSaber beatmap** (see [[saber-colors-and-one-saber]] — the pack
must reference the song data's beatmap, not clone Standard's). See
[[architecture|Architecture]] for the song-data vs song-pack distinction.

## Related

- [[pipeline-song-metadata-blob-injection|BeatmapLevelSO Blob Injection]] — preview-set injection blocker
- [[beatmap-format-v3|PS4 Beatmap Format (V3)]] — field names (`c` vs `a`, `d`, rotationEvents)
- [[beatmap-conversion-pipeline|Beatmap Conversion Pipeline]] — V2→V3 conversion (`convert_v2_to_v3`)
- [[saber-colors-and-one-saber|Saber Colors & OneSaber Convention]] — LEFT=Red, RIGHT=Blue; OneSaber is RIGHT/blue only
- `beat_saber_deluxe/docs/features/beatmap-mode-mapping.md` — full feature documentation
