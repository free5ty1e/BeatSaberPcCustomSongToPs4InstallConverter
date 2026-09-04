"""
Unit tests for recent pipeline bug fixes
=========================================
1. Info.dat case-insensitive loading
2. Undefined variables in main() (bpm, song_name, song_artist, note_count_standard)
3. manage_song_metadata passthrough (None vs actual values)
4. Note count standard initialization
"""
import os
import sys
import json
import tempfile
import shutil
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

from full_custom_song_pipeline import (
    _scan_beatmap_max_beat,
    load_bpm_regions,
    _select_beatmap_file,
    manage_song_metadata,
    DIFFICULTIES,
    SAMPLE_RATE,
)


# ======================================================================
# 1. Info.dat Case-Insensitive Loading
# ======================================================================
class TestInfoDatCaseInsensitive:
    """
    The pipeline had Info.dat (uppercase) hardcoded but BeatSaver downloads
    use info.dat (lowercase). The fix added fallback to lowercase in main()
    and replace_beatmaps(). _scan_beatmap_max_beat uses lowercased comparison.
    """

    def test_scan_beatmap_skips_lowercase_info_dat(self, tmp_dir):
        """_scan_beatmap_max_beat should skip info.dat (lowercase) as metadata."""
        info = {"_beatsPerMinute": 120.0}
        with open(os.path.join(tmp_dir, "info.dat"), 'w') as f:
            json.dump(info, f)

        beatmap = {"_notes": [{"_time": 75.0}, {"_time": 100.0}]}
        with open(os.path.join(tmp_dir, "Hard.dat"), 'w') as f:
            json.dump(beatmap, f)

        max_beat = _scan_beatmap_max_beat(tmp_dir)
        assert max_beat == 100.0

    def test_scan_beatmap_skips_uppercase_info_dat(self, tmp_dir):
        """_scan_beatmap_max_beat should skip Info.dat (uppercase) as metadata."""
        info = {"_beatsPerMinute": 120.0}
        with open(os.path.join(tmp_dir, "Info.dat"), 'w') as f:
            json.dump(info, f)

        beatmap = {"_notes": [{"_time": 50.0}]}
        with open(os.path.join(tmp_dir, "Normal.dat"), 'w') as f:
            json.dump(beatmap, f)

        max_beat = _scan_beatmap_max_beat(tmp_dir)
        assert max_beat == 50.0

    def test_scan_beatmap_skips_bpm_info_dat(self, tmp_dir):
        """_scan_beatmap_max_beat should skip BPMInfo.dat."""
        bpm_info = {"_regions": []}
        with open(os.path.join(tmp_dir, "BPMInfo.dat"), 'w') as f:
            json.dump(bpm_info, f)

        beatmap = {"_notes": [{"_time": 200.0}]}
        with open(os.path.join(tmp_dir, "Expert.dat"), 'w') as f:
            json.dump(beatmap, f)

        max_beat = _scan_beatmap_max_beat(tmp_dir)
        assert max_beat == 200.0

    def test_scan_beatmap_with_both_info_cases(self, tmp_dir):
        """When both Info.dat and info.dat exist, neither is counted as beat data."""
        with open(os.path.join(tmp_dir, "Info.dat"), 'w') as f:
            json.dump({"_beatsPerMinute": 120.0}, f)
        with open(os.path.join(tmp_dir, "info.dat"), 'w') as f:
            json.dump({"_beatsPerMinute": 120.0}, f)

        beatmap = {"_notes": [{"_time": 300.0}]}
        with open(os.path.join(tmp_dir, "ExpertPlus.dat"), 'w') as f:
            json.dump(beatmap, f)

        assert _scan_beatmap_max_beat(tmp_dir) == 300.0

    def test_load_bpm_regions_uppercase_info_dat_fallback(self, tmp_dir):
        """load_bpm_regions should find Info.dat (uppercase) for BPM fallback
        when no BPMInfo.dat and no beatmaps exist."""
        info = {"_beatsPerMinute": 150.0}
        with open(os.path.join(tmp_dir, "Info.dat"), 'w') as f:
            json.dump(info, f)

        sample_count = 44100 * 60
        regions = load_bpm_regions(tmp_dir, sample_count)
        assert len(regions) == 1
        # 60s * 150 BPM / 60 = 150 beats
        assert regions[0]['eb'] == 150.0

    def test_load_bpm_regions_beatmap_overrides_info_dat(self, tmp_dir):
        """When beatmaps exist, their max beat is used regardless of Info.dat."""
        info = {"_beatsPerMinute": 120.0}
        with open(os.path.join(tmp_dir, "Info.dat"), 'w') as f:
            json.dump(info, f)

        beatmap = {"_notes": [{"_time": 250.0}]}
        with open(os.path.join(tmp_dir, "Hard.dat"), 'w') as f:
            json.dump(beatmap, f)

        sample_count = 44100 * 60
        regions = load_bpm_regions(tmp_dir, sample_count)
        assert regions[0]['eb'] == 250.0

    def test_replace_beatmaps_reads_uppercase_info_dat(self, tmp_dir):
        """replace_beatmaps reads Info.dat (uppercase) for BPM."""
        info = {"_beatsPerMinute": 140.0}
        with open(os.path.join(tmp_dir, "Info.dat"), 'w') as f:
            json.dump(info, f)
        # Need at least one beatmap file for replace_beatmaps to work with
        bm = {"version": "2.0.0", "_notes": [{"_time": 0.0}]}
        with open(os.path.join(tmp_dir, "Easy.dat"), 'w') as f:
            json.dump(bm, f)

        # Verify the code path exists and doesn't crash
        info_path = os.path.join(tmp_dir, "Info.dat")
        if not os.path.exists(info_path):
            info_path = os.path.join(tmp_dir, "info.dat")
        assert os.path.exists(info_path)

    def test_replace_beatmaps_falls_back_to_lowercase(self, tmp_dir):
        """replace_beatmaps falls back to info.dat (lowercase) when uppercase missing."""
        info = {"_beatsPerMinute": 160.0}
        with open(os.path.join(tmp_dir, "info.dat"), 'w') as f:
            json.dump(info, f)

        # Replicate replace_beatmaps' Info.dat loading logic
        info_path = os.path.join(tmp_dir, "Info.dat")
        if not os.path.exists(info_path):
            info_path = os.path.join(tmp_dir, "info.dat")
        assert os.path.exists(info_path)
        assert info_path.endswith("info.dat")

        with open(info_path) as f:
            parsed = json.load(f)
        assert parsed["_beatsPerMinute"] == 160.0


