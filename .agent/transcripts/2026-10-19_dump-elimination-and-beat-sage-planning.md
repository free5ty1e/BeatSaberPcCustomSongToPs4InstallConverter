# Session Transcript — M12 Era: Dump-Requirement Elimination Research + Beat Sage/Local-Folder Planning

**Date:** 2026-10-19
**Session topic:** Post-M11 exploration: (a) eliminating/automating the ps4_dump folder requirement so the repo is legally complete for new users; (b) the web app's Pick-a-song tab gaining Beat Sage + local-folder support. Two plan documents + README FTP prerequisites + roadmap additions.
**Experiments:** Exp 279 (M12 kickoff — research + planning)
**Prior transcript:** `.agent/transcripts/2026-10-14_in-game-plugin-toggle-m11.md` (M11 — SHIPPED)
**Experiment log:** rotated — M11 (exp278-278k) archived; fresh log opens at Exp 279.

## Research performed (hard data, measured this cycle)

**The dump's TRUE runtime footprint (measured from the actual 4.9GB dump):**
- What the pipeline actually reads: (1) per-slot template files (`Media/StreamingAssets/BeatmapLevelsData/<slot>` — single UnityFS files, ~13.24MB avg); (2) the 5 target pack bundles (`Media/StreamingAssets/aa/PS4/<pack>_pack_assets_all_<hash>.bundle` — 34.8MB total); (3) the origin catalog (`aa/catalog.json` — 0.79MB). NOTHING ELSE.
- Current live 5-pack/47-song loadout needs **658MB** (622MB templates + 35MB packs + 1MB catalog) — vs the 4.9GB dump. A ONE-pack user needs ~140MB; a single-song addition needs one ~13MB template file.
- Config: `paths.game_dump_dir` (+ pack_modes dump paths) — all PROJECT_ROOT-relative since Exp 271.

**The previously-overlooked alternative (log-proven):** the game reads its own assets from **`/archive/mount/point/Media/...` (1,067 opens) and `/app0/Media/...` (1,073 opens)** — both mounts are openable IN-PROCESS by our plugin (the open-hook log proves the paths resolve). **A plugin-side extractor can copy exactly the files the pipeline needs into the AFR directory during a normal boot** — no dumper homebrew, no USB, no 4.9GB dump; the web app pulls the small set over FTP into a local `game_data/` cache that mirrors the dump's relative layout (so the pipeline needs ZERO changes — just point `game_dump_dir` at the cache). Per-user extraction from their own console = legally clean; nothing committable is game content.

**Legal analysis:** committing templates/pack bundles/catalog (even pre-patched) = shipping copyrighted game bytes = NO. The committable-repo goal is achieved by per-user extraction (Path A) now, and eventually by the custom-album model (Path C, all-custom content) which eliminates stock-bundle dependence entirely.

