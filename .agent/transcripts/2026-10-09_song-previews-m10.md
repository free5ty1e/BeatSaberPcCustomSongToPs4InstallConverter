# Session Transcript: M10 Song Previews (2026-10-09 —)

**Feature:** Redirect the song-menu preview playback to the custom song's own
audio (currently plays the stock song's preview — confusing for the user).
**Branch:** `feature/web-app-song-conversion-pipeline` (M9 merged to main; the
new feature work continues per user direction).
**Plan:** `.agent/plans/song-previews.md`

---

## Cycle 1 — Feature kickoff + deep research (2026-10-09)

**User:** M9 validated live by the user ("I checked the deployed Pages version
myself and it looked good - excellent job!"). Next feature on the roadmap:
SONG PREVIEWS. When the player selects a custom song in the song menu, it still
plays the stock song's preview — confusing. Choose an appropriate couple
seconds from each custom song to redirect preview playback to. Leverage the
knowledge base, study the ps4_dump, experiment behind a new feature flag named
like the others (`enable_song_previews` / similar). Write a detailed markdown
plan in .agent/plans BEFORE beginning actual work; keep the plan updated as we
make progress.

### Research performed (all verified against real bytes, this session)

**1. Runtime preview chain (from `/workspace/il2cpp_output/dump.cs`):**
- `SongPreviewPlayer : AudioPlayerBase` (TypeDefIndex 4029) — the menu's
  preview player. `CrossfadeTo(AudioClip, musicVolume, startTime, duration,
  onFadeOutCallback)`; keeps a `_defaultAudioClip` for ambient fallback;
  channels 2-6, crossfade speeds.
- `LevelCollectionViewController` (0x1C2E460 `SongPlayerCrossfadeToLevelAsync`)
  is the caller for song-menu selection; also `HandleLevelCollectionTableViewDidSelectLevel`
  → `SongPlayerCrossfadeToLevel`. Practice view (`PracticeViewController.PlayPreview`
  at 0x1B7BA10) uses the FULL song clip with a start-time slider (separate path).
- `BeatmapLevelSO` (TypeDefIndex 11680 — the same class we patch for mode
  selectors) implements `IAssetSongPreviewAudioClipProvider`:
  - `_previewAudioClip` (AudioClip PPtr) @ 0x48
  - `_previewStartTime` (float) @ 0x64, `_previewDuration` (float) @ 0x68
  - `get_songPreviewAudioClip()` @ 0x988E60 → returns `_previewAudioClip`
- `BeatmapLevel` (runtime wrapper, TypeDefIndex 11647) copies previewStartTime/
  previewDuration/previewMediaData (IPreviewMediaData) from the SO.
- `StaticPreviewMediaData` (11685) holds `(Sprite, AudioClip)` for asset-based
  levels — the pack-bundle path. `FileSystemPreviewMediaData` (11686) loads from
  paths (the WIP levels path, not ours).

**2. Stock preview storage format (verified in lizzo pack bundle bytes):**
- All 5 replaced packs: every BeatmapLevelSO's `_previewAudioClip` is a LOCAL
  PPtr (`m_FileID: 0`) to an AudioClip in the SAME pack bundle CAB. Verified
  across britneyspears (11 SOs/11 clips), camellia (6/6), lizzo (9/9),
  therollingstones (11/11), billieeilish (10/10) — all OK, no cross-bundle refs.
- Each preview AudioClip: `m_LoadType=1` (DecompressOnLoad), 2ch, 44100 Hz,
  16-bit, `m_Length=10.0`, `m_CompressionFormat=1` (Vorbis), m_Resource →
  `archive:/CAB-…/CAB-….resource` with per-clip offset/size slices.
- The 9 lizzo preview clips live CONCATENATED in the pack bundle's inner
  `CAB-….resource` stream (5,066,944 B total), each ~510-605 KB (FSB5 Vorbis,
  mode 15 — the encoder-BLOCKED codec per KB). Preview = exactly 10.0s,
  `_previewStartTime=0.0` for all (the clip itself is pre-cut).
- UnityPy CAN decode them (`d.samples` → 1.76 MB WAV each) — great for
  regression fixtures and for REVERT testing.
- `BeatmapLevelSO._previewStartTime=0.0` and `_previewDuration=10.0` on every
  slot: the SO plays from 0.0 of whatever clip `_previewAudioClip` points at.
  So if we pre-cut the preview ourselves, NO float fields need touching.

**3. Our proven audio format (the one to reuse):**
- Our custom bundles' full-song AudioClips are FSB5 **PCM16 (mode 2)** —
  hardware-proven across the whole 47-song fleet (KB: ps4-fsb5-pcm16-format).
- `hevag_encoder.build_pcm16_fsb5(audio_path, sample_rate, pad_to_size,
  clip_seconds)` already supports a `clip_seconds` truncation parameter.
- The preview player feeds the clip to the same FMOD path; an FSB5 PCM16
  10s preview ≈ 1.76 MB raw (no codec risk).

**4. Mapper intent is available:** 92/94 local BeatSaver sources carry
`_previewStartTime` (V2/V3) or `audio.previewStartTime` (V4) in Info.dat
(the 2 without are V4.0.1 with `audio.previewStartTime` — so ALL 94 carry it,
just different schemas; both readable). Typical values 24-70s, previewDuration
10 or 20s. We will honor the mapper's chosen moment, not invent our own.

**5. Existing patch machinery (build_pack_mode_bundles.py):**
- `get_cab_raw()` → decompressed CAB; `walk_blob()` parses BeatmapLevelSO blobs;
  `rebuild_bundle()` patches CAB object blobs + fixes object table; and
  `rebuild_bundle_file()` rebuilds the UnityFS — IT ALREADY rebuilds the
  `.resource` node: `rebuild_bundle_file` reads the old resource from `dec`
  (the decompressed stream) and re-emits it after the new CAB. The resource
  rides through untouched today.
- `patch_pack_bundle()` patches ONLY CAB blobs today (modes blob per song SO);
  the `.resource` is copied verbatim via the nodes.
- CRC: `crc_decompressed_stream()` computes the CRC the catalog needs;
  `update_catalog_entry()` rewrites m_Crc/m_BundleSize + dataIndex shifts
  (Exp 189 lesson). The deploy path (`deploy_pack_modes`) always deploys the
  merged catalog with the patched bundles (Exp 225 invariant).
- `beat_saber_song_ids.json` albums carry `pack`, `packBundle`, per-song
  `patchPathID`, `songID`, `songName`, `songAuthorName` — everything needed to
  map slot → preview data. `previewSetCount` exists per song too.

**6. Feature-flag plumbing:**
- Plugin (main.cpp): flags parsed from features.json at startup;
  `enable_beatmap_mode_mapping` gate at open_hook skips pack_assets + catalog
  redirects when OFF (stock bundle loads). Current version v0.8047.
- Pipeline DEFAULT_FEATURES = {enable_plugin, enable_custom_song_replacements,
  enable_song_metadata_modification, enable_beatmap_mode_mapping}.
- KEY ARCHITECTURAL INSIGHT: because preview clips ride INSIDE the patched
  pack bundle, a `enable_song_previews` flag is a **redirect-set switch**:
  ON → redirect to the previews-patched bundle; OFF → stock bundle path
  (either via a separate bundle name, or skip-mode-bundle logic). The plugin
  gate mirrors enable_beatmap_mode_mapping's structure.
- Note the flag-DEPENDENCE coupling: previews ride in the SAME bundle as mode
  buttons. If `enable_beatmap_mode_mapping` is OFF but previews ON, we need a
  previews-only patched bundle variant (mode sets stock + previews swapped).
  The clean resolution: preview patching becomes part of the same
  `_ensure_pack_mode_bundles` build with a bundle VARIANTS concept keyed by
  feature combination (the plugin already picks bundle names from
  redirects.json, so variants = different redirect VALUES).

**7. Current live state:** 53 redirects (6 pack/catalog, 47 per-song),
5 patched pack bundles in `beat_saber_deluxe/pack_modes_bundles/` (built from
the dump originals, Exp 191 byte-identical proven), 48 local custom bundles,
47 songs live on the PS4.

### Decisions (reasoning recorded for the plan)

1. **Pure pipeline approach** — patch the preview AudioClips into the pack
   bundle's `.resource` + repoint `_previewAudioClip` fields. NO hooks needed:
   the game's own `get_songPreviewAudioClip()` serves our data. This matches the
   proven M4/M5 pattern (bundle-level patching, catalog CRC correction).
2. **PCM16 for previews** — Vorbis encoder is blocked (KB), PCM16 is proven.
   Cost: ~1.76 MB/preview × 47 ≈ 83 MB across the 5 patched bundles (Vorbis
   would be ~30 MB but is unbuildable). Acceptable; note LZ4HC compresses the
   bundle on disk.
3. **Honor mapper's `_previewStartTime`** with a fallback heuristic
   (loudest-section / beat-grid-aligned) for maps without the field.
4. **Feature flag** `enable_song_previews` (naming matches siblings), default
   false, plugin gates pack-bundle redirects by flag combination; pipeline
   builds the matching bundle variant; DEFAULT_FEATURES gains the key.

### Files touched this cycle
- `.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md` — ROTATED to M10
  (M9's log archived to `experiment_log_archive/experiment_log_web-app-interface_exp244-267_2026-09-28_to_2026-10-09.md`).
- `.agent/transcripts/2026-10-09_song-previews-m10.md` — this file (new session).
- `.agent/plans/song-previews.md` — the detailed plan (next).

---

## Cycle 2 — Phase 1: implementation complete, deploy-ready (Exp 269)

**User:** answered the four plan questions — Q1 mirror what works; Q2 research
it myself; Q3 normalization yes; Q4 determine as I work. Proceed with the
plan; notify when an experiment is ready to deploy to the PS4 for a joint
test. Also: add a README section directing users to the Pages web app for
the getting-started guide.

### README (user request, done first)
- New "🚀 New Here? Start with the Web App" section right after prerequisites:
  the Pages URL (verified live: 200 + `data-mode="pages"` marker), Get Started
  landing, funnel summary, link to the local-app feature tour.

### Q resolutions (all research-verified this cycle)
- **Q1** `m_CompressionFormat=1` — stock preview AND our proven clip declare the
  same value; codec truth lives in the FSB5 header (mode 2 = PCM16).
- **Q2** No block-flag math needed: `rebuild_bundle_file` re-derives blocks
  LZ4HC from the extended stream; nodes carry offsets. THE TRAP: `m_Offset` is
  RELATIVE TO THE RESOURCE NODE START — first spike build used absolute stream
  offsets and every clip read garbage (decode FORMAT/INVALID PARAM errors).
  Control test (modes bundle decodes 9/9) isolated my rebuild; node table diff
  showed resource grew exactly 9×1,764,125; offsets-relative insight fixed it.
- **Q3** Stock previews measure −15.1..−7.6 dBFS RMS (mean ≈ −10.4);
  normalizer targets −10.4, peak-limits −1, engages only when >3 dB off.
- **Q4** Stock preview template = our proven clip's exact field values; only
  m_Offset/m_Size change (m_Length stays 10.0 since we cut exactly 10s).

### Source-of-truth lesson (the deep find of the cycle)
The 2BeLoved repo Info.dat says previewStart=33.8, but the DEPLOYED bundle's
audio (fresh BeatSaver download at release-script time = a different map
version) matches the 34.3s window with correlation 1.0. Preview STARTS from
repo metadata can be wrong for freshly-downloaded deploys. Resolution: audio
ALWAYS comes from the deployed per-song bundle (in sync with gameplay by
construction); start = Info.dat when a matching local source dir exists, else
the busiest-bar heuristic from the deployed bundle's own beatmaps (BPM-aware —
notes carry BEAT values; `bpmEvents.m` converts; surrogateescape decodes
m_Script; mode clones excluded; 4-beat bar snap).

### Implementation (production paths, not spike-only)
- `tools/song_previews.py` — new module: pcm extraction, start resolution
  (info + heuristic), cut/fade/normalize, FSB5 PCM16 container,
  AudioClip-blob parsing (archive:/ anchor; 4-aligned tail), in-place
  repoint, variant rebuild via the existing bundle machinery, variant naming.
- Pipeline 0.5357: DEFAULT_FEATURES + enable_song_previews (False);
  `_previews_enabled`; `_get_pack_modes_entries` variant-aware; build step
  `_ensure_previews_variants` inside `_ensure_pack_mode_bundles`; manifest
  entry with catalogBundleName so catalog regen encodes the variant.
- Plugin 0.8048: flag parsed/logged; gate serves pack pair when EITHER
  mode-mapping OR previews ON; toast N/4. ps4_state.py reports the 4th flag.

### Verification
- Production path builds the lizzo variant byte-identical to the spike
  (cmp → IDENTICAL): 22,656,895 B, crc 619811098, 9/9 previews.
- All 9 patched clips decode exactly 10.0s (UnityPy + independent fsb5 lib
  parse: PCM16, 441000 samples); 9 SOs keep 4 mode sets + stock floats;
  catalog regen encodes variant CRC with 0 invalid dataIndexes.
- Full dry run of the deploy sequence (flag → entries → variant → catalog →
  redirect pair) green; catalog restored to modes-state after the dry run
  (Exp 180 invariant).
- 21 new tests + 4 gating contracts; suite 828/828; ruff clean; plugin builds
  (strings show v0.8048 + song_previews flag line).

### Files touched this cycle
- README.md (Pages section)
- tools/song_previews.py (NEW), tools/full_custom_song_pipeline.py (variant
  threading + build step + DEFAULT_FEATURES), src/main.cpp (v0.8048),
  development/scripts/ps4_state.py (4th flag)
- VERSION → 0.5357, CHANGELOG-PIPELINE.md, CHANGELOG-PLUGIN.md
- tests/test_song_previews.py (NEW, 21 tests), tests/test_pack_mode_pipeline.py
  (Tier 8 gating contracts)
- features.json (materialized enable_song_previews=false)
- .agent/plans/song-previews.md (Phase 1 complete, Qs resolved)
- pack_modes_bundles/lizzo_pack_modes_previews_…bundle + manifest entry
  (deploy artifact)

### Next: Exp 269b — hardware spike (PS4 currently off; user will power on)
Deploy: plugin v0.8048 → lizzo variant + catalog → flag true → redirects.
Rollback: flag false + redirect back to modes bundle.

---

## Cycle 3 — Procedure check + webapp flag surfacing (Exp 269 pre-deploy hardening)

**User:** PS4 powered on. Asked to confirm the test procedure: open the web app,
run the lizzo bundle batch install, then look for song previews — and whether
they need to flip the feature flag on the Feature Flags page.

**Procedure audit findings (answering with code, not guesses):**
1. **The webapp didn't know the new flag** — KNOWN_FLAGS (ps4.py) and
   FLAG_DESCRIPTIONS (server.py) are explicit lists; the Feature Flags page
   would not have shown enable_song_previews at all. Added to both with a
   full description. (57 webapp tests pass.)
2. **Order matters — flag BEFORE batch:** --deploy-full re-deploys
   features.json on every run (merging local + DEFAULT_FEATURES), so flipping
   the flag first means the batch carries it; flipping after works too, but
   then the variant bundle wouldn't be in the redirect values until the NEXT
   deploy (the flag flip alone doesn't swap bundles — the plugin gate does
   patched-vs-stock, but the VARIANT name comes from the redirect VALUE the
   deploy writes). Correct order: flag ON first, then deploy.
3. **Batch scope cost measured:** 3.0 s/song preview build (2.3s audio
   extract + 0.7s cut/fsb5) → full 47-song variant build ≈ 2-3 min per
   deploy. The lizzo batch unions ALL 5 deployed packs (Exp 226/227 rule) →
   it would build preview variants for every pack on the first run. That's
   SAFE (each pack gets its variant + catalog regen covers all) — just
   slower than the single-song path. Recommendation given: EITHER the lizzo
   batch (full-fleet previews, still only minutes) OR one lizzo song deploy
   (surgical spike).
4. **Crash-window fix (the big catch):** `_get_pack_modes_entries` with flag
   ON had made EVERY pack point at the variant name — including packs with
   NO variant built → their catalog entries would have been regenerated
   with variant CRCs from a manifest that doesn't have them / or the
   redirect would name a file that doesn't deploy → the Exp 225
   CE-34878-0 class. Fixed: the variant name is used only when the variant
   (or its buildable modes base) exists locally; otherwise the pack keeps
   its modes-only name (flag-off behavior — nothing breaks, that pack just
   keeps stock previews until its variant builds).
5. **mtime freshness trap:** shutil.copy2 of a downloaded PS4 modes bundle
   preserves the REMOTE mtime (upload time, possibly days old) — an mtime
   comparison would have let a STALE variant ship. Removed the mtime check;
   variants rebuild unconditionally on deploy (3 s/song makes this cheap).

**Verified:** flag False → modes name; flag True → variant name (lizzo);
webapp tests 57 pass; previews tests 21 pass; ruff clean. Staged.

### Corrected user procedure (delivered):
1. Web app → Feature Flags → enable_song_previews ON → Apply
2. Web app → Batch → Lizzo pack → Run (or Deploy page, any lizzo song)
3. Boot Beat Saber → song menu → highlight lizzo slots → previews play the
   custom songs' own audio. Boot toast: 4/4 features ON.

---

## Cycle 4 — LIVE deploy: false-alarm validation failure RCA'd; state verified READY (Exp 269b)

**User run (the log, verbatim highlights):** flag flip via webapp OK → lizzo batch song 1/9: full
song build → bundle deploy (one transient "UNVERIFIED" on the song bundle upload, the known
Exp-240-class flake; the pack files deployed clean) → plugin v0.8048 built+uploaded → 5-pack
incremental bases downloaded → **all 5 packs' preview variants built (46 previews: lizzo 9,
britney 11, RS 11, billie 9, camellia 6)** → all 5 variants + catalog + redirects deployed
and size-verified on-PS4 → then: `❌ Deployed catalog missing/incorrect pack entries:
mismatched=[all 5 pack guids]` → batch stopped (validation failure = exit 1 by design).

**RCA (fast — the log told the story):** catalog md5 local==PS4 (✅), so the DEPLOYED
catalog was the right one. The check builds expected (guid, crc, size) triples from the
manifest row indexed by stock packBundle; my `_record_previews_manifest` wrote variant rows
with `packBundle=<PACK ID>` — so the check read each pack's MODES row (crc 3526914570 for
lizzo) and "mismatched" against the correctly-variant catalog (619811098). False alarm.

