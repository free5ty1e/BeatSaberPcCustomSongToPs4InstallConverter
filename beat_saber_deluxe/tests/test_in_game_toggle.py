"""In-game global plugin toggle (M11, Exp 278) — hermetic source-level tests.

The plugin change is C++ (compiled by make, not unit-testable from Python), so
these tests pin the researched facts and the behavioral contract in the source,
mirroring the TestSongPreviewsFlagGating pattern. The researched facts (hook
target, button bits, struct layout, time source) were verified against the
game's real eboot imports + two independent SDK sources — see the plan:
.agent/plans/in-game-global-plugin-enable-toggle-plan.md
"""
import os
import re
import sys

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools')
sys.path.insert(0, TOOLS)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_CPP = os.path.join(PROJECT_ROOT, "src", "main.cpp")
WEBAPP = os.path.join(PROJECT_ROOT, "webapp")


def _code():
    with open(MAIN_CPP, encoding="utf-8") as f:
        return f.read()


def _def_body(code, name, span=2000):
    """Find a function DEFINITION (not a forward declaration) and return its
    first `span` chars. Definitions have a '{' before the next ';'."""
    for variant in (f"static void* {name}(", f"static void {name}(",
                    f"static int {name}("):
        idx = 0
        while True:
            idx = code.find(variant, idx)
            if idx < 0:
                break
            brace = code.find("{", idx)
            semi = code.find(";", idx)
            if brace >= 0 and (semi < 0 or brace < semi):
                return code[idx:idx + span]
            idx += 1
    return ""


class TestInGameToggleFlagGating:
    """The enable_in_game_plugin_toggle flag gates the pad hook install AND
    the hook body (feature-flag enforcement, CLAUDE.md §2)."""

    def test_plugin_parses_toggle_flag(self):
        code = _code()
        assert 'strcmp(key, "enable_in_game_plugin_toggle")' in code
        assert "g_feature_in_game_plugin_toggle" in code

    def test_flag_not_decorative(self):
        """Real conditional use outside load_features (gating-audit rule)."""
        code = _code()
        lf_start = code.find("static void load_features(")
        lf_end = code.find('extern "C" FILE *fopen', lf_start)
        lf_body = code[lf_start:lf_end]
        rest = code.replace(lf_body, "")
        conds = re.findall(r"(?:if\s*\(|&&\s*|!\s*)g_feature_in_game_plugin_toggle", rest)
        assert len(conds) >= 1, \
            "g_feature_in_game_plugin_toggle has no behavioral gate outside load_features"

    def test_hotkey_not_gated_by_kill_switch(self):
        """ONE-WAY-DOOR PREVENTION (plan §2.4): the hotkey must keep working
        when enable_plugin=false, or a user toggled OFF could never re-enable
        without a PC. No toggle-path function may require g_feature_plugin_enabled."""
        code = _code()
        for fn in ("try_install_pad_hook", "pad_read_hook", "in_game_toggle_plugin"):
            body = _def_body(code, fn)
            assert body, f"{fn} definition not found"
            assert "g_feature_plugin_enabled" not in body, \
                f"{fn} must NOT be gated by the kill switch (one-way-door rule)"

    def test_toggle_only_writes_file_not_runtime_state(self):
        """PERSIST-ONLY (plan §2.2): the flip must not change the session's
        runtime state — in_game_toggle_plugin never assigns g_feature_plugin_enabled."""
        body = _def_body(_code(), "in_game_toggle_plugin")
        assert "g_feature_plugin_enabled =" not in body.replace("==", "")
        assert "features.json" in body or "FEATURES_PATH" in body


