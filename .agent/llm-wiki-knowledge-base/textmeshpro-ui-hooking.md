---
name: textmeshpro-ui-hooking
description: "TextMeshPro UI hooking approach for modifying song list metadata in Beat Saber PS4 — hooking TMP_Text.set_text to intercept and replace displayed text"
metadata:
  type: reference
---

# TextMeshPro UI Hooking — Song Metadata Modification

## Overview

After memory injection failed (v0.66–v0.8024), the new approach hooks Unity's TextMeshPro text rendering pipeline to intercept and modify displayed song names/artists in the song list UI.

**Status:** 🔵 Implementation planned (v0.8026+)

## UI Framework: TextMeshPro

Beat Saber uses **TextMeshPro** (`Unity.TextMeshPro.dll`) for all UI text:
- `TextMeshProUGUI` — all in-game UI text (song names, scores, buttons)
- `TMP_Text` — base class with `set_text(string)` virtual method

## Song List UI Class Hierarchy

```
LevelSelectionNavigationController
  ├── AnnotatedBeatmapLevelCollectionsViewController
  │     └── AnnotatedBeatmapLevelCollectionsGridView
  │           └── AnnotatedBeatmapLevelCollectionCell
  │                 _infoText: TextMeshProUGUI @ 0x68
  │
  └── LevelCollectionViewController
        └── LevelCollectionTableView
              └── LevelListTableCell  ← KEY CLASS
                    _songNameText:   TextMeshProUGUI @ 0x90
                    _songAuthorText: TextMeshProUGUI @ 0x98
                    _beatmapLevel:   BeatmapLevel @ 0x118

StandardLevelDetailViewController (detail panel)
  └── LevelBar
        _songNameText:   TextMeshProUGUI @ 0x28
        _authorNameText: TextMeshProUGUI @ 0x30
        _beatmapLevel:   BeatmapLevel @ 0xA0
```

## Key Method Addresses

| Method | RVA | Notes |
|--------|-----|-------|
| `TMP_Text.set_text(string)` | **0x2D35BE0** | Virtual method, slot 66. Hook target. |
| `TMP_Text.get_text()` | 0x2D35A60 | Virtual method, slot 65 |
| `LevelListTableCell.SetDataFromLevelAsync` | **0x1D36940** | Async — populates cell with song data |
| `LevelCollectionTableView.CellForIdx` | 0x1B95D40 | Returns TableCell for index |
| `LevelCollectionTableView.SetData` | 0x1B95360 | Sets song list data |

## Hook Strategy: TMP_Text.set_text with Pointer Tracking

### Phase 1: Hook + Diagnostic (v0.8026)
1. Find `Il2CppUserAssemblies` module base via `sceKernelGetModuleList()`
2. Calculate target: `module_base + 0x2D35BE0`
3. Install Detour using `DetourMode_x32` (5-byte JMP — safe for IL2CPP)
4. Log every call: `this` pointer, string value (first 32 chars), call count

### Phase 2: Pointer Tracking (v0.8027)
1. Hook `LevelListTableCell.SetDataFromLevelAsync` (RVA `0x1D36940`)
2. When it fires, capture `this` (LevelListTableCell)
3. Read `_songNameText` at `this+0x90` and `_songAuthorText` at `this+0x98`
4. Store in tracking table: `{TextMeshProUGUI*, original_name, original_artist}`
5. In `set_text` hook, check if `this` matches tracked pointer

### Phase 3: String Replacement (v0.8028)
1. When tracked pointer matches AND string is in replacement table:
   - Option A: In-place UTF-16LE overwrite (replacement ≤ original length)
   - Option B: Use `il2cpp_string_new()` to create fresh managed string
2. Call original `set_text` with replacement string

## Critical Implementation Details

### Calling Convention
PS4 IL2CPP uses **SysV AMD64** (NOT MS x64):
- `this` in **RDI**
- `value` in **RSI**
- `method` in **RDX**
- No `__attribute__((ms_abi))` — crashes if used

### DetourMode Selection
- **Use `DetourMode_x32`** (5-byte JMP `E9 xx xx xx xx`)
- `DetourMode_x64` (14-byte JMP) can split IL2CPP instructions and crash
- Range ±2GB — always satisfied on PS4 (modules load at 0x80000000–0x90000000)

### System.String Layout (PS4)
```
System.String_o:
  0x00: klass (Il2CppClass*)
  0x08: monitor (void*)
  0x10: _stringLength (int32)  — may be at 0x14 or 0x18 on PS4
  0x14: first_char (UTF-16LE)  — or 0x18/0x1C depending on _stringLength offset
```

### IL2CPP Runtime Functions
To create managed strings from C++:
```c
// Find via dlsym on Il2CppUserAssemblies.prx
typedef void* (*il2cpp_string_new_func)(const char*);
il2cpp_string_new_func il2cpp_string_new = dlsym(RTLD_DEFAULT, "il2cpp_string_new");
```

### Cell Recycling
Table views reuse cells. The same `TextMeshProUGUI*` pointer may display different songs. Must re-track pointers each time `SetDataFromLevelAsync` fires.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| `set_text` is inlined | Low | High | Virtual method with vtable — unlikely. Verify via disassembly. |
| mprotect crash at install | Medium | High | Use `DetourMode_x32`. If crashes, `mprotect()` the page first. |
| High call frequency | Medium | Low | Hook body: just pointer comparison + branch. Fast enough. |
| Cell recycling breaks tracking | High | Medium | Re-track on every `SetDataFromLevelAsync` call. |
| String sharing (in-place modify affects other refs) | Medium | Medium | Use `il2cpp_string_new()` for fresh strings if needed. |

## Related

- [[memory-injection-addressables-bypass]] — Previous approach (DEAD END)
- [[plugin-architecture]] — Plugin build system, hook system
- [[il2cpp-dump-mode-selector-hook]] — Previous IL2CPP hook experiments (inlining, mprotect issues)
- [[feature-flags]] — `enable_song_metadata_modification` flag gates this feature
