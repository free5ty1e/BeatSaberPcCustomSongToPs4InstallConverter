# Eliminating or Automating the ps4_dump Folder Requirement

**Status:** 🟢 Path A IMPLEMENTED (Exps 280-280b, 2026-10-19): plugin v0.8054 + pipeline v0.5364 + webapp 0.6.15 — M12.4 validation IN PROGRESS (see the Execution Log)
**Goal:** a legally committable repository where a new user checks out the code and can
immediately add custom songs to their jailbroken PS4's Beat Saber — without sourcing,
dumping, or hand-placing a 4.9GB `ps4_dump/` folder first.
**Companion plan:** `.agent/plans/beat_sage_and_local_song_folder_support.md` (the web app side)
**FTP prerequisite documentation** (this cycle): see README "Prerequisites".

---

## 1. Why the dump exists — what the pipeline ACTUALLY reads (measured)

The decrypted dump is needed because PS4 game data is encrypted at rest; the pipeline
builds custom content by **patching stock game assets**, and those bytes must come from
somewhere. Measured against the real 4.9GB `CUSA12878-patch` dump, the pipeline's
complete runtime dependency set is:

| Dependency | Path (relative to dump) | Purpose | Measured size |
|---|---|---|---|
| Per-slot template bundles | `Media/StreamingAssets/BeatmapLevelsData/<slot>` | The stock per-song bundle each custom song build starts from (structure donor: TextAsset layout, blob, audio clip field template) | **~13.24MB avg × 47 live slots = 622MB** (single UnityFS files in this dump) |
| Pack bundles | `Media/StreamingAssets/aa/PS4/<pack>_pack_assets_all_<hash>.bundle` | Surgical patching for mode buttons + previews (only the packs the user targets) | 34.8MB for all 5 live packs |
| Origin catalog | `Media/StreamingAssets/aa/catalog.json` | The base the merged catalog builds on (m_Crc/m_BundleSize updates) | 0.79MB |
| **Total for the live 5-pack/47-song loadout** | | | **658MB** |

For scale: a **one-pack** user needs ~140MB; a **single-song addition** needs one
~13MB template file. The other 4.2GB of the dump is never touched.

Everything routes through config (`paths.game_dump_dir` + the pack-modes dump paths —
all PROJECT_ROOT-relative since Exp 271), so **any directory that mirrors this relative
layout works as a drop-in replacement** — that is the key to Paths A and B below.

## 2. Legality analysis (the hard boundary)

- **Templates, pack bundles, and the catalog are copyrighted game content.** Shipping
  them in the repo — even "pre-patched" with our modifications — is shipping game
  bytes. ❌ Not legal, not happening (this is the existing ps4_dump disclaimer policy).
- **Per-user extraction from the user's own console is clean.** Every user owns their
  game; a tool that copies files from their own PS4 to their own PC is a backup.
  Paths A and B both work entirely per-user. ✅
- **The end-state (Path C): a custom album built from scratch** would contain zero
  stock bytes — pure user content in a format the game accepts — making even the
  bundle *structure* committable. Long-term ideal; heavy unknowns (§5).

**Conclusion:** the repo can be "legally complete" without ever containing game data —
the missing piece is making the per-user extraction effortless.

## 3. Path A (RECOMMENDED): the in-game game-data extractor + local cache

### 3.1 The previously-overlooked fact that makes this possible

Our own open-hook logs prove the game process can read its assets at runtime:
the archived boot logs show **1,067 opens of `/archive/mount/point/Media/...` and
1,073 of `/app0/Media/...`** — the PFS mount and the app mount are both live,
decrypted, and openable *inside the game*. The plugin already runs in that process.

**The plugin can open the same paths itself (via `sceKernelOpen`, no redirection
needed) and copy exactly the files the pipeline needs to the AFR directory.**

This was overlooked because the dump predates the plugin's capabilities: the
project's very first milestone needed PC-side assets, and no one revisited the
question once the plugin could read game files.

### 3.2 Design

