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
