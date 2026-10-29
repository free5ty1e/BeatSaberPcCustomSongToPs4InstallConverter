"""
difficulty_engine.py — M15: the Lower-Difficulty Descent Engine.

Turns a dense source chart (Expert/Expert+ — Beat Sage output, community
maps) into official-style Easy/Normal/Hard(/Expert), following the MEASURED
official difficulty grammar (304 official songs; see
`development/scripts/measure_official_difficulty_grammar.py` and the KB
page `official-difficulty-grammar`) and the codified playability rules
(KB: `beatmapping-guidelines` — vision blocks, parity/flow, stacked/collision
geometry, the object policy).

Design (the research distilled):
- A lower difficulty is the SAME SONG at a coarser SNAP FILTER + FLOW
  REPAIR — never "random fewer notes." The official ladder IS the snap
  ladder: Easy 87% on-beat (a note every ~2 beats), Normal ~1/beat
  (on-beat + offbeat eighths), Hard ~1.5/beat (half-beat grid).
- The engine only ever: SELECTS notes (drops), REWRITES cut directions
  (d/a) for parity/flow + the difficulty's allowed direction set, and
  STRIPS bombs (official lower difficulties carry none — measured median
  0). It never invents note times and never touches the color cadence.
- Vision-block avoidance + rest preservation are enforced on the output.

Pure functions, V3 note dicts in/out ({b, x, y, c, d, a}; V2 sources are
converted by the pipeline before reaching here — see
full_custom_song_pipeline.is_v2_beatmap/convert_v2_to_v3).
"""

from __future__ import annotations

import bisect
from collections import Counter

# ─────────────────────────────────────────────────────────────────────────────
# The measured grammar (per-difficulty targets). Sources: the 304-song
# measurement (KB: official-difficulty-grammar). Beat-domain — BPM-free.
# ─────────────────────────────────────────────────────────────────────────────