**Fixes (pipeline 0.5358):**
1. Variant manifest rows carry the stock bundle name as packBundle.
2. The check's manifest index is FLAG-AWARE (variant row wins when the flag is ON; modes
   row when OFF — dict order can never decide).
3. The 5 on-disk rows repaired.
4. Suite caught a second latent bug while the local flag was ON (its true state from the
   user's webapp Apply): `_get_pack_modes_entries` picked the variant name when only the
   MODES base existed → redirect/presence filters (which check the variant FILE) dropped
   the entries entirely (6 test failures). Rule: variant name only when the variant FILE
   exists.

**Live verification (all green):**
- Re-ran the fixed check against the LIVE downloaded catalog: missing=[] mismatched=[] —
  the deployed state needed NO redeploy.
- Standalone `--verify-ps4` → 🎉 PASSED (after refreshing the stale local Oxytocin bundle
  from the authoritative PS4 copy — the pre-existing informational 4-byte delta).
- Live spot-check: deployed lizzo variant pulled; 9/9 clips decode at exactly 10.0s;
  2BeLoved preview correlates 1.0000 with the custom song's own audio @34.3s.
- PS4 features.json: all 5 flags ON. Plugin: v0.8048 strings-verified.
- Suite: 834/834 (2 new manifest-selection regressions + the 146-file re-run).

**Delivered to the user:** the deploy SUCCEEDED — no re-run needed; boot and listen. If
they want the batch green end-to-end, re-running is now safe (validation passes).

---

## Cycle 5 — Previews hardware-confirmed; batch optimization (Exp 269c)

**User:** re-ran the lizzo batch to verify their own process works; booted the game —
song previews working for ALL custom songs; boot toast v0.8048 4/4 features ON. Asks:
(1) any lizzo hardcoding? (must be any-pack/any-song); (2) optimize the batch preview
regeneration with a --skip-song-preview-management parameter on all-but-last commands
+ only regenerate previews for packs actually touched; (3) download + analyze the PS4 log.

**PS4 log (archived v0.8048_song_previews_first_boot.txt; cleared after):** v0.8048
session perfect — song_previews=1 parsed; 53 redirects (variant names in the pack
redirects); all 5 packs' preview variants served REDIRECTED; catalog redirected;
lizzo pack opened 5× (menu + preview loads); 86 metadata swaps; 0 crash markers.

**Hardcoding audit:** none anywhere in the preview path — scope from deployed state,
slot mapping from song_ids (36 packs), custom detection via song_metadata, audio from
each slot's own bundle. The user's 46-preview batch across 5 packs already proved it.

**Optimization 1 — --skip-song-preview-management:** skips variant BUILD management
(deploy of existing variant continues). batch_runner injects it into all-but-the-last
batch command (previews regenerate once at the end); user-supplied flag on the last
command honored with a NOTE. Threaded through deploy_pack_bundle/modes + CLI paths;
documented in help + README.

**Optimization 2 — per-pack dirty-check:** variant rebuilds only on (a) missing
variant/row, (b) modes-base mtime > previewsAt, (c) custom-slot set changed, or
(d) any slot fingerprint [bundle_md5, info_dat_md5] changed — no UnityPy parse on the
skip path. Measured: clean 5-pack skip = 23.3s (md5 reads) vs 152s rebuild. Profiling
caught _repo_title_index reparsing ~100 Info.dats per SLOT (46×, 42s) → process cache.

**Tests:** 843/843 (7 new: skip-flag threading, 4 dirty-check legs, fingerprint shape,
cache identity, runner injection); lint clean. README: Song Previews in the feature
table + the new flag documented. v0.5359.

---

## Cycle 6 — Second batch failure: 3-part RCA + fixes, live-verified (Exp 269d, pipeline 0.5360)

**User's run:** the lizzo batch (now with --skip-song-preview-management auto-injected)
failed validation at song 1/9 — again with the deploy itself successful. The new
stale-row detector printed the smoking gun: manifest rows named the MODES bundles
while the deploy shipped PREVIEW variants.

**RCAs + fixes:**
1. **Manifest clobber** — _save_manifest (modes builder) keyed rows by pack →
   per-song modes rebuilds replaced the 5 variant rows. Fixed: variant rows are
   preserved (keyed by patchedBundle, deduped newest previewsAt); only the variant
   builder replaces them.
2. **Preview-start drift (found during verification)** — 'Queencard (' is the map's
   literal title (BeatSaver metadata malformed); first-separator split broke the
   repo lookup → heuristic silently took over (53.4→83.1s across rebuilds). Fixed:
   last-separator split + resolution ladder (exact → strip punct → drop parens →
   heuristic), identically in build + fingerprint. Queencard = mapper's 53.423s.
3. **Upload waste completed** — batch songs are separate processes; session memory
   can't dedupe. Fixed: pack/catalog artifacts skip upload when the live remote
   listing confirms the identical size (rebuilt variants always differ in size).

**Live proof (one deploy, all three visible):** 4 packs ⏭️ dirty-skipped in seconds;
4 bundles ⏭️ upload-skipped; only the genuinely-changed lizzo variant + catalog
deployed (Queencard start fix) → --verify-ps4 🎉 PASSED.

**Tests 850/850** (7 new: manifest preservation/dedupe, title ladder, upload-skip
×3). Lint clean. v0.5360.

---

## Cycle 7 — CE-34878-0 crash after batch: full RCA + 3 defenses (Exp 269e, pipeline 0.5361)

**User:** batch succeeded and was MUCH faster (previews only processed at the last song —
the optimization visibly working) but booting the game crashed CE-34878-0. Asked for log
download + RCA + fix + defensive programming + unit coverage.

**Log (archived v0.5360_preview_batch_crash.txt):** crash session dies mid-pack-scan at
RS's redirected open #571; lizzo NEVER re-opened in scan pass 2 (healthy sessions open it
2-4×) — the lazy-CRC crash signature (Exp 180 family).

