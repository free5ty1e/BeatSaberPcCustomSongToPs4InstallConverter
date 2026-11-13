# Session — 2026-11-07: container-rebuild recovery + Pi session persistence + webapp checkout deps

Branch: `feature/lower-difficulty-generation-engine`. New session after the user's devcontainer
rebuild wiped home-dir state (Pi sessions lost). Continuation of M15 (plan:
`.agent/plans/lower_difficulty_generation_engine.md`; transcript of the M15 feature work:
`.agent/transcripts/2026-10-24_m15-lower-difficulty-engine.md` — Cycle 8 / Exp 293b there was
staged but never committed or summarized).

## User's asks (this session)
1. Get up to speed from: uncommitted changes + last commits + the M15 plan + KB index +
   AGENTS.md + introduction.md; figure out where the previous agent left off (staged changes
   present, but no summary / commit message survived).
2. Build `pi_persist_devcontainer.sh`: auto-detect Pi's state in the user folder, migrate it
   into the workspace (`.pi_persist`), and symlink home → workspace so `pi` launches normally.
3. (mid-session) Web app fails to start after rebuild: `ModuleNotFoundError: No module named
   'fastapi'` — requirements unclear for a repo checkout; README only covers the release
   artifact — fix + document.

## Where the previous agent left off (reconstructed)
- Last commit `e36791e` = Exp 293 (the evaluation pack; the lizzo A/B suite). Its quoted user
  response contained the Dragon report: "chaotic on Hard… notes a bit off the beat… faster
  notes close together can result in the wrong note being chosen", plus: validate the user's
  5-pack mass re-deploy, then spread the test songs over the BTS pack.
- The STAGED (uncommitted) changes = Exp 293b (Cycle 8), fully documented by that agent in
  experiment_log / transcript / KB / changelog before staging: the grid-native selection v3
  (`tools/difficulty_engine.py`, pipeline 0.5369 — quantize-first, the phase search tried and
  rejected), `deploy_bts_spread.py` (6 BTS deploys, the wait_job poll-race fix), the
  .gitignore for deploy-state artifacts, docs. The Dragons [Descent v2] re-deployed to Good As
  Hell (validation PASSED); BTS spread deployed (all PASSED); mass re-deploy validated
  (47 songs/5 packs). The user's RE-JUDGMENT is still pending → then the M15 release.
- Gaps the previous agent left: `project_summary.md` Status line stale (still M13-era),
  `context.yml` top version fields stale (plugin 0.8054 / pipeline 0.5364 vs actual
  v0.8055 / 0.5369), a ruff F841 dead store (`span_q`) in the staged engine code, and no
  commit message handed over.

## This session's work

### 1. Orientation
- Read the plan, staged diff, last commit bodies, transcript, KB index, HANDOFF.md (stale —
  2026-08-25 Exp-197-era, not current), project_summary, context.yml.

### 2. Webapp deps (the user's error)
- Root cause: the container rebuild wiped pip installs; the webapp runtime deps (fastapi,
  uvicorn, python-multipart) exist only inside `beat_saber_deluxe/requirements-test.txt`
  (the release zip ships that file AS its requirements.txt — CI line 252), and README §3.1b
  showed no install step for repo checkouts.
