import json
import os
import tempfile
import unittest

from tools.full_custom_song_pipeline import (
    _generate_no_arrows,
    _generate_one_saber,
    _generate_90_degree,
    generate_missing_mode_beatmaps,
    detect_song_modes,
    build_mode_mapping,
)

V2_NOTE = {"_time": 1.0, "_lineIndex": 0, "_lineLayer": 0, "_type": 1, "_cutDirection": 3}
V3_NOTE = {"b": 1.0, "x": 0, "y": 0, "c": 1, "d": 3}


class TestNoArrowsGenerator(unittest.TestCase):
    def test_v2_color_notes_become_dots(self):
        data = {"_version": "2.0.0", "_notes": [V2_NOTE]}
        gen = _generate_no_arrows(data)
        self.assertEqual(gen["_notes"][0]["_cutDirection"], 8)

    def test_v2_bombs_keep_direction(self):
        bomb = {"_time": 2.0, "_lineIndex": 1, "_lineLayer": 1, "_type": 3, "_cutDirection": 0}
        data = {"_version": "2.0.0", "_notes": [V2_NOTE, bomb]}
        gen = _generate_no_arrows(data)
        self.assertEqual(gen["_notes"][1]["_cutDirection"], 0)

    def test_v3_color_notes_become_dots(self):
        data = {"version": "3.2.0", "colorNotes": [V3_NOTE]}
        gen = _generate_no_arrows(data)
        self.assertEqual(gen["colorNotes"][0]["d"], 8)

    def test_input_not_mutated(self):
        data = {"_version": "2.0.0", "_notes": [V2_NOTE]}
        _generate_no_arrows(data)
        self.assertEqual(data["_notes"][0]["_cutDirection"], 3)


class TestOneSaberGenerator(unittest.TestCase):
    def test_recolors_all_notes_to_one_color(self):
        data = {"_version": "2.0.0", "_notes": [
            {"_time": 1.0, "_lineIndex": 0, "_lineLayer": 0, "_type": 0, "_cutDirection": 1},
            {"_time": 2.0, "_lineIndex": 1, "_lineLayer": 1, "_type": 1, "_cutDirection": 2},
        ]}
        gen = _generate_one_saber(data)
        self.assertTrue(all(n["_type"] == 0 for n in gen["_notes"]))

    def test_drops_simultaneous_notes(self):
        data = {"_version": "2.0.0", "_notes": [
            {"_time": 1.0, "_lineIndex": 0, "_lineLayer": 0, "_type": 0, "_cutDirection": 1},
            {"_time": 1.0, "_lineIndex": 3, "_lineLayer": 2, "_type": 1, "_cutDirection": 2},
        ]}
        gen = _generate_one_saber(data)
        self.assertEqual(len(gen["_notes"]), 1)

    def test_drops_close_same_cell_arrowed_notes(self):
        data = {"_version": "2.0.0", "_notes": [
            {"_time": 1.0, "_lineIndex": 0, "_lineLayer": 0, "_type": 0, "_cutDirection": 1},
            {"_time": 1.125, "_lineIndex": 0, "_lineLayer": 0, "_type": 0, "_cutDirection": 2},
        ]}
        gen = _generate_one_saber(data, min_gap=0.25)
        self.assertEqual(len(gen["_notes"]), 1)

    def test_keeps_dots_near_arrows(self):
        # A dot after an arrow in the same cell is fine (any swing hits it).
        data = {"_version": "2.0.0", "_notes": [
            {"_time": 1.0, "_lineIndex": 0, "_lineLayer": 0, "_type": 0, "_cutDirection": 1},
            {"_time": 1.125, "_lineIndex": 0, "_lineLayer": 0, "_type": 0, "_cutDirection": 8},
        ]}
        gen = _generate_one_saber(data, min_gap=0.25)
        self.assertEqual(len(gen["_notes"]), 2)

    def test_v3_recolors_to_single_saber(self):
        data = {"version": "3.2.0", "colorNotes": [
            {"b": 1.0, "x": 0, "y": 0, "c": 1, "d": 1},
            {"b": 1.0, "x": 2, "y": 2, "c": 0, "d": 2},
        ]}
        gen = _generate_one_saber(data)
        self.assertEqual(len(gen["colorNotes"]), 1)
        self.assertEqual(gen["colorNotes"][0]["c"], 0)

    def test_input_not_mutated(self):
        data = {"_version": "2.0.0", "_notes": [V2_NOTE]}
        _generate_one_saber(data)
        self.assertEqual(data["_notes"][0]["_type"], 1)


