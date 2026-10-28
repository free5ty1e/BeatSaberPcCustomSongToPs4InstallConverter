# Lower-Difficulty Generation Engine + Charting Quality

**Status:** ✅ Round-trip validated against the official corpus (15/15); live-validated on a real Beat Sage map (all three difficulties in the official bands) · pipeline **0.5367+** · web app **0.6.21+** (the test-song picker) · no plugin changes

## What it does

**Missing Easy/Normal/Hard difficulties are now GENERATED — official-grade —
instead of cloned.** When a map ships only Expert/Expert+ (Beat Sage output,
the dense community library), the descent engine produces the missing lower
difficulties following the **measured official difficulty grammar**: the
density ladder, the snap ladder, the official color cadence, the official
object policy, and zero vision blocks.

This closes the gap the user named: Beat Sage's lower difficulties are one
near-empty band (live-measured 0.49–0.61 notes/sec), and most dense
community maps ship no playable low difficulties. Generate with Beat Sage
(their Expert/Expert+ is decent) → descend with this engine → the full
difficulty set, official-style.

## The measured grammar (the engine's targets)

Measured from **304 official songs** in the game's own catalog
(`development/scripts/measure_official_difficulty_grammar.py` — regenerable;
aggregates only, no note data stored):

| | Easy | Normal | Hard | Expert | Expert+ |
|---|---|---|---|---|---|
| notes/beat (median) | 0.65 | 0.99 | 1.52 | 2.03 | 2.35 |
| gap median (beats) | **2.0** | **1.0** | **0.5** | 0.5 | 0.5 |
| on-beat notes | **87%** | 80% | 62% | 51% | 48% |
| bombs (median!) | **0** | **0** | **0** | 0 | 0 |

The reading: a lower difficulty is the SAME SONG at a coarser snap filter
with flow repair — never "random fewer notes." Official charts use almost no
bombs at ANY difficulty (Beat Sage's 53-bomb Expert is not official-style),
and head-level same-lane vision blockers measure **0.0 per chart** in
official Easy/Normal.

## How the engine works (`tools/difficulty_engine.py`)

1. **Grid inference** — real-world sources often carry a wrong BPM label
   (Beat Sage's claim was 120; one test song is really ~88). The engine
   detects the fundamental 16th period from the inter-note gap histogram,
   then a **PLL tracker** walks the song drift-correcting at each lock.
   Analysis runs in TRUE beats (where the official bands live); every
   emitted note keeps its ORIGINAL time (selection-only doctrine).
2. **Stride selection** — the strongest snap tier paces the whole span
   evenly (never front-loaded), then weaker tiers fill holes to the
   measured target, spaced by the gap floor.
3. **L/R emphasis doubles** — same-tick opposite-color pairs emit together
   (the official emphasis pattern, ~10–16% of notes), never stacked in one lane.
4. **Cross-tier color alternation + recolor-last-resort** — the official
   hand cadence (~⅓ same-color) is preserved; mono-run sources get minimal
   recoloring (a documented deviation; the official FEEL outranks the
   literal source color).
5. **Flow repair** — same-hand same-direction close pairs (wrist crushers)
   flip to comfortable orthogonal cuts; directions map into the per-
   difficulty official sets (Easy/Normal: down/left/right/dot only — the
   measured official charts carry no diagonals below Hard).
6. **Vision-block avoidance** — the measured rule: head-level (y=2) notes
   never hide the same lane behind them within the difficulty's window.
7. **The object policy** — bombs stripped for generated lower difficulties
   (the official median is zero); walls preserved.

**Validation:** the round-trip acceptance — descend official Expert+ charts
and compare against their own official lower difficulties: **15/15 in-band,
zero vision blocks** (e.g. startmeup/Easy: generated 293 notes/0.69 per beat
vs official 282/0.67). Live on the user's real Beat Sage map (a drifting
tempo): Easy 0.54 · Normal 1.00 · Hard 1.51 — all in the official bands.

## The mode-generator quality upgrades (the charting guidelines)

The procedural OneSaber/NoArrows/90° generators now follow the codified
community rules (KB: `beatmapping-guidelines`):

- **OneSaber — travel-time rules:** one saber must physically REACH the
  next note. Required time grows with grid distance: same-cell double-swings
  kept, one-cell hops need ½ the gap, two-cell reaches the full gap,
  cross-grid jumps 2×, and head-level (y=2) notes get the long-arc time.
  Physically unreachable notes are dropped (the user's
  "almost impossible to play in one-saber mode" patterns).
- **NoArrows — the cluster audit:** with every arrow gone, spacing + color
  carry the rhythm; same-color dots closer than ¼ beat within 2 cells are
  a blob one hand cannot take — the later is dropped.
- **90° — rest-aligned rotations:** each cycle's rotation lands on the
  nearest clear beat (≥½-beat clearance preferred, graceful degradation in
  wall-to-wall sections) instead of firing blind under a stream.

## The chiptune test songs (the test-song picker)

The web app's 🧪 button now offers three rights-clean test songs, synthesized
on demand (100% math — deterministic):

- **BSD Deluxe Theme** — the original synth (byte-identical to the deployed one)
- **NES Groove** — drums (the LFSR noise channel), triangle bass, and a
  duty-cycled pulse riff at 120 BPM (the "basic rhythm with drum beats")
- **NES Scale Runner** — running major scales at 140 BPM over a steady
  kick/hat pulse (the cleanest descent-engine input: strong on-beat
  emphasis where every run starts)

The synthesis mimics the NES's audio hardware: pulse channels with
12.5/25/50/75% duty cycles, the 4-bit 16-step triangle, the 15-bit LFSR
noise channel at the hardware's 16 periods, and stepped 16-level volume
envelopes. CLI: `python3 development/scripts/make_rights_clean_test_song.py
out.wav [theme|nes_groove|nes_scale_runner] [seconds]`.

## Usage

Everything is automatic in the deploy flow: a map missing Easy/Normal/Hard
gets them descended from its densest difficulty. `--skip-difficulty-descent`
opts out (the old clone behavior). Re-deploying an existing loadout with
this version upgrades every song's generated modes (the guideline upgrades)
and fills any missing difficulties.
