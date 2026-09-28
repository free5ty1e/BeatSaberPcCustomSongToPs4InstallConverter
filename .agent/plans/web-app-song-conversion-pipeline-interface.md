# Web App Interface for the Song-Conversion Pipeline

**Status:** PLANNED — the next milestone after the v0.8047/v0.5351 release (roadmap M9)
**Goal:** Make the entire pipeline accessible to non-CLI users via a web interface, included with the release and deployable on GitHub Pages
**Date:** 2026-09-28
**Current versions:** Plugin v0.8047, Pipeline v0.5351 (56 CLI parameters across 8 functional groups)

---

## 1. What We're Building And Why

The pipeline today is a 56-flag CLI tool with a scratch-folder validation
procedure. That's excellent for CI and power users, but it walls off the
majority of the Beat Saber PS4 modding audience: people who can jailbreak a
PS4 and copy files but won't live in a terminal. A web app turns the same
pipeline into point-and-click:

- **Pick your game dump** (the `ps4_dump` folder the release insists on —
  the UI can never let the user forget it: no dump, no pack-mode features)
- **Pick your song** — search BeatSaver, browse your local folder, or paste
  a map ID
- **Pick your target slot** — guided: the UI knows every pack and slot from
  `beat_saber_song_ids.json` (the same catalog the CLI uses), shows what's
  currently deployed at each slot (live PS4 state), and warns on
  target-artist / missing-difficulty rule violations BEFORE deploying
- **Configure and deploy** — every pipeline option exposed with safe
  defaults; feature flags as toggle switches; PS4 connection with a
  Test Connection button
- **Validate** — the 35-check release validator surfaced as a UI page with
  live per-check results and a saved report

**Non-negotiable principle: the web app is a THIN LAYER.** It calls the
pipeline — it never re-implements any conversion, deploy, validation, or
state logic. Every button maps to a documented pipeline invocation. This
keeps one source of truth for behavior, and every web-app bug fix lands in
the pipeline (and benefits CLI users) automatically.

---

## 2. The Two Deployment Modes (why both)

| Mode | What it is | What it can do |
|---|---|---|
| **A. Local backend (full)** | A small FastAPI/Flask server the user runs on the same machine as the pipeline (`pip install`-free: ships as `webapp/` in the release zip; `python3 webapp/server.py`) | Everything: folder pickers (native dialog via tkinter/pywebview fallback), BeatSaver download, full deploys over FTP to the PS4, live state reads, the 35-check validator. The browser talks to `localhost:<port>`. |
| **B. GitHub Pages (static)** | The same UI bundle deployed to Pages with the backend disabled | A first-run wizard + **command builder**: users configure everything visually, and the app generates the exact `python3 tools/full_custom_song_pipeline.py ...` command to copy-paste, plus deep links into the docs. BeatSaver search works (public API); no local files, no FTP. This is the marketing/onboarding surface AND the fallback for users who won't run a server. |

The UI detects which mode it's in (backend heartbeat at `/api/ping`) and
hides/enables sections accordingly. One codebase, one build, two deploys.

**Why a local backend is unavoidable for full function:** the pipeline needs
(1) the game dump on local disk, (2) FTP to the PS4, (3) writes to the
release folder's state files. Browser sandboxing forbids all three; GitHub
Pages forbids all three forever. Any "pure Pages" full-function design would
require re-implementing pipeline logic in JS — violating the thin-layer
principle and duplicating ~5,000 lines of hardware-proven Python.

---

## 3. Architecture

```
┌────────────────────────── Browser ──────────────────────────┐
│  UI (single-page app; vanilla JS + small CSS or Preact)    │
│  Pages: Wizard · SongPicker · Deploy · Flags · PS4 ·       │
│         Validate · Logs · Settings                          │
└──────────────┬─────────────────────────────┬───────────────┘
               │ fetch /api/* (JSON)         │ fetch /api/stream (SSE)
┌──────────────▼─────────────────────────────▼───────────────┐
│  webapp/server.py — FastAPI, ~local only (127.0.0.1)        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ adapters/: ONE module per pipeline subsystem         │  │
│  │  config.py   — ps4_config.json read/write + validate │  │
│  │  beatsaver.py— search/get (public API, no key)       │  │
│  │  deploy.py   — the 56-flag CLI surface → typed calls │  │
│  │  ps4.py      — FTP state reads (banner-free transport)│ │
│  │  validate.py — wraps the release validator functions │  │
│  │  flags.py    — features.json get/set (merge rules!) │  │
│  └──────────────────────────────────────────────────────┘
│  ┌──────────────────────────────────────────────────────┐  │
│  │ runner.py — subprocess executor with SSE log stream │  │
│  │  • runs the pipeline as a subprocess (never threads:│  │
│  │    UnityPy/FTP subprocess safety), one job at a time │  │
│  │  • streams stdout/stderr lines to the browser        │  │
│  │  • cancel = terminate process group (deploy safety)  │  │
│  └──────────────────────────────────────────────────────┘
└───────────────────────────┬───────────────────────────────┘
                            │ imports + subprocess
┌───────────────────────────▼───────────────────────────────┐
│  tools/full_custom_song_pipeline.py (UNCHANGED — the      │
│  pipeline is called with the exact same argv the CLI uses) │
│  + development/scripts/ps4_state.py (state reads)         │
│  + .agent/docs/release-validation-test-procedure.sh        │
│    (validator invoked via bash, output parsed)            │
└───────────────────────────────────────────────────────────┘
```