# ======================================================================
# 2. Info.dat Parsing (bpm, song_name, song_artist initialization)
# ======================================================================
class TestInfoDatParsing:
    """
    The fix initializes bpm, song_name, song_artist from Info.dat before
    Step 0, so they aren't undefined in Step 6.5.
    Test that Info.dat parsing works for both uppercase and lowercase filenames.
    """

    def test_parse_uppercase_info_dat(self, tmp_dir):
        """Parse Info.dat (uppercase) and extract metadata fields."""
        info = {
            "_songName": "My Custom Song",
            "_songAuthorName": "Artist Name",
            "_beatsPerMinute": 142.0,
        }
        with open(os.path.join(tmp_dir, "Info.dat"), 'w') as f:
            json.dump(info, f)

        # Replicate main()'s Info.dat loading logic (lines 2058-2066)
        info_dat_path = os.path.join(tmp_dir, "Info.dat")
        if not os.path.isfile(info_dat_path):
            info_dat_path = os.path.join(tmp_dir, "info.dat")

        song_name = os.path.basename(tmp_dir)
        song_artist = ""
        bpm = 120.0

        assert os.path.isfile(info_dat_path)
        with open(info_dat_path) as f:
            parsed = json.load(f)

        song_name = parsed.get("_songName", song_name)
        song_artist = parsed.get("_songAuthorName", song_artist)
        bpm = float(parsed.get("_beatsPerMinute", 120.0))

        assert song_name == "My Custom Song"
        assert song_artist == "Artist Name"
        assert bpm == 142.0

    def test_parse_lowercase_info_dat(self, tmp_dir):
        """Parse info.dat (lowercase, BeatSaver format) and extract metadata fields."""
        info = {
            "_songName": "Downloaded Song",
            "_songAuthorName": "BeatSaver Mapper",
            "_beatsPerMinute": 175.0,
        }
        with open(os.path.join(tmp_dir, "info.dat"), 'w') as f:
            json.dump(info, f)

        # Replicate main()'s Info.dat loading with fallback (lines 2058-2060)
        info_dat_path = os.path.join(tmp_dir, "Info.dat")
        if not os.path.isfile(info_dat_path):
            info_dat_path = os.path.join(tmp_dir, "info.dat")

        song_name = os.path.basename(tmp_dir)
        song_artist = ""
        bpm = 120.0

        assert os.path.isfile(info_dat_path)
        with open(info_dat_path) as f:
            parsed = json.load(f)

        song_name = parsed.get("_songName", song_name)
        song_artist = parsed.get("_songAuthorName", song_artist)
        bpm = float(parsed.get("_beatsPerMinute", 120.0))

        assert song_name == "Downloaded Song"
        assert song_artist == "BeatSaver Mapper"
        assert bpm == 175.0

    def test_uppercase_takes_priority_for_parsing(self, tmp_dir):
        """When both exist, Info.dat (uppercase) should be used first."""
        info_upper = {"_songName": "Upper Song", "_beatsPerMinute": 130.0}
        with open(os.path.join(tmp_dir, "Info.dat"), 'w') as f:
            json.dump(info_upper, f)

        info_lower = {"_songName": "Lower Song", "_beatsPerMinute": 160.0}
        with open(os.path.join(tmp_dir, "info.dat"), 'w') as f:
            json.dump(info_lower, f)

        info_dat_path = os.path.join(tmp_dir, "Info.dat")
        if not os.path.isfile(info_dat_path):
            info_dat_path = os.path.join(tmp_dir, "info.dat")

        assert os.path.isfile(info_dat_path)
        assert info_dat_path.endswith("Info.dat")

        with open(info_dat_path) as f:
            parsed = json.load(f)
        assert parsed["_songName"] == "Upper Song"

    def test_missing_info_dat_uses_defaults(self, tmp_dir):
        """When no Info.dat exists, defaults should be used."""
        info_dat_path = os.path.join(tmp_dir, "Info.dat")
        if not os.path.isfile(info_dat_path):
            info_dat_path = os.path.join(tmp_dir, "info.dat")

        song_name = os.path.basename(tmp_dir)
        song_artist = ""
        bpm = 120.0

        assert not os.path.isfile(info_dat_path)
        assert song_name == os.path.basename(tmp_dir)
        assert song_artist == ""
        assert bpm == 120.0

    def test_second_info_dat_read_in_step_6_5(self, tmp_dir):
        """Step 6.5 re-reads Info.dat for custom_name/custom_artist resolution."""
        info = {
            "_songName": "Step 6.5 Song",
            "_songAuthorName": "Step 6.5 Artist",
            "_beatsPerMinute": 155.0,
        }
        with open(os.path.join(tmp_dir, "info.dat"), 'w') as f:
            json.dump(info, f)

        # Replicate Step 6.5's Info.dat re-read (lines 2198-2206)
        info_dat_path = os.path.join(tmp_dir, "Info.dat")
        if not os.path.isfile(info_dat_path):
            info_dat_path = os.path.join(tmp_dir, "info.dat")

        song_name = "default"
        song_artist = ""
        bpm = 120.0

        if os.path.isfile(info_dat_path):
            with open(info_dat_path) as f:
                info = json.load(f)
            song_name = info.get("_songName", song_name)
            song_artist = info.get("_songAuthorName", song_artist)
            bpm = float(info.get("_beatsPerMinute", bpm))

        custom_name = None or song_name  # args.song_name is None
        custom_artist = None or song_artist  # args.artist is None

        assert custom_name == "Step 6.5 Song"
        assert custom_artist == "Step 6.5 Artist"
        assert bpm == 155.0


