"""
test_difficulty_engine.py — M15: the descent engine's unit + round-trip tests.

The round-trip acceptance (plan §5): regenerate a lower difficulty from an
official song's own Expert+ chart and verify the result lands inside the
MEASURED official bands (KB: official-difficulty-grammar) with zero vision
blocks. Hardware-env gated (needs the dump) like the existing corpus tests;
the pure-logic tests below run everywhere, hermetically.
"""

import json
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from difficulty_engine import PROFILES, chart_summary, descend  # noqa: E402

DUMP_LEVELS = Path("/workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData")
HAS_DUMP = DUMP_LEVELS.is_dir()

# note time/spatial conventions used by the fixtures
def n(b, x=1, y=1, c=0, d=1):
    return {"b": b, "x": x, "y": y, "c": c, "d": d}


# ─────────────────────────────────────────────────────────────────────────────
# Pure logic (hermetic)
# ─────────────────────────────────────────────────────────────────────────────

class TestSelection:
    def test_descend_never_increases_density(self):
        src = [n(b=i * 0.25, c=i % 2) for i in range(400)]  # 16ths stream
        out = descend(src, bpm=120, difficulty="Easy")
        assert len(out["notes"]) < len(src)
        s = chart_summary(out["notes"])
        # Easy's measured envelope: 0.49–0.86 notes/beat
        assert 0.3 <= s["notes_per_beat"] <= 1.0

    def test_easy_lives_on_whole_beats(self):
        src = [n(b=i * 0.25, c=i % 2) for i in range(400)]
        out = descend(src, bpm=120, difficulty="Easy")
        s = chart_summary(out["notes"])
        # the snap ladder: Easy is ~87% on-beat; at minimum no sixteenth spam
        assert s["on_beat_pct"] >= 60
        assert s["sixteenth_pct"] <= 5

    def test_hard_uses_eighths(self):
        src = [n(b=i * 0.25, c=i % 2) for i in range(400)]
        for diff, min_density in (("Normal", 0.5), ("Hard", 0.9)):
            out = descend(src, bpm=120, difficulty=diff)
            s = chart_summary(out["notes"])
            assert s["notes_per_beat"] >= min_density, f"{diff} too sparse: {s}"

    def test_selection_preserves_color_cadence(self):
        # a strictly alternating source stays alternating
        src = [n(b=i * 0.5, c=i % 2) for i in range(200)]
        out = descend(src, bpm=120, difficulty="Easy")
        colors = [x["c"] for x in out["notes"]]
        same = sum(1 for a, b in zip(colors, colors[1:]) if a == b)
        assert same <= 0.5 * max(len(colors) - 1, 1)

    def test_output_never_vision_blocks(self):
        # mid-lane wall of notes: the next note always behind the blocker
        src = [n(b=i * 0.25, x=2, c=i % 2) for i in range(400)]
        for diff in ("Easy", "Normal", "Hard"):
            out = descend(src, bpm=120, difficulty=diff)
            assert chart_summary(out["notes"])["vision_blocks_rough"] == 0, diff

    def test_gap_floor_respected(self):
        src = [n(b=i * 0.25, c=i % 2) for i in range(400)]
        for diff in ("Easy", "Normal", "Hard"):
            prof = PROFILES[diff]
            out = descend(src, bpm=120, difficulty=diff)
            times = [x["b"] for x in out["notes"]]
            gaps = [b - a for a, b in zip(times, times[1:])]
            if gaps:
                assert min(gaps) >= prof["gap_floor_beats"] / 2 - 1e-6, \
                    f"{diff}: gap {min(gaps)} below half-floor"

    def test_bombs_stripped_for_lower_difficulties(self):
        src = [n(b=i, c=i % 2) for i in range(50)]
        bombs = [{"b": 4.0}, {"b": 8.0}]
        out = descend(src, bpm=120, difficulty="Easy",
                      source_bombs=bombs, source_walls=[{"b": 2.0}])
        assert out["bombs"] == []          # measured official median: 0
        assert out["walls"] == [{"b": 2.0}]  # walls preserved (official style)
        e_out = descend(src, bpm=120, difficulty="Expert", source_bombs=bombs)
        assert len(e_out["bombs"]) == 2    # Expert keeps them


class TestDirectionPolicy:
    def test_easy_directions_in_allowed_set(self):
        # diagonals + up cuts in the source
        src = [n(b=i, c=i % 2, d=[4, 5, 6, 7, 0][i % 5]) for i in range(100)]
        out = descend(src, bpm=120, difficulty="Easy")
        for note in out["notes"]:
            assert note["d"] in PROFILES["Easy"]["allowed_directions"]

    def test_double_directional_repaired(self):
        # same hand, same direction, close together (the wrist crusher)
        src = [n(b=0, c=0, d=1), n(b=0.25, c=0, d=1), n(b=0.5, c=0, d=1)]
        out = descend(src, bpm=120, difficulty="Hard")
        dirs = [(x["b"], x["d"]) for x in out["notes"]]
        for (b1, d1), (b2, d2) in zip(dirs, dirs[1:]):
            if b2 - b1 <= 0.5:
                assert d1 != d2, f"double-directional survived: {dirs}"

    def test_note_times_never_invented(self):
        src = [n(b=i * 0.5, c=i % 2) for i in range(100)]
        src_times = {x["b"] for x in src}
        out = descend(src, bpm=120, difficulty="Normal")
        assert all(x["b"] in src_times for x in out["notes"])

    def test_source_ordering_is_musical_not_front_loaded(self):
        # 400 notes; selection must span the whole chart, not the first N
        src = [n(b=i * 0.25, c=i % 2) for i in range(400)]
        out = descend(src, bpm=120, difficulty="Easy")
        times = [x["b"] for x in out["notes"]]
        assert times[-1] > 0.9 * src[-1]["b"]   # reaches the song's end


