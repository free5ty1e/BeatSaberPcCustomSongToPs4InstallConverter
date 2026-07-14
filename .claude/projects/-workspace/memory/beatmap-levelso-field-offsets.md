---
name: beatmap-levelso-field-offsets
description: Known field offsets for BeatmapLevelSO and related IL2CPP objects
metadata:
  type: reference
---

# BeatmapLevelSO Field Offsets (IL2CPP v31, 64-bit, PS4)

These offsets are from the dump.cs / DummyDll analysis of the PS4 Beat Saber binary.

## BeatmapLevelSO (TypeDefIndex: 11680)

| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0x00 | Il2CppObject* | klass | Class pointer (vtable) |
| 0x08 | void* | monitor | Sync block (usually NULL) |
| 0x10 | Il2CppString* | m_Name | Asset name (inherited from Object) |
| 0x18 | int | m_HideFlags | Unity hide flags |
| 0x20 | Il2CppString* | _levelID | Song level identifier |
| 0x28 | Il2CppString* | _songName | Song display name |
| 0x30 | Il2CppString* | _songSubName | Song subtitle |
| 0x38 | Il2CppString* | _songAuthorName | Song author |
| 0x40 | Il2CppString* | _levelAuthorName | Level author |
| 0x48 | float | _beatsPerMinute | BPM |
| 0x4C | float | _previewStartTime | Preview audio start (seconds) |
| 0x50 | float | _previewDuration | Preview audio duration (seconds) |
| 0x98 | Il2CppArray* | _previewDifficultyBeatmapSets | Array of PreviewDifficultyBeatmapSet |

## BeatmapLevel (TypeDefIndex: 11647)

| Offset | Type | Field |
|--------|------|-------|
| 0x18 | Il2CppString* | levelID |
| 0x20 | Il2CppString* | songName |

## StandardLevelDetailView (TypeDefIndex: 14781)

| Offset | Type | Field |
|--------|------|-------|
| 0x50 | BeatmapDifficultySegmentedControlController* | _beatmapDifficultySegmentedControlController |
| 0x58 | BeatmapCharacteristicSegmentedControlController* | _beatmapCharacteristicSegmentedControlController |
| 0xE8 | BeatmapLevel* | _beatmapLevel |

## Il2CppArray Layout (SZArray, 64-bit)

| Offset | Size | Field |
|--------|------|-------|
| 0x00 | 8 | klass (Il2CppClass*) |
| 0x08 | 8 | monitor (void*) |
| 0x10 | 8 | bounds (Il2CppArrayBounds*, NULL for SZArray) |
| 0x18 | 8 | max_length (uint64) |
| 0x20 | varies | m_Items[] |

## Il2CppString Layout

| Offset | Size | Field |
|--------|------|-------|
| 0x00 | 8 | klass |
| 0x08 | 8 | monitor |
| 0x10 | 4 | length (int32) |
| 0x14 | 2*length | chars (UTF-16) |

**Related:** [[mode-selector-difficulty-flow]], [[il2cpp-calling-convention]]
