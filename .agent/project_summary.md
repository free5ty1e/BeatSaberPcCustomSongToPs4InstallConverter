# Project Summary: Beat Saber PS4 Custom Song Support
**Last Updated:** 2026-06-11
**Current Status:** 📝 v0.36 DEPLOYED — Manifest levelId patch. v0.35 confirmed asset name mismatch (game uses LoadAsset by name). New approach: modify resources.assets to change Start Me Up's levelId from "startmeup" to "100bills". Then when game opens BeatmapLevelsData/100bills, the ORIGINAL 100bills file from /app0/ provides assets named "100bills" — exact match! Re-enabled resources.assets redirect with new v3 patch. AWAITING TEST.

> 📖 **New to this project?** See the [Research Index](../.ai_memory/RESEARCH_INDEX.md) for a complete catalog of all project documents, status, and quick commands.

## The Goal
Enable installation and playback of custom songs on a jailbroken PS4 by patching the game's global song database (`resources.assets`) and redirecting asset loads via a GoldHEN plugin.

## Technical Landscape
- **Game Engine:** Unity 2022.3 (LZ4HAM Compression)
- **Asset Format:** Unity AssetBundles (`.assets`, `.bundle`)
- **Audio Format:** FSB5 (contained within AssetBundles)
- **Environment:** Strictly offline, no Unity PS4 license, FTP is read-only
- **PS4 Info:** GoldHEN jailbreak, FTP on port 2121
- **Beat Saber CUSA ID:** CUSA12878

## Fixed Context
- **PS4 IP:** `192.168.100.117:2121`
- **FTP Credentials:** anonymous (no password)
- **PS4 Firmware:** 9.00
- **GoldHEN versions:** 2.3 / 2.4b16.2
- **Plugin path on PS4:** `/data/GoldHEN/plugins/beat_saber_deluxe.prx`
- **Custom assets path:** `/data/custom/bs_deluxe/`
- **GoldHEN plugin config:** `/data/GoldHEN/plugins.ini` (⚠️ root level, NOT `plugins/` subdirectory)
- **Custom assets deployed:**
  - `resources_patched.assets` (modified manifest)
  - `CustomSong` (test AssetBundle, clone of $100 Bills)

## Experiment Timeline

### Experiment 1: Direct FTP Overwrite
- **Status:** FAILED
- **What we tried:** Modified `resources.assets` and attempted to upload directly to the game's installation directory via FTP.
- **Result:** FTP server rejected writes to the game directory (read-only). Files are also likely checksummed/encrypted.
- **Key insight:** Direct file modification on PS4 is blocked. Need a plugin for redirection.

### Experiment 2: "The First Hijack" (Initial PRX)
- **Status:** FAILED
- **What we tried:**
  - Created "Beat Saber Deluxe" `.sprx` plugin
  - Hooked `sceFileUtilsOpen` with strict path matching (`strcmp`)
  - Redirection table: `resources.assets` -> `/data/custom/bs_deluxe/resources_patched.assets`, `startmeup` -> `/data/custom/bs_deluxe/CustomSong`
  - Compiled using host `clang` targeting `x86_64-pc-linux-gnu` (WRONG target)
  - Manual hook installation using raw `memcpy` into system function bytes (no `mprotect`)
- **Result:** Game played original "Start Me Up". Plugin either not loading or crashing immediately.
- **Key insights:**
  - Host `clang` produces Linux x86_64 ELF, not PS4 PRX - completely invalid binary
  - `memcpy` on code pages without `mprotect` causes segfault
  - Need PS4 target triple: `--target=x86_64-pc-freebsd12-elf`

### Experiment 3: "Logging & Fuzzy Match"
- **Status:** FAILED (no log file created)
- **What we tried:**
  - Changed hook target from `sceFileUtilsOpen` to `open`
  - Added fuzzy matching (`strstr`) instead of strict `strcmp`
  - Added file-based logging to `/data/custom/bs_deluxe/plugin.log`
  - Still compiled with host `clang` target (WRONG)
- **Result:** `/data/custom/bs_deluxe/plugin.log` was never created. Binary was still invalid (Linux ELF, not PS4 PRX).
- **Key insight:** The compiler target must match PS4's FreeBSD-based kernel.

### Experiment 4a: Heartbeat (Initial)
- **Status:** FAILED - no heartbeat.txt
- **What we tried:**
  - Stripped plugin to absolute minimum: zero hooks, zero redirection
  - Only action: write `/data/custom/bs_deluxe/heartbeat.txt` on load
  - Fixed Makefile to use proper OpenOrbis toolchain
  - Installed plugin to `/data/GoldHEN/plugins/`
- **Result:** No `heartbeat.txt` appeared.
- **Root cause identified:** Plugin was not listed in `plugins.ini` (GoldHEN requires explicit registration).

### Experiment 4b: Heartbeat (plugins.ini fix)
- **Status:** FAILED - no heartbeat.txt
- **What we tried:**
  - Added `beat_saber_deluxe.prx` to `plugins.ini` under `[default]` section
- **Result:** Still no `heartbeat.txt`.
- **Root cause identified:** ELF entry point was `0x0` (not set). The linker was not pointing `e_entry` to `module_start`. The PS4 PRX loader likely rejected the module.

### Experiment 4c: Heartbeat (entry point fix) [FAILED]
- **Status:** ❌ FAILED — No heartbeat.txt (2026-06-11)
- **Actual Result:** `heartbeat.txt` did NOT appear. Confirmed via PS4 FTP check.
- **What we tried:**
  - Added `-e module_start` to linker flags in Makefile
  - Verified `e_entry` = `0x53e0` (points to `module_start`)
  - Scoped `plugins.ini` to Beat Saber only: `[CUSA12878]` instead of `[default]`
  - Rebuilt and re-uploaded plugin + `plugins.ini`
- **Expected Result:** `heartbeat.txt` appears in `/data/custom/bs_deluxe/` after boot + game launch
- **Post-hoc analysis:** Even if entry point is correct, `crtlib.o`'s `module_start` only runs the init array — it does NOT call `plugin_main()`, so heartbeat will likely still not appear (see Experiment 4d for root cause).
- **Next step if successes:** Build proper hooking plugin with `mprotect` and `sceFileUtilsOpen` (skipped — 4c failed)
- **Next step if fails:** ⬅️ THIS HAPPENED. Implementing Experiment 4d (constructor fix) — rename `plugin_main` to `__attribute__((constructor))`

