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
