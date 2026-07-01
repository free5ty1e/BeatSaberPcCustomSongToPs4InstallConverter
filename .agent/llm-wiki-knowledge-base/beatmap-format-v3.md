---
name: beatmap-format-v3
description: "PS4 Beat Saber's V3 beatmap format: colorNotes + colorNotesData with deduplicated data arrays"
metadata:
  type: entity
---

# PS4 Beatmap Format (V3)

The PS4 version of Beat Saber uses **V3 format** for its beatmap data, which differs significantly from the V2 format used by BeatSaver custom songs.

## V3 Format Overview

V3 uses **deduplicated data arrays**. Note properties are stored in one array (`colorNotesData`), and notes in another array (`colorNotes`) reference data entries by index.

```
Top-level JSON:
{
  "version": "4.0.0",
  "colorNotes": [{"b": <beat, required>, "i": <data_index, default=0}],
  "colorNotesData": [{"x": <col>, "y": <row>, "c": <color>, "d": <direction>}],
  "obstacles": [{"b": <beat>, "i": <data_index>}],
  "obstaclesData": [{"d": <duration>, "w": <width>, "h": <height>}],
  "bombNotes": [...],
  "bombNotesData": [...],
  "chains": [...],
  "chainsData": [...],
  "arcs": [...],
  "arcsData": [...],
  "spawnRotations": [],
  "spawnRotationsData": []
}
```

## Notes: colorNotes + colorNotesData

### colorNotes Array
Each entry:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `b` | float | required | Beat time (e.g., 5.5) |
| `i` | int | 0 | Index into `colorNotesData` |

When `i` is omitted, it defaults to 0 (using `colorNotesData[0]`).

### colorNotesData Array
Each entry (only non-default fields are stored):
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `x` | int | 0 | Column position (0-3, left to right) |
| `y` | int | 0 | Row position (0-2, bottom to top) |
| `c` | int | 0 | Color (0=red, 1=blue) |
| `d` | int | 1 | Cut direction (1-8, same as V2) |

Default entry (index 0): `{"x": 1, "d": 1}` — red note at column 1, direction down-right.

### Example
```json
"colorNotes": [{"b": 5.5}, {"b": 7.0, "i": 1}, {"b": 9.5, "i": 2}],
"colorNotesData": [
    {"x": 1, "d": 1},           // data[0]: red at col 1, down-right
    {"x": 3, "y": 1, "c": 1, "d": 3}, // data[1]: blue at col 3, upper row, right
    {"x": 2, "c": 1, "d": 1}    // data[2]: blue at col 2, down-right
]
```
Note [0]: `b=5.5, i=0` → uses data[0] (red, col 1, down-right)
Note [1]: `b=7.0, i=1` → uses data[1] (blue, col 3, upper, right)
Note [2]: `b=9.5, i=2` → uses data[2] (blue, col 2, down-right)

## Obstacles: obstacles + obstaclesData

### obstacles Array
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `b` | float | required | Beat time |
| `i` | int | 0 | Index into `obstaclesData` |

### obstaclesData Array
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `d` | float | 1.0 | Duration in beats |
| `w` | int | 1 | Width in columns |
| `h` | int | 5 | Height in rows (5 = full height wall) |

## Other Arrays
- `bombNotes` + `bombNotesData`: Same structure as notes (type=3 bombs from V2)
- `chains` + `chainsData`: Chain notes with additional properties
- `arcs` + `arcsData`: Arc notes with additional properties
- `spawnRotations` + `spawnRotationsData`: Stage rotation events

## V2 vs V3 Key Differences

| Aspect | V2 (BeatSaver) | V3 (PS4) |
|--------|----------------|----------|
| Version field | `"_version": "2.0.0"` | `"version": "4.0.0"` (no underscore) |
| Notes format | `"_notes": [{"_time": t, "_lineIndex": x, "_lineLayer": y, "_type": c, "_cutDirection": d}]` | `colorNotes[n] + colorNotesData[n]` (deduplicated) |
| Properties | Inline in each note | In data arrays, referenced by index |
| Obstacles | `"_obstacles": [{"_time": t, "_duration": d, "_lineIndex": x, "_width": w, "_type": 0}]` | `obstacles[n] + obstaclesData[n]` |
| Events | `"_events": [...]` inline | Stored in separate lightshow data |
| Bomb type | `_type: 3` in `_notes` | Separate `bombNotes` array |
| Field naming | Underscore prefix (`_time`) | No underscore (`b`) |

See also: [[beatmap-conversion-pipeline]], [[assetbundle-structure]]
