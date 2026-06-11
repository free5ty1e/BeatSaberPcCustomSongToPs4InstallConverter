---
name: experiment-4f-init-entry-point
description: "Experiment 4f — changed entry point from module_start to _init, moved heartbeat into _init, matching RB4DX pattern"
metadata:
  type: reference
---

## Experiment 4f: _init entry point

**Date:** 2026-06-11
**Status:** Deployed, awaiting test

**What was wrong:** Three approaches (4c entry point fix, 4d constructor, 4e direct module_start) all failed. RB4DX uses `-e _init` — GoldHEN may specifically call `_init` rather than the ELF entry point.

**Changes:**
1. Changed Makefile from `-e module_start` to `-e _init`
2. Moved heartbeat code from `module_start` (main.cpp) into `_init` (crt_patch.cpp)
3. `_init` writes heartbeat.txt and calls `module_start()`
4. `_fini` calls `module_stop()`

**Binary verification:**
- Entry point: 0x20 (_init at .text+0x20)
- _init at 0x20 (87 bytes, includes heartbeat + module_start call)
- _fini at 0x80 (18 bytes, calls module_stop)
- module_start at 0x140 (clean stub)
- module_stop at 0x150 (clean stub)
- PRX: 88576 bytes

**See also:** [[rb4dx-plugin-architecture-reference]] for the working GoldHEN plugin pattern.