### Key design decisions (each with a hard-won rationale)

1. **Subprocess, not imports, for deploys.** The pipeline is a 5,200-line
   script with `sys.exit()` calls, module-level config loading, and
   long-running FTP transfers. Importing it into a server invites global-state
   corruption between requests. Running it as a subprocess with the same argv
   the CLI uses means: identical behavior, identical logs, and the UI is
   literally a CLI front-end (the thin-layer principle, mechanically enforced).
   Read-only queries (config, features.json, BeatSaver search) MAY import
   helpers directly — they're pure functions.

2. **Single-job executor with a visible queue.** Deploys mutate the PS4's
   redirects/catalog/metadata as a transaction; concurrent deploys would
   race (the Exp 227/232 lesson family: state files are the record of what's
   live). The runner allows ONE pipeline job at a time; the UI shows a job
   badge on every page while one runs.

3. **Banner-free FTP reads everywhere.** Every PS4 read in `ps4.py` uses
   the `get`-to-temp-dir transport (never `lftp cat`), and JSON parsing is
   first-`{`-to-last-`}`. The lftp-ftp-pitfalls KB page is required reading
   for the adapter author; the UI must never re-learn those seven traps.

4. **The config-localization step is UI-mandatory.** Release finding #1
   (devcontainer-absolute default paths) means the web app's setup wizard
   must write the localized `ps4_config.json` itself (the wizard asks for
   the ps4_dump folder; everything else derives from the release folder's
   own location). When the post-merge PROJECT_ROOT-relative-defaults fix
   lands, the wizard simplifies but stays as the dump-picker.

5. **Pages mode shares everything except adapters.** The static build stubs
   the `/api/*` layer and swaps Deploy buttons for "copy generated command".
   BeatSaver search still works client-side (public JSON API, no key,
   CORS-enabled — same one the pipeline hits).

---

## 4. UI Pages (functional spec)

### 4.1 Setup Wizard (first run; local-backend mode)
1. Welcome → what BSD is + the ps4_dump disclaimer (same text as the release notes)
2. **Game dump picker** — native folder dialog (pywebview when available;
   tkinter `filedialog.askdirectory()` fallback; manual path entry as last
   resort). Validates: `ps4_dump/CUSA12878-patch/Media/StreamingAssets/aa/catalog.json`
   exists; shows the found DLC packs from the dump as a confidence list.
3. **PS4 connection** — IP (default 192.168.100.117), port (2121). **Test
   Connection** button → runs the pipeline's own reachability path
   (`--verify-ps4` dry reachability step) and reports files-in-AFR.
