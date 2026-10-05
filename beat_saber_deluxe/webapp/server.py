#!/usr/bin/env python3
"""
server.py — Beat Saber Deluxe web app (local backend mode).

A THIN LAYER over the pipeline CLI: read-only queries hit small adapters;
every deploy is a subprocess argv call via the single-job runner
(plan: .agent/plans/web-app-song-conversion-pipeline-interface.md).

Run:
    python3 webapp/server.py            # binds 127.0.0.1:8765, opens browser
    python3 webapp/server.py --no-browser --port 9000

The static UI detects local-backend mode via GET /api/ping; the GitHub Pages
build of the same UI stubs /api/* and swaps Deploy for the command builder.
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from pathlib import Path

from adapters import batch, beatsaver, config, deploy, loadout, paths, ps4, runner
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Beat Saber Deluxe Web App")
RUNNER = runner.SingleJobRunner()
STATIC_DIR = paths.WEBAPP_DIR / "static"


# --------------------------------------------------------------------------
# Mode detection + static UI
# --------------------------------------------------------------------------
@app.get("/api/ping")
def ping():
    """Backend heartbeat — the UI's local-backend/Pages mode switch."""
    return {"mode": "local-backend", "webapp_version": _webapp_version(),
            "pipeline_version": _pipeline_version(),
            "plugin_version": _plugin_version(),
            "pipeline_present": paths.PIPELINE.exists()}


def _webapp_version() -> str:
    v = paths.WEBAPP_DIR / "VERSION"
    try:
        return v.read_text(encoding="utf-8").strip() or "unknown"
    except OSError:
        return "unknown"


def _pipeline_version() -> str:
    v = paths.PROJECT_DIR / "VERSION"
    try:
        return v.read_text(encoding="utf-8").strip() or "unknown"
    except OSError:
        return "unknown"


def _plugin_version() -> str:
    """Parse #define PLUGIN_VERSION from the plugin source (or 'deployed' in
    a release zip, where src/ is absent — the bundled .prx is the artifact)."""
    src = paths.PROJECT_DIR / "src" / "main.cpp"
    try:
        for line in src.read_text(encoding="utf-8").splitlines():
            if "PLUGIN_VERSION" in line and '"' in line:
                return line.split('"')[1]
    except OSError:
        pass
    return "bundled"


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


# --------------------------------------------------------------------------
# Wizard: dump validation + config write
# --------------------------------------------------------------------------
@app.get("/api/dump/validate")
def dump_validate(path: str):
    """Live structural validation with per-missing-piece errors (plan §4.1b)."""
    if not path:
        raise HTTPException(400, "path parameter required")
    res = config.validate_dump(path)
    return {
        "ok": res.ok,
        "errors": res.errors,
        "warnings": res.warnings,
        "app_dir_present": res.app_dir_present,
        "patch_dir_present": res.patch_dir_present,
        "eboot_present": res.eboot_present,
        "origin_catalog_present": res.origin_catalog_present,
        "dlc_packs_found": res.dlc_packs_found,
    }


@app.get("/api/dump/default-location")
def dump_default_location():
    """Where this release expects the dump + whether it's already there."""
    default = paths.release_default_dump_dir()
    if default.exists():
        res = config.validate_dump(default)
        return {"default_path": str(default), "exists": True,
                "ok": res.ok, "errors": res.errors,
                "warnings": res.warnings,
                "dlc_packs_found": res.dlc_packs_found}
    return {"default_path": str(default), "exists": False}


@app.post("/api/config/save")
def config_save(body: dict):
    """Wizard step 4: write the fully-localized ps4_config.json."""
    try:
        cfg = config.build_wizard_config(
            dump_root=body["dump_root"],
            ps4_ip=body.get("ps4_ip", "192.168.100.117"),
            ftp_port=body.get("ftp_port", 2121),
            ftp_user=body.get("ftp_user", "anonymous"),
            ftp_password=body.get("ftp_password", ""),
        )
    except KeyError as e:
        raise HTTPException(400, f"missing field: {e}")
    written = config.save_config(cfg)
    return {"ok": True, "config_path": str(written), "config": cfg}


@app.get("/api/config")
def config_read():
    """Current ps4_config.json (or the example defaults) for the wizard."""
    return config.load_config()


