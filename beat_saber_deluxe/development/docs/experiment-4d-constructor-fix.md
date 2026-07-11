---
name: experiment-4d-constructor-fix
description: "Experiment 4d — changed plugin_main() to __attribute__((constructor)) so crtlib.o calls it via init array"
metadata:
  type: reference
---

## Experiment 4d: Constructor Fix

**Date:** 2026-06-11
**Status:** Deployed, awaiting test

**What was wrong:** `crtlib.o`'s `module_start` only iterates the init array and returns 0. Our `plugin_main()` was never called.

**Fix applied:** Changed `extern "C" int plugin_main()` to `__attribute__((constructor)) void plugin_init()` in `/workspace/beat_saber_deluxe/src/main.cpp`.

**Verification:**
- `INIT_ARRAY` size = 8 bytes (1 entry)
- Init array relocation at 0x8008 → `plugin_init` at 0x00c0
- Entry point unchanged: crtlib.o's `module_start` at 0x53e0
- PRX file: 72416 bytes, deployed to `/data/GoldHEN/plugins/beat_saber_deluxe.prx`

**Expected result:** After reboot + GoldHEN + game launch, `/data/custom/bs_deluxe/heartbeat.txt` should appear.

**If fails:** Drop crtlib.o, define module_start directly, or install GoldHEN SDK and use crtprx.o + -e _init pattern.

**How to apply:** Modify `main.cpp` to use `__attribute__((constructor))` on the init function. Rebuild with `make clean && rm -rf obj && make -B`. See [[crtlib-o-module-start-analysis]] for root cause.