### Experiment 4d: Heartbeat (constructor fix) [FAILED]
- **Status:** ❌ FAILED — No heartbeat.txt (2026-06-11)
- **Root cause confirmed:** The heartbeat test (4c) failed exactly as predicted. `crtlib.o`'s `module_start` does NOT call `plugin_main()`.
- **Fix attempted:** Changed `plugin_main()` to `__attribute__((constructor)) void plugin_init()` so crtlib.o's module_start would call it via init array.
- **Binary verification:** Init array size = 8 bytes (1 constructor entry), relocation at 0x8008 points to plugin_init at 0x00c0.
- **Test result:** Even with constructor registered, no heartbeat.txt appeared. This suggests GoldHEN either doesn't call `module_start`, or crtlib.o's module_start doesn't iterate the init array at runtime as expected.
- **Escalation:** Since the init array approach failed, we dropped `crtlib.o` entirely and defined `module_start`/`module_stop` directly (see Experiment 4e).
- **What we did (2026-06-11):**
  - Changed `extern "C" int plugin_main()` to `__attribute__((constructor)) void plugin_init()`
  - Rebuilt and verified: init array size = 8 bytes (1 constructor entry), relocation at 0x8008 points to plugin_init at 0x00c0
  - Entry point unchanged: `-e module_start` → crtlib.o's module_start at 0x53e0
  - Deployed `beat_saber_deluxe.prx` (72416 bytes) to PS4
- **What the analysis found:**
  - Disassembled `/opt/openorbis/OpenOrbis/PS4Toolchain/lib/crtlib.o` and found `module_start` at offset 0x00
  - `module_start` only iterates the `__init_array` (calls `__attribute__((constructor))` functions), then returns 0
  - It NEVER calls any function named `plugin_main()`
  - Our `main.cpp` defines `extern "C" int plugin_main()` which is **never executed**
  - This explains why no heartbeat.txt has ever appeared — the plugin loads (returns 0), but our code never runs
- **Fix applied (2026-06-11):** Changed `plugin_main()` to a constructor function:
  ```cpp
  __attribute__((constructor))
  void plugin_init() {
      FILE* f = fopen("/data/custom/bs_deluxe/heartbeat.txt", "w");
      if (f) {
          fprintf(f, "Heartbeat: Plugin Loaded Successfully!\n");
          fclose(f);
      }
  }
  ```
  This way `crtlib.o`'s `module_start` will call it via the init array iteration.
  - **Verify:** readelf shows INIT_ARRAY size=8, relocation at 0x8008 → plugin_init at 0x00c0
- **Alternative approach (IMPLEMENTED):** Dropped `crtlib.o` entirely, defined `module_start`/`module_stop` ourselves following RB4DX pattern (see Experiment 4e).

