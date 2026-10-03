"""
test_webapp_tools.py — Flags / Backup-Restore / Feature-Request endpoint tests.

All PS4 contact mocked; the backup script is NEVER executed here (its jobs
route is exercised only for its guard logic).
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "webapp"))

import server  # noqa: E402
from adapters import ps4 as ps4_adapter  # noqa: E402

client = TestClient(server.app)


@pytest.fixture(autouse=True)
def clean_runner():
    server.RUNNER._job = None
    server.RUNNER.pending_flags = None
    yield
    server.RUNNER._job = None
    server.RUNNER.pending_flags = None


LIVE_FLAGS = {"enable_plugin": True, "enable_custom_song_replacements": True,
              "enable_song_metadata_modification": True, "enable_beatmap_mode_mapping": True}


class TestFlagsEndpoints:
    def test_flags_read_with_descriptions(self, monkeypatch):
        monkeypatch.setattr(server.ps4, "read_features",
                            lambda: ps4_adapter.ReadResult(ok=True, data=dict(LIVE_FLAGS)))
        r = client.get("/api/flags")
        j = r.json()
        assert j["ok"] is True
        by_name = {f["name"]: f for f in j["flags"]}
        assert set(by_name) == set(LIVE_FLAGS)
        # every flag carries a real description
        for f in j["flags"]:
            assert f["description"], f"{f['name']} missing description"
        assert "kill switch" in by_name["enable_plugin"]["description"].lower()

    def test_flags_read_failure_explicit(self, monkeypatch):
        monkeypatch.setattr(server.ps4, "read_features",
                            lambda: ps4_adapter.ReadResult(ok=False, error="timeout"))
        r = client.get("/api/flags")
        j = r.json()
        assert j["ok"] is False and j["flags"] == []

    def test_flags_apply_requires_config(self, tmp_path, monkeypatch):
        monkeypatch.setattr(server.paths, "CONFIG_PATH", tmp_path / "none.json")
        r = client.post("/api/jobs/flags-apply", json={"flags": {"enable_plugin": False}})
        assert r.status_code == 400

    def test_flags_apply_rejects_unknown_flag(self, tmp_path, monkeypatch):
        monkeypatch.setattr(server.paths, "CONFIG_PATH", PROJECT / "ps4_config.json")
        monkeypatch.setattr(server.ps4, "read_features",
                            lambda: ps4_adapter.ReadResult(ok=True, data=dict(LIVE_FLAGS)))
        r = client.post("/api/jobs/flags-apply",
                        json={"flags": {"destroy_everything": True}})
        assert r.status_code == 400

    def test_flags_apply_blind_refused_when_ps4_unreadable(self, tmp_path, monkeypatch):
        """PS4 flags unreadable → 502, never apply blind (anti-wipe posture)."""
        monkeypatch.setattr(server.paths, "CONFIG_PATH", PROJECT / "ps4_config.json")
        monkeypatch.setattr(server.ps4, "read_features",
                            lambda: ps4_adapter.ReadResult(ok=False, error="no route"))
        r = client.post("/api/jobs/flags-apply",
                        json={"flags": {"enable_plugin": False}})
        assert r.status_code == 502

    def test_flags_apply_noop_when_unchanged(self, monkeypatch):
        monkeypatch.setattr(server.paths, "CONFIG_PATH", PROJECT / "ps4_config.json")
        monkeypatch.setattr(server.ps4, "read_features",
                            lambda: ps4_adapter.ReadResult(ok=True, data=dict(LIVE_FLAGS)))
        r = client.post("/api/jobs/flags-apply", json={"flags": dict(LIVE_FLAGS)})
        j = r.json()
        assert j["changed"] == 0 and j["job_id"] is None

    def test_flags_apply_diffs_only_changes(self, monkeypatch):
        """Only CHANGED flags go into argv — unchanged ones are not re-pushed."""
        monkeypatch.setattr(server.paths, "CONFIG_PATH", PROJECT / "ps4_config.json")
        monkeypatch.setattr(server.ps4, "read_features",
                            lambda: ps4_adapter.ReadResult(ok=True, data=dict(LIVE_FLAGS)))
        wanted = dict(LIVE_FLAGS)
        wanted["enable_song_metadata_modification"] = False
        r = client.post("/api/jobs/flags-apply", json={"flags": wanted})
        j = r.json()
        assert j["changed"] == 1
        assert "--set-feature" in j["command"]
        assert "enable_song_metadata_modification=false" in j["command"]
        assert "enable_plugin" not in j["command"].split("--set-feature")[-1]


class TestBackupEndpoints:
    def test_backup_list_reads_dir(self, monkeypatch, tmp_path):
        monkeypatch.setattr(server, "BACKUP_DIR", tmp_path)
        (tmp_path / "bsd_backup_20260101_000000.zip").write_bytes(b"x" * 100)
        (tmp_path / "notazip.txt").write_text("ignore me")
        r = client.get("/api/backup/list")
        j = r.json()
        assert len(j["backups"]) == 1
        assert j["backups"][0]["name"] == "bsd_backup_20260101_000000.zip"
        assert j["backups"][0]["size"] == 100

    def test_backup_list_empty_dir_ok(self, monkeypatch, tmp_path):
        monkeypatch.setattr(server, "BACKUP_DIR", tmp_path)
        assert client.get("/api/backup/list").json()["backups"] == []

    def test_backup_job_starts(self, monkeypatch):
        monkeypatch.setattr(server, "BACKUP_SCRIPT", PROJECT / "VERSION")  # exists
        r = client.post("/api/jobs/backup", json={"clean_ps4": False})
        assert r.status_code == 200
        assert "backup" in r.json()["command"]
        # clean up the job (VERSION "script" exits immediately; poll drains it)

    def test_backup_clean_flag_in_command(self, monkeypatch):
        monkeypatch.setattr(server, "BACKUP_SCRIPT", PROJECT / "VERSION")
        r = client.post("/api/jobs/backup", json={"clean_ps4": True})
        assert "--clean-ps4" in r.json()["command"]

    def test_restore_rejects_path_traversal(self, monkeypatch):
        """backup names are sanitized: no paths, no .. — the zip dir is a jail."""
        monkeypatch.setattr(server, "BACKUP_SCRIPT", PROJECT / "VERSION")
        monkeypatch.setattr(server, "BACKUP_DIR", PROJECT.parent / "ps4_backups")
        r = client.post("/api/jobs/restore",
                        json={"backup": "../../etc/passwd", "clean_ps4": False})
        assert r.status_code == 400

    def test_restore_unknown_backup_404(self, monkeypatch, tmp_path):
        monkeypatch.setattr(server, "BACKUP_SCRIPT", PROJECT / "VERSION")
        monkeypatch.setattr(server, "BACKUP_DIR", tmp_path)
        r = client.post("/api/jobs/restore",
                        json={"backup": "nope.zip", "clean_ps4": False})
        assert r.status_code == 404


class TestFeatureRequest:
    def test_template_carries_repo(self):
        j = client.get("/api/feature-request/template").json()
        assert "BeatSaberPcCustomSongToPs4InstallConverter" in j["repo"]
        assert j["issue_url"].startswith("https://github.com/")


class TestRunnerStartScript:
    def test_start_script_runs_and_streams(self):
        """The runner executes a real (harmless) python script and streams it."""
        import time as _t
        job = server.RUNNER.start_script(
            str(PROJECT / "VERSION"), [], label="test")
        # VERSION isn't python — job fails fast; the point is execution+drain
        deadline = _t.time() + 30
        while job.exit_code is None and _t.time() < deadline:
            _t.sleep(0.05)
        assert job.exit_code is not None
        assert job.command_line.startswith("python3")

    def test_single_job_rule_covers_scripts(self, monkeypatch):
        """A backup job running blocks a deploy job (and vice versa).
        (Note: FastAPI converts HTTPException into a response — assert on
        the status code, not on the exception propagating.)"""
        import adapters.runner as runner_mod
        fake = runner_mod.Job(id=1, argv=["x"], cwd="/tmp",
                              started_at=0.0)
        fake.exit_code = None
        server.RUNNER._job = fake
        monkeypatch.setattr(server, "BACKUP_SCRIPT", PROJECT / "VERSION")
        r = client.post("/api/jobs/backup", json={})
        assert r.status_code == 409
        assert "already running" in r.json()["detail"]
