"""Game-data extraction (M12, Exp 280) — hermetic tests.

The in-console extractor eliminates the PC-side dump requirement for users:
the plugin copies the files the pipeline needs from the game's own mounts
during a normal boot; --request-game-data writes the manifest, --pull-game-data
mirrors the output into the local game_data cache (a drop-in for
paths.game_dump_dir). Ownership: requests.txt pipeline/web-app-owned, status.txt
plugin-owned; failures retry on the next boot (ERR lines never match a request).
"""
import importlib.util
import os
import sys

import pytest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools')
sys.path.insert(0, TOOLS)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_CPP = os.path.join(PROJECT_ROOT, "src", "main.cpp")


def _pipeline():
    spec = importlib.util.spec_from_file_location(
        "fp_game_data", os.path.join(TOOLS, "full_custom_song_pipeline.py"))
    fp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fp)
    return fp


def _config():
    fp = _pipeline()
    return fp.load_config(os.path.join(PROJECT_ROOT, "ps4_config.json"))


class TestManifestComputation:
    """compute_game_data_manifest — from beat_saber_song_ids.json (no dump needed)."""

    def test_pack_manifest_includes_templates_bundle_and_catalog(self):
        fp = _pipeline()
        cfg = _config()
        rels = fp.compute_game_data_manifest(cfg, packs=["lizzo"])
        templates = [r for r in rels if "BeatmapLevelsData" in r]
        bundles = [r for r in rels if "_pack_assets_all_" in r]
        assert len(templates) == 9, "lizzo has 9 slots"
        assert len(bundles) == 1 and "lizzo_pack_assets_all_" in bundles[0]
        assert "Media/StreamingAssets/aa/catalog.json" in rels
        assert all(r.startswith("Media/StreamingAssets/") for r in rels)

    def test_slot_manifest_includes_its_pack_bundle(self):
        """A single-slot request needs the template + ITS pack's bundle + catalog
        (pack-mode patching reads the pack bundle)."""
        fp = _pipeline()
        rels = fp.compute_game_data_manifest(_config(), slots=["2BeLoved"])
        assert rels == [
            "Media/StreamingAssets/BeatmapLevelsData/2BeLoved",
            "Media/StreamingAssets/aa/PS4/lizzo_pack_assets_all_8bf3db217732cc18af0b9a2a32d13a9a.bundle",
            "Media/StreamingAssets/aa/catalog.json",
        ]

    def test_full_five_pack_manifest_shape(self):
        fp = _pipeline()
        rels = fp.compute_game_data_manifest(
            _config(), packs=["lizzo", "billieeilish", "britneyspears", "camellia",
                              "therollingstones"])
        assert len([r for r in rels if "BeatmapLevelsData" in r]) == 47
        assert len([r for r in rels if "_pack_assets_all_" in r]) == 5
        assert len(rels) == 53  # 47 + 5 + catalog

    def test_unknown_requests_yield_empty(self):
        fp = _pipeline()
        assert fp.compute_game_data_manifest(_config(), packs=["nosuchpack"]) == []


class TestRequestGameData:
    def _monkey_lftp(self, monkeypatch, rc=0, out=""):
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            class R:
                returncode = rc
                stdout = out
                stderr = ""
            return R()
        import subprocess
        monkeypatch.setattr(subprocess, "run", fake_run)
        return calls

    def test_requests_error_message_carries_a_fix(self, caplog, monkeypatch):
        """User directive (Exp 278h policy): every error carries a suggested fix."""
        fp = _pipeline()
        with pytest.raises(SystemExit), caplog.at_level("ERROR"):
            fp.request_game_data(_config(), packs=None, slots=None)
        assert "Nothing to request" in caplog.text

    def test_request_writes_manifest_and_pushes(self, monkeypatch, tmp_path):
        fp = _pipeline()
        calls = []
        import re
        import subprocess
        payloads = {}

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            script = " ".join(cmd)
            if "put " in script:
                m = re.search(r'put \"([^\"]+)\"', script) or re.search(r'put (\S+)', script)
                if m and os.path.exists(m.group(1)):
                    payloads["requests"] = open(m.group(1), encoding="utf-8").read()
            class R:
                returncode = 0
                stdout = "12345"
                stderr = ""
            return R()
        monkeypatch.setattr(subprocess, "run", fake_run)
        fp.request_game_data(_config(), packs=["lizzo"])
        assert "BeatmapLevelsData/2BeLoved" in payloads["requests"], \
            "the manifest carries the slot templates"
        assert "Media/StreamingAssets/aa/PS4/lizzo_pack_assets_all_" in payloads["requests"]
        assert "game_data_requests.txt" in " ".join(c[7] if len(c) > 7 else "" for c in calls) \
            or any("game_data_requests.txt" in " ".join(c) for c in calls), \
            "the lftp push targets the requests file on the PS4"


