---
name: il2cpp-calling-convention
description: PS4 IL2CPP uses SysV AMD64 (same as native C) — confirmed by crash testing
metadata:
  type: reference
---

# IL2CPP Calling Convention on PS4

**CORRECTED: PS4 IL2CPP uses SysV AMD64**, NOT MS x64.

## Evidence

1. Hooks WITHOUT `ms_abi` compiled fine and the game launched without crashing during startup (get_preview never fired, possibly inlined)
2. Hooks WITH `__attribute__((ms_abi))` caused the game to crash on ANY song selection → `this` from RCX was garbage
3. This confirms IL2CPP on PS4/FreeBSD uses the **System V AMD64 ABI**, just like native C code compiled by the PS4 toolchain

## Calling Conventions

| Convention | 1st arg | 2nd arg | 3rd arg | 4th arg | 5th arg | 6th arg |
|-----------|---------|---------|---------|---------|---------|---------|
| SysV AMD64 | RDI | RSI | RDX | RCX | R8 | R9 |
| MS x64 | RCX | RDX | R8 | R9 | stack | stack |

## What Works

On PS4, both native C hooks (`open`, `fopen`) and IL2CPP method hooks use the same calling convention (SysV AMD64). This means:

- **For IL2CPP hook functions**: Use DEFAULT C convention. No `ms_abi` needed.
- **For `Detour_Stub`**: The stub function pointer is called with the C convention (SysV), which matches the IL2CPP method's convention. So `Detour_Stub` may work for IL2CPP hooks IF the method's function address is correct.
- **For `TrampolinePtr`**: Can be called directly with default C convention.

## Reading Fields Directly (Recommended)

For `get_previewDifficultyBeatmapSets`, the method simply returns the value of `this._previewDifficultyBeatmapSets` (field at offset `0x98`). There's no need to call the original at all:

```cpp
void* get_preview_detour(void* _this) {
    void* result = *(void**)((char*)_this + 0x98);
    if (!result) return result;
    // ... augment if length == 1 ...
    return new_array;
}
```

This eliminates ALL calling convention concerns because no function is called — just a memory read from the `this` pointer.

## Key Lesson

MS x64 convention is used by IL2CPP on **Windows** platforms. On PS4/FreeBSD, IL2CPP generates code that follows the **platform's native ABI** (SysV AMD64). Always default to SysV AMD64 for PS4, and only try `ms_abi` if you have definitive proof otherwise.

**Related:** [[beatmap-levelso-field-offsets]], [[experiment-123]], [[experiment-124]]