- Also found `/home/vscode/.local` root-owned (rebuild artifact) — chowned back to vscode
  (the container's own setup_devcontainer.sh does exactly this at creation), then:
  `pip3 install --break-system-packages -r requirements.txt -r beat_saber_deluxe/requirements-test.txt`
  → all imports OK, `from server import app` OK.
- NEW `beat_saber_deluxe/webapp/requirements.txt` (runtime-only: fastapi/uvicorn/
  python-multipart, header pointing at requirements-test.txt for dev).
- README §3.1b: added the "From a full repo checkout" install block (webapp-only and
  everything variants).
- BOTH devcontainer postCreateCommands (`.devcontainer/standard|openorbis/devcontainer.json`)
  now install the project requirements on rebuild (persisted toolset per the rules).

### 3. Pi persistence (`.devcontainer/pi_persist_devcontainer.sh`)
- Design: migrate ALL of `$HOME/.pi` (166MB: agent/{sessions,auth.json,settings.json,
  models-store.json,bin,install}) into `<ws>/.pi_persist`, then `ln -s` home → workspace so
  `pi` works with no special params/env changes (PI_MANAGED_INSTALL_ROOT etc. resolve through
  the link).
- Modes: already-persisted (idempotent exit; folds newer session files from any
  `.pi.pre-persist-*` backups — a running pi keeps its fd on the OLD session file after the
  swap) / restore-after-rebuild (symlink only) / migrate (copy → backup-rename → symlink) /
  merge (rsync home over target: fresh install wins conflicts, old sessions preserved) / seed.
- Nothing deleted: original renamed to `~/.pi.pre-persist-<ts>`; undo line printed.
- Auto-adds `.pi_persist/` to the workspace .gitignore (auth.json = credentials — never commit).
- Wired into BOTH postCreateCommands (after the pip installs) so rebuilds restore the link
  automatically; header says: RUN ONCE MORE BEFORE REBUILDING (the backup lives in $HOME,
  which the rebuild wipes).
- RAN it live: migrated 166MB / 1 session; verified the live session file readable+growing
  through the symlink; `.gitignore` got the `.pi_persist/` line.

### 4. Docs currency + lint gate
- `context.yml`: plugin_version 0.8054→0.8055, pipeline_version 0.5364→0.5369 (short
  0.5369/0.5368/0.5367 notes prepended, history kept).
- `project_summary.md`: Status line refreshed to M15-current (Exp 293b state, re-judgment
  pending, the Cycle-8 checklist note, this session's env items).
- ruff F841 in staged `tools/difficulty_engine.py` (dead `span_q`) REMOVED; re-ran
  tests/test_difficulty_engine.py: 17 passed.
- FULL SUITE: 1076 passed, 3 skipped (10m07s) — larger than the historical 948+87 because the
  webapp tests now RUN with fastapi installed. ruff tools/+tests/ clean.

## Key findings (durable)
- A devcontainer rebuild loses: pip packages AND `$HOME` (Pi sessions/auth). The webapp
  runtime deps must be installed from requirements files, now wired into postCreateCommand.
- Release-zip requirements.txt = requirements-test.txt (CI copies it); repo checkouts now
  have webapp/requirements.txt (runtime) + root requirements.txt (pipeline).
- Pi keeps an open fd on the live session file → after the persist swap, the session tail
  keeps writing into the backup dir; the script's Case-1 fold + "run before rebuild" note
  handle it.

## Files changed (this session)
- NEW: `.devcontainer/pi_persist_devcontainer.sh`, `beat_saber_deluxe/webapp/requirements.txt`
- MODIFIED: `README.md` (§3.1b checkout setup), `.devcontainer/{standard,openorbis}/devcontainer.json`
  (postCreate: requirements + pi persist), `.agent/context.yml` (versions), `.agent/project_summary.md`
  (status), `.gitignore` (`.pi_persist/` via script), `beat_saber_deluxe/tools/difficulty_engine.py`
  (ruff F841 dead store out)
- STAGED-BY-PREVIOUS-AGENT (Exp 293b, left intact): context.yml milestone, KB
  beatmapping-guidelines, M15 transcript, experiment_log, .gitignore M15 entries,
  CHANGELOG-PIPELINE (v0.5369), VERSION, deploy_bts_spread.py, difficulty_engine.py (now also
  carries the F841 fix).

## Next steps
1. User: commit (two suggested commits: Exp 293b feature work — already in the index, plus
   this session's env-recovery work) + re-judge the PS4 A/B: Good As Hell [Descent v2] vs
   Tempo [Beat Sage] + the BTS 6-song spread.
2. Then: the M15 release (tag + validation per the release procedure).
3. Optional cleanup: stale untracked HANDOFF.md (Exp-197-era) can be deleted.

## Cycle 2 — the user's verdict + the M15 release validation (Exp 294)

- **User: "Just tested, they played great. I think this is good enough for release, please
  validate the new tag / release I just created — watch github for the build completion and
  then download and thoroughly validate the release, the tag is
  `v0.8055-pipeline-0.5369-webapp-0.6.22-alpha01`."** → M15 ENGINE VERDICT: PASS.
- Commit mishap found: the user's commit 5a86d21 carried the WHOLE agent response as the
  message (both suggested messages + next steps + the user's reply). Content is right;
  message is garbled — flagged to the user (amend + re-tag is their call; I cannot run git
  writes). Commit 2 (env-recovery files) is still uncommitted: README, project_summary,
  devcontainer ×2, pi_persist script, webapp/requirements.txt, this transcript.
- Tag IS on GitHub (pushed via the user's VS Code flow — this container's CLI git can't SSH:
  openssh-client was a rebuild casualty; now installed + persisted). gh was missing too —
  installed + persisted; gh 2.45 demands auth even for public release downloads → the
  validator script gained an anonymous curl fallback (bash -n OK).
- Build status via the public API: tag run 42754489773 completed SUCCESS (+ branch CI success).
- Zip downloaded (1,211,517 B — exact API size match) → extracted → STATIC AUDIT ALL GREEN
  (VERSION 0.5369 / webapp 0.6.22 / 69 examples / FSELF pair / v0.8055 binary / no-prompt /
  bundled-plugin fallback / Unicode fix / M15 + validation docs shipped).
- Webapp smoke from the zip ALL GREEN (ping versions, Get Started ×4, 34 packs / 47 songs).
- **Live-PS4 validation BLOCKED: PS4 off ("No route to host").** Asked the user to power it
  on; the full automated run (`release-validation-test-procedure.sh --log <TAG>`) fires the
  moment it's up. Exp 294 logged; project_summary refreshed.

## Cycle 3 — THE M15 RELEASE VALIDATION (Exp 295): 45/45 PASS

- User powered the PS4 on → full automated run #1: **44 PASS / 1 FAIL** — the single FAIL was
  "loadout vs live truth: SERVED 53 != live 0". Root-caused to a VALIDATOR ordering bug: the
  step-4 check compared SERVED against the extraction's local redirects.json, but the zip
  ships an EMPTY placeholder (CI_RELEASE.md documents it) and the real pull happens at step 5.
  The release was never at fault — SERVED 53 matched the true live count (53 songs / 6 packs,
  confirmed by step 5 minutes later).
- Fix #1: the check now pulls redirects.json fresh from the PS4 (self-contained, banner-immune
  parse, soft-skip when unreachable). Run #2: 44 PASS / 0 FAIL — but the loadout row
  soft-skipped: my pull used `mktemp` (CREATES the file) and lftp `get -o` refuses clobber
  (the KB's lftp-ftp-pitfalls lesson, re-learned). Fix #2: `mktemp -u` + standalone proof
  (SERVED 53 == live 53 PASS).
- Run #3 (definitive): **45 PASS / 0 FAIL, exit 0 — "RELEASE VALIDATED — live state
  unchanged."** All static/webapp/deploy/flag/kill-switch/surgical/integrity checks green;
  final state 6 packs / 53 songs / 53 names identical to pre-validation.
- Pages workflow runs on main pushes (post-merge). CI green for the tag + branch. gh/ssh
  persisted; validator curl-fallback shipped. Docs: Exp 294 + 295 logged, summary → VALIDATED.
- Staged for the next commit: validator fixes, Exp 294/295 log entries, transcript, summary.

## Cycle 4 — the final tag is missing; the M14 plan written

- The user merged to main and believed they kicked off tagged CI for
  `v0.8055-pipeline-0.5369-webapp-0.6.22` — but the tag exists NOWHERE (404 on the tag ref,
  no release, no tag-triggered run; not even locally in this container). The main-branch
  builds that ran were the merge push (Build/CI/Pages all green on main — the merge landed
  and the Pages deploy ran). Told the user: create + push the tag (git writes are
  agent-blocked); CI + the release build fire automatically when it lands.
- Local repo still on `feature/lower-difficulty-generation-engine` (in sync with origin —
  e9483cb + 08565c4 pushed and merged). The new feature branch is the user's to cut.
- M14 PREP: audited .agent/plans — NO environment-control plan existed → wrote
  `.agent/plans/custom-song-environment-control.md` (research-first: R1 = the roadmap's
  E1–E4 + the env-idx mapping; R2 = the injection mechanism — the Exp-129 raw-CAB patch vs
  the UnityPy blocker Options A/B/C, the layer decision; R3 = the four modes defined by
  evidence; phases M14.1–M14.5; feature-flag enable_environment_control). Key dump finding
  folded into the plan: TWO env layers — BeatmapLevelSO._environmentName (string, 0x18) AND
  a pack-side record's _environmentNameIdx (int, 0x14) — the pack/Addressables layer binds
  envs by INDEX, prime suspect for the blank-vs-working split (roadmap hypothesis b).
