# Note Color Field: V3 vs V3.3+ vs V4

## The Bug

The PS4 version of Beat Saber uses the **`c` field** for note color, NOT the `a` field. 
Our V2→V3 converter was only setting `a`, causing all notes to appear Red.

## Evidence

**Espresso (V3.3.0, WORKING correctly):**
```json
{'b': 4, 'x': 2, 'y': 0, 'a': 0, 'c': 1, 'd': 1}
{'b': 6, 'x': 1, 'y': 0, 'a': 0, 'c': 0, 'd': 1}
```
- `a: 0` for ALL 262 notes (constant — NOT the color field)
- `c: 0` or `c: 1` alternating — **this IS the color field**

**Our V3.2.0 converter output (BROKEN):**
```json
{'b': 4.0, 'x': 2, 'y': 0, 'a': 0, 'd': 1}
```
- No `c` field → game defaults to `c: 0` → ALL Red

## How Color Works Across Beatmap Versions

| Format | Field for Color | Location | Notes |
|--------|----------------|----------|-------|
| V2 | `_type` | `_notes[]` | `0`=Red, `1`=Blue, `3`=Bomb |
| V3 (3.0.0–3.2.0) | `a` | `colorNotes[]` | `a` = color (inline on note object) |
| V3 (3.3.0+) | `c` | `colorNotes[]` | `c` = color, `a` = chain/arc color? (both set) |
| V4 | `c` | `colorNotesData[]` | Separate data array, `c` = color |

## The Fix

In the V2→V3 converter, both `a` and `c` must be set:

```python
base["a"] = nt   # standard V3 field
base["c"] = nt   # PS4 game uses this for color (V3.3.0+)
base["d"] = int(note.get("_cutDirection", 0))
```

## Why This Happens

The original Rolling Stones bundles shipped with V4.0.0 format beatmaps,
where note data (including color) is stored in `colorNotesData[]` with
`c` being the color field. The PS4 port expects this `c` field.
When a V3.2.0 beatmap without `c` is loaded, the game parser defaults
`c` to 0 (Red).

Reference: Beat Saber format evolution
- V2: `_notes[]` with `_type: 0|1` (Red/Blue)
- V3.0.0–3.2.0: `colorNotes[]` with `a: 0|1`  
- V3.3.0: `colorNotes[]` with `a: 0|1, c: 0|1` (added c field)
- V4/V5: `colorNotes[]` with only `b`, separate `colorNotesData[]` with `{x, c, d}`
