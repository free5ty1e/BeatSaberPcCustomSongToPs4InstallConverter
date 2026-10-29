---
name: official-difficulty-grammar
description: "M15's ground truth: the OFFICIAL Beat Saber difficulty grammar, live-measured from 304 official songs in the game's own catalog (the dump) — density ladders, snap histograms, direction evolution, object policy. The descent engine's targets."
metadata:
  type: reference
---

# The official difficulty grammar (measured, M15 R1)

**Corpus: 304 official songs × 5 Standard difficulties**, read from the
game's own slot bundles (`.beatmap.gz` TextAssets) in the dump — measured
by `development/scripts/measure_official_difficulty_grammar.py`
(regenerable; the JSON is gitignored, aggregates only, no note data stored).

**The official beatmap storage is SPARSE-COLUMNAR** (a critical read-side
discovery, Exp 285): `colorNotes` carry `{b, i}` indexing into
`colorNotesData`, and each data row OMITS fields equal to their defaults
(x=0, y=0, c=0, d=8, a=0). Verified empirically: fixed defaults reproduce
the natural L/R alternation + even lane spread; a carry-forward reading
produced a nonsense 100%-same-color sequence. Any official-chart reader
must apply defaults, not inheritance.

## The ladders (medians across 304 songs)

| Metric | Easy | Normal | Hard | Expert | Expert+ |
|---|---|---|---|---|---|
| **notes/beat** | 0.65 | 0.99 | 1.52 | 2.03 | 2.35 |
| notes (total) | 284 | 421 | 645 | 869 | 1004 |
| **gap median (beats)** | **2.0** | **1.0** | **0.5** | **0.5** | **0.5** |
| gap p90 (beats) | 2.0 | 2.0 | 1.0 | 1.0 | 0.75 |
| peak notes / 8 beats | 10 | 14 | 19 | 26 | 32 |
| doubles (same-tick pairs) | 48.5 | 58.5 | 88 | 114 | 162 |
| same-color-adjacent | 33% | 35% | 33% | 31% | 31% |
| **snap on-beat** | **87%** | 80% | 62% | 51% | 48% |
| snap offbeat-eighth | 10% | 15% | 28% | 30% | 30% |
| snap sixteenth | 1.5% | 3.5% | 7% | 13% | 16% |
| vision blocks (rough) | **0** | **0** | **0** | 1 | 11 |
| bombs (median!) | **0** | **0** | **0** | **0** | **0** |
| walls | 40.5 | 41 | 46 | 43 | 50 |

**notes/beat p10–p90 bands** (the engine's target envelope): Easy
0.49–0.86 · Normal 0.71–1.31 · Hard 1.04–2.04 · Expert 1.39–2.80 · E+
1.69–3.18.

## The reading (what the numbers say)

- **The descent ladder IS the snap ladder**: Easy lives on whole beats
  (87% on-beat, a note every ~2 beats), Normal adds offbeat eighths, Hard
  is half-beat notes, Expert/E+ layer sixteenths. A lower difficulty is
  the SAME song with a coarser snap filter + flow repair — not "fewer
  random notes."
- **Color cadence is constant** (~2/3 alternation, ~1/3 same-color) across
  ALL difficulties — thinning must preserve the L/R musicality.
- **Direction evolution**: Easy = down (45%) + dots (28%) + straight
  left/right (24%) — **NO diagonals below Hard**. Diagonals (upright,
  downleft — the flow diagonals) appear at Expert (6% each) and dominate
  Expert+ (downleft 11%, upright 10%).
- **Vision blocks are ~zero by design** in Easy/Normal/Hard (our rough
  metric found medians of 0) — the #1 hard rule for lower difficulties.
- **Official songs use almost NO bombs** (median 0 at every difficulty!)
  — bombs are rare accents in official-style charting; Beat Sage's
  53-bomb Expert is NOT official-style. Descent policy: strip or reduce
  bombs for generated lower difficulties.
- **Walls are uniform** (~40-50 per song at every difficulty) — mostly
  crouch/event walls, not density features.

Cross-references: [[beatmapping-guidelines]] (the codified playability
rules this grammar must satisfy), [[beatsage-charting-behavior]] (the gap
this engine fills).