**Byte forensics (decisive):** catalog expects lizzo crc 2,222,108,153; deployed file's
actual crc = 1,065,772,882 — SAME SIZE, different bytes; stream-diff localized the delta
to exactly one preview slice (EverybodysGay). Two different valid builds of one variant.

**Chain (two v0.5359 optimizations interacting):** deploy pass 1 uploaded the variant
built from batch-song-1's fresh BeatSaver bundles; pass 2's dirty-check fired on the
touched modes mtime → REBUILT → catalog got pass-2's CRC → my same-SIZE upload-skip
blocked the corrective upload (same slot set = same size, always) → pass-1 file +
pass-2 catalog → Unity CRC fail at pack scan → CE-34878-0.

**Fixes:** (1) sound upload-skip: same-session record + unchanged remote size only;
cross-process always uploads. (2) single build per deploy: build BEFORE any upload.
(3) NEW deployed-bundle CRC guard in validation: pulls every deployed pack bundle,
compares actual CRC vs catalog — names the crash signature on failure. Would have
caught this pre-boot.

**Live repair:** all 5 variants + catalog re-deployed; --verify-ps4 with the new guard:
5/5 ✅ CRC matches → 🎉 PASSED. PS4 safe to boot.

**Tests 856/856** (5 new: skip soundness ×3, crash-number contract, single-build
ordering, guard presence). Lint clean. v0.5361.

