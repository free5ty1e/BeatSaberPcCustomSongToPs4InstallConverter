# M10 — Song Previews: Redirect Menu Preview Playback to the Custom Song's Audio

**Status:** 🟡 Phase 0 (research complete, plan approved-pending)
**Started:** 2026-10-09 · **Experiments:** 268+
**Plan file:** `.agent/plans/song-previews.md` (this file — update as we progress)
**Feature flag:** `enable_song_previews` (defaults false when absent)

---

## 1. Problem

When the player highlights a custom song in the song menu, the PS4 plays the
**stock song's 10-second preview** — the name says "Oxytocin" but the audio is
Billie Eilish's original. Confusing for the user; breaks the replacement
illusion the rest of the project maintains (names, artists, charts, full audio).

**Goal:** each replaced slot's menu preview plays a ~10s excerpt of the CUSTOM
song's own audio, chosen at the mapper's designated preview moment.

## 2. Research findings (verified against real bytes, 2026-10-09)

### 2.1 Runtime chain (dump.cs)

```
Song menu highlights a level
  └─ LevelCollectionViewController.HandleLevelCollectionTableViewDidSelectLevel
       └─ SongPlayerCrossfadeToLevelAsync(level)          [RVA 0x1C2E460]
            └─ level.previewMediaData.GetPreviewAudioClip()   (asset path)
                 └─ BeatmapLevelSO.get_songPreviewAudioClip() [RVA 0x988E60]
                      → returns _previewAudioClip (PPtr @ 0x48)
            └─ SongPreviewPlayer.CrossfadeTo(clip, vol,
                  level.previewStartTime, level.previewDuration)
```

- `BeatmapLevelSO` (TypeDefIndex 11680) — **the same class we already patch**
  for mode-selector preview sets — holds everything:
  - `_previewAudioClip` AudioClip PPtr @ 0x48
  - `_previewStartTime` float @ 0x64, `_previewDuration` float @ 0x68
  - implements `IAssetSongPreviewAudioClipProvider`
- `SongPreviewPlayer.CrossfadeTo(AudioClip, musicVolume, startTime, duration,
  onFadeOut)` — plays `clip` from `startTime` for `duration` seconds.
- Practice view uses the FULL song clip (separate path; unaffected).
- Fallback: `_defaultAudioClip` (ambient menu music) when no clip.

### 2.2 Stock storage (verified in all 5 replaced packs)

- Every `BeatmapLevelSO._previewAudioClip` is a **local PPtr (m_FileID=0)** to
  an AudioClip object in the SAME pack-bundle CAB. Verified: britney 11/11,
  camellia 6/6, lizzo 9/9, RS 11/11, billie 10/10 — zero cross-bundle refs.
- Each preview AudioClip: `m_LoadType=1`, 2ch, 44100 Hz, 16-bit,
  `m_Length=10.0`, `m_CompressionFormat=1` (**FSB5 Vorbis, mode 15** — the
  encoder-blocked codec per KB `ps4-fsb5-vorbis`).
- All N clips are **concatenated in the pack bundle's inner `CAB-….resource`
  stream**; each AudioClip's `m_Resource.m_Offset/m_Size` slices its own FSB5.
- Example (lizzo): 9 clips, 5,066,944 B resource; per-clip ~510-605 KB.
- `_previewStartTime=0.0`, `_previewDuration=10.0` on every SO — **the clip is
  pre-cut; the SO plays it from 0.0.** So a pre-cut replacement needs NO float
  field changes in the SO blob — only the AudioClip's resource slice.

### 2.3 Our proven format is reusable

- Full-song clips in our custom bundles are **FSB5 PCM16 (mode 2)** —
  hardware-proven fleet-wide (KB `ps4-fsb5-pcm16-format`).
- `hevag_encoder.build_pcm16_fsb5(..., clip_seconds=...)` already supports
  truncation. The preview player feeds any FSB5 to the same FMOD path →
  PCM16 preview is safe. Cost: 10 s × 44,100 × 2 ch × 2 B = **1,764,000 B**
  per preview (~1.76 MB; ≈83 MB raw across 47 slots before LZ4HC).

### 2.4 Mapper intent

