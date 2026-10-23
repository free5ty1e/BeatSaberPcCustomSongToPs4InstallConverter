"""
test_webapp_songs.py — M13: local song validation + zip intake + staging.

Hermetic (plan §6): synthetic map fixtures in tmp dirs; NO network, NO PS4.
The validator's contract mirrors the pipeline's own (adapters/songs.py
docstring) — these tests pin that mirror so the thin layer never drifts.
"""

import json
import shutil
import sys
import zipfile
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "webapp"))

from adapters import songs  # noqa: E402


@pytest.fixture()
def staging(tmp_path, monkeypatch):
    """Point staging at a tmp dir so tests never touch the real one."""
    st = tmp_path / "staged_songs"
    monkeypatch.setattr(songs, "STAGING_DIR", st)
    monkeypatch.setattr(songs, "MANIFEST_PATH", st / "manifest.json")
    return st


def make_map(root: Path, *, schema="3.3.0", name="Test Song", artist="Tester",
             bpm=120.0, diffs=("Easy", "Normal", "Hard"),
             audio="song.ogg", extra=None) -> Path:
    """A minimal valid map folder (V2/V3 shape by default; V4 via schema=4)."""
    root.mkdir(parents=True, exist_ok=True)
    info = {
        "_version": schema,
        "_songName": name,
        "_songAuthorName": artist,
        "_beatsPerMinute": bpm,
        "_difficultyBeatmapSets": [{
            "_beatmapCharacteristicName": "Standard",
            "_difficultyBeatmaps": [
                {"_difficulty": d, "_beatmapFilename": f"{d}.dat"} for d in diffs
            ],
        }],
    }
    (root / "Info.dat").write_text(json.dumps(info))
    for d in diffs:
        (root / f"{d}.dat").write_text('{"_notes": []}')
    (root / audio).write_bytes(b"fake-ogg-data")
    for f in (extra or []):
        (root / f).write_bytes(b"x")
    return root


def make_v4_map(root: Path, name="V4 Song", artist="V4ist") -> Path:
    """A V4-shape map (nested song/audio objects, difficultyBeatmaps)."""
    root.mkdir(parents=True, exist_ok=True)
    info = {
        "_version": "4.0.0",
        "song": {"title": name, "author": artist},
        "audio": {"bpm": 111.0, "songFilename": "song.egg"},
        "difficultyBeatmaps": [
            {"characteristic": "Standard", "difficulty": "Expert",
             "beatmapFile": "Expert.beatmap.dat"},
        ],
    }
    (root / "Info.dat").write_text(json.dumps(info))
    (root / "Expert.beatmap.dat").write_text('{"colorNotes": []}')
    (root / "song.egg").write_bytes(b"fake-egg")
    return root


# ------------------------------------------------------------ validate_dir

def test_validate_happy_path(tmp_path):
    d = make_map(tmp_path / "map", name="Happy", artist="Camper")
    v = songs.validate_dir(str(d))
    assert v.ok, v.errors
    assert v.name == "Happy" and v.artist == "Camper"
    assert v.bpm == 120.0
    assert v.schema == "V3"
    assert v.difficulties == ["Easy", "Normal", "Hard"]
    assert v.audio_files == ["song.ogg"]
    # Easy present, Expert missing → exactly one warning (the auto-fill note)
    assert any("Expert" in w for w in v.warnings)


def test_validate_v2_schema():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = make_map(Path(td) / "m", schema="2.2.0")
        v = songs.validate_dir(str(d))
        assert v.ok and v.schema == "V2"


def test_validate_v4_nested_metadata(tmp_path):
    d = make_v4_map(tmp_path / "v4")
    v = songs.validate_dir(str(d))
    assert v.ok, v.errors
    assert v.name == "V4 Song" and v.artist == "V4ist"
    assert v.bpm == 111.0
    assert v.schema == "V4"
    assert v.difficulties == ["Expert"]


