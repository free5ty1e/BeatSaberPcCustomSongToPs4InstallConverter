# Web App Interface for the Song-Conversion Pipeline

**Status:** ACTIVE — M9 implementation phase. The v0.8047/v0.5351 release is MERGED, TAGGED, and
validated 35/35 (Exp 243); this plan is the immediate work item on branch
`feature/web-app-song-conversion-pipeline` (fresh off merged main). Start at Phase 1.
**Goal:** Make the entire pipeline accessible to non-CLI users via a web interface, included with the release and deployable on GitHub Pages
**Date:** 2026-09-28 (last updated 2026-09-28, pre-compaction context audit)
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

### 4.1b Game Dump Guide (wizard step 1's expandable panel + standalone page)

The #1 setup blocker for new users is producing a decrypted dump — the web
app must actively help, not just insist. Two levels:

**Informational (both modes, incl. GitHub Pages):**
- A step-by-step guide rendered in the wizard (and linked from the Pages
  command-builder mode): what a dump is, why the release can't ship one
  (copyright), and the exact recipe:
  1. What you need: jailbroken PS4 with GoldHEN, the game (CUSA12878) with
     **patch 2.04 installed** and the DLC packs you intend to modify
     **installed BEFORE dumping** (pack bundles live in the patch dump)
  2. Copy a `dumper.cfg` with `split=3` to a USB stick root — the web app
     provides a **download link to a ready-made `dumper.cfg`** (ours, the
     exact config this project's own dump used: split=3) plus the config
     explained line-by-line
  3. Run the dumper homebrew (GoldHEN's PS4 Dumper or equivalent); the dump
     lands on the USB stick as `CUSA12878-app/` + `CUSA12878-patch/`
  4. Copy BOTH folders from the USB stick into a `ps4_dump` folder on the
     machine running the web app (or point the web app at wherever you put
     them)
- External links (kept in one `links.json` so they can be corrected without
  a rebuild): the GoldHEN project (homebrew source), the PS4 Dumper tool
  page, and this project's README prerequisites section.
- **Expected pitfalls called out inline**: missing patch 2.04 (wrong
  version), DLC installed after dumping (pack bundles absent — the #1
  support symptom), running the dumper without `split=3` (no
  `-app`/`-patch` split), and dumping to a FAT32 stick with <2x game-size
  free space.

**Functional (local-backend mode):**
- The wizard's dump picker validates the structure live and reports
  precisely what's wrong when it fails: which of
  `CUSA12878-app/` / `CUSA12878-patch/` is missing, whether the patch dump
  contains `eboot.bin` + `Media/StreamingAssets/aa/` (the unpacked-files
  requirement), and which DLC pack bundles it found (a confidence list —
  "your dump contains billieeilish, lizzo, rolling stones...").
- "Import/copy dump here" affordance: if the user's dump is elsewhere (USB
  stick still mounted, another folder), the wizard offers to COPY it into
  `<release>/ps4_dump/` (with a size warning — the dump is several GB) or
  just remember the chosen path (the config-localization step writes it
  into `ps4_config.json` either way).
- Pages mode cannot pick folders — its guide ends with "copy the folders
  manually, then continue in the local web app or the CLI".

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
- **Exit criterion:** a user can go from extracted-release → wizard (incl.
  the Dump Guide with live validation) → pick a song → deploy to a slot →
  see PASSED, without ever opening a shell.
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
| Users stuck before the pipeline even runs (bad/missing dump) | The Dump Guide (4.1b): ready-made dumper.cfg download, step-by-step recipe with pitfalls, live structural validation with per-missing-piece error messages, and DLC-found confidence list. The wizard turns "no dump found" into "here's exactly what to do next". |
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

---

## 9. Implementation Context (read before Phase 1 kickoff)

*This section carries everything the planning session knew that isn't written
elsewhere — so implementation can start from this document alone after a
context compaction. Verify nothing here has drifted since (versions, paths).*

### 9.1 Project operating rules that bind the web-app work

- **CLAUDE.md is authoritative** (mirrored in `.opencode/rules.md`). Non-obvious
  rules that apply directly to web-app development:
  - **Danger Mode guardrails**: git COMMIT/PUSH/branch/tag etc. are FORBIDDEN
    (stage + suggest a commit message; the user commits). `gh` is read-only
    except `gh edit`/PR-description PATCH. `az` read-only. Never delete files
    without asking. Never run system-modifying commands without asking.
  - **Versioning**: any change to the pipeline or plugin bumps versions
    (+0.0001, pipeline in `beat_saber_deluxe/VERSION`, plugin in
    `src/main.cpp` PLUGIN_VERSION) with changelog entries. **The web app
    itself needs a version scheme** — recommend `webapp/VERSION` starting at
    `0.1.0`, separate from the pipeline/plugin (it's a new component), with
    its own `CHANGELOG-WEBAPP.md`; when the release zip bundles it, the
    release notes mention the webapp version. Decide at kickoff.
  - **Testing**: full suite green before presenting
    (`cd beat_saber_deluxe && python3 -m pytest tests/ -q` — 649 tests,
    ~2-4 min). New web-app code needs its own tests (adapter unit tests with
    a mocked PS4/FTP; server endpoint tests with FastAPI's TestClient; NO
    tests may touch the real PS4 — the hardware gates pattern,
    `tests/test_pack_mode_pipeline.py` HAS_DUMP/HAS_BUILT_ALL, is the model).
  - **Docs per cycle**: experiment log (`.ai_memory/beat-saber-ps4-custom-songs/
    experiment_log.md`, next number 244+), project_summary, context.yml,
    roadmap, AND **a session transcript** (`.agent/transcripts/`,
    CLAUDE.md §0.5 — the web-app feature's transcript is
    `2026-09-28_web-app-interface-m9.md`; append every cycle before responding).
  - **PS4 log workflow**: any on-hardware test's `bs_log.txt` downloads to
    `.ai_memory/experiment_logs/` with a version-specific name and gets
    cleared on the PS4 after.
  - **Experiment numbers are globally sequential** (currently at 243).

### 9.2 The environment the web app runs in (facts, not assumptions)

- **The PS4**: GoldHEN 2.3/2.4b, Beat Saber CUSA12878 v2.04, FTP on port 2121,
  anonymous login (`lftp -u anonymous:anonymous`, NOT bare `anonymous` — see
  pitfall 6). Default IP in this workspace: 192.168.100.117 (the wizard's
  default, overridable).
- **The pipeline is invoked as `python3 tools/full_custom_song_pipeline.py
  <flags>` with CWD = the release/checkout root** (PROJECT_ROOT derives from
  `__file__` — the webapp server must spawn it with cwd set to the release
  root, NOT the webapp/ dir).
- **ps4_config.json schema** (exact, dev-repo values shown; the wizard writes
  this with all paths localized — release finding #1: the pipeline's built-in
  DEFAULTS are devcontainer-absolute and MUST be overridden):
  ```json
  {
   "ps4": {"ip": "192.168.100.117", "ftp_port": 2121,
           "ftp_user": "anonymous", "ftp_password": ""},
   "title": {"id": "CUSA12878", "name": "Beat Saber"},
   "paths": {
    "afr_base": "/data/GoldHEN/AFR",
    "afr_target_suffix": "_v3.bundle",
    "game_dump_dir": "<release>/ps4_dump/CUSA12878-patch",
    "template_dir": "Media/StreamingAssets/BeatmapLevelsData",
    "output_dir": "<release>/custom_songs"},
   "pack_modes": {"packs": [], "build_dir": "<release>/pack_modes_bundles",
    "song_ids_path": "<release>/beat_saber_song_ids.json",
    "dump_dir": "<release>/ps4_dump/CUSA12878-patch",
    "catalog_key": "aa/catalog.json",
    "patched_catalog": "catalog_pack_modes.json",
    "patched_catalog_local": "<release>/catalog_pack_modes.json"},
   "mass_deploy": {"bundle_dir": "<release>/mass_bundles", "slots": []}
  }
  ```
- **The three PS4 state files** (all in `/data/GoldHEN/AFR/CUSA12878/`):
  `redirects.json` (deployment record: `BeatmapLevelsData/<slot>` → `<slot>_v3.bundle`
  song entries, `<pack>_pack_assets_all_<hash>.bundle` → patched bundle pack
  entries, and `aa/catalog.json` → `catalog_pack_modes.json`),
  `song_metadata.json` (`song_names`: stock-title → "Custom / Artist";
  `song_artists`: pack-artist → " " blanking), and `features.json` (4 flags,
  `enable_plugin` defaults TRUE when absent — the only one that does).
  **Never push a local state file over the PS4's without pulling first**
  (Exp 237: local-missing → empty default → wipes live state).
- **The 35-check validator**: `.agent/docs/release-validation-test-procedure.sh`
  — invokes with `bash <script> --log <file> [TAG]`; parse-able output lines:
  `   [PASS] <label>` / `   [FAIL] <label>` (indented, from the `mark()`
  helper), plus a final `PASS: N   FAIL: N` and exit 0/1. The Validate page
  parses `[PASS]/[FAIL]` lines — stable format, ours. Its defaults assume the
  maintainer's workspace paths — the web-app Validate page must pass an
  explicit TAG and (Phase 2+) may need the script's `PS4_IP` env override.
  NOTE: the validator is written for the maintainer's layout; the web-app
  should invoke it with the release folder as CWD (it self-locates the
  extraction into /workspace/temp/release-validation — for non-/workspace
  layouts, adapt `TEMP`/`VAL` or call the underlying pipeline checks directly
  via `verify_ps4_deployment(config)`).
- **BeatSaver API** (public, no key; client-side calls work from Pages —
  CORS-enabled): search `GET https://api.beatsaver.com/search/text/<page>?q=<query>&per_page=N>`
  → `{docs: [{id, name, metadata: {songAuthorName, levelAuthorName, bpm,
  duration}, versions: [{downloadURL, diffs: [...]}], stats: {downloads}}]}`;
  map-by-id `GET /maps/id/<key>`. **Gotchas learned in-session**: votes/score
  fields return 0/None (unreliable — do not sort on them; prefer recency +
  the song-selection rules), maps get DELETED (a picked map can 404 at deploy
  time — handle gracefully with a re-check), use `versions[0].downloadURL`
  (the legacy `/maps/id/<id>/download` endpoint is dead), and per-difficulty
  note-count progressions are the real quality check (the pipeline does
  this; the UI's badge can use `diffs` characteristic/difficulty lists).
- **The song-selection rules** (user's, enforced by the picker's badges):
  custom maps must ship **native Easy/Normal/Hard** (Expert/E+ auto-filled
  from lower difficulties by the pipeline); no target-artist songs in that
  artist's pack; the user's taste: electronic/rave/80s-2000s preferred,
  avoid country/pre-1980.

### 9.3 Where everything lives (reference map)

| Artifact | Path |
|---|---|
| The pipeline (the thing the web app drives) | `beat_saber_deluxe/tools/full_custom_song_pipeline.py` (CLI surface: `--help`; deploy orchestration: `--deploy-full`; read-only: `--verify-ps4`) |
| Slot/pack catalog (drives the target picker) | `beat_saber_deluxe/beat_saber_song_ids.json` — albums[].{pack, packBundle, songs[].{songID, songName, songAuthorName, characteristicModes, difficulties}} |
| PS4 state reader (existing, reusable) | `beat_saber_deluxe/development/scripts/ps4_state.py` (reads live PS4: redirects, features, AFR listing) |
| The 35-check validator | `.agent/docs/release-validation-test-procedure.sh` + `.md` (manual procedure) |
| lftp pitfall reference (REQUIRED reading for adapter authors) | `.agent/llm-wiki-knowledge-base/lftp-ftp-pitfalls.md` |
| Safe-default deploy flags | `--download-beat-saver-song <ID> --target <SLOT> --pcm16 --no-pad --convert-to-v3 --deploy-full` (options panel's defaults; `--skip-plugin-deployment` when pinning a plugin) |
| Feature-flag toggles | `--features-only --set-feature <name>=<true|false>` (repeatable) |
| Surgical revert | `--clear-target-song <SLOT>` |
| Metadata-only | `--metadata-only --target <SLOT> --song-name "X" --artist "Y" --deploy` |
| Example pack scripts (69, with `--no-prompt`) | `.agent/docs/example_*` (shipped in release `docs/example-scripts/`) |
| Release validation history | `.ai_memory/experiment_logs/release-validation-*.log` (the format the Validate page replicates) |
| Prior transcript (release-validation saga, Exps 234-242) | `.agent/transcripts/2026-09-27_release-validation-hardening.md` |
| This feature's transcript (append per cycle) | `.agent/transcripts/2026-09-28_web-app-interface-m9.md` |
| Roadmap M9 entry | `.agent/roadmap.md` (## M9 section) |

### 9.4 Hard-won invariants the adapters must not violate

1. **Thin layer**: deploys = subprocess argv. The web app never re-implements
   conversion/deploy/validation logic. Read-only helpers may be imported
   (`_load_local_redirects`, `_load_local_song_metadata`,
   `verify_ps4_deployment`, `resolve_audio_codec`-style pure functions) —
   but anything with `sys.exit`, FTP writes, or long runs = subprocess.
2. **One deploy at a time** (single-job runner). The PS4's state files are a
   transaction record; concurrent writers corrupt them (Exp 227/232/237 all
   trace to this class).
3. **Banner-free FTP reads only** (KB: lftp-ftp-pitfalls). `get`-to-temp-dir
   + first-`{`-to-last-`}` JSON extraction + retries; READ-FAILED is an
   "unknown/couldn't read" state, NEVER rendered as zero/empty-truth.
4. **Pull-before-push for any state file** (redirects/song_metadata/features):
   read the live PS4 copy, mutate, push. Never push a possibly-absent local
   file (Exp 237).
5. **`enable_plugin` defaults TRUE when absent** (the only flag that does) —
   the flags page must render unknown/absent as ON for that key, and any
   flags.json write goes through the merge-with-DEFAULT_FEATURES path
   (`_deploy_features_to_ps4` behavior) via `--features-only`/`--deploy-full`.
6. **The user's PS4 is production**: the web app's default posture is
   read-only; every state-mutating action shows exactly what will change and
   what will be preserved (the surgical-revert contract: clear one song →
   its pack's other songs and every other pack untouched) and requires an
   explicit confirm. Auto-restore/backup semantics like the validator's.
7. **The wizard's dump validation checks** (exact paths):
   `<dump>/CUSA12878-patch/Media/StreamingAssets/aa/catalog.json` (origin
   catalog), `.../aa/PS4/<pack>_pack_assets_all_<hash>.bundle` per DLC pack
   (the confidence list), and `CUSA12878-app/` presence (base dump). The
   `dumper.cfg` we ship for download: `split=3` (ours:
   `/workspace/ps4_dump/dumper.cfg` — the live reference file).
8. **Git**: stage only; commit messages suggested, never committed (Danger
   Mode). The web-app branch is `feature/web-app-song-conversion-pipeline`.

### 9.5 Definition of done for this milestone

- Phases 1-3 per §5 exit criteria; final: the release zip contains `webapp/`,
  the Pages site builds from the same UI bundle, the README carries a web-app
  section, and the release-day checklist (bottom of the validation procedure
  doc) includes a webapp smoke test. The web app has its own tests, version,
  and changelog. The 35-check release validator runs green from a web-app-
  driven fresh extraction on real hardware.
