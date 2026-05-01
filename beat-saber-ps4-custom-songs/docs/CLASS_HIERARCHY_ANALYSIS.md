# Beat Saber PS4 - Class Hierarchy Analysis

## Date: 2026-05-01

## Key Classes Found

### Level Loading Hierarchy

```
BeatmapLevelsModel (0x0003789c)
  └── Handles level data model
  └── Probably references level collections

IBeatmapLevelLoader (0x0002f3ed)
  └── Interface for loading beatmap data
  └── LoadBeatmapLevelDataResult (0x00072e24)

CustomLevelLoader (0x0006139c)
  └── Tayx.Graphy.UI namespace
  └── "CustomLevelLoader" class confirmed

CustomLevelPathHelper (0x000224cc)
  └── LiteNetLib.Utils namespace
  └── Path helper for custom levels

CustomLevelsSettingsAsyncInstaller (0x00041614)
  └── Main assembly
  └── Async installer for custom level settings
```

### Level Pack Classes

```
BeatmapLevelPack (0x000276b4, 0x000276dc)
  └── Container for DLC song packs
  └── Part of DataModels namespace
  └── Native support confirmed

BeatmapLevelPackCollection (0x0002fe04)
  └── Collection of beatmap level packs
  └── Part of DataModels namespace

SongPackMask (0x00025f88)
  └── Filter for song packs
  └── GameplayCore namespace

SonyLevelPacksPriceModel (0x0002c915)
  └── Pricing model for Sony DLC

SonyLevelProductPackSourceSO (0x0003d0d4)
  └── Sony DLC source system
```

### UI Controllers

```
AnnotatedBeatmapLevelCollection (0x00019b64, 0x0001d374)
  └── UI representation of level collection
  └── References LadyGaga collection specifically
  └── GridView component

AnnotatedBeatmapLevelCollectionCell (0x00019b64)
  └── Individual cell in collection grid

SelectLevelCategoryViewController (0x00037f62)
  └── Category/album selector
  └── References LevelCategory

StandardLevelDetailViewController (0x0002c7ac)
  └── Level detail view
  └── StandardLevel related

StandardLevelFinishedController (0x0002c7ac)
  └── Post-level completion screen

StandardLevelReturnToMenuController (0x0001fc84)
  └── Return to menu controller

MusicPackPromoBanner (0x00026de4)
  └── DLC promotional banner
```

### Content Model

```
IAdditionalContentModel (0x00019014)
  └── LiteNetLib.Utils namespace
  └── Additional content interface

LevelListTableCell (0x0003f25c)
  └── BGNetCore namespace
  └── Table cell for level list
```

## Important Discovery

### CustomLevelLoader Namespace: Tayx.Graphy.UI

The `CustomLevelLoader` class is in the `Tayx.Graphy.UI` namespace.

**Tayx.Graphy** appears to be a third-party library used by Beat Saber for:
- Custom level loading functionality
- UI components for level selection

This suggests Beat Saber already has custom level support infrastructure that was potentially disabled or incomplete.

### Key Question

Does the PS4 version have CustomLevelLoader ENABLED or is it disabled/removed?

If enabled, we might be able to:
1. Hook into the existing custom level system
2. Use the same file format that PC Beat Saber uses
3. Place custom levels in the expected location

## Next Steps for Investigation

1. Find where CustomLevelLoader looks for custom levels (file path)
2. Determine if the system is enabled/disabled
3. Check if there's a config setting to enable custom levels
4. Look for any Mods/CustomLevels folder references

## References

- CustomLevelLoader: 0x0006139c in globalgamemanagers.assets
- Tayx.Graphy: Third-party library namespace
- Beat Saber may use similar structure to PC version