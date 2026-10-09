# Session Transcript — Web App Interface (M9)

**Date:** 2026-09-28 (session start)
**Branch:** `feature/web-app-song-conversion-pipeline` (fresh off merged main)
**Prior session:** `2026-09-27_release-validation-hardening.md` (Exps 234–242, the release-validation saga + M9 planning)
**Context:** PR #4 MERGED to main; release `v0.8047-pipeline-0.5351` TAGGED and validated.

---

## Session start — release validated + dump-guide added to plan

### User message (verbatim core)
> "we also want to add info and maybe links or even functionality to the web app to help the user perform the decrypted game dump procedure and get it into a place the web app can access. Additionally, the release has been merged and built successfully; the tag is v0.8047-pipeline-0.5351 — please perform a full automated validation and analyze the results for me, now that we have this process perfected. I've also started us a fresh branch to develop on and checked it out, based off the latest main branch after our feature merge. Please start a new transcript document from this point moving forward on the new web app interface feature, once the release has been validated using your automation test."

### Actions + results

**1. Release state confirmed:**
- Branch: `feature/web-app-song-conversion-pipeline`, branched from merged main (verified `git merge-base --is-ancestor main HEAD`)
- Main history shows the PR #4 merge + user's demo-video README commit ("Added demo video in readme, formatted" — the screenshots/videos the user said they'd add)
- Tag `v0.8047-pipeline-0.5351` exists; Build Plugin + CI workflows all green on it
- Release asset: `beat-saber-deluxe-v0.8047-pipeline-0.5351.zip`

**2. Full automated validation of the FINAL release** (command from the docs, explicit tag):
`bash .agent/docs/release-validation-test-procedure.sh --log /workspace/temp/release-validation-$(date +%Y%m%d-%H%M%S).log v0.8047-pipeline-0.5351`

**RESULT: 35/35 PASS, exit 0** — log: `/workspace/temp/release-validation-20260928-144217.log`
- Static audit 7/7: VERSION 0.5351 in-zip, 69 examples, FSELF+v0.8047 binaries, bundled-plugin fallback + Unicode fix confirmed in shipped code
- **NEW this tag**: the zip now ships both validation-procedure docs (the Exp 241 CI fix — first time live on a published release)
- Core 5/5: verify, build quality (NoArrows 5/5 all-dots / OneSaber 5/5 blue-dots), deploy-full incl. bundled plugin, skip-plugin, debug-swap + restore
- Flags/surgical 9/9: all round-trips verified by PS4 read-back, clear-target-song 47→46→47 surgical + restored, sync/enforce, pack-modes scoping
- State integrity 4/4: **all six `[state]` traces 47/47 — ZERO read failures** (banner-free transport solid), final state == pre-validation on both files AND live PS4, flags all ON
- PS4 left exactly as it stands: 5 packs, 47 songs, full metadata, all flags on

Analysis: the process is genuinely "perfected" in the sense the user meant — the validator exercises the published artifact end-to-end, proves state preservation against the live console with instrumentation at every step, and this run had zero anomalies of any kind (no read failures, no auto-restores, no racing).