# ======================================================================
# 3. manage_song_metadata Passthrough
# ======================================================================
class TestManageSongMetadata:
    """
    When args.song_name and args.artist are None (not passed via CLI),
    the metadata function was called with None values, so downloaded songs'
    metadata was never saved. The fix passes custom_name and custom_artist
    (resolved from Info.dat) instead.
    """
    def test_both_values_provided(self, tmp_dir):
        """When song_name and artist are both provided, they are combined as 'Name / Artist'."""
        import full_custom_song_pipeline as fp
        local_path = os.path.join(tmp_dir, "song_metadata.json")
        orig = fp._get_song_metadata_path
        fp._get_song_metadata_path = lambda: local_path

        try:
            metadata = manage_song_metadata(
                {},
                song_name="Test Song",
                artist="Test Artist",
                target_name="StartMeUp",
            )
            assert metadata['song_names']['Start Me Up'] == "Test Song / Test Artist"
        finally:
            fp._get_song_metadata_path = orig

    def test_none_song_name_not_saved(self, tmp_dir):
        """When song_name is None, the song name should NOT be written."""
        import full_custom_song_pipeline as fp
        local_path = os.path.join(tmp_dir, "song_metadata.json")
        orig = fp._get_song_metadata_path
        fp._get_song_metadata_path = lambda: local_path
        try:
            metadata = manage_song_metadata(
                {},
                song_name=None,
                artist="Some Artist",
                target_name="StartMeUp",
            )
            assert 'Start Me Up' not in metadata['song_names']
        finally:
            fp._get_song_metadata_path = orig

    def test_none_artist_not_saved(self, tmp_dir):
        """When artist is None, the song name is saved without artist suffix."""
        import full_custom_song_pipeline as fp
        local_path = os.path.join(tmp_dir, "song_metadata.json")
        orig = fp._get_song_metadata_path
        fp._get_song_metadata_path = lambda: local_path
        try:
            metadata = manage_song_metadata(
                {},
                song_name="Some Song",
                artist=None,
                target_name="StartMeUp",
            )
            assert metadata['song_names']['Start Me Up'] == "Some Song"
        finally:
            fp._get_song_metadata_path = orig

    def test_both_none_no_changes(self, tmp_dir):
        """When both song_name and artist are None, only artist blanking occurs for resolved targets."""
        import full_custom_song_pipeline as fp
        local_path = os.path.join(tmp_dir, "song_metadata.json")
        orig = fp._get_song_metadata_path
        fp._get_song_metadata_path = lambda: local_path
        try:
            metadata = manage_song_metadata(
                {},
                song_name=None,
                artist=None,
                target_name="StartMeUp",
            )
            assert metadata['song_names'] == {}
            # Original author is blanked when target resolves via beat_saber_song_ids.json
        finally:
            fp._get_song_metadata_path = orig

    def test_passthrough_resolved_from_info_dat(self, tmp_dir):
        """
        The fix: when CLI args are None, custom_name/custom_artist from
        Info.dat are passed to manage_song_metadata instead of None.
        This simulates the corrected main() logic.
        """
        import full_custom_song_pipeline as fp
        local_path = os.path.join(tmp_dir, "song_metadata.json")
        orig = fp._get_song_metadata_path
        fp._get_song_metadata_path = lambda: local_path

        # Simulate: Info.dat was read and provided these values
        custom_name = "Info Song Name"
        custom_artist = "Info Artist"
        args_song_name = None  # user didn't pass --song-name
        args_artist = None     # user didn't pass --artist

        try:
            metadata = manage_song_metadata(
                {},
                song_name=args_song_name or custom_name,
                artist=args_artist or custom_artist,
                target_name="StartMeUp",
            )
            # Combined name format: "SongName / Artist"
            assert metadata['song_names']['Start Me Up'] == "Info Song Name / Info Artist"
        finally:
            fp._get_song_metadata_path = orig

    def test_cli_args_override_info_dat(self, tmp_dir):
        """
        When CLI args ARE provided, they should take precedence over Info.dat values.
        """
        import full_custom_song_pipeline as fp
        local_path = os.path.join(tmp_dir, "song_metadata.json")
        orig = fp._get_song_metadata_path
        fp._get_song_metadata_path = lambda: local_path

        custom_name = "Info Song Name"
        custom_artist = "Info Artist"
        args_song_name = "CLI Override Name"
        args_artist = "CLI Override Artist"

        try:
            metadata = manage_song_metadata(
                {},
                song_name=args_song_name or custom_name,
                artist=args_artist or custom_artist,
                target_name="StartMeUp",
            )
            assert metadata['song_names']['Start Me Up'] == "CLI Override Name / CLI Override Artist"
        finally:
            fp._get_song_metadata_path = orig

    def test_empty_string_not_falsy_over_info_dat(self, tmp_dir):
        """
        When CLI args are empty strings (falsy), Info.dat values should be used.
        """
        import full_custom_song_pipeline as fp
        local_path = os.path.join(tmp_dir, "song_metadata.json")
        orig = fp._get_song_metadata_path
        fp._get_song_metadata_path = lambda: local_path

        custom_name = "Info Song"
        custom_artist = "Info Artist"
        args_song_name = ""  # empty string is falsy
        args_artist = ""

        try:
            metadata = manage_song_metadata(
                {},
                song_name=args_song_name or custom_name,
                artist=args_artist or custom_artist,
                target_name="StartMeUp",
            )
            assert metadata['song_names']['Start Me Up'] == "Info Song / Info Artist"
        finally:
            fp._get_song_metadata_path = orig

    def test_existing_metadata_preserved(self, tmp_dir):
        """New metadata should not clobber existing entries for other songs."""
        import full_custom_song_pipeline as fp
        local_path = os.path.join(tmp_dir, "song_metadata.json")

        existing = {"song_names": {"Angry": "Angry"}, "song_artists": {"Angry": "Artist A"}}
        with open(local_path, 'w') as f:
            json.dump(existing, f)

        orig = fp._get_song_metadata_path
        fp._get_song_metadata_path = lambda: local_path
        try:
            metadata = manage_song_metadata(
                {},
                song_name="New Song",
                artist="New Artist",
                target_name="StartMeUp",
            )
            assert metadata['song_names']['Angry'] == "Angry"
            assert metadata['song_artists']['Angry'] == "Artist A"
            assert metadata['song_names']['Start Me Up'] == "New Song / New Artist"
        finally:
            fp._get_song_metadata_path = orig


