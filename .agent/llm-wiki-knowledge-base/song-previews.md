---
name: song-previews
description: "M10 song previews: redirecting the PS4 song-menu preview playback to the custom song's own audio — BeatmapLevelSO._previewAudioClip patching, FSB5 PCM16 preview slices, the enable_song_previews flag + variant bundles, and the batch optimizations"
metadata:
  type: reference
---

# Song Previews (M10) — Custom Audio in the Song Menu

## The problem & the runtime chain

When the player highlights a song in the song menu, the game plays a ~10s preview:
`LevelCollectionViewController.SongPlayerCrossfadeToLevelAsync` →
`BeatmapLevelSO.get_songPreviewAudioClip()` (returns the `_previewAudioClip` PPtr,
field offset 0x48) → `SongPreviewPlayer.CrossfadeTo(clip, volume, startTime, duration)`.
Stock preview clips stay in place after a slot replacement — the menu played the
ORIGINAL song's audio under the custom song's name.

## Storage (verified across all 5 replaced packs)

- Every `BeatmapLevelSO._previewAudioClip` is a LOCAL PPtr (`m_FileID=0`) into the
  same pack bundle's CAB; clips are concatenated FSB5s inside the pack bundle's
  inner `.resource` stream.
- Stock previews: 10.0s, 44.1 kHz stereo 16-bit, **FSB5 Vorbis (mode 15)** — the
  encoder-blocked codec ([[ps4-fsb5-vorbis]]). We ship **FSB5 PCM16 (mode 2)** —
  the hardware-proven codec ([[ps4-fsb5-pcm16-format]]) — via the same FMOD path.
- Every stock SO carries `_previewStartTime=0.0` / `_previewDuration=10.0` —
  **clips are pre-cut, so the SO floats never need touching**; only the
  AudioClip's `m_Resource.m_Offset/m_Size` change.
- **`m_Offset` is RELATIVE TO THE RESOURCE NODE START** (stock first clip = 0 while
  its node sits at absolute stream offset 2,013,244). Absolute offsets make every
  clip read garbage — the Exp 269 spike's big catch.

## Preview selection (who chooses the moment)

Two paths, in the DEPLOYED bundle's own timebase (never repo-side guesses — the
Exp 269 lesson: repo Info.dat starts can be wrong for freshly re-downloaded maps):

1. **The mapper's `Info.dat` `_previewStartTime`** (V2/V3; V4 `audio.previewStartTime`)
   when a matching local source dir exists. Resolution ladder for messy titles:
   exact → trailing-punctuation-stripped → parens-dropped → heuristic
   (the map titled literally `'Queencard ('` with artist `(G)I-DLE` broke
   first-separator splitting).
2. **Busiest-bar heuristic** (no local source): the densest 10s window of the
   bundle's own Standard beatmaps — notes carry BEAT values, converted via
   `bpmEvents.m`; mode clones excluded; snapped back to a 4-beat bar.

Cut: 10.0s, 8 ms fade-in / 250 ms fade-out, normalized to the stock-preview fleet
loudness (−10.4 dBFS RMS, peak-limited −1 dBFS, engaged only when >3 dB off).

## The patch (tools/song_previews.py)

FSB5 blobs are APPENDED at the end of the modes bundle's `.resource`; each
preview AudioClip is repointed IN PLACE (16 bytes, same blob length — zero
object-table shifts). AudioClip field values mirror the proven full-song clip
exactly (`m_LoadType=1`, 2ch/44.1k/16-bit, `m_CompressionFormat=1`,
`m_LoadInBackground/m_Legacy3D` true) — only offset/size differ.

## Flag + variant bundles (`enable_song_previews`)

Previews ride INSIDE the patched pack bundle (the same one as mode buttons) — so
the flag is a redirect-set switch like [[partial-pack-deployment-and-clear-target]]'s
Exp 222 pattern: the plugin serves the patched pack+catalog pair when EITHER
`enable_beatmap_mode_mapping` OR `enable_song_previews` is ON; both OFF serves
stock (preserving the [[pack-bundle-patching]] CRC invariant). The pipeline builds
a SEPARATE bundle VARIANT (`…_pack_modes_previews_assets_all_…`) so flag flips
swap redirect VALUES without mutating the modes-only bundle.

## Batch optimizations (Exp 269c/269d/269e)

- **`--skip-song-preview-management`** — batch_runner injects it into all-but-the-last
  batch command (previews regenerate once at the end).
- **Per-pack dirty-check** — a variant rebuilds only when the modes base changed
  (mtime), the custom-slot set changed, or any slot's fingerprint changed
  (`[bundle_md5, info_dat_md5]`; no UnityPy parsing on the skip path).
- **THE CRASH LESSON (Exp 269e, CE-34878-0):** size equality is NOT content
  identity — two different builds of the same variant share size whenever the
  slot set matches (fixed 10s PCM16 slices). The same-size upload-skip + the
  double build in `--deploy-full` together shipped a catalog/file CRC mismatch.
  Sound rules now: uploads skip only on a SAME-SESSION record + unchanged remote
  size; ONE build per deploy happens BEFORE any upload; and post-deploy
  validation pulls every deployed pack bundle and checks its actual
  catalog-scheme CRC against the catalog entry — naming the crash signature.

## Verification

- Every patched clip decodes at exactly 10.0s (UnityPy + independent fsb5-lib parse).
- Deployed content proven by correlation: preview vs the custom song's audio at the
  chosen start = 1.0000.
- The CRC guard (above) runs in `--verify-ps4` and post-deploy validation.

Related: [[ps4-fsb5-pcm16-format]], [[pack-bundle-patching]],
[[surrogateescape-encoding]] (beatmap TextAsset decode), [[feature-flags]]


## The deploy-order preview bug (Exp 283d, 2026-10-23 — the user's field report)

**Symptom:** a freshly deployed song kept its STOCK menu preview while the
previously deployed song's preview worked. Order-dependent: each deploy
baked the PREVIOUS deploy's preview, never its own (Open Road's preview
appeared only after the NEXT deploy ran; the theme song on StartMeUp played
the stock clip until a fixed deploy re-ran).

**Root cause:** the pack/preview pass
(`deploy_pack_bundle → _ensure_previews_variants →
song_previews.build_preview_map`) gates every slot on the LOCAL
song_metadata.json — and the deploy wrote the new song's entry at the very
END (Step 11). At preview-build time the just-deployed slot read as "not a
custom" → no preview baked → the variant on the console carried everyone
else's preview but never the new song's.

**Fix (pipeline 0.5366):** register the target's metadata LOCALLY
(`manage_song_metadata(..., deploy=False)`, idempotent) BEFORE the pack
pass; Step 11 still owns the upload. Pinned by
tests/test_exp283d_preview_metadata_order.py (source-order assertions —
the same pattern as the release-workflow CI-step pin).

**Lesson (the recurring class):** when a BUILD pass reads a STATE file that
a later step writes, verify WHERE in the flow the write happens — "the
deploy updates song_metadata" was true but insufficient; the ORDER was the
bug. Diagnose with the pack_modes_bundles/manifest.json `previews` list
(it records exactly which slots a variant contains — the RS row showed
`previews=['MessItUp']` while StartMeUp was the new deploy, which named the
bug instantly). Also: console file mtimes lie (PS4 clock skew) — trust the
manifest's previewsAt unix timestamps and the pipeline log's local times.
