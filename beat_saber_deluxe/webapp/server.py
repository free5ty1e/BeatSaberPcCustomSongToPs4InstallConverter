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

from adapters import beatsaver, config, deploy, paths, ps4, runner
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Beat Saber Deluxe Web App", version="0.1.0")
RUNNER = runner.SingleJobRunner()
STATIC_DIR = paths.WEBAPP_DIR / "static"


# --------------------------------------------------------------------------
# Mode detection + static UI
# --------------------------------------------------------------------------
@app.get("/api/ping")
def ping():
    """Backend heartbeat — the UI's local-backend/Pages mode switch."""
    return {"mode": "local-backend", "webapp_version": "0.1.0",
            "pipeline_present": paths.PIPELINE.exists()}


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
