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
