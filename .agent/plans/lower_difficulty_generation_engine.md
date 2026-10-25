# M15 — Lower-Difficulty Generation Engine + Charting Quality (the Mode Generators)

**Status:** 🟢 In progress (Exp 285+, 2026-10-24)
**Branch:** `feature/lower-difficulty-generation-engine`
**User directive:** professional-grade output — "dial in our beatmap outputs to be professional-grade; there is no reason we can't make beatmaps as good as the official DLC with the tools we have in front of us." Research online as needed; improve the mode generators (OneSaber/NoArrows/90Degree) to the same guideline standard (the user's report: certain OneSaber patterns are near-impossible to play). No stopping to ask questions.
**Companion docs:** roadmap M15/M16 · KB: `beatsage-charting-behavior` (the gap), `saber-colors-and-one-saber` (the OneSaber color rule) · M5 roadmap section (the existing generators)
**Doctrine:** research-first, measured-not-guessed (the official catalog is the ground truth), every rule test-pinned, the web app stays a thin layer.

---

## 1. The problem (why this exists)

- **Beat Sage's lower difficulties are one near-empty band** (live-measured: Easy 0.49 / Normal 0.49 / Hard 0.61 NPS on a real song — "barely any boxes"). No density control exists on their service.
- **The dense community library** is almost all Expert/Expert+ — great charts, unplayable for anyone not at that level. Converting one gives you a song with only brutal difficulties.
- **Our current lower-difficulty machinery is a placeholder:** the Easy auto-fill *clones* Normal. No intelligence.
- **The mode generators** (M5: OneSaber/NoArrows/90Degree) work but ignore playability rules — e.g. OneSaber keeps same-color patterns that demand impossible wrist resets; the user has played these and flagged it.

**The bar:** official-DLC-quality lower difficulties — the official songs are FUN at low density because they follow real charting rules (rhythm emphasis, flow, readability, rest cadence, measured doubles), not just fewer notes.

## 2. What we already have (the foundation)

| Asset | Role in M15 |
|---|---|
| The **official catalog in the dump** (47 songs × 5 difficulties × Standard, V3 `.beatmap.gz` in each slot bundle) | **The ground truth corpus**: measure the official difficulty grammar from it (R1) — density bands, gap distributions, pattern rules |
| The M5 mode generators (`_generate_one_saber/no_arrows/90_degree`) | Prove chart-analysis → transform → re-inject end-to-end; get upgraded in M15.5 |
| The pipeline's V2→V3 conversion + `.beatmap.gz` inject path | The output format is solved — the engine only produces note data |
| The M13 chart-stats engine (`adapters/songs.py`) | Parses notes/NPS/peaks/bombs/walls from any map — the measurement half exists (webapp side; the measurement script reuses the concepts) |
| `BPMInfo.dat` / BPM-grid handling | The descent engine must select notes ON THE MUSIC GRID (beat-snap), not by wall-clock slicing |
| songs_repo + Beat Sage staged maps | Community reference data + the primary input class (E/E+ from Beat Sage) |

## 3. Research plan (before any engine code)

### R1 — Measure the OFFICIAL difficulty grammar (the corpus is local)

Script: `development/scripts/measure_official_difficulty_grammar.py` → walks
every official slot bundle in the dump (or the game_data cache), decompresses
each Standard difficulty's `.beatmap.gz`, and produces a per-difficulty
profile:

- **Density**: notes-per-second distribution (min/median/max per difficulty),
  notes per beat at the song's BPM, peak-window NPS (10s)
- **Timing**: inter-note gap distribution (in beats + seconds), rest
  frequency/length (longest gaps per difficulty), downbeat vs offbeat
  emphasis, beat-snap histogram (1/1, 1/2, 1/4, 1/8 usage per difficulty)
- **Patterning**: double (same-tick two-note) rates, the color-alternation
  rhythm (L/R cadence — the "one note per color per beat" rule), cut
  direction usage (down cuts dominate; up cuts when), angle-change
  frequency, the **vision-block geometry** (a note directly in front of
  another at close time), lane usage spread
- **Objects**: bomb/wall counts per difficulty (Easy: ~0; Hard: walls appear;
  Expert+: full object usage), per-object-type rates
- Output: `development/scripts/official_difficulty_grammar.json` + a KB
  page (`official-difficulty-grammar`) with the measured tables — the
  engine's TARGETS, and the reference the mode generators are checked
  against.

### R2 — The established community/official guidelines (online research)

Supplement the measurements with the mapping community's codified rules
(the criteria ecosystem around ranked maps; official-style guidance):

- **Vision blocks / readability** — the #1 quality rule: never place a note
  where it hides the next note; the "look ahead" window per difficulty
- **Flow & the swing feel** — cut directions follow natural wrist motion
  (downward cuts dominate; direction alternation; the reset/wrist-flick
  rules); angle blocks (hitbox orientation) as a readability tool
- **Per-difficulty expectations** — density bands + snap granularity + allowed
  patterns per difficulty (cross-checked against our R1 measurements — the
  measurements WIN where they disagree with folklore)
- **One Saber specifics** — single-color flow: the same-direction/streak
  rules, spacing to prevent impossible alternation, no same-lane rapid
  direction flips (the user's report), head-level placement conventions
- **90° specifics** — rotation-event timing (never mid-pattern), the
  reachable-lane constraint after rotation, rest beats around rotations
- **No Arrows specifics** — dot readability: spacing + color alternation
  become the whole game; anti-cluster rules
- Output: KB page `beatmapping-guidelines` with every rule sourced/attributed,
  cross-referenced with R1's measurements.

### R3 — The subset-selection study (the core algorithm question)

Given an E/E+ chart, WHICH notes make a good lower difficulty? Hypotheses to
test against the corpus:

- **Beat-snap hierarchy**: stronger snaps survive first (downbeats before
  offbeats before eighths before sixteenths) — the classic "descent" ladder
- **Onset/structural selection**: keep notes on the music's strong beats
  (we have BPMInfo/grid data; Beat Sage maps are AI-on-beat — ideal input)
- **Pattern preservation**: the L/R color cadence must stay musical after
  thinning (never two same-color notes in a row where the original
  alternated — the feel rule)
- **Flow repair after thinning**: removing notes can create awkward
  direction sequences; the direction of a kept note may need RE-MAPPING for
  flow (the engine may rewrite `_cutDirection`, not just delete notes)
- Validation: official songs exist in ALL difficulties — regenerate a
  lower difficulty from its own E+ chart and compare against the official
  result (density band ✓, snap histogram ✓, gap distribution ✓, flow
  score ✓). **This round-trip test is the engine's acceptance criterion.**

### R4 — Vision-block + flow scoring (the quality gate)

A scoring function over any generated chart: vision-block count (geometry
rule), direction-flow score (wrist-ergonomics rules), snap histogram fit,
rest cadence fit. Used in tests AND surfaced in the web app's staged-song
stats (a quality line per difficulty).

## 4. Implementation phases

- **M15.1 (R1+R2+KB)** — the measured grammar + the guidelines synthesis;
  the two KB pages; grammar JSON checked into the repo (it's derived data
  about OUR OWN tooling targets, not game content — derived statistics only,
  NO note data from the official charts is stored, only aggregates. If
  aggregates are deemed too close to game data, the JSON stays gitignored
  and regenerable from any dump — the SCRIPT is the shipped artifact).
- **M15.2 — the descent engine** (`tools/difficulty_engine.py`):
  `analyze(E+_chart, bpm_grid) → profile` · `descend(chart, target_profile)
  → chart` with: snap-aware selection, color-cadence repair, flow
  re-patterning, vision-block avoidance, object policy (bombs/walls per
  target difficulty). Pure functions, deeply unit-tested; the round-trip
  acceptance test against the corpus.
- **M15.3 — pipeline integration**: `--generate-difficulties
  easy,normal,hard[,expert]` (+ a config block); replaces the clone-Easy
  placeholder (auto-fill only when the mapper's own chart is missing);
  the generated charts marked in the deploy log; a `--descent-profile`
  override knob.
- **M15.4 — the mode-generator quality upgrades** (the user's explicit ask):
  - **OneSaber**: the impossible-pattern fixes — same-direction streak
    limits, min-gap enforcement per placement angle, no rapid same-lane
    direction flips, head-level spacing; checked against the KB's
    One-Saber rules + measured against official OneSaber content if any
    exists in the dump (check!) — else against the guidelines.
  - **NoArrows**: post-dot spacing/cluster rules; color-alternation audit.
  - **90Degree**: rotation timing rules (rest-beat-aligned, never
    mid-pattern), post-rotation reachability.
  - All three: the R4 quality score before/after in tests.
- **M15.5 — web app + docs**: the per-deploy "generate lower difficulties"
  option (Deploy tab, default ON when the map lacks them) + the staged-song
  stats gain the quality line; feature doc `lower-difficulty-engine.md`;
  README rows; the Beat Sage synergy note (generate with them → descend
  with us = the full set).
- **M15.6 — validation**: the round-trip corpus test + a live end-to-end:
  Beat Sage an audio → descend → deploy → **play all five difficulties on
  the PS4** (the user's final judgment, as with M13).

## 5. Test strategy

- Corpus round-trip (M15.2's acceptance): ≥N official songs, generated
  lower diffs within the measured bands + flow/vision scores ≥ thresholds
- Property tests: the descent never increases density; never emits a
  vision block at ≥ X notes; color cadence never breaks the feel rule;
  every generated note's time exists in the source (selection-only, until
  flow re-patterning explicitly rewrites directions — which is also tested)
- Mode generators: the user's impossible-pattern cases as named regression
  tests + the quality score deltas pinned
- Hermetic: all offline (the corpus is local); no network in CI

## 6. Open questions (answered by research, not by asking)

- Q1: Do official OneSaber/NoArrows/90° charts exist in the dump to
  measure? (M15.4's baseline — else guidelines-only.)
- Q2: Do we rewrite note DIRECTIONS during descent (flow repair) or only
  select? (R3's round-trip decides — official lower diffs clearly re-map
  directions; expect rewrite.)
- Q3: Expert from Expert+ too? (The roadmap names E/N/H; E from E+ is a
  small density step — include if the round-trip supports it.)
