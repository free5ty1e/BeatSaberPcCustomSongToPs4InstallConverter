# M13: Beat Sage + Local Song Folder Support — session transcript

Branch: `feature/m13-beat-sage-integration`. Plan: `.agent/plans/beat_sage_and_local_song_folder_support.md` (implementation-ready).
Milestone phases: M13.1 local-folder section → M13.2 Beat Sage Tier 2 → M13.3 Tier 1 research+impl → M13.4 docs.
Doctrine: the web app is a thin layer — every operation = one pipeline subprocess or a well-bounded adapter; the pipeline already accepts local folders via --song-dir; ZERO pipeline/plugin changes for the core.
Experiment numbers continue from the M12 log (last used: 282/281h) → first M13 experiment = 283.

## Cycle 1 — orientation + experiment-log rotation + codebase study

- Verified the branch: `feature/m13-beat-sage-integration` (clean tree, only pre-existing untracked dirs).
- Rotated the per-feature experiment log: M12 (dump-elimination, Exps 279-282) → archive; fresh M13 log opened.
- Studied the webapp adapter surface: webapp_state (per-machine persisted state — the staging-persistence model), deploy.py (argv builder — DeployOptions.validate currently requires map_id, the local-folder deploys arrive via --song-dir), paths.py (layout-agnostic resolution).

## Cycle 2 — Exp 283: the full M13 implementation + live verification

- Experiment log rotated (M12 → archive); M13 opens at Exp 283.
- Beat Sage API live-captured from the Nuxt bundle (chunk-map trick → page chunk → serverFetch routes + FormData + Vuex defaults). Tier 1 implementable — no auth/captcha.
- Built: adapters/songs.py + adapters/beatsage.py + beatsage_client.py + 5 server endpoints + deploy.py --song-dir + the two UI sections + staged list. 57 new tests; suite 924+93; ruff clean.
- quickjs found 2 REAL JS bugs (missing paren in a template literal + lexical redefinition) the Python suite couldn't see → permanent test_webapp_js_syntax.py gate added.
- LIVE proof: synthesized 48s original song → /api/jobs/beatsage → accepted → 12s → staged (V2, N/H/E/E+); survived restart; command preview emits --song-dir.
- Deploy to TruthHurts: bundle built beautifully (V2→V3, Easy auto-filled, 15 mode beatmaps) — FTP hit No route to host: the PS4 went to rest mid-flow; job failed cleanly. The staged song persists — one click re-runs it when the console is back.

## Cycle 2 wrap-up

- Final: 926 passed + 94 gated (the 94th = the BEATSAGE_LIVE contract test, skipped in CI by design); ruff clean; the release-doc invariant now glob-ships docs/features (the release test updated to pin the glob).
- The app is LIVE at http://127.0.0.1:8765 (0.6.20) with "BSD Deluxe Theme (An Original)" sitting in the Staged list — the user can browse the two new sections right now.
- The one remaining hardware validation: PS4 back on → one Deploy click (TruthHurts) → play.

## Cycle 3 — Exp 283b: the Lights trap + the hardware validation + the M14 roadmap request

- User's failed generation root-caused by live probes: the Lights event is a broken checkbox on beatsage.com's own site (400 in both v1+v2). Fixed (removed + validated + pinned); the user's Eve 6 song re-generated through the app in 57s and staged.
- The pending M13 hardware validation completed: BSD Deluxe Theme → TruthHurts deployed + validation PASSED. M13 feature-complete.
- Roadmap: M14 — Custom Song Environment Control written (the 4 modes + hypotheses E1-E4 + the blob-injection connection); album exploration renumbered M15.

## Cycle 4-5 — Exps 283c/283d: density research + stats/test-song surfaces; THE PREVIEW BUG

