# Memory Injection — Status Report (2026-07-17)

## Executive Summary

**Status:** ✅ Implementation complete — prototype integrated into plugin v0.66  
**Previous Blocker:** Option B (uncompressed block injection) BLOCKED due to shared decompressed stream  
**New Approach:** Memory injection bypasses Addressables CRC validation entirely  
**Current Phase:** Code integrated, awaiting PS4 hardware testing

## Architecture

```
module_start()
  ├── load_redirects()              — file redirection table
  ├── install_fopen_hook()
  ├── install_open_hook()
  ├── register_song_metadata()      — 13 Rolling Stones entries
  ├── memory_inject_init()          ← NEW
  │     └── pthread_create()        — detached worker thread
  │           └── patch_worker()
  │                 ├── usleep(30s)  — wait for game init
  │                 ├── find_beatmap_level_so_klass()  — locate class by string search
  │                 ├── scan_for_beatmap_level_objects() — memory scan by klass ptr
  │                 └── patch_beatmap_level_object()  — in-place string overwrite
  └── notification
```

## Key Technical Details

### Finding BeatmapLevelSO Class Metadata
1. Use `sceKernelGetModuleList()` to find Il2CppUserAssemblies module base
2. Search module segments for C string "BeatmapLevelSO"
3. Search for 8-byte pointer references to that string → these are `name` fields at Il2CppClass_1+0x10
4. Validate by checking surrounding fields (namespaze, byval_arg)
5. Result: the `BeatmapLevelSO_c` klass pointer

### Finding Objects in Memory
1. Search process memory (0x100000000–0x800000000) in 64KB pages
2. For each readable page, scan for 8-byte-aligned values matching klass pointer
3. Validate candidates by checking:
   - `_version` at +0x18 is a small integer (1–100)
   - `_levelID` at +0x20 is a valid pointer
   - String klass at _levelID[0] is a valid class pointer
   - `_songName` at +0x28 and `_songAuthorName` at +0x38 are valid pointers

### In-Place String Patching
- Managed strings (System_String_o) have format: klass(8) + monitor(8) + length(4) + chars(variable)
- Character data starts at offset 0x14 in UTF-16LE
- New string MUST fit within old capacity (length ≤ original)
- Write new length at +0x10, new chars at +0x14, zero-fill remainder
- This avoids GC complications entirely

## Progress Summary

### Completed
- [x] **Research Phase** — Determined Addressables validates CRC LAZILY (when contents accessed, not during LoadFromFile)
- [x] **IL2CPP Hook Analysis** — Confirmed all previous IL2CPP method hooks are dead ends (inlined/never called)
- [x] **Test Script Created** — `development/scripts/memory_inject_test.py` verifies scanning and patching logic
- [x] **Plugin Skeleton Created** — `development/scripts/memory_inject_plugin.cpp` provides framework
- [x] **Implementation Plan Documented** — `development/scripts/memory_scan_implementation.md` details approach
- [x] **Full Implementation** — `src/memory_inject.h` + `src/memory_inject.cpp` integrated into plugin v0.66
  - Worker thread with 30s delay
  - BeatmapLevelSO klass finding via string search in Il2CppUserAssemblies
  - Process memory scan for BeatmapLevelSO instances
  - In-place string patching (song name, artist, level ID, sub name, mapper)
  - 13 Rolling Stones metadata entries registered

### In Progress / Pending Testing
- [ ] **PS4 Hardware Test** — Deploy v0.66 and verify:
  - Game does not crash
  - Metadata is correctly patched in song selection menu
  - All 13 Rolling Stones songs show correct names + artists
  - Mode selector still works (5 modes)
- [ ] **Edge Cases** — Handle songs with names longer than original capacity
- [ ] **Cover Image Patching** — Replace album art in BeatmapLevelSO

## Implementation Files

| File | Purpose |
|------|---------|
| `src/memory_inject.h` | Public API: init, register, SongMetadataEntry |
| `src/memory_inject.cpp` | Full implementation (~550 lines) |
| `src/main.cpp` | Integration: v0.66, includes metadata registration |
| `development/scripts/memory_inject_test.py` | Test script (Python simulation) |
| `development/scripts/memory_scan_implementation.md` | Design document |

## Verification

The implementation uses the **exact** struct layouts verified from the IL2CPP dump:
- `BeatmapLevelSO_Fields` at `il2cpp.h:381156`
- `BeatmapLevelSO_o` at `il2cpp.h:381195`
- `System_String_Fields` at `il2cpp.h:67167`
- `System_String_o` at `il2cpp.h:67207`
- `Il2CppClass_1` at `il2cpp.h:38`
- `Il2CppObject` at `il2cpp.h:19`