def test_validate_missing_dir():
    v = songs.validate_dir("/no/such/dir/anywhere")
    assert not v.ok
    assert "Folder not found" in v.errors[0]
    assert "To fix" in v.errors[0]


def test_validate_empty_path():
    v = songs.validate_dir("  ")
    assert not v.ok
    assert "No folder path" in v.errors[0]


def test_validate_no_info_dat(tmp_path):
    d = tmp_path / "empty"
    d.mkdir()
    v = songs.validate_dir(str(d))
    assert not v.ok
    assert "No Info.dat found" in v.errors[0]
    assert "To fix" in v.errors[0]


def test_validate_bad_json(tmp_path):
    d = tmp_path / "corrupt"
    d.mkdir()
    (d / "Info.dat").write_text("{not json")
    (d / "song.ogg").write_bytes(b"x")
    v = songs.validate_dir(str(d))
    assert not v.ok
    assert "not valid JSON" in v.errors[0]


def test_validate_no_audio(tmp_path):
    d = make_map(tmp_path / "noaudio")
    (d / "song.ogg").unlink()
    v = songs.validate_dir(str(d))
    assert not v.ok
    assert "No audio file found" in v.errors[0]
    assert "To fix" in v.errors[0]


def test_validate_no_beatmaps(tmp_path):
    d = make_map(tmp_path / "nobm")
    for f in d.glob("*.dat"):
        if f.name != "Info.dat":
            f.unlink()
    v = songs.validate_dir(str(d))
    assert not v.ok
    assert "No beatmap" in v.errors[0]


def test_validate_lowercase_info(tmp_path):
    d = tmp_path / "lower"
    d.mkdir()
    (d / "info.dat").write_text(json.dumps({
        "_version": "3.3.0", "_songName": "L", "_songAuthorName": "C",
        "_beatsPerMinute": 100, "_difficultyBeatmapSets": []}))
    (d / "Easy.dat").write_text("{}")
    (d / "s.wav").write_bytes(b"x")
    v = songs.validate_dir(str(d))
    assert v.ok and v.name == "L"


def test_validate_one_saber_filename(tmp_path):
    d = make_map(tmp_path / "modes")
    (d / "OneSaberExpert.dat").write_text("{}")
    (d / "ExpertPlusOneSaber.dat").write_text("{}")
    v = songs.validate_dir(str(d))
    assert v.ok
    assert "OneSaber" in v.modes
    assert "ExpertPlus" in v.difficulties


def test_validate_info_only_difficulties(tmp_path):
    """Info.dat declares Standard difficulties; filenames are V4-style —
    the declared set fills gaps the filename scan missed."""
    d = make_v4_map(tmp_path / "declared")
    info = json.loads((d / "Info.dat").read_text())
    info["difficultyBeatmaps"] = [
        {"characteristic": "Standard", "difficulty": d_, "beatmapFile": "x"}
        for d_ in ("Normal", "Expert")]
    (d / "Info.dat").write_text(json.dumps(info))
    (d / "Normal.beatmap.dat").write_text("{}")
    v = songs.validate_dir(str(d))
    assert v.ok
    assert set(v.difficulties) == {"Normal", "Expert"}


# ------------------------------------------------------------ zip intake

def _zip_bytes(files: dict[str, bytes]) -> bytes:
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


def _map_files(name="Zipped", artist="Zipper") -> dict[str, bytes]:
    info = {
        "_version": "3.3.0", "_songName": name, "_songAuthorName": artist,
        "_beatsPerMinute": 128,
        "_difficultyBeatmapSets": [{"_beatmapCharacteristicName": "Standard",
                                    "_difficultyBeatmaps": [
                                        {"_difficulty": "Hard", "_beatmapFilename": "Hard.dat"}]}],
    }
    return {"Info.dat": json.dumps(info).encode(),
            "Hard.dat": b"{}",
            "song.ogg": b"ogg-bytes"}


