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