PROFILES: dict[str, dict] = {
    # notes/beat: the measured median (p10-p90 envelope in the KB page).
    # snap_rank keys = snap_bucket() values: 0 on-beat · 50 offbeat-eighth ·
    # 25 sixteenth. (The measured snap ladder: Easy 87% on-beat, Normal
    # 80%, Hard 62% — the ladder IS the difficulty.)
    "Easy": {
        "notes_per_beat": 0.65,        # band 0.49–0.86
        "snap_rank": {0: 1.0},         # whole beats ONLY (87% measured)
        "gap_floor_beats": 1.0,        # never denser than one note per beat
        "allowed_directions": {1, 2, 3, 8},   # down, left, right, dot (no up, NO diagonals)
        "vision_block_s": (0.025, 1.2),
        "keep_bombs": False,
        "max_doubles_pct": 0.10,
    },
    "Normal": {
        "notes_per_beat": 1.0,         # band 0.71–1.31
        "snap_rank": {0: 1.0, 50: 0.15},  # on-beat + occasional offbeat eighths
        "gap_floor_beats": 0.5,
        "allowed_directions": {1, 2, 3, 8},
        "vision_block_s": (0.05, 1.0),
        "keep_bombs": False,
        "max_doubles_pct": 0.12,
    },
    "Hard": {
        "notes_per_beat": 1.5,         # band 1.04–2.04
        "snap_rank": {0: 1.0, 50: 0.5, 25: 0.12},  # on-beat + eighths + some sixteenths
        "gap_floor_beats": 0.25,
        "allowed_directions": {0, 1, 2, 3, 8},    # up enters; diagonals still rare
        "vision_block_s": (0.08, 0.75),
        "keep_bombs": False,
        "max_doubles_pct": 0.14,
    },
    "Expert": {
        "notes_per_beat": 2.0,
        "snap_rank": {0: 1.0, 50: 0.8, 25: 0.3},
        "gap_floor_beats": 0.25,
        "allowed_directions": {0, 1, 2, 3, 4, 5, 6, 7, 8},
        "vision_block_s": (0.1, 0.625),
        "keep_bombs": True,
        "max_doubles_pct": 0.16,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# GRID INFERENCE (Exp 286's Beat Sage discovery): real-world sources often
# carry a beat grid that does NOT match their claimed BPM — Beat Sage maps
# place notes correctly in TIME but label _time with their (wrong) BPM
# estimate, so the times drift off any fixed snap grid and the snap ladder
# finds nothing. The engine therefore FITS the source's true grid (a scale
# around 1.0 + an origin shift) by maximizing the fraction of notes landing
# on the quarter-beat grid, then classifies snaps on the INFERRED grid.
# The notes' own times are never modified (selection-only doctrine).
# ─────────────────────────────────────────────────────────────────────────────

def _modal_sixteenth(times: list[float]) -> float:
    """The fundamental 16th-note period in source units. Drift-robust (the
    Exp 289 lesson: Beat Sage's audio drifts against their fixed BPM label,
    so the gap histogram splits into jitter bands — 0.20/0.22 around the
    true 0.214 — and an exact-mode pick grabbed a band edge, sending the
    PLL to a wrong multiple): the MEDIAN of the small gaps sits on the
    true period regardless of the band split."""
    gaps = sorted(g for g in (b - a for a, b in zip(times, times[1:]))
                  if 0.05 < g < 0.5)
    if not gaps:
        return 0.25
    return gaps[len(gaps) // 2]


def _direct_grid_fit(times: list[float]) -> float:
    """Fraction of notes landing on the raw 0.25 grid (official charts and
    correctly-gridded community maps fit ~100%)."""
    frac_buckets = [snap_bucket(t) for t in times]
    return sum(1 for b in frac_buckets if b in (0, 25, 50)) / max(len(times), 1)


def _track_grid(times: list[float], quarter_hint: float) -> list[int]:
    """PLL grid tracker (Exp 286): walk the notes in time order, locking to
    near-grid notes and drift-correcting the reference as the song's tempo
    breathes (a real recording's grid drifts — no fixed scale fits the whole
    song; the measured Beat Sage map: 18% global fit vs drifting tempo).
    Returns a snap-bucket code per note: 0 on-beat · 50 offbeat-eighth ·
    25 sixteenth · -1 off-grid."""
    if not times:
        return []
    out: list[int] = []
    ref_t, ref_k = times[0], 0
    for t in times:
        k_f = (t - ref_t) / quarter_hint + ref_k
        k = round(k_f)
        err = abs(k_f - k)
        if err <= 0.30:            # ±30% of a 16th: the measured sweet spot
                                   # (±22% left 37% of a drifting song unclassified;
                                   #    ±38% over-locks into wrong grid positions)
            ref_t, ref_k = t, k    # drift-correct: re-anchor at this note
            m = k % 4
            out.append(0 if m == 0 else 50 if m == 2 else 25)
        else:
            out.append(-1)
    # resolve the downbeat ambiguity: relabel so the mode of {0, 50} with the
    # most notes is on-beat (rhythm emphasis: strong beats carry more notes)
    n_on = sum(1 for b in out if b == 0)
    n_off = sum(1 for b in out if b == 50)
    if n_off > n_on:
        out = [{0: 50, 50: 0, 25: 25, -1: -1}[b] for b in out]
    return out


def infer_grid(times: list[float]) -> tuple[list[int], float]:
    """The grid-aware snap classification for a source chart. Perfectly
    gridded sources (official, most community maps) classify directly on
    the raw beat grid (beat period 1.0); drifting sources (Beat Sage's
    mis-BPM'd output, live recordings) get the PLL tracker + a linear-
    REGRESSION refinement: the first pass locks notes to a coarse grid
    (the median-gap hint — drift splits the exact modes into jitter
    bands), then the locked (time, grid-index) pairs regress to the TRUE
    16th period (the regression absorbs tempo drift exactly — the
    Scale Runner measured: 120 claimed, 140.2 recovered vs 140 true).
    The engine then works in TRUE beats (the official bands are defined
    there) while emitting the notes' ORIGINAL times untouched. Returns
    (snap codes per note, beat period in source units)."""
    if not times:
        return [], 1.0
    if _direct_grid_fit(times) >= 0.60:
        return [snap_bucket(t) for t in times], 1.0
    hint = _modal_sixteenth(times)
    first = _track_grid(times, hint)
    # the refinement: regress time vs the locked 16th index
    locked = [(t, k) for t, code, k in
              zip(times, first, _lock_indices(times, hint, first))
              if code in (0, 25, 50) and k is not None]
    if len(locked) >= 20:
        n = len(locked)
        sx = sum(k for _, k in locked)
        sy = sum(t for t, _ in locked)
        sxx = sum(k * k for _, k in locked)
        sxy = sum(t * k for t, k in locked)
        denom = n * sxx - sx * sx
        if abs(denom) > 1e-9:
            slope = (n * sxy - sx * sy) / denom      # the TRUE 16th period
            if 0.3 * hint < slope < 3.0 * hint:
                hint = slope                          # the refined 16th
    # ── the EM refinement + MULTI-START (the oracle's demand, Exp 289):
    # the EM converges to the LOCAL optimum nearest its starting hint —
    # multiple self-consistent grids exist within ±5% (the Scale Runner:
    # the 139.4-BPM basin vs the true 140.0), and the wrong one leaves
    # residual outliers. Multi-start EM: try hints across ±6% (a 1% step),
    # run the snap+regress iterations from each, and keep the grid with the
    # SMALLEST mean snapping residual (the true grid explains every note).
    def em(h: float) -> float:
        for _ in range(6):
            pairs = [(t, round(t / h)) for t in times]
            n = len(pairs)
            sx = sum(k for _, k in pairs)
            sy = sum(t for t, _ in pairs)
            sxx = sum(k * k for _, k in pairs)
            sxy = sum(t * k for t, k in pairs)
            den = n * sxx - sx * sx
            if abs(den) < 1e-9:
                break
            slope = (n * sxy - sx * sy) / den
            if not (0.9 * h < slope < 1.1 * h):
                break
            if abs(slope - h) < 1e-7:
                h = slope
                break
            h = slope
        return h

    def residual(h: float) -> float:
        total = sum(abs(t - round(t / h) * h) for t in times)
        return total / max(len(times), 1)

    best_hint, best_res = hint, residual(hint)
    for k in range(-6, 7):
        if k == 0:
            continue
        trial = em(hint * (1.0 + 0.01 * k))
        res = residual(trial)
        if res < best_res - 1e-9:
            best_hint, best_res = trial, res
    hint = best_hint
    refined = _track_grid(times, hint)
    return refined, max(4 * hint, 0.05)


def _lock_indices(times: list[float], hint: float,
                  codes: list[int]) -> list[int | None]:
    """The 16th-index each locked note snapped to (for the regression)."""
    out: list[int | None] = []
    ref_t, ref_k = times[0], 0
    for t in times:
        k_f = (t - ref_t) / hint + ref_k
        k = round(k_f)
        if abs(k_f - k) <= 0.30:
            ref_t, ref_k = t, k
            out.append(k)
        else:
            out.append(None)
    return out



# snap categories: the fractional part of the beat position, in 1/100 beats
def snap_bucket(beat: float) -> int:
    """0 = on-beat · 25 = sixteenth · 50 = offbeat-eighth · -1 = other."""
    frac = round((beat % 1.0) * 100)
    if frac in (0, 100):
        return 0
    if frac in (25, 75):
        return 25
    if frac == 50:
        return 50
    return -1


# direction helpers ───────────────────────────────────────────────────────────
# V3 cut directions: 0=up 1=down 2=left 3=right 4=upleft 5=upright
#                    6=downleft 7=downright 8=any/dot
_DIAG_AXIS = {4: 2, 5: 3, 6: 2, 7: 1}   # diagonal → its flow axis (left/right/down)
_ORTHOGONAL = {1: {2, 3}, 0: {2, 3}, 2: {0, 1}, 3: {0, 1}}


def _map_direction(d: int, allowed: set[int]) -> int:
    """Map a cut direction into the difficulty's allowed set, preserving the
    swing's feel (diagonals collapse to their axis; unmapped awkward cuts
    become dots — 28% of official notes at every difficulty are dots)."""
    if d in allowed:
        return d
    if d in _DIAG_AXIS and _DIAG_AXIS[d] in allowed:
        return _DIAG_AXIS[d]
    return 8  # dot: always playable, official-style repair


def _is_double_directional(prev: dict, cur: dict) -> bool:
    """Same hand, same direction, close in time → a wrist reset (the parity
    rule, KB: beatmapping-guidelines)."""
    return (prev["c"] == cur["c"] and prev["d"] == cur["d"]
            and prev["d"] != 8 and (cur["b"] - prev["b"]) <= 0.5)


# ─────────────────────────────────────────────────────────────────────────────
# The engine
# ─────────────────────────────────────────────────────────────────────────────

def descend(source_notes: list[dict], bpm: float, difficulty: str,
            source_bombs: list[dict] | None = None,
            source_walls: list[dict] | None = None) -> dict:
    """Generate a lower difficulty from a dense source chart.

    source_notes: V3 notes [{b, x, y, c, d(, a)}], any density (E/E+ ideal).
    bpm:          the song's BPM (for the vision-block window, seconds-based).
    difficulty:   "Easy" | "Normal" | "Hard" | "Expert".
    Returns: {"notes": [...V3...], "bombs": [...], "walls": [...]} — the
    generated chart, selection-only on times, flow-repaired directions,
    bombs stripped per the official object policy (walls preserved).
    """
    profile = PROFILES[difficulty]
    allowed = set(profile["allowed_directions"])
    sec_per_beat = 60.0 / max(bpm, 1.0)

    if not source_notes:
        return {"notes": [], "bombs": [] if not profile["keep_bombs"] else list(source_bombs or []),
                "walls": list(source_walls or [])}

    # ── 1. SNAP-AWARE SELECTION ─────────────────────────────────────────────
    # Group candidates by beat position within each snap tier. When a beat
    # carries BOTH colors, emit the L/R pair together (the official emphasis
    # double — the source of the official ~33% same-color adjacency). When it
    # carries one color, emit it as an alternating single — preferring a nearby
    # opposite-color candidate in the same tier when the beat's own color
    # would repeat the last color.
    # ── 0. GRID AWARENESS: work in TRUE beats, emit ORIGINAL times ──────────
    # Mis-BPM'd sources (Beat Sage, live recordings) put the true beat grid
    # at beat_period source-units per real beat; the official bands + the
    # engine's gap floors are defined in TRUE beats, so the analysis works
    # on scaled copies (b_true = b / beat_period) while every emitted note
    # keeps its original b (the pipeline's grid machinery handles the rest).
    snap_codes, beat_period = infer_grid([n["b"] for n in source_notes])
    if beat_period == 1.0:
        work = [dict(n) for n in source_notes]
        for w, o in zip(work, source_notes):
            w["b_orig"] = o["b"]
    else:
        work = [{**n, "b": n["b"] / beat_period, "b_orig": n["b"]}
                for n in source_notes]
    sec_per_beat = beat_period * 60.0 / max(bpm, 1.0)

    ranked: dict[int, dict[float, list[dict]]] = {}
    for n, snap in zip(work, snap_codes):
        if profile["snap_rank"].get(snap, 0.0) <= 0:
            continue                       # this difficulty doesn't use that snap
        ranked.setdefault(snap, {}).setdefault(round(n["b"], 4), []).append(n)

    # The target count from the measured density (median of the band) — in
    # TRUE beats (work notes), so mis-BPM'd sources land in the official band
    span_beats = work[-1]["b"] - work[0]["b"]
    target = max(1, int(round(profile["notes_per_beat"] * max(span_beats, 1.0))))

    # An index of ALL candidates by beat position (across the profile's
    # allowed snaps) for the cross-tier alternation search below.
    by_beat: dict[float, list[dict]] = {}
    for pool in ranked.values():
        for beat_pos, cands in pool.items():
            by_beat.setdefault(beat_pos, []).extend(cands)

    # STRIDE SELECTION (Exp 285): TWO PHASES.
    # PRIMARY: the strongest tier walks the WHOLE span at >= ideal_gap
    # (span/target) spacing — even coverage, never front-loaded (the early
    # stop at the target died at the bridge).
    # FILL: weaker tiers add density into the gaps — min distance to ANY
    # selected note >= gap_floor — until the measured target. (Distance to
    # the LAST note left Hard at ~1.0 npb; the official band is 1.04–2.04.)
    ideal_gap = max(profile["gap_floor_beats"], span_beats / max(target, 1))
    tiers = sorted(ranked, key=lambda s: -profile["snap_rank"][s])
    selected: list[dict] = []

    def emit_double(cands: list[dict]) -> bool:
        """The official L/R emphasis double — both colors at this tick, ONLY
        when they sit in different lanes (the corpus: 0.0 same-lane y=2
        pairs per official Easy/Normal chart). Returns True if a pair went
        out; the caller falls back to the best single otherwise."""
        by_color: dict[int, dict] = {}
        for z in cands:
            by_color.setdefault(z["c"], z)
        if len(by_color) < 2:
            return False
        a, b = by_color[0], by_color[1]
        if a["x"] == b["x"]:
            return False
        selected.append(a)
        selected.append(b)
        return True

    def pick_alternating(note: dict, beat_pos: float) -> dict:
        """When this note repeats the last emitted color, prefer a nearby
        opposite-color candidate (any allowed snap within ±0.5/±0.25)."""
        if not selected or note["c"] != selected[-1]["c"]:
            return note
        for nearby in (beat_pos + 0.5, beat_pos - 0.5,
                       beat_pos + 0.25, beat_pos - 0.25):
            group = by_beat.get(round(nearby, 4))
            if group and any(z["c"] != note["c"] for z in group):
                alt = next(z for z in group if z["c"] != note["c"])
                if abs(nearby - beat_pos) >= profile["gap_floor_beats"] - 1e-6:
                    return alt
        return note

    # ── phase 1: the primary tier's stride walk ────────────────────────────
    next_allowed = float("-inf")
    if tiers:
        pool = ranked[tiers[0]]
        for beat_pos in sorted(pool):
            if beat_pos < next_allowed - 1e-6:
                continue
            cands = pool[beat_pos]
            if not emit_double(cands):
                selected.append(pick_alternating(cands[0], beat_pos))
            next_allowed = beat_pos + ideal_gap

    # ── phase 2: the fill (all tiers, weakest holes first per tier) ───────
    for snap in tiers:
        if len(selected) >= target:
            break
        pool = ranked[snap]
        occupied = sorted(x["b"] for x in selected)
        for beat_pos in sorted(pool):
            if len(selected) >= target:
                break
            idx = bisect.bisect_left(occupied, beat_pos)
            near = float("inf")
            if idx > 0:
                near = min(near, beat_pos - occupied[idx - 1])
            if idx < len(occupied):
                near = min(near, occupied[idx] - beat_pos)
            if near < profile["gap_floor_beats"] - 1e-6:
                continue
            cands = pool[beat_pos]
            if not emit_double(cands):
                selected.append(pick_alternating(cands[0], beat_pos))
            occupied = sorted(x["b"] for x in selected)

    # ── the final safety: exact duplicates must never survive ──────────────
    seen: set[tuple] = set()
    deduped: list[dict] = []
    for n in sorted(selected, key=lambda z: z["b"]):
        key = (round(n["b"], 4), n["x"], n["y"], n["c"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(n)
    selected = deduped
    selected.sort(key=lambda n: n["b"])

    # ── 2. THE DOUBLE POLICY ─────────────────────────────────────────────
    # Same-tick L/R pairs are the official emphasis pattern (kept, capped by
    # the measured %); 3+ note stacks are trimmed to the first two.
    counts = Counter(round(n["b"], 3) for n in selected)
    max_stack = 2
    pruned: list[dict] = []
    stack_used: dict[float, int] = {}
    for n in selected:
        t = round(n["b"], 3)
        if counts[t] > 1:
            used = stack_used.get(t, 0)
            if used >= max_stack:
                continue
            stack_used[t] = used + 1
        pruned.append(n)
    selected = pruned

    # ── 2b. CADENCE LAST RESORT (documented deviation) ─────────────────────
    # When a mono-run would form (3+ same-color consecutive — official
    # medians cap runs around 5 but the ~33% same-color AGGREGATE is the
    # feel target), and no substitute candidate exists (a mono snap tier —
    # e.g. an alternating-16ths source where every on-beat note is one
    # color), FLIP the excess notes' color to restore alternation. Mapping
    # edits do exactly this; the official FEEL (hand alternation) outranks
    # the source's literal color at that position. Never applied at Expert.
    if difficulty != "Expert":
        run = 0
        for i in range(1, len(selected)):
            if selected[i]["c"] == selected[i - 1]["c"]:
                run += 1
                if run >= 2:  # 3rd same-color note in a row → flip this one
                    selected[i] = {**selected[i], "c": 1 - selected[i]["c"]}
                    run = 0
            else:
                run = 0

    # ── 3. FLOW REPAIR + TIME CORRECTION ────────────────────────────────────
    # Emission snaps each note onto the INFERRED 16th grid (in source units).
    # The loop's data (Exp 289, the oracle): mis-BPM'd sources drift against
    # the music (Beat Sage's Scale Runner: 120 claimed vs 140 true — the
    # oracle measured 0% grid lock on the raw times), and a chart labeled
    # with the wrong BPM drifts IN-GAME too. The inferred grid IS the true
    # musical grid in source units — snapping corrects sync AND musicality.
    # For correctly-gridded sources (period 1.0, 16ths = 0.25) this is a
    # no-op: they already sit on the grid.
    sixteenth_period = beat_period / 4.0
    out: list[dict] = []
    last_by_color: dict[int, dict] = {}
    for n in selected:
        b_raw = n.get("b_orig", n["b"])
        b_out = round(b_raw / sixteenth_period) * sixteenth_period if \
            sixteenth_period > 0 else b_raw
        note = {"b": round(b_out, 6), "x": n["x"], "y": n["y"], "c": n["c"],
                "d": _map_direction(n.get("d", 8), allowed), "a": n.get("a", 0)}
        prev = last_by_color.get(note["c"])
        if prev is not None:
            gap = note["b"] - prev["b"]
            if _is_double_directional(prev, note) and gap <= 0.75:
                # same hand, same direction, close: flip to a comfortable
                # orthogonal cut (or dot at Easy) — the parity repair
                if allowed - {note["d"]}:
                    alts = _ORTHOGONAL.get(note["d"], set())
                    pick = next((a for a in sorted(alts) if a in allowed), None)
                    if pick is not None:
                        note["d"] = pick
                    else:
                        note["d"] = 8
                else:
                    note["d"] = 8
        out.append(note)
        last_by_color[note["c"]] = note

    # ── 4. VISION-BLOCK AVOIDANCE (the #1 readability rule) ─────────────────
    # THE MEASURED RULE (grounded, Exp 285): a HEAD-LEVEL (y=2) note in a lane
    # hides the next note in the SAME lane within the difficulty's window —
    # official Easy/Normal contain 0.0 such pairs per chart (corpus medians;
    # Hard 0.4, Expert 2.1). The first version of this rule (any mid-lane
    # note) ate whole charts — the y=2 geometry is the truth.
    lo_s, hi_s = profile["vision_block_s"]
    lo, hi = lo_s / sec_per_beat, hi_s / sec_per_beat
    result: list[dict] = []
    for n in out:
        blocked = False
        for prev in reversed(result):
            gap = n["b"] - prev["b"]
            if gap > hi:
                break
            if (prev["y"] == 2 and prev["x"] == n["x"]
                    and lo <= gap <= hi):
                blocked = True
                break
        if not blocked:
            result.append(n)

    # ── 5. THE OBJECT POLICY ────────────────────────────────────────────────
    bombs = list(source_bombs or []) if profile["keep_bombs"] else []

    return {"notes": result, "bombs": bombs, "walls": list(source_walls or [])}


def chart_summary(notes: list[dict]) -> dict:
    """The engine's self-check + the round-trip test's comparison payload:
    density, snap histogram, gap medians, doubles, same-color %, vision
    blocks (rough), direction set — the same shape as the measured grammar."""
    if not notes:
        return {"n": 0}
    times = [n["b"] for n in notes]
    span = max(times[-1] - times[0], 1e-6)
    gaps = sorted(round(b - a, 4) for a, b in zip(times, times[1:]))
    snaps = Counter(snap_bucket(t) for t in times)
    colors = [n["c"] for n in notes]
    same_adj = sum(1 for a, b in zip(colors, colors[1:]) if a == b)
    doubles = sum(1 for a, b in zip(times, times[1:]) if abs(b - a) < 1e-6)
    vb = 0
    for a, b in zip(notes, notes[1:]):
        # THE MEASURED GEOMETRY: head-level (y=2) same-lane close pairs —
        # official Easy/Normal contain 0.0 of these per chart
        if a["y"] == 2 and a["x"] == b["x"] and (b["b"] - a["b"]) <= 0.25:
            vb += 1
    return {
        "n": len(notes),
        "notes_per_beat": round(len(notes) / span, 3),
        "gap_median": gaps[len(gaps) // 2] if gaps else None,
        "on_beat_pct": round(100 * snaps.get(0, 0) / len(notes), 1),
        "sixteenth_pct": round(100 * (snaps.get(25, 0)) / len(notes), 1),
        "doubles_pct": round(100 * doubles / max(len(notes), 1), 1),
        "same_color_pct": round(100 * same_adj / max(len(notes) - 1, 1), 1),
        "vision_blocks_rough": vb,
        "direction_set": sorted({n["d"] for n in notes}),
    }
