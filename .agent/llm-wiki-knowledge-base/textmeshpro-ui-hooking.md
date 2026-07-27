---
name: textmeshpro-ui-hooking
description: "TextMeshPro UI hooking approach for modifying song list metadata in Beat Saber PS4 — hooking TMP_Text.set_text to intercept and replace displayed text"
metadata:
  type: reference
---

# TextMeshPro UI Hooking — Song Metadata Modification

## Overview

After memory injection failed (v0.66–v0.8024), the new approach hooks Unity's TextMeshPro text rendering pipeline to intercept and modify displayed song names/artists in the song list UI.

**Status:** ✅ **PROVEN WORKING** (v0.8034) — Hook fires, strings read, replacements displayed in pause menu. Song list partially works, song details show "?" for some fields.

## Breakthrough Results (v0.8034)

### What Works
- **Pause menu**: Shows replacement song name AND artist perfectly ("Espresso" / "Sabrina Carpenter")
- **Song artist in list**: "The Rolling Stones" → "Sabrina Carpenter" replaces correctly
- **No crashes**: Signal-protected string extraction handles non-string arguments safely
- **300+ hook calls per session**: Performance is fine, no hangs

### Known Issues
- **Song name in list**: Some song names still show original Rolling Stones names (not all text goes through TMP_Text.set_text)
- **Song details (selection panel)**: Shows "?" for name and empty for artist — the `create_il2cpp_string()` klass pointer or layout may be wrong for this context
- **Artist mismatch**: Replaces "The Rolling Stones" → "Sabrina Carpenter" in artist field, but the real Beat Saber artists for other songs (Megaphonix, Boom Kitty, Jaroslav Beck) are correct

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
| `TMP_Text.set_text(string)` | **0x2D35BE0** | Virtual method, slot 66. Hook target for details/pause menu. |
| `TMP_Text.get_text()` | 0x2D35A60 | Virtual method, slot 65 |
| `TMP_Text.SetText(string, bool)` | **0x2D3E1D0** | Non-virtual, explicit bool overload. Hook target for song list names (but replacement overwritten by data model re-render). |
| `LevelListTableCell.SetDataFromLevelAsync` | 0x1D36940 | **⚠️ DO NOT HOOK** — async wrapper, gets inlined by AsyncVoidMethodBuilder.Start<T>(). Never fires. |
| `LevelListTableCell.SetDataFromLevelAsync/d__21.MoveNext()` | **0x1D377C0** | **ACTUAL HOOK TARGET** — state machine execution. Modifies BeatmapLevel fields before original reads them. |
| `LevelCollectionTableView.CellForIdx` | 0x1B95D40 | Returns TableCell for index |
| `LevelCollectionTableView.SetData` | 0x1B95360 | Sets song list data |

## Hook Strategy: TMP_Text.set_text with Pointer Tracking

### Phase 1: Hook + Diagnostic ✅ COMPLETE (v0.8026–v0.8031)
1. Find `Il2CppUserAssemblies` module base via `sceKernelGetModuleList()`
2. Calculate target: `module_base + 0x2D35BE0`
3. Install Detour using `DetourMode_x64`
4. Log every call: `this` pointer, string value (first 32 chars), call count
5. Signal-protected string extraction for safe pointer reads

### Phase 2: Data Source Modification — IN PROGRESS (v0.8038–v0.8039)
1. ~~Hook `LevelListTableCell.SetDataFromLevelAsync` (RVA `0x1D36940`)~~ — **FAILED**: async wrapper inlined, never fires
2. Hook `MoveNext()` of the state machine (RVA `0x1D377C0`)
3. In `MoveNext()` hook: `this` = state machine struct
4. Read `beatmapLevel` from `this + 0x30`
5. Modify `beatmapLevel.songName` at offset 0x20 and `beatmapLevel.songAuthorName` at offset 0x30
6. Call original `MoveNext()` — it reads our modified fields

### Phase 3: String Replacement ⚠️ PARTIALLY WORKING (v0.8034–v0.8037)
1. When string is in replacement table:
   - Create new IL2CPP System.String using `create_il2cpp_string()`
   - Copy klass pointer from original string
   - Convert ASCII replacement to UTF-16LE