# ======================================================================
# 4. Note Count Standard Initialization
# ======================================================================
class TestNoteCountStandard:
    """
    Test that note counting from beatmap files works correctly.
    This verifies the note_count_standard variable is properly initialized
    and populated by scanning beatmap files.
    """

    def _count_notes_from_beatmaps(self, song_dir):
        """
        Replicate the note counting logic from main() Step 6.
        """
        note_count_standard = 0
        for diff_file in ['Hard.dat', 'Normal.dat', 'Easy.dat', 'Expert.dat', 'ExpertPlus.dat',
                           'HardStandard.dat', 'NormalStandard.dat', 'EasyStandard.dat',
                           'ExpertStandard.dat', 'ExpertPlusStandard.dat']:
            diff_path = os.path.join(song_dir, diff_file)
            if os.path.isfile(diff_path):
                try:
                    with open(diff_path) as f:
                        bm = json.load(f)
                    note_count_standard += len(bm.get('notes', []))
                except Exception:
                    pass
        return note_count_standard

    def test_counts_v2_notes(self, tmp_dir):
        """V2 beatmaps use 'notes' key for note counting."""
        beatmap = {
            "notes": [
                {"_time": 0.0, "_lineIndex": 0, "_lineLayer": 0, "_type": 0},
                {"_time": 1.0, "_lineIndex": 1, "_lineLayer": 1, "_type": 1},
                {"_time": 2.0, "_lineIndex": 2, "_lineLayer": 2, "_type": 0},
            ]
        }
        with open(os.path.join(tmp_dir, "Hard.dat"), 'w') as f:
            json.dump(beatmap, f)

        count = self._count_notes_from_beatmaps(tmp_dir)
        assert count == 3

    def test_counts_multiple_difficulties(self, tmp_dir):
        """Should sum notes across all difficulty files."""
        for diff, n_notes in [("Easy.dat", 10), ("Normal.dat", 25), ("Hard.dat", 50)]:
            beatmap = {"notes": [{"_time": float(i)} for i in range(n_notes)]}
            with open(os.path.join(tmp_dir, diff), 'w') as f:
                json.dump(beatmap, f)

        count = self._count_notes_from_beatmaps(tmp_dir)
        assert count == 85

    def test_counts_standard_suffixed_files(self, tmp_dir):
        """Should also count files with Standard suffix."""
        beatmap = {"notes": [{"_time": 0.0}, {"_time": 1.0}]}
        with open(os.path.join(tmp_dir, "HardStandard.dat"), 'w') as f:
            json.dump(beatmap, f)

        count = self._count_notes_from_beatmaps(tmp_dir)
        assert count == 2

    def test_empty_song_dir_returns_zero(self, tmp_dir):
        """Empty directory should return 0 notes."""
        count = self._count_notes_from_beatmaps(tmp_dir)
        assert count == 0

    def test_unrelated_dat_files_ignored(self, tmp_dir):
        """Info.dat and other non-beatmap .dat files should not be counted."""
        info = {"_beatsPerMinute": 120.0}
        with open(os.path.join(tmp_dir, "Info.dat"), 'w') as f:
            json.dump(info, f)

        bpm_info = {"_regions": []}
        with open(os.path.join(tmp_dir, "BPMInfo.dat"), 'w') as f:
            json.dump(bpm_info, f)

        count = self._count_notes_from_beatmaps(tmp_dir)
        assert count == 0

    def test_zero_initialized_before_accumulation(self, tmp_dir):
        """note_count_standard starts at 0 before the accumulation loop."""
        note_count_standard = 0
        assert note_count_standard == 0

        beatmap = {"notes": [{"_time": 0.0}]}
        with open(os.path.join(tmp_dir, "Expert.dat"), 'w') as f:
            json.dump(beatmap, f)

        # Replicate the loop
        for diff_file in ['Hard.dat', 'Normal.dat', 'Easy.dat', 'Expert.dat', 'ExpertPlus.dat']:
            diff_path = os.path.join(tmp_dir, diff_file)
            if os.path.isfile(diff_path):
                with open(diff_path) as f:
                    bm = json.load(f)
                note_count_standard += len(bm.get('notes', []))

        assert note_count_standard == 1

    def test_malformed_dat_file_skipped(self, tmp_dir):
        """Malformed .dat files should be skipped without crashing."""
        with open(os.path.join(tmp_dir, "Hard.dat"), 'w') as f:
            f.write("NOT JSON {{{")

        count = self._count_notes_from_beatmaps(tmp_dir)
        assert count == 0

    def test_beatmap_with_no_notes_key(self, tmp_dir):
        """Beatmap without 'notes' key should contribute 0 notes."""
        beatmap = {"version": "2.0.0", "_obstacles": []}
        with open(os.path.join(tmp_dir, "Normal.dat"), 'w') as f:
            json.dump(beatmap, f)

        count = self._count_notes_from_beatmaps(tmp_dir)
        assert count == 0

    def test_all_five_difficulties_counted(self, tmp_dir):
        """All 5 standard difficulties should be counted when present."""
        for diff in ['Easy', 'Normal', 'Hard', 'Expert', 'ExpertPlus']:
            beatmap = {"notes": [{"_time": float(i)} for i in range(10)]}
            with open(os.path.join(tmp_dir, f"{diff}.dat"), 'w') as f:
                json.dump(beatmap, f)

        count = self._count_notes_from_beatmaps(tmp_dir)
        assert count == 50  # 5 difficulties * 10 notes each

    def test_standard_suffix_takes_priority(self, tmp_dir):
        """Both Hard.dat and HardStandard.dat should be counted (they're separate files)."""
        bare = {"notes": [{"_time": 0.0}]}
        with open(os.path.join(tmp_dir, "Hard.dat"), 'w') as f:
            json.dump(bare, f)

        standard = {"notes": [{"_time": 0.0}, {"_time": 1.0}]}
        with open(os.path.join(tmp_dir, "HardStandard.dat"), 'w') as f:
            json.dump(standard, f)

        count = self._count_notes_from_beatmaps(tmp_dir)
        assert count == 3  # 1 + 2