@app.get("/api/catalog")
def catalog():
    """Slot/pack catalog from beat_saber_song_ids.json — drives the picker."""
    if not paths.SONG_CATALOG.exists():
        raise HTTPException(500, f"song catalog missing: {paths.SONG_CATALOG}")
    with open(paths.SONG_CATALOG, encoding="utf-8") as f:
        data = json.load(f)
    # Slim it for the UI: pack → slots (id, stock name/author, difficulties)
    albums = []
    for album in data.get("albums", []):
        albums.append({
            "pack": album.get("pack"),
            "packBundle": album.get("packBundle"),
            "songs": [
                {"songID": s.get("songID"),
                 "songName": s.get("songName"),
                 "songAuthorName": s.get("songAuthorName"),
                 "difficulties": s.get("difficulties")}
                for s in album.get("songs", [])
            ],
        })
    return {"albums": albums}


# --------------------------------------------------------------------------
# BeatSaver (server-side proxy for local-backend mode)
# --------------------------------------------------------------------------
@app.get("/api/beatsaver/search")
def beatsaver_search(q: str, page: int = 0, per_page: int = 20):
    try:
        return beatsaver.search(q, page=page, per_page=min(per_page, 50))
    except beatsaver.BeatSaverError as e:
        raise HTTPException(502, str(e))


@app.get("/api/beatsaver/map/{map_id}")
def beatsaver_map(map_id: str):
    try:
        return beatsaver.map_by_id(map_id)
    except beatsaver.BeatSaverError as e:
        if e.status == 404:
            raise HTTPException(404, f"Map {map_id} not found — it may have "
                                     "been deleted from BeatSaver.")
        raise HTTPException(502, str(e))


# --------------------------------------------------------------------------
# PS4: test connection + read-only state
# --------------------------------------------------------------------------
@app.get("/api/ps4/test")
def ps4_test():
    res = ps4.test_connection()
    return {"ok": res.ok, **(res.data or {}), "error": res.error}


@app.get("/api/ps4/state")
def ps4_state():
    """Dashboard payload: redirects summary, features, metadata counts."""
    payload: dict = {}
    red = ps4.read_redirects_summary()
    payload["redirects"] = {"ok": red.ok, "error": red.error,
                            **(red.data or {})}
    feat = ps4.read_features()
    payload["features"] = {"ok": feat.ok, "error": feat.error,
                           **(feat.data or {})}
    meta = ps4.read_song_metadata()
    if meta.ok and meta.data:
        names = (meta.data.get("song_names") or {})
        payload["song_metadata"] = {
            "ok": True,
            "custom_song_count": sum(
                1 for v in names.values()
                if isinstance(v, str) and v and " / " in v),
            "entries": names,
        }
    else:
        payload["song_metadata"] = {"ok": False, "error": meta.error}
    return payload


# --------------------------------------------------------------------------
# Feature flags (read live; apply via --features-only job)
# --------------------------------------------------------------------------
FLAG_DESCRIPTIONS = {
    "enable_plugin": "Global kill switch. OFF = the plugin is fully inert and the game plays 100% official songs on the next boot — no uninstall needed. The only flag that defaults ON when absent.",
    "enable_custom_song_replacements": "Gates all custom-song bundle redirects. OFF = every song loads its original stock audio and beatmaps (metadata labels stay).",
    "enable_song_metadata_modification": "Gates the in-game song-list name/artist swaps. OFF = songs show their official titles even when customs are deployed.",
    "enable_beatmap_mode_mapping": "Gates the extra game-mode buttons (OneSaber / NoArrows / 90Degree). OFF = the stock pack bundles + catalog are served (Standard only) — the safe posture while a pack is only partially deployed.",
}


@app.get("/api/flags")
def flags_read():
    """Live feature flags with descriptions + which are pending-apply."""
    res = ps4.read_features()
    pending = RUNNER.pending_flags if RUNNER.pending_flags else {}
    out = {
        "ok": res.ok,
        "error": res.error,
        "flags": [],
    }
    for name, value in (res.data or {}).items():
        out["flags"].append({
            "name": name,
            "value": value,
            "pending": pending.get(name, value) != value,
            "pendingValue": pending.get(name),
            "description": FLAG_DESCRIPTIONS.get(name, ""),
        })
    return out