class TestPullGameData:
    def test_pull_without_status_carries_a_fix(self, caplog, monkeypatch):
        """No status file on the PS4 (nothing extracted yet) → SystemExit + fix."""
        fp = _pipeline()
        import subprocess

        class R0:
            def __init__(self):
                self.returncode = 0
                self.stdout = ""
                self.stderr = ""
        monkeypatch.setattr(subprocess, "run", lambda *a, **k: R0())
        with pytest.raises(SystemExit), caplog.at_level("ERROR"):
            fp.pull_game_data(_config())
        assert "Nothing has been extracted" in caplog.text
        assert "To fix" in caplog.text


class TestCliWiring:
    def test_flags_present_in_help(self):
        import subprocess
        r = subprocess.run(
            [sys.executable, os.path.join(TOOLS, "full_custom_song_pipeline.py"), "--help"],
            capture_output=True, text=True, timeout=30)
        for flag in ("--request-game-data", "--pull-game-data",
                     "--game-data-packs", "--game-data-slots"):
            assert flag in r.stdout, f"{flag} missing from --help"

    def test_default_features_has_extractor_flag(self):
        fp = _pipeline()
        assert fp.DEFAULT_FEATURES.get("enable_game_data_extractor") is False

    def test_config_defaults_gain_game_data_dir(self):
        """The local cache path ships as a default (PROJECT_ROOT-relative)."""
        cfg = _config()
        assert "game_data" in cfg.get("paths", {}).get("game_data_dir", "")
        fp = _pipeline()
        assert fp._get_local_game_data_dir(cfg).endswith("game_data")


class TestPluginSourcePins:
    """The extractor lives in C++ (compiled by make) — pin the behavioral
    contract in the source, mirroring the M11 toggle-test style."""

    @staticmethod
    def _code():
        with open(MAIN_CPP, encoding="utf-8") as f:
            return f.read()

    def test_plugin_parses_extractor_flag(self):
        code = self._code()
        assert 'strcmp(key, "enable_game_data_extractor")' in code
        assert "g_feature_game_data_extractor" in code

    def test_extractor_not_gated_by_kill_switch(self):
        """Like the M11 hotkey, the extractor is console-maintenance tooling —
        the enable_plugin kill switch must NOT gate it (a user can fill their
        cache regardless of the plugin's game-behavior state)."""
        code = self._code()
        def_pos = code.find("static void try_run_game_data_extractor(void) {")
        assert def_pos > 0, "extractor definition not found"
        body = code[def_pos:def_pos + 900]
        assert "g_feature_game_data_extractor" in body
        assert "g_feature_plugin_enabled" not in body

    def test_both_mount_prefixes_tried(self):
        """The game reads its assets from /archive/mount/point/ and /app0/ —
        the extractor must try BOTH (log-proven availability)."""
        code = self._code()
        assert '"/archive/mount/point/"' in code
        assert '"/app0/"' in code

    def test_requests_and_status_ownership(self):
        """requests.txt is web-app owned (plugin only reads); status.txt is
        plugin owned (web app only reads) — the pull-before-push doctrine."""
        code = self._code()
        assert 'GAMEDATA_REQUESTS_PATH AFR_BASE "/" TITLE_ID "/game_data_requests.txt"' in code
        assert 'GAMEDATA_STATUS_PATH  AFR_BASE "/" TITLE_ID "/game_data_status.txt"' in code
        # the plugin only ever APPENDS to status (never writes requests)
        req_def = code.find("GAMEDATA_REQUESTS_PATH")
        req_reads = code.find("sceKernelOpen(GAMEDATA_REQUESTS_PATH, O_RDONLY")
        assert req_reads > req_def, "requests must be opened read-only by the plugin"

    def test_line_exact_matching_prevents_false_done(self):
        """A rel that is a SUFFIX of another must not count as done via
        substring matching — the line-exact matcher prevents re-extraction
        skips from false-positiving."""
        assert "gamedata_line_present" in self._code()

    def test_err_lines_retry_next_boot(self):
        """Failures append 'ERR <rel> <reason>' which never matches a request
        line — so they are re-attempted on the next boot automatically."""
        code = self._code()
        assert '"ERR %s not-found-on-mounts"' in code or \
               '"ERR %s dest-open-failed"' in code or "ERR %s" in code

    def test_once_per_boot_state(self):
        code = self._code()
        assert "g_extractor_state" in code

    def test_plugin_version_bumped(self):
        assert '#define PLUGIN_VERSION "v0.8054"' in self._code()

    def test_toast_counts_six_flags(self):
        code = self._code()
        assert "(%d/6 features ON)" in code
        tail = code.split("enabled_count =")[1].split("memset")[0]
        assert "g_feature_game_data_extractor" in tail
