---
name: beatsage-charting-behavior
description: "What Beat Sage actually charts (live-measured): the flat Easy/Normal/Hard density band, v1-vs-v2 comparison, no density control exists, per-difficulty NPS expectations, and the naming/BPM quirks of their output."
metadata:
  type: reference
---

# Beat Sage charting behavior (live-measured, 2026-10-23)

Two controlled measurements on the same rights-clean synthesized 48s song
(120 BPM, constant kick/melody content) plus one real-song field report
(Eve 6 "Open Road Song", ~176s of mapped time).

## The flat Easy/Normal/Hard band — the #1 user surprise

**v2's Easy, Normal, and Hard are nearly the SAME difficulty.** Measured
NPS (notes per second) on the real song (v2):

| Difficulty | Notes | NPS | Verdict |
|---|---|---|---|
| Easy | 86 | 0.49 | baseline |
| Normal | 86 | 0.49 | identical to Easy |
| Hard | 108 | **0.61** | barely above Normal — **reads "sparse"** |
| Expert | 381 | 2.11 | the real curve starts here |
| ExpertPlus | 630 | 3.31 | the densest chart |

User field report: v2 Hard on a real rock song felt "really really sparse —
even less interesting than an Easy beatmap; barely any boxes." That is v2's
design, not a conversion bug: **the density lives in Expert/ExpertPlus.**
The practical guidance (now shown in our UI): play/deploy Expert+ for a
real workout; Hard exists but is mellow.

## v1 vs v2 (the only "model" control their API offers)

Same synth song, same options, both systems:

| Difficulty | v1 NPS | v2 NPS |
|---|---|---|
| Normal | 0.95 | 0.98 |
| Hard | 1.30 | 1.19 |
| Expert | 2.40 | 2.19 |
| ExpertPlus | 3.28 | 2.83 |

**v1 is only marginally denser** (a few %, more visible in the higher
difficulties). Switching to v1 is NOT a fix for sparse Hard — the flat band
is the model family's shape. v2 stays our recommended default (current
model, 90°/OneSaber/NoArrows mode support); v1 is exposed in our UI for
completeness with this caveat.

## There is NO density control

The complete, live-captured + probed option surface is: **difficulties
(Normal/Hard/Expert/ExpertPlus), modes (Standard/NoArrows/OneSaber/90°/
360°), events (Bombs/DotBlocks/Obstacles — "Lights" is a trap, see
[[beatsage-api-capture]]), environment (16), system_tag (v1/v2).** No
slider, no intensity/NPS setting, no "aggressive" flag. What their AI gives
is what you get; the only levers are difficulty choice and v1/v2.

## Output quirks to expect in their zips

- **Inconsistent mode-file naming in the SAME zip**: e.g. `90DegreeExpert.dat`
  (mode-prefix, populated) next to `Easy90Degree.dat` (difficulty-prefix,
  0 notes). Our validator + the pipeline's `detect_song_modes` handle BOTH
  orders, so this is cosmetic — but don't assume one convention.
- **Empty 90Degree charts**: v2 happily emits 0-note `*90Degree.dat` files
  (and 0-note `Easy90Degree`-style variants) — real 90° content only appears
  as the mode-prefix files. The pipeline's mode generators overwrite/replace
  mode charts with our own procedural versions anyway.
- **BPM estimates can be wrong**: their Info.dat `_beatsPerMinute` for the
  real song claimed 120.0 (the song's actual tempo is not that). Our
  pipeline treats Info.dat BPM as the mapper's grid (authoritative) and
  extends the grid when notes land beyond it — charts still play, but
  density per wall-clock-second is what it is.
- v2 emits `_version: 2.0.0` maps — our pipeline's V2→V3 conversion +
  Easy auto-fill (from Normal) handle them; **we auto-fill the Easy Beat
  Sage cannot generate.**

## What we built on top of this knowledge

- The web app's staging validator computes **per-difficulty note counts +
  NPS** from the map itself and shows them BEFORE you deploy/play (a sparse
  Hard is visible at staging time, not mid-song).
- A sparse-chart warning (Standard Hard/Easy below ~0.75 NPS) with the
  "density lives in Expert/Expert+" guidance.
- The Beat Sage form's "what to expect" note + the v1/v2 system dropdown
  with this page's caveat.

Cross-references: [[beatsage-api-capture]] (the API contract + the Lights
trap), [[absent-vs-failed-doctrine]] (sparse is a property to display, not
a failure).
