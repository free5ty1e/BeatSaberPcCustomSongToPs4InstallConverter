# Beat Saber Deluxe — Web App Changelog

The web app is a thin UI layer over the pipeline CLI (`tools/full_custom_song_pipeline.py`).
It never re-implements conversion, deploy, or validation logic — every deploy is a
subprocess argv call to the pipeline (plan:
`.agent/plans/web-app-song-conversion-pipeline-interface.md`).

## [0.2.0] — 2026-09-29 (Exp 245)
### Added
- **Manage Songs tab** — music-pack dropdown → a table of every stock song
  (slot, stock name/artist) with the custom song installed over it
  (custom name/artist from live `song_metadata.json`), per-row **Clear**
  button (goes through `--clear-target-song <songID>` as a single-job
  subprocess; surgical-revert contract shown in the confirm dialog).
- **Full Loadout tab** — every music pack and song in the game with custom
  status, printable: save-the-page or print-to-PDF support (`@media print`
  stylesheet flips to a clean light document, hides interactive chrome);
  "only packs with customs" filter; per-row Clear buttons. The generated
  document doubles as a reference of the PS4's song loadout.
- `adapters/loadout.py` — the pure catalog × redirects × song_metadata merge
  (the metadata join is case/space-insensitive: the real catalog has
  `'You Should See Me In A Crown '` vs song_metadata
  `'You Should See Me In A Crown'`); `ps4.read_deployment_state()` — one
  banner-free read of BOTH state files with explicit per-source read errors
  (never rendered as "nothing deployed").
- `/api/loadout` + `/api/loadout/packs` endpoints (packs list works even
  with the PS4 offline — catalog-only).
- **GitHub Pages build** — `webapp/build_pages.py` stamps the same UI bundle
  with `data-mode="pages"` (instant command-builder mode: Deploy becomes
  "copy the generated command") + a mode banner; `.github/workflows/pages.yml`
  builds, smoke-tests, and deploys it to Pages on every push to main.
- CI/release coverage: webapp tests' deps (fastapi/uvicorn/httpx) added to
  `requirements-test.txt` (CI previously would have failed on the new tests);
  `ci.yml` + plugin-build lint now cover `webapp/` and `tests/`; the release
  workflow smoke-tests the webapp server (imports, routes, static files) and
  bundles `webapp/` into the release zip; CI_RELEASE.md documents the webapp
  section + Pages mode.

## [0.1.0] — 2026-09-29 (Exp 244)

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
