#!/usr/bin/env python3
"""
measure_official_difficulty_grammar.py — M15 R1: measure the OFFICIAL
difficulty grammar from the game's own catalog (the ground truth corpus).

Reads every official slot bundle's Standard `.beatmap.gz` TextAssets,
reconstructs the notes, and computes per-difficulty statistics:

  Density    notes/beat (the engine's primary unit), est. notes/sec, peak
  Timing     inter-note gaps (beats), rest cadence (>=2-beat gaps), snap
             histogram (on-beat / offbeat-eighth / sixteenth / other)
  Patterning doubles rate (same-tick pairs), color alternation
             (same-color-adjacent fraction), cut-direction histogram,
             lane/layer spread, vision-block geometry (same-lane close pairs)
  Objects    bombs + walls per difficulty

The official beatmap storage is SPARSE-COLUMNAR: colorNotes carry {b, i}
(indexing colorNotesData) and each data row OMITS fields that equal their
defaults (verified empirically, Exp 285: fixed defaults x=0/y=0/c=0/d=8
reproduce the natural L/R alternation + even lane spread; a carry-forward
reading produced a nonsense 100%-same-color sequence).

Output: official_difficulty_grammar.json (aggregates ONLY — no note data
from the game is stored) + a printed summary. Regenerable from any dump or
game_data cache; the JSON stays gitignored (regenerable), the SCRIPT ships.

Usage:
    python3 development/scripts/measure_official_difficulty_grammar.py \
        /workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData [out.json]
"""

from __future__ import annotations

import gzip
import json
import sys
from collections import Counter
from pathlib import Path

import UnityPy

DIFFS = ["Easy", "Normal", "Hard", "Expert", "ExpertPlus"]
# Fixed field defaults for the sparse colorNotesData encoding (verified Exp 285)
DEFAULTS = {"x": 0, "y": 0, "c": 0, "d": 8, "a": 0}
# V3/V4 cut-direction names (d values)
DIRECTIONS = {0: "up", 1: "down", 2: "left", 3: "right", 4: "upleft",
              5: "upright", 6: "downleft", 7: "downright", 8: "any/dot"}


def reconstruct_notes(beatmap: dict) -> list[dict]:
    """colorNotes[{b,i}] + sparse colorNotesData[{x?,y?,c?,d?,a?}] →
    full notes with defaults applied for omitted fields."""
    dat = beatmap.get("colorNotesData") or []
    out = []
    for n in beatmap.get("colorNotes") or []:
        row = dict(DEFAULTS)
        i = n.get("i", 0)
        if 0 <= i < len(dat) and isinstance(dat[i], dict):
            row.update(dat[i])
        out.append({"b": float(n.get("b", 0)), "x": row["x"], "y": row["y"],
                    "c": row["c"], "d": row["d"]})
    out.sort(key=lambda n: n["b"])
    return out


def snap_category(beat_time: float) -> str:
    frac = beat_time % 1.0
    if frac < 1e-6 or frac > 1.0 - 1e-6:
        return "on_beat"
    if abs(frac - 0.5) < 1e-6:
        return "offbeat_eighth"
    if abs(frac - 0.25) < 1e-6 or abs(frac - 0.75) < 1e-6:
        return "sixteenth"
    return "other"


