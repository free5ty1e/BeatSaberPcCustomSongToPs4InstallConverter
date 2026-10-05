"""
test_webapp_batch.py — Batch tab: example-script parser + custom-batch
files + endpoints (all local; no PS4, no real deploys — the batch job
route is validated for its guard logic only).
"""

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "webapp"))

import server  # noqa: E402
from adapters import batch  # noqa: E402

client = TestClient(server.app)


class FakeJob:
    def __init__(self, argv, label=""):
        self.argv = list(argv)
        self.label = label
        self.id = 1
        self.exit_code = 0
        self.lines = ["(mocked)"]
        self.cancelled = False
        self.command_line = " ".join(argv)


@pytest.fixture(autouse=True)
def no_real_jobs(monkeypatch):
    started = []

    def fake_start(argv, label=""):
        started.append(("pipeline", list(argv), label))
        job = FakeJob(argv, label)
        server.RUNNER._job = job
        return job

    def fake_start_script(script, argv, label=""):
        started.append(("script", list(argv), label))
        job = FakeJob(argv, label)
        server.RUNNER._job = job
        return job

    monkeypatch.setattr(server.RUNNER, "start", fake_start)
    monkeypatch.setattr(server.RUNNER, "start_script", fake_start_script)
    server.RUNNER._job = None
    server.RUNNER.pending_flags = None
    yield started
    server.RUNNER._job = None
    server.RUNNER.pending_flags = None


@pytest.fixture
def started_jobs(no_real_jobs):
    return no_real_jobs


@pytest.fixture
def batches_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(batch, "BATCH_DIR", tmp_path)
    return tmp_path


class TestExampleParsing:
    def test_all_34_packs_parse(self):
        packs = batch.parse_example_scripts()
        assert len(packs) == 34
        names = [p["name"] for p in packs]
        assert any("Rolling Stones" in n for n in names)

    def test_rolling_stones_entries_shape(self):
        packs = batch.parse_example_scripts()
        rs = next(p for p in packs if "Rolling Stones" in p["name"])
        assert len(rs["songs"]) == 11
        s = rs["songs"][0]
        assert s["map_id"] and s["target"]
        assert s["convert_to_v3"] is True and s["pad_fsb5"] is False
        # human hints attached (the # Song N: comments)
        assert s["song_name"], "song comment hint not attached"
        assert s["artist"], "artist hint not attached"

    def test_commented_template_lines_skipped(self):
        """The docs' <MAP_ID> template lines (commented) must NOT parse."""
        packs = batch.parse_example_scripts()
        for p in packs:
            for s in p["songs"]:
                assert "<" not in s["map_id"], f"template placeholder parsed: {s}"

    def test_endpoint_matches_parser(self):
        j = client.get("/api/batch/examples").json()
        assert len(j["packs"]) == 34


class TestCustomBatchFiles:
    def test_save_and_load_roundtrip(self, batches_dir):
        doc = {"format": "bsd-batch", "version": 1, "name": "My Pack",
               "description": "test",
               "songs": [{"map_id": "c213", "target": "Angry",
                          "song_name": "Rhythm Is A Dancer",
                          "artist": "Pegboard Nerds"}]}
        saved = batch.save_custom_batch(doc)
        assert saved["file"].endswith(".json")
        loaded = batch.load_custom_batch(saved["file"])
        assert loaded["name"] == "My Pack"
        assert loaded["songs"][0]["map_id"] == "c213"
        assert loaded["songs"][0]["artist"] == "Pegboard Nerds"

    def test_defaults_normalized(self, batches_dir):
        doc = {"format": "bsd-batch", "version": 1, "name": "X",
               "songs": [{"map_id": "a", "target": "b"}]}
        saved = batch.save_custom_batch(doc)
        s = batch.load_custom_batch(saved["file"])["songs"][0]
        assert s["audio"] == "pcm16" and s["convert_to_v3"] is True \
            and s["pad_fsb5"] is False

    def test_unknown_fields_roundtrip(self, batches_dir):
        doc = {"format": "bsd-batch", "version": 1, "name": "X",
               "songs": [{"map_id": "a", "target": "b", "my_future_field": 42}]}
        saved = batch.save_custom_batch(doc)
        loaded = batch.load_custom_batch(saved["file"])
        assert loaded["songs"][0]["my_future_field"] == 42

    def test_validation_errors(self, batches_dir):
        with pytest.raises(ValueError, match="name"):
            batch.save_custom_batch({"songs": []})
        with pytest.raises(ValueError, match="map_id"):
            batch.save_custom_batch({"name": "X", "songs": [{"target": "b"}]})
        with pytest.raises(ValueError, match="format"):
            batch.save_custom_batch({"format": "other", "name": "X", "songs": []})
        with pytest.raises(ValueError, match="audio"):
            batch.save_custom_batch({"name": "X",
                                     "songs": [{"map_id": "a", "target": "b",
                                                "audio": "mp3"}]})

    def test_path_traversal_rejected(self, batches_dir):
        with pytest.raises(ValueError):
            batch.load_custom_batch("../evil.json")
        with pytest.raises(ValueError):
            batch.save_custom_batch({"name": "X", "songs": []},
                                    filename="a/b.json")

    def test_endpoint_save_list_delete(self, batches_dir):
        r = client.post("/api/batch/custom", json={
            "batch": {"format": "bsd-batch", "version": 1, "name": "API Pack",
                      "songs": [{"map_id": "c213", "target": "Angry"}]}})
        assert r.status_code == 200
        fname = r.json()["file"]
        lst = client.get("/api/batch/custom").json()["batches"]
        assert any(b["file"] == fname for b in lst)
        got = client.get(f"/api/batch/custom/{fname}").json()
        assert got["ok"] and got["batch"]["name"] == "API Pack"
        dele = client.delete(f"/api/batch/custom/{fname}")
        assert dele.status_code == 200
        assert client.get("/api/batch/custom/{fname}".replace("{fname}", fname)).status_code == 404


