# Development Scripts Index

> **Purpose:** Utility and experimental scripts for Beat Saber PS4 custom song development.
> Each script is documented with its purpose, usage, and relevant experiments.

## Scripts

| Script | Purpose | Created In | Requires | Last Used |
|--------|---------|-----------|----------|-----------|
| `modify_pack_bundle.py` | Binary-patch Addressables pack bundle's `BeatmapLevelSO._previewDifficultyBeatmapSets` to add extra mode entries (OneSaber, 90Degree) via raw byte manipulation | Exp 111 | UnityPy | Exp 115 |

## Notes
- Scripts in this directory are utility/experimental tools, not part of the main pipeline
- They may be superseded by IL2CPP hook approaches in future versions
- All scripts should be run from the workspace root (`/workspace`) unless otherwise noted
