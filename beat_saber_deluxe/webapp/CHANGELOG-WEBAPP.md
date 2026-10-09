# Beat Saber Deluxe — Web App Changelog

The web app is a thin UI layer over the pipeline CLI (`tools/full_custom_song_pipeline.py`).
It never re-implements conversion, deploy, or validation logic — every deploy is a
subprocess argv call to the pipeline (plan:
`.agent/plans/web-app-song-conversion-pipeline-interface.md`).

## [0.6.3] — 2026-10-08 (Exp 266)
### Fixed
- **Pages mode landed on the Setup Wizard instead of Get Started (found on the LIVE Pages deploy by the user, minutes after PR #5 merged).** Root cause: a landing race — `detectMode()`'s pages branch clicks the Get Started button (correct), but the `DOMContentLoaded` handler at the script's tail then runs `showPage("wizard")` UNCONDITIONALLY, and it fires after the script bottom — stomping the landing back to the wizard on every fast connection. The badge/banner/tab-hiding all worked (they're not overwritten later), which is exactly why the page LOOKED correct except for the landing. Fix: the DOMContentLoaded wizard landing is now mode-aware — `if (state.mode !== "pages") showPage("wizard")`; pages mode keeps the Get Started landing, local mode keeps the wizard. The hidden-tabs behavior the user noticed ("most of the tabs are missing") is the DESIGNED pages mode — the 6 backend-only tabs (PS4, Manage Songs, Loadout, Flags, Batch, Backup) can't function hosted and hide; verified all 12 buttons ship in the bundle with `local-only` markers. Proven with a browser-order headless simulation (startPage click → DOMContentLoaded guard → lands on startPage; local regression lands on wizard). Suite 807/807.

## [0.6.2] — 2026-10-07 (Exp 264)
### Fixed
- **Batch parser carried shell quoting into `--target` values** (found proving the user's failed multi-pack batch: the Britney pack's song 8 parsed as target `"Scream&Shout"` — literal quotes included — because the example scripts quote `&` for the SHELL and the parser's `\S+` regex captured the quotes as part of the slot name; the batch would have deployed to a garbage slot even after the pipeline's size-check fix). `parse_example_scripts()` now strips matching leading/trailing quotes via `_unquote()` — quotes are shell syntax, not slot names. All 34 packs re-verified: zero quoted targets remain; the Scream&Shout entry is `target: "Scream&Shout"` clean. 18 batch tests green.

## [0.6.1] — 2026-10-06 (Exp 263)
### Fixed
- **Dead-PS4 reads no longer take minutes to report "unreachable"** (Exp 263 finding, measured during release validation of webapp-0.6.0-alpha01: with the PS4 powered off, `/api/loadout` took ~3.5 min — 3 reads × 3 retries against a host lftp defaults kept retrying; a bare lftp call was measured at 12:14 min). The adapters' `_run_lftp` now sets `net:timeout 5`, `net:max-retries 1`, `net:connect-timeout 5` (the same dead read fails in 0.25s), and `fetch_remote_json` stops retrying once the error is a connectivity refusal ("No route to host" / "connection refused" / timeout / DNS) — retries remain for genuine transfer flakes. The PS4-state/Loadout tabs now surface "unreachable" in seconds instead of hanging the spinner for minutes. (Found while validating against a PS4 that was initially off; pipeline-side twin of this fix: none needed — the pipeline's reads are single-attempt with hard aborts.)