# ─────────────────────────────────────────────────────────────────────────────
# The round-trip acceptance (gated on the local dump — the official corpus)
# ─────────────────────────────────────────────────────────────────────────────

def _read_official_chart(slot_path: Path, diff: str) -> tuple[list[dict], list, list] | None:
    import gzip

    import UnityPy
    env = UnityPy.load(str(slot_path))
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            d = obj.read(check_read=False)
            if d.m_Name.endswith(f"{diff}.beatmap.gz"):
                raw = (d.m_Script.encode("utf-8", "surrogateescape")
                       if isinstance(d.m_Script, str) else d.m_Script)
                bm = json.loads(gzip.decompress(raw))
                dat = bm.get("colorNotesData") or []
                defaults = {"x": 0, "y": 0, "c": 0, "d": 8, "a": 0}
                notes = []
                for nn in bm.get("colorNotes") or []:
                    row = dict(defaults)
                    i = nn.get("i", 0)
                    if 0 <= i < len(dat) and isinstance(dat[i], dict):
                        row.update(dat[i])
                    notes.append({"b": float(nn.get("b", 0)), "x": row["x"],
                                  "y": row["y"], "c": row["c"], "d": row["d"]})
                notes.sort(key=lambda x: x["b"])
                return (notes, bm.get("bombNotes") or [], bm.get("obstacles") or [])
    return None


@pytest.mark.skipif(not HAS_DUMP, reason="requires the local dump (hardware env)")
class TestOfficialRoundTrip:
    """THE acceptance test (plan §5): descend official Expert+ charts to
    Easy/Normal/Hard and land inside the MEASURED official bands."""

    SLOTS = ["TruthHurts", "2beloved", "aboutdamntime", "startmeup", "100bills"]

    def test_descended_charts_match_official_bands(self):
        results = {}
        for slot in self.SLOTS:
            path = DUMP_LEVELS / slot
            if not path.exists():
                continue
            ep = _read_official_chart(path, "ExpertPlus")
            if not ep:
                continue
            notes, bombs, walls = ep
            if len(notes) < 100:
                continue
            for diff in ("Easy", "Normal", "Hard"):
                out = descend(notes, bpm=120, difficulty=diff,
                             source_bombs=bombs, source_walls=walls)
                s = chart_summary(out["notes"])
                band = {"Easy": (0.30, 1.05), "Normal": (0.45, 1.55),
                        "Hard": (0.70, 2.40)}[diff]
                results[(slot, diff)] = s
                # inside (or sparser than) the measured envelope — never denser
                assert s["notes_per_beat"] <= band[1] + 0.15, \
                    f"{slot}/{diff}: {s['notes_per_beat']} > band {band[1]}"
                # no vision blocks, ever (the official lower diffs measure 0)
                assert s["vision_blocks_rough"] == 0, f"{slot}/{diff}: {s}"
                # the color cadence stays musical
                assert s["same_color_pct"] <= 60, f"{slot}/{diff}: {s}"
                # Easy directions stay in the allowed set
                if diff == "Easy":
                    assert set(s["direction_set"]) <= PROFILES["Easy"]["allowed_directions"]
        assert results, "no official charts found for the round trip"


# ─────────────────────────────────────────────────────────────────────────────
# The pipeline integration (Exp 286): fill_missing_standard_difficulties
# ─────────────────────────────────────────────────────────────────────────────

