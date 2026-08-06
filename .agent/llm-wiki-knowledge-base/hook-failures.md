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