@app.post("/api/jobs/flags-apply")
def jobs_flags_apply(body: dict):
    """Apply a whole flag loadout: one --features-only call per CHANGED flag
    would re-upload features.json repeatedly; instead build one argv with a
    --set-feature per flag (the pipeline accepts repeats)."""
    _require_config()
    wanted = body.get("flags", {})
    if not isinstance(wanted, dict) or not wanted:
        raise HTTPException(400, "flags map required")
    current_res = ps4.read_features()
    if not current_res.ok:
        raise HTTPException(502, f"Couldn't read live flags from the PS4 ({current_res.error}) "
                                 "— refusing to apply blind. Check the connection and retry.")
    current = current_res.data or {}
    argv = ["--features-only"]
    changed = 0
    for name, value in wanted.items():
        if name not in FLAG_DESCRIPTIONS:
            raise HTTPException(400, f"unknown feature flag: {name!r}")
        value = bool(value)
        if bool(current.get(name, name == "enable_plugin")) != value:
            argv += ["--set-feature", f"{name}={str(value).lower()}"]
            changed += 1
    if changed == 0:
        return {"ok": True, "job_id": None, "changed": 0,
                "message": "No changes — the PS4 flags already match this loadout."}
    RUNNER.pending_flags = {k: bool(v) for k, v in wanted.items()}
    try:
        job = RUNNER.start(argv, label=f"flags apply ({changed} changed)")
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    return {"ok": True, "job_id": job.id, "changed": changed,
            "command": deploy.pipeline_command(argv)}


# --------------------------------------------------------------------------
# Backup / Restore (thin layer over backup-beat-saber-deluxe-files.py)
# --------------------------------------------------------------------------
BACKUP_SCRIPT = paths.RELEASE_ROOT / "backup-beat-saber-deluxe-files.py"
DEFAULT_BACKUP_DIR = paths.RELEASE_ROOT / "ps4_backups"


def _backup_dir() -> Path:
    """The effective backups dir: the user's persisted setting, else default."""
    from adapters import webapp_state
    return webapp_state.get_backup_dir()


@app.get("/api/backup/list")
def backup_list():
    """List available backups (name, size, when) — read-only."""
    backup_dir = _backup_dir()
    if not backup_dir.is_dir():
        return {"backups": [], "backup_dir": str(backup_dir)}
    out = []
    for entry in sorted(backup_dir.iterdir(), reverse=True):
        if entry.is_file() and entry.suffix == ".zip":
            out.append({"name": entry.name, "size": entry.stat().st_size,
                        "mtime": entry.stat().st_mtime})
    return {"backups": out, "backup_dir": str(backup_dir)}


@app.get("/api/backup/dir")
def backup_dir_get():
    """Where backups are read from/written to (the browse-button display)."""
    d = _backup_dir()
    return {"backup_dir": str(d), "default": str(DEFAULT_BACKUP_DIR),
            "is_default": d == DEFAULT_BACKUP_DIR, "exists": d.is_dir()}


@app.post("/api/backup/dir")
def backup_dir_set(body: dict):
    """Point the Backup/Restore tab at another backups folder. No paths are
    browsed arbitrarily: we accept any user-chosen path, list zips in it, and
    pass the resolved zip path to the restore job verbatim (the script
    handles its own validation)."""
    from adapters import webapp_state
    raw = str(body.get("path", "")).strip()
    if not raw:
        raise HTTPException(400, "path required")
    resolved = webapp_state.set_backup_dir(raw)
    # list immediately so the UI refreshes from the same call
    return {"ok": True, "backup_dir": str(resolved),
            **backup_list()}


@app.get("/api/backup/browse")
def backup_dir_browse(path: str = ""):
    """Lightweight folder listing for the browse UI: child dirs only (never
    files — the picker is for folders). Empty path = start at the current
    backup dir's parent (or home when unset)."""
    from adapters import webapp_state
    try:
        base = Path(path).expanduser() if path else webapp_state.get_backup_dir().parent
        if not base.is_dir():
            raise HTTPException(400, f"not a folder: {base}")
    except (OSError, ValueError) as e:
        raise HTTPException(400, f"invalid path: {e}")
    try:
        children = sorted(
            (d for d in base.iterdir() if d.is_dir()),
            key=lambda d: d.name.lower())
    except PermissionError:
        raise HTTPException(403, f"permission denied: {base}")
    return {"path": str(base), "parent": str(base.parent) if base.parent != base else None,
            "dirs": [{"name": d.name, "path": str(d)} for d in children]}


