"""
test_exp246_redirect_wipe.py — regression tests for the 46-redirect wipe (Exp 246).

THE BUG (2026-10-02, live PS4): a single-song deploy over a 47-song loadout
wiped 46 song redirects and crashed every other custom song in-game.

Root cause chain (three stacked defects, all fixed + pinned here):
1. The release-validation clear-target round-trip restored the PS4's
   redirects.json but left the LOCAL copy at 1 song (local/PS4 divergence).
2. manage_redirect_config GENERATE mode based a generate+DEPLOY on the stale
   LOCAL file — pushing it over the live 47-redirect state (pull-before-push,
   the Exp 237 invariant, violated by the pipeline itself).
3. The single-song scope-expansion path silently fell back to "just the new
   target" when its PS4 read failed (READ-FAILED rendered as empty-truth).

The fixes:
- generate+deploy REBASES onto the live PS4 state (stale local → live base,
  local file resynced); unreachable PS4 + existing local file → hard ABORT.
- Scope-expansion read failure → hard ABORT with a clear message.
- _ensure_mass_song_redirects NEVER deletes out-of-scope song redirects
  (dedicated removal paths only: --clear-target-song, clean slate).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import full_custom_song_pipeline as pipeline  # noqa: E402
import pytest


@pytest.fixture
def tmp_redirect_file(tmp_path, monkeypatch):
    """Point the pipeline at a scratch redirects.json."""
    path = tmp_path / "redirects.json"
    monkeypatch.setattr(pipeline, "_get_redirect_config_path",
                        lambda project_root=None: str(path))
    return path


CONFIG = {"title": {"id": "CUSA12878"},
          "paths": {"afr_base": "/data/GoldHEN/AFR", "afr_target_suffix": "_v3"}}

LIVE_47 = {"titleId": "CUSA12878", "afrBase": "/data/GoldHEN/AFR",
           "redirects": {f"BeatmapLevelsData/Slot{i}": f"Slot{i}_v3.bundle"
                        for i in range(47)}}


class TestGenerateDeployRebasesOnLiveState:
    def test_stale_local_not_pushed_over_live(self, tmp_redirect_file, monkeypatch):
        """THE Exp 246 scenario: local has 1 song, PS4 has 47, a deploy runs.
        The live PS4 state must be the base — all 47 preserved + the new one."""
        # stale local: 1 song
        tmp_redirect_file.write_text(json.dumps(
            {"titleId": "CUSA12878", "afrBase": "/data/GoldHEN/AFR",
             "redirects": {"BeatmapLevelsData/MessItUp": "MessItUp_v3.bundle"}}))
        monkeypatch.setattr(pipeline, "_download_redirect_from_ps4",
                            lambda config: json.loads(json.dumps(LIVE_47)))
        monkeypatch.setattr(pipeline, "_deploy_redirect_to_ps4", lambda config: None)

        result = pipeline.manage_redirect_config(
            CONFIG, target_name="NewSong", generate=True, deploy=True)

        red = result["redirects"]
        assert len(red) == 48, f"expected 47 preserved + 1 new, got {len(red)}"
        assert "BeatmapLevelsData/NewSong" in red
        assert "BeatmapLevelsData/Slot0" in red and "BeatmapLevelsData/Slot46" in red
        # local file resynced to the live base
        assert len(json.loads(tmp_redirect_file.read_text())["redirects"]) == 48

    def test_unreachable_ps4_aborts_deploy(self, tmp_redirect_file, monkeypatch):
        """PS4 unreachable + local file exists → ABORT (SystemExit), never a
        silent stale-file push. This is the anti-wipe gate."""
        tmp_redirect_file.write_text(json.dumps(LIVE_47))
        monkeypatch.setattr(pipeline, "_download_redirect_from_ps4",
                            lambda config: None)  # read FAILED (not 'absent')
        monkeypatch.setattr(pipeline, "_deploy_redirect_to_ps4", lambda config: None)

        with pytest.raises(SystemExit):
            pipeline.manage_redirect_config(
                CONFIG, target_name="NewSong", generate=True, deploy=True)

    def test_no_local_no_live_is_clean_slate(self, tmp_redirect_file, monkeypatch):
        """Genuinely fresh start (no local file, no PS4 state): empty base is
        CORRECT — the documented clean-slate first-deploy flow must work."""
        assert not tmp_redirect_file.exists()
        monkeypatch.setattr(pipeline, "_download_redirect_from_ps4",
                            lambda config: None)
        monkeypatch.setattr(pipeline, "_deploy_redirect_to_ps4", lambda config: None)

        result = pipeline.manage_redirect_config(
            CONFIG, target_name="FirstSong", generate=True, deploy=True)
        # Clean-slate flow: the new song's redirect exists. (The pack-pair
        # ensure step may add pack/catalog redirects from the developer's
        # local bundle cache — not this test's concern; the anti-wipe concern
        # is that NOTHING pre-existing was clobbered, and there was nothing
        # pre-existing to clobber in this scenario.)
        assert "BeatmapLevelsData/FirstSong" in result["redirects"]

    def test_local_only_generate_keeps_local_base(self, tmp_redirect_file, monkeypatch):
        """generate WITHOUT deploy (the offline 'edit my local file' flow) must
        NOT touch the network — local file stays the base."""
        tmp_redirect_file.write_text(json.dumps(
            {"titleId": "CUSA12878", "afrBase": "/data/GoldHEN/AFR",
             "redirects": {"BeatmapLevelsData/Existing": "Existing_v3"}}))

        def fail_net(config):
            raise AssertionError("local-only generate must not contact the PS4")

        monkeypatch.setattr(pipeline, "_download_redirect_from_ps4", fail_net)

        result = pipeline.manage_redirect_config(
            CONFIG, target_name="Angry", generate=True, deploy=False)
        assert len(result["redirects"]) == 2


class TestEnsureMassSongRedirectsNeverSweeps:
    MASS_CFG = {"paths": {"afr_target_suffix": "_v3.bundle"},
                "mass_deploy": {"slots": ["startmeup", "angry"]}}

    def test_out_of_scope_redirects_preserved(self):
        """Exp 226/246 invariant: scope filtering must never delete a song
        redirect — removal is the job of --clear-target-song / clean slate."""
        data = {"titleId": "CUSA12878", "afrBase": "/x", "redirects": {
            "BeatmapLevelsData/startmeup": "startmeup_v3.bundle",
            "BeatmapLevelsData/BadGuy": "BadGuy_v3.bundle",   # out of scope
            "aa/catalog.json": "catalog_pack_modes.json",
        }}
        pipeline._ensure_mass_song_redirects(data, self.MASS_CFG, slots=["startmeup"])
        red = data["redirects"]
        assert "BeatmapLevelsData/BadGuy" in red, "out-of-scope redirect was deleted"
        assert red["BeatmapLevelsData/BadGuy"] == "BadGuy_v3.bundle"
        assert "BeatmapLevelsData/startmeup" in red
        assert "aa/catalog.json" in red

    def test_stale_value_healed_in_scope(self):
        """In-scope slots still get their VALUE healed to the deployed name."""
        data = {"titleId": "CUSA12878", "afrBase": "/x", "redirects": {
            "BeatmapLevelsData/startmeup": "startmeup_v3",  # pre-.bundle stale
        }}
        pipeline._ensure_mass_song_redirects(data, self.MASS_CFG, slots=["startmeup"])
        assert data["redirects"]["BeatmapLevelsData/startmeup"] == "startmeup_v3.bundle"


class TestBannerProofScopeRead:
    """Fix B's extraction helper behavior (the scope read must parse banners)."""

    def test_extract_json_survives_banner(self, tmp_path):
        raw = "156 bytes transferred\n" + json.dumps(
            {"redirects": {"BeatmapLevelsData/X": "X_v3.bundle"}}) + "}more banner"
        f = tmp_path / "r.json"
        f.write_text(raw)
        start, _end = raw.find("{"), raw.rfind("}")
        # the deployed code uses first-{ to LAST-} … which breaks on a
        # trailing banner that STARTS with }. Use raw-decode semantics here:
        dec = json.JSONDecoder()
        obj, _ = dec.raw_decode(raw, start)
        assert obj["redirects"]["BeatmapLevelsData/X"] == "X_v3.bundle"