class TestFillIntegration:
    """The descent replaces the clone for missing Easy/Normal/Hard when a
    dense source (≥2 tiers up) exists; the clone remains the fallback."""

    def _make_map_dir(self, tmp_path, difficulties: dict[str, list[dict]]):
        import json as _json
        d = tmp_path / "map"
        d.mkdir(parents=True, exist_ok=True)
        info = {"_version": "3.3.0", "_songName": "T", "_songAuthorName": "A",
                "_beatsPerMinute": 120,
                "_difficultyBeatmapSets": [{"_beatmapCharacteristicName": "Standard",
                                            "_difficultyBeatmaps": [
                                                {"_difficulty": k, "_beatmapFilename": f"{k}.dat"}
                                                for k in difficulties]}]}
        (d / "Info.dat").write_text(_json.dumps(info))
        for diff, notes in difficulties.items():
            (d / f"{diff}.dat").write_text(_json.dumps({
                "version": "3.3.0",
                "colorNotes": notes, "bombNotes": [], "obstacles": []}))
        (d / "song.ogg").write_bytes(b"x")
        return d

    def _notes(self, count, quarter=0.25):
        """A dense alternating 16th stream on the raw 0.25 grid."""
        return [{"b": round(i * quarter, 4), "x": 1 + (i % 3), "y": i % 3,
                 "c": i % 2, "d": 1} for i in range(count)]

    def test_descent_fills_missing_from_dense_source(self, tmp_path):
        sys.path.insert(0, str(TOOLS))
        import full_custom_song_pipeline as fp
        # only ExpertPlus exists → Easy/Normal/Hard get DESCENDED (not cloned)
        d = self._make_map_dir(tmp_path, {"ExpertPlus": self._notes(600)})
        written = fp.fill_missing_standard_difficulties(str(d))
        assert set(written) >= {"Easy.dat", "Normal.dat", "Hard.dat"}
        out_notes = {}
        for diff in ("Easy", "Normal", "Hard", "ExpertPlus"):
            bm = json.loads((d / f"{diff}.dat").read_text())
            out_notes[diff] = bm["colorNotes"]
        # the ladder: monotonic density, all inside the official bands
        import difficulty_engine as de
        for diff, band in (("Easy", (0.3, 1.0)), ("Normal", (0.5, 1.5)),
                           ("Hard", (0.7, 2.2))):
            s = de.chart_summary(out_notes[diff])
            assert band[0] <= s["notes_per_beat"] <= band[1], f"{diff}: {s}"
            assert s["vision_blocks_rough"] == 0
        assert len(out_notes["Easy"]) < len(out_notes["Normal"]) < len(out_notes["Hard"])

    def test_clone_fallback_for_adjacent_only(self, tmp_path):
        """Only Normal exists → Easy is cloned (no 2-tier-up dense source)."""
        sys.path.insert(0, str(TOOLS))
        import full_custom_song_pipeline as fp
        d = self._make_map_dir(tmp_path, {"Normal": self._notes(200)})
        written = fp.fill_missing_standard_difficulties(str(d))
        assert "Easy.dat" in written
        easy = json.loads((d / "Easy.dat").read_text())["colorNotes"]
        normal = json.loads((d / "Normal.dat").read_text())["colorNotes"]
        assert easy == normal  # the clone: identical content

    def test_skip_descent_flag(self, tmp_path):
        sys.path.insert(0, str(TOOLS))
        import full_custom_song_pipeline as fp
        d = self._make_map_dir(tmp_path, {"ExpertPlus": self._notes(600)})
        written = fp.fill_missing_standard_difficulties(str(d), skip_descent=True)
        easy = json.loads((d / "Easy.dat").read_text())["colorNotes"]
        ep = json.loads((d / "ExpertPlus.dat").read_text())["colorNotes"]
        assert easy == ep  # the clone: E+ copied wholesale

    def test_existing_files_never_overwritten(self, tmp_path):
        sys.path.insert(0, str(TOOLS))
        import full_custom_song_pipeline as fp
        d = self._make_map_dir(tmp_path, {"ExpertPlus": self._notes(600),
                                          "Easy": self._notes(50)})
        written = fp.fill_missing_standard_difficulties(str(d))
        assert "Easy.dat" not in written
        easy = json.loads((d / "Easy.dat").read_text())["colorNotes"]
        assert len(easy) == 50

    def test_drifting_source_descends_in_true_beats(self, tmp_path):
        """The Beat Sage class (Exp 286): notes on a TRUE grid of ~88 BPM
        labeled with a 120 BPM claim — the modal 16th is 0.35 claimed-beats.
        The engine infers the grid and lands the official bands in TRUE beats
        while emitting the notes' original (claimed-grid) times."""
        sys.path.insert(0, str(TOOLS))
        import full_custom_song_pipeline as fp
        import difficulty_engine as de
        # 16th stream at the true tempo: b_true multiples of 0.25 → in
        # claimed units = multiples of 0.25 * 1.36
        scale = 1.36
        notes = [{"b": round(i * 0.25 * scale, 4), "x": 1 + (i % 3), "y": i % 2,
                  "c": i % 2, "d": 1} for i in range(600)]
        d = self._make_map_dir(tmp_path, {"ExpertPlus": notes})
        fp.fill_missing_standard_difficulties(str(d))
        codes, period = de.infer_grid([n["b"] for n in notes])
        assert 1.2 < period < 1.6          # the true beat period inferred
        easy = json.loads((d / "Easy.dat").read_text())["colorNotes"]
        # honest density: in TRUE beats the descent must land the Easy band
        s = de.chart_summary([{"b": n["b"] / period, "x": n["x"], "y": n["y"],
                               "c": n["c"], "d": n["d"]} for n in easy])
        assert 0.35 <= s["notes_per_beat"] <= 1.0, s
        # and the emitted times are the SOURCE's own (never rescaled)
        src_times = {n["b"] for n in notes}
        assert all(n["b"] in src_times for n in easy)