@app.post("/api/jobs/backup")
def jobs_backup(body: dict):
    """Run the backup script as a job. body: {"clean_ps4": bool}"""
    if not BACKUP_SCRIPT.exists():
        raise HTTPException(500, f"backup script missing: {BACKUP_SCRIPT}")
    clean = bool(body.get("clean_ps4", False))
    argv = ["backup"] + (["--clean-ps4"] if clean else [])
    # Custom backups folder → the script's --out flag (default dir needs no flag)
    backup_dir = _backup_dir()
    if backup_dir != DEFAULT_BACKUP_DIR:
        argv += ["--out", str(backup_dir)]
    try:
        job = RUNNER.start_script(str(BACKUP_SCRIPT), argv,
                                  label=f"backup{' + clean-ps4' if clean else ''}")
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    return {"ok": True, "job_id": job.id,
            "command": f"python3 backup-beat-saber-deluxe-files.py {' '.join(argv)}"}


@app.post("/api/jobs/restore")
def jobs_restore(body: dict):
    """Restore a backup as a job. body: {"backup": name, "clean_ps4": bool}.
    DANGEROUS: overwrites the PS4's BSD state — confirm posture in the UI."""
    if not BACKUP_SCRIPT.exists():
        raise HTTPException(500, f"backup script missing: {BACKUP_SCRIPT}")
    name = str(body.get("backup", "")).strip()
    if not name or ".." in name or "/" in name:
        raise HTTPException(400, "backup name required (no paths)")
    path = _backup_dir() / name
    if not path.exists():
        raise HTTPException(404, f"no such backup: {name}")
    clean = bool(body.get("clean_ps4", False))
    argv = ["restore", str(path)] + (["--clean-ps4"] if clean else [])
    try:
        job = RUNNER.start_script(str(BACKUP_SCRIPT), argv,
                                  label=f"restore {name}{' + clean-ps4' if clean else ''}")
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    return {"ok": True, "job_id": job.id,
            "command": f"python3 backup-beat-saber-deluxe-files.py {' '.join(argv)}"}


# --------------------------------------------------------------------------
# Batch deployments (example-script packs + custom batches)
# --------------------------------------------------------------------------
@app.get("/api/batch/examples")
def batch_examples():
    """The 34 example-script packs, parsed live from the scripts themselves
    (the scripts stay the single source of truth)."""
    return {"packs": batch.parse_example_scripts()}


@app.get("/api/batch/custom")
def batch_custom_list():
    """Saved custom batches (JSON files in webapp/batches/)."""
    return {"batches": batch.list_custom_batches()}


@app.get("/api/batch/custom/{filename}")
def batch_custom_load(filename: str):
    try:
        return {"ok": True, "batch": batch.load_custom_batch(filename)}
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except (ValueError, json.JSONDecodeError) as e:
        raise HTTPException(400, str(e))


@app.post("/api/batch/custom")
def batch_custom_save(body: dict):
    """Save (or overwrite) a custom batch. body: {"filename": optional,
    "batch": {format/version/name/description/songs}}."""
    try:
        saved = batch.save_custom_batch(
            body.get("batch", body),
            body.get("filename") or None)
        return {"ok": True, **saved}
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.delete("/api/batch/custom/{filename}")
def batch_custom_delete(filename: str):
    try:
        batch.delete_custom_batch(filename)
        return {"ok": True}
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/jobs/batch")
def jobs_batch(body: dict):
    """Run a batch as a sequence of --deploy-full jobs (one at a time — the
    runner's single-job rule; the client drives them serially and shows one
    live console). body: {"songs": [{map_id, target, ...}]}."""
    _require_config()
    songs = body.get("songs", [])
    if not isinstance(songs, list) or not songs:
        raise HTTPException(400, "songs list required")
    # validate every entry BEFORE starting anything (fail fast, deploy nothing)
    for i, s in enumerate(songs):
        if not str(s.get("map_id", "")).strip():
            raise HTTPException(400, f"songs[{i}].map_id required")
        if not str(s.get("target", "")).strip():
            raise HTTPException(400, f"songs[{i}].target required")
    argv = []
    for s in songs:
        opts = deploy.DeployOptions(
            map_id=str(s["map_id"]).strip(),
            target=str(s["target"]).strip(),
            audio=s.get("audio", "pcm16"),
            pad_fsb5=bool(s.get("pad_fsb5", False)),
            convert_to_v3=bool(s.get("convert_to_v3", True)),
            deploy_full=True,
            skip_plugin=bool(s.get("skip_plugin", False)),
            song_name=str(s.get("song_name", "")).strip(),
            artist=str(s.get("artist", "")).strip(),
        )
        try:
            argv.append(opts.build_argv())
        except ValueError as e:
            raise HTTPException(400, f"songs[{i}]: {e}")
    # Run the batch as ONE shell-equivalent job: the runner gets a small
    # driver script that executes each argv in sequence, stopping at the
    # first failure (the exact semantics of the chained example scripts).
    driver = paths.WEBAPP_DIR / "batch_runner.py"
    if not driver.exists():
        raise HTTPException(500, f"batch driver missing: {driver}")
    payload = json.dumps(argv)
    try:
        job = RUNNER.start_script(
            str(driver), ["--jobs", payload],
            label=f"batch ({len(argv)} songs)")
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    return {"ok": True, "job_id": job.id, "count": len(argv),
            "command": f"batch deploy: {len(argv)} songs"}


