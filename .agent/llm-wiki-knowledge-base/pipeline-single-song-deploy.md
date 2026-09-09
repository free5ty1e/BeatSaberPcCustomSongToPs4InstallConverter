---
name: pipeline-single-song-deploy
description: "Self-contained single-song deploy via --deploy-full (v0.5331). Diagnosed and fixed: pipeline was re-deploying all configured packs on every single-song deploy."
metadata:
  type: reference
---

# Self-Contained Single-Song Deploy (`--deploy-full`)

**Introduced:** v0.5331 (Exp 211, 2026-09-08)

## The Problem

A `--download-beat-saver-song 4a901 --target AllTheGoodGirlsGoToHell --deploy-full`
command was **re-deploying all 4 configured packs** (therollingstones, billieeilish, lizzo,
camellia) plus 43 redirects — even though the user only wanted ONE song over one target slot.
On a clean PS4 this also failed validation ("Redirect targets missing") because the individual
`*_v3.bundle` song files for the other 38 slots were never uploaded.

## Root Cause

Two full-fleet behaviors fired unconditionally on every single-song deploy:

1. **Pack-mode deploy (Step 9a):** the song-processing path called
   `deploy_pack_bundle()` / `deploy_pack_modes()` with **no pack filter**, so
   `_get_pack_modes_entries()` iterated ALL `pack_modes.packs` and uploaded every pack's
   patched bundle + the merged catalog.
2. **Redirect generation (`_ensure_mass_song_redirects`):** regenerated the **entire 38-song**
   `mass_deploy.slots` redirect set, producing a 43-entry `redirects.json` that referenced
   bundles not present on a clean PS4.

Both are correct for a full-fleet deploy but wrong for a targeted single-song deploy. The
pipeline was full-fleet oriented with no single-song scoping.

## The Fix (v0.5331)

Added **single-song scoping** through the whole deployment stack:

- **`_resolve_target_pack(config, target)`** — maps a `--target` slot (e.g.
  `AllTheGoodGirlsGoToHell`) to its DLC pack (e.g. `billieeilish`) via
  `beat_saber_song_ids.json` albums.
- Threaded an optional `packs` filter through `_get_pack_modes_entries`,
  `_get_pack_modes_redirects`, `_get_pack_bundle_redirects`, `_ensure_pack_bundle_redirects`,
  `_regenerate_merged_catalog`, `_ensure_pack_mode_bundles`, `deploy_pack_modes`,
  `deploy_pack_bundle`, `_get_remote_pack_paths`; and a `slots` filter through
  `_ensure_mass_song_redirects`; and both through `manage_redirect_config`.
- In the song path, when a `--target` is present, the pipeline resolves the pack and scopes
  the pack-bundle deploy + catalog regen + redirect generation to **just that pack and that
  song slot**. Full-fleet behavior is preserved when no `--target` is given.
- `--deploy-full` now also implies `--deploy-plugin` (build + deploy plugin, ensure
  `plugins.ini` `[CUSA12878]` entry) and `--deploy-features` (deploy `features.json`).

## Result

A single `--deploy-full` for one song now:
1. resolves the target's pack,
2. deploys ONLY the song bundle,
3. deploys ONLY that pack's mode bundle + a matching **single-pack** merged catalog,
4. builds + deploys the plugin + ensures `plugins.ini`,
5. deploys `features.json`,
6. generates redirects scoped to just that song + pack pair,
7. validates.

It does **NOT** touch the other packs/songs — so you can rebuild custom songs one at a time
and test in-game after each (see `example_commands_to_install_custom_songs_over_*_music_pack.md`).

## Keeping the Exp 180 Invariant

The single-pack catalog must cover exactly the redirected pack so CRC/size validation always
passes at boot. This is preserved: the merged catalog is regenerated for exactly the scoped
pack set(s). Related: [[pipeline-deploy-full-orchestration]], [[addressables-catalog-crc-validation]].