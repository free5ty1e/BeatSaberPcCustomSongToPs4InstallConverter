"""
ps4.py — read-only live PS4 state adapter (banner-free transport ONLY).

Every read goes through `_fetch_remote_file`: lftp `get` into a fresh
mktemp -d dir (NEVER `lftp cat` — banners contaminate stdout on slow Wi-Fi
links; fast dev rigs never see it. See every pitfall in
.agent/llm-wiki-knowledge-base/lftp-ftp-pitfalls.md) + first-`{`-to-last-`}`
JSON extraction, with retries. A failed read returns READ-FAILED status —
NEVER rendered as an empty/zero state (Exp 237/239/240 lesson, plan §9.4
invariant 3).

Read-only by design (plan §9.4 invariant 6): the PS4 is production; every
mutation happens through pipeline subprocess deploys, not this module.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .config import load_config

AFR_TITLE_DIR = "/data/GoldHEN/AFR/CUSA12878"
PS4_FEATURES = f"{AFR_TITLE_DIR}/features.json"
PS4_REDIRECTS = f"{AFR_TITLE_DIR}/redirects.json"
PS4_SONG_METADATA = f"{AFR_TITLE_DIR}/song_metadata.json"

# enable_plugin defaults TRUE when absent — the ONLY flag that does
# (plan §9.4 invariant 5). Unknown/absent renders as ON for that key.
DEFAULTS_TRUE = {"enable_plugin"}
KNOWN_FLAGS = ("enable_plugin", "enable_beatmap_mode_mapping",
               "enable_song_metadata_modification", "enable_custom_song_replacement")


@dataclass
class ReadResult:
    """A read that can fail loudly — never collapse failure into emptiness."""

    ok: bool = False
    data: dict | None = None
    error: str = ""
    raw_bytes: int = 0


def _ps4_endpoint() -> tuple[str, str, int]:
    """(host, user_part, port) from ps4_config.json — pitfall 6: the reliable
    anonymous form is user AND password ('anonymous:anonymous')."""
    cfg = load_config().get("ps4", {})
    host = cfg.get("ip", "192.168.100.117")
    user = cfg.get("ftp_user", "anonymous")
    pw = cfg.get("ftp_password", "")
    user_part = f"{user}:{pw}" if pw else f"{user}:anonymous"
    return host, user_part, int(cfg.get("ftp_port", 2121))


def _run_lftp(host: str, user_part: str, port: int, commands: list[str],
              timeout: int = 30) -> tuple[int, str]:
    """Run lftp with the reliable anonymous form (pitfall 6: user AND password)."""
    joined = "; ".join(commands) + "; quit"
    try:
        r = subprocess.run(
            ["lftp", "-u", user_part, "-p", str(port), host, "-e", joined],
            capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout + r.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return 1, str(e)


def _extract_json_object(text: str) -> dict | None:
    """
    Banner-proof JSON extraction (pitfall 1 — the Exp 240 lesson).

    First-`{`-to-LAST-`}` is NOT sufficient: a trailing banner can itself
    start with `}` ('}156 bytes transferred'), so rfind grabs the banner's
    brace and the slice becomes invalid. The proven pattern (Exp 221, the
    one ps4_state.py uses): scan from the first `{` and let
    json.JSONDecoder().raw_decode() parse ONE complete object, ignoring
    whatever follows. If the first `{` doesn't parse (leading banner with a
    brace in it), keep scanning subsequent `{` positions.
    """
    decoder = json.JSONDecoder()
    pos = text.find("{")
    while pos != -1:
        try:
            obj, _ = decoder.raw_decode(text, pos)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
        pos = text.find("{", pos + 1)
    return None


def fetch_remote_json(remote_path: str, retries: int = 3) -> ReadResult:
    """Banner-free JSON read from the PS4 (the one transport, everywhere)."""
    host, user_part, port = _ps4_endpoint()
    last_err = ""
    for attempt in range(1, retries + 1):
        with tempfile.TemporaryDirectory() as tmpd:  # mktemp -d, NOT mktemp (pitfall 2)
            local = Path(tmpd) / "f"
            rc, out = _run_lftp(host, user_part, port, [
                f"get {remote_path} -o {local}"])
            # NOTE: paths must be quoted when they contain shell metachars
            # (pitfall 4) — remote_path here comes from our own constants,
            # which contain no metacharacters; user input never reaches this.
            if rc == 0 and local.exists() and local.stat().st_size > 0:
                text = local.read_text(encoding="utf-8", errors="replace")
                data = _extract_json_object(text)
                if data is not None:
                    return ReadResult(ok=True, data=data,
                                      raw_bytes=len(text))
                last_err = f"parse failed (attempt {attempt})"
            else:
                last_err = out.strip().splitlines()[-1] if out.strip() else f"lftp rc={rc}"
    return ReadResult(ok=False, error=last_err)


def list_afr_dir() -> ReadResult:
    """List the AFR title dir with sizes — the Test-Connection payload."""
    host, user_part, port = _ps4_endpoint()
    rc, out = _run_lftp(host, user_part, port, [f"ls {AFR_TITLE_DIR}"])
    if rc != 0 or not out.strip():
        return ReadResult(ok=False, error=out.strip() or "empty listing")
    files: dict[str, int] = {}
    for line in out.splitlines():
        parts = line.split()
        # GoldHEN FTPD listing: perms ... size name
        if len(parts) >= 9:
            try:
                files[" ".join(parts[8:])] = int(parts[4])
            except ValueError:
                continue
    if not files:
        return ReadResult(ok=False, error="no parsable entries")
    return ReadResult(ok=True, data={"files": files, "count": len(files)})


def read_features() -> ReadResult:
    """Live features.json; applies the enable_plugin-defaults-TRUE rule."""
    res = fetch_remote_json(PS4_FEATURES)
    if not res.ok:
        return res
    raw = res.data or {}
    features = raw.get("features", raw)
    rendered: dict[str, bool] = {}
    for name in KNOWN_FLAGS:
        if name in features:
            rendered[name] = bool(features[name])
        else:
            rendered[name] = name in DEFAULTS_TRUE
    res.data = rendered
    return res


def read_redirects_summary() -> ReadResult:
    """redirects.json projected to counts + per-kind entries (dashboard)."""
    res = fetch_remote_json(PS4_REDIRECTS)
    if not res.ok:
        return res
    redirects = (res.data or {}).get("redirects", {})
    songs = [k for k in redirects if k.startswith("BeatmapLevelsData/")]
    packs = [k for k in redirects if "_pack_assets_all_" in k]
    catalog = [k for k in redirects if k == "aa/catalog.json"]
    res.data = {
        "total": len(redirects),
        "song_count": len(songs),
        "pack_count": len(packs),
        "catalog_redirect_present": bool(catalog),
        "song_entries": sorted(songs),
        "pack_entries": sorted(packs),
    }
    return res


def read_song_metadata() -> ReadResult:
    """song_metadata.json (song_names/song_artists) — the metadata dashboard."""
    return fetch_remote_json(PS4_SONG_METADATA)


def list_deployed_slot_bundles() -> ReadResult:
    """
    List every `<slot>_v3.bundle` file in the AFR dir (the deployed payloads).

    Deployed-truth model (verified against live state + plugin source):
    - the game serves a custom song ONLY when redirects.json carries
      `BeatmapLevelsData/<slot>` → the bundle (open_hook matches on the
      redirect table — nothing else);
    - a `<slot>_v3.bundle` present WITHOUT a redirect entry is a STALE
      payload: uploaded by an earlier flow but not currently served.
      The loadout table distinguishes served (redirect) vs stale (file only)
      instead of hiding either.
    """
    res = list_afr_dir()
    if not res.ok:
        return res
    files = (res.data or {}).get("files", {})
    suffix = load_config().get("paths", {}).get("afr_target_suffix", "_v3.bundle")
    bundles = sorted(name[: -len(suffix)] for name in files
                     if name.endswith(suffix) and not name.startswith("."))
    res.data = {"slot_bundles": bundles, "count": len(bundles)}
    return res


def read_deployment_state() -> ReadResult:
    """
    One read for BOTH state files (the loadout tables need them together).

    Returns data={"redirects": {...}, "song_metadata": {...}} — each inner
    value is the RAW parsed file (redirects dict; song_names/song_artists
    dicts) so the pure merge in loadout.py never does I/O. A failed half
    carries {"ok": false, "error": ...} (never rendered as empty-truth).
    """
    red = fetch_remote_json(PS4_REDIRECTS)
    meta = fetch_remote_json(PS4_SONG_METADATA)
    data: dict = {}
    if red.ok:
        data["redirects"] = (red.data or {}).get("redirects", {})
    else:
        data["redirects_read_error"] = red.error
    if meta.ok:
        md = meta.data or {}
        data["song_names"] = md.get("song_names", {})
        data["song_artists"] = md.get("song_artists", {})
    else:
        data["metadata_read_error"] = meta.error
    # AFR file listing (third truth signal: deployed bundles on disk)
    afr = list_deployed_slot_bundles()
    if afr.ok:
        data["slot_bundles"] = (afr.data or {}).get("slot_bundles", [])
    else:
        data["afr_read_error"] = afr.error
    return ReadResult(ok=red.ok or meta.ok,
                      data=data,
                      error="; ".join(e for e in (red.error, meta.error, afr.error) if e))


def test_connection() -> ReadResult:
    """Reachability probe: anonymous login + AFR dir listing."""
    res = list_afr_dir()
    if res.ok:
        res.data["status"] = "reachable"
    else:
        res.data = {"status": "unreachable", "error": res.error}
    return res
