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

**⚠️ CRITICAL FORMAT FIX (deployed alongside 4f):**
All prior experiments deployed the WRONG file format. `create-fself` produces two outputs:
- `--lib=<name>.prx` → **fself wrapper** (starts with SCE magic `4f 15 3d 1d`) ❌ — was being deployed
- `-out=<name>.oelf` → **signed ELF** (starts with ELF magic `7f 45 4c 46`, e_type=0xfe18) ✅ — GoldHEN expects this

The deployed RB4DX PRX on the PS4 IS a signed ELF (`.oelf`), NOT the fself wrapper. **Fix:** Changed Makefile to `cp obj/beat_saber_deluxe.oelf beat_saber_deluxe.prx`.

**Binary verification:**
- Entry point: 0x20 (_init at .text+0x20)
- _init at 0x20 (87 bytes, includes heartbeat + module_start call)
- _fini at 0x80 (18 bytes, calls module_stop)
- module_start at 0x140 (clean stub)
- module_stop at 0x150 (clean stub)
- PRX: 95784 bytes (signed ELF format ✅)
- **7 program headers** (matches RB4DX) ✅
- **No TLS segment** ✅ (switched from `-lc` musl to `-lSceLibcInternal`)
- **No duplicate LOAD** ✅ (merged data/BSS sections in custom `link.x`)
- **Libraries:** `-lSceLibcInternal -lkernel`

**Three root causes discovered (2026-06-11):**
1. Wrong container format (deployed fself wrapper instead of signed ELF `.oelf`)
2. TLS segment from musl libc (`-lc` pulled in `.tbss.__musl_current_locale`, creating PT_TLS)
3. Duplicate LOAD program header (linker script placed data sections separately)

**See also:**
- [[rb4dx-plugin-architecture-reference]] for the working GoldHEN plugin pattern
- [[experiment-4e-direct-module-start]] for prior approach
