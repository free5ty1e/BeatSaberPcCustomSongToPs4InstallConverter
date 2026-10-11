---
name: experiment-log
description: "Active experiment log for the CURRENT feature only (M10: Song Previews — redirect the song-menu preview playback to the custom song's own audio). Per-feature rotation: when a feature concludes, archive this file into experiment_log_archive/ and open a fresh log. Experiment numbers are globally sequential across the whole project."
metadata:
  node_type: memory
  type: reference
---

# Experiment Log: Beat Saber PS4 Custom Song Support — M10 Song Previews

**Feature:** Redirect the song-menu preview to the custom song's own audio.
When the player highlights a custom song in the song menu, the PS4 currently
plays the STOCK song's 10s preview clip — confusing. We patch each pack
bundle's per-song `BeatmapLevelSO._previewAudioClip` (FSB5) with a preview cut
from the custom song's own audio, honoring the mapper's `_previewStartTime`
from Info.dat. Plan: `.agent/plans/song-previews.md`.
**Started:** 2026-10-09 (Exp 268)
**System:** PS4 FW 9.00, GoldHEN 2.3 / 2.4b16.2
**Feature flag:** `enable_song_previews` (new, defaults false when absent)
**Archive:** Exps 244-267 (M9 Web App) → `experiment_log_archive/experiment_log_web-app-interface_exp244-267_2026-09-28_to_2026-10-09.md`

---

### Experiment 268: M10 kickoff — song-preview architecture research-verified; plan written (2026-10-09)
- **User:** confirmed the deployed Pages site looks good (M9 done); next feature: SONG PREVIEWS — the menu currently plays the stock song's preview when a custom song is highlighted; choose an appropriate couple of seconds from each custom song and redirect preview playback. New feature flag matching the existing naming; detailed plan in .agent/plans BEFORE work; keep the plan updated.
- **Research (all verified against real bytes, not assumptions):**
  - **Runtime chain (dump.cs):** song-menu selection → `LevelCollectionViewController.SongPlayerCrossfadeToLevelAsync` → `BeatmapLevelSO.get_songPreviewAudioClip()` (RVA 0x988E60, returns `_previewAudioClip` PPtr @ 0x48) → `SongPreviewPlayer.CrossfadeTo(clip, volume, startTime, duration)`. BeatmapLevelSO = the SAME class we already patch for mode selectors.
  - **Storage (verified across all 5 replaced packs — britney 11/11, camellia 6/6, lizzo 9/9, RS 11/11, billie 10/10):** every `_previewAudioClip` is a LOCAL PPtr (m_FileID=0) to an AudioClip in the same pack-bundle CAB; the N clips are concatenated in the bundle's inner `.resource` (e.g. lizzo: 9 clips in 5,066,944 B); every SO has `_previewStartTime=0.0`, `_previewDuration=10.0` — clips are PRE-CUT, so the SO floats never need touching; only the AudioClip's `m_Resource.m_Offset/m_Size` + header fields do.
  - **Codec:** stock previews = FSB5 **Vorbis mode 15** (encoder-BLOCKED per KB); our full-song clips = FSB5 **PCM16 mode 2** (hardware-proven fleet-wide) → reuse PCM16. 10s stereo 44.1k = 1,764,000 B/preview. `build_pcm16_fsb5()` already takes `clip_seconds`.
  - **Mapper intent:** 94/94 local sources carry a preview start (V2/V3 `_previewStartTime`; V4 `audio.previewStartTime`) — we honor the mapper's moment, not our own guess; heuristic fallback for absent fields.
  - **Flag mechanics — architectural insight:** previews ride INSIDE the patched pack bundle (same one as mode buttons) → `enable_song_previews` is a redirect-set switch like Exp 222's `enable_beatmap_mode_mapping`, and the flag matrix needs bundle VARIANTS (modes+previews / modes-only / previews-only / stock) selected at deploy time from features.json; redirects carry the variant name as VALUE.
  - **Machinery reuse:** `rebuild_bundle_file()` already re-emits the `.resource` node; appending new PCM16 blobs at the stream end + repointing only patched clips leaves every untouched clip's bytes/offsets intact. CRC + catalog handled by existing `crc_decompressed_stream`/`update_catalog_entry` (Exp 189 dataIndex shifting covers the size change).
