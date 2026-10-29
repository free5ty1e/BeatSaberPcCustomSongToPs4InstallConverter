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

## Cycle 3 — Exp 287: the chiptunes + the picker + the docs

- The NES synthesis built: duty-cycled pulses, the 4-bit triangle, the LFSR noise channel (the hardware's period table), stepped envelopes. Two new songs (Groove 120 BPM + Scale Runner 140 BPM) + the theme (byte-identity pinned).
- The picker UI (select + generate-and-attach), the endpoint type dispatch, the CLI type param. The app boots 0.6.21 with all three songs serving.
- 7 new tests (determinism, endpoint, authenticity); suite 981+89.
- M15.5 docs: the feature doc, the changelog (asserted anchors!), README + CI_RELEASE.
- The live-experiment checklist formed: chiptune → Beat Sage → descend → deploy → play; plus the user's mass re-deploy plan.

## Cycle 4 — Exps 288-289: the Test Songs card + the closed loop

- The Test Songs card (registry endpoint, preview player, WAV/MP3 downloads, the attach bridge, pages-mode handling); ffmpeg installed + persisted.
- The score refactor (the ground truth as a first-class artifact); the byte-identity check caught the dropped _finish_pcm.
- THE CLOSED LOOP (the user's design): the oracle built → the chain run → Beat Sage's -14.29% BPM error + 4.6% grid lock measured → correction 1 (the time snap: 0→40%) → correction 2 (the multi-start EM) → correction 3 (the GCD quantization check) → VERDICT PASS (100% grid lock, 97-98% melody match on the descended charts).
- Exp 290: THE BATCH BUG (the user's field report) — the size-only session-ledger skip blocked a same-size different-bytes catalog upload (the console left in a CE-34878-0 risk state, the batch stopped at 1/47). Fixed: the md5 ledger (content-verified skips). Regression tests pin the exact scenario.
- Exp 291: THREE NEW CHIPTUNES per the user's designs — NES BeatTour 2026 (8 drum styles × 4 measures + fills + modulations), NES Scale Expedition (8 scales × 8 measures: runs/reversals/thirds/pivots with per-scale drums), One And a Half Dragons (the E-minor action-theme homage: 16th bass, the wide-interval hook, the pulse stabs, the half-time bridge). The registry/picker/CLI/oracle all carry the six songs.
- PR #11 updated (title + the full M15 description). The AGENTS.md staging discipline restored.

## Cycle 6 — Exp 292: the prefill fix + the repair + THE DEPLOY

- The stale-prefill bug fixed (state.lastAutoTitle/Artist — hand-edits preserved, stale auto-fills updated).
- The console repaired (the catalog re-uploaded, validation PASSED — the md5-ledger skip working "bytes verified").
- The Scale Runner deployed to Juice (the descended charts + Beat Sage's E+) — validation PASSED. THE FULL CHAIN COMPLETE.
- Staged: the app.js fix. The mass re-deploy ready for the user's go.

## Cycle 7 — Exp 293: THE EVALUATION PACK

The lizzo pack filled with 9 A/B variants (4 songs × descent/Beat Sage + the theme) — all validated, distinct in-game titles/artists. The automation: build_ab_pack.py (the Beat Sage runs, the variant preps, the deploys — with 3 path bugs fixed along the way). The prefill bug fixed (state.lastAutoTitle/Artist). The user's play-test = the final judgment; the mass re-deploy ready next.
