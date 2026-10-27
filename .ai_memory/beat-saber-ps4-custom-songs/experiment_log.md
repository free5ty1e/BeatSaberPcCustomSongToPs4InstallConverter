---
name: experiment-log
description: "Active experiment log for the CURRENT feature only (M15: the Lower-Difficulty Generation Engine — professional-grade Easy/Normal/Hard from Expert/Expert+ maps, following the official charting grammar; PLUS the mode-generator quality upgrades — OneSaber/NoArrows/90Degree to guideline standards). Per-feature rotation: when a feature concludes, archive this file into experiment_log_archive/ and open a fresh log. Experiment numbers are globally sequential across the whole project (last used: 284b in the M13 log)."
metadata:
  node_type: memory
  type: reference
---

# Experiment Log — M15: Lower-Difficulty Generation Engine + Charting Quality

Feature: turn Expert/Expert+ maps (Beat Sage output + the dense community
library) into genuinely good Easy/Normal/Hard following the OFFICIAL
difficulty grammar (measured from the dump's own catalog + the community
mapping guidelines); upgrade the mode generators to guideline standards
(the user's report: certain OneSaber patterns are near-impossible to play).
Plan: `.agent/plans/lower_difficulty_generation_engine.md`.

Archived logs: `experiment_log_archive/` (the previous feature ended at Exp
284b — the M13 log,
`experiment_log_m13-beat-sage-local-songs_exp283-284b_2026-10-22_to_2026-10-24.md`).


### Experiment 285: M15 begins — the plan, R1 (the official grammar MEASURED from 304 songs), R2 (the codified guidelines), and the descent engine v1 — 15/15 round-trip (2026-10-24)
- **User:** M15 is next (the lower-difficulty generation engine + the mode-generator quality upgrades); "no reason we can't make beatmaps as good as the official DLC"; research online as needed; no questions.
- **The plan:** `.agent/plans/lower_difficulty_generation_engine.md` — research-first (R1 measure the official grammar from the dump's own catalog; R2 the codified community guidelines; R3 subset-selection; R4 flow/vision scoring), then M15.2-M15.6 (engine → pipeline → mode-generator upgrades → webapp → live validation).
- **R1 — THE OFFICIAL GRAMMAR MEASURED** (`development/scripts/measure_official_difficulty_grammar.py`, 304 official songs × 5 difficulties): the density ladder (notes/beat 0.65 → 0.99 → 1.52 → 2.03 → 2.35; gap medians 2.0/1.0/0.5 beats), the snap ladder (Easy 87% on-beat → Hard 62% → E+ 48%), direction evolution (no diagonals below Hard; down+dot dominate), **official songs use almost NO bombs (median 0 at EVERY difficulty)**, walls uniform (~40-50), vision blocks ≈ 0 in lower difficulties. **The read-side discovery:** official beatmaps are SPARSE-COLUMNAR with FIXED DEFAULTS (x=0/y=0/c=0/d=8) — a carry-forward interpretation produced a nonsense 100%-same-color chart; the defaults interpretation reproduces the natural alternation + even lane spread. KB: official-difficulty-grammar.
- **R2 — the codified rules** (MapCheck's implementations of the ranking criteria + BSMG): vision-block windows per difficulty (0.025–1.2s Easy → 0.1–0.5s E+), parity/double-directional (the wrist-reset rule), stacked/hammer-hit(≤2)/handclap(≤1,≤1.5) geometry, excessive doubles, the OneSaber/90°/NoArrows mode rules. Cross-validated with a targeted corpus measurement: **y=2 same-lane close pairs = 0.0/chart in official Easy/Normal** (the exact vision-block geometry; the first version of the engine's rule — any mid-lane note — ate whole charts; the y=2 measurement corrected it). KB: beatmapping-guidelines.
- **The engine v1** (`tools/difficulty_engine.py`): stride selection (the strongest snap tier paces the whole span at ideal_gap — the early-stop bug front-loaded the first 2/3), the fill phase (weaker tiers fill holes with min-distance-to-ANY — the distance-to-last bug left Hard at 1.0 npb), L/R same-tick doubles with the same-lane guard, cross-tier alternation + recolor-last-resort (documented deviation; official feel > literal source color on mono runs), flow repair (double-directional orthogonals/dots), direction mapping into the per-difficulty allowed sets (diagonals→axis/dot), the y=2 vision filter, bombs stripped per the official object policy, walls preserved, exact-duplicate safety.
- **THE ROUND-TRIP ACCEPTANCE (15/15):** descended Easy/Normal/Hard from official E+ charts land IN the measured official bands with ZERO vision blocks — and track their own official counterparts (startmeup/Easy 293·0.69 vs official 282·0.67; startmeup/Hard 546·1.29 vs 607·1.43; TruthHurts/Hard 552·1.24 vs 517·1.16). Same-color ~15-33% (official band). 12 engine tests; suite 961+89 gated; ruff clean.
- **Next:** M15.3 the pipeline integration (--generate-difficulties), M15.4 the mode-generator upgrades, M15.5 webapp + docs, M15.6 the live play-test.

### Experiment 286: M15.3 + M15.4 — the descent INTEGRATED into the pipeline (grid inference for real-world sources) + the mode generators upgraded to the guidelines (2026-10-24)
- **M15.3 (pipeline 0.5367):** `fill_missing_standard_difficulties` now DESCENDS missing Easy/Normal/Hard from the map's densest source (≥2 tiers up) instead of cloning — `--skip-difficulty-descent` opts out; the clone remains the fallback for thin maps. 5 integration tests (descent, clone fallback, skip flag, no-overwrite, the drifting-source case).
- **THE GRID INFERENCE DISCOVERY (the Beat Sage integration):** the first live test (the user's actual Open Road Song) produced 13 notes — their maps label _time with a WRONG BPM (claimed 120; the song is really ~88; the note times drift off every fixed grid — no snap classification lands). Three fit attempts failed (a global scale search can't beat 380 beats of accumulated drift; the max-beat/duration estimate is off too — the chart doesn't reach the audio's end). THE FIX: (1) the fundamental 16th period from the inter-note gap histogram (the modal gap — 0.35 claimed-beats), (2) a **PLL grid tracker** walking the song and drift-correcting at each lock (tolerance ±30% of a 16th — the measured sweet spot: ±22% left 37% unclassified; ±38% over-locks), (3) the engine works in TRUE beats (the official bands live there) while emitting the notes' ORIGINAL times (selection-only doctrine). Live result: Easy 0.54 · Normal 1.00 · Hard 1.51 notes/beat — ALL IN THE OFFICIAL BANDS from the real drifting Beat Sage map.
- **M15.4 (the mode generators — the user's "impossible patterns" report):** OneSaber gains TRAVEL-TIME rules (required time grows with grid distance: same-cell double-swings kept per the M5 semantics, one-cell hops ½ gap, two-cell reaches the full gap, cross-grid jumps 2×, head-level y=2 the long arc); NoArrows gains the same-hand CLUSTER audit (same-color dots <¼ beat within 2 cells = a blob one hand can't take → dropped); 90Degree rotations now REST-ALIGN (the nearest clear beat with ≥½-beat clearance preferred, an outward-first search, graceful degradation in dense sections — the first version maximized clearance and flew to window edges). 8 new regression tests (the user's named impossible patterns: the cross-grid teleport, the head-level arc).
- **Suite: 974 passed + 89 gated** (+13); ruff clean; the official round-trip still 15/15.
- **Next:** M15.5 (the webapp deploy option + the feature doc + the stats surface), then M15.6 — the live end-to-end: Beat Sage → descend → deploy → PLAY all five difficulties on the PS4.