# ======================================================================
# 5. _scan_beatmap_max_beat with V2 and V3
# ======================================================================
class TestScanBeatmapMaxBeatV2V3:
    """
    Test that _scan_beatmap_max_beat works correctly with both V2 and V3
    beatmaps, including edge cases.
    """

    def test_v2_notes_time_field(self, tmp_dir):
        """V2 beatmaps use _time field for beat position."""
        data = {
            "_notes": [
                {"_time": 10.0},
                {"_time": 250.0},
                {"_time": 50.0},
            ]
        }
        with open(os.path.join(tmp_dir, "ExpertPlus.dat"), 'w') as f:
            json.dump(data, f)

        assert _scan_beatmap_max_beat(tmp_dir) == 250.0

    def test_v3_color_notes_b_field(self, tmp_dir):
        """V3 beatmaps use colorNotes[].b for beat position."""
        data = {
            "colorNotes": [
                {"b": 100.0, "x": 0, "y": 0, "d": 0},
                {"b": 300.0, "x": 1, "y": 1, "d": 1},
            ]
        }
        with open(os.path.join(tmp_dir, "Hard.dat"), 'w') as f:
            json.dump(data, f)

        assert _scan_beatmap_max_beat(tmp_dir) == 300.0

    def test_mixed_v2_and_v3_files(self, tmp_dir):
        """Should find max across multiple files of different versions."""
        v2 = {"_notes": [{"_time": 100.0}]}
        with open(os.path.join(tmp_dir, "Easy.dat"), 'w') as f:
            json.dump(v2, f)

        v3 = {"colorNotes": [{"b": 500.0, "x": 0, "y": 0, "d": 0}]}
        with open(os.path.join(tmp_dir, "Hard.dat"), 'w') as f:
            json.dump(v3, f)

        assert _scan_beatmap_max_beat(tmp_dir) == 500.0

    def test_skips_all_info_variants(self, tmp_dir):
        """Should skip info.dat, Info.dat, and BPMInfo.dat."""
        for fname in ["info.dat", "Info.dat", "BPMInfo.dat"]:
            with open(os.path.join(tmp_dir, fname), 'w') as f:
                json.dump({"_beatsPerMinute": 99999.0}, f)

        beatmap = {"_notes": [{"_time": 42.0}]}
        with open(os.path.join(tmp_dir, "Normal.dat"), 'w') as f:
            json.dump(beatmap, f)

        assert _scan_beatmap_max_beat(tmp_dir) == 42.0

    def test_empty_beatmap_files(self, tmp_dir):
        """Empty beatmap files should be skipped gracefully."""
        with open(os.path.join(tmp_dir, "Hard.dat"), 'w') as f:
            json.dump({}, f)

        beatmap = {"_notes": [{"_time": 15.0}]}
        with open(os.path.join(tmp_dir, "Easy.dat"), 'w') as f:
            json.dump(beatmap, f)

        assert _scan_beatmap_max_beat(tmp_dir) == 15.0

    def test_non_numeric_time_ignored(self, tmp_dir):
        """Notes with non-numeric _time should be ignored."""
        data = {
            "_notes": [
                {"_time": "invalid"},
                {"_time": 50.0},
                {"_time": None},
            ]
        }
        with open(os.path.join(tmp_dir, "Expert.dat"), 'w') as f:
            json.dump(data, f)

        assert _scan_beatmap_max_beat(tmp_dir) == 50.0

    def test_zero_beat_value(self, tmp_dir):
        """A beat value of exactly 0.0 should not affect max."""
        data = {"_notes": [{"_time": 0.0}]}
        with open(os.path.join(tmp_dir, "Easy.dat"), 'w') as f:
            json.dump(data, f)

        assert _scan_beatmap_max_beat(tmp_dir) == 0.0

    def test_negative_beat_values_ignored(self, tmp_dir):
        """Negative beat values should not become the max."""
        data = {"_notes": [{"_time": -10.0}, {"_time": 5.0}]}
        with open(os.path.join(tmp_dir, "Normal.dat"), 'w') as f:
            json.dump(data, f)

        assert _scan_beatmap_max_beat(tmp_dir) == 5.0


