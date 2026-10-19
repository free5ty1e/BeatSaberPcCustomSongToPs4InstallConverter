---
name: experiment-log
description: "Active experiment log for the CURRENT feature only (M12 era: eliminating/automating the ps4_dump requirement + Beat Sage/local-folder web-app support — post-M11 research & planning). Per-feature rotation: when a feature concludes, archive this file into experiment_log_archive/ and open a fresh log. Experiment numbers are globally sequential across the whole project."
metadata:
  node_type: memory
  type: reference
---

# Experiment Log: Beat Saber PS4 Custom Song Support — M12 Era (Dump Elimination + Beat Sage)

**Feature:** Make the repository self-sufficient for new users: eliminate or fully
automate the `ps4_dump/` requirement (legally — no game bytes in the repo), add
Beat Sage + local-song-folder support to the web app's Pick-a-song tab, and document
the FTP prerequisite honestly in the README. Plans:
`.agent/plans/eliminating_or_automating_ps4_dump_folder_requirement.md` +
`.agent/plans/beat_sage_and_local_song_folder_support.md`.
**Started:** 2026-10-19 (Exp 279)
**System:** PS4 FW 9.00, GoldHEN 2.3 / 2.4b16.2 · Plugin v0.8053 / Pipeline 0.5363 / Webapp 0.6.13
**Archive:** Exps 278-278k (M11 In-Game Plugin Toggle — SHIPPED in v0.8053-pipeline-0.5363-webapp-0.6.13) → `experiment_log_archive/experiment_log_in-game-plugin-toggle_exp278-278k_2026-10-14_to_2026-10-19.md`

---

### Experiment 279: M12-era kickoff — dump-requirement research (measured, not assumed) + two plan documents written (2026-10-19)
- **User:** post-M11 direction — thoroughly explore eliminating the ps4_dump folder requirement (alternatives previously overlooked? would a NEW custom album help? would any existing roadmap feature help first?); goal: a legally committable repo so new users can start immediately; OR a web-app-automated dump procedure. Plus: call out FTP as a prerequisite in the README with the limitations of not having it. Second feature: the Pick-a-song tab gains a Beat Sage section (automate as much as possible, guide the mandatory manual steps) and a local-song-folder section below it. Two plan documents requested. Filenames: user's typo ("elimintating") corrected per explicit approval. **Transcript + experiment log rotate per milestone (user directive).**
- **Research (all measured against the real dump):**
  - The pipeline's ONLY runtime dump dependencies: per-slot template files (~13.24MB avg, 622MB for the live 47), the 5 target pack bundles (34.8MB), aa/catalog.json (0.79MB) — **658MB total vs the 4.9GB dump; ~140MB for a one-pack user; one ~13MB file per single-song addition.**
  - **THE OVERLOOKED ALTERNATIVE (log-proven):** the game reads its assets from `/archive/mount/point/Media/...` (1,067 opens) and `/app0/Media/...` (1,073 opens) — both openable IN-PROCESS by the plugin. **A plugin-side game-data extractor can copy exactly the needed files to the AFR dir during a normal boot** — no dumper homebrew, no USB, no PC-side dump; the web app pulls the small set over FTP into a local `game_data/` cache mirroring the dump's relative layout (zero pipeline changes — `game_dump_dir` points at the cache). Legally clean (per-user extraction from their own console).
  - Committing any game-derived bytes (even pre-patched) is NOT legal → the committable-repo goal rides on the extractor (near-term) and eventually the custom-album model (all-custom content).
  - New-album analysis: eliminates the entire stock-bundle dependence + lifts the 47-slot ceiling, but unknowns (pack enumeration: catalog-driven vs entitlement-gated; NEW catalog entries; from-scratch bundle builders) make it a research-first BIG milestone — recorded as an exploration entry, not the near-term path.
  - Existing roadmap features: NONE are prerequisites (M3 note colors orthogonal; its `globalgamemanagers.assets` noted as a future extractor-manifest candidate).
- **Deliverables:** two plan documents (recommended path A = extractor + cache; path B = webapp-automated dumper import as fallback; path C = custom-album exploration), README FTP prerequisites + limitations section, roadmap M12/M13 + M14-exploration entries, log/transcript rotation.
- **Status:** ✅ research + planning complete. Awaiting user pick: implement M12 (extractor + cache) and/or M13 (Beat Sage + local folder).

### Experiment 280: M12 IMPLEMENTED — the in-console game-data extractor (plugin v0.8054 + pipeline v0.5364 + webapp 0.6.14); hardware validation pending (2026-10-19)
- **User:** approved the plans; M12 then M13 in sequence; the optimal outcome locked in: only the DEVELOPER needs ps4_dump — users never do. Branch renamed accordingly (feature/eliminate-ps4-dump-requirement-and-support-beat-sage).
- **Plugin v0.8054:** `enable_game_data_extractor` flag (console-maintenance tooling like the M11 hotkey — NOT gated by the kill switch); reads `game_data_requests.txt` (web-app-owned, one rel path/line) and stream-copies each file from the game's own mounts (`/archive/mount/point/` then `/app0/`) into `game_data/` in the AFR dir; mkdir-p chain; 256KB static buffer; line-exact done-matching (suffix paths can't false-match); ERR lines retry next boot; once-per-boot; per-file logs with byte counts + serving mount; toast N/6. All I/O via direct sceKernelOpen (no open-hook interference).
- **Pipeline v0.5364:** `--request-game-data --game-data-packs/--game-data-slots` (manifest computed from beat_saber_song_ids.json — NO dump needed; a slot request auto-includes its pack's bundle; upload verified; errors carry fixes) + `--pull-game-data` (status read → resumable lftp mirror into paths.game_data_dir, new default ./game_data; missing-file check; every failure carries a "To fix:"); DEFAULT_FEATURES gains the flag; requests.txt pipeline-owned / status.txt plugin-owned (pull-before-push doctrine). Measured: lizzo=11 entries, 2BeLoved=3, full 5-pack=53.
- **Webapp 0.6.14:** Dump Guide gains "Option A — Let the game extract it" (5-step guided flow: arm flag → pack checkboxes from /api/catalog → request → boot once → pull → use the cache) with live state polling; 4 new endpoints (both operations = pipeline subprocesses — thin layer); 6th flag everywhere; TOAST_VERSION v0.8054. One build bug fixed: endpoints were appended AFTER the __main__ guard (dead code — 404s); reordered before it.
- **Docs:** NEW feature doc docs/features/game-data-extractor.md (ships in the zip — plugin-build.yml cp list updated, enforced by the Exp-278i all-docs-bundle test); README (prerequisite row rewritten — dump no longer required for users; feature-table row); CI_RELEASE (6th flag + N/6 toast + doc row); ps4_config.example.json (game_data_dir); KB feature-flags + index.
- **Verification:** manifest computation verified against the real ids file (lizzo=11, slot=3 with pack bundle, 5-pack=53); plugin builds clean (release 105,568 B + debug 105,648 B, both with the extractor strings); suite **930/930** (19 new test_game_data.py tests + every stale N/5→N/6 pin updated incl. the Exp-278f workflow test's DEFAULT_FEATURES set); ruff clean; webapp boots with the new endpoints serving (state endpoint verified live: PS4 off → correct unreachable state + empty cache reporting).
- **Status:** ✅ implementation complete. PENDING (M12.4 hardware): user powers on the PS4 → deploy plugin v0.8054 + enable the flag → request a pack (recommend lizzo first — 11 files ~140MB) → boot the game once → pull → use-cache → deploy a song from cache-only → --verify-ps4. The devcontainer keeps the real dump for development parity checks.