- User: sparse Hard report + "expose any controls"; loves stats; wants the theme song on demand; confirms they only ever used the web UI (the two file-naming styles in one Beat Sage zip are their quirk).
- Live v1-vs-v2 density test: v1 only marginally denser; v2's E/N/H = ONE mellow band (real-song Hard 0.61 NPS). No density slider exists. KB: beatsage-charting-behavior.
- Shipped: v1/v2 selector + density note; per-difficulty notes/NPS/peak/bombs/walls/events + map facts + generation record on staged songs; sparse warnings; lazy stats upgrade of old entries; testsong.py (byte-identical to the deployed theme) + GET /api/songs/test-song + the 🧪 one-click button.
- THE PREVIEW BUG (user's field report): root-caused via the manifest's previews list — the pack/preview pass ran BEFORE the deploy's own song_metadata registration (Step 11, end of deploy) → build_preview_map skipped the new slot → every deploy baked the previous deploy's preview, never its own. Fixed (0.5366): early LOCAL registration before the pack pass; Step 11 keeps the upload. Live-validated: the re-deploy cut ✂️ MessItUp (preserved) AND StartMeUp (new) — validation PASSED, console repaired.
- Two 47-loadout-era test pins made state-dynamic (patched==9/start==0.0/4-sets broke with the clean-slate state). Suite: 948 + 87 gated.

## Cycle 6 — Exp 283e: the button UX + the boot-wiring gate + the clean slate

- The user's two button reports addressed: label fixed (no console claim); the click now visibly does something (button disables + relabels through the flow); the stale-page class killed at the server (index.html → Cache-Control: no-store).
- The NEW boot-wiring test: executes the DOMContentLoaded wiring under a quickjs DOM shim — the only gate for "page renders, clicks dead". Debugging it exposed the repr-string-literal trap (the first version executed nothing) + a shim gap; both fixed. 3 tests green.
- Console to true clean slate per the user's authorization: session log archived (2,385 lines), backup saved (bsd_backup_20261023_220344.zip), clean-ps4 + local wipe verified (AFR empty, plugins.ini absent, app reads clean_slate=True). The user's fresh run covers the whole path incl. the preview-order fix.

## Cycle 7 — Exp 284: the release audit + M15 roadmapped + alpha01

- The user validated the full fresh flow themselves on the clean console; Expert+ = "decently dense"; requested the lower-difficulty engine on the roadmap.
- M15 — Lower-Difficulty Generation Engine written (official-difficulty-grammar research-first; the dump's catalog as the measurement corpus; the album → M16).
- alpha01: CI green (1038→914+124); the zip audit: FSELF pair, 7 docs, 7-flag template, byte parity (all 5 core files), the M13 files ship, the zip's app boots 0.6.20/0.5366/v0.8055.
- THE AUDIT FINDING: the changelogs — 4+ silent string-replace no-ops across the milestone left the webapp changelog disordered with 0.6.20 missing + the pipeline changelog missing 0.5366. Both fixed properly (full reorganization; entries written from session records). CI_RELEASE + the feature doc + the KB index brought current. Lesson: changelog inserts must assert their anchors.

## Cycle 8 — PR #10 updated

Title → "M13: Beat Sage + Local Song Folders — any audio → AI map → your PS4 (web app 0.6.20, pipeline 0.5366)". The full M13 release story: the surfaces table (Beat Sage/local songs/staged stats/test song), the live-capture + respect rules, the findings→fixes table (Lights trap, density band, the preview-order bug, the stale-page class, the changelog audit), the validation section (the live Tier-1 proof + the user's own clean-slate run + alpha01), and the M14/M15 roadmap pointers. **The user's screenshot preserved** (github user-attachments/95d319e7…, the Beat Sage section screenshot). Pushed via gh api PATCH (6,646 chars).

## Cycle 9 — Exp 284b: 🎉 THE M13 RELEASE — fully validated + Pages audited

The final tag built green (914+124; 51-route smoke test). The audit's centerpiece check: **THE FIXED CHANGELOGS SHIP** (v0.5366 + 0.6.20 heads, 41 ordered headers) — closing the silent-replace finding. Byte parity: all 8 files MATCH. The zip's app boots + every M13 endpoint works; the shipped client tells the Lights-trap story. Pages: rebuilt on merge; all three versions in the badge; the M13 sections render; the live app.js carries every M13 function + parses; the landing guard + no-dump message intact. **M13 SHIPPED — M0-M13 complete.**
