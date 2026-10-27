# M15: Lower-Difficulty Generation Engine + Charting Quality — session transcript

Branch: `feature/lower-difficulty-generation-engine`. The user's directive: no questions needed; research online to supplement the KB on official charting guidelines; ALSO improve the mode generators (OneSaber impossible patterns, etc.) to the same standard; the goal is professional-grade, DLC-quality beatmaps from our tools.
Experiment numbers continue from the M13 log (last used 284b) → first M15 experiment = 285.

## Cycle 1 — orientation

- Branch verified: feature/lower-difficulty-generation-engine.
- Experiment log rotated (M13 → archive); the fresh M15 log opened.
- Next: the plan document, then the research (the official-grammar measurement over the dump's own catalog + the online guidelines synthesis), then the engine.

## Cycle 1 — Exp 285: plan + R1 + R2 + the engine v1 (15/15 round-trip)

- The plan written (research-first, M15.1-M15.6).
- R1: the official grammar MEASURED from 304 songs (the density/snap/direction ladders; bombs median 0; the sparse-columnar-with-defaults read-side discovery).
- R2: MapCheck's codified rules fetched + the targeted y=2 vision-geometry measurement (0.0/chart official Easy/Normal).
- Engine v1 built + debugged through 3 real iterations (front-loading stride fix; distance-to-any fill; the y=2 vision rule replacing the chart-eating mid-lane version; same-lane double guard; exact-duplicate safety).
- THE ROUND-TRIP: 15/15 in-band, zero vision blocks, profiles tracking the official counterparts. 12 tests; suite 961+89; ruff clean.

## Cycle 2 — Exp 286: integration + grid inference + the generator upgrades

- fill_missing_standard_difficulties wired to the engine (descent for E/N/H from ≥2-tier-up sources; --skip-difficulty-descent; clone fallback; 5 tests).
- THE DISCOVERY: Beat Sage's BPM label is wrong (claimed 120, really ~88) — the notes drift off every fixed grid; three fit attempts failed before the gap-histogram + PLL tracker solution (tolerance ±30%); the engine now works in TRUE beats and emits ORIGINAL times. Live proof on the user's map: all three difficulties in the official bands.
- The mode generators upgraded per the guidelines + the user's report: OneSaber travel-time rules (the proportional distance ladder + the head-level arc), NoArrows same-hand cluster audit, 90° rest-aligned rotations (outward-first search + the graceful degradation ladder). 8 regression tests.
- Suite 974 + 89 (+13); pipeline 0.5367 + changelog; the official round-trip still 15/15.