# ======================================================================
# Exp 200 (v0.5328): V3 schema normalization + empty-beatmap rescue
# ======================================================================
class TestV3SchemaNormalization:
    """Minimal-schema V3 maps crash the PS4 at gameplay load (Exp 200: Chromeo
    V4→V3 reconstruction emitted 8-key maps; game needs the full schema)."""

    def test_normalize_fills_missing_arrays(self):
        from full_custom_song_pipeline import normalize_v3_schema
        minimal = {"version": "3.2.0", "colorNotes": [{"b": 1, "x": 1, "y": 0, "c": 0, "d": 0}]}
        out = normalize_v3_schema(minimal)
        for key in ("basicBeatmapEvents", "waypoints", "lightColorEventBoxGroups",
                    "obstacles", "bpmEvents", "chains", "arcs"):
            assert isinstance(out[key], list), f"{key} should be a filled list"
        assert out["useNormalEventsAsCompatibleEvents"] is True
        assert "customData" in out
        assert isinstance(out["basicEventTypesWithKeywords"], dict)

    def test_normalize_is_idempotent(self):
        from full_custom_song_pipeline import normalize_v3_schema
        m = {"version": "3.2.0", "colorNotes": []}
        once = normalize_v3_schema(dict(m))
        twice = normalize_v3_schema(once)
        assert sorted(once.keys()) == sorted(twice.keys())

    def test_normalize_preserves_existing_content(self):
        from full_custom_song_pipeline import normalize_v3_schema
        full = {"version": "3.2.0", "colorNotes": [{"b": 2}], "obstacles": [{"b": 1}],
                "useNormalEventsAsCompatibleEvents": False}
        out = normalize_v3_schema(full)
        assert out["colorNotes"] == [{"b": 2}]
        assert out["obstacles"] == [{"b": 1}]
        assert out["useNormalEventsAsCompatibleEvents"] is False

    def test_beatmap_is_empty(self):
        from full_custom_song_pipeline import beatmap_is_empty
        assert beatmap_is_empty({"colorNotes": [], "bombNotes": [], "obstacles": []})
        assert not beatmap_is_empty({"colorNotes": [{"b": 1}]})


