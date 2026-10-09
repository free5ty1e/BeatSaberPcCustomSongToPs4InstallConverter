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