---

## Cycle 8 — Success verified + release-prep audit (Exp 270)

**User:** lizzo batch re-run fast + successful; PS4 tested — no crash, previews working,
spot-check played levels. Asked for log audit + full release-notes/CI/KB/docs/README audit
for release prep. Also complimented the preview section choices (title-in-lyrics moments).

**Log audit:** 4 sessions — 2 pre-repair crash boots (kept for the record), 2 post-repair
successes: menu reached, lizzo opened 4-5× (previews streaming), 46 metadata swaps, the
user's two played levels visible (startmeup→Wake Me Up, paintitblack→VOLUPTE). Zero crash
markers. Archived + cleared.

**Preview-selection answer:** shared credit — the mappers' `_previewStartTime` honored
verbatim (26/47) + my busiest-bar heuristic (21/47) that finds choruses (densest windows,
snapped to a bar — titles usually live in choruses).

**Release-prep audit — gaps found and fixed:**
1. CI_RELEASE.md: 4th flag row, 4/4 toast, previews in the tools table.
2. NEW docs/features/song-previews.md — added to the release-zip workflow.
3. requirements-test.txt +fsb5 (CI needs it for the previews roundtrip tests).
4. CI shape proven: 43/43 previews tests hermetic-pass.
5. KB: song-previews.md (new), feature-flags.md (4th flag), lftp-ftp-pitfalls.md
   (pitfall 9: size≠identity + sound upload-skip rules), index.md.