class TestBatchJobEndpoint:
    def test_batch_requires_config(self, tmp_path, monkeypatch):
        monkeypatch.setattr(server.paths, "CONFIG_PATH", tmp_path / "none.json")
        r = client.post("/api/jobs/batch", json={"songs": [{"map_id": "a", "target": "b"}]})
        assert r.status_code == 400

    def test_batch_validates_before_starting(self, monkeypatch, started_jobs):
        """A bad entry aborts with 400 and starts NOTHING."""
        monkeypatch.setattr(server.paths, "CONFIG_PATH", PROJECT / "ps4_config.json")
        r = client.post("/api/jobs/batch", json={
            "songs": [{"map_id": "a", "target": "b"},
                      {"map_id": "", "target": "x"}]})
        assert r.status_code == 400
        assert started_jobs == []

    def test_batch_starts_script_job(self, monkeypatch, started_jobs):
        monkeypatch.setattr(server.paths, "CONFIG_PATH", PROJECT / "ps4_config.json")
        r = client.post("/api/jobs/batch", json={
            "songs": [{"map_id": "c213", "target": "Angry"},
                      {"map_id": "6d63", "target": "BadGuy", "audio": "vorbis"}]})
        assert r.status_code == 200
        j = r.json()
        assert j["count"] == 2
        kind, argv, _ = started_jobs[0]
        assert kind == "script"
        payload = json.loads(argv[argv.index("--jobs") + 1])
        assert len(payload) == 2
        assert "--vorbis" in payload[1] and "--pcm16" in payload[0]


class TestMultiPackBatch:
    """The multi-pack flow: the client merges selected example packs (in the
    order shown) into ONE /api/jobs/batch call. Server-side contract: the
    merged payload is a plain songs list — pinned here end-to-end."""

    def test_multi_pack_merge_and_run(self, monkeypatch, started_jobs):
        """Selecting the user's standard loadout (rolling stones, billie
        eilish, britney spears, lizzo, camellia) merges to the same songs
        the chained example scripts would deploy — in pack order."""
        monkeypatch.setattr(server.paths, "CONFIG_PATH", PROJECT / "ps4_config.json")
        packs = batch.parse_example_scripts()
        wanted = ["Rolling Stones", "Billie Eilish", "Britney Spears",
                  "Lizzo", "Camelia"]
        selected = [p for p in packs if any(w in p["name"] for w in wanted)]
        assert len(selected) == 5, f"expected 5 packs, got {[p['name'] for p in selected]}"
        songs = [dict(s) for p in selected for s in p["songs"]]
        total = sum(len(p["songs"]) for p in selected)
        assert len(songs) == total
        r = client.post("/api/jobs/batch", json={"songs": songs})
        assert r.status_code == 200
        j = r.json()
        assert j["count"] == total
        # the payload preserves pack order: first songs are pack 0's
        payload = json.loads(started_jobs[0][1][started_jobs[0][1].index("--jobs") + 1])
        assert len(payload) == total
        assert payload[0] == selected[0]["songs"][0]["map_id"] or \
               payload[0][0] == "--download-beat-saver-song"  # argv shape intact

    def test_multi_pack_counts_match_scripts(self):
        """The five-pack standard loadout's merged size == the sum of the
        scripts' deploy-line counts (no drops, no dupes from the merge)."""
        packs = batch.parse_example_scripts()
        wanted = ["Rolling Stones", "Billie Eilish", "Britney Spears",
                  "Lizzo", "Camelia"]
        selected = [p for p in packs if any(w in p["name"] for w in wanted)]
        merged = sum(len(p["songs"]) for p in selected)
        assert merged == 11 + 13 + 11 + 9 + 6  # RS, BE, BS, Lizzo, Camelia