4. Writes `ps4_config.json` with ALL paths localized (wizard output = the
   procedure doc's step 1.5, automated).

### 4.2 Song Picker
- **BeatSaver tab**: search box (name/artist/mapper) → results with the map's
  key, name, song author, mapper, BPM, difficulty list + **native
  Easy/Normal/Hard badge** (the song-selection rule — hard-fail with an
  explain-why if missing; Expert/E+ auto-fill note shown as informational).
  Filters: has-native-E/N/H, sort by downloads/rating/date. Click a result →
  detail panel with per-difficulty note-count progressions (the
  download-and-verify step the CLI does; adapter previews the same data).
- **Local folder tab**: pick a song directory; the UI validates Info.dat
  (V2/V3/V4 aware — shows which format it found) and lists difficulties.
- **Map ID tab**: paste an ID/hash; resolves via the BeatSaver API.

### 4.3 Deploy Page
- Target slot picker grouped by pack (from `beat_saber_song_ids.json`),
  each slot showing: stock title/author, **currently-deployed custom (live
  PS4 state)**, and mode-set status. The Exp 227/232 rules live here:
  the UI computes scope and always shows "what else will be preserved".
- Options panel with safe defaults (`--pcm16 --no-pad --convert-to-v3`) and
  an "advanced" disclosure for the rest (mode selection, min-gap,
  rotation-cycle, fallback-mode-map, song-name/artist overrides...).
  Every option carries its doc one-liner (source: `--help` text).
- **Deploy button → live log stream** (SSE) into a scrollable pane, with the
  pipeline's own lines rendered as they arrive; final status banner
  (PASSED/FAILED from the pipeline's exit code).
- Post-deploy: one-click "Verify PS4" and "View deployed state".

### 4.4 Feature Flags Page
- Four toggle switches (kill switch first) over the current PS4 state,
  read live. Writes go through `--features-only --set-feature ...` (the
  merge-with-DEFAULT_FEATURES behavior is the pipeline's job, not the UI's).
- Shows the expected boot toast for the current combination (the README
  table, rendered).

### 4.5 PS4 Page
- Connection info + Test Connection
- Live state dashboard: redirects.json summary (packs/songs/catalog counts),
  song_metadata.json counts, features.json, plugins.ini entry, AFR file
  listing with sizes. All via banner-free reads.
- Slot table: every deployed song, its slot/pack, stock↔custom title,
  modes enabled. `--clear-target-song` per-row with a confirm dialog that
  spells out what gets preserved (the surgical-revert contract).

### 4.6 Validate Page
- Runs the release validator (`release-validation-test-procedure.sh`) as a
  job; the `[PASS]/[FAIL]` table lines stream into a results table; the run's
  log is downloadable. Includes the validator's own state-backup/restore
  guarantee as its safety note.

### 4.7 Logs Page
- Job history (every subprocess invocation with argv, exit code, duration,
  full output) — the transparency users need to self-diagnose or file
  useful issues.

---

## 5. Phased Delivery

### Phase 1 — Skeleton + Setup Wizard + Deploy (the vertical slice)
- FastAPI server, static UI shell, wizard (dump picker + PS4 test), Song
  Picker (BeatSaver search + ID), Deploy page with the safe-default command
  + SSE log streaming, single-job runner.
- **Exit criterion:** a user can go from extracted-release → wizard →
  pick a song → deploy to a slot → see PASSED, without ever opening a shell.
- Regression: the pipeline untouched (diff on tools/ = 0).

### Phase 2 — State + Flags + Validation
- PS4 dashboard page, feature-flag toggles, Validate page (validator
  surfaced), slot table with live state, clear-target-song flow.
- **Exit criterion:** everything on the user's original list except folder
  pickers for local songs works, end-to-end, against a real PS4.

### Phase 3 — Local-folder songs + Pages mode + shipping
- Local song-folder tab, advanced options panel, GitHub Pages build (command
  builder mode), bundle `webapp/` into the release zip (plugin-build.yml),
  README + release-notes sections, `--webapp` convenience launcher.
- **Exit criterion:** release zip contains webapp/; Pages site live; the
  release-day checklist grows a "webapp smoke test" line.

### Phase 4 — Polish (post-first-release-of-webapp)
- Saved presets (favorite slots/options), multi-song queueing (sequential,
  one-job-at-a-time rule), diff previews, telemetry-free error reporting
  (user-copyable diagnostics bundle), i18n groundwork.

---

## 6. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| UI drifts from CLI behavior | Thin-layer rule enforced by architecture: deploys are subprocess argv calls; the CLI is the contract. Every UI feature must name the pipeline flag/function it wraps. |
| Pipeline gets state-mutating regressions exposed to a wider audience | The 35-check validator ships with the app and is one click away; the UI surfaces the post-deploy validation result of EVERY deploy (already exit-code-gated in the pipeline). |
| Users expect Pages to deploy | The Pages mode is explicit about being a command builder; the UI's Deploy button is replaced, never hidden-and-broken. |
| FTP flakiness confuses UI users | All reads use the banner-free transport + retries (lftp-ftp-pitfalls); every failed read says "couldn't read from PS4 — check connection" instead of rendering empty state as truth (the Exp 237/239/240 lesson, made visual). |
| Config-localization forgotten | The wizard is mandatory on first run; the Deploy page re-checks dump presence every session. |
| Scope creep into pipeline rewrites | This plan's pipeline-touching surface is ZERO lines; exceptions require a new plan doc. |

---

## 7. Open Questions (to resolve at Phase 1 kickoff)

1. **Frontend framework choice** — vanilla JS + fetch/SSE keeps the Pages
   build trivial (no build step, no toolchain in the release zip); Preact
   helps the state dashboard. Recommendation: start vanilla; introduce a
   tool only if the Dashboard/Slot-table complexity demands it.
2. **pywebview vs tkinter for the folder dialog** — pywebview gives a real
   native dialog from the server process; tkinter is dependency-free but
   needs a display. Ship both paths, probe at runtime.
3. **Does the server auto-open the browser?** (`webbrowser.open` on start —
   friendlier; recommend yes, with a `--no-browser` flag).
4. **Validator integration depth** — parse the validator's PASS/FAIL table
   (stable format, ours) vs. reimplementing checks in Python. Recommendation:
   parse; the validator is already the maintained artifact.
5. **Multi-PS4 profiles** — out of scope for Phase 1-3; the config file is
   single-PS4 today.

---

## 8. What NOT To Build (explicitly out of scope)

- Any audio/beatmap conversion logic in JS/Python-in-server (the pipeline does it)
- A BeatSaver mirror/proxy (use the public API directly, client-side where possible)
- User accounts, cloud state, or any server beyond localhost
- Modifying the plugin or the PS4-side protocol (the webapp speaks the
  SAME FTP + file conventions that exist today)
- Packaging as an .exe/app (devcontainer/python users are the audience for
  v1; packaging can be a later user request)
