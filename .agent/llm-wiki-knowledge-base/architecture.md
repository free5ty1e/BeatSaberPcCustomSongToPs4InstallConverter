---
name: architecture
description: "High-level Beat Saber PS4 modding architecture: how the game loads songs, the song-data vs song-pack distinction, and which files implement which features"
metadata:
  type: reference
---

# Beat Saber PS4 — Architecture Overview

This page defines the high-level mental model for how Beat Saber (PS4,
CUSA12878) loads and plays custom songs, and which project files are responsible
for which feature. Read this BEFORE touching beatmap-mode or pack code —
confusing the two asset roles below has caused repeated OneSaber bugs.

## Delivery mechanism: file redirects, not code injection

Custom content is shipped by **redirecting file opens** at the OS layer:
- The GoldHEN plugin (`beat_saber_deluxe.prx`) hooks libc `open()` and
  substring-matches the requested path against `redirects.json` keys, serving a
  replacement file from the AFR directory instead. See
  [[ps4-file-system-redirects]] and [[plugin-architecture]].
- Addressables catalog loads as plain JSON, so it is redirected too
  (`aa/catalog.json` → `catalog_pack_modes.json`), which lets us publish corrected
  `m_Crc`/`m_BundleSize` for patched bundles. See [[pack-bundle-patching]].

## The two asset roles (THE key distinction)

### 1. Song data = per-song (custom) bundle
Example: `custom_songs/angry_v3.bundle`, mapped by `redirects.json` onto the
official song slot.
- Holds the **audio** (FSB5 PCM16) and the **beatmaps**.
- Beatmaps include **Standard** plus procedurally generated
  **OneSaber / NoArrows / 90°** mode files from the pipeline generators
  ([[procedural-mode-generators]]). The **OneSaber beatmap is all-blue**
  (`_ONE_SABER_COLOR = 1`) — see [[saber-colors-and-one-saber]].
- **This is where the actual NOTE DATA lives.**

### 2. Song pack = album bundle + Addressables catalog
Example: `therollingstones_pack_assets_all_*.bundle` +
`catalog_pack_modes.json`.
- Holds ONLY **metadata**: the song list, cover art, environment, and
  `_previewDifficultyBeatmapSets` — the list of **mode buttons**
  (Standard / OneSaber / NoArrows / 90°) shown in the song menu, each difficulty
  carrying a **PPtr** that points at a beatmap inside the per-song bundle.
- **Contains no note data.** Editing the pack never changes note colors.

### How mode selection works
1. The pack advertises which mode buttons exist (`_previewDifficultyBeatmapSets`).
2. The player picks a mode (e.g. OneSaber).
3. The game follows that mode's PPtr to load the **beatmap from the song data**
   (per-song bundle).

Therefore, to make OneSaber playable you need BOTH:
- a blue OneSaber beatmap **in the song data** (generator — done), AND
- a OneSaber **button in the pack that points at that blue beatmap**
  (pack-metadata fix — currently the pack clones Standard's PPtr, so it loads
  mixed notes; fix = redirect the OneSaber PPtr to the per-song OneSaber beatmap).

## Feature → file map

| Feature | File(s) | Asset role |
|---|---|---|
| Replace official song with custom song | `redirects.json`, `custom_songs/*_custom.bundle` | song data |
| Convert + build custom song bundle (audio, beatmaps, modes) | `tools/full_custom_song_pipeline.py` | song data |
| Generate blue OneSaber / NoArrows / 90° beatmaps | `_generate_one_saber` etc. in `tools/full_custom_song_pipeline.py` | song data |
| Show mode buttons in song menu (per-pack) | `tools/build_pack_mode_bundles.py` (`build_modes_blob`) + `catalog_pack_modes.json` | song pack metadata |
| Point OneSaber button at blue beatmap | `tools/build_pack_mode_bundles.py` (PPtr reference) | song pack → song data link |
| Song name / artist text in UI | TMP hook, `song_metadata.json` | metadata |
| Catalog CRC/size for patched bundles | `catalog_pack_modes.json`, `update_catalog_entry` | song pack metadata |

## Related
- [[saber-colors-and-one-saber|Saber Colors & OneSaber]] — blue OneSaber lives in song data
- [[procedural-mode-generators|Procedural Mode Generators]] — how mode beatmaps are made
- [[pack-bundle-patching|Pack Bundle Patching]] — CRC/catalog mechanics for the pack
- [[ps4-file-system-redirects|PS4 File System & Redirects]] — open() hook + redirects.json
- [[plugin-architecture|Plugin Architecture]] — the hook that makes redirection possible
- [[song-metadata-storage|Song Metadata Storage]] — where names/artists/environments live
