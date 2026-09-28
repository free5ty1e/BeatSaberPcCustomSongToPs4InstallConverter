# Beat Saber PS4 Crash — Compaction Anchor (2026-08-16)

## Objective
- Fix the Beat Saber PS4 boot crash. User is frustrated it STILL crashes after the v0.8040 notification even though the catalog fix was deployed. The Exp 189 dataIndex fix is confirmed deployed and moved the crash (no longer at OPEN #74), but a SECOND crash remains later in boot — must be found and fixed.

## Important Details
- PS4 online. Downloading `bs_log.txt`: ftplib RETR fails (502), but `lftp -u anonymous, -p 2121 192.168.100.117 -e "get ...; quit"` works.
- Fresh log: `/workspace/.ai_memory/experiment_logs/v0.5322_boot_after_deploy.txt` (174,000 B, 1,704 lines, cumulative 4 boot sessions, never cleared; repull identical — session 4 is the last/current boot).
- Session 1 (line 1, "loaded 40 redirects"): legacy single-pack (startmeup) config. Got FURTHER — MoveNext hooks fired (lines 755+) → song list text rendered. This is the known-good-ish baseline.
- Session 2 (line 894, "loaded 43 redirects"): crash at OPEN #74 (core_assets.bundle) — broken catalog `0eb8a27d…` (pre-Exp-189 dataIndex bug).
- Session 3 (line 993, "loaded 43 redirects"): crash at OPEN #74 after catalog redirect (#87 REDIRECTED) — same broken catalog.
- Session 4 (line 1092, "loaded 43 redirects", CURRENT boot): catalog redirect OK, NO #74 crash, loads ALL 36 packs (therollingstones #321/#527/#577/#582 REDIRECTED, lizzo #580 REDIRECTED, billieeilish #581 REDIRECTED, camellia #577 REDIRECTED), reaches HMD devices (#585 hmd_cmd, #586 hmd_snsr, #587 hmd_3da, #588 hmd_dist), then HARD CRASH — no MoveNext (song list never renders), no error logged.
- CONFIRMED fixed catalog IS deployed: PS4 `catalog_pack_modes.json` = 795,783 B, md5 `975bacca0902624c9fb5c6a82cfa90c5` = local fixed (0 invalid dataIndexes). So Exp 189 dataIndex fix is live; #74 crash gone. Remaining crash is SEPARATE.
- 43-redirect config has been on PS4 since before session 2 (sessions 2-4 all "loaded 43 redirects"); only the catalog was stale until the Exp 191 deploy.
- User hypothesis (2026-08-16): "if we are destroying the bundle when we modify it with the pipeline then of course the game will crash when it looks for specific assets." → REFUTED by exhaustive verification (see Evidence).
- Regression isolated: session 1 (works further, 1 patched pack via legacy catalog) vs session 4 (crashes pre-song-list, 4 patched packs + merged 2251-entry catalog) → the 4-pack merged-catalog deploy is the differentiator. But bundles+catalog are verified clean.

## Work State
### Completed
- Deployed fixed `catalog_pack_modes.json` (md5 975bacca, 0 invalid dataIndexes) — verified on-device, and confirmed live by session-4 no longer crashing at #74 (Exp 189 dataIndex fix WORKED).
- Hardened `--verify-ps4` (check #7). Removed legacy `pack_bundle` default. Cleaned PS4 legacy files. Version 0.5322, 451/451 tests. Docs updated + staged.
- **REFUTED the "pipeline destroys the bundle" hypothesis with exhaustive verification** (see Evidence). Bundles + catalog are 100% clean.

### Active
- Diagnosing the SECOND crash (session 4): game loads ALL 36 packs (4 patched bundles REDIRECTED + CRC-valid), reaches HMD devices (#585-588), then HARD CRASHES — no MoveNext (song list never renders), no error in log. Crash is during in-memory song-list/asset-DB build after HMD init, NOT during file load.
- Bundles AND catalog are verified byte/structurally perfect. So the crash is a RUNTIME issue that static analysis cannot explain.

### Blocked
- Root cause of post-HMD crash unknown. Bundles/catalog ruled out as corrupt. Remaining possibilities:
  (a) Having 4 patched DLC packs vs the 1 (startmeup) that worked in Exp 182 — aggregation/memory.
  (b) The generalized `build_pack_mode_bundles.py` (never boot-validated) produces output that, while statically clean, the game's loader rejects at deserialization — vs the legacy `inject_pack_bundle.py` prototype that built the working startmeup pack.
  (c) A runtime content expectation (e.g., game chokes on the new preview sets only when many levels are present).
  Cannot diagnose statically — needs a controlled boot.

## Evidence (bundles NOT destroyed — hypothesis refuted)
- All 4 deployed patched bundles md5-match local (no stale deploy): therollingstones 5ed23829…, billieeilish 003ffdc7…, lizzo c87aa5a0…, camellia 878aa774….
- Object tables (pathID+type) IDENTICAL to originals: therollingstones 81/81, billieeilish 51/51, lizzo 49/49, camellia 34/34.
- `byteSize` of patched BeatmapLevelSO correctly grown (Δ588 or Δ464 = 3 added preview sets).
- Preview sets correctly added: therollingstones 11→44, billieeilish 10→40, lizzo 9→36, camellia 6→24. Each = Standard/OneSaber/NoArrows/90Degree with CORRECT characteristic PIDs and 5 difficulties (fid 2/3 external refs copied from Standard).
- No blob truncation: `_contentRating` is the last field for ALL levels in ALL packs.
- Catalog 100% valid: all 138 extra-data entries have dataIndex ≥0 pointing to VALID type-7 blocks (decoded JSON parses, has m_BundleName). CRCs match deployed bundles. dataIndex shift logic verified correct for the 4-block case.

## Next Move
1. **Empirical isolation (decisive):** deploy with ONLY `therollingstones` (1 DLC pack) + catalog redirect (other 3 packs load origin bundles, no mods). Boot once.
   - If it reaches the song list → issue is having 4 patched packs (aggregate) or one of billieeilish/lizzo/camellia.
   - If it ALSO crashes post-HMD → therollingstones DLC pack (built by `build_pack_mode_bundles.py`) is broken at runtime despite clean statics → compare against legacy `inject_pack_bundle.py`/`build_startmeup_pack_modes.py` output.
2. Get the exact PS4 error (CE-34878-0?) and whether the main menu appears at all.
3. If base (38 songs, no packs) is confirmed to still boot (pre-pack_modes state ffb5f8c), that isolates packs as the cause.

## Relevant Files
- `/workspace/.ai_memory/experiment_logs/v0.5322_boot_after_deploy.txt` (and `_REPULL.txt`): current crash log (session 4 = current crash, post-HMD, pre-song-list).
- `/workspace/.ai_memory/experiment_logs/v0.5319_crash_after_packmodes_deploy.txt` + `v0.5321_crash_after_redeploy.txt`: prior crash logs.
- `/workspace/beat_saber_deluxe/catalog_pack_modes.json`: fixed catalog, md5 975bacca, 0 invalid — confirmed deployed.
- `/workspace/beat_saber_deluxe/pack_modes_bundles/manifest.json`: 4 configured packs' patchedBundle/catalogBundleName/crc/size.
- `/workspace/beat_saber_deluxe/tools/build_pack_mode_bundles.py`: `update_catalog_entry()`, `build_modes_blob()`, `rebuild_bundle()`, `validate_catalog_dataindexes()`, `walk_blob()`.
- `/workspace/beat_saber_deluxe/tools/inject_pack_bundle.py` + `development/scripts/build_startmeup_pack_modes.py`: LEGACY prototype that built the Exp 182 working startmeup pack (never-boot-validated generalized path is `build_pack_mode_bundles.py`).
- `/workspace/beat_saber_deluxe/tools/full_custom_song_pipeline.py`: `--verify-ps4` check #7; `deploy_pack_modes`.
- PS4: `/data/GoldHEN/AFR/CUSA12878/{catalog_pack_modes.json (FIXED 975bacca), redirects.json (43, OK), bs_log.txt, 4 *_modes_assets_all_*.bundle}`.
- Staged: VERSION (0.5322), CHANGELOG-PIPELINE.md, .agent/* docs, experiment_log.md (Exp 191).