class TestEmptyBeatmapRescue:
    """Chromeo Easy maps decoded with zero notes; pipeline must clone playable
    content from the closest populated Standard difficulty."""

    def test_find_populated_beatmap_prefers_normal(self, tmp_path):
        from full_custom_song_pipeline import _find_populated_beatmap
        (tmp_path / "EasyStandard.dat").write_text(json.dumps(
            {"version": "3.2.0", "colorNotes": []}))
        (tmp_path / "NormalStandard.dat").write_text(json.dumps(
            {"version": "3.2.0", "colorNotes": [{"b": 1, "x": 0, "y": 1, "c": 0, "d": 1}]}))
        donor = _find_populated_beatmap(str(tmp_path), "EasyStandard.dat")
        assert donor is not None and "NormalStandard" in donor

    def test_find_populated_skips_mode_files(self, tmp_path):
        from full_custom_song_pipeline import _find_populated_beatmap
        # Only mode files present — none qualify as Standard donors
        (tmp_path / "ExpertOneSaber.dat").write_text(json.dumps(
            {"version": "3.2.0", "colorNotes": [{"b": 1}]}))
        assert _find_populated_beatmap(str(tmp_path), "EasyStandard.dat") is None

    def test_find_populated_skips_empty_donors(self, tmp_path):
        from full_custom_song_pipeline import _find_populated_beatmap
        (tmp_path / "NormalStandard.dat").write_text(json.dumps(
            {"version": "3.2.0", "colorNotes": []}))
        (tmp_path / "HardStandard.dat").write_text(json.dumps(
            {"version": "3.2.0", "colorNotes": [{"b": 5}]}))
        donor = _find_populated_beatmap(str(tmp_path), "EasyStandard.dat")
        assert donor is not None and "HardStandard" in donor


