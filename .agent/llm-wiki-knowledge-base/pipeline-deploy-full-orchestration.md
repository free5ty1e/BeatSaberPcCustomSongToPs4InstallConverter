---
name: pipeline-deploy-full-orchestration
description: "Complete end-to-end orchestration via --deploy-full flag in full_custom_song_pipeline.py"
metadata:
  type: reference
---

# Pipeline Deploy Full Orchestration (`--deploy-full`)

**Added in:** v0.5328 (Exp 207, 2026-09-03)

## Overview

The `--deploy-full` flag provides **complete end-to-end orchestration in a single command**. It replaced the previous two-workflow architecture where users had to run:
1. Per-song `--deploy` (only song bundle)
2. Separate `build_deploy_all38.py` script (pack bundles + catalog + redirects)

## What `--deploy-full` Does (All In One Command)

When you run:
```bash
python3 tools/full_custom_song_pipeline.py \
  --download-beat-saver-song <MAP_ID> \
  --target <slot_name> \
  --deploy-full
```

The pipeline performs **all** of these steps in the correct order (following Exp 180 rule: pack bundles + catalog BEFORE redirects.json):

### Phase 1: Song Bundle Build
1. Downloads song from BeatSaver (fresh every time — not local cached sources)
2. Converts to V3.2.0 (V2→V3 auto-conversion)
3. Generates all 4 modes (Standard, OneSaber, NoArrows, 90Degree)
4. Builds song bundle with PCM16 lossless audio
5. Saves bundle locally

### Phase 2: Pack Mode Bundles + Merged Catalog
6. **Builds** pack mode bundles for all configured packs (if `pack_modes.packs` in config)
7. **Regenerates** merged catalog (`catalog_pack_modes.json`) from origin catalog
8. **Deploys** pack mode bundles + merged catalog to PS4

### Phase 3: Song Bundle + Redirects
9. **Deploys** song bundle to PS4
10. **Generates/updates** `redirects.json` (includes song entry + pack mode bundle entries + catalog entry)
11. **Deploys** `redirects.json` to PS4

### Phase 4: Validation
12. **Runs post-deploy validation** (redirects match, all targets exist, pack+catalog pair present, sizes match)

## Implied Flags

`--deploy-full` automatically sets:
- `--deploy` — upload song bundle to PS4
- `--deploy-config` — deploy local `redirects.json` to PS4
- `--generate-config` — update `redirects.json` with current target
- `--deploy-pack-modes` — build-if-missing + deploy pack mode bundles + merged catalog
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