# --------------------------------------------------------------------------
# Feature requests (GitHub issue builder — client-side, works in Pages mode)
# --------------------------------------------------------------------------
@app.get("/api/feature-request/template")
def feature_request_template():
    """Repo coordinates for the issue-builder (client composes the URL; in
    Pages mode this is baked in — the endpoint exists for parity)."""
    return {
        "repo": "free5ty1e/BeatSaberPcCustomSongToPs4InstallConverter",
        "issue_url": "https://github.com/free5ty1e/BeatSaberPcCustomSongToPs4InstallConverter/issues/new",
        "labels": ["webapp feature request"],
    }


# --------------------------------------------------------------------------
# Loadout tables (Manage Songs + Full Loadout tabs)
# --------------------------------------------------------------------------
@app.get("/api/loadout")
def loadout_state():
    """
    Full merge: every catalog pack/slot × live redirects × song metadata.

    Read failures are explicit (never "nothing deployed"): the payload always
    carries per-source read status the UI must surface when not ok.
    """
    res = ps4.read_deployment_state()
    merged = loadout.loadout_from_state(res.data or {})
    merged["readStatus"] = {
        "redirectsOk": not (res.data or {}).get("redirects_read_error"),
        "metadataOk": not (res.data or {}).get("metadata_read_error"),
        "afrOk": not (res.data or {}).get("afr_read_error"),
        "redirectsReadError": (res.data or {}).get("redirects_read_error"),
        "metadataReadError": (res.data or {}).get("metadata_read_error"),
        "afrReadError": (res.data or {}).get("afr_read_error"),
    }
    return merged


@app.get("/api/loadout/packs")
def loadout_packs():
    """Pack list for the Manage-Songs dropdown (from the local catalog —
    works even when the PS4 is offline)."""
    catalog = loadout.load_catalog()
    return {"packs": sorted(catalog.keys()),
            "songCounts": {p: len(s) for p, s in catalog.items()}}


# --------------------------------------------------------------------------
# Jobs: deploy + flags + clear + verify (ALL via the single-job runner)
# --------------------------------------------------------------------------
def _require_config() -> None:
    """Deploy pages refuse to run without a wizard-written config."""
    if not paths.CONFIG_PATH.exists():
        raise HTTPException(
            400, "No ps4_config.json yet — run the Setup Wizard first "
                 "(the pipeline's built-in defaults are devcontainer-absolute "
                 "and would misdirect the deploy).")


@app.post("/api/jobs/deploy")
def jobs_deploy(body: dict):
    _require_config()
    opts = deploy.DeployOptions(
        map_id=str(body.get("map_id", "")).strip(),
        target=str(body.get("target", "")).strip(),
        audio=body.get("audio", "pcm16"),
        pad_fsb5=bool(body.get("pad_fsb5", False)),
        convert_to_v3=bool(body.get("convert_to_v3", True)),
        deploy_full=bool(body.get("deploy_full", True)),
        skip_plugin=bool(body.get("skip_plugin", False)),
        song_name=str(body.get("song_name", "")).strip(),
        artist=str(body.get("artist", "")).strip(),
        enable_modes=str(body.get("enable_modes", "")).strip(),
    )
    try:
        argv = opts.build_argv()
    except ValueError as e:
        raise HTTPException(400, str(e))
    try:
        job = RUNNER.start(argv, label=f"deploy {opts.describe()}")
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    return {"ok": True, "job_id": job.id,
            "command": deploy.pipeline_command(argv)}


