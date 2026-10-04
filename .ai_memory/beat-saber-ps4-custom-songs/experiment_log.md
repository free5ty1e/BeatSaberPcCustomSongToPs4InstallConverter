---
name: experiment-log
description: "Active experiment log for the CURRENT feature only (M9: Web App Interface for the Song-Conversion Pipeline). Per-feature rotation: when a feature concludes, archive this file into experiment_log_archive/ and open a fresh log. Experiment numbers are globally sequential across the whole project."
metadata:
  node_type: memory
  type: reference
---

# Experiment Log: Beat Saber PS4 Custom Song Support — M9 Web App Interface

**Feature:** Build a web app interface for the song-conversion pipeline (plan:
`.agent/plans/web-app-song-conversion-pipeline-interface.md`): a thin-layer UI over
the existing CLI — local FastAPI backend (full function) + GitHub Pages static build
(command builder). Setup wizard with game-dump guide + live validation, BeatSaver song
picker, guided deploys with live log streaming, feature flags, PS4 dashboard,
35-check validator surfaced as a page. **Thin-layer principle: the web app NEVER
re-implements conversion/deploy/validation logic — every deploy is a subprocess argv
call to `tools/full_custom_song_pipeline.py`.**
**Started:** 2026-09-29 (Exp 244)
**System:** PS4 FW 9.00, GoldHEN 2.3 / 2.4b16.2
**Toolchain:** Python 3.12, FastAPI + uvicorn (already in devcontainer), vanilla JS UI
**Current versions:** Plugin v0.8047, Pipeline v0.5351 (unchanged — webapp has its own
version scheme, `webapp/VERSION` starting at 0.1.0, per plan §9.1)
**Prior experiments (Exp 1-159, archived):** `experiment_log_archive/experiment_log_exp001-159_prior-features_2026-06-08_to_2026-07-31.md`
**Prior experiments (Exp 160-183, archived):** `experiment_log_archive/experiment_log_beatmap-mode-mapping_exp160-183_2026-07-28_to_2026-08-11.md`
**Prior experiments (Exp 184-187, archived):** `experiment_log_archive/experiment_log_chromeo-source-recovery-mass-redeploy_exp184-187_2026-08-12_to_2026-08-13.md`
**Prior experiments (Exp 188-243, archived):** `experiment_log_archive/experiment_log_generalized-pack-patch_exp188-243_2026-08-14_to_2026-09-28.md`

**How to append:** Add the next `### Experiment <N+1>:` entry at the end of THIS file
(only current-feature experiments). When this feature concludes, move the whole file
into `experiment_log_archive/` with a feature+date name and open a fresh
`experiment_log.md`.

---