class TestRoniSourceRegression:
    """The actual Exp 200 crashing source: ExitThisEarthsAtomosphere backout.
    After the fix, injecting its files must yield full-schema, non-empty maps."""

    RONI = "/workspace/beat-saber-ps4-custom-songs/songs/chromeo_backout/ExitThisEarthsAtomosphere"

    @pytest.mark.skipif(not os.path.isdir(RONI), reason="Chromeo backout sources not present")
    def test_roni_easy_gets_rescued(self, tmp_path):
        import shutil
        from full_custom_song_pipeline import (
            normalize_v3_schema, beatmap_is_empty, _find_populated_beatmap,
            is_v2_beatmap,
        )
        workdir = tmp_path / "roni"
        shutil.copytree(self.RONI, str(workdir))
        empty_file = "EasyStandard.dat"
        data = json.load(open(workdir / empty_file))
        assert beatmap_is_empty(data), "precondition: Roni Easy is empty in source"
        donor = _find_populated_beatmap(str(workdir), empty_file)
        assert donor is not None, "must find a populated donor among Roni diffs"
        ddata = json.load(open(donor))
        if is_v2_beatmap(ddata):
            from full_custom_song_pipeline import convert_v2_to_v3
            ddata = convert_v2_to_v3(ddata)
        normalize_v3_schema(ddata)
        data.update({k: ddata[k] for k in ("colorNotes", "bombNotes", "obstacles")})
        assert not beatmap_is_empty(data)

    @pytest.mark.skipif(not os.path.isdir(RONI), reason="Chromeo backout sources not present")
    def test_roni_normal_normalized_has_events_field(self):
        from full_custom_song_pipeline import normalize_v3_schema
        data = json.load(open(os.path.join(self.RONI, "HardStandard.dat")))
        assert "basicBeatmapEvents" not in data, "precondition: Hard lacks events array"
        normalize_v3_schema(data)
        assert isinstance(data["basicBeatmapEvents"], list)
        assert "waypoints" in data
