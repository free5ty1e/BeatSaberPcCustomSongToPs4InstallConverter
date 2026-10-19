# Eliminating or Automating the ps4_dump Folder Requirement

**Status:** 🟢 Path A IMPLEMENTED (Exp 280, 2026-10-19): plugin v0.8054 + pipeline v0.5364 + webapp 0.6.14 — hardware validation (M12.4) pending
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
- [ ] **M12.4** — Hardware validation: fresh-cache → full 5-pack deploy from
      `game_data/` alone, `--verify-ps4` PASSED
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
