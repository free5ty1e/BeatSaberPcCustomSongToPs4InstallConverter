---
name: il2cpp-dump-mode-selector-hook
description: "IL2CPP class dump findings for BeatmapLevelSO, get_previewDifficultyBeatmapSets method address, and hook implementation plan"
metadata:
  type: reference
---

# IL2CPP Dump: BeatmapLevelSO Mode Selector Hook

## Overview

After bundle patching approaches repeatedly crashed the game (UnityPy `bf.save()` produces PS4-incompatible bundles), the mode selector modification approach pivoted to **IL2CPP hooking** — intercepting the game's C# method at runtime to inject additional preview difficulty beatmap sets.

## How the IL2CPP Dump Was Done

The game's `Il2CppUserAssemblies.prx` module was dumped with Il2CppDumper instead of `eboot.bin` (which is PS4-protected):

```bash
# From /workspace/Il2CppDumper/
echo "0" | dotnet Il2CppDumper.dll \
    /workspace/ps4_dump/CUSA12878-patch/Media/Modules/Il2cppUserAssemblies.prx \
    /workspace/ps4_dump/CUSA12878-patch/Media/Metadata/global-metadata.dat \
    /workspace/il2cpp_output
```

Il2CppDumper **does not work** with `eboot.bin` (PS4 ELF protection) but **works** with `Il2CppUserAssemblies.prx`.

**Output files:**
| File | Size | Contents |
|------|------|----------|
| `dump.cs` | 32MB | All classes with field offsets and method RVAs |
| `il2cpp.h` | 52MB | C header struct definitions |
| `script.json` | 93MB | JSON script dump |
| `stringliteral.json` | 1.8MB | String literals |
| `DummyDll/` | ~1MB | Decompiled stub DLLs |

**Detected metadata:**
- Metadata Version: 31
- Il2Cpp Version: 31
- CodeRegistration: 4000538
- MetadataRegistration: 418b660

## BeatmapLevelSO Class Layout

From `dump.cs`:

```
// TypeDefIndex: 11680
public class BeatmapLevelSO : PersistentScriptableObject, IAssetSongPreviewAudioClipProvider
{
    // Field offsets (from start of BeatmapLevelSO managed object):
    0x18 - int _version
    0x20 - string _levelID
    0x28 - string _songName
    0x30 - string _songSubName
    0x38 - string _songAuthorName
    0x40 - string _levelAuthorName
    0x48 - AudioClip _previewAudioClip
    0x50 - float _beatsPerMinute
    0x54 - float _integratedLufs
    0x58 - float _songTimeOffset
    0x5C - float _shuffle
    0x60 - float _shufflePeriod
    0x64 - float _previewStartTime
    0x68 - float _previewDuration
    0x6C - float _songDuration
    0x70 - Sprite _coverImage
    0x78 - EnvironmentName _environmentName
    0x80 - EnvironmentName _allDirectionsEnvironmentName
    0x88 - EnvironmentName[] _environmentNames
    0x90 - ColorScheme[] _colorSchemes
    0x98 - PreviewDifficultyBeatmapSet[] _previewDifficultyBeatmapSets  ← TARGET FIELD
    0xA0 - PlayerSensitivityFlag _contentRating
}
```

The field `_previewDifficultyBeatmapSets` at offset **0x98** holds a reference to a managed array of `PreviewDifficultyBeatmapSet` structs.

## PreviewDifficultyBeatmapSet Class Layout

```
// TypeDefIndex: 11677
public class PreviewDifficultyBeatmapSet
{
    0x10 - BeatmapCharacteristicSO _beatmapCharacteristic
    0x18 - List<PreviewDifficultyBeatmap> _previewDifficultyBeatmaps
}
```

Each `PreviewDifficultyBeatmap` struct (at object offset 0x10):
```
0x10 - BeatmapDifficulty _difficulty (int)
0x14 - int _environmentNameIdx
0x18 - int _beatmapColorSchemeIdx
0x1C - float _noteJumpMovementSpeed
0x20 - float _noteJumpStartBeatOffset
0x24 - int _notesCount
0x28 - int _obstaclesCount
0x2C - int _bombsCount
0x30 - int _cuttableBeatmapObjectsCount
```

## Method Addresses

| Method | RVA | Notes |
|--------|-----|-------|
| `get_previewDifficultyBeatmapSets()` | **0x988E80** | Property getter - returns `PreviewDifficultyBeatmapSet[]` |
| `get_beatmapCharacteristic()` (on PreviewDifficultyBeatmapSet) | 0x9892A0 | Returns BeatmapCharacteristicSO ref |

## Hook Implementation Plan

### In the GoldHEN plugin:

