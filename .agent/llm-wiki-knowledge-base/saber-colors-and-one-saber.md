---
name: saber-colors-and-one-saber
description: "Beat Saber saber color convention: LEFT saber = RED, RIGHT saber = BLUE, and OneSaber mode is played exclusively with the RIGHT (blue) saber"
metadata:
  type: reference
---

# Saber Colors & OneSaber Convention

## Core Convention (durable)

- **LEFT saber = RED**
  - V2 beatmaps (`_notes[]`): `_type = 0`
  - V3 beatmaps (`colorNotes[]`): `c = 0` (and `a = 0`)
- **RIGHT saber = BLUE**
  - V2: `_type = 1`
  - V3: `c = 1` (and `a = 1`)
- Bombs are `_type = 3` / `c = 3` in both formats and are saber-agnostic.

This color→saber mapping is fixed by the game. A note's color determines
**which saber must strike it**; a red note can only be cut by the left saber
and a blue note only by the right saber.

## OneSaber Mode Uses the RIGHT (Blue) Saber Exclusively

- OneSaber is a single-saber mode played with the **RIGHT (blue) saber only**.
- Therefore **every note in a OneSaber map MUST be BLUE (`c = 1` / `_type = 1`)**.
- A OneSaber map whose notes are RED is **unplayable**: the red notes cannot be
  hit by the (only) right saber, so they register as misses and the chart is
  effectively broken.

## The Pipeline Bug We Hit (and Fixed)

Our procedural OneSaber generator (`_generate_one_saber` in
`tools/full_custom_song_pipeline.py`) originally forced the single-saber color
to `_ONE_SABER_COLOR = 0` (LEFT/RED). That produced fully-red OneSaber maps that
were unplayable on the PS4 — confirmed by real in-headset play on 2026-08-16
(90° and No-Arrows were fun; OneSaber was broken because every note was red).

**Fix (pipeline v0.5323):** `_ONE_SABER_COLOR = 1` (RIGHT/BLUE). After the fix,
all 33 buggy generated OneSaber `.dat` files were regenerated from their Standard
sources via `development/scripts/regenerate_onesaber_blue.py`; the 12–15
already-blue (correct, incl. mapper-authored) OneSaber maps were left untouched.
Final state: 0 red OneSaber files, all remaining maps blue (or empty).

## Regenerating OneSaber After a Color Change

When the forced color changes, every generated OneSaber `.dat` must be
regenerated from its Standard source or recolored in place — see
`development/scripts/regenerate_onesaber_blue.py`. The pipeline's
`generate_missing_mode_beatmaps` skips songs that already ship their own
`<Diff>OneSaber.dat`, so a plain re-run will NOT fix already-generated red files;
they must be deleted or force-regenerated first.

## Architecture: where OneSaber actually lives (CRITICAL — do not confuse the two)

Beat Saber separates **song data** from **song-pack metadata**. Conflating them
is the #1 source of OneSaber bugs:

- **Song data = the per-song (custom) bundle** (e.g. `angry_v3.bundle`).
  Holds the AUDIO and the BEATMAPS, including the **all-blue OneSaber beatmap**
  from `_generate_one_saber` (`_ONE_SABER_COLOR = 1`). The blue OneSaber notes
  live HERE — never in the pack.
- **Song pack = the album bundle + Addressables catalog** (e.g.
  `therollingstones_pack_*.bundle`, `catalog_pack_modes.json`). Holds ONLY
  **metadata**: song list, cover, environment, and `_previewDifficultyBeatmapSets`
  — which mode buttons (Standard / OneSaber / NoArrows / 90°) appear, each
  difficulty carrying a **PPtr** into the per-song bundle's beatmaps. It contains
  **no note data**.

Enabling OneSaber is two independent steps that are easy to merge:
1. **Generate the blue OneSaber beatmap** → in the song data (custom-song
   generator; DONE, blue).
2. **Make the pack show the OneSaber button AND point it at that blue beatmap**
   → pack-metadata fix. The OneSaber preview entry must reference the per-song
   bundle's OneSaber beatmap PPtr, not clone Standard's.

### The actual pack bug (and why "recolor the pack" is wrong)
`build_pack_mode_bundles.py` `build_modes_blob` builds the OneSaber preview set
by **cloning Standard's difficulty PPtrs** into the OneSaber slot (lines 256-260).
That makes the OneSaber button load **Standard's (mixed) beatmap**, so the mode
shows red+blue notes and is unplayable. The fix is a **PPtr reference fix** in
the pack — point OneSaber at the per-song bundle's blue OneSaber beatmap — NOT
recoloring note data in the pack, which has none.

### UnityPy limitation (informational only)
UnityPy returns `UnknownObject` for `BeatmapLevelSO` / `BeatmapData`
MonoBehaviours, so preview-set PPtrs are edited at the raw serialized-blob level
by `build_pack_mode_bundles.py` (the same machinery used for the
Standard/OneSaber/NoArrows/90° set extension and CRC-correct catalog). No note
recoloring is needed or possible in the pack — the notes are in the song data.

## Related

- [[procedural-mode-generators|Procedural Mode Generators]] — `_generate_one_saber` wiring & the `_ONE_SABER_COLOR` constant
- [[note-color-field-version-differences|Note Color Field: V3 vs V3.3+ vs V4]] — `c` vs `a` field, `0`=Red/`1`=Blue across formats
- [[beatmap-format-v3|PS4 Beatmap Format (V3)]] — `colorNotes[]` field names (`c`, `a`, `d`)
- [[pack-bundle-patching|Pack Bundle Patching]] — raw-blob UnityFS/CAB surgery + GF(2) CRC correction (the machinery to reuse for OneSaber recolor)
- [[procedural-mode-generators|Procedural Mode Generators]] — custom-song OneSaber generation (distinct from the pack-clone path above)