2. Call original `set_text` or `SetText` with replacement string

**Phase 3 status**: Works for song details panel ✅, pause menu ✅, artist blanking in song list ✅. **Song list song names NOT visible** — SetText hook fires and replacement applied (v0.8037 log confirms), but song list UI re-renders from BeatmapLevelSO data model, overwriting the replacement. MoveNext() hook (v0.8039) attempts to fix this by modifying BeatmapLevel fields before the state machine reads them.

### Key Finding: Song List Re-rendering (v0.8037 — CRITICAL)
The song list uses `TMP_Text.SetText(string, bool)` for song name text. The SetText hook fires and applies the replacement, but the song list UI framework then re-applies the original text from its data model (BeatmapLevelSO), overwriting our hook's output. This means **hooking text output methods is fundamentally limited for song list names** — need to hook the data source (BeatmapLevelSO fields) instead.

### Key Finding: Async Wrapper Inlining (v0.8038 — CRITICAL)
IL2CPP async methods like `SetDataFromLevelAsync` are compiled into state machines. The method at the declared RVA (`0x1D36940`) is just a trampoline that creates the state machine and calls `AsyncVoidMethodBuilder.Start<T>()`. This trampoline gets **inlined** — our detour hook at that RVA **never fires** (zero log entries in v0.8038 test).

**Solution:** Hook `MoveNext()` at the state machine's actual RVA (`0x1D377C0`). `MoveNext()` is where the real work happens — it reads `BeatmapLevel.songName`/`songAuthorName` and assigns to TMP_Text fields. The state machine struct layout:
- Offset 0x00: `<>1__state` (int)
- Offset 0x08: `<>t__builder` (AsyncVoidMethodBuilder)
- Offset 0x28: `<>4__this` (LevelListTableCell)
- Offset 0x30: `beatmapLevel` (BeatmapLevel)
- Offset 0x38: `interactable` (bool)
- Offset 0x39: `isFavorite` (bool)
- Offset 0x3A: `isPromoted` (bool)
- Offset 0x3B: `isUpdated` (bool)

**Lesson:** Never hook an async method's declared RVA — always hook the state machine's `MoveNext()` instead.

### Key Finding: Case Sensitivity in Metadata Matching (v0.8040 — CRITICAL)
Game uses different casing than expected for many songs:
- Billie Eilish songs are **all lowercase** in the game: "all the good girls go to hell", "bad guy", "bellyache", "bury a friend"
- Some songs have **different capitalization**: "Mess it Up" (lowercase 'i'), "Sympathy For The Devil" (capitalized), "Good As Hell" (capitalized)
- Some songs have **trailing spaces**: "You Should See Me In A Crown " (trailing space)
- Some songs have **missing articles**: "Whole Wide World" (no "The" prefix)

**Solution:** Pipeline now reads exact song names from `beat_saber_song_ids.json` via `_lookup_song_name()`. Plugin trims trailing spaces before comparison. The `beat_saber_song_ids.json` file is the authoritative source for exact game strings.

## Critical Implementation Details

### Module Discovery Timing (CRITICAL)

**At `module_start()`: only 3 modules visible** (`eboot.bin`, `libSceFios2.prx`, `libc.prx`).
IL2CPP modules not loaded yet. `Il2CppUserAssemblies.prx` becomes visible at ~open #10-11.

**Solution**: Defer `find_il2cpp_module_base()` to `open_hook()`, retry on each call until found. Module list grows from 3→5 as game initializes.

### DetourMode Selection (CORRECTED)

- **Use `DetourMode_x64`** (14-byte JMP) — works correctly, used by open/close hooks
- ~~`DetourMode_x32`~~ (5-byte JMP) — **CRASHES** (v0.8030). Splits IL2CPP variable-length instructions.
- Previous knowledge base note recommending x32 was **WRONG** — corrected in v0.8031.

### Calling Convention
PS4 IL2CPP uses **SysV AMD64** (NOT MS x64):
- `this` in **RDI**
- `value` in **RSI**
- `method` in **RDX**
- No `__attribute__((ms_abi))` — crashes if used