6. README: banner v0.8048/0.5361/0.6.3 + previews highlight; flag table + N/4 toast.
7. Webapp 0.6.4: toast simulation counts from the flag-list length, v0.8048, 4th flag
   in the simulated list; changelog entry.
8. Validation procedure: step 5.1b (previews round-trip) + default TAG bump.

**Suggested release tag: v0.8048-pipeline-0.5361-webapp-0.6.4.**

---

## Cycle 9 — alpha01 release validation: 3 latent layout bugs fixed (Exp 271)

**User:** committed + pushed v0.8048-pipeline-0.5361-webapp-0.6.4-alpha01 (CI green);
asked for full release validation, PR description update (per the prompt), and an
.agent/introduction.md onboarding doc.

**Validation from a CLEAN zip extraction (the M9 lesson applied):**
- Static audit green (FSELF magic both PRXs, song_previews.py + feature doc + fsb5 + 69
  examples shipped; versions consistent).
- Webapp boots from the zip (3-version ping); full --deploy-full from the SHIPPED pipeline
  PASSED against the live PS4.
- Found 3 latent release bugs:
  1. Batch tab: 0 example packs from the zip (flat layout vs RELEASE_ROOT's one-level-up
     assumption — latent since the first M9 release; proven against the 0.6.3 zip too).
     Fixed: paths.py layout probing (release_root_surname/release_path) applied to batch
     dirs, runner cwd, backups, validator. 34 packs now parse from a clean extraction.
  2. Devcontainer-absolute default config paths (Exp 234 finding #1) — all defaults now
     PROJECT_ROOT-relative; example config ships ./ps4_dump/... with a teaching note;
     relative paths localize at load.
  3. Deploy-only --deploy-pack-modes shipped variants+catalog while live redirects still
     named modes bundles (found LIVE during the smoke: catalog/bundle CRC landmine — the
     exact CE-34878-0 class). Deploy-only paths now refresh the redirect pair. The live
     PS4 was healed mid-validation (flag restore + variant re-deploy + redirects refresh →
     all 5 CRCs match, verify 🎉 PASSED).
  - Also: backup script now ships in the zip.

**Deliverables:** introduction.md (onboarding), PR #7 description drafted (46 lines:
summary, how-it-works, batch optimizations, hard-won fixes, testing, release-validation
findings, flag table, after-merge) — awaiting approval to push via the raw-field gh api.
Pipeline 0.5362 + webapp 0.6.5 changelogs; 5 regression tests; suite 864/864; lint clean.

