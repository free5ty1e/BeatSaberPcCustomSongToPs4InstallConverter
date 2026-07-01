---
name: beatmap-conversion-pipeline
description: "End-to-end V2→V3 beatmap conversion: notes, obstacles, bombs, chains, arcs"
metadata:
  type: concept
---

# Beatmap Conversion Pipeline

## Overview

The conversion pipeline takes a BeatSaver custom song (V2 format) and converts it to PS4-compatible V3 format. The converted JSON is then gzip-compressed and stored in the m_Script field of a TextAsset in the PS4's AssetBundle template.

## V2 → V3 Data Flow

```
BeatSaver info.dat → extract _difficultyBeatmapSets → load each .dat file
  → parse V2 JSON
  → convert notes: _notes → colorNotes + colorNotesData
  → convert obstacles: _obstacles → obstacles + obstaclesData
  → convert bombs: _notes (type=3) → bombNotes + bombNotesData
  → convert chains: (future)
  → convert arcs: (future)
  → strip _events (PS4 uses separate lightshow data)
  → strip _customData
  → set version to "4.0.0"
  → serialize with json.dumps(..., separators=(',',':'))
  → gzip.compress()
  → write to m_Script via save_typetree with surrogateescape
```

## Note Conversion Algorithm

```python
def v2_to_v3_notes(v2_notes):
    data_map = {}       # (x, y, c, d) → index
    data_list = []      # index → {x, y, c, d}
    color_notes = []    # [{b, i}]
    
    for n in v2_notes:
        # Skip bombs (type=3) — they go in bombNotes
        if n.get('_type', 0) == 3:
            continue
            
        # Extract V2 properties
        key = (
            n.get('_lineIndex', 0),
            n.get('_lineLayer', 0),
            n.get('_type', 0),
            n.get('_cutDirection', 1)
        )
        
        # Deduplicate into data arrays
        if key not in data_map:
            data_map[key] = len(data_list)
            entry = {}
            if key[0] != 0: entry['x'] = key[0]
            if key[1] != 0: entry['y'] = key[1]
            if key[2] != 0: entry['c'] = key[2]
            if key[3] != 1: entry['d'] = key[3]
            data_list.append(entry)
        
        # Create colorNote (omit i if default 0)
        note = {'b': n['_time']}
        idx = data_map[key]
        if idx != 0: note['i'] = idx
        color_notes.append(note)
    
    return color_notes, data_list
```

### Key rules:
- If `_type == 3`, the note is a bomb → place in bombNotes, not colorNotes
- Only store non-default values in data entries to match PS4 format
- Default colorNotesData[0] is `{"x": 1, "d": 1}` — notes with default properties omit `i`
- Default bombNotesData[0] is `{"x": 3}` — bombs at column 3, row 0 (default)
- `json.dumps(..., separators=(',',':'))` produces compact output matching the template

## Bomb Notes Conversion

Bombs in V2 are notes with `_type: 3`. They use the same fields as regular notes (`_time`, `_lineIndex`, `_lineLayer`, `_cutDirection`) but are stored in separate V3 arrays: `bombNotes` + `bombNotesData`.

### V3 bombNotes Format
```json
"bombNotes": [{"b": <beat>, "i": <data_index>}],
"bombNotesData": [{"x": <col>, "y": <row>}]
```

BombNotesData only stores position (x, y) — no color (`c`) or direction (`d`) since bombs aren't cut.

### Conversion Algorithm

```python
def v2_to_v3_bombs(v2_notes):
    """Separate type=3 notes into bombNotes + bombNotesData"""
    bomb_v2 = [n for n in v2_notes if n.get('_type') == 3]
    
    data_map = {}; data_list = []; result = []
    for n in bomb_v2:
        key = (n.get('_lineIndex', 0), n.get('_lineLayer', 0))
        if key not in data_map:
            data_map[key] = len(data_list)
            entry = {}
            if key[0] != 0: entry['x'] = key[0]
            if key[1] != 0: entry['y'] = key[1]
            data_list.append(entry)
        
        note = {'b': n['_time']}
        idx = data_map[key]
        if idx != 0: note['i'] = idx
        result.append(note)
    
    return result, data_list
```

### Key differences from colorNotes:
- BombNotesData has only `x` and `y` fields (no `c` or `d`)
- Bombs with `_cutDirection` V2 field — this field is DISCARDED (bombs don't have direction in V3)
- Default bombNotesData[0] is `{"x": 3}` (column 3, row 0)
- The deduplication is by (x, y) position only — bombs at the same position reuse the same data entry

### Integration into pipeline
The full conversion separates V2 notes at the start:
```python
v2_notes = v2_data.get('_notes', [])
color_v2 = [n for n in v2_notes if n.get('_type', 0) in (0, 1)]   # Normal notes
bomb_v2  = [n for n in v2_notes if n.get('_type', 0) == 3]         # Bombs
```

## Obstacle Conversion

```python
def v2_to_v3_obstacles(v2_obs):
    obs_map = {}; obs_list = []; v3_obs = []
    for o in v2_obs:
        entry = {'d': o.get('_duration', 1.0), 'w': o.get('_width', 1), 'h': 5}
        key = (entry['d'], entry['w'], entry['h'])
        if key not in obs_map:
            obs_map[key] = len(obs_list)
            obs_list.append(entry)
        idx = obs_map[key]
        ob = {'b': o['_time']}
        if idx != 0: ob['i'] = idx
        v3_obs.append(ob)
    return v3_obs, obs_list
```

### V2→V3 obstacle field mapping:
| V2 field | V3 field | Notes |
|----------|----------|-------|
| `_time` | `b` | Beat time |
| `_duration` | `d` | Duration |
| `_width` | `w` | Width in columns |
| `_lineIndex` | (implicit) | V3 doesn't store column position — obstacles span from closest lane |
| `_type` | (implicit) | Always type 0 (wall) → height = 5 |

## m_Script Storage (Critical!)

The converted JSON is stored in the m_Script field of the TextAsset. **m_Script is JUST gzip data — no 4-byte decompressed_size prefix.**

```python
# ✅ CORRECT
new_json = json.dumps(v3_data, separators=(',',':')).encode('utf-8')
new_script = gzip.compress(new_json)  # just gzip, NO prefix!
tt['m_Script'] = new_script.decode('utf-8', 'surrogateescape')
reader.save_typetree(tt)
```

## Template Structure Preservation

To minimize risks, the conversion replaces ONLY the `colorNotes`/`colorNotesData` and `obstacles`/`obstaclesData` fields in the template's existing V3 data. This preserves:
- Exact V3 field ordering
- Empty arrays for unused types
- Any template-specific metadata

```python
# Load template V3 data
template_bm = json.loads(gzip.decompress(template_raw))
# Replace only what we need
template_bm['colorNotes'] = v3_notes
template_bm['colorNotesData'] = v3_data
template_bm['obstacles'] = v3_obs
template_bm['obstaclesData'] = v3_obs_data
# Keep everything else from template (bombNotes, chains, arcs, etc.)
```

See also: [[beatmap-format-v3]], [[m-script-gzip-format]], [[unitypy-serialization]], [[assetbundle-structure]]