def chart_stats(notes: list[dict], bombs: int, walls: int) -> dict:
    s: dict = {"n_notes": len(notes), "bombs": bombs, "walls": walls}
    if not notes:
        return s
    times = [n["b"] for n in notes]
    span = times[-1] - times[0]
    s["span_beats"] = round(span, 2)
    s["notes_per_beat"] = round(len(notes) / max(span, 1.0), 4)
    # gaps
    gaps = [round(b - a, 4) for a, b in zip(times, times[1:])]
    gaps_sorted = sorted(gaps)
    def pct(p):
        return gaps_sorted[min(len(gaps_sorted) - 1, int(p * len(gaps_sorted)))]
    if gaps:
        s["gap_min"] = gaps_sorted[0]
        s["gap_median"] = pct(0.5)
        s["gap_p90"] = pct(0.9)
        s["rests_ge2beats"] = sum(1 for g in gaps if g >= 2.0)
        s["rests_ge4beats"] = sum(1 for g in gaps if g >= 4.0)
    # snap histogram
    snaps = Counter(snap_category(t) for t in times)
    s["snap"] = {k: snaps.get(k, 0) for k in
                 ("on_beat", "offbeat_eighth", "sixteenth", "other")}
    # doubles (same-tick consecutive pairs)
    doubles = sum(1 for a, b in zip(times, times[1:]) if abs(b - a) < 1e-6)
    s["doubles"] = doubles
    # color alternation
    colors = [n["c"] for n in notes]
    same_adj = sum(1 for a, b in zip(colors, colors[1:]) if a == b)
    s["same_color_adjacent_pct"] = round(100 * same_adj / max(len(colors) - 1, 1), 1)
    # directions + lanes/layers
    dirs = Counter(n["d"] for n in notes)
    s["directions"] = {DIRECTIONS.get(k, k): v for k, v in sorted(dirs.items())}
    s["lane_spread"] = dict(sorted(Counter(n["x"] for n in notes).items()))
    s["layer_spread"] = dict(sorted(Counter(n["y"] for n in notes).items()))
    # vision blocks (first-pass geometry): consecutive notes, same lane,
    # close in time, and the FRONT note at head level (y=2) — the classic
    # "you can't see the next note" shape
    vb = 0
    for a, b in zip(notes, notes[1:]):
        if b["x"] == a["x"] and (b["b"] - a["b"]) <= 0.25 and a["y"] == 2:
            vb += 1
    s["vision_blocks_rough"] = vb
    # peak window (beats): max notes in any 8-beat window (2 measures)
    if times:
        best = left = 0
        for right in range(len(times)):
            while times[right] - times[left] > 8.0:
                left += 1
            best = max(best, right - left + 1)
        s["peak_notes_per_8beats"] = best
    return s


def measure(levels_dir: str) -> dict:
    root = Path(levels_dir)
    slots = sorted(p for p in root.iterdir() if p.is_file() and not p.name.startswith("."))
    per_diff: dict[str, list[dict]] = {d: [] for d in DIFFS}
    songs = 0
    for slot_path in slots:
        try:
            env = UnityPy.load(str(slot_path))
        except Exception:
            continue
        texts = {}
        for obj in env.objects:
            if obj.type.name == "TextAsset":
                d = obj.read(check_read=False)
                name = d.m_Name
                for diff in DIFFS:
                    if diff == "Expert" and "ExpertPlus" in name:
                        continue
                    if diff in name and name.endswith(".beatmap.gz"):
                        raw = (d.m_Script.encode("utf-8", "surrogateescape")
                               if isinstance(d.m_Script, str) else d.m_Script)
                        try:
                            texts[diff] = json.loads(gzip.decompress(raw))
                        except Exception:
                            pass
        if not texts:
            continue
        songs += 1
        for diff, bm in texts.items():
            notes = reconstruct_notes(bm)
            bombs = len(bm.get("bombNotes") or [])
            walls = len(bm.get("obstacles") or [])
            per_diff[diff].append(chart_stats(notes, bombs, walls))
    return {"songs_measured": songs, "per_difficulty": per_diff}