**Suggested final tag: v0.8048-pipeline-0.5362-webapp-0.6.5.**

---

## Cycle 10 — New-tag CI failure RCA (Exp 272)

**User:** approved PR description (pushed ✓); committed layout fixes; tagged
v0.8048-pipeline-0.5362-webapp-0.6.5-alpha01; personally tested webapp + lizzo deploy +
game function (PS4 now off for the night). CI + release build failed.

**RCA:** all 3 failed runs (CI lint, CI tests, plugin-build tests) = ONE line: the new
zip-layout test's `from adapters import paths, batch` unsorted import. The user's commit
predated my final lint-fix edit. Compounding: CI's ruff auto-resolved to 0.17.0 (released
today) with stricter import-sorting vs local 0.16.0 → "passed locally, failed remotely"
even at equal code.

**Fixes (CI-only, no component changes):** (1) sorted the import; (2) pinned
ruff==0.16.0 in requirements-test.txt + ci.yml's lint job (plugin-build inherits) —
local/CI can never lint-diverge again.

**Verified:** ruff clean + 864/864 locally in the CI-equivalent sequence. Ready for
commit + re-tag.

---

## Cycle 11 — alpha02 release validated + CI audit (Exp 273)

**User:** committed + re-tagged v0.8048-pipeline-0.5362-webapp-0.6.5-alpha02; all runs green;
release published. Asked for release validation + CI build audit.

**CI audit:** pinned ruff 0.16.0 confirmed in the release build's install log (with fsb5-1.0);
864 tests collected; build + release jobs green. RESIDUAL FOUND: ci.yml's standalone Lint job
still ran unpinned ruff 0.17.0 — my previous pin edit was a SILENT NO-OP (replace pattern said
`python3 -m ruff`, file says `python -m ruff`) and the file wasn't in the user's commit.
Passed this time (code clean under both), but the divergence window was open → re-applied with
an assert guard + staged. Lesson: never rely on .replace() without an `assert old in s`.

**Release validation (clean extraction):** versions/FSELF/strings/docs/69-examples all correct;
all three Exp 270a fixes verified LIVE from the zip: Batch tab 34 packs (was 0), config paths
all resolve zip-root-relative (build smoke wrote bundle+catalog into the extraction dir; built
modes bundle loads), backup script ships. Core code byte-identical to the repo. Deploy-only
against the powered-off PS4 correctly REFUSED (pull-before-push held; noted a 30s-timeout UX
wart in the deploy-only redirect pull — non-blocking).