- **94/94** local BeatSaver sources carry a preview start (92 in V2/V3
  `_previewStartTime`; the 2 V4.0.1 maps use `audio.previewStartTime`).
  `previewDuration` is typically 10 s (some 20 s — we cut at 10 s to match the
  stock SO field and keep size down).

### 2.5 Existing machinery

- `tools/build_pack_mode_bundles.py`: `get_cab_raw()` (bundle → decompressed
  CAB + `.resource` stream), `walk_blob()` (SO blob parser),
  `rebuild_bundle()` (CAB blob patch + object-table fixups),
  `rebuild_bundle_file()` (rebuilds UnityFS; **already re-emits the
  `.resource` node**), `crc_decompressed_stream()`, `update_catalog_entry()`
  (CRC + dataIndex shift, Exp 189), `validate_catalog_*()`.
- `rebuild_bundle()` handles object-table shifts for CAB blobs; the resource
  stream is separate (nodes) — appending to it doesn't shift CAB offsets
  (nodes carry their own offsets).
- Deploy: `deploy_pack_modes()` builds-if-missing + uploads bundle + merged
  catalog together (Exp 225 invariant: never one without the other).
- `beat_saber_song_ids.json`: albums → songs with `songID`, `songName`,
  `patchPathID`, `pack` — the slot map. `redirects.json` on the PS4 is the
  source of truth for which slots are live (Exp 263 lesson: use deployed
  state, not local assumptions).

### 2.6 Feature-flag mechanics (the architectural insight)

Preview clips ride **inside the patched pack bundle** — the same bundle the
mode-selector patch produces, referenced by the pack redirect. Therefore:

- The plugin flag gate is a **redirect-set switch**, exactly like
  `enable_beatmap_mode_mapping` (Exp 222): when OFF, skip the `pack_assets`
  redirects (+ catalog) so the stock bundle loads.