## [0.6.0] — 2026-10-06 (Exp 262)
### Added — the Get Started tab: hosted → full app in 5 guided steps
- **A guided download funnel for Pages visitors** (user request: "guide the
  user through downloading the latest release, extracting it, and running
  THAT web app for full functionality — as seamless as we can"): a new
  **Get Started** tab with a prerequisite checklist (interactive
  checkboxes: Python, jailbroken PS4 + GoldHEN FTP, Beat Saber 2.04, the
  decrypted dump with a Dump-Guide handoff link, same-network), a
  **Download the latest release** button (the `releases/latest` link —
  always current, no version updates needed), per-OS extract instructions,
  **per-OS run commands** (Windows/macOS/Linux tabs: `pip install -r
  requirements.txt` + `python webapp/server.py`, with the python-vs-python3
  and Store-redirect gotchas called out), and the wizard's 4-step finale.
- **Hosted visitors land on it**: the Pages bundle auto-opens Get Started,
  and the banner now leads with "Get Started takes you to the full app in
  ~2 minutes" — the planning-mode note and the command-builder alternative
  remain.
- The local backend gets the same tab (the handoff instructions live there
  for copy/paste convenience).
- Verified with a headless-DOM consumer test against the built bundle: nav
  wiring at load, auto-landing, relabel — plus local-mode regression.

## [0.5.5] — 2026-10-06 (Exp 261)
### Added — command-builder mode actually works on the hosted Pages site
- **The Deploy preview builds the exact pipeline command LOCALLY in pages
  mode** (the argv order mirrors `adapters/deploy.py` 1:1) — previously the
  preview called a backend endpoint that doesn't exist on the hosted site,
  so nothing appeared.
- **The Deploy button becomes "Copy deploy command"** in pages mode: copies
  the generated command (with clipboard fallback) + a note to run it on the
  machine with the ps4_dump + PS4.
- **Backend-only tabs hidden in pages mode** (PS4, Manage Songs, Full
  Loadout, Feature Flags, Batch, Backup/Restore — all require the local
  server), the wizard's Save-config button too, and the builder's injected
  pages-branch now carries the full setup (it previously returned early,
  skipping the relabel — found by a headless-DOM consumer-flow test).
- BeatSaver search, the Dump Guide (with dumper.cfg download), batch
  building + export, and the Feature Request composer all work hosted.

### Why deploys can never run on the hosted site (by design)
Browsers cannot read a local ps4_dump folder, run Python, or open FTP to
a PS4 — and GitHub Pages is static hosting. The hosted site is the
plan-and-onboard surface (find songs, learn the dump process, generate
exact commands); the release's `python3 webapp/server.py` is the surface
that actually deploys.

## [0.5.4] — 2026-10-06 (Exp 259)
### Changed
- **The example scripts now live at `docs/example-scripts/` in the REPO as
  well as the release** (moved from `.agent/docs/` — they're user-facing
  content and now the repo and release layouts are identical). The Batch
  parser's canonical path follows them; the legacy `.agent/docs/` location
  is still parsed for old checkouts (first-match wins). All references
  updated: README (script paths + chained examples + Batch description),
  the release packaging workflow (copies from the new location), the plan
  doc, the regression tests. Knowledge base updated.

## [0.5.3] — 2026-10-06 (Exp 258)
### Fixed
- **The Batch tab was EMPTY when run from an extracted release zip** (found
  in the alpha01 release audit): the script parser looked only at the repo
  layout (`.agent/docs/`), but the release zip ships the example scripts at
  `docs/example-scripts/`. The parser now checks both layouts (and an
  extracted zip's `beat_saber_deluxe/docs/example-scripts/`), first-match
  wins, no duplicates. Verified from the actual extracted alpha01 zip:
  34 packs, RS=11, BE=10, the 5-pack standard loadout = 47.
  (Superseded in 0.5.4/Exp 259: the scripts moved to docs/example-scripts/ in
  the REPO too, making the layouts identical.)

## [0.5.2] — 2026-10-04 (Exp 256)
### Fixed
- **The 5-pack multi-batch now counts 47, matching the PS4** (was 50):
  the Billie Eilish example script carried 3 songs that belong to the
  LIZZO pack (2 be loved / about damn time / cuz i love you — Lizzo stock
  slots with the same map IDs the Lizzo script already deploys). Removed
  from the BE `.sh` + companion `.md` (renumbered, count references fixed);
  the Lizzo script keeps them. Verified: the five scripts' unique slot set
  now EXACTLY equals the live PS4's 47 redirects (zero diff both ways);
  the multi-batch counter reads 11+10+11+9+6 = 47.

## [0.5.1] — 2026-10-04 (Exp 255)
### Added
- **Multi-pack batch deploys** (Batch tab, new section): a checkbox list of
  all 34 example packs with per-pack song counts; check any combination
  (e.g. the standard loadout: Rolling Stones, Billie Eilish, Britney
  Spears, Lizzo, Camelia = 50 songs), select all/none shortcuts, a live
  "N packs · M songs selected" counter, the deploy order previewed on the
  button tooltip, and a **Deploy selected music packs** button that runs
  them as ONE serial job — the web-app equivalent of chaining the example
  scripts (`script1.sh --no-prompt && script2.sh --no-prompt && …`),
  stopping at the first failure.

## [0.5.0] — 2026-10-04 (Exp 254)
### Added — the Batch tab
- **Pre-defined packs dropdown**: all 34 example-script packs, parsed LIVE
  from the example scripts (`docs/example-scripts/example_*.sh`, moved there
  from `.agent/docs/` in Exp 259; 296 song replacements — map IDs, target
  slots, and the custom song/artist names from the scripts' own comments).
  The scripts stay the single source of truth: the tab always shows exactly
  what the CLI runs.
- **Custom batch builder**: "Build a custom batch…" — add songs via the
  integrated BeatSaver search (native E/N/H filter + badges) or a
  map-ID + slot form; remove rows; name/describe; deploy.
- **Save / Load / Delete** custom batches as JSON files
  (`webapp/batches/`), with the format documented in the tab AND
  hand-editable anywhere: `{"format": "bsd-batch", "version": 1, "name":
  …, "songs": [{map_id, target, song_name, artist, audio, pad_fsb5,
  convert_to_v3}]}`.
- **Export / Import** via the browser's file dialogs — platform-agnostic by
  design (Windows/macOS/Linux browsers; nothing depends on server-side
  paths, so it also works in Pages mode for building batches).
- **Batch deploys run as ONE serial job**: `webapp/batch_runner.py` executes
  each song's `--deploy-full` in sequence through the single-job runner,
  streaming every line into the live console, STOPPING at the first failure
  (the exact `script1 && script2` semantics of the chained example scripts).
  All entries validated BEFORE anything deploys (a bad row starts nothing).

## [0.4.5] — 2026-10-04 (Exp 253)
### Fixed
- **Job panels now live at the TOP of long pages** (Manage Songs, Full
  Loadout) — they sat below the tables, invisible while a clear ran. The
  page scrolls to the panel on job start (spinner + live console in view
  immediately), and the Deploy progress row scrolls into view too.
- **Clear now refreshes the table at the right moment**: the panel's
  completion promise was fire-and-forget, so the refresh fired while the job
  was still running. `runJobWithPanel` now resolves when the job ENDS; the
  clear's refresh happens at completion.

### With pipeline v0.5354 (the "Stale" answer)
- `--clear-target-song` now removes EVERY casing variant of the slot bundle
  (deploy history wrote both `MessItUp_v3.bundle` and
  `messitup_v3.bundle`; the old clear removed only the literal-cased one —
  the leftover file, correctly detected, rendered as "stale" right after a
  clear). A cleared slot now genuinely shows **stock**.

## [0.4.4] — 2026-10-04 (Exp 252b)
### Fixed
- **The Deploy progress row still showed permanently** (and stayed after a
  deploy): it used the `hidden` ATTRIBUTE, but `.row { display: flex }`
  overrode the UA's attribute default (any author `display` beats it — the
  classic attribute-vs-specificity trap; yesterday's generic `.hidden`-class
  fix didn't cover it). Added `[hidden] { display: none !important; }` and
  the row now hides via BOTH class and attribute, toggled together. Sweep
  confirmed it was the only element in the trap.

## [0.4.3] — 2026-10-04 (Exp 252)
### Fixed
- **Job panels rendered permanently** ("Working…" + spinner on Full Loadout
  and Backup/Restore before any action): the stylesheet only had a
  `.page.hidden` rule — the generic `hidden` class had NO rule, so every
  non-page element relying on it displayed unconditionally. Added the
  standalone `.hidden { display: none; }` rule.
- **Backup dialog crash** (`Cannot set properties of null (setting
  'textContent')`): the Backup page's panel children used
  `backup-job-*` IDs while the shared panel machinery expects
  `<panelId>-*` (`backup-job-panel-*`) — the status assignment hit null.
  IDs aligned across the panel; all three panels' five children each now
  verified by a static audit + live serve check.

### Added
- **Deploy tab working-status**: a progress row (spinner + Deploying… + the
  song → slot label) shows during deploys; the Deploy button disables and
  relabels itself ("Deploying…"); both clear on completion.
- **Verify PS4 button feedback**: spinner + relabelled "Verifying…", the
  progress row, and the live console (previously silent).
- **PS4 tab loading spinner** while reading state.

## [0.4.2] — 2026-10-04 (Exp 251)
### Added
- **Version badge, lower-right corner** (user: "so I can tell when your
  changes have taken effect"): web app + pipeline + plugin versions, live
  from the server in local-backend mode (`/api/ping` now carries all three),
  baked into the Pages bundle at build time. Hidden when printing the
  loadout.

### Fixed
- **The Pages bundle 404'd its own JS/CSS** — `build_pages.py` copied assets
  to the bundle root but the HTML still referenced `/static/*`, so the entire
  app was dead at the Pages URL (the user's "is this change being served?"
  was exactly right: no JS ran at all, so the flags page — and everything
  else — was inert). The builder now rewrites the three references to
  root-relative, and the workflow's smoke-test asserts every referenced
  asset resolves in the bundle (this exact regression is pinned by tests).

## [0.4.1] — 2026-10-04 (Exp 250)
### Added
- **Live job feedback everywhere** (user request after finding the backup
  button silent mid-run): a shared job panel — spinner + Working… → ✅ Done /
  ❌ Failed status + the exact command + a live-streamed console — wired into
  Backup, Restore, and per-row Clear (Manage Songs + Full Loadout). The
  Backup button also disables + relabels itself ("Backing up…") so it can't
  be double-clicked; Apply (Flags) gets the same treatment. The Deploy page
  already streamed; it now shares the same visual language.
- **Simulated PS4 launch notification** (Flags page): a live toast preview in
  the plugin's exact boot format — `BS Deluxe vX (ON) / (N/3 features ON)`
  vs `(OFF) / (official songs only)` — recomputed as toggles flip, with a
  note explaining what the next boot will do with the current state.

### Fixed
- **CI lint was red on the PR** (blocking the merge): the Exp 245 lint-scope
  widening to `tests/` exposed ~180 pre-existing findings. All fixed
  (144 auto + hand-fixes); includes two real finds: a corrupted dev helper
  (`tests/quick_validation.py` — split `he vig_data` identifier, literal
  `\n` in source; now parses) and a typo'd assertion variable
  (`valid_rate` vs `validity_rate` in test_hevag_audio_compatibility — only
  fired on failure, i.e. exactly when you need it). Suite 770/770 green,
  lint clean across tools/ + webapp/ + tests/.
- Live backup run validated end-to-end through the panel flow (30 lines
  streamed, exit 0, zip created).

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
