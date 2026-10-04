"""
test_webapp_tools.py — Flags / Backup-Restore / Feature-Request endpoint tests.

HARD RULE (Exp 248): NO test in this file may start a real pipeline job or
touch the real PS4. The user's live console was mutated by an earlier
version of these tests (a flags-apply test started a REAL
`--features-only` subprocess that pushed a stale local features.json over
the PS4's live state — turning the metadata flag OFF in-game).

Every job-starting endpoint is therefore tested against a MOCKED runner:
`no_real_jobs` (autouse) replaces server.RUNNER.start/start_script with
fakes that record argv and never spawn a subprocess.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "webapp"))

import server  # noqa: E402
from adapters import ps4 as ps4_adapter  # noqa: E402
from adapters import runner as runner_mod  # noqa: E402

client = TestClient(server.app)


class FakeJob:
    """Stand-in for a runner Job — no process, never touches the PS4."""

    def __init__(self, argv, label=""):
        self.argv = list(argv)
        self.label = label
        self.id = 1
        self.exit_code = 0
        self.lines = ["(mocked job — no real pipeline invocation)"]
        self.cancelled = False
        self.command_line = " ".join(argv)


@pytest.fixture(autouse=True)
def no_real_jobs(monkeypatch):
    """Exp 248: replace the runner's spawn methods with recorders. Any test
    that would have started a real pipeline/script subprocess gets a FakeJob
    instead; the recorded argv lets us assert EXACTLY what would have run
    (better coverage than before — we now assert the argv, not just 200 OK).
    """
    started = []

    def fake_start(argv, label=""):
        if server.RUNNER.is_busy():
            raise RuntimeError(
                "A job is already running — one at a time (PS4 state files "
                "are transaction records; concurrent writers corrupt them).")
        started.append(("pipeline", list(argv), label))
        job = FakeJob(argv, label)
        server.RUNNER._job = job
        return job

    def fake_start_script(script, argv, label=""):
        if server.RUNNER.is_busy():
            raise RuntimeError(
                "A job is already running — one at a time (PS4 state files "
                "are transaction records; concurrent writers corrupt them).")
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


@pytest.fixture(autouse=True)
def clean_runner(no_real_jobs):
    yield


# Back-compat alias for tests that referenced the old fixture shape.
@pytest.fixture
def started_jobs(no_real_jobs):
    return no_real_jobs


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

    def test_flags_apply_diffs_only_changes(self, monkeypatch, started_jobs):
        """Only CHANGED flags go into argv — unchanged ones are not re-pushed.
        (Exp 248: this test previously started a REAL --features-only
        subprocess that pushed the stale local features.json over the live
        PS4 — it must run against the MOCKED runner and assert the argv.)"""
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
        # the mocked runner captured exactly one pipeline invocation
        assert len(started_jobs) == 1
        kind, argv, _label = started_jobs[0]
        assert kind == "pipeline"
        assert "enable_song_metadata_modification=false" in argv
        assert not any("enable_plugin" in tok for tok in argv)

    def test_flags_apply_never_pushes_stale_local_file(self, monkeypatch, started_jobs):
        """Exp 248 regression pin: a flags-apply job carries ONLY the
        user-requested diffs as --set-feature tokens — it must never
        transport a local features.json wholesale (the stale-local-file
        push was the mechanism that turned the user's metadata flag off)."""
        monkeypatch.setattr(server.paths, "CONFIG_PATH", PROJECT / "ps4_config.json")
        monkeypatch.setattr(server.ps4, "read_features",
                            lambda: ps4_adapter.ReadResult(ok=True, data=dict(LIVE_FLAGS)))
        r = client.post("/api/jobs/flags-apply",
                        json={"flags": {"enable_song_metadata_modification": False}})
        j = r.json()
        assert j["changed"] == 1
        kind, argv, _ = started_jobs[0]
        set_feature_vals = [argv[i + 1] for i, t in enumerate(argv) if t == "--set-feature"]
        assert set_feature_vals == ["enable_song_metadata_modification=false"]
        # and absolutely no unrelated flag may ride along:
        for val in set_feature_vals:
            assert val.startswith(("enable_song_metadata_modification",
                                   "enable_plugin", "enable_custom_song_replacements",
                                   "enable_beatmap_mode_mapping"))


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


class TestRunnerContract:
    """Exp 248: the runner's SPAWN methods are mocked for ALL tests in this
    file (autouse no_real_jobs) — these tests assert the contract against
    the mocked recorder instead of executing real subprocesses. Real
    subprocess execution + streaming is covered in test_webapp_deploy.py's
    TestSingleJobRunner (which uses --help, never the PS4)."""

    def test_backup_job_argv_recorded(self, monkeypatch, started_jobs):
        """A backup request produces exactly one script job with the right argv."""
        monkeypatch.setattr(server, "BACKUP_SCRIPT", PROJECT / "VERSION")
        r = client.post("/api/jobs/backup", json={"clean_ps4": False})
        assert r.status_code == 200
        kind, argv, label = started_jobs[0]
        assert kind == "script" and argv == ["backup"]
        assert "backup" in label

    def test_single_job_rule_covers_scripts(self, monkeypatch, started_jobs):
        """A busy runner blocks a backup job (409) and starts NOTHING.
        (FastAPI converts HTTPException into a response — assert status.)"""
        fake = runner_mod.Job(id=1, argv=["x"], cwd="/tmp",
                              started_at=0.0)
        fake.exit_code = None
        server.RUNNER._job = fake
        monkeypatch.setattr(server, "BACKUP_SCRIPT", PROJECT / "VERSION")
        r = client.post("/api/jobs/backup", json={})
        assert r.status_code == 409
        assert "already running" in r.json()["detail"]
        assert started_jobs == [], "a blocked job must not be recorded as started"
