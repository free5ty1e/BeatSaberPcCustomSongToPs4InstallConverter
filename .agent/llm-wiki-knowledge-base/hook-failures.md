---
name: ps4-hook-instantiation-failures
description: "Lessons learned from failed manual hook installation attempts."
metadata:
  type: knowledge
---

# Failed Experiment: Manual Hook Installation (`mprotect`/`memcpy`)

## Failure Summary
Manual `mprotect` + `memcpy` hook installation on PS4 `libkernel` functions (e.g., `open`) causes an immediate `CE-34878-0` crash on startup.

## Root Causes
1. **Memory Protection Hazards:** `sceKernelMprotect` requires strict alignment and often conflicts with the game's own internal memory management (GC page-protection) if not handled with precise timing.
2. **Redundancy:** The project already utilizes the `GoldHEN_Hook` library which provides a stable, system-validated API for hooking. Manual hooks bypass these protections and are unstable.
3. **Instruction Corruption:** Overwriting function prologues without a proper trampoline leads to corrupted execution flow when the system library is called by the game engine.

## Conclusion
**Never attempt manual jump-based hooks** on core PS4 library functions. Use the provided `GoldHEN_Hook` API exclusively.
[[plugin-architecture]]

## Regression Log (2026-08-06 — Exp 176): v0.8050/v0.8051 Startup Crash

The definitive real-world case: a "cleanup" commit (`e18921b`) rewrote `src/main.cpp` to call
`install_hook((void*)sys_open, (void*)open_hook)` and **re-enabled `src/hooks.cpp` in the
Makefile** (removed from `filter-out src/crt_patch.cpp src/hooks.cpp src/main_printf_backup.cpp`).

- Result: **instant CE-34878-0 at game launch, no plugin notification** — a PS4 reboot + re-jailbreak to recover.
- Adding `sceKernelMprotect` around the `memcpy` (`cb2ed1a`) did **not** fix it — the 12-byte overwrite
  of a live function prologue with no trampoline is fatal regardless of page protection.
- Reverting only the version string was insufficient — the crash lives in the hook architecture.

### Golden Rule for this repo
- `src/hooks.cpp` (manual `find_symbol`/`install_hook` + 12-byte jump) **must remain excluded from
  the build**. The Makefile line that filters it out is load-bearing:
  `CPPFILES := $(filter-out src/crt_patch.cpp src/hooks.cpp src/main_printf_backup.cpp, $(wildcard src/*.cpp))`
- All hooks in the stable plugin use the GoldHEN **Detour API** (`Detour_Construct` +
  `Detour_DetourFunction` with `DetourMode_x64`) from `GoldHEN/Common.h`.
- Stable plugin baseline: **v0.8040** (commit `a8a06f0`). Any future hook change must be tested on
  this base and must never reintroduce a manual `memcpy`/`mprotect` hook.