1. **Find module base address** — locate `Il2CppUserAssemblies.prx` in memory at runtime using `sys_dynlib_dlsym()` or module name scan
2. **Calculate hook target**: `base + 0x988E80`
3. **Install Detour** at that address using GoldHEN's `Detour_DetourFunction()`
4. **In the detour handler:**
   a. Call the original function (preserving `this` pointer)
   b. Get the returned `PreviewDifficultyBeatmapSet[]` array
   c. Check if `this` BeatmapLevelSO is for a redirected song (e.g., by checking `_levelID` field)
   d. If match: create a new managed array with additional OneSaber/90Degree entries
   e. Return the modified array

### To create new managed objects from C++:
- Use IL2CPP runtime functions: `il2cpp_array_new()`, `il2cpp_object_new()`
- Find their addresses via `sys_dynlib_dlsym()` on `Il2CppUserAssemblies.prx`
- OR scan for exported function names

## Related

- [[song-metadata-addressables-structure]] — Overall Addressables structure
- [[plans/song-list-modes]] — Implementation plan with all option comparisons
- [[../../experiment_log]] — Experiments 113-117 documenting the investigation path

---

## UPDATE: Calling Convention Corrected (Exp 124-126)

### Calling Convention

**PS4 IL2CPP uses SysV AMD64** (same as native C), NOT MS x64. This was confirmed by crash testing:
- Hooks WITH `__attribute__((ms_abi))` crashed on any song selection (read `this` from RCX instead of RDI)
- Hooks WITHOUT `ms_abi` work correctly (read `this` from RDI, which matches IL2CPP)

### Why IL2CPP Function Hooks Don't Work for get_previewDifficultyBeatmapSets

The property getter at RVA 0x988E80 is **inlined by the IL2CPP optimizer**. The function body is copied to every call site, so the original function address is never called at runtime. Hooking it does nothing.

### Constructor Hook — The Working Approach (Exp 126)

Instead of hooking the property getter, hook the **default constructor** at RVA **0x9891E0** (`BeatmapLevelSO..ctor()`). Unlike the getter, the constructor IS called through its function pointer by Unity's serialization system when ScriptableObjects are deserialized from AssetBundles.

**Flow:**
1. Hook constructor (no ms_abi — SysV convention)
2. Save `_this` pointer (fields not populated yet at constructor time)
3. In open_hook, detect rollingstones pack bundle → set `patch_pending = 1`
4. After 3 more file opens → run `patch_beatmap_level_sos()`
5. Iterate saved pointers, check for populated `_previewDifficultyBeatmapSets` (offset 0x98)
6. Augment 1→5 entries

**BeatmapLevelSO field layout (IL2CPP runtime):**
| Offset | Type | Field |
|--------|------|-------|
| 0x00 | Il2CppObject* | klass |
| 0x08 | void* | monitor |
| 0x10 | Il2CppString* | m_Name (inherited from Object) |
| 0x18 | int32 | _version |
| 0x20 | Il2CppString* | _levelID |
| 0x28 | Il2CppString* | _songName |
| 0x30 | Il2CppString* | _songSubName |
| 0x38 | Il2CppString* | _songAuthorName |
| 0x40 | Il2CppString* | _levelAuthorName |
| 0x48 | AudioClip* | _previewAudioClip |
| 0x50 | float | _beatsPerMinute |
| 0x98 | Il2CppArray* | _previewDifficultyBeatmapSets |
| 0xA0 | int32 | _contentRating |

**PreviewDifficultyBeatmapSet layout (IL2CPP runtime, 0x20 bytes):**
| Offset | Type | Field |
|--------|------|-------|
| 0x00 | Il2CppObject* | klass |
| 0x08 | void* | monitor |
| 0x10 | BeatmapCharacteristicSO* | _beatmapCharacteristic |
| 0x18 | Il2CppArray* | _previewDifficultyBeatmaps |

### Creating (Fake) Managed Objects from C++

Since IL2CPP's `il2cpp_object_new()` and `il2cpp_array_new()` are not easily callable from C++, use `malloc()` to create fake managed objects:

```c
// Il2CppArray header: 0x20 bytes (klass + monitor + bounds + max_length)
void *new_arr = malloc(0x20 + N * sizeof(void*));
memcpy(new_arr, existing_arr, 0x20);  // copy klass pointer
*(uint64_t*)(new_arr + 0x18) = N;      // set max_length

// Fake PreviewDifficultyBeatmapSet: 0x20 bytes
void *set = malloc(0x20);
memcpy(set, existing_set, 0x20);  // copy klass, maintain ref count
```

The Boehm GC (conservative) scans these malloc'd regions and won't crash because:
1. The klass pointer is valid and points to alive memory
2. The difficulty array reference points to alive memory
3. Any faux-pointer values in the PPtr fields don't match heap regions

### Next Steps: Finding Real Characteristic Objects

Currently all 5 preview sets reference Standard. To find OneSaber/NoArrows/90Degree/360Degree objects:
- Scan memory for Il2CppStrings matching characteristic serialized names
- Or follow from `BeatmapCharacteristicCollection` singleton