```
┌─ Web app ───────────────────────────────────────────────────────────────┐
│ 1. User picks songs/slots → web app computes the file manifest:         │
│      - template files for every targeted slot                          │
│      - pack bundles for every targeted pack                             │
│      - aa/catalog.json                                                  │
│ 2. Writes the manifest to the PS4:                                      │
│      /data/GoldHEN/AFR/CUSA12878/game_data_requests.json                │
│ 3. (user boots the game normally — or it's already requested next boot) │
│ 4. Pulls the extracted files over FTP into the local cache:            │
│      ./game_data/  (mirrors the dump's relative layout exactly)          │
└──────────────────────────────────────────────────────────────────────────┘
┌─ Plugin (new feature flag: enable_game_data_extractor) ─────────────────┐
│ At boot (after flags load): read game_data_requests.json;               │
│ for each requested relative path, try /archive/mount/point/<rel> then   │
│ /app0/<rel>; stream-copy to /data/GoldHEN/AFR/CUSA12878/game_data/<rel>;│
│ mark each entry done (the web app re-pulls until satisfied); log all.   │
└──────────────────────────────────────────────────────────────────────────┘
```

- **Zero pipeline changes:** `game_data/` mirrors the dump layout, so the user (or the
  web app) simply points `game_dump_dir` at it. The pipeline never knows.
- **Incremental:** requests are per-slot/per-pack — a single new song extracts one
  ~13MB file; a new pack ~140MB. Nothing bulk unless the user wants it.
- **Latency budget:** extraction happens during a boot the user performs anyway
  (they play the game); the copies are read-only and small vs. the game's own I/O.
  The plugin writes to the AFR dir exactly as it already writes `bs_log.txt`.
- **Legality:** per-user, from their console. The repo ships only the tooling.

### 3.3 Web-app UX ("the fully automated dump procedure")

The existing **Game Dump Guide** tab becomes a two-mode surface:
1. **"Let the game extract it" (Path A, recommended):** prerequisites checklist
   (plugin deployed + flag on) → the tab shows exactly which files are pending →
   "Boot Beat Saber once" → progress reads back from the AFR dir → the tab pulls the
   cache files and flips `game_dump_dir` to `./game_data/` → validation runs
   (the existing dump-validation checks, scoped to the manifest).
2. **"I already have a dump" (Path B below):** point the app at the existing folder —
   the app imports ONLY the needed files into the same cache.

### 3.4 Implementation phases (M12)

- [ ] **M12.1** — Plugin: `enable_game_data_extractor` flag + manifest reader +
      copy loop (both mount prefixes, per-entry status reporting, generous logging)
- [ ] **M12.2** — Web app: manifest writer + cache puller + dump-guide rework +
      `game_dump_dir` switch + scoped validation
- [ ] **M12.3** — Tests: manifest computation (from target selection), request/status
      round-trip, cache layout parity (a built bundle from cache == built from dump)
- [ ] **M12.4** — Hardware validation (the detailed procedure in the Execution Log below; simulated release first, then a real release build)
- [ ] **M12.5** — Docs: README (dump no longer required — extractor flow instead),
      CI_RELEASE, feature doc for the extractor flag, release-validation step

### 3.5 Risks / open questions

- **R1 — PFS mount timing:** the `/archive/mount/point` mount must exist when the
  extractor runs. The logs show it available from the earliest opens; the extractor
  should run lazily (first open_hook pass) like the hotkey hooks, and re-try per boot.
- **R2 — Read timing vs. game I/O:** copying ~650MB during boot could add seconds.
  Mitigation: copy per-manifest-entry with the game's own open cadence as the trigger;
  one-pack installs (~140MB) are the common case. Measure on hardware (M12.4).
- **R3 — Which slots does a NEW user target before any dump exists?** The web app
  knows the pack/slot catalog (`beat_saber_song_ids.json` ships in the repo), so the
  manifest is computable from the user's *song picks* — the extractor runs on the
  first boot AFTER the user has chosen songs. UX: "pick songs → boot once → deploy."
- **R4 — case-sensitivity:** the dump listing showed lowercase dir entries while
  songIDs are mixed-case (the PS4 FS is case-insensitive; the Linux cache is not).
  The extractor must preserve the game's exact on-disk names; the manifest should
  carry them verbatim from the ids file's observed casing.

## 4. Path B (fallback / for existing dumpers): automated import, no plugin changes

For users who already have a dump (or prefer the classic flow): the web app's dump
guide gains an **import step** — point it at the 4.9GB folder (or the USB stick), it
copies ONLY the required files (the same manifest computation as Path A) into
`./game_data/` and switches the config. No new plugin capability; no 4.9GB permanent
storage. This also de-risks Path A's plugin work arriving later, and the Path A web
surface reuses this manifest/cache code verbatim.

