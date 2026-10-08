"""
test_webapp_server.py — FastAPI endpoint tests (TestClient).

No network, no PS4: BeatSaver calls and ps4 adapter reads are monkeypatched.
Hardware-gate pattern: no test here may touch the real PS4 — the ps4
adapter's lftp path is never invoked.
"""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "webapp"))

import server  # noqa: E402
from adapters import beatsaver as bs_adapter  # noqa: E402
from adapters import ps4 as ps4_adapter  # noqa: E402

client = TestClient(server.app)


class TestModeDetection:
    def test_ping_local_backend(self):
        r = client.get("/api/ping")
        assert r.status_code == 200
        j = r.json()
        assert j["mode"] == "local-backend"
        assert j["pipeline_present"] is True


class TestWizardEndpoints:
    def test_dump_validate_requires_path(self):
        r = client.get("/api/dump/validate")
        assert r.status_code == 422  # FastAPI: missing required query param

    def test_dump_validate_reports_missing(self, tmp_path):
        r = client.get("/api/dump/validate", params={"path": str(tmp_path / "nope")})
        assert r.status_code == 200
        j = r.json()
        assert j["ok"] is False
        assert any("does not exist" in e for e in j["errors"])

    def test_dump_validate_good(self, tmp_path):
        patch = tmp_path / "CUSA12878-patch"
        (patch / "Media/StreamingAssets/aa/PS4").mkdir(parents=True)
        (patch / "eboot.bin").write_bytes(b"x")
        (patch / "Media/StreamingAssets/aa/catalog.json").write_text("{}")
        (tmp_path / "CUSA12878-app").mkdir()
        r = client.get("/api/dump/validate", params={"path": str(tmp_path)})
        assert r.json()["ok"] is True

    def test_config_read_returns_something(self):
        r = client.get("/api/config")
        assert r.status_code == 200
        assert "ps4" in r.json()

    def test_config_save_and_roundtrip(self, tmp_path, monkeypatch):
        scratch = tmp_path / "ps4_config.json"
        monkeypatch.setattr(server.config.paths, "CONFIG_PATH", scratch)
        r = client.post("/api/config/save", json={
            "dump_root": str(tmp_path), "ps4_ip": "10.0.0.9"})
        assert r.status_code == 200
        assert r.json()["config_path"] == str(scratch)
        assert r.json()["config"]["ps4"]["ip"] == "10.0.0.9"


class TestCatalogEndpoint:
    def test_catalog_shape(self):
        r = client.get("/api/catalog")
        assert r.status_code == 200
        albums = r.json()["albums"]
        assert len(albums) > 30  # 36 packs in the real catalog
        pack_names = {a["pack"] for a in albums}
        assert "rollingstones" in pack_names or "therollingstones" in pack_names
        first_song = albums[0]["songs"][0]
        for key in ("songID", "songName", "songAuthorName"):
            assert key in first_song


class TestBeatSaverEndpoints:
    def test_search_proxies(self, monkeypatch):
        def fake_search(q, page=0, per_page=20, api_base=None):
            return {"docs": [{"id": "6d63", "name": "Take on Me - a-ha",
                             "nativeDifficulties": ["Easy", "Hard"]}], "total": 1}
        monkeypatch.setattr(server, "beatsaver", type("M", (), {"search": staticmethod(fake_search), "map_by_id": staticmethod(lambda i: {}), "BeatSaverError": bs_adapter.BeatSaverError}))
        r = client.get("/api/beatsaver/search", params={"q": "take on me"})
        assert r.status_code == 200
        assert r.json()["docs"][0]["id"] == "6d63"

    def test_map_404_maps_to_deleted_message(self, monkeypatch):
        def fake_map(map_id, api_base=None):
            raise bs_adapter.BeatSaverError("404", status=404)
        monkeypatch.setattr(server, "beatsaver", type("M", (), {"search": staticmethod(lambda *a, **k: {"docs": [], "total": 0}), "map_by_id": staticmethod(fake_map), "BeatSaverError": bs_adapter.BeatSaverError}))
        r = client.get("/api/beatsaver/map/deadmap")
        assert r.status_code == 404
        assert "deleted" in r.json()["detail"]


class TestPs4Endpoints:
    def test_ps4_test_unreachable_is_explicit(self, monkeypatch):
        """Failed read → explicit failure, never empty-truth (Exp 237/239/240)."""
        monkeypatch.setattr(server.ps4, "test_connection",
                            lambda: ps4_adapter.ReadResult(
                                ok=False, error="connection refused"))
        r = client.get("/api/ps4/test")
        j = r.json()
        assert j["ok"] is False
        # The endpoint spreads ReadResult.data OR {} — a failed read has
        # data=None, so 'status' comes only from the ok branch; the explicit
        # contract: ok=False + error present, never a fake success.
        assert j["error"] == "connection refused"

    def test_ps4_state_carries_read_errors(self, monkeypatch):
        monkeypatch.setattr(server.ps4, "read_redirects_summary",
                            lambda: ps4_adapter.ReadResult(ok=False, error="read failed"))
        monkeypatch.setattr(server.ps4, "read_features",
                            lambda: ps4_adapter.ReadResult(ok=False, error="read failed"))
        monkeypatch.setattr(server.ps4, "read_song_metadata",
                            lambda: ps4_adapter.ReadResult(ok=False, error="read failed"))
        r = client.get("/api/ps4/state")
        j = r.json()
        assert j["redirects"]["ok"] is False and "error" in j["redirects"]
        assert j["features"]["ok"] is False
        assert j["song_metadata"]["ok"] is False


