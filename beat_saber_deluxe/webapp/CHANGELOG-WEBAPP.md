# Beat Saber Deluxe — Web App Changelog

The web app is a thin UI layer over the pipeline CLI (`tools/full_custom_song_pipeline.py`).
It never re-implements conversion, deploy, or validation logic — every deploy is a
subprocess argv call to the pipeline (plan:
`.agent/plans/web-app-song-conversion-pipeline-interface.md`).

## [0.4.0] — 2026-10-03 (Exp 249)
### Added
- **Backups-folder browse button** (Backup/Restore tab): the path is now
  displayed and changeable — a server-side folder browser (dirs only),
  manual path entry, "use default" reset, and persistence across server
  restarts (`webapp_state.json`, gitignored — same treatment as
  `ps4_config.json`). Backup jobs pass `--out` to the backup script when the
  folder differs from the default; restore already took absolute paths.
  New endpoints: `/api/backup/dir` (GET/POST), `/api/backup/browse`.
  The backup script gained the `--out` flag (its hardcoded default is
  unchanged for CLI users).
- **Feature-flag independence note** in the Flags tab: song-list labels
  built before a metadata-flag change keep their old text until the list is
  re-entered (from the Exp 249 audit — cosmetic, self-healing).

## [0.3.1] — 2026-10-02 (Exp 248)

## [0.3.1] — 2026-10-02 (Exp 248)
### Fixed
- **Test-suite PS4 safety (the amplifier of the Exp 248 flags bug):** webapp
  endpoint tests previously started REAL pipeline subprocesses; one
  (`flags-apply`) pushed a stale local features.json over the user's live
  console, turning the metadata flag off in-game. ALL job-starting endpoint
  tests now run against a mocked runner that records argv (asserted —
  better coverage than before), and `tests/conftest.py` blocks lftp
  uploads suite-wide. The webapp itself needed no code change — its API
  already diffs against the live state; the pipeline fix (v0.5353
  pull-before-push for flags) closes the underlying hole.

## [0.3.0] — 2026-10-02 (Exp 247)

## [0.3.0] — 2026-10-02 (Exp 247)
### Added
- **Feature Flags tab** — live per-flag read (kill switch first, with
  detailed descriptions and the enable_plugin-defaults-TRUE rule), an Apply
  button that diffs against the live PS4 state and deploys only CHANGED
  flags through `--features-only` (refuses to apply blind if the live read
  fails; unknown flags rejected), pending badges, live job log.
- **Backup / Restore tab** — thin wrapper over
  `backup-beat-saber-deluxe-files.py` (the same script the CLI uses): list
  `ps4_backups/*.zip`, backup now (with optional `--clean-ps4` behind a hard
  confirm), per-row restore (backup names sanitized — no path traversal),
  cancel, live job log. The runner gained `start_script()` with the same
  single-job/streaming/cancel guarantees as deploys.
- **Feature Request tab** — composes a prefilled GitHub issue URL (title +
  details + optional app-state footer: mode and deployed-pack summary, never
  IPs or paths); preview then open on GitHub. Works in Pages mode (client-side).
- Runner: `pending_flags` hint so the Flags page can show pending state while
  a flags job runs.

### Fixed
- **Flag-key mismatch (live smoke catch):** the PS4 wire-format key is the
  PLURAL `enable_custom_song_replacements` (the pipeline's DEFAULT_FEATURES
  key); the adapter had the singular — the Flags page showed the flag
  default-OFF when the console had it ON. Corrected across adapter + server
  + tests.
- Old runner test asserted the pre-unification error string; updated.

## [0.2.0] — 2026-09-29 (Exp 245)

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