### System.String Layout (PS4 — VERIFIED)
```
System.String_o:
  0x00: klass (Il2CppClass*) — first 8 bytes, copy to create replacement strings
  0x08: monitor (void*)
  0x10: _stringLength (int32) — verified at 0x10, fallback to 0x14
  0x14: first_char (UTF-16LE) — or 0x18 depending on _stringLength offset
```

### Signal-Protected String Extraction (REQUIRED)

The `TMP_Text.set_text` hook fires on **ALL text updates** (~300+ per session), not just song names. Most calls pass non-string values or pointers to strings with different memory layouts.

**Solution**: Wrap `extract_utf16_string()` in `sigsetjmp`/`siglongjmp` with `SIGSEGV`/`SIGBUS` handlers. Catches invalid pointer dereferences and returns 0 (no match) instead of crashing.

```c
static sigjmp_buf g_extract_jmp_buf;
// In extract_utf16_string:
new_sa.sa_sigaction = [](int, struct __siginfo*, void*) {
    siglongjmp(g_extract_jmp_buf, 1);
};
sigaction(SIGSEGV, &new_sa, &old_sa);
if (sigsetjmp(g_extract_jmp_buf, 1) == 0) {
    // safe to dereference str_obj pointers here
} else {
    // SIGSEGV caught — invalid pointer, return 0
}
sigaction(SIGSEGV, &old_sa, NULL);
```

### create_il2cpp_string() — Replacement String Creation

```c
static void* create_il2cpp_string(void* klass_ptr, const char* cstr) {
    int len = strlen(cstr);
    int total = 16 + 4 + (len * 2) + 2;  // klass + monitor + length + chars + null
    void* str_mem = malloc(total);
    memcpy(str_mem, klass_ptr, 8);         // copy klass from original
    memset((char*)str_mem + 8, 0, 8);      // zero monitor
    *(uint32_t*)((char*)str_mem + 16) = len; // string length
    // ASCII → UTF-16LE conversion
    uint16_t* chars = (uint16_t*)((char*)str_mem + 20);
    for (int i = 0; i < len; i++) chars[i] = (uint16_t)(unsigned char)cstr[i];
    chars[len] = 0;
    return str_mem;
}
```

**Known issue**: Works for pause menu text, but shows "?" for song details name. Possible cause: different TMP_Text subclass hierarchy or different encoding expectations in StandardLevelDetailViewController.

### Cell Recycling
Table views reuse cells. The same `TextMeshProUGUI*` pointer may display different songs. Must re-track pointers each time `SetDataFromLevelAsync` fires.

## Hook Call Pattern (v0.8034 Test Data)

| Call Range | Context | Notes |
|------------|---------|-------|
| #1–#15 | Plugin startup | Menu text, buttons |
| #15–#200 | Song list navigation | Scrolling through packs |
| #200–#270 | Rolling Stones pack selected | "The Rolling Stones" artist matches, "Start Me Up" name matches |
| #270–#320 | Song selected, detail view | Replacements fire but "?" appears for name |

**17 total replacements** in a typical session (all 14 artist + 3 song name matches).

## Risk Assessment (UPDATED)

| Risk | Likelihood | Impact | Status |
|------|------------|--------|--------|
| `set_text` is inlined | Low | High | ✅ Not inlined — virtual method works |
| DetourMode crash | ~~Medium~~ | High | ✅ **RESOLVED**: Use x64, NOT x32 |
| Module not found | High | High | ✅ **RESOLVED**: Defer to open_hook(), retry |
| SIGSEGV from invalid pointers | High | High | ✅ **RESOLVED**: Signal handler protection |
| High call frequency | Medium | Low | ✅ Fine — fast pointer comparison + branch |
| Cell recycling breaks tracking | High | Medium | Phase 2 — re-track on SetDataFromLevelAsync |
| String layout mismatch | Medium | Medium | ⚠️ Song details show "?" — needs investigation |
| malloc in hook callback | Low | Medium | Works but may need IL2CPP GC allocation |

## Related

- [[memory-injection-addressables-bypass]] — Previous approach (DEAD END)
- [[plugin-architecture]] — Plugin build system, hook system
- [[il2cpp-dump-mode-selector-hook]] — Previous IL2CPP hook experiments (inlining, mprotect issues)
- [[feature-flags]] — `enable_song_metadata_modification` flag gates this feature