### Experiment 244: M9 Phase 1 — Web App Skeleton (vertical slice) (2026-09-29)
- **Date:** 2026-09-29
- **What was attempted:** Phase 1 of the web-app plan (`.agent/plans/web-app-song-conversion-pipeline-interface.md` §5): FastAPI server + adapter layer + single-job runner + static UI shell (Setup Wizard, Song Picker, Deploy, PS4 state, Dump Guide). Component version webapp 0.1.0 (own `webapp/VERSION` + `CHANGELOG-WEBAPP.md` per plan §9.1).
- **Ground-truth verification first** (plan §9 discipline): all 56 pipeline flags confirmed via `--help`; catalog schema (36 packs, songID = `--target` slot); dump structure (invariant §9.4.7 paths verified against /workspace/ps4_dump incl. dumper.cfg split=3 — shipped into webapp/static/); BeatSaver API shape + CORS probed live (200 with a github.io Origin → Pages-mode client-side search viable); pipeline does `logging.basicConfig()` at import + `sys.exit()` → subprocess design mechanically confirmed; tkinter absent in devcontainer → wizard ships manual-path entry as the guaranteed fallback (pywebview/tkinter dialog probes arrive Phase 3).
- **Built:** `beat_saber_deluxe/webapp/` — `server.py` (FastAPI, binds 127.0.0.1 by default; 20 routes; `--no-browser` flag) + `adapters/` (paths, config + DumpValidation with per-missing-piece errors + DLC confidence list, beatsaver with native-E/N/H badges, deploy argv builder, ps4 banner-free reads, runner single-job subprocess executor) + `static/` (index.html, app.js with /api/ping mode detection, style.css, dumper.cfg download). Deploy button argv = the example scripts' safe-default command byte-for-byte.
- **Tests (65 new, all mocked — NO PS4 contact per the hardware-gate pattern):** config adapter (13), deploy argv contract incl. "every flag exists in pipeline --help" (18), server endpoints (18), ps4 transport (16).
- **Key finding — the banner tests caught a REAL Exp-240-class bug pre-field:** first-`{`-to-LAST-`}` extraction BREAKS when a trailing banner itself starts with `}` (real lftp banners do: `}156 bytes transferred`) — `rfind('}')` grabs the banner's brace → invalid JSON slice → every read fails on slow links while passing on fast dev rigs. Fixed in `ps4.py` with the KB's proven pattern (Exp 221, ps4_state.py's): `JSONDecoder().raw_decode()` scanning from each `{` position. Regression tests cover clean/trailing/leading/both-side banners + 0-byte files + retry counts + mktemp -d transport shape.
- **Smoke test (live server):** ping/dump-validate (real dump: ok, 30 DLC packs)/command-preview (byte-exact)/BeatSaver search all pass. PS4 test-connection correctly reported explicit unreachable+error (PS4 in rest mode — container on Docker bridge, `No route to host`); the failure path IS the designed behavior (never empty-truth).
- **Regression gate:** `git diff HEAD -- beat_saber_deluxe/tools/` EMPTY — pipeline untouched. Full suite: **714/714 pass** (649 existing + 65 new) in 2:30. Lint: tools/ clean, webapp/ clean, tests clean.
- **Version bumps:** NONE for pipeline/plugin (untouched). Webapp 0.1.0 (new component, own scheme).
- **Next steps:** Phase 1 hardware validation with the user (PS4 awake: wizard → test connection → pick song → deploy → PASSED), then Phase 2 (PS4 dashboard + flags + Validate page).
- **Status:** ✅ Phase 1 skeleton complete; awaiting user hardware run.

### Experiment 245: M9 — Manage Songs + Full Loadout tabs, deployed-truth model, Pages + CI/release coverage (2026-09-29)
- **Date:** 2026-09-29
- **What was attempted (user request):** (1) a Manage Custom Songs tab: pack dropdown → table of every stock song + custom status (artist/name both sides) + per-row surgical Clear; (2) a Full Loadout tab: every pack/song in the game + customs, printable/saveable as an HTML/PDF reference, with Clear per row; (3) full CI/release audit: test coverage, release-zip inclusion, docs; (4) GitHub Pages deployment of the web UI.
- **Built (webapp 0.2.0):**
  - `adapters/loadout.py` — the pure merge: catalog (songID join) × redirects (`BeatmapLevelsData/<slot>`) × song_metadata (songName join, **case/space-normalized** — real data: catalog `'You Should See Me In A Crown '` trailing space vs song_metadata without) + AFR `<slot>_v3.bundle` listing. `ps4.read_deployment_state()` = one banner-free read of ALL THREE sources with explicit per-source errors.
  - **Deployed-truth model (key finding, verified against live PS4 + plugin source + bs_log.txt):** the game serves a custom ONLY via its redirects entry (open_hook matches the table with strstr). A `<slot>_v3.bundle` in AFR without a redirect = STALE payload (uploaded, not served). song_metadata alone = LABEL ONLY. The loadout renders all three distinctly: `customDeployed` (served) / `staleBundle` / `customName` (label).
  - UI: Manage Songs tab (dropdown → served/labeled/stale/stock badges, per-row Clear via `--clear-target-song` subprocess, surgical-revert confirm) + Full Loadout tab (all 36 packs, print stylesheet flips to clean light/PDF layout, filter only-packs-with-customs, per-row Clear, generated-date footer). `/api/loadout` + `/api/loadout/packs`.
  - **GitHub Pages:** `webapp/build_pages.py` (stamps `data-mode="pages"` + command-builder banner on the same UI bundle) + `.github/workflows/pages.yml` (build → smoke-test → deploy to Pages on push to main; concurrency-guarded, OIDC).
- **CI/release audit findings (all fixed):**
  1. **webapp tests would have broken CI** — test jobs install `requirements-test.txt` only; the webapp tests import fastapi/httpx. Added fastapi+uvicorn+httpx to requirements-test.txt (and thus to the release zip's requirements.txt).
  2. **lint blind spot** — ci.yml linted `tools/` only. Now `tools/ webapp/ tests/` in both ci.yml and the release workflow (which also gained a ruff step).
  3. **release workflow never exercised the webapp** — added a smoke-test step (imports server, asserts the 20 routes + static files present) and bundled `webapp/` into the release zip (with VERSION + CHANGELOG-WEBAPP.md).
  4. CI_RELEASE.md grew the webapp artifact table (server, adapters, static incl. Manage/Loadout/Dump Guide, own version scheme) + a "no terminal? start the web app" quick-start + Pages-mode note. README §3.1b updated for the two new tabs + Pages.
- **Live validation (PS4 awake):** `/api/loadout` three-signal merge correct on real state: **1 served (MessItUp) / 46 stale / 47 labeled / 0 unmatched** — and the trailing-space crown song joined (the normalization fix proven on live data).
- **⚠️ REAL PS4-STATE FINDING (surfaced to the user, not a webapp bug):** the live redirects.json holds ONE song redirect — the current boot serves only MessItUp as a custom song. bs_log.txt proves it across boots: earlier boots loaded 47 song redirects (the full loadout worked); the LATEST boot loads 7 (1 song + 5 packs + catalog) — a leftover from the release-validation `--clear-target-song` round-trip (restore rebuilt metadata but never re-added the 46 song redirects). The user's known-good loadout needs a redeploy (the chained example scripts restore it); the Loadout tab now displays exactly this state.
- **Tests:** 16 new (loadout merge 11 + live-truth-model pins + endpoint readStatus 3 + bundles-adapter cases) — total suite **730/730**. Lint clean. app.js parses; pages bundle builds + parses.
- **Version bumps:** webapp 0.1.0 → **0.2.0** (CHANGELOG-WEBAPP.md). Pipeline/plugin untouched (diff tools/ = 0).
- **Next steps:** user runs the two tabs live (after optionally redeploying the loadout); GitHub Pages enabled by user in repo settings (workflow is ready — Pages → GitHub Actions source); Phase 2 remainder (flag toggles page, Validate page).
- **Status:** ✅ tabs built + validated; CI/release gaps closed; Pages workflow ready.

### Experiment 247: M9 — Feature Flags + Backup/Restore + Feature Request tabs; Exp 246 flag-key fix; live PS4 re-enable (2026-10-02)
- **Date:** 2026-10-02
- **What was attempted (user request):** web app as the one-stop shop: a Feature Flags page (per-flag toggles + descriptions + Apply), a Backup/Restore page wrapping backup-beat-saber-deluxe-files.py (incl. the clean-PS4 flag), and a Feature Request tab that composes a GitHub issue URL. User also enabled GitHub Pages and opened the draft PR.
- **Built (webapp 0.3.0):**
  - **Feature Flags tab**: live read via the banner-free adapter (kill switch first, pending badges, per-flag descriptions incl. the plural `enable_custom_song_replacements` + enable_plugin-defaults-TRUE rule); Apply → one `--features-only` call with a `--set-feature` per CHANGED flag (diffed against the live read — never re-pushes unchanged flags; refuses to apply blind when the PS4 read fails; unknown flags rejected).
  - **Backup/Restore tab**: lists ps4_backups/*.zip (name/size/date); backup job (+ optional --clean-ps4 with a hard confirm spelling out the fresh-slate posture); restore per-row (backup-name sanitized — no paths/traversal; 404 on unknown); cancel button; shared job poller. Thin layer: the runner's new `start_script()` runs the SAME script the CLI uses — the webapp adds zero backup logic.
  - **Feature Request tab**: title + details + optional app-state footer (mode + deployed packs — no IPs/paths) → preview → opens github.com/<repo>/issues/new prefilled (client-side; works in Pages mode too).
  - Runner: `start_script()` (unified `_spawn` for pipeline + helper scripts, same single-job/streaming/cancel guarantees); `pending_flags` hint cleared on job completion.
- **BUG FOUND + FIXED during live smoke — flag-key mismatch:** the adapter's KNOWN_FLAGS used the SINGULAR `enable_custom_song_replacement` but the pipeline's canonical key (DEFAULT_FEATURES) + PS4 wire format is the PLURAL `enable_custom_song_replacements` → the Flags page displayed the flag as default-OFF when the PS4 had it ON (and my Apply would have written the wrong key). Fixed in adapters/ps4.py + server FLAG_DESCRIPTIONS + test fixtures. ALSO: the first attempt at the key rename in server.py popped an already-renamed key → boot-time KeyError — caught by the smoke boot before any user could hit it. Lesson repeated: boot the artifact before handing it off.
- **Live PS4 state finding + fix:** the flags read showed `enable_custom_song_replacements` AND `enable_song_metadata_modification` OFF on the console (left from the release-validation flag round-trip testing). Re-enabled both via the pipeline (`--features-only --set-feature ...×2`), verified via the webapp read: ALL FOUR FLAGS ON. The user's PS4 is fully restored (Exp 246) AND fully enabled.
- **Tests:** 16 new (flags read/descriptions/read-failure-explicit/apply-rejects-unknown/apply-refuses-blind/no-op-when-unchanged/diffs-only-changes; backup list/empty/clean-flag/traversal-jail/404; runner start_script execution + single-job-covers-scripts — the latter caught a TEST bug: pytest.raises(HTTPException) can never fire through TestClient; assert on the 409 response instead). Old runner test's error-string regex updated to the unified message. Suite **753/753**; lint clean; app.js + server boot verified live.
- **Version bumps:** webapp 0.2.0 → **0.3.0**; pipeline stays 0.5352 (the Exp 246 fix landed this session as v0.5352).
- **Status:** ✅ all three tabs live + smoke-tested against the real PS4; awaiting user's in-browser pass.

### Experiment 248: RCA — "2/3 features" boot toast + vanished song metadata; flags pull-before-push + test-suite PS4-safety net (2026-10-02)
- **Date:** 2026-10-02 (second incident same day)
- **User-reported symptoms (hardware):** boot toast "2/3 features enabled" (was 3/3); song-list custom metadata GONE (customs still there, mode selectors + nonstandard modes still work) — i.e. enable_song_metadata_modification OFF in-game.
- **RCA (evidence: local+committed features.json carry `enable_song_metadata_modification: false`; the Exp-246 restore had set it true on the PS4 at 20:13):** My test suite mutated the user's live PS4.
  1. The Exp 246 restore re-enabled the flag via --features-only but left the LOCAL features.json stale (false — the release-validation round-trip state).
  2. `apply_feature_flags` based its write on the LOCAL file and pushed it wholesale — the exact pull-before-push violation fixed for redirects in Exp 246, still present on the flags path.
  3. The AMPLIFIER: `test_flags_apply_diffs_only_changes` called the /api/jobs/flags-apply endpoint with the live read MOCKED → started a REAL pipeline --features-only subprocess against the user's console → pushed the stale local file (with the requested diff riding along). Post-deploy, the flag was OFF in the committed features.json too — I then STAGED that poisoned file as part of Exp 247's commit batch.
  - NOT a QA miss, NOT the webapp's API design (its diff logic was right); the endpoint test bypassed the webapp's own guard by mocking the read while NOT mocking the runner. My "hardware-gate pattern" claim was violated by my own tests — the second time the tests' behavior diverged from the documented rule (first: never ran final-form).
- **PS4 restored (live-verified):** --set-feature enable_song_metadata_modification=true via the FIXED pipeline → live + local both all-4-ON; --verify-ps4 PASSED (53 redirects, packs, catalog). Boot toast expected back to 3/3; metadata restored.
- **Fixes (pipeline v0.5353):**
  1. **Flags pull-before-push:** new `_download_features_from_ps4` (mktemp -d + raw_decode banner-proof extraction; ABORT on read failure; absent file = clean slate from DEFAULT_FEATURES; Exp 221 default-materialization preserved); `apply_feature_flags` = parse diffs first (syntax error aborts pre-I/O) → pull live → materialize defaults → apply ONLY requested diffs → resync local → deploy. 9 regression tests incl. the exact live scenario (stale local=false, live=true, unrelated diff → live value preserved).
  2. **Test-suite PS4-safety net:** ALL webapp job-starting endpoint tests mock the runner (FakeJob records argv — asserted, better coverage than before); `tests/conftest.py` blocks lftp UPLOADS suite-wide (AssertionError on ` put `); reads/listings allowed (hardware-gated tests).
  3. Banner-parse: raw_decode scanning everywhere now (first-{ to last-} BREAKS on trailing banners starting with `}` — third instance this month; the new pipeline helper initially had it, caught by its own test pre-field).
- **Verification:** suite **763/763** (753 + 9 new + 1 conftest-guard refinement); live PS4 flags verified all-ON; --verify-ps4 green.
- **User-facing answer also delivered:** GitHub Pages — user had enabled BRANCH mode (main /docs — would publish developer-info.md, not the app, and would conflict with pages.yml). Directed: switch Settings→Pages→Source to "GitHub Actions"; local preview served + verified (data-mode=pages, all assets 200); workflow_dispatch allows branch testing pre-merge.
- **Lessons (durable):** (1) pull-before-push applies to EVERY PS4 state file, not just redirects — features.json was the same bug class waiting; (2) a test that mocks INPUT but not EXECUTION is a live-fire test — mock at the execution boundary (the runner), not the data boundary; (3) after any state-mutating live operation, verify BOTH sides (PS4 + local cache) — the Exp 246 restore's blind spot was exactly "local file not resynced".
- **Status:** ✅ fixed + restored + suite fenced; user to confirm 3/3 toast + metadata on next boot.

### Experiment 249: Backups-folder browse + THE feature-flag independence audit (2026-10-03)
- **Date:** 2026-10-03
- **User reports:** webapp deploy validated on hardware (Sandstorm over MessItUp: clean log, 53 redirects preserved; cross-pack spot-check + new custom both play). Requests: (1) browse button + path display for the backup tab's hardcoded folder; (2) re-iterate remaining test procedure steps; (3) thorough audit of every feature flag's usages and independence — "each flag should be entirely independent of the other flags (except the global enable)"; disabling one must never crash.
- **Built (webapp 0.4.0):** webapp_state.py (per-machine settings, gitignored webapp_state.json); /api/backup/dir GET+POST + /api/backup/browse (server-side dirs-only browser, manual path entry, use-default reset); backup jobs pass `--out <dir>` when the folder ≠ default (backup script gained the --out flag; restore already took absolute paths); UI: path display + Browse… panel + parent/up navigation + Choose-this-folder.
- **THE AUDIT (every g_feature_* site traced in plugin v0.8047, all 16 ON/OFF combinations evaluated):**
  - Wiring: enable_plugin = global gate checked first at every subsystem (L367 redirects, L703/759 metadata hooks, L858 hook installer); defaults TRUE when key absent (only flag that does).
  - **Independence HOLDS for crash-safety in all 16 combinations.** Proof points: replacements ⊥ metadata (zero shared state; "label only" and "custom without label" both render); metadata ⊥ mode-mapping (zero shared sites); missing files all safe (absent features/metadata/redirects each log + no-op; all table reads count-guarded, null-checked).
  - **One designed, documented coupling:** mode-mapping's gate sits INSIDE the replacements loop (Exp 222) — so replacements=OFF + mode-mapping=ON is unobservable (modes can't appear over stock packs). This is also the Exp 180 crash-fix invariant (patched catalog + stock bundles never co-serve). Documented as a modifier-of-the-redirect-stream, not a defect.
  - **The one hazard (cosmetic, self-healing):** metadata flag OFF mid-session — move_next_hook mutates BeatmapLevel.songName/songAuthorName IN-PLACE; list cells built before the change keep swapped strings until re-entering the song list (MoveNext re-populates). No crash path: hooks null-check every pointer; string-creation falls back to the original object on failure. Mitigation shipped: explanatory note in the Flags tab UI (option b of the audit's options; option c — plugin-level string restoration — explicitly not recommended: more state, more risk).
  - Full matrix + wiring + options captured in the KB: .agent/llm-wiki-knowledge-base/feature-flag-independence-audit.md (indexed).
- **Tests:** 7 new (backup-dir get/set/persist/reject-empty; browse dirs-only/reject-missing; --out in backup argv when custom dir; NO --out at default) + 4 old tests migrated from the removed BACKUP_DIR constant to the _backup_dir() function. Suite **770/770**. Lint clean; app.js parses.
- **User-facing deliverables this cycle:** browse feature, the audit report + KB page, the Flags-tab staleness note, and the re-iterated test procedure (Phases 0-6 with expected outcomes).
- **Status:** ✅ browse shipped; audit complete — independence holds, one cosmetic hazard documented + mitigated in UI; awaiting user's remaining test phases.
