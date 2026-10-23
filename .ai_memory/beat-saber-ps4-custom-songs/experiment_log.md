---
name: experiment-log
description: "Active experiment log for the CURRENT feature only (M13: Beat Sage + local song folder support in the web app's Pick-a-Song tab — the 3-tier automation ladder, zip intake, local-folder validation + staging). Per-feature rotation: when a feature concludes, archive this file into experiment_log_archive/ and open a fresh log. Experiment numbers are globally sequential across the whole project (last used: 282/281h in the M12 log)."
metadata:
  node_type: memory
  type: reference
---

# Experiment Log — M13: Beat Sage + Local Song Folder Support

Feature: the Pick-a-Song tab gains (2) Beat Sage — AI map generation from any
audio, with a 3-tier automation ladder (backend-driven → guided + zip intake →
manual fallback) — and (3) a local song folder section (path validation + zip
drag-drop + staged-songs list). Plan: `.agent/plans/beat_sage_and_local_song_folder_support.md`.

Archived logs: `experiment_log_archive/` (the previous feature ended at Exp
281h + 282 — the M12 dump-elimination log,
`experiment_log_dump-elimination_exp279-282_2026-10-19_to_2026-10-22.md`).


### Experiment 283: M13 IMPLEMENTED — Beat Sage Tier 1 live-verified + local-folder staging; the full user flow proven to the FTP step (2026-10-22)
- **User:** "ready to move on to M13, we have a new branch, please proceed" (branch: feature/m13-beat-sage-integration).
- **The research first (M13.3):** live-captured beatsage.com's whole API from their Nuxt bundle — the webpack-runtime chunk map → the page chunk → serverFetch routes + the FormData construction + the Vuex defaults. Contract: Cloud Run host, create/heartbeat/download routes, multipart fields verbatim, status values, their 3s/3-failure poll cadence, v2 has NO Easy. KB: beatsage-api-capture.md.
- **Implementation (web app 0.6.20, zero pipeline/plugin changes as planned):** adapters/songs.py (validator mirroring the pipeline's contract, zip-slip-guarded intake, persistent staging w/ auto-prune), adapters/beatsage.py (contract constants + HTTP client + the guided payload), beatsage_client.py (the Tier-1 job: upload → poll at THEIR cadence → download → validate → stage; any failure prints the guided-flow pointer), server endpoints (validate-dir, stage-zip, staged+DELETE, beatsage/guide, jobs/beatsage), deploy.py --song-dir (the pipeline's own precedence), the two new UI sections + staged list + the pages-mode command-builder variant.
- **Testing:** 57 new tests (24 songs fixtures V2/V3/V4+failures+slip-guard; 18 beatsage contract+client state machine, all HTTP mocked — CI never contacts them; the live-contract test is BEATSAGE_LIVE-gated and PASSED against the real service with a synthesized tone); 7 deploy-argv; 11 server endpoints; the NEW quickjs JS-syntax gate (Exp finding: esprima-era parsers choke on valid modern code, and the Python suite had NO JS gate — quickjs caught a real template-literal missing paren + a lexical redefinition that had slipped through). Suite: 924 passed + 93 hardware-gated; ruff clean; python-multipart + quickjs added to requirements.
- **The live Tier-1 proof (the full user flow):** synthesized a 48s RIGHTS-CLEAN original song (development/scripts/make_rights_clean_test_song.py — math only, no samples) → the app's own /api/jobs/beatsage → Beat Sage accepted → DONE in 12s → 338,890-byte zip → validated (V2, Normal/Hard/Expert/ExpertPlus) → STAGED; the staged entry survived a web-app restart (persistence proven); the command preview emits --song-dir correctly.
- **The deploy:** the staged folder → /api/jobs/deploy song_dir=TrueHurts: V2→V3 auto-converted, Easy auto-filled from Normal (Beat Sage can't make it — our pipeline covers the gap), 15 mode beatmaps generated, bundle built + verified (6.9MB)… and the FTP push hit No route to host — the PS4 went to rest mid-flow. The job failed CLEANLY (lftp 600s timeout, exit 1; a possibly-partial TruthHurts_v3.bundle is stale-but-harmless; the re-deploy overwrites it). **Remaining hardware validation: one Deploy click from the staged list once the console is back on.**
- **Docs (M13.4):** feature doc beat-sage-and-local-songs.md (ships in the zip), README feature row, CI_RELEASE rows, KB beatsage-api-capture.md + index, the plan doc run log, roadmap/context.