**3. Dump-procedure guide added to the web-app plan** (user's new requirement):
- Plan §4.1b "Game Dump Guide": informational (both modes) — step-by-step recipe, **ready-made `dumper.cfg` download** (ours, `split=3`, the exact config our own dump used — verified /workspace/ps4_dump/dumper.cfg), config explained line-by-line, external links in one `links.json`, expected pitfalls called out (missing patch 2.04, DLC installed after dumping, no-split, FAT32 space)
- Functional (local-backend): live structural validation with **per-missing-piece error messages** (which of app/patch missing, eboot+Media present, DLC packs found → confidence list), and a copy/import-dump affordance (with GB-size warning) or remember-path option
- Roadmap M9 core UX: added the dump-guide checkbox
- Plan risk table + Phase 1 exit criterion updated to include the guide

### Files changed this cycle
- `.agent/plans/web-app-song-conversion-pipeline-interface.md` — §4.1b dump guide + risk row + phase-1 exit criterion
- `.agent/roadmap.md` — M9 dump-guide checkbox
- This transcript (new session document)
- (staged for commit: experiment_log Exp 243, context.yml)

### Where we are
The release is DONE (merged, tagged, validated 35/35 in final form). This branch now carries M9 work only. Next step when the user says go: Phase 1 of the web-app plan (FastAPI skeleton + wizard + deploy vertical slice) per `.agent/plans/web-app-song-conversion-pipeline-interface.md`.

---

## Cycle 2 — Pre-compaction plan audit: §9 Implementation Context added

### User
> "audit the plan ... one more time and ensure it contains all relevant context and details - I am going to compact this session after you are finished, so be sure to store needed context in this plan so it is available for us to begin implementation after the compaction."

### Audit findings
The plan carried design context (architecture, pages, phases, risks) but NOT the session's operational knowledge: project operating rules (Danger Mode, versioning, testing, docs-per-cycle, transcripts), environment facts (PS4/FTP specifics, the exact ps4_config.json schema, the three state files and their never-push-without-pull invariant), the BeatSaver API shape + its in-session gotchas (votes fields unreliable, maps get deleted, use versions[0].downloadURL), where every reference artifact lives, and the hard invariants the adapters must respect.

### Actions
- Status header → ACTIVE (release merged; this is the current work item; "Start at Phase 1")
- NEW **§9 Implementation Context** (9 subsections): operating rules binding web-app work; environment facts (config schema verbatim, state files + semantics, validator invocation/parsing contract, BeatSaver API + gotchas, song-selection rules); reference map (15 artifact paths); 8 hard invariants (thin-layer subprocess, single-job, banner-free reads, pull-before-push, enable_plugin default, PS4-is-production confirm posture, wizard dump-validation paths + dumper.cfg source, Danger-Mode git); definition-of-done for M9
- Every cited fact verified against ground truth before writing: function names (`_load_local_redirects` L2664, `_load_local_song_metadata` L3985, `resolve_audio_codec` L181), safe-default flags (example script line 92), song_ids schema (songID/songName/songAuthorName/characteristicModes/difficulties...), config schema (live file), validator output format (`[PASS]/[FAIL]` from mark(), final `PASS: N FAIL: N`, exit 0/1), dumper.cfg (split=3, /workspace/ps4_dump/dumper.cfg)

### Post-compaction entry point
`.agent/plans/web-app-song-conversion-pipeline-interface.md` §9 → Phase 1 (§5). Transcript: this file. Branch: feature/web-app-song-conversion-pipeline.

---

## Cycle 3 — M9 Phase 1 BUILT: webapp skeleton (vertical slice) — Exp 244

### User
> "please proceed with our plan '/workspace/.agent/plans/web-app-song-conversion-pipeline-interface.md'"

### Ground-truth verification (plan §9 discipline, before any code)
- Read the full plan (§1-9). Branch confirmed: `feature/web-app-song-conversion-pipeline` @ c9b11c6 (user committed the staged plan-audit batch), clean tree.
- **All 56 pipeline flags** confirmed via `--help` (both halves); `--deploy-full` semantics verified (build song+pack modes, deploy, redirects, post-deploy validation; exit-nonzero-on-failed-validation confirmed at pipeline L5218-5232).
- **Catalog**: `beat_saber_song_ids.json` = {meta, albums[36]}; album keys pack/packBundle/songs[]; song keys songID (= --target slot), songName, songAuthorName, difficulties…; meta.templateDir notes devcontainer-absolute.
- **Dump** (invariant §9.4.7): `ps4_dump/CUSA12878-app` + `-patch` present; `aa/catalog.json` present; `aa/PS4/` has 272 `_pack_assets_all_*.bundle` files across all 36 packs (30 unique pack prefixes seen — billieeilish, britneyspears, bts, camellia, daftpunk, …). `dumper.cfg` split=3 confirmed → shipped into webapp/static/.
- **BeatSaver API probed live**: search + maps/id return 200 with `Origin: https://free5ty1e.github.io` → CORS OK → Pages-mode client-side search viable. Shape matches §9.2 (docs[].metadata/versions[0].diffs[].notes/downloadURL; stats.downloads; note votes/score sometimes 0/None → never sort on them).
- **FastAPI 0.136.3 + uvicorn 0.49 + httpx/TestClient** already in devcontainer; **tkinter absent** (headless) → wizard ships manual-path entry now; native dialog probes arrive Phase 3 (plan §7.2).
- Pipeline does `logging.basicConfig()` at import + `sys.exit()` everywhere → subprocess design mechanically confirmed (invariant 1). `--verify-ps4` guard confirmed: `if (… or args.verify_ps4) and not args.song_dir:` deploy-only branch (L4762).
- CI: ci.yml (test 649 + lint `ruff check tools/`), plugin-build.yml (release zip packaging; requirements-test.txt → zip requirements.txt). pyproject ruff: line-length 120, E/F/W/I (E501/E402 ignored).
- **No `input()` calls in the pipeline** → subprocess runs can't hang on prompts.
- §3.0 rotation DONE: archived Exp 188-243 log (`experiment_log_generalized-pack-patch_exp188-243_2026-08-14_to_2026-09-28.md`); fresh log opened at Exp 244.

### What was built — `beat_saber_deluxe/webapp/` (webapp 0.1.0, own VERSION + CHANGELOG-WEBAPP.md)
- **server.py** — FastAPI, binds 127.0.0.1:8765 default (`--port`, `--host`, `--no-browser`; auto-opens browser). 20 routes: ping (mode heartbeat), dump/validate + dump/default-location, config GET/POST(save), catalog (slimmed albums→songs), beatsaver search + map/id (404→"may have been deleted"), ps4/test + ps4/state, jobs/{deploy,flags,clear-target,verify,cancel,status,lines}, stream (SSE), command-preview (works in both modes). Job endpoints gated on wizard config existing (devcontainer-absolute-default protection).
- **adapters/paths.py** — release-root-relative resolution (works from extracted zip or dev checkout).
- **adapters/config.py** — validate_dump: per-missing-piece errors (app/patch presence, eboot.bin, origin catalog, DLC confidence list from `<pack>_pack_assets_all_<hash>.bundle` scan), warnings for no-DLC; build_wizard_config: ALL paths localized (game_dump_dir/dump_dir→user's dump; output/build/song_ids/patched_catalog→this release's beat_saber_deluxe/; packs:[] auto-discover per Exp 224).
- **adapters/beatsaver.py** — search + map_by_id; slim projection with nativeDifficulties badge (E/N/H present check); BeatSaverError(status) for 404-deleted handling.
- **adapters/deploy.py** — DeployOptions typed builder → argv. Safe default = example script command byte-for-byte: `--download-beat-saver-song <ID> --target <SLOT> --pcm16 --no-pad --convert-to-v3 --deploy-full`. Also flags_only_command (--features-only --set-feature name=bool), clear_target_command (--clear-target-song), verify_command (--verify-ps4), pipeline_command (release-root-relative render).
- **adapters/ps4.py** — READ-ONLY live state: _run_lftp (anonymous:anonymous form, pitfall 6), fetch_remote_json (get-to-mktemp -d + retries), **_extract_json_object = raw_decode scanning** (see bug below), read_features (enable_plugin defaults-TRUE when absent — the only one), read_redirects_summary (song/pack/catalog counts), read_song_metadata, test_connection. ReadResult(ok,error) — failures are explicit, never empty-truth.
- **adapters/runner.py** — SingleJobRunner: one job at a time (409 on second start), subprocess with CWD=release root, own process group (cancel = killpg), line-buffered drain thread into a 20k-line buffer, lines_since(after) long-poll contract, status/job JSON.
- **static/** — index.html (5 pages: Wizard, Picker, Deploy, PS4, Dump Guide), app.js (mode detect via /api/ping → local-backend vs pages; wizard flow: check-dump → test-conn → save-config; BeatSaver search UI with E/N/H filter + badges; map-ID lookup; deploy: pack→slot cascading dropdowns from catalog, option panel, live command preview, confirm dialog (PS4-is-production), long-poll log streaming, PASSED/FAILED verdict + post-deploy Verify button; PS4 read-only dashboard), style.css, **dumper.cfg** (copied from /workspace/ps4_dump/dumper.cfg, split=3) + inline Dump Guide with line-by-line cfg explanation + external links + pitfalls.

### THE BUG the new tests caught (Exp-240-class, fixed pre-field)
First-`{`-to-LAST-`}` extraction (`text.find('{')..text.rfind('}')`) **breaks when a trailing banner itself starts with `}`** — real lftp banners look like `}156 bytes transferred` → rfind grabs the banner's brace → slice = `<json>}more banner after` → JSONDecodeError on every read. Deterministic on slow links, invisible on fast rigs (the exact Exp 240 signature). Fixed with the KB's proven pattern (Exp 221 / ps4_state.py): `json.JSONDecoder().raw_decode()` scanning each `{` position until one parses; test proves clean/leading/trailing/both-side banners + 0-byte + retry-count + mktemp-d transport shape.

### Tests — 65 new, ALL mocked, zero PS4 contact (hardware-gate pattern)
- test_webapp_config.py (13): every per-missing-piece error path, DLC-list sorting, no-DLC-is-warning, wizard-config localization (all seven path keys), save/load roundtrip (scratch CONFIG_PATH — dev config untouched), paths resolution.
- test_webapp_deploy.py (18): safe-default argv == example-script command; every flag asserted present in live `--help` output (thin-layer proof); option permutations; validation errors; **single-job runner**: busy-refuses-second, lines stream + exit 0, cancel-on-finished no-op.
- test_webapp_server.py (18): TestClient endpoints; dump-validate paths; config-save roundtrip; catalog shape (36 packs); BeatSaver 404→"deleted" message; **ps4 test unreachable → explicit ok:false+error (never fake success)**; deploy-requires-config (Setup Wizard message); flags rejects unknown flag (delete_everything); command-preview safe default; index + dumper.cfg served.
- test_webapp_ps4_adapter.py (16): FakeLftp (writes remote content into the -o target, records commands); banner survival ×4; 0-byte = failure; retries=3 = 3 calls; temp-dir transport shape; enable_plugin default-TRUE; flat-features-format; redirects summary counts.

### Full suite + regression gates
- `python3 -m pytest tests/ -q` → **714 passed** (649 existing + 65 new), 2:30.
- `git diff HEAD -- beat_saber_deluxe/tools/` → **EMPTY** (pipeline untouched; no pipeline/plugin version bump — webapp has its own scheme).
- ruff: tools/ clean, webapp/ clean (4 auto-fixed: unused imports), tests clean.

### Live smoke test (server booted on :8799)
- /api/ping → local-backend ✓; /api/dump/validate?path=/workspace/ps4_dump → ok:true, 30 DLC packs listed ✓; /api/command-preview → byte-exact example-script command ✓; /api/beatsaver/search?q=take+on+me → "Take on Me - a-ha", native E/N/H ✓.
- /api/ps4/test → ok:false + explicit error — **PS4 currently in rest mode / no route from the Docker-bridge container** (192.168.100.117:2121 → No route to host, confirmed by direct TCP probe). The failure path behaved exactly as designed (explicit unreachable, error text shown, never empty-truth). Live test-connection validation happens on the user's hardware run.

### Docs
- README: Web App row in Features table + new §3.1b "Web App — deploy without the CLI (M9, Phase 1)" (usage, capabilities, status, 127.0.0.1-only note).
- roadmap M9: header → IN PROGRESS (Phase 1 built); checked off 5 Core UX items + 3 Architecture items (with Phase-3 notes on picker/dialog/local-songs).
- context.yml: webapp_m9 block (phase1_state, version scheme, the banner-bug finding, awaiting=user hardware run).
- Experiment log: Exp 244 in the fresh M9 log.
- webapp/VERSION 0.1.0 + CHANGELOG-WEBAPP.md (new component scheme per plan §9.1 recommendation).

### Open items carried forward
- Phase 1 exit criterion needs the user's hardware run: wizard → test connection (PS4 awake) → pick song → deploy to a slot → see PASSED.
- Native folder-dialog probe (pywebview) + local-folder song tab + advanced options panel → Phase 3 per plan.
- Pages command-builder build + bundling webapp/ into the release zip (plugin-build.yml) → Phase 3 shipping step.

---

## Cycle 4 — Manage Songs + Full Loadout tabs; deployed-truth model; CI/release audit; Pages (Exp 245)

### User
> "Wow, excellent job - you nailed it! This web app works perfectly here locally at least. Exactly what I wanted! Can we add two new tabs... a tab that is for managing custom songs currently on the PS4... choose a music pack from a dropdown to get a populated table showing each song and its custom status (artist / name of target stock song, artist / name of custom song installed in this slot if any) with a button to uninstall / clear each song. Then another tab that generates a full table showing every music pack and song in the game, along with the custom songs installed over each slot... 'save' the webpage as a simple HTML file or print this page to PDF... Then let's audit the CI and release pipelines and ensure we have full test coverage, and make sure that everything required is included in the release including documentation and instructions. Then we can also try to deploy this to github pages for this repo, enable github pages so we can deploy to a docs folder or something like that."

### Ground truth read FIRST (the join keys, before any code)
- song_metadata.json: `song_names[<stock songName>] = "<Custom> / <Artist>"`, `song_artists[<pack artist>] = " "`; keys are STOCK songNames — NOT songIDs.
- redirects.json: `redirects["BeatmapLevelsData/<songID>"] = "<songID>_v3.bundle"` + pack redirects + `aa/catalog.json`.
- **Join-key quirk found:** catalog `'You Should See Me In A Crown '` (trailing space) vs song_metadata `'You Should See Me In A Crown'` → merge uses case/space normalization.
- CI/release: ci.yml (test installs requirements-test.txt; lint `ruff check tools/` ONLY), plugin-build.yml (test + zip + release; zip has no webapp/).

### THE deployed-truth discovery (live PS4 audit — the cycle's key finding)
Built the first cut of the merge using redirects as "deployed", smoke-tested against the live PS4, and got **1 served / 47 labeled** — which contradicted the user's known-good state (5 packs, 47 songs). Investigated instead of shipping:
- Live redirects.json = 948 bytes, **ONE song redirect** (MessItUp) + 5 pack + catalog.
- AFR dir listing = **48 `<slot>_v3.bundle` files**.
- Plugin source (main.cpp open_hook): the game serves a custom ONLY when a redirects key substring-matches the open path. No fallback. Bundle-without-redirect is NEVER loaded.
- **bs_log.txt (983KB, spans multiple boots) proved it:** earlier boots loaded "47 songs, 5 packs, 1 catalog" (the full loadout, working); the LATEST boot loaded "7 redirects — 1 songs, 5 packs, 1 catalog". The current-boot section redirects only `messitup`.
- **Conclusion:** the deployed-truth model is THREE signals: SERVED (redirect present), STALE (bundle in AFR, no redirect), LABEL ONLY (metadata name, no redirect/bundle). The live PS4 is in a transitional state left by the release-validation `--clear-target-song` round-trip (restore rebuilt metadata, never re-added the 46 song redirects) — surfaced to the user as a real finding: **the current boot serves only MessItUp as a custom song; redeploy the loadout to restore.**
- Modeled all three distinctly in the merge + UI badges (`custom`/`stale`/`label only`/stock), with live-truth regression tests pinning the exact live shape (1 served, 46 stale, 47 labeled).

### Built (webapp 0.2.0)
- adapters/loadout.py: pure merge (catalog × redirects × metadata × AFR listing), normalized metadata join, unmatchedMetadata + unmatchedBundles reporting.
- adapters/ps4.py: `list_deployed_slot_bundles()` (AFR `<slot>_v3.bundle` stems); `read_deployment_state()` now reads redirects + metadata + AFR in one call with per-source read errors.
- server.py: `/api/loadout` (merge + readStatus incl. afrOk), `/api/loadout/packs` (catalog-only, PS4-offline capable).
- UI: Manage Songs tab (pack dropdown → per-song table: slot, stock name/artist, custom name/artist, status badge, Clear button → `--clear-target-song` job → poll → refresh); Full Loadout tab (all 36 packs × songs, "only packs with customs" filter, per-row Clear, print stylesheet: light theme, chrome hidden, break-inside avoid, generated-date footer; Ctrl+S / Ctrl+P → PDF instructions in the intro).
- Pages: webapp/build_pages.py (same UI bundle + `data-mode="pages"` stamp + command-builder banner + instant mode switch in app.js) → /tmp build verified; .github/workflows/pages.yml (push-to-main + manual; build → bundle smoke-test → deploy-pages; concurrency group; OIDC permissions).

### CI/release audit findings + fixes
1. requirements-test.txt had no fastapi/uvicorn/httpx → **CI test job would have failed on the next push**. Fixed (+ release zip requirements.txt inherits them).
2. ci.yml lint covered tools/ only → now `tools/ webapp/ tests/`; plugin-build.yml gained the same ruff step before pytest.
3. Release zip never bundled webapp/ → added rsync (excl. __pycache__) + count echo; release workflow gained a webapp smoke-test step (imports server, asserts /api/ping,/api/loadout,/api/jobs/deploy routes + static files).
4. CI_RELEASE.md: webapp artifact table + "no terminal? start the web app" + Pages note. README §3.1b: the two new tabs + Pages command-builder paragraph; title de-phased ("M9", no longer "Phase 1").

### Verification
- New tests: 16 (merge incl. three-signal pins, live-truth-model class with the exact 1/46/47 shape, readStatus propagation, stale/unmatched-bundle cases). Full suite **730/730** (2:27). Lint clean (2 auto-fixed unused imports). app.js + pages bundle parse.
- Live smoke: /api/loadout → reads ok ×3; served 1 | stale 46 | labeled 47 | unmatched 0; crown-song join works on live data.

### Surfaced to the user (real state, not webapp)
The PS4 currently serves only MessItUp as a custom song (1 song redirect in the live table; the other 46 bundles are stale in AFR; metadata still labels all 47). Recommendation: re-run the chained example scripts to restore the full loadout, then the Loadout tab will show 47 served.

### Files
webapp/adapters/{loadout.py NEW, ps4.py, }, webapp/server.py, webapp/static/{index.html, app.js, style.css}, webapp/build_pages.py NEW, webapp/VERSION → 0.2.0, webapp/CHANGELOG-WEBAPP.md, tests/test_webapp_{loadout.py NEW, server.py, ps4_adapter.py}, .github/workflows/{ci.yml, plugin-build.yml, pages.yml NEW}, requirements-test.txt, CI_RELEASE.md, README.md, docs/experiment log Exp 245, this transcript, context.yml, roadmap.

---

## Cycle 5 — CRASH RCA + PS4 restore (Exp 246) + Flags/Backup/Feature-Request tabs (Exp 247)

### User
> "I tested the PS4 and you're right, all the other custom songs crash now when I try to play them. We have to fix this. Why did this happen? Have you already performed a root cause analysis?... I had this fully tested when we made the last release, so if something is broken we need to know if this is somehow a situation I missed during my QA tests or if this is recently broken in this branch's work. Then, of course, we need it fixed ASAP and I need all my song redirects restored - I have friends coming over soon, fix this ASAP so I can play this game and show it off!... I also don't see a feature flag management tab in the web app yet. Next, I also want the web app to have a feature flag management page... And we also need a backup / restore page for the PS4 backup script, including the clear PS4 flag. Any other missing handy tool pages you can think of... Let's include a feature request tab with a form that will generate a github issue for this repo."

### Exp 246 RCA (complete, evidence-pinned)
Timeline (filesystem + PS4 mtimes): 10:28 user ran the webapp Setup Wizard (wrote localized ps4_config.json) → 10:33-10:34 user deployed MessItUp via the webapp Deploy tab (bundle built 10:33:21, pack bundles 10:34:00-02, redirects.json rewritten 10:34:13, metadata 10:34:15) → the deploy left redirects.json at 1 song.

Root cause chain (3 stacked defects):
1. LOCAL/PS4 DIVERGENCE: the release-validation clear-target round-trip restored the PS4 to 47 but left the LOCAL redirects.json at 1 song.
2. PULL-BEFORE-PUSH VIOLATED (Exp 237 invariant, by the pipeline itself): manage_redirect_config GENERATE mode based generate+deploy on the stale LOCAL file → pushed 1-song over live 47. Post-deploy validation stayed green (it compares local==PS4; both equally wiped).
3. SILENT FALLBACK: the single-song scope expansion's `except: pass` fell back to "just the new target" on PS4-read failure (READ-FAILED as empty-truth, the Exp 239/240 lesson).

In-game crash mechanism: with the per-song redirects gone, open_hook serves stock BeatmapLevelsData for the other 46 slots while the PATCHED PACK bundles advertise preview sets for customs → selecting a song whose mode data paths don't resolve = crash. NOT a QA miss: the release QA never exercised single-song-deploy-onto-existing-loadout with a diverged local file. Not the webapp either (all its reads are GETs) — the webapp's wizard wrote a config whose empty mass_deploy.slots shaped the failure, but the pipeline's generate+deploy path is the actual defect site.

### Restore (live, verified)
redirects.json.bak (validator's own backup, Sep 28: 47 songs/5 packs/1 catalog) → preflight: every one of the 53 redirect targets still on PS4 (bundles never deleted) → pushed restored file → read back: 47 songs live. Pack bundles verified FULL-PACK builds (manifest patched_slots = every song per pack — the 10:34 deploy built full packs, so all modes intact for all songs). --verify-ps4: 53 redirects match, all targets present, sizes OK after refreshing 2 stale local caches (messitup rebuilt today; oxytocin QA-era) — **validation PASSED, all green**.

During cache refresh my pull script hit KB pitfall #2 exactly (get -o refuses clobber → second file got the first file's bytes) — caught by md5 check immediately, re-pulled correctly. The KB pitfall list pays for itself again.

### Pipeline v0.5352 fixes (7 regression tests, tests/test_exp246_redirect_wipe.py)
1. GENERATE+DEPLOY now REBASES on the live PS4 state (stale local detected → live base, local resynced; PS4 unreachable + local exists → HARD ABORT; genuinely-fresh clean slate still works; local-only generate stays offline).
2. Scope-expansion read failure → HARD ABORT (both the download and the parse paths).
3. _ensure_mass_song_redirects NEVER deletes out-of-scope song redirects (preserves with warning; removal is exclusively --clear-target-song / clean-slate).
All 753 tests green including 7 new pins reproducing the exact live scenario (local=1, PS4=47 → deploy → 47 preserved + 1 new).

### Exp 247 tabs (webapp 0.3.0)
Feature Flags (live read, descriptions, diff-only apply via --features-only, blind-apply refused, kill-switch hard confirm) + Backup/Restore (thin layer over backup script: list/backup/--clean-ps4/restore with sanitized names + 409 single-job + cancel) + Feature Request (prefilled GitHub issue URL, client-side, Pages-capable). Runner: start_script() unified _spawn; pending_flags hint.
**Live-smoke catch #1:** flag-key mismatch — adapter had singular `enable_custom_song_replacement`, wire format is PLURAL `enable_custom_song_replacements` (pipeline DEFAULT_FEATURES). Fixed everywhere; the page had been showing the flag default-OFF when the console had it ON.
**Live-smoke catch #2 (boot-time):** first fix attempt popped an already-renamed dict key → server KeyError at import; caught by booting before hand-off.
**Live PS4 finding + fix:** the console had custom_song_replacements + song_metadata_modification OFF (release-validation flag round-trip leftovers) — re-enabled both via the pipeline; all four flags now ON (verified via the webapp read).
**Test-bug lesson:** pytest.raises(HTTPException) around TestClient.post can NEVER fire (FastAPI converts HTTPExceptions to responses) — assert the 409 response. Chased my tail through 4 debug files before realizing the "pollution" theory was wrong; the minimal repro passed because it asserted on the response.

### Files (cycle)
tools/full_custom_song_pipeline.py (v0.5352: rebase + abort + no-sweep), VERSION, CHANGELOG-PIPELINE.md, tests/test_exp246_redirect_wipe.py (new), webapp/{server.py, adapters/ps4.py, adapters/runner.py, static/index.html, static/app.js, static/style.css, VERSION 0.3.0, CHANGELOG-WEBAPP.md}, tests/test_webapp_tools.py (new), tests/test_webapp_deploy.py (regex), tests/test_webapp_ps4_adapter.py (plural), README.md, experiment log Exps 246-247, this transcript, context.yml, roadmap.

### PS4 state NOW (user can play immediately)
47 song redirects live, 5 full-pack mode bundles + catalog, all four feature flags ON, --verify-ps4 fully green. Loadout tab will show 47 served / 0 stale.

---

## Cycle 6 — RCA #2: "2/3 features" + vanished metadata (Exp 248); flags pull-before-push; test-suite PS4 fence; Pages guidance

### User
> "ok, i lost your github pages instructions, I went to the github page for this repo and enabled for github pages: 'Deploy from a branch' 'main' and '/docs' - is this the intended setup? Or did we set up github actions pages? I haven't used those before. Is that more appropriate for what we're doing here? How can we test it before merging to main? Tested on the PS4 to validate your claims, on startup the notification said 2/3 features enabled instead of 3/3 features enabled so something is going on there. Then in the song list, none of the custom song metadata is showing, but all the custom songs are still there and the beatmap mode selectors are still enabled and the nonstandard beatmap modes still work. So the song metadata is broken from the most recent work. I have not manually deployed anything else from the webapp yet, I want my PS4 to be in the known good stable state before proceeding. Please perform another RCA..."

### RCA (conclusive — my own test suite mutated the user's PS4)
Symptoms = enable_song_metadata_modification OFF in-game. Evidence chain:
- Local + HEAD-committed features.json: `enable_song_metadata_modification: false` — but the Exp 246 restore had set it TRUE on the PS4 (20:13 log).
- The pipeline's `apply_feature_flags` (`--features-only --set-feature`) based its write on the LOCAL features.json (stale from release-validation round-trips) and pushed it wholesale — the Exp 246 pull-before-push violation, on the FLAGS path (I fixed redirects but missed that features.json was the same class).
- The AMPLIFIER: my `test_flags_apply_diffs_only_changes` webapp endpoint test mocked the live READ but NOT the runner → started a REAL pipeline `--features-only` subprocess → pushed the stale local file over the live console. And I then STAGED the poisoned features.json in the Exp 247 commit batch.
- Not a QA miss; not the webapp's design. My own tests violated my documented "no test touches the real PS4" rule.

### Restore (live)
--set-feature enable_song_metadata_modification=true via the fixed path → live+local all four ON; --verify-ps4 PASSED (53 redirects/packs/catalog green). User expects 3/3 toast + metadata back on next boot.

### Fixes (pipeline v0.5353 + webapp 0.3.1)
1. `_download_features_from_ps4` (mktemp -d, raw_decode banner-proof, ABORT on read-fail, absent=clean-slate, Exp 221 materialization) + `apply_feature_flags` rewrite: parse diffs first → pull live → materialize defaults → apply ONLY diffs → resync local → deploy. Bad syntax aborts pre-I/O.
2. ALL webapp job-starting tests mock the runner (FakeJob records argv — asserted; better coverage). conftest.py: suite-wide lftp-UPLOAD blocker (put/mirror -R → AssertionError).
3. Caught ANOTHER Exp-240-class banner bug in my own new helper (first-{ to last-} breaks on '}156 bytes' trailing banners) — fixed with raw_decode scanning; third instance this month.

### Tests
9 new (test_exp248_flags_pull_before_push.py: live-base-not-stale-local [the exact scenario], diff-on-live, read-fail-aborts, clean-slate-defaults [fixed wrong expectation — DEFAULT_FEATURES has metadata ON], Exp 221 merge, bad-syntax-pre-IO, transport banner/absent/fail). Suite 763/763. tools-test debug detours: (a) pytest.raises(HTTPException) can't fire through TestClient (relearned); (b) lftp -o target lives INSIDE the single -e token (argv parse in fakes must split the -e string); (c) _ftp_quote wraps -o targets in literal quotes — strip in fakes.

### GitHub Pages answer (delivered in-response)
- User's current setting (branch: main /docs) = "legacy" build_type per gh api — would publish docs/developer-info.md and CONFLICT with pages.yml.
- Directed: Settings → Pages → Source: "GitHub Actions" (one dropdown change). Our pages.yml builds (build_pages.py stamps data-mode="pages" + banner), smoke-tests, deploys on push to main; workflow_dispatch allows manual runs.
- Pre-merge testing: (1) local preview — built + served on :8877, verified (data-mode=pages marker, all assets 200); (2) temporarily point pages.yml's push trigger at the feature branch + run from Actions tab (offered to stage that change on request).

### Files
tools/full_custom_song_pipeline.py (v0.5353), VERSION, CHANGELOG-PIPELINE.md, tests/test_exp248_flags_pull_before_push.py (NEW), tests/test_webapp_tools.py (mocked-runner rewrite), tests/conftest.py (lftp-upload blocker), webapp/VERSION 0.3.1, webapp/CHANGELOG-WEBAPP.md, experiment log Exp 248, this transcript, context.yml, roadmap, project_summary.

---

## Cycle 7 — Backup-folder browse + feature-flag independence audit (Exp 249)

### User
> "Can we add a browse button with path display for where the backup tab is finding backups to restore? Right now it seems hardcoded. I tested by deploying a fresh custom with the web interface over mess it up and I performed the spot check of another custom song in another music pack, and I also tested the new Mess it up custom song and that worked too. I have not tested any of the other steps yet, so please reiterate them to me in your next message... I also would like for you to perform a thorough audit of each feature flag, its usages, and independence from the other flags; each flag should be entirely independent of the other flags (except the global enable, of course). I don't want disabling a flag to cause a crash or other issues."

### Hardware validation received
User's webapp deploy of Sandstorm→MessItUp: clean (log showed the 46-preserve lines + 53-redirect match — the v0.5352 anti-wipe fix proven on hardware); cross-pack spot check + the new custom both play. The restored-slot metadata residue (Sandstorm label over the old custom) explained last cycle; the redeploy resolved it.

### Built (webapp 0.4.0)
- webapp_state.py: per-machine settings (gitignored) — backup_dir.
- /api/backup/dir GET/POST + /api/backup/browse (server-side folder browser, dirs only, parent navigation); backup jobs pass `--out` when folder ≠ default (backup script gained --out; restore already took absolute paths). UI: path display, Browse… panel, manual entry, use-default.
- Debug detours: the Edit tool reported ENOENT on the backup script (transient — file existed; re-Read fixed); the --out flag argument turned out to already exist in the parser (added out-of-band) but was UNWIRED at runtime — I added the args.out override + `global LOCAL_BACKUP_DIR` in main().
- 4 old tests migrated off the removed BACKUP_DIR constant; 7 new tests incl. --out-in-argv vs no-flag-at-default.

### THE FLAG AUDIT (the cycle's main deliverable)
Every g_feature_* site in plugin v0.8047 traced; all 16 combinations evaluated. Verdict:
- **Crash-safety independence holds in ALL 16 combinations.** Proof: replacements ⊥ metadata (zero shared state); metadata ⊥ mode-mapping (zero shared sites); missing files safe everywhere (count-guarded, null-checked, logged); toast is diagnostic only.
- **One designed coupling (documented, not a defect):** mode-mapping gates INSIDE the replacements loop (Exp 222 + the Exp 180 CRC invariant) — replacements OFF makes mode-mapping unobservable. It's a modifier of the redirect stream.
- **One cosmetic hazard:** metadata OFF mid-session leaves stale swapped strings on already-built list cells (move_next mutates BeatmapLevel in-place) until list re-entry. Self-healing; no crash path. Mitigation: explanatory note in the Flags tab (chose UI note over plugin string-restoration — more state = more risk).
- KB page: .agent/llm-wiki-knowledge-base/feature-flag-independence-audit.md (indexed after feature-flags).

### Suite
770/770. Lint clean. webapp 0.4.0 (CHANGELOG-WEBAPP.md). Pipeline/plugin untouched this cycle (no version bumps there — the backup script's --out is not the pipeline).

### Re-iterated test procedure (Phases 0-6) delivered in the response with expected outcomes per phase.

---

## Cycle 8 — Pages diagnosis + CI lint recovery + live job feedback UI (Exp 250)

### User
> "I don't see how to test deploy the github pages, there is no matching controls for what you describe. Does this just build and deploy when I push these changes to the PR? I see a pages-build-deployment workflow that was run yesterday... and it says it deployed but my URL brings up a 404... I went through the test procedure phases 0 through 6, and I notice the backup process has no visual feedback... Can we throw up a loading spinner...? It would be best if we could also see the terminal output on the page. And for the feature flag page, the example notification text... does not update with the feature flag count... there should also be a simulated PS4 notification... Phase 6 shows another part of the interface with insufficient feedback during work... everywhere possible wherever we are launching a command, I want the user to be able to view the console output live."

### Phases 0-6: COMPLETE on hardware (user-verified). The webapp's core flows are now all live-proven.

### Pages: the full answer (evidence: gh api pages → build_type=workflow)
- Config correct (Actions source). Our pages.yml exists ONLY on the feature branch → GitHub hasn't registered it (workflows register from the default branch) → no Run-workflow button, no runs. It deploys automatically at PR merge; afterwards the manual button exists for branch-testing.
- The user's found run = the LEGACY /docs deploy from main (published developer-info.md only → root 404). Harmless history; replaced at merge.

### CI lint recovery (the actual merge blocker)
The PR's lint job failed: Exp 245 widened lint scope to tests/ which had ~180 never-linted findings. Fixed 179→0: 144 auto + hand-fixes (one-liners, unused locals, whitespace). TWO REAL BUGS: quick_validation.py corrupted (identifier + literal-\n — never parsed); hevag test asserted a typo'd var (NameError exactly on failure). Detour: my bulk splitter used stale line numbers and broke indentation in two files — ruff caught it, hand-repaired. Suite 770/770; lint clean everywhere.

### Live job feedback (webapp 0.4.1) — the user's UX principle: "everywhere we launch a command, live console"
- Shared job-panel: spinner + Working→✅/❌ + exact command + live console. Wired: Backup (btn disables + relabels), Restore, Clear (Manage + Loadout pages), Apply (Flags spinner). Deploy already streamed.
- Simulated PS4 boot toast (Flags): exact plugin format, recomputes live per toggle; contextual note per kill-switch state.
- Live-validated: real backup via endpoint — 30 lines streamed, exit 0, zip created.

### Files
webapp/static/{index.html, app.js, style.css} (panels, toast, spinner), webapp/VERSION 0.4.1, CHANGELOG-WEBAPP.md, tests/ (lint recovery: ~20 files touched — auto-fixes + 2 real bug repairs), experiment log Exp 250, this transcript, context.yml, project_summary.

---

## Cycle 9 — Version badge + the Pages-bundle asset bug (Exp 251)

### User
> "Can we have the web app display all version numbers in the lower corner or something out of the way? I want to see the pipeline version, the plugin version, and the web app version. That way I can tell when your changes have taken effect. Because right now, I don't see the updated feature flags page showing any notification preview of any kind as I'm toggling flag checkboxes. Is this change being served?"

### The diagnosis (user's suspicion was exactly right)
The PAGES bundle never worked: build_pages.py copies assets to the bundle ROOT but index.html referenced /static/* → 404 on every asset → zero JS ran at the Pages URL (no toggles, no preview, no mode badge — the whole UI inert). The LOCAL backend serves /static/* correctly, so the flags toast DOES work there (needs a server restart to pick up new code + Ctrl+Shift+R for the JS cache).

### Fixes (webapp 0.4.2)
1. Builder rewrites the 3 asset refs root-relative.
2. pages.yml smoke-test: every href/src in the built index must resolve in-bundle; no /static/ remnants (the class-level blind spot that shipped the dead bundle — the old test checked markers, never asset resolution).
3. Version badge (lower-right, both modes): ping carries webapp+pipeline+plugin versions (VERSION files + #define parse; "bundled" in release zips without src/); Pages build BAKES the numbers (no backend). Print-hidden. Stale FastAPI(version="0.1.0") removed — VERSION file is the truth.
4. Tests +4 (ping versions, badge elements, pages-bundle asset resolution, baked versions). Suite 774/774. Live-verified both paths.

### Answer to "is this change being served?"
- Local backend: restart the server + hard-refresh (JS caching). The toast preview is in 0.4.1+, which you have committed — it works locally.
- The hosted Pages page: was inert for EVERYONE until this fix; goes live at PR merge.

---

## Cycle 10 — The missing .hidden rule + panel-ID mismatch (Exp 252, webapp 0.4.3)

### User
> "Full Loadout and Backup / Restore tabs now have a permanent 'working' section with a loading spinner, before I take any action. Then when I try the backup, I get a dialog error: Couldn't start the backup: Cannot set properties of null (setting 'textContent'). You might as well also add the loading spinner to the Deploy tab's working status... everywhere you have a loading spinner right now it shows at all times instead of only during work. Same with the deploy's Verify button, no feedback given on this either. Same on the PS4 state tab, could also use a loading spinner here."

### RCA (two bugs, both introduced by me in Exp 250)
1. Generic `hidden` class had NO CSS rule (only `.page.hidden` existed) → all three job panels (and every other non-page hidden element: cancel/verify buttons, browse panel, deploy log) rendered permanently. The panels' markup looked right; the CSS never had the utility.
2. Backup panel children hand-typed `backup-job-*` while showJobPanel derives `panelId + "-*"` → `backup-job-panel-status` null → textContent throw → user's dialog. Manage/Loadout used the convention correctly by luck.

### Fixes
- Standalone `.hidden { display:none; }` (commented trap note); Backup IDs aligned to the convention.
- NEW VERIFICATION DISCIPLINE: a static-audit script cross-checks every JS-referenced id (all panels × 5 children) against the served HTML — catches this class forever. Live serve check: panels carry hidden; backup E2E re-run green (30 lines, exit 0, zip).
- User asks added: Deploy progress row + button relabel; Verify button spinner+console (was silent); PS4 tab read spinner.

### Suite 774/774; lint clean. User needs Ctrl+Shift+R (JS+CSS changed).

## Cycle 10b — The hidden-attribute specificity trap (Exp 252b, webapp 0.4.4)
User: deploy page still shows the spinner row on load + it persists after a deploy. RCA: the row used the hidden ATTRIBUTE; `.row{display:flex}` (author CSS) overrides the UA attribute default — yesterday's .hidden-CLASS fix didn't apply. Fix: `[hidden]{display:none !important}` + row carries class AND attribute + toggles both. Sweep: only element in the trap. Live-verified. Suite 774/774.

## Cycle 11 — Clear-flow UX + the Stale-after-clear RCA (Exp 253, webapp 0.4.5 + pipeline v0.5354)
User: (1) clear's spinner/output below the table, invisible — put at top + jump there; same on all long pages; (2) clear must refresh on completion; (3) why does clearing show "Stale" instead of "Stock"?

RCA for (3): the loadout was CORRECT — the PS4 held both MessItUp_v3.bundle (webapp casing) and messitup_v3.bundle (script casing); the pipeline's clear rm'd only the literal-cased one. Pipeline v0.5354: clear LISTs the AFR dir and removes every case-insensitive match of <slot><suffix>; 2 regression tests. The UI's three-signal model did exactly its job — it surfaced a real state discrepancy the CLI had been silently leaving behind.

(1)+(2): panels moved above the tables (Manage + Loadout) with window.scrollTo(0) + scrollIntoView(start) on job launch; Deploy progress row scrolls into view; runJobWithPanel now returns a completion promise so clear's refreshFn fires at job END (was fire-and-forget — refresh raced mid-job). Suite 776/776.

## Cycle 12 — The Batch tab (Exp 254, webapp 0.5.0)
User: v0.4.5 hardware-confirmed working. Request: Batch tab integrating the example_*.sh packs (dropdown → song table), custom batch builder (BeatSaver search + IDs), save/load, documented text-file format, platform-agnostic (Win/Mac/Linux).

Built: adapters/batch.py (live regex parse of the 34 scripts — 296 entries, map IDs + slots + name/artist from the # Song comments; custom bsd-batch v1 JSON format with validation + unknown-field roundtrip; filename jail), batch_runner.py (serial driver, stop-at-first-failure = the && semantics, one single-job-runner job), server endpoints (examples + CRUD + batch job with validate-everything-first), full UI (dropdown/table/add-card/search/save/export/import/delete/deploy via the job panel). Batches dir gitignored (user data). 13 tests; suite 789/789; live roundtrip smoked.

Design notes: the scripts stay the single source of truth (parsed, not duplicated); export/import via browser file APIs = the platform-agnostic path (works in Pages mode too — building batches needs no backend; deploying does, like everything else).

## Cycle 13 — Multi-pack batch mode (Exp 255, webapp 0.5.1)
User: single-batch tested + working. Request: checkbox selection of multiple pre-defined packs → one large deploy (their standard 5-pack loadout). Built: new Batch-tab section — 34-pack checkbox list (counts + slot ranges), select all/none, live N-packs/M-songs counter, deploy-order tooltip, Deploy Selected Music Packs → merged-in-pack-order /api/jobs/batch → serial runner with stop-at-first-failure. Their 5-pack loadout = 50 songs. 2 tests (merge integrity + count parity with the scripts). Suite 791/791.

## Cycle 14 — The 50-vs-47 audit + BE duplicate removal (Exp 256, webapp 0.5.2)
User: why 50 in the app vs 47 on the PS4 after the same 5 scripts? "Please audit and figure out what is going on here."

AUDIT: BE script + .md carried 3 LIZZO-pack songs (2BeLoved/AboutDamnTime/CuzILoveYou — same map IDs the Lizzo script deploys onto those same Lizzo slots). 50 lines / 47 unique; dupes overwrite identically → 47 live. (My audit detour: two one-off analysis scripts had their own bugs — lowercased-key lookup + a collapsed dict — briefly showing camellia live=0; caught and fixed before concluding.)

USER DECISION: remove the duplicates from the BE script entirely (they don't belong there); Lizzo keeps them.

EXECUTED: BE .sh — 3 blocks removed, songs renumbered (11→8, 12→9, 13→10), "All 13" footer → 10 (header already said 10 — itself evidence the 3 were accidental). BE .md — 3 sections removed, renumbered, both count references fixed. Verified: BE = 10 live lines, all genuine BE slots; parser total = 47; FINAL PARITY PROOF: scripts' unique slots == live 47, zero diff both directions. Suite 791/791.

## Cycle 15 — FINAL pre-merge audit + PR description (Exp 257)
User: "perform one final audit of the new web app interface, the CI, release process, release contents, release notes, documentation, knowledge base, etc... Include the PR description, we need to update that and do NOT lose my screenshots — follow the prompt file and only push once I approve. This will be last in your task list."

AUDIT FINDINGS + FIXES (4 tasks, done in order):
1. Webapp: lint clean, 41 routes, all 11 tabs, versions coherent (0.5.2/0.5354/v0.8047 across badge+toast+files), Pages bundle passes every smoke check; pages.yml's JS assertion tightened (checked literal "data-mode" but the builder stamps dataset.mode — the or-clause covered it, now proof-proof). One false alarm during audit: my grep for 'data-mode' in the BUILT js — the injected check uses dataset.mode; verified the workflow's real assertion passes.
2. CI/release: both workflows lint tools/+webapp/+tests/ + run the suite w/ requirements-test (fastapi/uvicorn/httpx); release job webapp-boot smoke + zip bundles webapp/ incl. batch_runner + build_pages (batches/ gitignored). CI_RELEASE.md webapp table REWRITTEN for 11 tabs (was pre-Batch/Flags/Backup/Request).
3. Docs: README version banner stale 0.5351 → v0.8047/0.5354/webapp 0.5.2; README webapp list gained the Batch tab entry; release-day checklist gained the webapp smoke test step (the plan §9.5 DoD item); context.yml top-level pipeline_version 0.5351→0.5354; roadmap M9 header → FEATURE COMPLETE. KB: 56 pages current; flag-audit + lftp-pitfalls accurate.
4. PR description (prompt file followed to the letter): PR #5 found; current body downloaded (43 lines — still the Exp-242 PLANNING description with 12 screenshots + stale narrative); updated copy: screenshots preserved VERBATIM (all 12, order intact), new body = shipped-milestone summary (versions, 11 tabs, architecture, the v0.5352-5354 state-safety fixes, 791-test validation, 47-parity) + the planning-notes footer kept for context; diff generated (.pr_temp/). NOT PUSHED — awaiting explicit approval per the user's instruction and the Danger Mode rules.

Suite 791/791 final; lint clean. All audit changes staged (14 files).

## Cycle 15b — PR description PUSHED (approved)
User: "approved". Pushed via the established raw-field PATCH (gh api pulls/5 --method PATCH --raw-field). Post-push verification: body byte-identical to the approved draft (pushed == intended: True); all 12 screenshots intact in order; the 11-tabs + architecture + validation sections live. One honesty note: the version-banner sentence ("Plugin v0.8047 · Pipeline v0.5354 · Web app 0.5.2") that appeared in my audit summary was from the FIRST (failed) edit attempt; the final python-built draft — the one in the diff the user approved — begins at "## What's in it (11 tabs)" and carries the versions only in the v0.5352-54 section + validation section. Offered a one-line PATCH to add the banner; no action without the user's say-so.

## Cycle 16 — alpha01 release audit (Exp 258, webapp 0.5.3)
User: created + pushed test tag v0.8047-pipeline-0.5354-webapp-0.5.2-alpha01; audit on GitHub + download/audit assets + validate the webapp runs FROM the release + everything possible pre-merge (to test live Pages).

GitHub side: tag build + release jobs success; PR CI green; asset 962KB; notes current.
Zip: 157 entries — plugins (FSELF + v0.8047 strings), both VERSIONs, complete webapp/, 69 example files (BE fixed at 10), validation docs, README banner current.
Live from the extracted zip: ping versions correct (plugin="bundled" — right for a release), assets 200, catalog 36, command-preview exact, release pipeline runs.

THE FINDING: Batch tab EMPTY from the release — parser looked only at .agent/docs/; the zip ships scripts at docs/example-scripts/. Fixed 0.5.3: parse both layouts (3 paths), first-match wins. PROVEN from the actual extracted alpha01 zip: 34 packs / BE 10 / 5-pack = 47. 3 regression tests; suite 794/794; lint clean.

Recommendation: re-tag alpha02 with the fix for a fully-clean consumer artifact before merge.

## Cycle 17 — Example scripts → docs/example-scripts/ (Exp 259, webapp 0.5.4)
User: "perhaps it makes sense to move those example scripts and docs over to the docs/example-scripts folder so that the release structure is the same. Maybe they don't belong in .agent at all... update all references... Update our knowledge base as well. Then I will cut a new alpha02."

Moved the 69 files; zip layout unchanged (byte-identical structure). Updated: plugin-build.yml packaging source, batch.py EXAMPLE_DIRS (canonical=docs/example-scripts, legacy .agent/docs still parsed), README ×3, plan doc, 3 test fixtures, changelog notes (history preserved), KB (pipeline-single-song-deploy ref + development-workflow location section). Verified: parser 34/BE-10/5-pack-47 from the new location; bash -n on moved scripts; Pages bundle smoke; lint clean; suite 794/794; zero stale refs repo-wide (outside preserved history). webapp 0.5.4.

## Cycle 17b — CI red: absolute paths in the new tests (Exp 259b)
User spotted run 37406290094 red. RCA: my Exp 259 release-layout tests hardcoded /workspace/docs/example-scripts/ as the copy source — passes in the devcontainer, FileNotFoundError on CI runners. Fixed: derive via PROJECT.parent (test-file-relative). Swept all new tests for the class (only inert conftest fixture data remains). PROOF: ran the tests from a repo copy at /tmp/ci-sim (non-/workspace — the CI condition): 3/3 pass. Suite 794/794; lint clean.

## Cycle 18 — alpha02 validated + release-title fix (Exp 260)
User: alpha02 tagged for validation + release titles should match the tag exactly (GitHub's list pane truncates; the "Beat Saber Deluxe " prefix made them indistinguishable).

Title fix: workflow name: → ${{ github.ref_name }} (next releases); alpha02 renamed in place via the API (user-requested) — verified in the list pane.

alpha02 validation: CI green on the tag AND the PR (the 259b fix proven in real CI). Zip: 157 entries, versions 0.5354/0.5.4, 69 examples, FSELF plugins, fixed BE script. THE alpha01 BUG FIXED IN THE ARTIFACT: Batch parses 34 packs from inside the zip (BE=10, 5-pack=47). Live boot: ping correct (0.5.4/0.5354/bundled), all assets 200, current UI elements served, release pipeline runs. Pages bundle smoke: all assets resolve, versions baked. READY TO MERGE.

## Cycle 19 — Pages-mode expectation question → command-builder mode made real (Exp 261, webapp 0.5.5)
User: "will the Pages deployment actually run this for people without downloading... They just need the ps4_dump folder and the website will work?"

HONEST ANSWER: No — browsers can't read local folders / run Python / FTP to a PS4; static hosting. Hosted = plan/onboard; release's local backend = deploy. (This two-surface split was the plan's §2 design from the start.)

The question exposed pages mode was INCOMPLETE: no local-only tagging (backend buttons rendered+failed), the Deploy preview called a nonexistent backend endpoint. Built 0.5.5: local argv builder in the preview (1:1 with deploy.py), Deploy→"Copy deploy command" (clipboard+fallback), backend-only tabs hidden, and a builder-injection bug found by a headless-DOM consumer test (early return skipped the relabel — now the injection carries the full setup). Verified headlessly against the BUILT bundle: mode→hidden→relabel→exact command. Local-mode tests green. Suite 794/794.

## Cycle 20 — The Get Started guided funnel (Exp 262, webapp 0.6.0)
User: "the Pages deployed web app should guide the user through downloading the latest release, extracting it, and running THAT web-app... encapsulate and automate this process as much as possible... ultimate easy user friendly experience."

Built the Get Started tab (both modes): prerequisite checklist (interactive, with the Dump-Guide handoff), the releases/latest download button (permalink — never needs updating), per-OS extract instructions, tabbed per-OS run commands (pip + python webapp/server.py; the Windows python gotchas), and the wizard finale. The Pages bundle auto-lands hosted visitors there; the banner leads with the ~2-minute promise. Honest framing preserved: download/extract/two-commands are the irreducible browser-limited steps — everything around them is guided. Headless-DOM consumer test (realistic shim: load-time nav wiring) passes against the built bundle; local-mode regression green. Suite 794/794.

---

## Cycle 21 — Exp 263: webapp-0.6.0-alpha01 release validation (found + fixed a live redirect-case bug)

**User:** committed + tagged `v0.8047-pipeline-0.5354-webapp-0.6.0-alpha01`; asked for complete validation + updating the validation script/procedure for all new functionality/UI; noted I could recover context from commit messages if the compaction lost any. Mid-validation: "oops! I forgot to power on the PS4... I just did so and ensured the ftp server was up."

### What ran (chronological)
1. Release audit on GitHub: title==tag exact, workflow green, asset 966,405 B. Downloaded + extracted to /workspace/temp/alpha01-validation.
2. Static audit: VERSION 0.5354 + webapp/VERSION 0.6.0 (both match tag), 69 examples, FSELF binaries v0.8047, exp-246/248/253 fixes in the shipped pipeline, 12 tabs (startPage present), 37 routes, 7 local-only buttons. **Release-body gap found:** CI_RELEASE.md still said "11 tabs" → fixed (12, Get Started listed).
3. Webapp boots from the zip: ping carries all 3 versions; catalog/batch/examples/backup/feature-request/dumper.cfg 200. **34 packs parse from the release layout; 5-pack = 47.** (batch adapter works from inside the zip.)
4. PS4 OFF at first: `/api/loadout` HUNG ~3.5min before unreachable (dead-host retries); a bare lftp call measured **12:14 min**. Logged as finding; user then powered the PS4 on.
5. PS4 ON: loadout 0.9s — SERVED 47 / STALE 0 / STOCK 258, readStatus all-true. ps4/state: 53 redirects, 47 songs, 5 packs, catalog true, all 4 flags ON. verify-ps4 PASSED (after pulling both state files; the no-local-file mismatch is expected pre-pull).
6. Build-only quality: 36,706,075 B bundle; NoArrows 5/5 all-dots, OneSiber 5/5 blue-dots.
7. **--deploy-full FAILED its own post-deploy check: `Redirect targets missing on PS4: ['messitup_v3.bundle']`.** RCA chain (fully traced in-session):
   - I had NOT localized ps4_config.json before the deploy (skipped validator step 3 — my own mistake, but it exposed the pipeline's failure mode).
   - No config → pipeline fell back to built-in defaults: devcontainer-absolute paths AND a `mass_deploy.slots` list with lowercase Rolling Stones spellings.
   - `_ensure_mass_song_redirects` "healed" redirect VALUES from `mass_deploy.slots` casing → 11 live mixed-case values lowercased (`MessItUp_v3.bundle` → `messitup_v3.bundle`), pushed to the PS4.
   - Out-of-scope slots are NOT re-uploaded by single-song deploys → files on disk kept mixed-case names → values dangled (5+ of 11; PS4 carried silent case-duplicates since Exp 253: both `Angry_v3.bundle` and `angry_v3.bundle` existed).
   - The release's own post-deploy check #3 (exact-case target existence) caught it and correctly refused to pass. **The validation did exactly what it exists to do.**
   - Reproduced deterministically: pre-validation backup + pure-default config + deploy scope → the same 11 diffs.
8. **Fix (pipeline v0.5355):** `_ensure_mass_song_redirects(…, remote_files=None)` — a value that already names a file present on the PS4 is NEVER rewritten; a dangling value heals toward the ON-DISK case variant; `manage_redirect_config` fetches the live AFR listing on every deploy. 7 regression tests (`tests/test_exp263_redirect_case_healing.py`). **My own wiring test leaked** (manage_redirect_config's local-resync overwrote the working-copy redirects.json with the fixture — the env-dependent pack-mode tests caught it); hermeticized via `_get_redirect_config_path` monkeypatch; working copy restored from the pre-validation backup. Suite **801/801**; lint clean.
9. **Webapp fix (0.6.1):** `_run_lftp` now sets `net:timeout 5 / max-retries 1 / connect-timeout 5`; `fetch_remote_json` stops retrying on connectivity refusals (retries stay for transfer flakes). Proven against the dead PS4: dead read **1.19s** (was ~3.5min via the endpoint / 12:14min bare). Suite 801/801 again.
10. Validator + procedure updated (both files): default TAG → new release; **version expectations DERIVED from the tag** (sed extraction; no manual bumps); new automated step 4/9 webapp smoke (boots shipped server: ping versions, Get Started, 34 packs, 5-pack=47, live-truth loadout); step-order enforcement (localize BEFORE any pipeline run, with the Exp 263 story inline); findings 4 (the case-healing bug) + 5 (dead-PS4 timeouts) added; expected-results table rewritten for this run; release-day checklist documents tag==title.
11. README banner → Pipeline 0.5355 | Web app 0.6.1 (was stale at 0.5.2).

### PS4 state at session end (⚠️ pending)
- The 15:48 deploy pushed the 11 rewritten values to the console. Pre-validation backup (`redirects.pre-validation.bak`, 53 entries, healthy mixed-case values) is safe locally. Metadata untouched (47 names live).
- **The PS4's FTP went unreachable ~16:20 mid-validation** (GoldHEN FTPD typically drops after heavy transfer sessions — the deploy pushed ~200MB of pack bundles). Monitor armed (bd3s6jkyk) to auto-detect its return; restore = one `put` of the backup + re-verify. Do NOT boot the game before the restore (the dangling `messitup_v3.bundle` value = MessItUp won't load; 5 slots affected; everything else healthy).

### Verdict on alpha01
NOT shippable as-is: its pipeline 0.5354 carries the case-healing bug. Recommend: commit 0.5355 + webapp 0.6.1, then alpha02 (or fold into the merge). The release's OWN safety net (post-deploy validation) is what caught it — the exact system working as designed.

### Cycle 21b — PS4 restored, fix proven live, hardware validations completed (Exp 263b)

**User:** "the ps4 is back on, i shut it off when I left, did not realize you were still working."

Mystery solved — not an FTPD crash, just the console powered off. Stopped both watchers, then:

1. **Restore:** verified the backup healthy (53 entries, MessItUp→MessItUp_v3.bundle), pushed it via `lftp put`, read back **byte-identical** (sha256). Exact-case check: all 53 targets resolve in the live AFR listing. (My first verification attempt tripped on lftp `cls -l` printing 8 fields with full-path-at-index-7 on this link vs the pipeline's 9-field `ls` parse — my check's bug, noted in the KB transcript. Also `put` returned rc=1 while succeeding — pitfall 3 again: always verify by read-back.)
2. **Fix proof (decisive):** fresh release extraction + localized config + live state pulled; swapped the FIXED pipeline in; ran the exact breaking scenario (single-song deploy-full). Result: 46 existing songs preserved, **zero redirect-value diffs vs pre-validation**, post-deploy validation PASSED, live read-back shows mixed-case values intact.
3. **Remaining hardware steps all green:** flags round-trip + kill-switch both directions + all-ON restore (each verified by reading the PS4 back), metadata-only (redirects untouched, 47→47 names), clear-target surgical (46 songs, 5 packs, zero case-variant bundles left — Exp 253's fix verified live) + re-deploy restore (47, all other values verbatim), sync-config, enforce identity, target-ip.
4. **Final integrity:** LIVE == pre-validation on every axis (53/47/5/catalog, 47 names, all 4 flags ON, zero value drift). Console fully healthy for game boot.

**Verdict:** alpha01 fully validated; its one found defect is fixed (0.5355) + proven live + pinned by 7 tests. Recommend alpha02 carrying pipeline 0.5355 + webapp 0.6.1.

---

## Cycle 22 — Exp 264: the user's batch failure RCA'd + fixed; PS4 cleaned; Pages question answered (Oct 7)

**User:** PS4 "in the state I expect" after game-boot test; multi-pack batch deploy (Britney + Rolling Stones) failed at song 1/22 (full log pasted); asked how the web app knows it's on Pages + lands on Get Started; asked to clean up PS4 duplicates.

### The three separate threads, untangled
1. **"Missing" MessItUp — NOT a bug:** live state had 52 redirects/46 songs (no MessItUp; bundle+metadata gone in every casing = the `--clear-target-song` signature). Forensics: `song_metadata.json` mtime 20:38:03 vs batch start 20:40:53 → the USER cleared MessItUp via Manage Songs two minutes before the batch (their own valid test; Exp 253's case-variant clear working).
2. **The batch failure — REAL bug (pipeline 0.5356):** post-deploy check 6 compared EVERY redirect target's local artifact vs live. Oxytocin (not in the batch) had a stale repo-local bundle (release-tools build, 36,706,086) vs the live copy (repo-tools build, 36,706,075) — 11 bytes of pipeline-version drift, charts hash-identical. Fix: **session upload ledger** (`_SESSION_UPLOADED_BUNDLES`) — deploy_to_ps4 + _deploy_file_to_ps4 record uploads; size check hard-fails only session uploads (its actual purpose), out-of-scope mismatches become an `ℹ️` informational note; standalone --verify-ps4 (empty ledger) keeps full checking. 6 regression tests; proven live (same deploy → PASSED with the informational note).
3. **Second bug found proving the first (webapp 0.6.2):** batch parser `\S+` captured literal shell quotes — `--target "Scream&Shout"` parsed WITH quotes → song 8 would have failed even after fix #2. `_unquote()` strips them; 34 packs re-verified clean.

### PS4 cleanup (user-requested)
10 unreferenced case-duplicate bundles (Sep-27 lowercase RS-era): each verified to have exactly one referenced mixed-case twin, then deleted. Post-cleanup: **56 files, zero unreferenced non-state, zero missing targets**. Refreshed the stale repo-local Oxytocin artifact → standalone verify fully PASSED.

### My testing mistake (corrected immediately)
Proving the size fix I deployed map 15f52 (All Eyes On Me) instead of the pack's 6d63 (Take on Me) into BabyOneMoreTime — caught via the log's `_levelID` line, redeployed the correct map; slot verified "Take on Me / a-ha".

### Pages-mode mechanics (the user's question, answered in-reply)
build_pages.py stamps `data-mode="pages"` on `<html>` at BUILD time → the Pages branch of detectMode() (injected by the builder) sees `document.documentElement.dataset.mode === 'pages'` IMMEDIATELY (no ping wait), sets the ◐ badge, hides the 7 `.local-only` nav buttons, relabels Deploy → "Copy deploy command", and clicks the Get Started nav button → `showPage('startPage')`. The local backend has no marker → detectMode pings /api/ping → "local-backend" mode, all tabs shown, lands on wizard as before.

### End-to-end proof (running in background)
The user's exact 22-song batch re-run with all fixes: webapp-parser argv (unquoted), batch_runner serial semantics, pipeline 0.5356.

### Cycle 22b — Exp 264b: the exact 22-song batch — 22/22 PASSED (Oct 7, ~22:07)
The end-to-end proof completed: "✅ Batch complete: 22/22 songs deployed." Every song's post-deploy validation PASSED (22 in the log). All three fixes held: no size-check false positive all batch long (stale Oxytocin artifact present but informational), Scream&Shout deployed clean (unquote fix), all 41 mixed-case values preserved (Exp 263 guard). Song 18 restored MessItUp (Powersnake / Brothers of Metal) → console back to 47 songs — flagged to the user (pack-list semantics; re-clear if wanted). One non-blocking wart: song 18's single-file upload verification flaked (`UNVERIFIED`) while the bundle DID land — check #3 confirmed present, validation PASSED; hardening candidate noted (retry the single-file listing). Final state fully verified: 53/47/5/catalog, 47 names, 57 AFR files with ZERO unreferenced junk, standalone deep-audit verify PASSED. Stage set for the user's commit.

---

## Cycle 23 — Exp 265: alpha01 0.5356/0.6.2 validated + the Pages answer re-delivered (Oct 8)

**User:** hardware-confirmed the batch fix; tagged `v0.8047-pipeline-0.5356-webapp-0.6.2-alpha01`; re-asked the Pages/Get Started question ("I didn't catch that" — my earlier answer was buried mid-report).

**Validation green:** both fixes SHIP in the zip (ledger + case guard + unquote parser); webapp boots with 0.6.2/0.5356, 34 packs, 5-pack=47, Get Started served; ordered setup (config-localize + state pull FIRST); live deploy PASSED from the shipped pipeline (bundled plugin); flag round-trip verified both directions; final integrity 53/47/5, 57 files, zero junk; standalone verify PASSED. Validator default TAG bumped.

**Pages mechanism (shown, not just told):** built the Pages bundle from the current UI and showed the user the two pieces — (1) `data-mode="pages"` baked on line 2 of the Pages index.html by build_pages.py (absent in the local UI), (2) the injected detectMode() branch: sees the marker instantly (no ping), sets ◐ badge, hides the 7 local-only buttons, relabels Deploy → "Copy deploy command", and CLICKS the Get Started nav button → showPage('startPage'). Local = no marker → ping /api/ping → full backend mode.

---

## Cycle 24 — Exp 266: LIVE Pages landing bug — RCA'd + fixed (webapp 0.6.3) (Oct 8, evening)

**Context:** PR #5 merged 21:02Z; Pages deployed green; final release tag v0.8047-pipeline-0.5356-webapp-0.6.2 built. **User (live report):** the hosted site starts on Setup Wizard instead of Get Started; "most of the tabs are missing"; pages-mode badge + version banner correct. Asked me to watch for the release tag (validated: green; already reported separately).

**RCA (from the live bundle):** all landing machinery present and correct (marker, injected branch, button) — the bug is a RACE: detectMode's pages branch clicks Get Started, then DOMContentLoaded's `showPage("wizard")` (unconditional, script tail, line 1544) fires after the script bottom and stomps the landing. Badge/banner/hiding aren't re-overwritten → they looked right; only the landing was wrong. Reproduced deterministically before fixing.

**"Missing tabs" — not a bug:** all 12 buttons ship; the 6 local-only (ps4Page, manage, loadout, flags, batch, backup) hide in pages mode BY DESIGN; the 6 visible (wizard, picker, deployPage, startPage, requestPage, guide) are the intended hosted surface. Explained to the user.

**Fix (webapp 0.6.3):** mode-aware landing — `if (state.mode !== "pages") showPage("wizard")` in the DOMContentLoaded tail. Pages bundle rebuilt + browser-order headless proof: lands on startPage; local regression lands on wizard. Suite 807/807, lint clean.

**Next:** user commits + pushes to main → Pages workflow redeploys → live re-verify: hosted visitors land on Get Started.