class Test90DegreeGenerator(unittest.TestCase):
    def test_v2_source_converted_to_v3(self):
        data = {"_version": "2.0.0", "_notes": [V2_NOTE]}
        gen = _generate_90_degree(data, cycle_beats=8, bpm=150.0)
        self.assertIn("colorNotes", gen)
        self.assertEqual(gen["version"], "3.2.0")
        self.assertEqual(gen["bpmEvents"][0]["m"], 150.0)

    def test_rotation_events_alternate_and_span_map(self):
        data = {"_version": "2.0.0", "_notes": [
            {"_time": 2.0, "_lineIndex": 0, "_lineLayer": 0, "_type": 0, "_cutDirection": 0},
            {"_time": 100.0, "_lineIndex": 0, "_lineLayer": 0, "_type": 0, "_cutDirection": 0},
        ]}
        gen = _generate_90_degree(data, cycle_beats=8)
        events = gen["rotationEvents"]
        self.assertEqual(events[0]["b"], 2.0)
        self.assertEqual(events[0]["r"], 90)
        self.assertEqual(events[1]["r"], -90)
        # Events span from first note through the end of the map.
        self.assertGreaterEqual(events[-1]["b"], 100.0)

    def test_v3_data_preserved(self):
        data = {"version": "3.2.0", "colorNotes": [
            {"b": 1.0, "x": 0, "y": 0, "c": 1, "d": 1},
            {"b": 5.0, "x": 1, "y": 1, "c": 0, "d": 2},
        ]}
        gen = _generate_90_degree(data, cycle_beats=4)
        self.assertEqual(len(gen["colorNotes"]), 2)
        self.assertEqual(gen["rotationEvents"][0], {"b": 1.0, "e": 0, "r": 90})
        self.assertEqual(gen["rotationEvents"][1]["r"], -90)

    def test_input_not_mutated(self):
        data = {"_version": "2.0.0", "_notes": [V2_NOTE]}
        _generate_90_degree(data)
        self.assertEqual(data["_notes"][0]["_cutDirection"], 3)


class TestGenerateMissingModeBeatmaps(unittest.TestCase):
    def _write_song(self, d, files):
        for name, content in files.items():
            with open(os.path.join(d, name), 'w') as fh:
                fh.write(content)

    def _v2(self, t, line=0, layer=0, typ=0, d=0):
        return json.dumps({"_version": "2.0.0", "_notes": [
            {"_time": t, "_lineIndex": line, "_lineLayer": layer, "_type": typ, "_cutDirection": d}
        ]})

    def test_generates_missing_modes_and_keeps_own(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_song(d, {
                "info.dat": json.dumps({"_songName": "Test", "_beatsPerMinute": 120.0}),
                "EasyStandard.dat": self._v2(1.0),
                "ExpertStandard.dat": self._v2(2.0),
                "90DegreeExpert.dat": self._v2(3.0),  # song's own — must not be overwritten
            })
            detected = detect_song_modes(d)
            enabled = build_mode_mapping(detected, None)
            generated = generate_missing_mode_beatmaps(d, detected, enabled, bpm=120.0)

            self.assertIn("EasyOneSaber.dat", generated)
            self.assertIn("EasyNoArrows.dat", generated)
            self.assertIn("Easy90Degree.dat", generated)
            # Expert has its own 90Degree file → not regenerated.
            self.assertNotIn("Expert90Degree.dat", generated)
            self.assertTrue(os.path.exists(os.path.join(d, "90DegreeExpert.dat")))

    def test_no_generation_when_modes_present(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_song(d, {
                "info.dat": json.dumps({"_songName": "Test"}),
                "EasyStandard.dat": self._v2(1.0),
                "EasyOneSaber.dat": self._v2(2.0),
                "EasyNoArrows.dat": self._v2(3.0),
                "Easy90Degree.dat": self._v2(4.0),
            })
            detected = detect_song_modes(d)
            enabled = build_mode_mapping(detected, None)
            generated = generate_missing_mode_beatmaps(d, detected, enabled)
            self.assertEqual(generated, [])

    def test_skips_difficulties_without_standard_source(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_song(d, {
                "info.dat": json.dumps({"_songName": "Test"}),
                "EasyStandard.dat": self._v2(1.0),
            })
            detected = detect_song_modes(d)
            enabled = build_mode_mapping(detected, None)
            generated = generate_missing_mode_beatmaps(d, detected, enabled)
            self.assertTrue(all(f.startswith("Easy") for f in generated))


if __name__ == '__main__':
    unittest.main()