def aggregate(per_diff: dict) -> dict:
    import statistics as st
    out = {}
    for diff, stats in per_diff.items():
        if not stats:
            continue
        def med(key):
            def get(s, key):
                # dotted keys walk into sub-dicts (e.g. "snap.on_beat")
                obj = s
                for part in key.split("."):
                    obj = obj.get(part) if isinstance(obj, dict) else None
                    if obj is None:
                        return None
                return obj
            vals = [get(s, key) for s in stats]
            vals = [v for v in vals if v is not None]
            return round(st.median(vals), 3) if vals else None
        def p(key, q):
            def get(s, key):
                obj = s
                for part in key.split("."):
                    obj = obj.get(part) if isinstance(obj, dict) else None
                    if obj is None:
                        return None
                return obj
            vals = sorted(get(s, key) for s in stats)
            vals = [v for v in vals if v is not None]
            return round(vals[min(len(vals) - 1, int(q * len(vals)))], 3) if vals else None
        agg = {
            "songs": len(stats),
            "notes_median": med("n_notes"),
            "notes_per_beat_median": med("notes_per_beat"),
            "notes_per_beat_p10": p("notes_per_beat", 0.10),
            "notes_per_beat_p90": p("notes_per_beat", 0.90),
            "gap_min_median": med("gap_min"),
            "gap_median": med("gap_median"),
            "gap_p90_median": med("gap_p90"),
            "rests_ge2beats_median": med("rests_ge2beats"),
            "doubles_median": med("doubles"),
            "doubles_p90": p("doubles", 0.90),
            "same_color_adjacent_pct_median": med("same_color_adjacent_pct"),
            "vision_blocks_rough_median": med("vision_blocks_rough"),
            "peak_notes_per_8beats_median": med("peak_notes_per_8beats"),
            "bombs_median": med("bombs"),
            "walls_median": med("walls"),
            "snap_on_beat_median": med("snap.on_beat"),
        }
        # snap + directions: mean fractions
        n_total = sum(s["n_notes"] for s in stats if s.get("n_notes"))
        if n_total:
            for key in ("on_beat", "offbeat_eighth", "sixteenth", "other"):
                agg[f"snap_{key}_mean_pct"] = round(
                    100 * sum(s["snap"].get(key, 0) for s in stats) / n_total, 1)
            dd = Counter()
            for s in stats:
                for k, v in s.get("directions", {}).items():
                    dd[k] += v
            top = dd.most_common(4)
            agg["top_directions"] = {k: f"{100*v/n_total:.0f}%" for k, v in top}
        out[diff] = agg
    return out


def main() -> int:
    levels_dir = sys.argv[1] if len(sys.argv) > 1 else \
        "/workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData"
    out_path = sys.argv[2] if len(sys.argv) > 2 else \
        "official_difficulty_grammar.json"
    print(f"Measuring the official catalog: {levels_dir}")
    result = measure(levels_dir)
    agg = aggregate(result["per_difficulty"])
    doc = {"corpus": result["songs_measured"], "levels_dir": levels_dir,
           "aggregates": agg, "raw": result["per_difficulty"]}
    Path(out_path).write_text(json.dumps(doc, indent=1))
    print(f"\nCorpus: {result['songs_measured']} songs × 5 difficulties\n")
    print(f"{'':14s} {'Easy':>8s} {'Normal':>8s} {'Hard':>8s} {'Expert':>8s} {'Expert+':>8s}")
    rows = [
        ("notes/beat", "notes_per_beat_median"),
        ("notes (med)", "notes_median"),
        ("gap med (bts)", "gap_median"),
        ("gap p90 (bts)", "gap_p90_median"),
        ("doubles (med)", "doubles_median"),
        ("same-color %", "same_color_adjacent_pct_median"),
        ("on-beat %", "snap_on_beat_median"),
        ("peak/8beats", "peak_notes_per_8beats_median"),
        ("bombs (med)", "bombs_median"),
        ("walls (med)", "walls_median"),
        ("vision-blk", "vision_blocks_rough_median"),
    ]
    for label, key in rows:
        vals = [agg.get(d, {}).get(key) for d in DIFFS]
        print(f"{label:14s} " + " ".join(f"{v if v is not None else '—':>8}" for v in vals))
    print(f"\nTop directions (Expert): {agg.get('Expert', {}).get('top_directions')}")
    print(f"\n✅ Written: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
