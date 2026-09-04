---
name: pipeline-deploy-flags
description: "All deploy-related flags in full_custom_song_pipeline.py"
metadata:
  type: reference
---

# Pipeline Deploy Flags

**Current as of:** v0.5328 (Exp 207, 2025-09-03)

## Complete Deploy Flags Reference

| Flag | Purpose | Implied By |
|------|---------|------------|
| `--deploy` | Upload bundle to PS4 via FTP | `--deploy-full` |
| `--deploy-config` | Deploy local `redirects.json` to PS4 | `--deploy-full` |
| `--generate-config` | Update `redirects.json` config with current target | `--deploy-full` |
| `--deploy-pack-modes` | Build-if-missing + deploy pack mode bundles + merged catalog | `--deploy-full` |
| `--verify-ps4` | Run post-deploy PS4 validation | `--deploy-full` (sets `--no-verify-ps4=false`) |
| `--no-verify-ps4` | Skip automatic post-deploy validation | — |
| `--sync-config` | Download config from PS4, merge, save, redeploy | — |
| `--enforce-config` | Use local `redirects.json` as truth and deploy to PS4 | — |
| `--deploy-full` | **Complete orchestration** (song + packs + catalog + redirects + validation) | — |
| `--deploy-plugin` | Build + deploy plugin PRX | — |
| `--debug-logging` | Verbose PS4 logging (DEBUG=1 build) | — |
| `--features-only` | Apply + deploy `--set-feature` changes only | — |
| `--set-feature key=value` | Set a runtime feature flag in features.json | — |
| `--enable-plugin` | Enable the Beat Saber Deluxe plugin on PS4 | — |
| `--disable-plugin` | Disable the Beat Saber Deluxe plugin on PS4 | — |

## Flag Hierarchy

```
--deploy-full
    ├── --deploy
    ├── --deploy-config
    ├── --generate-config
    ├── --deploy-pack-modes
    └── --no-verify-ps4=false  (validation cannot be skipped)

--deploy
    └── (upload bundle to PS4)

--deploy-config
    └── (deploy redirects.json to PS4)

--deploy-pack-modes
    ├── --build-pack-modes (if needed)
    ├── deploy pack bundles + merged catalog
    └── manages pack_modes redirects
```

## Primary Workflow Flags

| Workflow | Flags |
|----------|-------|
| **Complete orchestration (recommended)** | `--download-beat-saver-song <ID> --target <slot> --deploy-full` |
| Song only (no pack catalog) | `--download-beat-saver-song <ID> --target <slot> --deploy --deploy-config --generate-config` |
| Local song directory | `--song-dir <dir> --target <slot> --deploy-full` |
| Pack bundles + catalog only | `--deploy-pack-modes --deploy-config --verify-ps4` |
| Feature flags only | `--features-only --set-feature enable_custom_song_replacements=true` |
| Plugin only | `--deploy-plugin [--debug-logging]` |

## Config Requirements for Pack Modes

For `--deploy-pack-modes` (and thus `--deploy-full` with packs) to work, the config must have:

```json
{
  "pack_modes": {
    "packs": ["therollingstones", "billieeilish", "lizzo", "camelia"],
    "song_ids_path": "beat_saber_song_ids.json",
    "dump_dir": "/workspace/ps4_dump/CUSA12878-patch",
    "build_dir": "/workspace/beat_saber_deluxe/pack_modes_bundles",
    "catalog_key": "aa/catalog.json",
    "patched_catalog": "catalog_pack_modes.json",
    "patched_catalog_local": "/workspace/beat_saber_deluxe/catalog_pack_modes.json"
  }
}
```

If no `pack_modes.packs` is configured, `--deploy-full` works in song-only mode.

## Validation Flags

| Flag | When It Runs |
|------|--------------|
| `--verify-ps4` | Explicitly run validation |
| `--deploy` | Auto-runs validation unless `--no-verify-ps4` |
| `--deploy-full` | Auto-runs validation (cannot be skipped) |
| `--deploy-pack-modes` | Auto-runs validation unless `--no-verify-ps4` |

Validation checks:
1. All redirect targets exist on PS4
2. Sizes match local files
3. Pack bundle + catalog pair present
4. Catalog content validation (CRC/size for packs, dataIndex integrity)

## Related Pages

- [[pipeline-deploy-full-orchestration|Pipeline Deploy Full Orchestration (`--deploy-full`)]]
- [[pack-bundle-patching|Pack Bundle Patching]]
- [[development-workflow|Development Workflow]]
- [[procedural-mode-generators|Procedural Mode Generators]]