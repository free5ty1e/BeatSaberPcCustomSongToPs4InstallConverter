# Beat Saber PS4 - Level Loading Architecture

## Date: 2026-05-01

## Key Discovery: Level Loading Mechanism

### Addressables Analysis

Analyzed `/Media/StreamingAssets/aa/catalog.json`:
- **Total entries**: 2,049
- **Beat Saber package references**: 1,297
- **BeatmapLevelsData direct references**: 0

**Conclusion**: Beat Saber does NOT use Addressables for level loading!

### Level Loading Method

Levels in `BeatmapLevelsData/` are likely loaded via:
```
AssetBundle.LoadFromFile(path)
```

Not via:
```
Resources.LoadAsync(addressable_path)
```

This means we need to hook `AssetBundle.LoadFromFile` or similar Unity functions.

## Class Structure (from globalgamemanagers.assets analysis)

### Key Classes Found

| Class | Offset | Purpose |
|-------|--------|---------|
| `BeatmapLevelsModel` | 0x0003789c | Main data model for levels |
| `IBeatmapLevelLoader` | 0x0002f3ed | Level loading interface |
| `LoadBeatmapLevelDataResult` | 0x00072e24 | Level load result |
| `BeatmapLevelPack` | 0x000276b4, 0x000276dc | DLC pack container |
| `BeatmapLevelPackCollection` | 0x0002fe04 | Collection of packs |
| `StandardLevelDetailViewController` | 0x0002c7ac | UI for level detail |
| `StandardLevelListViewController` | (searching...) | Song selection UI |
| `SelectLevelCategoryViewController` | 0x00037f62 | Category/album selection |
| `SongPackMask` | 0x00025f88 | Filter for song packs |
| `AnnotatedBeatmapLevelCollection` | 0x00019b64, 0x0001d374 | Annotated collection UI |
| `AnnotatedBeatmapLevelCollectionCell` | 0x00019b64 | Collection cell |
| `MusicPackPromoBanner` | 0x00026de4 | DLC promo banner |
| `SonyLevelPacksPriceModel` | 0x0002c915 | Pricing model |
| `SonyLevelProductPackSourceSO` | 0x0003d0d4 | Sony DLC source |

### UI Flow (Guessed)
```
SelectLevelCategoryViewController
    └── AnnotatedBeatmapLevelCollectionsGridView
            └── AnnotatedBeatmapLevelCollectionCell
                    └── StandardLevelDetailViewController
                            └── StandardLevelBuyView (for DLC)
```

## Song Categories

From eboot analysis:
- `OST` (0x0192dd83) - Built-in songs
- `DLC` (0x01975670) - Downloadable content
- `SelectLevelCategoryViewController` (0x00037f62) - Category selector

## Plugin Hook Points

### Priority 1: AssetBundle Loading
```c
// Unity 2022 AssetBundle hooks
void* (*AssetBundle_LoadFromFile_Internal)(const char* path, uint32_t crc, uint64_t flags);
void* (*AssetBundle_LoadFromMemory_Internal)(void* data, uint32_t size, uint32_t crc, uint64_t flags);
```

### Priority 2: Level Data Model
```c
// Beat Saber specific hooks
void* (*BeatmapLevelsModel_GetLevelById)(void* model, const char* levelId);
void* (*BeatmapLevelsModel_GetAllLevels)(void* model);
```

### Priority 3: UI/Selection
```c
// For adding to song list
void (*LevelCollection_AddLevel)(void* collection, void* level);
```

## Next Steps

1. Find actual function addresses in eboot.bin (requires PS4 debugging)
2. Hook AssetBundle.LoadFromFile
3. Implement file redirect for custom levels
4. Add custom levels to level collection

## References

- Unity 2022 AssetBundle format: LZ4HAM
- Levels stored in: `Media/StreamingAssets/BeatmapLevelsData/`
- DLC packs in: `Media/StreamingAssets/aa/PS4/*.bundle`