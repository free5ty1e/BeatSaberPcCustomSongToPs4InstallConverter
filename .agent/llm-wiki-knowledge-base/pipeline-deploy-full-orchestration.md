---
name: pipeline-deploy-full-orchestration
description: "Complete end-to-end orchestration via --deploy-full flag in full_custom_song_pipeline.py"
metadata:
  type: reference
---

# Pipeline Deploy Full Orchestration (`--deploy-full`)

**Added in:** v0.5328 (Exp 207, 2026-09-03)
**Single-song scoping:** v0.5331 (Exp 211, 2026-09-08)

## Overview

The `--deploy-full` flag provides **complete end-to-end orchestration in a single command**.
Starting v0.5331, when used with a `--target` song it performs a **self-contained, idempotent
SINGLE-SONG deploy** — it deploys ONLY that one song + its music pack, never the other packs.
This is the recommended way to (re)build custom songs one at a time and test in-game after each.

## What `--deploy-full` Does (Self-Contained, Single Song)

When you run (e.g. replacing one Billie Eilish song):
```bash
python3 tools/full_custom_song_pipeline.py \
  --download-beat-saver-song <MAP_ID> \
  --target AllTheGoodGirlsGoToHell \
  --deploy-full
```

The pipeline:
1. Resolves the target's DLC pack via `beat_saber_song_ids.json` (`_resolve_target_pack`,
   e.g. `AllTheGoodGirlsGoToHell` → `billieeilish`) so everything below is scoped to just that pack.
2. Downloads the song fresh from BeatSaver, converts to V3.2.0 with all 4 modes, builds a PCM16 bundle.
3. **Deploys ONLY the song bundle.**
4. Deploys ONLY that song's **pack-mode bundle** + a matching **single-pack** `catalog_pack_modes.json`
   (so the catalog's CRC/size always match the redirected bundle — Exp 180 rule).
5. Builds + deploys the GoldHEN plugin and ensures the `plugins.ini` `[CUSA12878]` entry.
6. Deploys `features.json` (runtime feature flags).
7. Regenerates `redirects.json` scoped to just that song + its pack pair.
8. Runs post-deploy validation.

> It does **NOT** touch the other configured packs (e.g. deploying one Billie Eilish song no
> longer re-deploys therollingstones/lizzo/camellia or the other 9 songs). On a clean PS4, run
> these one command at a time and test each song's pack in-game before the next.

## Implied Flags

`--deploy-full` automatically sets:
- `--deploy` — upload song bundle to PS4
- `--deploy-config` — deploy local `redirects.json` to PS4
- `--generate-config` — update `redirects.json` with current target
- `--deploy-pack-modes` — build-if-missing + deploy pack mode bundles + merged catalog
- `--deploy-plugin` — build + deploy the GoldHEN plugin and ensure the `plugins.ini` entry
- `--deploy-features` — deploy `features.json` (runtime feature flags)
- `--no-verify-ps4=false` — ensure validation runs (cannot be skipped)

## Works With Both Input Methods

| Input Method | Works With `--deploy-full` |
|--------------|---------------------------|
| `--download-beat-saver-song <MAP_ID>` | ✅ Yes (downloads fresh from BeatSaver every time) |
| `--song-dir <directory>` | ✅ Yes (uses local song directory) |

## Why This Replaces `build_deploy_all38.py`

The old `build_deploy_all38.py` script had a critical flaw: it used **LOCAL CACHED SOURCES** (from `chromeo_backout/`) which were old V4→V3 reconstructions **without the v0.5328 bugfixes** (V3 schema normalization, zero-note rescue, color/direction restore, BPM timing fix).

`--deploy-full` with `--download-beat-saver-song` **always downloads fresh from BeatSaver**, so the beatmaps are converted with all current bugfixes applied.

## Architecture

The orchestration leverages existing pipeline flow which already handles the correct order (Exp 180 crash rule):

```
pack bundles + catalog  →  redirects.json  →  validation
      (Phase 2)               (Phase 3)            (Phase 4)
```

The pipeline's existing `manage_redirect_config()` already picks up pack_modes redirects when `deploy_pack_modes()` is called first.

## Config Requirements

For pack mode bundles to be built/deployed, the config must have:
```json
{
  "pack_modes": {
    "packs": ["therollingstones", "billieeilish", "lizzo", "camelia"]
  }
}
```

If no `pack_modes.packs` is configured, `--deploy-full` still works but only deploys the song bundle + redirects (song-only mode).

## Usage Examples

### Primary Workflow (Recommended)
```bash
python3 tools/full_custom_song_pipeline.py \
  --download-beat-saver-song 1d6c7c2 \
  --target startmeup \
  --deploy-full
```

### With Local Song Directory
```bash
python3 tools/full_custom_song_pipeline.py \
  --song-dir /path/to/song \
  --target startmeup \
  --deploy-full
```

### With Config File (for pack modes)
```bash
python3 tools/full_custom_song_pipeline.py \
  --download-beat-saver-song 5352 \
  --target LightItUp \
  --deploy-full \
  --config development/ps4_config_lizzo_only.json
```

## Related Knowledge

- [[pipeline-deploy-flags|Pipeline Deploy Flags]] — All deploy-related flags
- [[pack-bundle-patching|Pack Bundle Patching]] — CRC correction and pack mode bundles
- [[procedural-mode-generators|Procedural Mode Generators]] — OneSaber/NoArrows/90Degree generation
- [[development-workflow|Development Workflow]] — Deploy cycle, log analysis, FTP