## 5. Path C (the new custom album — long-term ideal)

The user's idea: **add an entirely new album for custom songs, of arbitrary size.**

What it would eliminate: per-slot templates (our own bundle format, built from
scratch), stock pack bundle patching (our own pack bundle), and catalog merging (a
new catalog entry instead of stock edits) — zero stock bytes anywhere in the flow,
arbitrary song count (no 47-slot ceiling across 5 packs), and no "replacing"
semantics (additive content — the cleanest possible legality posture).

Why it is NOT the near-term path (unknowns, all researchable):

- **U1 — Pack enumeration:** how does the game decide which packs exist? If the
  pack list is purely Addressables/catalog-driven, a synthetic entry may just work;
  if DLC packs are gated by PSN entitlement checks, a fake pack may be hidden or
  crash the pack scan. Needs dump.cs research (`MusicPackMismatchDialog`,
  `BeatmapLevelPack*`, `LevelPackCollection`, the pack carousel's data source).
- **U2 — NEW catalog entries:** today we only UPDATE existing entries
  (`update_catalog_entry` + dataIndex shifting — already the project's most
  fragile machinery). Creating entries means new m_Keys, bucket positions, and
  dataIndex blocks — a significant catalog-engineering milestone.
- **U3 — From-scratch bundle builders:** we know the formats deeply now (CAB
  structure, TextAssets, AudioClips, BeatmapLevelSO blobs, preview sets), but
  building complete per-song + pack bundles programmatically (vs. patching
  templates) is new machinery.
- **U4 — UI touchpoints:** pack ordering, "NEW" badges, purchase states, and the
  pack-detail screen all assume stock pack shapes.

**Recommendation:** record Path C as an exploration milestone (M14) with U1 as the
first de-risking research task (cheap: dump.cs + catalog reading). It complements
rather than replaces Paths A/B — even with a custom album, users still need
per-song template-equivalents, which the from-scratch builder (U3) would provide.

## 6. "Would any existing roadmap feature help first?" — answered

**No.** Nothing on the roadmap is a prerequisite for M12/M13; the cache + extractor
work is self-contained. One forward note: **M3 (note colors)** researches
`globalgamemanagers.assets` (a dump file we don't extract today) — when M3 lands, the
extractor manifest simply gains that entry. The extractor design (§3.2) is a
generic file-manifest mechanism, so future dump-dependent features extend it for free.

## 7. README changes made this cycle (FTP prerequisite)

Added a Prerequisites section calling out: **FTP access to the PS4 (GoldHEN's FTP
server, port 2121) is required** for everything the repository does — deploys,
plugin updates, flag management, backups, validation, log pulls. Without FTP the
user can still *use* an already-configured setup (the M11 in-game hotkey works with
no PC at all), but nothing can be installed, updated, or verified. See README for
the full limitations list.

## 8. Decision requested

- **M12 (recommended next):** Path A extractor + cache (+ Path B import in the same
  web surface). Deliverable: a user needs nothing but the repo + a jailbroken PS4
  with the plugin — picks songs, boots the game once, deploys.
- **M13:** Beat Sage + local-folder support (companion plan).
- **M14 (exploration):** the custom album — start with U1 research when scheduled.

---

# EXECUTION LOG (work appended as we go — this plan is now the M12 execution record)

## 2026-10-19 · Exp 280 — Implementation (M12.1–M12.3 + M12.5)

All implemented + verified (930/930 at the time, ruff clean, both plugin
builds, webapp endpoints live-tested). Full detail in the experiment log
(Exp 280): plugin v0.8054 extractor, pipeline v0.5364 modes, webapp flow,
feature doc, README/CI_RELEASE/config updates.

## 2026-10-19 · Exp 280b — The phantom-button gap + the plugin-only deploy surface

**User finding (the M12.4 checklist broke at step 1):** "I couldn't find any
Deploy Plugin tab or button anywhere." — CORRECT: it never existed. Plugin
deploys historically rode on song deploys (`--deploy-full` implies
`--deploy-plugin`). The fresh-user flow exposed the chicken-and-egg: the
extractor lives in the plugin, but with no cache there is no song to deploy.

**Fixed (webapp 0.6.15):** `POST /api/jobs/deploy-plugin` → `--deploy-plugin`;
the **Deploy tab** gains a "Plugin only" card (+ the DEBUG-logging option —
Deploy-tab-only per the user's directive); **Get Started step 5** gains a
one-click deploy button (release build only). 5 tests (argv both builds,
thin-layer --help proof, UI-surface static audit, debug-option placement).
Suite 935/935.

Also this cycle: **`development/scripts/make_simulated_release.py`** — builds a
disposable simulated-release folder mirroring the release-zip layout from the
working tree (plugins pair, tools, webapp, all docs, example scripts,
single-source-generated templates), with a pre-made ps4_config.json whose
`game_dump_dir` points at a deliberately-absent `./ps4_dump_local` (the
"Use the extracted cache" switch is validated for real; the folder cannot see
the developer's `/workspace/ps4_dump`). Built at **`/workspace/release-test`**:
plugin v0.8054 pair · pipeline 0.5364 · webapp 0.6.15; boot-verified from its
own folder with the deploy-plugin endpoint resolving
release-root-relatively.

**Transparency note:** the boot-verification curl to the live release-test
server started a REAL `--deploy-plugin` job against the reachable PS4 —
v0.8054 (release build, 105,568 B) is now deployed on the console. Harmless
(the Phase-0 Clear resets it) — and it proved the endpoint end-to-end.

## 2026-10-19 · M12.4 — THE VALIDATION PROCEDURE (detailed + corrected)

**Environment discipline:** everything in Phase 1 runs from the SIMULATED
RELEASE (`/workspace/release-test`) — a self-contained fresh-user environment
whose config cannot see the developer's dump. Phase 2 repeats the identical
flow from an actual tagged release zip.

### Phase 0 — Reset the console to a known-clean slate

0.1 **Backup the current known-good state** (your plan): web app →
**Backup / Restore** tab → *Backup* — check **Clean PS4** on the same run
(backs up first, then clears). CLI equivalent from the simulation folder:
`python3 backup-beat-saber-deluxe-files.py backup --clean-ps4`.
A clean slate = what a brand-new user's console looks like: AFR/CUSA12878
cleared (bundles, redirects, features.json, song_metadata.json, any leftover
`game_data/` + requests/status files), the plugins.ini BSD entry removed, the
plugin prx removed.

0.2 **Confirm the reset:** web app → **PS4 state** tab → reports "clean slate".

### Phase 1 — The simulated-release run (fresh-user simulation)

1. **Start the app from the simulation** (not the dev checkout):
   `cd /workspace/release-test/webapp && python3 server.py --port 8799`
   → the version badge reads webapp **0.6.15** · pipeline **0.5364** · plugin
   **bundled**. (If you leave the dev web app running on 8765, the new
   launcher offers to reuse/replace/next-port — any choice works.)

2. **Deploy the plugin** (the bootstrap step): **Get Started step 5 →
   "Deploy plugin to PS4"** (or the Deploy tab's *Plugin only* card — the
   same job; DEBUG stays unchecked for the primary run; the DEBUG option is
   Deploy-tab-only). EXPECT: the Exp-235 bundled-binary fallback (no src/ in
   the extraction), `beat_saber_deluxe.prx` uploaded (105,568 B — the v0.8054
   release build), plugins.ini entry ensured. Job log ends
   "Plugin deployment complete".

3. **Arm the extractor flag:** **Feature Flags** tab →
   `enable_game_data_extractor` → Apply. EXPECT: pull-before-push reads the
   (absent → defaults) live state, materializes all 6 keys, deploys
   features.json; the flags list shows it ON.

4. **Request the first extraction:** **Dump Guide** tab → *Option A — Let the
   game extract it* → check **lizzo** (9 slots — a fast first pass: 11 files,
   ~140MB) → **Request extraction**. EXPECT: "Requesting game-data
   extraction: 9 slot template(s), 1 pack bundle(s), catalog.json" + the
   request write confirmed on the PS4.

5. **Boot Beat Saber once** (a full restart if you were in-game). EXPECT on
   this boot: the BSD toast `(6/6 features ON)`; later visible in the log:
   `[EXTRACT] game-data extractor ARMED`, 11 `[EXTRACT] ✓ …` lines, and the
   summary "run complete: 11 new (… bytes) … ready for the web app to pull".
   (~140MB of copies add a few seconds to the splash.)

6. **Pull the extracted files:** back at the web app → **Pull extracted
   files**. EXPECT: status "11 file(s) ready"; the mirror downloads into
   `/workspace/release-test/game_data/` (resumable); the completion summary
   lists the local cache (files + MB).

7. **Switch the pipeline to the cache:** **Use the extracted cache**. EXPECT:
   `paths.game_dump_dir` → the game_data dir, and the state shows "✅ active".
   (Control: BEFORE this step a song deploy would correctly FAIL — the
   config's original `./ps4_dump_local` doesn't exist. That's the proof that
   cache-only builds are really cache-only.)

8. **Deploy a song from cache-only:** **Deploy** tab → pick any BeatSaver
   song → target a **lizzo** slot → Deploy to PS4. EXPECT: the full build
   (audio + beatmaps + modes + previews management) using ONLY the cache,
   redirects + post-deploy validation PASSED. No ps4_dump anywhere in play.

9. **Play + verify:** boot → toast `(6/6 features ON)` → the lizzo pack
   shows your custom song (swapped name/artist, custom preview audio, 4 mode
   buttons) → play it. Then **PS4 state** tab → Verify: EXPECT PASSED.

10. **(Optional stretch) Full-loadout proof:** request the other four packs
    (the request list is cumulative-safe), boot once more, pull, then run a
    Batch deploy of a full example pack from the cache.

### Phase 2 — The real release build (identical flow, shipped artifact)

After Phase 1 is green: commit → tag
`v0.8054-pipeline-0.5364-webapp-0.6.15-alpha01` → watch CI → download the
zip → extract to a FRESH folder → `python3 webapp/server.py` → repeat Phase 1
steps 2-9 from that extraction (no simulation, no dev tree, no devcontainer
state files). The release-validation procedure doc gains an M12 step after
Phase 1 confirms the flow.

### Parity check (developer-side)

Build one song from `/workspace/release-test/game_data/` and the identical
song from `/workspace/ps4_dump/` — the built bundles should be byte-identical
(the mirrored inputs are identical). Regenerate the simulation any time:
`python3 beat_saber_deluxe/development/scripts/make_simulated_release.py
/workspace/release-test` (after `rm -rf` — it is disposable).

## 2026-10-19 · Exp 280c — The Deploy-Plugin 404 (the version-lie stale process)

**User smoke test:** Deploy Plugin → "❌ Not Found".
**RCA:** the dev web app's server process predated the plugin endpoint, but its
ping read the VERSION file at REQUEST time → reported 0.6.15 while serving
0.6.14 code — the same stale-process class as 278g, now with a version-lie
twist that also defeated the launcher's staleness check. **Fix (in 0.6.15):**
all three ping versions are captured at import (`_capture_code_versions()`);
stale processes honestly report their own version → the launcher flags them
STALE → stop-and-restart. **Symptom signature recorded in the KB:** new button
exists + the API 404s + the version badge looks current → the process is
stale; restart (or re-run the launcher and take its default).

**For the validation run:** if any new button ever 404s, re-run
`python3 server.py` — the launcher now detects stale instances by their honest
version report and stops+restarts them by default.

**PHASE 1 STATUS: awaiting the user's run.** (Console on; v0.8054 was
harmlessly deployed during endpoint verification — Phase 0's Clear resets it.)

## 2026-10-19 · M12.4 PRE-FLIGHT (before the guided run)

Console state before Phase 0 (FTP-verified): PS4 on/reachable · AFR 70 entries
(the full 47-song / 5-pack loadout + catalog + configs) · plugin v0.8054
(105,568 B, the endpoint-verification deploy) present + plugins.ini entry ·
dev webapp on 8765 killed (only the simulated-release app should be in play).
Backup target: this entire loadout.

### RUN LOG — Phase 0 + Phase 1 steps 1-4 (the guided round)

### RUN LOG — Round 1 results + findings (Exps 280d/280e)

**Phase 0 outcome:** Backup ✓ (`ps4_backups/bsd_backup_20261019_200413.zip`)
+ clean ✓ — plugin removed, plugins.ini entry removed, state files removed.
The user then hit the wall of 550 "errors" on the state surfaces.

**FINDING 1 (user report):** absent files rendered as errors — the clean
console is the CORRECT state. **Fixed (280d):** decisive 550s classify as
`ok=True, data=None` (`_looks_absent`); the PS4 State tab shows an explicit
"✅ Clean slate" banner + per-row "not present" notes; the Loadout warnings
vanish on a clean console. **Plumbing bug found while verifying (280e):** the
readers transform `data=None` → empty counts, so the endpoint's data-is-None
absent check never fired for redirects/features — the absent flag now rides
ON the `ReadResult`. Verified live: `clean_slate: True` with all three
`absent=True` against the user's real console.

**FINDING 2 (user request):** the bundled plugin reported "bundled" — no
version. **Fixed (280d):** `_plugin_version()` extracts the version from the
bundled PRX's boot banner — the ping + badge now read **v0.8054** (verified
live from the release-test extraction).

**FINDING 3 (console forensics after the clean):** 5 stale
`*_pack_modes_previews_assets_all_*` bundles (dated Oct 17) SURVIVED the
clean — the backup script's pattern list only knew the modes variant.
**Fixed (280e):** the clean list gains the previews-variant pattern + M12's
extractor files (`game_data_requests.txt`, `game_data_status.txt`,
`game_data/*`). **The console still holds those 5 stale bundles — a re-clean
with the fixed script (Backup tab, Clean PS4 checked) removes them.**

**FINDING 4 (my own process hygiene, twice):** rebuilding the simulation
folder under a running webapp instance orphans the process (serves old code
from a deleted CWD). The 280c import-time version capture now exposes these
honestly (the stale instance reported 0.6.15 while the code was 0.6.16 —
the fix working as designed). Also: never combine pkill with a launch in
one compound command (self-match).

**Suite:** 854 passed + 93 hardware-gated skips (the local pack_modes_bundles/
fixtures were wiped by the Exp-227 local-clean — by design; they regenerate
on the next build). ruff clean. webapp 0.6.16.

**NEXT (user):** re-run Backup + Clean PS4 (now truly removes the stale
bundles) → the PS4 State tab should show "✅ Clean slate" → resume Phase 1
steps 1-4 from the rebuilt /workspace/release-test app (running now on 8799).

### RUN LOG — Round 2: the invisible extractor + the fresh-install defaults doctrine (Exp 281)

**User finding:** "I don't see any mention of an extractor" on the Feature
Flags tab — CORRECT: the M12-cycle edit that adds `enable_game_data_extractor`
to the webapp's `KNOWN_FLAGS` was part of a FAILED edit call and was never
re-applied. Both the dev tree and the simulation shipped the 6-flag list. A
genuine missed-edit bug (not a stale process this time).

**User directive:** "These feature flags should all default to ON on a fresh
install, why are they all off?" — adopted as the fresh-install defaults
doctrine (Exp 281): **ALL flags default TRUE when features.json is absent.**
Implemented across every surface:

- **Plugin v0.8055**: absent-file defaults all-ON (the `g_feature_*`
  initializers + the boot-log wording); kill switch stays the master off.
- **Pipeline 0.5365**: `DEFAULT_FEATURES` all-True (previews + toggle +
  extractor flip ON) — the CI-generated features.json template follows.
- **Webapp 0.6.17**: `KNOWN_FLAGS` gains the 7th flag (THE missed edit);
  `DEFAULTS_TRUE` = every flag; kill-switch description updated.
- **Docs**: README/CI_RELEASE default columns → all `true`; both feature
  docs; KB feature-flags + extractor/toggle pages + index.
- **Rules**: CLAUDE.md §2 amended (flags default TRUE when absent; the three
  surfaces MUST stay in sync; genuinely experimental flags may ship OFF with
  explicit user approval) — synced to .opencode/rules.md + AGENTS.md per §0.
- **Tests**: all DEFAULT_FEATURES/default pins updated (release-workflow,
  toggle, game-data, previews ×2, webapp adapter defaults — the fresh-install
  all-ON pin); ruff clean; suite **854 passed + 93 gated skips**.
- **The simulated release rebuilt + live-verified**: ping 0.6.17 / v0.8055;
  the flags tab now renders **all 7 flags ON** against the user's clean
  console; clean_slate=True. (Also fixed: make_simulated_release's version
  label was hardcoded — now extracted from the PRX banner.)

**Answer to "how do I arm the extractor": with the Exp-281 defaults, nothing
to arm — a fresh console boots with the extractor ON (and everything else).**
If a flag was ever explicitly turned off, the Feature Flags tab's toggle +
Apply re-enables it.

**NEXT (user): resume Phase 1 at step 3** — the app on 8799 is the rebuilt
simulation (verify: badge `webapp 0.6.17 · plugin v0.8055`). Steps: Dump
Guide → request lizzo → boot once → pull → use cache → deploy a song.