def test_stage_zip_root_layout(staging):
    entry = songs.stage_zip_bytes(_zip_bytes(_map_files()), source="zip")
    assert entry["name"] == "Zipped"
    assert entry["schema"] == "V3"
    assert entry["difficulties"] == ["Hard"]
    assert Path(entry["dir"]).is_dir()
    assert (Path(entry["dir"]) / "Info.dat").exists()
    # staged list reflects it
    listed = songs.list_staged()
    assert any(s["id"] == entry["id"] for s in listed)


def test_stage_zip_nested_folder(staging):
    """A zip that wraps everything in one folder descends to Info.dat."""
    files = {f"wrapper/{k}": v for k, v in _map_files().items()}
    entry = songs.stage_zip_bytes(_zip_bytes(files), source="zip")
    assert Path(entry["dir"]).name == "wrapper"
    assert (Path(entry["dir"]) / "Info.dat").exists()


def test_stage_zip_slip_guarded(staging):
    files = _map_files()
    files["../../evil.sh"] = b"#!/bin/sh\n"
    with pytest.raises(ValueError, match="unsafe zip entry"):
        songs.stage_zip_bytes(_zip_bytes(files))
    # and nothing escaped the staging dir
    assert not (staging.parent / "evil.sh").exists()


def test_stage_zip_absolute_path_guarded(staging):
    files = _map_files()
    files["/etc/pwned"] = b"x"
    with pytest.raises(ValueError, match="unsafe zip entry"):
        songs.stage_zip_bytes(_zip_bytes(files))


def test_stage_zip_bad_magic(staging):
    with pytest.raises(ValueError, match="Not a zip file"):
        songs.stage_zip_bytes(b"HTML-not-a-zip<html>")


def test_stage_zip_invalid_map_cleaned_up(staging):
    """A zip that extracts but doesn't validate leaves no staged residue."""
    files = {"Info.dat": b'{"_version": "3.0.0"}',  # no audio, no beatmaps
             }
    with pytest.raises(ValueError, match="No audio"):
        songs.stage_zip_bytes(_zip_bytes(files))
    assert list(staging.iterdir()) == []  # extraction dir cleaned


# ------------------------------------------------------------ staging lifecycle

def test_stage_dir_and_persistence(staging, tmp_path):
    d = make_map(tmp_path / "myfolder", name="Folder Song")
    e1 = songs.stage_dir(str(d))
    e2 = songs.stage_dir(str(d))  # same path → same id (refresh, not dupe)
    assert e1["id"] == e2["id"]
    assert len(songs.list_staged()) == 1


def test_stage_dir_invalid_raises(tmp_path):
    with pytest.raises(ValueError, match="No Info.dat"):
        songs.stage_dir(str(tmp_path))


def test_remove_staged_zip_deletes_extract(staging):
    entry = songs.stage_zip_bytes(_zip_bytes(_map_files()), source="beatsage")
    extracted = Path(entry["dir"])
    assert songs.remove_staged(entry["id"])
    assert not extracted.exists()
    assert songs.list_staged() == []


def test_remove_staged_path_keeps_folder(staging, tmp_path):
    d = make_map(tmp_path / "keepme")
    entry = songs.stage_dir(str(d))
    assert songs.remove_staged(entry["id"])
    assert d.exists()  # the user's folder was never ours
    assert songs.list_staged() == []


def test_list_staged_prunes_dead_paths(staging, tmp_path):
    d = make_map(tmp_path / "gone")
    songs.stage_dir(str(d))
    shutil.rmtree(d)  # folder vanished after staging
    assert songs.list_staged() == []  # pruned, not shown


def test_manifest_survives_restart(staging):
    songs.stage_zip_bytes(_zip_bytes(_map_files()), source="zip")
    # a "restart" = a fresh _load_manifest from the same file
    manifest = songs._load_manifest()
    assert manifest and manifest[list(manifest)[0]]["name"] == "Zipped"