### Experiment 4e: Direct module_start (drop crtlib.o) [FAILED]
- **Status:** ❌ FAILED — No heartbeat.txt (2026-06-11)
- **Why:** Both the entry point fix (4c) and constructor approach (4d) failed to produce a heartbeat. This suggests GoldHEN might not call crtlib.o's `module_start` at all, or the init array doesn't fire as expected. By dropping crtlib.o entirely and defining `module_start` directly as the ELF entry point, we remove all indirection.
- **What we did:**
  - Removed `$(TOOLCHAIN)/lib/crtlib.o` from the Makefile's LDFLAGS
  - Created `src/crt_patch.cpp` to provide the PS4-specific data sections that `create-fself` requires:
    - `.data.sce_module_param` (24 bytes) — module param structure with proper magic/flags
    - `.data` — `__dso_handle` and `_sceLibc` (null init)
    - `_init`/`_fini` stubs (empty, matching crtlib.o's behavior)
  - Rewrote `main.cpp` to define `extern "C" int module_start(size_t argc, const void *args)` directly with the heartbeat code
  - ELF entry point is now 0xe0 (our `module_start`), not crtlib.o's 0x53e0
  - PRX file: 88576 bytes, built and deployed
- **Binary verification:**
  - Entry point: `0xe0` (our module_start at .text+0xe0) ✓
  - `module_start` at 0xe0 (GLOBAL DEFAULT, 85 bytes) ✓
  - `module_stop` at 0x140 (GLOBAL DEFAULT, 16 bytes) ✓
  - `.data.sce_module_param` at 0x10000 (24 bytes) ✓
  - `_init` at 0x20 (6 bytes), `_fini` at 0x30 (6 bytes) — stubs ✓
  - No crtlib.o symbols in binary ✓
  - `create-fself` completed without panic ✓
- **Test result:** No heartbeat.txt appeared. GoldHEN does NOT appear to call the ELF entry point (module_start) for our PRX.
- **Next step (IMPLEMENTED):** Changed entry point to `_init` instead of `module_start` (like RB4DX), see Experiment 4f.

### Experiment 4f: _init entry point (matching RB4DX pattern) [CURRENT]
- **Status:** 🔄 DEPLOYED — awaiting test (2026-06-11)
- **Why:** Three approaches (4c entry point fix, 4d constructor, 4e direct module_start) all failed to produce a heartbeat. RB4DX (a working GoldHEN plugin) uses `-e _init` as its entry point — not `module_start`. This suggests GoldHEN specifically calls `_init` when loading a plugin, regardless of the ELF header's entry address.
- **What we did:**
  - Changed Makefile from `-e module_start` to `-e _init`
  - Moved heartbeat code from `module_start` (in main.cpp) into `_init` (in crt_patch.cpp)
  - `_init` now writes heartbeat.txt then calls `module_start()` for any future plugin initialization
  - `_fini` calls `module_stop()` for cleanup
  - `module_start`/`module_stop` remain in main.cpp as clean stubs
- **Binary verification:**
  - Entry point: `0x20` (our _init at .text+0x20) ✓
  - `_init` at 0x20 (87 bytes — heartbeat + call to module_start) ✓
  - `_fini` at 0x80 (18 bytes — calls module_stop) ✓
  - `module_start` at 0x0140 (16 bytes — clean stub) ✓
  - `module_stop` at 0x0150 (16 bytes — clean stub) ✓
  - `.data.sce_module_param` at 0x10000 (24 bytes) ✓
  - PRX file: 95784 bytes, built and deployed ✓
- **⚠️ CRITICAL FORMAT FIX (2026-06-11):** All prior experiments deployed the WRONG file format.
  - `create-fself` produces TWO outputs:
    1. `--lib=<name>.prx` → **fself wrapper** (starts with SCE magic `4f 15 3d 1d`) ❌ — was being deployed
    2. `-out=<name>.oelf` → **signed ELF** (starts with ELF magic `7f 45 4c 46`, e_type=0xfe18) ✅ — GoldHEN expects this
  - The deployed RB4DX PRX on the PS4 IS a signed ELF (`.oelf`), NOT the fself wrapper
  - **Fix:** Changed Makefile to `cp obj/beat_saber_deluxe.oelf beat_saber_deluxe.prx`, deploying the signed ELF as the .prx
  - All prior experiments had correct code but wrong container format
- **🔄 PATH PROBE (2026-06-11):** After format fix still no heartbeat. Hypothesis: game process lacks write permission to `/data/custom/bs_deluxe/`. Updated `_init()` in crt_patch.cpp to probe **14 candidate paths** across the PS4 filesystem:
  - `/data/`, `/data/cache0001/`, `/data/GoldHEN/`, `/data/PS4Xplorer/`, `/data/sce_logs/`
  - `/tmp/`, `/user/temp/`, `/user/data/`, `/user/savedata/`, `/user/settings/`
  - `/mnt/usb0/`, `/mnt/usb1/`, `/mnt/ext0/` (USB drive)
  - Each path gets fopen() with "w" — success/failure recorded with errno
  - First working path gets a full report table of all 14 attempts
  - USB drive connected by user for guaranteed writable target
- **🔧 STRUCTURAL FIXES (2026-06-11):** Deep comparison with working RB4DX PRX revealed **five root causes** preventing _init from being called:
  1. **Wrong container format** — deployed fself wrapper instead of signed ELF `.oelf`
  2. **TLS segment** — Linking against `-lc` (musl) pulled in `.tbss.__musl_current_locale`, creating PT_TLS. **Fix:** Changed to `-lSceLibcInternal -lkernel`.
  3. **Duplicate LOAD segment** — Original `link.x` placed `.data.sce_module_param`, `.data`, `.bss` in separate sections, causing two identical LOAD segments at same vaddr. **Fix:** Merged data sections in local `link.x`.
  4. **Wrong plugins.ini path** — Deployed to `/data/GoldHEN/plugins/plugins.ini` but GoldHEN reads `/data/GoldHEN/plugins.ini` (root). **Fix:** Deploy to root path.
  5. **⚠️ Module param flags bit 32** — Our `.flags = 0x0000000100000051` had bit 32 (exports) set; RB4DX has `0x0000000001000051` (bit 32 clear). `create-fself` adds bit 24 (PRX flag). **Fix:** Set `.flags = 0x0000000000000051` (create-fself adds PRX bit).
- **Current state:** All five fixes applied + plugin added to [default] section. PRX has matching module param, 7 PHDRs, no TLS, no duplicate LOAD, signed ELF.
- **Expected result:** GoldHEN loads the plugin and calls `_init`. One or more heartbeat files appear.
- **If fails (after all 5 fixes + [default]):** Plugin structure now matches RB4DX completely. Only remaining difference: RB4DX uses GoldHEN SDK's `crtprx.o` and `HOOK64()` macros. Next step: install GoldHEN SDK and build using `crtprx.o` + GoldHEN HOOK system.

### Experiment 4g: GoldHEN SDK crtprx.o [CURRENT]
- **Status:** 🔄 DEPLOYED — awaiting test (2026-06-11)
- **Why:** After all 5 structural fixes + correct plugins.ini path, `_init` was still not called. The remaining difference with RB4DX was the CRT — RB4DX uses GoldHEN SDK's `crtprx.o`, we used a custom CRT replacement (`crt_patch.cpp`). This build uses the exact same CRT as RB4DX.
- **What we did:**
  - Installed GoldHEN Plugin SDK from https://github.com/GoldHEN/GoldHEN_Plugins_SDK
  - Built `crtprx.o` and `libGoldHEN_Hook.a` from SDK source
  - Installed SDK headers and library to OpenOrbis toolchain
  - Replaced `crt_patch.cpp` with `crtprx.o` in the build (`$(TOOLCHAIN)/lib/crtprx.o` linked before our `.o` files)
  - Simplified `main.cpp`: `module_start` now contains the heartbeat code (crtprx.o's `_init` calls `module_start`)
  - Switched to **PS4 notification API** (`sceKernelSendNotificationRequest()`) for heartbeat detection — shows on-screen popup, bypasses file system permissions
  - Also kept `fopen()` file write attempt as fallback evidence
  - Added section header stripping post-processing (zeroed `e_shoff`, `e_shentsize`, `e_shnum`, `e_shstrndx` in ELF header) to match RB4DX's no-section-headers format
  - Updated libraries to match RB4DX exactly: `LIBS := -lGoldHEN_Hook -lkernel -lSceLibcInternal -lSceSysmodule -lScePad`
  - Added `sys_sdk_proc_info()` call in `module_start` to force `libGoldHEN_Hook.a` static code into the PRX
  - Added `attr_public` visibility attribute to `module_start`/`module_stop`
  - Added plugin metadata exports (`g_pluginName`, `g_pluginDesc`, `g_pluginAuth`, `g_pluginVersion`) matching RB4DX pattern
  - Kept `-e _init` entry point and our local `link.x`
- **🔍 DIAGNOSTIC TEST (2026-06-11):** After all structural fixes matched RB4DX but plugin still didn't load, added our plugin to [CUSA02084] (RB4's CUSA — known working). If plugin loads here when launching RB4, the PRX is correct and the issue is CUSA12878 or Beat Saber's process. If it still doesn't load, the PRX itself is the problem.
- **Binary verification:**
  - Entry point: `0x20` (crtprx.o's _init) ✅
  - `_init` at 0x20 (35 bytes — calls module_start) ✅
  - `module_start` at 0x0120 (103 bytes — writes heartbeat) ✅
  - `_sceProcessParam` at 0x10000 (module param from crtprx.o) ✅
  - Module param flags: `0x0000000001000051` (matches RB4DX) ✅
  - 7 program headers (matches RB4DX) ✅
  - PRX: 86160 bytes ✅
- **🔍 DIAGNOSTIC TEST — Expected result:** If our plugin is valid, launching RB4 will show "BS Deluxe: SDK Plugin Loaded!" notification (alongside RB4DX's usual notification). If no notification appears, our PRX is the problem despite all structural fixes.
- **🔬 ORDER TEST RESULTS (2026-06-11):** Put our PRX FIRST in [CUSA02084] (before RB4DX). When user launched RB4, only RB4DX notification appeared. This proves:
  1. ✅ GoldHEN processes ALL entries per section sequentially — our entry was attempted
  2. ✅ GoldHEN then moved to the next entry (RB4DX) when ours failed — confirming PRX attempted but rejected
  3. ❌ Our PRX binary **fails PS4 module validation** at load time — not a path/filename issue
  4. ❌ Not a CUSA scoping issue — the same [CUSA02084] that loads RB4DX rejected ours
- **🧪 FSELF FORMAT TEST (2026-06-11):** Deployed the `--lib` output (fself wrapper, SCE magic `4f 15 3d 1d`) instead of signed ELF. All working plugins on PS4 (game_patch.prx, no_share_watermark.prx, RB4DX) are signed ELF format (`7f 45 4c 46`). Unlikely to work but tested for completeness.
- **💡 KEY INSIGHT:** Our PRX now matches RB4DX in ALL observable aspects (CRT, format, module param, program headers, libraries, exports) but the PS4's `sys_dynlib_load_prx()` still rejects it. The remaining likely cause is the `create-fself` tool version producing incompatible **SCE authentication data** (NIDs, digests, or signing format). Working plugins on the PS4 were built with a different toolchain version (dated Dec 2023 or earlier via GoldHEN devs).
- **System info:** GoldHEN 2.3 / 2.4b16.2, PS4 firmware 9.00

### Diagnostic Test Log (2026-06-12)

| # | Test | What changed | Result | Key Learning |
|---|------|-------------|--------|--------------|
| 1 | **CUSA scoping** | Moved plugin to [CUSA02084] (RB4's section, known working) | ❌ No notification | Issue is not CUSA scoping — same section that loads RB4DX rejects ours |
| 2 | **Order test** | Put our PRX FIRST in [CUSA02084], RB4DX second | ❌ RB4DX at position 2 loaded | GoldHEN processes entries sequentially; our PRX fails loading |
| 3 | **Copy test** | Deployed working RB4DX PRX at our path (filename = beat_saber_deluxe.prx) | ❌ RB4DX at position 2 loaded | RB4DX identical binary at our path didn't load (possible FTP corruption or duplicate detection) |
| 4 | **ptype: system_dynlib** | `create-fself -ptype system_dynlib (0x9)` | ❌ No notification | ptype change didn't help |
| 5 | **ptype: fake** | `create-fself -ptype fake (0x1)` (original make_fself.py default) | ❌ No notification | ptype not the issue |
| 6 | **Minimal PRX** | Zero library imports, module_start returns 0, no notification code | ❌ RB4DX at position 2 loaded | Even empty PRX fails — issue is not with our code/imports |
| 7 | **create-fself v1.3** | Built create-fself from source at tag v1.3 (changelog: "Fixed various miscalculation bugs") | ❌ Still failed | Bugs may persist in v1.3, or issue is not create-fself version |
| 8 | **Module param segment fix** | Reverted to original toolchain link.x (no merged data sections). LOOS+0x1000002 filesz = 0x18 (matches RB4DX) instead of 0x50 | ❌ Still failed | Module param segment size was correct but not the root cause |
| 9 | **Control test** | REMOVED RB4DX entirely from ALL plugins.ini sections | ✅ **RB4DX notification DISAPPEARED** | **We control plugins.ini. GoldHEN reads our file. All prior tests have been valid.** |
| 10 | **FSELF format** | Deployed `--lib` output (FSELF wrapper, SCE magic `4f 15 3d 1d`) instead of OELF signed ELF | ✅ **LOADED! "BS Deluxe: SDK Plugin Loaded!" notification appeared!** | **GoldHEN expects FSELF format, not OELF!** All prior tests deployed wrong format. |
| 11 | **Notification causes crash** | FSELF with notification + fopen. Works but crashes BS | ❌ Game crashed after notification | Notification + fopen causes crash. Not clear which — both are in module_start. |
| 12 | **Path probe (no notification)** | FSELF with path probe (fopen/fprintf/fclose), no notification | ❌ Crashed | Similar crash without notification — suggests fopen/fprintf is the real cause, not notification. |
| 13 | **Minimal PRX (empty)** | FSELF, crtprx.o + main.o (just returns 0), no hooks.cpp, no extra libs | ✅ **NO CRASH!** Beat Saber booted to VR screen | Crash isolated to excluded components: hooks.cpp, GoldHEN_Hook, Sysmodule, Pad, or file I/O. |
| 14 | **Build A: fopen-only** (deployed) | Minimal + fopen/fprintf in module_start. No hooks, no GoldHEN_Hook, no Sysmodule/Pad. | ⏳ PENDING | Tests if fopen/fprintf alone causes crash. If yes → theory confirmed (sandbox issue). |

**Summary so far:** We have proven control over plugins.ini. GoldHEN processes our entries sequentially. FSELF format (--lib output) is required — OELF format is rejected. Module loads successfully when deployed as FSELF. Minimal PRX (crtprx.o + return 0) works without crashing. Crash occurs when any file I/O (fopen/fprintf) is called from module_start during early game initialization. Theory: PS4 file system sandbox not yet initialized at plugin load time. RB4DX confirms: uses printf/stat, never fopen, in module_start.

**Command used:**
```bash
objdump -d /opt/openorbis/OpenOrbis/PS4Toolchain/lib/crtlib.o
```

**`module_start` (offset 0x00):**
```assembly
push   %rbp
mov    %rsp,%rbp
sub    $0x20,%rsp
mov    %rdi,-0x8(%rbp)         # save argc
mov    %rsi,-0x10(%rbp)        # save argv
mov    0x0(%rip),%rax          # load __init_array_start
mov    %rax,-0x18(%rbp)
mov    0x0(%rip),%rax          # load __init_array_end
cmp    %rax,-0x18(%rbp)
je     43                      # if equal, skip to return 0
# loop: call each init array function pointer
mov    -0x18(%rbp),%rax
call   *(%rax)
mov    -0x18(%rbp),%rax
add    $0x8,%rax
mov    %rax,-0x18(%rbp)
jmp    1b                      # loop back to compare
# return 0
xor    %eax,%eax
add    $0x20,%rsp
pop    %rbp
ret
```

**Key insight:** `module_start` iterates the `__init_array` (calling `__attribute__((constructor))` functions), then returns 0. It NEVER calls any user function named `plugin_main()` or any other custom symbol. The only way to get user code executed during `module_start` is:
1. Via `__attribute__((constructor))` — added to init array automatically
2. By not using `crtlib.o` at all and defining our own `module_start`

## RB4DX Plugin Architecture Reference
**Analyzed:** 2026-06-11
**Source:** `/workspace/beat-saber-ps4-custom-songs/rb4dx_plugin_source/`
**Pre-built PRX:** `/workspace/rb4dx_repo/_build/GoldHEN/plugins/RB4DX-Plugin.prx`

### Key Differences: Our Plugin vs RB4DX (working GoldHEN plugin)

| Aspect | Beat Saber Deluxe (ours) ❌ | RB4DX (working) ✅ |
|--------|------------------------------|---------------------|
| **Entry point** | `-e _init` ✅ (matches RB4DX) | `-e _init` → GoldHEN SDK's `crtprx.o` |
| **Module entry function** | `int module_start()` in main.cpp ✅ (called from _init) | `int32_t attr_public module_start()` — called by GoldHEN CRT |
| **Module exit function** | `int module_stop()` in main.cpp ✅ (called from _fini) | `int32_t attr_public module_stop()` |
| **CRT** | `crt_patch.cpp` (custom, provides .data.sce_module_param, _init/_fini) ⚠️ not GoldHEN SDK | `$(GH_SDK)/build/crtprx.o` (GoldHEN-specific CRT) |
| **PRX format** | `.oelf` signed ELF (magic `7f 45 4c 46`, e_type=0xfe18) ✅ fixed 2026-06-11 | `.oelf` signed ELF (same format) |
| **Hook system** | Custom `memcpy` (no mprotect, dangerous) | GoldHEN SDK `HOOK` macros with mprotect |
| **Visibility** | No export attributes | `attr_public` = `__attribute__((visibility("default")))` |
| **Libraries** | `-lSceLibcInternal -lkernel` ✅ (no TLS, matches RB4DX) | `-lGoldHEN_Hook -lkernel -lSceLibcInternal -lSceSysmodule -lScePad` |
| **Logging** | `fprintf` to `/data/custom/bs_deluxe/heartbeat.txt` | `klog()` (kernel debug log) via `final_printf` macro |
| **GoldHEN SDK** | Not installed ($GOLDHEN_SDK unset) | Required (`#include <GoldHEN/Common.h>`) |

### RB4DX `module_start` Pattern
```c
#define attr_public __attribute__((visibility("default")))

int32_t attr_public module_start(size_t argc, const void *args)
{
    // 1. Get process info using GoldHEN SDK
    sys_sdk_proc_info(&procInfo);
    
    // 2. Validate title ID / version
    if (strcmp(procInfo.titleid, "CUSA02084") != 0) return 0;
    
    // 3. Get base address (for offset-based hook targets)
    uint64_t base_address = get_base_address();
    
    // 4. Install hooks using GoldHEN SDK macros
    // target = base_address + known_offset (game-version-specific)
    NewFile = (void*)(base_address + 0x00376d40);
    HOOK(NewFile);
    
    return 0;
}
```

### RB4DX Hook Macro Pattern
```c
HOOK_INIT(NewFile);  // declares function pointer + hook metadata

void NewFile_hook(const char* path, FileMode mode) {
    // Check if we want to redirect
    if (file_exists(newpath)) {
        HOOK_CONTINUE(NewFile, void (*)(const char*, FileMode), gamepath, kReadNoArk);
        return;
    }
    HOOK_CONTINUE(NewFile, void (*)(const char*, FileMode), path, mode);
}
```
This macro-based system handles mprotect, trampoline setup, and jump patching automatically.

### RB4DX `_init` Entry Point (from crtprx.o)
- The linker entry point is `_init` (not `module_start`)
- `crtprx.o` provides `_init` which does proper PRX initialization
- `_init` eventually calls the plugin's `module_start()` function
- This is the standard GoldHEN plugin pattern

## Technical Details: Build System

### Makefile structure (OpenOrbis SDK)
The build uses the OpenOrbis PS4 Toolchain at `/opt/openorbis/OpenOrbis/PS4Toolchain/`.

Key build commands (run from `/workspace/beat_saber_deluxe/`):
```bash
# Set toolchain path
export OO_PS4_TOOLCHAIN=/opt/openorbis/OpenOrbis/PS4Toolchain

# Clean and rebuild
make clean && rm -rf obj && make -B

# Verify entry point
readelf -h obj/beat_saber_deluxe.elf | grep Entry

# Verify exported symbol
readelf -s obj/beat_saber_deluxe.elf | grep plugin_main

# Analyze CRT object initialization
objdump -d /opt/openorbis/OpenOrbis/PS4Toolchain/lib/crtlib.o

# List symbols in CRT objects
nm /opt/openorbis/OpenOrbis/PS4Toolchain/lib/crtlib.o
nm /opt/openorbis/OpenOrbis/PS4Toolchain/lib/crt1.o
nm /opt/openorbis/OpenOrbis/PS4Toolchain/lib/crt_dyn.o
```

### Critical compiler flags (Makefile — current OpenOrbis approach)
- **Target triple:** `--target=x86_64-pc-freebsd12-elf` (MUST be this, NOT linux-gnu)
- **Sysroot:** `-isysroot $(OO_PS4_TOOLCHAIN)`
- **Linker:** `ld.lld` with script `$(TOOLCHAIN)/link.x`
- **Entry point:** `-e _init` (CRITICAL — matching RB4DX pattern; GoldHEN calls `_init`, not `module_start`)
- **CRT:** Dropped `$(TOOLCHAIN)/lib/crtlib.o`; custom CRT replacement in `src/crt_patch.cpp`
- **Linker script:** Copied from toolchain to local `link.x` and modified to merge `.data.sce_module_param + .data + .bss` into one output section (eliminates duplicate LOAD PHDR)
- **Libraries:** `-lSceLibcInternal -lkernel` (NOT `-lc -lc++ -lkernel`) — SceLibcInternal avoids musl's TLS dependency
- **Output packaging:** `create-fself -out=<oelf> --lib=<fself>.prx --paid 0x3800000000000011`
  - ⚠️ **FORMAT:** `--lib` produces fself wrapper (SCE magic `4f 15 3d 1d`) — **DO NOT DEPLOY THIS**
  - The `-out` file (signed ELF, magic `7f 45 4c 46`, e_type=0xfe18) is what GoldHEN expects
  - **Fix:** Copy `.oelf` as the deployable `.prx` file:
    ```makefile
    cp obj/beat_saber_deluxe.oelf beat_saber_deluxe.prx
    ```

### RB4DX Build System (GoldHEN SDK approach) — for reference
- **Toolchain:** OpenOrbis + GoldHEN SDK (`$GOLDHEN_SDK` must be set)
- **CRT:** `$(GH_SDK)/build/crtprx.o` (NOT crtlib.o)
- **Entry point:** `-e _init` (NOT module_start)
- **Libraries:** `-lGoldHEN_Hook -lkernel -lSceLibcInternal -lSceSysmodule -lScePad`
- **User function:** Define `module_start(size_t argc, const void *args)` directly with `__attribute__((visibility("default")))`
- **Hook macros:** `HOOK_INIT`, `HOOK`, `HOOK_CONTINUE`, `UNHOOK` (from GoldHEN SDK — handles mprotect automatically)
- **Base address:** Use `sys_sdk_proc_info()` from GoldHEN SDK to get process info + base_address for offset-based hooks
- **Logging:** `final_printf()` macro which wraps `klog()` (kernel debug log — visible via GoldHEN)
- **GoldHEN SDK status on this system:** NOT INSTALLED (`$GOLDHEN_SDK` unset)
  - Install URL: https://github.com/GoldHEN/GoldHEN_Plugins_SDK
  - May need manual installation or we can implement our own hook system

## Workflow: End-to-End Test Procedure

### Phase 1: Development (this environment)
1. Edit source files in `/workspace/beat_saber_deluxe/`
2. Rebuild: `export OO_PS4_TOOLCHAIN=/opt/openorbis/OpenOrbis/PS4Toolchain && make clean && rm -rf obj && make -B`
3. Verify entry point and symbols with `readelf`

### Phase 2: Deploy to PS4
```bash
lftp -u anonymous, <<EOF
open -p 2121 192.168.100.117
put /workspace/beat_saber_deluxe/beat_saber_deluxe.prx -o /data/GoldHEN/plugins/beat_saber_deluxe.prx
put /workspace/plugins.ini -o /data/GoldHEN/plugins.ini
quit
EOF
```

### Phase 3: Test (user on PS4)
⚠️ **No reboot needed** — plugins.ini is solidified. GoldHEN reads plugin updates on game launch.

1. **Deploy** updated PRX + plugins.ini via FTP (Phase 2 above)
2. **Launch Beat Saber** (CUSA12878) or configured game
3. Report:
   - **Notification text** seen on screen (if any)
   - **Did the game crash?** (PS4 may need hard reset if crash occurs)
   - **Did the game reach the "turn on VR headset" screen?** (baseline: plugin loaded without crash)

### Phase 4: Analyze (this environment)
Check for heartbeat or log file:
```bash
lftp -u anonymous, <<EOF
open -p 2121 192.168.100.117
ls /data/custom/bs_deluxe/
# To download a specific log:
# get /data/custom/bs_deluxe/heartbeat.txt -o /workspace/heartbeat.txt
# get /data/custom/bs_deluxe/plugin.log -o /workspace/plugin.log
quit
EOF
```

Check plugin deployment:
```bash
lftp -u anonymous, <<EOF
open -p 2121 192.168.100.117
ls /data/GoldHEN/plugins/
quit
EOF
```

### Phase 5: Iterate (updated with AFR breakthrough — 2026-07-01)
Based on results:
- **FSELF FORMAT BREAKTHROUGH ✅ (2026-06-12):** Deployed `--lib` FSELF wrapper instead of `-out` OELF signed ELF → **notification appeared!** GoldHEN's plugin loader accepts FSELF format (SCE magic `4f 15 3d 1c`) but REJECTS bare OELF signed ELF (ELF magic `7f 45 4c 46`).
- **Jailbreak + file I/O ❌ (v0.21-v0.25):** Jailbreak in module_start destabilizes the game process. Even with raw syscalls (no heap), the game crashes after module_start during normal init. Adding delays, extra syscalls, or mprotect calls doesn't fix the propagation issue. **Jailbreak fundamentally conflicts with game initialization on PS4.**
- **AFR BREAKTHROUGH ✅ (v0.27, 2026-07-01):** GoldHEN's AFR path `/data/GoldHEN/AFR/<TitleID>/` accepts `sceKernelOpen` writes **without jailbreak!** No heap allocation needed. No credential propagation issues. v0.27 confirmed: file written successfully, game runs without crashes. Full log captured at `/workspace/screenshots/afr_log_v27.txt`.
- **Working logging (v0.28):** Combined AFR file logging (`sceKernelOpen`/`sceKernelWrite`/`sceKernelClose`) with Detour hooks for fopen+open. No jailbreak. Only 2 status notifications. AWAITING TEST.
- **Key insight from user research:**
  - `fopen` to `/data/` under sandbox kills the thread (confirmed: v0.21 hard crash)
  - `make PRINTF=1` bypasses variadic stack corruption issues (not our current issue)
  - AFR redirects writes to `/data/GoldHEN/AFR/<TitleID>/` with sandbox bypass
  - `sceKernelOpenFile` (Orbis API) is the proper file I/O mechanism for plugins
  - Thread isolation (ring buffer + background thread) needed for production logging

## File Reference
- `/workspace/beat_saber_deluxe/src/main.cpp` - Plugin entry point (now defines `module_start`/`module_stop` directly, no crtlib.o)
- `/workspace/beat_saber_deluxe/src/crt_patch.cpp` - CRT replacement sections for `create-fself` (`.data.sce_module_param`, `_init`/`_fini` stubs)
- `/workspace/beat_saber_deluxe/src/hooks.cpp` - Hook utilities (`find_symbol`, `install_hook` — naive memcpy, needs mprotect)
- `/workspace/beat_saber_deluxe/include/bs_deluxe.h` - Plugin definitions
- `/workspace/beat_saber_deluxe/include/hooks.h` - Hook function declarations
- `/workspace/beat_saber_deluxe/Makefile` - Build system (no crtlib.o, -e _init entry, produces signed ELF .prx, `-lSceLibcInternal`)
- `/workspace/beat_saber_deluxe/link.x` - Modified linker script (merged data/BSS sections, local copy of toolchain's link.x)
- `/workspace/beat_saber_deluxe/beat_saber_deluxe.prx` - Compiled binary
- `/workspace/plugins.ini` - GoldHEN plugin configuration (deployed to `/data/GoldHEN/plugins.ini` — root level, NOT `plugins/` subdirectory)
- `/workspace/resources_patched.assets` - Modified manifest
- `/workspace/CustomSong` - Test song AssetBundle
- `/workspace/.devcontainer/openorbis/` - OpenOrbis SDK installation
- `/workspace/.agent/project_summary.md` - This file
- `/workspace/setup_claude_zen_devcontainer.sh` - Devcontainer setup script (includes memory symlink step)
- `/workspace/setup_claude_ollama_local_in_devcontainer.sh` - Alternative ollama-based setup script
- `/workspace/beat-saber-ps4-custom-songs/rb4dx_plugin_source/` - **RB4DX plugin source (REFERENCE)** — working GoldHEN plugin
  - `source/main.c` — module_start/stop, HOOK_INIT/HOOK pattern, game-specific offsets
  - `source/plugin_common.c` — base_address detection, file_exists, sys_sdk_proc_info
  - `Makefile` — uses GoldHEN SDK crtprx.o, -e _init, links GoldHEN_Hook
- `/workspace/rb4dx_repo/_build/GoldHEN/plugins/RB4DX-Plugin.prx` - Pre-built RB4DX PRX (reference binary)
- `/opt/openorbis/OpenOrbis/PS4Toolchain/lib/crtlib.o` - OpenOrbis PRX CRT (disassembled 2026-06-11)
  - `module_start` (offset 0x00): saves args, iterates __init_array, returns 0 — does NOT call plugin_main
  - `module_stop` (offset 0x50): returns 0
  - `_init` (offset 0x60): returns 0
  - `_fini` (offset 0x70): returns 0

## 🔥 MAJOR BREAKTHROUGH: AFR File Logging Works!

After 51 experiments over 3 weeks of crashes, we finally have a working file logging mechanism.

### The Problem (Experiments 4-51)
Every attempt to write log files from within the plugin crashed the game:
- `fopen` crashes in `module_start` (heap not initialized)
- Raw `open/write/close` after jailbreak works but game crashes during init
- Jailbreak destabilizes the game process (credential propagation issues)
- Detour hooks without jailbreak are stable but sandbox blocks file writes
- Notifications are unusable (endless spam in VR)
- `klog`/`printf` output goes to kernel log, not accessible via FTP

### The Solution: AFR (Application File Redirector)
GoldHEN includes an AFR system that allows writes to `/data/GoldHEN/AFR/<TitleID>/` paths. The RB4DX plugin uses this pattern (`data:/GoldHEN/AFR/CUSA02084/...`). Key findings:

1. **No jailbreak needed** — AFR paths are accessible under normal game sandbox
2. **No heap allocation** — `sceKernelOpen`/`sceKernelWrite`/`sceKernelClose` are direct kernel syscalls, not libc FILE* operations
3. **No crashes** — v0.27 (AFR write test) ran successfully with zero crashes
4. **Works within hooks** — `log_write()` helper can be called from within Detour hooks without reentrancy issues (since `sceKernelOpen` is a different function from hooked `fopen`/`open`)

### Current State (v0.28)
Combines all proven components:
- ✅ `sceKernelOpen` to `/data/GoldHEN/AFR/CUSA12878/bs_log.txt` for file logging
- ✅ Detour hook for `fopen()` (logging + redirect for resources.assets / CustomSong)
- ✅ Detour hook for `open()` (logging only, silent pass-through)
- ✅ No jailbreak, no mprotect conflicts, no credential propagation issues
- ✅ Only 2 status notifications (no spam)
- ⏳ Awaiting test: does the log capture all file operations? Does the redirect work?

### Log format (when available)
```
=== BS Deluxe v0.28 started ===
fopen+open hooks active, AFR logging OK
open:/dev/urandom
open:/app0/sce_discmap.plt
...
fopen:/app0/Media/resources.assets -> /data/custom/bs_deluxe/resources_patched.assets
fopen:/data/custom/bs_deluxe/CustomSong (if startmeup matched)
...
```

### Master Index
- **[Research Index](../.ai_memory/RESEARCH_INDEX.md)** — **START HERE.** Comprehensive catalog of all project documents with descriptions, status tracking, and quick commands.
- **[Memory Index](../.ai_memory/MEMORY.md)** — Categorized links to all research/planning documents.

### Recent Findings (2026-06-11)
- [crtlib.o module_start analysis](../.ai_memory/beat-saber-ps4-custom-songs/crtlib-o-module-start-analysis.md) — Root cause: plugin_main() never called by CRT
- [RB4DX Plugin Architecture Reference](../.ai_memory/beat-saber-ps4-custom-songs/rb4dx-plugin-architecture-reference.md) — Working GoldHEN plugin pattern reference
- [Experiment 4d: Constructor Fix](../.ai_memory/beat-saber-ps4-custom-songs/experiment-4d-constructor-fix.md) — FAILED: constructor didn't fire either
- [Experiment 4e: Direct module_start](../.ai_memory/beat-saber-ps4-custom-songs/experiment-4e-direct-module-start.md) — Dropped crtlib.o, defined module_start directly. FAILED.
- [Experiment 4f: _init entry point](../.ai_memory/beat-saber-ps4-custom-songs/experiment-4f-init-entry-point.md) — Changed entry to _init like RB4DX. DEPLOYED.
- [PRX Format Discovery] — GoldHEN expects `.oelf` (signed ELF), not fself wrapper. All prior experiments deployed wrong format. FIXED in Makefile.
- [⚠️ plugins.ini Path Discovery](../.ai_memory/beat-saber-ps4-custom-songs/plugins-ini-path-discovery.md) — **CRITICAL:** GoldHEN reads root `/data/GoldHEN/plugins.ini`, not `plugins/`. All prior tests were never registered. FIXED.
- [Module param flags fix] — Bit 32 (exports) was set in our SceModuleParam flags. RB4DX has it clear. Fixed by setting `.flags = 0x0000000000000051`.
- [Experiment 4g: GoldHEN SDK crtprx.o] — First build using GoldHEN SDK CRT (matching RB4DX exactly). DEPLOYED 2026-06-11.

## Key Technical Decisions
1. **Plugin over PKG:** `.prx` plugin via GoldHEN chosen for rapid iteration vs full PKG rebuild
2. **Sacrifice Song:** "Start Me Up" (Rolling Stones) selected as the hijack target
3. **Sacrifice Replacement:** `CustomSong` bundle (clone of $100 Bills) as test replacement
4. **Toolchain:** OpenOrbis SDK for cross-compilation (provides PS4 headers, linker script, `create-fself`)
5. **CUSA scoping:** Plugin registered under `[CUSA12878]` (Beat Saber) so it only loads for this game
6. **crtlib.o limitation (discovered 2026-06-11):** OpenOrbis's `crtlib.o` provides a `module_start` that only runs the init array — it does NOT call any user-defined `plugin_main()`. All user init code must be `__attribute__((constructor))` or we must drop crtlib.o and define `module_start` ourselves. Long-term, the RB4DX pattern (GoldHEN SDK's `crtprx.o` + `-e _init` + custom `module_start`) is the correct approach.
7. **GoldHEN SDK not installed:** Future work may require installing GoldHEN_Plugins_SDK for proper `HOOK` macros with `mprotect` support. Until then, we can implement our own mprotect-based hooking.
8. **⚠️ PRX format (discovered 2026-06-11):** GoldHEN expects the **signed ELF (`.oelf`)** from `create-fself`, NOT the fself wrapper (`--lib` output). The deployed RB4DX plugin on the PS4 has ELF magic `7f 45 4c 46` with e_type=0xfe18, not SCE fself magic `4f 15 3d 1d`. All experiments 4a-4f deployed the wrong format until this fix. **Makefile updated:** `cp obj/*.oelf $(TARGET)`
9. **⚠️ TLS segment (discovered 2026-06-11):** Linking against `-lc` (musl) pulls in `__musl_current_locale` via `.tbss`, creating a PT_TLS program header. The PS4/FreeBSD kernel likely rejects PRX modules with TLS segments. **Fix:** Link against `-lSceLibcInternal` instead of `-lc -lc++`.
10. **⚠️ Duplicate LOAD PHDR (discovered 2026-06-11):** The toolchain's `link.x` linker script places `.data.sce_module_param`, `.data`, and `.bss` in separate output sections, causing the linker to emit two identical LOAD segments at the same vaddr. **Fix:** Copied `link.x` to project, merged data/BSS into one output section.
11. **⚠️ WRONG plugins.ini path (discovered 2026-06-11):** GoldHEN reads `/data/GoldHEN/plugins.ini` (root level), NOT `/data/GoldHEN/plugins/plugins.ini` (subdirectory). All experiments 4b-4f deployed to the wrong path and were never registered. **Fix:** Deploy `plugins.ini` to root path, preserving existing RB4DX entries.
12. **⚠️ Module param flags (discovered 2026-06-11):** Our SceModuleParam `.flags = 0x0000000100000051` set bit 32 (exports flag), but RB4DX has `0x0000000001000051` (bit 32 clear). The PS4 loader may reject PRX modules that falsely claim exports. `create-fself` adds bit 24 (PRX flag) automatically. **Fix:** Set `.flags = 0x0000000000000051`.
13. **GoldHEN SDK installed (2026-06-11):** Installed GoldHEN Plugin SDK from GitHub. Built `crtprx.o` and `libGoldHEN_Hook.a`. Modified plugin to use `crtprx.o` as CRT (matching RB4DX exactly).
14. **Full RB4DX library set (2026-06-11):** Updated to link against the same libraries as RB4DX: `-lGoldHEN_Hook -lkernel -lSceLibcInternal -lSceSysmodule -lScePad`. Added `sys_sdk_proc_info()` call to force `libGoldHEN_Hook.a` into the final PRX (static library only included when referenced). PRX now includes GoldHEN SDK symbols.
15. **🔴 create-fself SCE authentication (2026-06-11):** After matching RB4DX in ALL structural aspects, our PRX still fails `sys_dynlib_load_prx()` validation. Order test confirmed GoldHEN attempts our entry but rejects it, continuing to the next. The remaining difference is likely the SCE authentication data generated by our `create-fself` tool (from OpenOrbis toolchain). Working PS4 plugins (game_patch.prx, no_share_watermark.prx, RB4DX) were built with potentially different toolchains. GoldHEN 2.3/2.4b16.2 on PS4 firmware 9.00.
