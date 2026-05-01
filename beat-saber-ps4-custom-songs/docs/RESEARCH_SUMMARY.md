# Beat Saber PS4 - Research Summary

## Date: 2026-05-01

## Game Version Analyzed
- **CUSA ID**: CUSA12878 (US PS4/PSVR)
- **Dump Source**: Decrypted PS4 dump via USB dumper
- **Unity Version**: 2022.3.x (LZ4HAM AssetBundles)

## Directory Structure

```
CUSA12878-patch/Media/
├── StreamingAssets/
│   ├── BeatmapLevelsData/    # Built-in levels (AssetBundle per song)
│   │   ├── beatsaber/
│   │   ├── believer/
│   │   └── ... (200+ songs)
│   └── aa/PS4/              # DLC packs as addressable bundles
│       ├── billieeilish_pack_*.bundle
│       ├── bts_pack_*.bundle
│       └── ... (1300+ bundles)
├── globalgamemanagers        # Game metadata
├── globalgamemanagers.assets # Script assemblies (DLLs)
├── level*                   # Scene files
└── sce_module/              # System modules

CUSA12878-app/
├── eboot.bin               # Main executable (30MB ELF)
└── sce_sys/                # System files
```

## Key Classes Found

| Class | Offset | Namespace | Purpose |
|-------|--------|-----------|---------|
| `BeatmapLevelsModel` | 0x0003789c | Main | Main level data model |
| `IBeatmapLevelLoader` | 0x0002f3ed | Main | Level loading interface |
| `CustomLevelLoader` | 0x0006139c | Tayx.Graphy.UI | Custom level loader (EXISTS!) |
| `CustomLevelPathHelper` | 0x000224cc | LiteNetLib.Utils | Path helper |
| `BeatmapLevelPack` | 0x000276b4 | BeatmapCore.DataModels | DLC pack container |
| `AnnotatedBeatmapLevelCollection` | 0x00019b64 | Zenject | Level collection UI |
| `SelectLevelCategoryViewController` | 0x00037f62 | Main | Category selector |
| `StandardLevelDetailViewController` | 0x0002c7ac | Main | Level detail view |

## Important Discovery: CustomLevelLoader EXISTS

The class `CustomLevelLoader` is present in `Tayx.Graphy.UI` namespace!

This suggests:
1. Beat Saber may have custom level infrastructure built-in
2. The system might be disabled or incomplete
3. Could be enabled via config or network

## Addressables Analysis

- **Catalog entries**: 2,049
- **Beat Saber package refs**: 1,297
- **BeatmapLevelsData refs in catalog**: 0

**Conclusion**: Levels NOT loaded via Addressables system.
Levels loaded directly via `AssetBundle.LoadFromFile`.

## RB4DX Comparison

| Aspect | RB4DX | Beat Saber |
|--------|-------|-----------|
| Engine | Proprietary | Unity 2022 |
| File Hook | `NewFile()` | `AssetBundle.LoadFromFile` |
| Song Format | .mid/.dta | AssetBundle |
| Data Format | DTA binary | Unity serialized |
| Plugin Status | **WORKING** | **NOT BUILT** |

## Approach Summary

### Option 1: Plugin (Recommended)
- Hook `AssetBundle.LoadFromFile`
- Redirect to custom levels in `/data/GoldHEN/BeatSaberDX/songs/`
- Create levels in Unity 2022 AssetBundle format

### Option 2: Replace Existing Levels
- Extract game's sharedassets
- Replace existing levels with custom ones
- Risky - breaks game updates

### Option 3: Network-based (Speculative)
- `LiteNetLib` found in codebase
- `CustomLevelsSettingsAsyncInstaller` suggests async config
- Might support downloading custom levels

## Files Created This Session

1. **beat_saber_dx/** - Plugin skeleton (C code)
2. **docs/RB4DX_ARCHITECTURE.md** - RB4DX file redirection explained
3. **docs/BACKPORTER_CONVERTER_ANALYSIS.md** - Backporter tool analysis
4. **docs/ASSET_FORMAT_ANALYSIS.md** - Unity 2022 AssetBundle format
5. **docs/PROJECT_STATUS_TODO.md** - Project plan
6. **docs/LEVEL_LOADING_ARCHITECTURE.md** - Level loading mechanism
7. **docs/CLASS_HIERARCHY_ANALYSIS.md** - Class structure analysis

## Git Commits

```
9f133c4 Analysis: Level loading architecture and class hierarchy
6548424 Create Beat Saber Deluxe (BSDX) plugin skeleton
83b4794 Research: RB4DX analysis, Backporter converter analysis
```

## Next Steps

1. **Verify CustomLevelLoader exists** - can it be enabled?
2. **Create test AssetBundle** - format similar to existing levels
3. **Build minimal plugin** - hook AssetBundle.LoadFromFile
4. **Test on PS4** - verify plugin loads and hooks work

## Tools Needed

1. **UABEA** - For analyzing/extracting Beat Saber AssetBundles
2. **OpenOrbis SDK** - For building GoldHEN plugin
3. **Unity 2022.3** - For creating custom AssetBundles

## Questions to Answer

1. Can CustomLevelLoader be enabled via config?
2. What file format does Beat Saber expect for custom levels?
3. Are function addresses consistent across versions?
4. Does the game check for DLC entitlement before showing songs?