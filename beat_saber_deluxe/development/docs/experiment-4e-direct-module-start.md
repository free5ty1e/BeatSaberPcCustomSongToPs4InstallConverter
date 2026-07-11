---
name: experiment-4e-direct-module-start
description: "Experiment 4e — dropped crtlib.o, defined module_start/module_stop directly with CRT replacement sections"
metadata:
  type: reference
---

## Experiment 4e: Direct module_start (drop crtlib.o)

**Date:** 2026-06-11
**Status:** Deployed, awaiting test

**What was wrong:** Both the entry point fix (4c) and constructor approach (4d) failed to produce a heartbeat. Dropping crtlib.o and defining module_start directly removes all indirection.

**Changes:**
1. Removed `$(TOOLCHAIN)/lib/crtlib.o` from Makefile LDFLAGS
2. Created `src/crt_patch.cpp` with PS4-specific data sections (`_sce_module_param`, `_init`/`_fini` stubs)
3. Changed `main.cpp` to define `extern "C" int module_start(size_t argc, const void *args)` directly

**Binary verification:**
- Entry point: 0xe0 (our module_start at .text+0xe0)
- module_start at 0xe0 (GLOBAL DEFAULT, 85 bytes)
- module_stop at 0x140 (GLOBAL DEFAULT, 16 bytes)
- .data.sce_module_param at 0x10000 (24 bytes)
- No crtlib.o symbols in binary
- create-fself completed without panic
- PRX: 88576 bytes

**See also:** [[crtlib-o-module-start-analysis]] for root cause of why crtlib.o wasn't calling our code.
