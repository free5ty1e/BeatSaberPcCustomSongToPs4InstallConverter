# Beat Saber Deluxe — Web App Changelog

The web app is a thin UI layer over the pipeline CLI (`tools/full_custom_song_pipeline.py`).
It never re-implements conversion, deploy, or validation logic — every deploy is a
subprocess argv call to the pipeline (plan:
`.agent/plans/web-app-song-conversion-pipeline-interface.md`).

## [0.1.0] — 2026-09-29 (Exp 244)
### Added
- Phase 1 skeleton (plan §5): FastAPI server (`webapp/server.py`, binds 127.0.0.1
  only) + static UI shell (Setup Wizard, Song Picker, Deploy) with local-backend /
  Pages command-builder mode detection (`/api/ping` heartbeat).
- Adapters, one module per pipeline subsystem: `adapters/config.py`
  (ps4_config.json read/write + validation + wizard dump validation with
  per-missing-piece errors and found-DLC confidence list), `adapters/beatsaver.py`
  (search/map-by-id via the public API), `adapters/deploy.py` (the 56-flag CLI
  surface → typed argv builder), `adapters/ps4.py` (banner-free FTP state reads),
  `adapters/runner.py` (single-job subprocess executor with SSE log streaming).
- Single-job rule: one pipeline job at a time (state files are transaction
  records — concurrent writers corrupt them, plan §9.4 invariant 2).
- Every PS4 read uses the `get`-to-temp-dir banner-free transport (never
  `lftp cat`) with first-`{`-to-last-`}` JSON extraction and retries
  (`.agent/llm-wiki-knowledge-base/lftp-ftp-pitfalls.md`, plan §9.4 invariant 3).