- **Deliverables:** `.agent/plans/song-previews.md` (full plan: problem, findings, design incl. fade-in/out + loudness match, 4 phases, open questions); roadmap M10 section; experiment log rotated to M10 (M9 archived exp244-267); new session transcript.
- **Open questions for Phase 1 (hardware spike, lizzo 9 slots):** Q1 `m_CompressionFormat` value for PCM16 clip (mirror our proven custom-bundle value vs stock-PCM16 convention — hardware is the oracle); Q2 resource-append block handling; Q3 preview loudness vs stock (measure stock RMS as reference); Q4 mirror stock `m_LoadType=1` + defaults exactly.
- **Status:** ✅ research + plan complete. Next: Phase 1 spike — build the lizzo modes+previews variant, deploy, user listens in the song menu.

### Experiment 269: M10 Phase 1 — previews implemented (pipeline 0.5357, plugin 0.8048); all open questions resolved; lizzo variant built + verified (2026-10-09)
- **User answers locked in:** Q1 mirror what works (our proven m_CompressionFormat=1); Q3 normalize (yes); Q2/Q4 mine to resolve — both RESOLVED via research: m_Offset is RELATIVE TO THE RESOURCE NODE START (absolute offsets made every clip read garbage in the first spike build); the stock preview AudioClip template is byte-identical to our proven clip's field values (LoadType=1/2ch/44.1k/16-bit/CompressionFormat=1/bgload+legacy3D true) — only the resource offset/size change. Also requested: README section pointing users at the Pages getting-started site (added; live URL verified 200 + pages marker).
- **Implementation (production, not spike-only):**
  - `tools/song_previews.py`: cut 10.0s from the slot's own DEPLOYED custom bundle audio (always in sync with gameplay — the repo Info.dat's 33.8s start proved 0.5s WRONG for the freshly-downloaded 2BeLoved deploy; perfect correlation at 34.3s), start = mapper Info.dat _previewStartTime when a matching local source dir exists else the busiest-bar heuristic from the bundle's own beatmaps (BPM-aware: notes carry beats; surrogateescape decode; mode clones excluded; 4-beat bar snap), 8ms/250ms fades, normalize to −10.4 dBFS RMS (9-clip stock measurement) peak-limited −1 dBFS when >3 dB off, FSB5 PCM16 container mirroring build_pcm16_fsb5.
  - Bundle patch: FSB5s appended at the END of the modes bundle's inner .resource; AudioClip m_Resource.m_Offset/m_Size repointed IN PLACE (16 bytes, same blob length — zero object-table shifts). SO floats untouched (stock 0.0/10.0 already plays a pre-cut clip). Variant ships as a SEPARATE bundle (…_pack_modes_previews_assets_all_…) — modes-only bundle untouched.
  - Pipeline 0.5357: `enable_song_previews` in DEFAULT_FEATURES (default False); `_previews_enabled()`; `_get_pack_modes_entries` returns variant names when ON (deploy/catalog/redirect all follow); `_ensure_previews_variants()` builds+manifests the variant in `_ensure_pack_mode_bundles`.
  - Plugin 0.8048: parses the flag; Exp-222 gate now serves pack_assets+catalog when EITHER mode-mapping OR previews is ON (both OFF → stock, Exp 180 CRC invariant preserved); boot toast N/4.
- **Verification:** production path builds the lizzo variant BYTE-IDENTICAL to the spike (22,656,895 B, crc 619811098, 9 previews); all 9 patched clips decode at exactly 10.0s @44.1kHz stereo (UnityPy + independent fsb5-lib parse: mode=2 PCM16, 441000 samples); 9 SOs keep 4 mode sets + stock preview floats; catalog regen encodes the variant CRC (0 invalid dataIndexes); dry run of the full deploy sequence green. 21 new tests (test_song_previews.py incl. real-bundle E2E) + 4 gating contract tests; suite 828/828; ruff clean.
- **Status:** ✅ Phase 1 complete, deploy-ready. PENDING: hardware spike (Exp 269b) — PS4 is off; user will power it on for the joint listen test. Deploy sequence: plugin v0.8048 → lizzo variant + catalog → enable_song_previews=true → redirects. Rollback: flag false + redirect value back to the modes bundle.
