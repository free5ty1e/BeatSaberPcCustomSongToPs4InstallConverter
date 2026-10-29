---
name: beatmapping-guidelines
description: "The codified community playability rules (from MapCheck's implementations of the ranking criteria) + the official-catalog measurements that validate them — the descent engine's and the mode generators' constraint set."
metadata:
  type: reference
---

# Beatmapping guidelines (the codified rules, M15 R2)

Sources: the mapping community's ranking-criteria ecosystem as implemented
by **MapCheck** (KivalEvan/BeatSaber-MapCheck, the criteria checker's
`src/ts/checks/notes/*` — the rules in executable form), cross-validated
against [[official-difficulty-grammar]] (our own 304-song measurements).
Where folklore and measurement disagree, the measurement wins.

## The playability rules (the constraint set)

### Vision blocks — the #1 readability rule
A note in a **middle lane** (x=1 or x=2) hides notes that arrive soon
after behind it. MapCheck's per-difficulty time windows (seconds, capped
by jump-distance duration):

| Difficulty | min | max |
|---|---|---|
| Easy | 0.025 | 1.2 |
| Normal | 0.05 | 1.0 |
| Hard | 0.08 | 0.75 |
| Expert | 0.10 | 0.625 |
| Expert+ | 0.10 | 0.5 |

Rule for our generators: **after placing any mid-lane note, the next note
may not be at lower-or-equal x-lane within the difficulty's window** —
and our measurements show official Easy/Normal/Hard contain ~ZERO of
these (median 0 across 304 songs).

### Parity & the swing feel (the flow rules)
- **Swings alternate forehand/backhand per hand** (the parity model).
  A **double-directional** — the same hand hitting the SAME cut direction
  twice in a row — forces a wrist reset; it needs extra time or it plays
  badly. Parity breaks ARE sometimes intentional (double-directional ≠
  always wrong) but demand spacing.
- **Down cuts dominate everywhere** (45% Easy → 25% E+ as diagonals take
  over); **dots are ~1/3 of official notes at every difficulty**.
- **Direction follows position**: e.g. a left-side note cutting down-left
  flows out of the grid; an up-cut on the bottom row plays naturally
  after a down-cut above it. The wrist never travels against the swing.

### Stacked + collision geometry (MapCheck's exact models)
- **Stacked note**: same grid position at near-identical time —
  unplayable, never emit.
- **Hammer hit**: two notes within grid-distance ≤ 2 at close time —
  the second swing can't complete.
- **Handclap**: same-tick notes within distance ≤ 1 (or 1.5 with
  opposite colors) — the two sabers collide.
- **Hitbox rules** (inline/path/stair/reverse-stair): notes too close in
  time AND space clip the saber's travel path. The practical rule:
  consecutive same-color notes closer than ~¼ beat need ≥ 2 grid cells
  of separation in a consistent direction.

### Doubles + density
- **Excessive doubles**: too many same-tick pairs back-to-back is a
  stamina/readability smell (official medians: 48 Easy → 162 E+, see the
  grammar page).
- **Effective BPM / speed pauses**: sustained sub-¼-beat streams need
  rest windows; official lower difficulties ALWAYS breathe (gap medians:
  Easy 2 beats, Normal 1 beat — see the grammar).

### One Saber (the mode-generator upgrade targets)
One saber = one hand hits EVERYTHING. Consequences (the user's report:
"certain note patterns are almost impossible to play in one-saber mode"):
- **No same-tick doubles** (one saber, one note at a time) — the M5
  generator drops them ✓
- **No rapid same-lane direction flips** — a down-cut then up-cut in the
  same lane within ¼ beat is a wrist-crusher (needs ≥ ~½ beat or a lane
  change)
- **Min-gap per placement**: notes closer than ~¼ beat in adjacent lanes
  need consistent directions (the saber sweeps, it doesn't teleport)
- **Head-level (y=2) spacing**: consecutive y=2 notes need more time than
  mid-row notes (the swing arc is longer)
- **The saber color convention**: see [[saber-colors-and-one-saber]] —
  OneSaber is RIGHT/blue only; generated charts must recolor all notes c=0
  (the M5 generator does ✓ — keep it)

### 90 Degree (rotation rules)
- Rotation events must never fire mid-pattern: place them on rest beats
  (≥ ½ beat of empty space after), give the player ~½ beat to re-orient
  before the next note (the M5 generator cycles every N beats — the
  upgrade: align cycle boundaries to gaps in the note stream, not blind
  multiples).

### No Arrows
- With dots, **spacing + color alternation carry the entire rhythm** —
  tighten the min-gap (dots are individually readable but clusters read
  as one blob); keep the source's color cadence untouched (the M5
  generator only converts arrows→dots ✓ — the upgrade is the cluster
  audit).

## Engine-facing summary (the constraint set to implement)

1. Never emit: stacked notes, mid-lane vision blocks within the window,
   handclap/hammer geometry
2. Preserve: color cadence (~2/3 alternation), the difficulty's snap
   envelope + density band (the grammar's targets)
3. Repair: after note selection, re-map cut directions for parity/flow
   (the descent may rewrite `d`, never `b`/`c`-cadence)
4. Strip: bombs for generated lower difficulties (official style: none);
   walls only from the source's own wall policy
5. Rest: never emit a chart without breathing gaps (the per-difficulty
   gap medians are the floor)

Cross-references: [[official-difficulty-grammar]] (the measured targets),
[[saber-colors-and-one-saber]] (the OneSaber color rule),
[[beatsage-charting-behavior]] (why the engine exists).