- **Flag-coupling problem:** previews and mode buttons live in one bundle. The
  flag matrix needs a bundle per distinct ON/OFF combination:
  | mode_mapping | song_previews | bundle variant |
  |---|---|---|
  | ON | ON | modes + previews patched |
  | ON | OFF | modes only (today's bundle) |
  | OFF | ON | previews only (stock mode sets + swapped clips) |
  | OFF | OFF | stock (no redirect) |
- Implementation: **variant-suffixed bundle names**. Today:
  `<pack>_pack_modes_assets_all_<hash>.bundle`. Variants:
  - modes+previews → `..._pack_modes_previews_assets_all_<hash>.bundle`
  - previews-only → `..._pack_previews_assets_all_<hash>.bundle`
  The pipeline builds the variant the CURRENT features.json requests;
  `redirects.json` VALUES point at the variant name; the plugin's Exp-222-style
  gate skips by KEY content (`pack_assets`/`catalog`) per flag. `manage_redirects`
  / `deploy` flows regenerate the redirect VALUE from the same variant logic →
  no dangling (Exp 263 case-healing protects value rewriting; values change
  only when we deploy a new variant).

### 2.7 Risks / unknowns

- **R1 — `.resource` append + slice repoint:** must keep every UNPATCHED clip's
  bytes intact (same offsets), append new PCM16 blobs at the end, and repoint
  only patched AudioClips' `m_Offset/m_Size` (+ `m_Length`, `m_Frequency`).
  Object-table shift logic only applies to the CAB (resource rides in nodes).
  → Phase 1 spike proves this with one pack on hardware.
- **R2 — Vorbis→PCM16 load path:** stock `m_LoadType=1` DecompressOnLoad with
  PCM16 is exactly our full-song configuration (proven). The preview player's
  channel count (2-6) and FMOD resampling are the same as gameplay audio.
  Low risk; verify on hardware (Phase 1).
- **R3 — Bundle size growth:** +1.76 MB per previewed slot. LZ4HC-compressed
  bundle grows less on disk; catalog `m_BundleSize` updated by
  `update_catalog_entry` (already handles arbitrary sizes; Exp 189 dataIndex
  shifting handles m_ExtraDataString block-size changes).
- **R4 — `enable_beatmap_mode_mapping` OFF + previews ON:** requires the
  previews-only variant (mode sets STOCK in the SO blob + clips swapped).
  `build_modes_blob` currently always writes the 4-mode preview sets — needs a
  "stock sets" path or a previews-only patcher that never touches sets.
- **R5 — Songs without local audio:** preview cut needs the song's audio
  (song.egg / audio.fsb). All 47 deployed slots have local sources
  (`custom_songs/` 48 bundles; mass_bundles; chromeo backout). A slot without
  audio → preview patch SKIPPED with a warning (never fails the deploy).
- **R6 — CRC timing:** patched bundle + catalog deploy as a pair (Exp 225
  already enforces). No new risk.

## 3. Design

### 3.1 Preview cut selection

```
preview_start(song_dir):
  1. V2/V3: Info.dat._previewStartTime        (92/94 have it)
     V4:     Info.dat.audio.previewStartTime  (the 2 V4.0.1 maps)
     → clamp to [0, duration-10]
  2. Fallback (rare): beat-grid-aligned heuristic — start at the loudest
     window's nearest downbeat; simple RMS scan over 10s windows, snap to
     the Info.dat BPM grid. (Only used when the field is absent/broken.)
  cut: [start, start+10) seconds, 44.1 kHz stereo 16-bit, light 50 ms fade-in /
       250 ms fade-out to avoid clicks; normalize to the fleet's preview level
       (match stock preview RMS ±3 dB, measured from a stock clip).
```

### 3.2 Bundle patch (extend `build_pack_mode_bundles.py`)

```
patch_previews(song_ids, album, preview_data_map, ...):
  For each song slot with preview data:
    1. Build PCM16 FSB5 preview (10 s) via build_pcm16_fsb5(clip_seconds=10,
       pad_to_size=0, plus fade envelope).
    2. Locate the SO by patchPathID (existing machinery).
    3. Locate its _previewAudioClip PPtr → AudioClip object (same CAB).
    4. Append the FSB5 to the .resource stream (end); record new offset/size.
    5. Patch the AudioClip object blob: m_Resource.m_Offset/m_Size, m_Length=10,
       m_Frequency=44100, m_CompressionFormat=2 (PCM16), m_LoadType stays 1,
       m_BitsPerSample=16, m_Channels=2. (Name kept — cosmetic.)
  Unpatched slots' clips keep their original offsets — untouched bytes.
  → rebuild_bundle_file with the extended resource; crc + catalog entry update.
```

- SO blob floats untouched (`_previewStartTime=0.0` stays; clip is pre-cut).
- `m_CompressionFormat`: set 2 (PCM16). Note our full-song clips ALSO carry
  `m_CompressionFormat=1` (see 2BeLoved: value 1) — check what the 2BeLoved
  object actually declares vs what stock declares; if PCM16-in-Vorbis-compression
  field is what our proven bundles do, mirror the PROVEN value exactly
  (Phase 1 spike decides; vgmstream decode test is the oracle).
- **Phase 1 spike resolves:** exact m_CompressionFormat value to write for a
  PCM16 clip, by mirroring our hardware-proven custom bundle's field value.

### 3.3 Feature flag + variants

- `features.json`: `enable_song_previews` (bool, default false). Added to
  pipeline `DEFAULT_FEATURES` (deploys merge missing keys — Exp 221).
- Plugin `main.cpp` v0.8048:
  - parse `enable_song_previews` → `g_feature_song_previews`
  - boot toast: "N/4 features ON"
  - Exp-222-style gate in open_hook: pack_assets/catalog redirects require
    `g_feature_beatmap_mode_mapping || g_feature_song_previews`; the redirect
    VALUE (variant name) was already chosen at deploy time by the pipeline.
- Pipeline variant selection at build+deploy: read current features.json →
  choose variant suffix (see 2.6 table); build that bundle; write redirect
  VALUES with the variant name; deploy bundle+catalog pair.
  - `--features-only --set-feature enable_song_previews=false` must ALSO
    swap the deployed bundle variant + redirect values (a features-only
    deploy that changes either flag re-deploys the matching variant). This is
    the same "config deploy" path as flag flips today (Exp 222 flow proved).
- `--verify-ps4` gains a preview check: for each live previewed slot, the
  redirected pack bundle on the PS4 contains the slot's PCM16 preview slice
  (size known from build manifest), and redirects point at the deployed
  variant name.

### 3.4 CLI surface (pipeline)

- `--deploy-full` unchanged (variant chosen by current flags).
- New: `--build-song-previews` (explicit; also automatic under --deploy-full
  when `enable_song_previews` is on).
- Preview-data resolution: for each song slot in scope, find its local song
  source dir (reuse the pipeline's slot→source resolution from
  `build_deploy_all38.py` / `deploy_slots` discovery; sources: BeatSaver
  downloads, chromeo backout `audio.fsb`, existing `custom_songs/` bundle's
  audio.gz extraction — decode-able since we built them).
- Config: `pack_modes.preview_fades_ms = {in: 50, out: 250}`,
  `pack_modes.preview_seconds = 10` (defaults; no config needed).

### 3.5 Test plan (pytest, hermetic)

1. `build_pcm16_preview` unit: cut/fade/clamp behavior, V2/V3 + V4 Info.dat
   readers, fallback heuristic on a synthetic map.
2. `patch_previews` on a fixture pack bundle (small synthetic CAB + resource):
   - unpatched clip offsets unchanged; patched clip repointed; resource grew;
   - decode patched clip with UnityPy/fsb5 → 10.0 s, 44100 Hz, 2 ch.
3. Variant naming + redirect VALUE generation: 4-combination matrix.
4. Flag gate: plugin-side is compile-tested (no PS4 in CI); pipeline-side
   variant selection per features.json content.
5. End-to-end local build: build the lizzo variant from the dump + local
   sources → catalog validation (dataIndexes, CRCs) all green.
6. Regression: modes-only build byte-identical to today's bundles when
   previews OFF (proves no accidental coupling).

## 4. Phases (update as we go)

- [x] **Phase 0 — Research** (Exp 268, 2026-10-09): dump.cs chain, storage
      format, flag mechanics, mapper-intent availability, machinery reuse —
      all verified. Plan written.
- [ ] **Phase 1 — Spike: one pack on hardware (Exp 269)**
      - lizzo (9 slots, all custom): build modes+previews variant, deploy,
        user listens in the song menu. Decides m_CompressionFormat question.
      - Deliverable: preview audible for 9 lizzo slots; modes unchanged.
- [ ] **Phase 2 — Full fleet (Exp 270)**
      - All 5 packs × 47 slots; fallback heuristic where needed; variant
        build + redirect updates; verify-ps4 preview check; deploy; user test.
- [ ] **Phase 3 — Flag polish + docs (Exp 271)**
      - features-only variant swap on flag flip; boot toast 4-flag count;
        DEFAULT_FEATURES; KB pages (new `song-previews` page + updates to
        feature-flags, song-metadata-addressables-structure, roadmap);
        README feature list; changelogs; release procedure update.
- [ ] **Phase 4 — (optional) Vorbis preview encoder** if a safe path appears
      (out of scope for now; PCM16 sizes are acceptable).

## 5. Open questions (resolve in Phase 1)

- Q1: `m_CompressionFormat` for a PCM16 preview clip — mirror our proven
     custom-bundle value (1) or stock-PCM16 convention (2)? Spike decides
     (both readable; only hardware is the oracle).
- Q2: does appending to `.resource` in `rebuild_bundle_file` need block-flag
     adjustments for the bigger stream? (Nodes carry offsets; blocks re-derived
     — believed safe; spike proves.)
- Q3: preview loudness matching — measure a stock preview's RMS as reference;
     confirm our normalization keeps menus from blaring.
- Q4: does `m_IsTrackerFormat`/`m_Ambisonic`/`m_SubsoundIndex` matter? (Stock:
     all 0/1 defaults; mirror stock exactly.)

## 6. Documentation map

- Plan (this file) — updated every phase.
- Experiment log: `.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md`
  (M10 header, Exp 268+).
- KB: new `song-previews.md` page (Phase 3) + cross-refs from
  `feature-flags.md`, `song-metadata-addressables-structure.md`,
  `pack-bundle-patching.md`, `index.md`.
- Roadmap: M10 section.
- Transcript: `.agent/transcripts/2026-10-09_song-previews-m10.md`.