@app.post("/api/jobs/flags")
def jobs_flags(body: dict):
    _require_config()
    name = str(body.get("flag", "")).strip()
    value = bool(body.get("value", True))
    if not name or not name.startswith("enable_"):
        raise HTTPException(400, f"unknown feature flag: {name!r}")
    argv = deploy.flags_only_command(name, value)
    try:
        job = RUNNER.start(argv, label=f"flags {name}={value}")
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    return {"ok": True, "job_id": job.id,
            "command": deploy.pipeline_command(argv)}


@app.post("/api/jobs/clear-target")
def jobs_clear_target(body: dict):
    _require_config()
    slot = str(body.get("slot", "")).strip()
    if not slot:
        raise HTTPException(400, "slot required")
    argv = deploy.clear_target_command(slot)
    try:
        job = RUNNER.start(argv, label=f"clear {slot}")
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    return {"ok": True, "job_id": job.id,
            "command": deploy.pipeline_command(argv)}


@app.post("/api/jobs/verify")
def jobs_verify():
    _require_config()
    argv = deploy.verify_command()
    try:
        job = RUNNER.start(argv, label="verify-ps4")
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    return {"ok": True, "job_id": job.id,
            "command": deploy.pipeline_command(argv)}


@app.get("/api/jobs/status")
def jobs_status():
    return RUNNER.status()


@app.post("/api/jobs/cancel")
def jobs_cancel():
    return {"ok": RUNNER.cancel()}


@app.get("/api/jobs/lines")
def jobs_lines(after: int = 0):
    """Long-poll contract: returns (new_index, lines[after:])."""
    index, lines = RUNNER.lines_since(after)
    return {"index": index, "lines": lines,
            **RUNNER.status()}


# SSE variant (Phase 1 uses simple long-poll; kept for parity with the plan's
# architecture diagram — browsers with EventSource prefer this endpoint).
@app.get("/api/stream")
def stream():
    def event_gen():
        index = 0
        yield "data: {\"type\": \"start\"}\n\n"
        while True:
            index, lines = RUNNER.lines_since(index)
            if lines:
                payload = json.dumps({"type": "lines", "lines": lines})
                yield f"data: {payload}\n\n"
            status = RUNNER.status()
            if not status["running"] and status["job"] is not None:
                payload = json.dumps({"type": "end", "status": status["job"]})
                yield f"data: {payload}\n\n"
                return
            time.sleep(0.7)

    return StreamingResponse(event_gen(), media_type="text/event-stream")


# --------------------------------------------------------------------------
# Pages command-builder support (works in BOTH modes — pure function)
# --------------------------------------------------------------------------
@app.get("/api/command-preview")
def command_preview(map_id: str, target: str, audio: str = "pcm16",
                     pad_fsb5: bool = False, convert_to_v3: bool = True,
                     deploy_full: bool = True, skip_plugin: bool = False):
    """The exact command the Deploy button would run (no config required)."""
    opts = deploy.DeployOptions(
        map_id=map_id, target=target, audio=audio, pad_fsb5=pad_fsb5,
        convert_to_v3=convert_to_v3, deploy_full=deploy_full,
        skip_plugin=skip_plugin)
    try:
        argv = opts.build_argv()
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"command": deploy.pipeline_command(argv)}


# Static assets (must be mounted LAST so /api routes win)
if Path(STATIC_DIR).exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1",
                        help="local only by default — do not expose the PS4's "
                             "FTP credentials on the network")
    parser.add_argument("--no-browser", action="store_true",
                        help="don't auto-open the browser on start")
    args = parser.parse_args()

    print(f"Beat Saber Deluxe web app — http://{args.host}:{args.port}")
    print(f"  release root: {paths.RELEASE_ROOT}")
    print(f"  pipeline:     {paths.find_pipeline()}")
    if not args.no_browser:
        import webbrowser
        threading.Timer(1.0, lambda: webbrowser.open(
            f"http://{args.host}:{args.port}")).start()
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