class TestInGameToggleResearchedFacts:
    """Pins the Exp-278 research: hook target, button bits, hold timing.
    Verified against the game's real imports (development/scripts/ps4_elf_imports.py
    + aerolib NID decode) and dual-checked SDK sources (OpenOrbis + shadPS4Plus)."""

    def test_hook_target_is_scePadRead(self):
        """Beat Saber reads pads via scePadRead (NID q1cHNfGycLI in the eboot
        imports); scePadReadState is NOT imported. Pin the hook target."""
        code = _code()
        assert 'dlsym(RTLD_DEFAULT, "scePadRead")' in code
        assert 'dlsym(RTLD_DEFAULT, "scePadReadState")' not in code

    def test_l3_r3_button_bits(self):
        """L3=0x0002, R3=0x0004 (dual-verified); clean combo = exactly 0x0006."""
        code = _code()
        assert "#define PAD_BUTTON_L3 0x0002u" in code
        assert "#define PAD_BUTTON_R3 0x0004u" in code
        assert "(PAD_BUTTON_L3 | PAD_BUTTON_R3)" in code

    def test_clean_combo_exact_match(self):
        """Anti-accidental-trigger: the trigger requires buttons == the combo
        EXACTLY (any other digital bit breaks it) — not a bitmask test."""
        body = _def_body(_code(), "pad_read_hook")
        assert "buttons == PAD_TOGGLE_COMBO" in body
        assert "buttons & PAD_TOGGLE_COMBO" not in body

    def test_two_second_hold_with_kernel_time(self):
        """2 s hold timed by sceKernelGetProcessTime (µs) = 2,000,000."""
        code = _code()
        assert "#define PAD_TOGGLE_HOLD_US 2000000ULL" in code
        assert "sceKernelGetProcessTime()" in _def_body(code, "pad_read_hook")

    def test_release_latch(self):
        """After a toggle fires, the combo must be RELEASED before the next."""
        body = _def_body(_code(), "pad_read_hook")
        assert "g_toggle_latched = 0" in body  # cleared on non-combo poll
        assert "!g_toggle_latched" in body      # blocks re-fire while held

    def test_surgical_in_place_flip(self):
        """The flip edits the enable_plugin value in place (memmove for the
        1-byte true/false size delta), preserving every other key (plan §2.3)."""
        body = _def_body(_code(), "in_game_toggle_plugin", span=6000)
        assert 'strstr(buf, "\\"enable_plugin\\"")' in body
        assert "memmove(" in body
        assert "O_TRUNC" in body  # write-back replaces the file atomically

    def test_notification_shows_state_and_restart_hint(self):
        code = _code()
        assert "Plugin %s\\nRestart game to apply" in code
        assert '"ENABLED"' in code.replace('"', '"') and "ENABLED" in code
        assert "DISABLED" in code


class TestInGameToggleVersions:
    def test_plugin_version_bumped(self):
        assert '#define PLUGIN_VERSION "v0.8049"' in _code()

    def test_toast_counts_five_flags(self):
        code = _code()
        assert "(%d/5 features ON)" in code
        # the new flag participates in the enabled_count sum
        tail = code.split("enabled_count =")[1].split("memset")[0]
        assert "g_feature_in_game_plugin_toggle" in tail


class TestInGameTogglePipeline:
    def test_default_features_has_toggle_flag(self):
        import full_custom_song_pipeline as fp
        assert fp.DEFAULT_FEATURES.get("enable_in_game_plugin_toggle") is False


class TestInGameToggleWebappSurfaces:
    """The webapp must list + describe the 5th flag everywhere it surfaces flags."""

    def test_adapter_known_flags(self):
        with open(os.path.join(WEBAPP, "adapters", "ps4.py"), encoding="utf-8") as f:
            code = f.read()
        assert '"enable_in_game_plugin_toggle"' in code

    def test_server_flag_descriptions(self):
        with open(os.path.join(WEBAPP, "server.py"), encoding="utf-8") as f:
            code = f.read()
        assert '"enable_in_game_plugin_toggle"' in code

    def test_static_toast_and_flag_list(self):
        with open(os.path.join(WEBAPP, "static", "app.js"), encoding="utf-8") as f:
            code = f.read()
        assert '"enable_in_game_plugin_toggle"' in code
        assert 'TOAST_VERSION = "v0.8049"' in code

    def test_index_placeholder_five_of_five(self):
        with open(os.path.join(WEBAPP, "static", "index.html"), encoding="utf-8") as f:
            code = f.read()
        assert "(5/5 features ON)" in code
        assert "(4/4 features ON)" not in code
