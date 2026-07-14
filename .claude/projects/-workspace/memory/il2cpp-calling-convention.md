---
name: il2cpp-calling-convention
description: IL2CPP on PS4 uses MS x64 calling convention; C hooks must use __attribute__((ms_abi)) to match
metadata:
  type: reference
---

# IL2CPP Calling Convention on PS4

IL2CPP (v31) on PS4 generates native code using the **Microsoft x64 calling convention**:
- RCX = `this` (1st arg)
- RDX = 2nd arg
- R8  = 3rd arg
- R9  = 4th arg
- Stack = 5th arg+

The native C/C++ toolchain on PS4/FreeBSD defaults to **System V AMD64**:
- RDI = 1st arg
- RSI = 2nd arg
- RDX = 3rd arg
- RCX = 4th arg
- R8  = 5th arg
- R9  = 6th arg
- Stack = 7th arg+

## The Crash

When `[[Detour]]` patches an IL2CPP method's bytes and jumps to a C hook function, the jump preserves the **register state from the IL2CPP caller** (MS x64: RCX=this, RDX=arg1, ...). But the C hook function's prologue reads arguments from **SysV registers** (RDI=this, RSI=arg1, ...). Since RDI and RSI were not set by the MS x64 caller, they contain garbage → `this` and `level` are corrupted → CE-34878-0 crash.

## The Fix: `__attribute__((ms_abi))`

Clang on PS4/FreeBSD supports `__attribute__((ms_abi))` on function declarations. This tells the compiler to generate function prologue/epilogue and argument reads using the **MS x64 convention** instead of SysV.

```cpp
static void* __attribute__((ms_abi)) get_preview_detour(void* _this);
static void  __attribute__((ms_abi)) set_content_detour(void* _this, void* level, int mask, ...);
```

With `ms_abi`:
- The function reads `_this` from **RCX** (matches IL2CPP's RCX=this)
- Returns via RAX (same in both conventions)
- Saves/restores MS x64 non-volatile registers (RBX, RBP, RSI, RDI, R12-R15), not SysV's list
- Stack unwinding uses MS x64 rules

## Calling the Original: Use `TrampolinePtr`

`Detour_Stub` uses SysV convention internally and will pass wrong registers. Instead, call via `TrampolinePtr` with an ms_abi function pointer:

```cpp
typedef void __attribute__((ms_abi)) (*orig_t)(void*, void*, int, ...);
((orig_t)(Detour_hook_xxx.TrampolinePtr))(_this, arg1, arg2, ...);
```

## Alternative: Read Field Directly

For `get_preview` the original simply returns `this._previewDifficultyBeatmapSets`. We can read the field at offset `0x98` directly, avoiding the need to call the original at all:

```cpp
void* result = *(void**)((char*)_this + 0x98);
```

## Verification

The attribute works on PS4's Clang toolchain (OpenOrbis/FreeBSD). Confirmed in [[experiment-123]].

**Related:** [[project-summary-update-rule]] (version increment rule), [[beatmap-levelso-field-offsets]]