**Path C (the user's new-album idea) analysis:** eliminates templates + pack bundles + catalog merging (all-custom content, arbitrary song count, repo-committable structure) — but heavy unknowns: how the game enumerates packs (catalog-driven vs PSN-entitlement-gated), creating NEW catalog entries (we only update existing ones today), from-scratch bundle builders. Big milestone; research-first. Not gated by any existing roadmap feature.

**"Explore other roadmap features first?" — answered:** no existing roadmap item is a prerequisite. M3 note colors is orthogonal (but its research target `globalgamemanagers.assets` should be an extractor-manifest candidate when M3 lands). The cache+extractor work stands alone.

**Web app dump guide today:** manual recipe (dumper.cfg download, GoldHEN → PS4 Dumper homebrew, USB stick, copy into ps4_dump/) — Path B keeps this as fallback and adds automated import/scoping; Path A removes the dumper step entirely.

## Deliverables this cycle
1. `.agent/plans/eliminating_or_automating_ps4_dump_folder_requirement.md` (filename typo corrected per user approval)
2. `.agent/plans/beat_sage_and_local_song_folder_support.md`
3. README: FTP prerequisites + limitations-without-FTP callout
4. Roadmap: M12 (game-data cache + in-game extractor), M13 (Beat Sage + local folder), M14-exploration (custom album)
5. Experiment log rotation + this transcript

(Appended at cycle end with the write-up results.)

## Cycle 1 — Deliverables written (Exp 279)

1. **`.agent/plans/eliminating_or_automating_ps4_dump_folder_requirement.md`** (filename typo corrected per user approval) — the full research: measured dependency footprint (658MB live / ~140MB per pack / ~13MB per slot vs 4.9GB dump), legality analysis (game bytes never committable; per-user extraction clean), Path A (RECOMMENDED: plugin `enable_game_data_extractor` + manifest + AFR cache + web-app pull into a layout-mirroring `game_data/` cache → zero pipeline changes), Path B (web-app import for existing dumpers), Path C (the user's new-album idea — long-term ideal, U1-U4 unknowns, M14-exploration), the roadmap-prerequisite answer (none), risks R1-R4, M12.1-M12.5 phases.
2. **`.agent/plans/beat_sage_and_local_song_folder_support.md`** — the Pick-a-song tab additions: Beat Sage three-tier automation ladder (Tier 1 backend-driven generation behind a to-be-verified undocumented API; Tier 2 guided flow + fully-automated zip intake — the guaranteed tier; Tier 3 manual fallback), the rights + ToS handling, the local-folder section (path validation + zip drop + staging + recent list), the web-app-only adapter surface (zero pipeline changes), hermetic test plan, M13.1-M13.4 phases.
3. **README**: Prerequisites table (jailbroken PS4 + GoldHEN, ⚠️ FTP REQUIRED callout, game version, user-supplied dump w/ M12 pointer, Python) + "Limitations without FTP" section (the five ❌s + the one thing that works PC-free: the M11 hotkey + the no-alternative-transport note).
4. **Roadmap**: M12, M13, M14-exploration sections added.
5. **Rotations (user directive)**: M11 experiment log (exp278-278k) → archive; fresh M12-era log with Exp 279; this new session transcript opened.
6. project_summary + context.yml updated to the M12 era.

**Status:** ✅ research + planning complete. Awaiting the user's pick: M12 (extractor + cache) and/or M13 (Beat Sage + local folder) — both are implementation-ready plans.

---

## Cycle 2 — M12 IMPLEMENTED (Exp 280): plugin v0.8054 + pipeline v0.5364 + webapp 0.6.14

**User:** plans approved; M12 then M13; the goal locked: only the developer needs ps4_dump. Branch renamed feature/eliminate-ps4-dump-requirement-and-support-beat-sage.

**Implemented (full detail in the Exp-280 log entry):** the plugin extractor (both-mount copy loop, requests/status text formats, idempotent + ERR-retry, kill-switch-independent, toast N/6); the pipeline's --request-game-data/--pull-game-data modes (manifest from the ids file — no dump needed; slot requests auto-include pack bundles; every error carries a fix); the webapp's Option A flow (pack checkboxes + 5-step guide + live state + use-cache switch; both operations are pipeline subprocesses — the thin-layer doctrine held). Config gains paths.game_data_dir (./game_data).

**Bugs found + fixed during the build:** (1) webapp endpoints appended after the __main__ guard → 404s — reordered before it; (2) the Exp-278f DEFAULT_FEATURES pin caught the 6th flag; (3) three stale N/5 toast pins + two grown-open_hook test windows updated; (4) ambiguous list-comp var + missing os import (ruff).

**Verification:** manifest math verified live (lizzo=11, 2BeLoved=3, 5-pack=53); both plugin builds clean with extractor strings; suite 930/930; ruff clean; the webapp serves the new endpoints (state endpoint live-tested: PS4 off → clean unreachable state).

**Status:** M12.1-M12.3 + M12.5 complete. M12.4 (hardware) pending: deploy v0.8054 + flag → request lizzo → boot once → pull → use-cache → cache-only deploy → verify. Then M13.

---

## Cycle 3 — Exp 280b: the phantom-button fix + KB audit + the simulated release

**User:** broke at checklist step 1 (no Deploy Plugin button — correct, it never existed); asked for the KB audit, a simulated release folder that can't see the dev dump, backup+clear for a clean slate, and the plan as an execution log with a revised detailed procedure. Then: Deploy Plugin on the Deploy tab AND Get Started; DEBUG option only on the Deploy tab.

**Done:** webapp 0.6.15 (plugin-only deploy: endpoint + Deploy-tab card w/ DEBUG checkbox + Get Started step-5 button; 5 tests; suite 935/935); KB new page game-data-extractor.md + index; make_simulated_release.py + /workspace/release-test built + boot-verified (deploy-plugin endpoint fired a REAL deploy against the reachable PS4 — v0.8054 now on the console, transparently noted, Phase-0 Clear resets it); the plan doc is now the execution log with Phase 0 (backup+clean) / Phase 1 (simulated 10-step) / Phase 2 (real release) + the parity check.

## Cycle 4 — Exp 280c: the Deploy-Plugin 404 RCA'd (the version-lie stale process)

**User:** Deploy Plugin smoke test → "❌ Not Found".
**RCA:** the running server was an Exp-280-era process serving 0.6.14 code, but the ping read the VERSION file at REQUEST time → reported 0.6.15 → looked current → (and would have defeated the launcher's staleness check the same way). **Fix:** import-time capture of all three versions (`_capture_code_versions()`); ping reports the RUNNING code's versions — a stale process now honestly reports its own version → the launcher flags STALE → stop-and-restart. 3 regression tests; stale process killed + fresh verified (route present); the simulation rebuilt + verified. Suite 938/938; ruff clean. KB round-3 lesson recorded with the symptom signature.

## Cycle 5 — Exp 280d/280e: the user's Round-1 findings all fixed

**User:** bundled plugin needs a version number; post-clear errors instead of clean-slate reporting. **Fixed:** 550→absent classification (fetch_remote_json + ReadResult.absent riding through the readers' transformations — the plumbing bug I found while verifying), the explicit "✅ Clean slate" banner, the PRX-banner version extraction (v0.8054 verified live), the backup script's clean pattern gap (5 stale previews-variant bundles survived — + the M12 extractor files added). Two of my own orphaned server instances caught (the 280c capture exposed one honestly). Suite 854+93 gated; ruff clean. The simulation rebuilt + running on 8799; clean_slate=True verified against the real console.

## Cycle 6 — Exp 281: the invisible extractor + fresh-install defaults all-ON

**User:** no extractor on the flags tab (RIGHT — the KNOWN_FLAGS edit was lost in a failed edit call and never re-applied) + the directive: all flags default ON on a fresh install. **Implemented everywhere:** plugin v0.8055 (absent-file defaults all-ON), pipeline 0.5365 (DEFAULT_FEATURES all-True), webapp 0.6.17 (KNOWN_FLAGS 7 flags + DEFAULTS_TRUE = all + description updates), all doc surfaces, the CLAUDE.md §2 doctrine change (3-way synced), 6 test files re-pinned + the fresh-install all-ON pin. The simulation rebuilt + live-verified: all 7 flags ON against the clean console; the extractor needs no arming. Also fixed the hardcoded version label in make_simulated_release (parses the PRX banner now).

## Cycle 7 — Exp 281b: request-succeeded-but-looked-failed

**User:** request flow errored "PS4 unreachable"; wants Select-all + PS4/web-app feedback. **RCA (live):** the request SUCCEEDED (the 11-file manifest is on the console); the status reader misclassified absent-as-unreachable (pre-280d code path) + the invalid net:connect-timeout variable noise. The dir-missing theory disproven (malformed ls -la probe) — the mkdir bootstrap stays as a safety net. **Added:** absent-classification in the game-data readers (verified live: pending: 11), Select all/none + size estimates, the 5s auto-poll with the "⏳ boot the game" state, the plugin's "BSD: game data ready" notification. Suite 857+93; ruff clean; simulation rebuilt + live-verified.

## Cycle 8 — Exp 282: 🎉 the no-dump flow hardware-validated end-to-end

The user ran steps 1-7 from the simulation and it all worked: v0.8055 deployed → request → boot (the extractor: 11 files / 101.7MB / 0 errors, all from /app0; the notification fired; the web app auto-flipped to "all extracted") → Pull (98MB into release-test/game_data) → Use (game_dump_dir switched). Console log archived + cleared; the stale bundles confirmed gone. The VERSION-file question: pre-commit fold policy + the trailing-newline artifact (restored). Remaining: the cache-only song deploy (the proof build) + Phase 2 from a real release build.

## Cycle 9 — Exp 281c: the cache-only song deploy's two fresh-console bugs fixed

The user's Buddy Holly → 2BeLoved deploy built perfectly cache-only but failed twice on deploy: (1) the upload verify's basename equality never matched GoldHEN's full-path ls lines (FALSE "UNVERIFIED" — the 28MB bundle was verifiably on the console); (2) the Exp-246 scoping guard treated ABSENT redirects.json as a failed read and refused — a decisive 550 is the clean-slate state (no customs to preserve → proceed with target+pack scope). Fixed both + the flags reader's same class (550 → defaults); shared `_ps4_output_looks_absent`; 4 tests; suite 861+93; ruff clean; simulation rebuilt.

## Cycle 10 — Exp 281d: pack-modes follows the cache + absent/failed split + the numbered walkthrough

The user's fresh deploy failed at two deeper layers: pack_modes.dump_dir never followed game_dump_dir (the "Use" switch left the pack builder hunting ps4_dump → "Dump dir missing" → the pack patch skipped) and the redirect-config deploy refused absent+local (the clean-console first deploy). Fixed both (unpinned dump_dir follows at load; _download_redirect_from_ps4 raises on genuine failures, returns None only for decisive absent — the caller deploys the freshly-built local set on a clean console; the Exp-246 gate preserved + stronger). Shipped the 5-step numbered walkthrough with active-step highlighting + the STEP-3 live progress bar. One self-inflicted lesson: a heredoc edit printed without writing (FIX A lost) — caught by the config assertion + re-applied. Suite 867+93; ruff clean. The console holds the user's 23/23 extracted files; the rebuild cleared the LOCAL cache (noted) — the next Pull re-fetches.

## Cycle 11 — Exp 281e: the clean-slate audit

The user asked whether --clean-ps4 was ready for a full fresh-slate run. Answer: NEEDED attention — the game_data flat pattern could only hit the Media directory (DELE on a dir fails) → every extracted file would have survived. Fixed with _ftp_recursive_delete (depth-first). Verified LIVE: backup → clean → post-clean probes (AFR empty, game_data ABSENT, plugin ABSENT, plugins.ini entry gone) → a second clean found nothing (idempotent). The simulation rebuilt + app restarted with the complete fresh state (clean_slate=True, 0/0/0, config at the absent ./ps4_dump_local). Ready for the definitive end-to-end run.

## Cycle 12 — Exp 281f: the certainty audit + THE definitive proof

The user's full run succeeded (played the custom song!) and they asked the certainty question. The audit found a HYBRID: the wizard had pinned pack_modes.dump_dir at the real dump — the pack step read the lizzo bundle + catalog from /workspace/ps4_dump. Fixed (0.6.19: the Use button repoints everything; the wizard's dump_root optional → the cache default). THE PROOF: with the real dump physically HIDDEN, the full deploy completed cache-only — validation PASSED. Dump restored. alpha01 watched + validated (CI 960→837+123; all artifacts; the webapp delta = the 281f fixes → alpha02). The full docs audit done: README/Get Started/introduction/CI_RELEASE/feature doc/KB all carry the no-dump-required message. M12 COMPLETE pending alpha02.