class TestLoadoutEndpoints:
    def test_packs_list_offline_capable(self):
        """The Manage-Songs dropdown works without the PS4 (catalog only)."""
        r = client.get("/api/loadout/packs")
        assert r.status_code == 200
        j = r.json()
        assert len(j["packs"]) == 36
        assert j["songCounts"]["billieeilish"] > 0

    def test_loadout_carries_read_status(self, monkeypatch):
        """Read failures must surface as readStatus, never as clean-empty."""
        from adapters import ps4 as ps4_mod
        monkeypatch.setattr(
            server.ps4, "read_deployment_state",
            lambda: ps4_mod.ReadResult(ok=False, data={
                "redirects_read_error": "get: timeout"}, error="get: timeout"))
        r = client.get("/api/loadout")
        j = r.json()
        assert j["readStatus"]["redirectsOk"] is False
        assert j["readStatus"]["redirectsReadError"] == "get: timeout"
        # rows still render (catalog merge), but flagged unknown
        assert j["redirectedSlotCount"] == 0

    def test_loadout_happy_path_shape(self, monkeypatch):
        from adapters import ps4 as ps4_mod
        monkeypatch.setattr(
            server.ps4, "read_deployment_state",
            lambda: ps4_mod.ReadResult(ok=True, data={
                "redirects": {"BeatmapLevelsData/BadGuy": "BadGuy_v3.bundle"},
                "song_names": {"bad guy": "Odo / Ado"},
                "song_artists": {"Billie Eilish": " "}}))
        r = client.get("/api/loadout")
        j = r.json()
        assert j["readStatus"]["redirectsOk"] and j["readStatus"]["metadataOk"]
        billie = [p for p in j["packs"] if p["pack"] == "billieeilish"][0]
        badguy = [s for s in billie["songs"] if s["songID"] == "BadGuy"][0]
        assert badguy["customDeployed"] is True
        assert badguy["customName"] == "Odo"
        assert billie["deployedCount"] == 1


class TestJobGuards:
    def test_deploy_requires_config(self, monkeypatch, tmp_path):
        monkeypatch.setattr(server.paths, "CONFIG_PATH", tmp_path / "none.json")
        r = client.post("/api/jobs/deploy", json={"map_id": "x", "target": "y"})
        assert r.status_code == 400
        assert "Setup Wizard" in r.json()["detail"]

    def test_deploy_validates_options(self, tmp_path, monkeypatch):
        monkeypatch.setattr(server.paths, "CONFIG_PATH", tmp_path / "none.json")
        monkeypatch.setattr(server.config.paths, "CONFIG_PATH", tmp_path / "none.json")
        r = client.post("/api/jobs/deploy", json={"map_id": "", "target": ""})
        assert r.status_code == 400

    def test_flags_rejects_unknown_flag(self, tmp_path, monkeypatch):
        monkeypatch.setattr(server.paths, "CONFIG_PATH", tmp_path / "none.json")
        monkeypatch.setattr(server.config.paths, "CONFIG_PATH", tmp_path / "none.json")
        r = client.post("/api/jobs/flags", json={"flag": "delete_everything", "value": True})
        assert r.status_code == 400

    def test_command_preview_needs_both(self):
        r = client.get("/api/command-preview", params={"map_id": "x", "target": ""})
        assert r.status_code == 400

    def test_command_preview_safe_default(self):
        r = client.get("/api/command-preview",
                       params={"map_id": "1d6c7c2", "target": "BadGuy"})
        j = r.json()
        assert j["command"].endswith(
            "--download-beat-saver-song 1d6c7c2 --target BadGuy "
            "--pcm16 --no-pad --convert-to-v3 --deploy-full")


class TestUiServed:
    def test_index_served(self):
        r = client.get("/")
        assert r.status_code == 200
        assert b"Beat Saber Deluxe" in r.content

    def test_dumper_cfg_served(self):
        r = client.get("/static/dumper.cfg")
        assert r.status_code == 200
        assert b"split=3" in r.content


class TestVersionBadge:
    """The lower-corner version badge (user: 'so I can tell when your changes
    have taken effect'). Ping carries all three component versions."""

    def test_ping_carries_all_versions(self):
        j = client.get("/api/ping").json()
        assert j["webapp_version"] != "unknown" and j["webapp_version"] != "0.1.0"
        assert j["pipeline_version"] != "unknown"
        assert j["plugin_version"].startswith("v0.")

    def test_index_has_version_badge(self):
        html = client.get("/").text
        assert "version-badge" in html
        assert 'id="ver-webapp"' in html and 'id="ver-pipeline"' in html \
            and 'id="ver-plugin"' in html
