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
