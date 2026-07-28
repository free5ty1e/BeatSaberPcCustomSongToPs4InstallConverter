---
name: mode-selector-difficulty-flow
description: How the mode selector and difficulty list interact in Beat Saber PS4 song menu
metadata:
  type: reference
---

# Mode Selector → Difficulty Display Flow

## How It Works (for native songs)

When you select a song in the pack list and the detail view renders:

1. **StandardLevelDetailView.SetContent(BeatmapLevel, ...)** is called (RVA 0x1C3B630)
2. The view reads the **BeatmapLevelSO** (pack-level ScriptableObject loaded at startup) to know which modes and difficulties exist
3. It populates the **BeatmapCharacteristicSegmentedControlController** (offset 0x58 in StandardLevelDetailView) with modes from `_previewDifficultyBeatmapSets`
4. Selecting a mode in this controller fires **DidSelectBeatmapCharacteristicEvent** (RVA ~0x1C4B2E0)
5. The **BeatmapDifficultySegmentedControlController** (offset 0x50) then updates to show the difficulties available for that mode

## Data Source

The mode selector reads from **BeatmapLevelSO._previewDifficultyBeatmapSets** (offset 0x98):
- An array of **PreviewDifficultyBeatmapSet** objects
- Each set contains:
  - `_beatmapCharacteristic` — PPtr\<BeatmapCharacteristicSO\> (fileID=2, external reference)
  - `_previewDifficultyBeatmaps` — array of **PreviewDifficultyBeatmap** objects

Each PreviewDifficultyBeatmap contains difficulty metadata (difficulty enum, note count, obstacle count, etc.).

## Characteristics (BeatmapCharacteristicSO)

| Characteristic | PPtr (fileID=2) PathID |
|---|---|
| Standard | -7286399427822119286 |
| OneSaber | -8583864861369561029 |
| NoArrows | -5623662769225589684 |
| 90Degree | 4533580413116749821 |
| 360Degree | 1189643819550092755 |

These are stored in **sharedassets2.assets** (fileID=2), loaded at startup and shared across all packs.

## The Problem with Redirected Songs

For Rolling Stones songs, `_previewDifficultyBeatmapSets` has only **1 entry** (Standard). The OST Vol 1 pack has **5 entries** (Standard + OneSaber + NoArrows + 90Degree + 360Degree).

Since the preview data is loaded from the **pack bundle at startup** and the get_previewDifficultyBeatmapSets() method is **inlined by IL2CPP** (never called at runtime), IL2CPP function hooks cannot augment this data.

## Future Fix

The BeatmapLevelSO objects are in memory after the pack bundle is loaded. The field at offset 0x98 can be modified directly via memory patching from the open_hook when the pack bundle open is detected.

**Related:** [[beatmap-levelso-field-offsets]], [[il2cpp-calling-convention]], [[experiment-124]]
