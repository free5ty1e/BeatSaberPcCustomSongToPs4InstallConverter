# Project Summary: Beat Saber PS4 Custom Song Support
**Last Updated:** 2026-06-11
**Current Status:** Experiment 4d ❌ FAILED | Experiment 4e (direct module_start) 🔄 DEPLOYED — awaiting test

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
- **Plugin path on PS4:** `/data/GoldHEN/plugins/beat_saber_deluxe.prx`
- **Custom assets path:** `/data/custom/bs_deluxe/`
- **GoldHEN plugin config:** `/data/GoldHEN/plugins/plugins.ini`
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

### Experiment 4e: Direct module_start (drop crtlib.o) [CURRENT]
- **Status:** 🔄 DEPLOYED — awaiting test (2026-06-11)
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
- **Expected result:** `heartbeat.txt` appears in `/data/custom/bs_deluxe/` after PS4 reboot + GoldHEN + game launch.
- **If fails:** The issue is not with our plugin code but with GoldHEN plugin loading itself. Possible causes:
  1. The `.prx` (fself) format generated by `create-fself` is incompatible with GoldHEN
  2. GoldHEN's `[CUSA12878]` section in plugins.ini isn't triggering for Beat Saber
  3. The PRX needs to be signed differently
  4. GoldHEN expects `_init` as entry point (like RB4DX's `crtprx.o`), not `module_start`
  Next step: Try with `-e _init` entry point or install GoldHEN SDK and use `crtprx.o` directly.

### crtlib.o Disassembly Analysis
**Analyzed:** 2026-06-11
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
| **Entry point** | `-e module_start` → `crtlib.o`'s default (just runs constructors) | `-e _init` → GoldHEN SDK's `crtprx.o` |
| **Module entry function** | `int plugin_main()` — never called by crtlib.o | `int32_t attr_public module_start(size_t argc, const void *args)` — called by GoldHEN CRT |
| **Module exit function** | (none) | `int32_t attr_public module_stop(size_t argc, const void *args)` |
| **CRT** | `crtlib.o` (mini CRT: runs init array, returns 0) | `$(GH_SDK)/build/crtprx.o` (GoldHEN-specific CRT) |
| **Hook system** | Custom `memcpy` (no mprotect, dangerous) | GoldHEN SDK `HOOK` macros (`HOOK_INIT`, `HOOK`, `HOOK_CONTINUE`) with mprotect |
| **Visibility** | No export attributes | `attr_public` = `__attribute__((visibility("default")))` |
| **Libraries** | `-lc -lc++ -lkernel` | `-lGoldHEN_Hook -lkernel -lSceLibcInternal -lSceSysmodule -lScePad` |
| **Logging** | `fprintf` to `/data/custom/bs_deluxe/plugin.log` | `klog()` (kernel debug log) via `final_printf` macro |
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
- **Entry point:** `-e module_start` (CRITICAL - must be set explicitly)
- **CRT for libraries:** `$(TOOLCHAIN)/lib/crtlib.o`
  - ⚠️ **KNOWN ISSUE:** `crtlib.o`'s `module_start` only iterates `__init_array` and returns 0
  - It does NOT call any user-defined function named `plugin_main()`
  - **Fix:** Either use `__attribute__((constructor))` on init functions, or drop crtlib.o and define module_start directly
- **Output packaging:** `create-fself --lib=beat_saber_deluxe.prx --paid 0x3800000000000011`

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
put /workspace/plugins.ini -o /data/GoldHEN/plugins/plugins.ini
# Also deploy custom assets if changed:
# put /workspace/resources_patched.assets -o /data/custom/bs_deluxe/resources_patched.assets
# put /workspace/CustomSong -o /data/custom/bs_deluxe/CustomSong
quit
EOF
```

### Phase 3: Test (user on PS4)
1. **Full reboot** the PS4 (hold power button, select Restart PS4)
2. **Re-run GoldHEN jailbreak** (the exploit payload)
3. **Launch Beat Saber** (CUSA12878)
4. Navigate to Rolling Stones album, select "Start Me Up" on Hard difficulty
5. Report whether you hear original track or $100 Bills
6. Notify the dev environment that PS4 is ready for log check

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

### Phase 5: Iterate (updated for Experiment 4e)
Based on results:
- **heartbeat.txt found ✅:** Plugin loads. Move to Experiment 5 (safe hooking with mprotect).
- **No heartbeat (even with direct module_start) ❌:** The issue is likely with GoldHEN plugin loading itself, not our code. Next steps:
  1. Try `-e _init` as entry point instead of `module_start` (RB4DX uses `_init` via GoldHEN SDK's `crtprx.o`)
  2. Install GoldHEN SDK and use `crtprx.o` + `-e _init` + GoldHEN hook macros (matching RB4DX exactly)
  3. Verify plugin loading via GoldHEN's klog / notification API instead of file writes
  4. Check if `[CUSA12878]` scoping in plugins.ini is correct for Beat Saber's actual CUSA
- **If plugin crashes or causes issues:** Investigate `klog()` output via GoldHEN logging, add proper error handling

## File Reference
- `/workspace/beat_saber_deluxe/src/main.cpp` - Plugin entry point (now defines `module_start`/`module_stop` directly, no crtlib.o)
- `/workspace/beat_saber_deluxe/src/crt_patch.cpp` - CRT replacement sections for `create-fself` (`.data.sce_module_param`, `_init`/`_fini` stubs)
- `/workspace/beat_saber_deluxe/src/hooks.cpp` - Hook utilities (`find_symbol`, `install_hook` — naive memcpy, needs mprotect)
- `/workspace/beat_saber_deluxe/include/bs_deluxe.h` - Plugin definitions
- `/workspace/beat_saber_deluxe/include/hooks.h` - Hook function declarations
- `/workspace/beat_saber_deluxe/Makefile` - Build system (no longer links crtlib.o)
- `/workspace/beat_saber_deluxe/beat_saber_deluxe.prx` - Compiled binary
- `/workspace/plugins.ini` - GoldHEN plugin configuration (deployed to PS4)
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

## Related Research & Memory Files

### Master Index
- **[Research Index](../.ai_memory/RESEARCH_INDEX.md)** — **START HERE.** Comprehensive catalog of all project documents with descriptions, status tracking, and quick commands.
- **[Memory Index](../.ai_memory/MEMORY.md)** — Categorized links to all research/planning documents.

### Recent Findings (2026-06-11)
- [crtlib.o module_start analysis](../.ai_memory/beat-saber-ps4-custom-songs/crtlib-o-module-start-analysis.md) — Root cause: plugin_main() never called by CRT
- [RB4DX Plugin Architecture Reference](../.ai_memory/beat-saber-ps4-custom-songs/rb4dx-plugin-architecture-reference.md) — Working GoldHEN plugin pattern reference
- [Experiment 4d: Constructor Fix](../.ai_memory/beat-saber-ps4-custom-songs/experiment-4d-constructor-fix.md) — FAILED: constructor didn't fire either
- [Experiment 4e: Direct module_start](../.ai_memory/beat-saber-ps4-custom-songs/experiment-4e-direct-module-start.md) — Dropped crtlib.o, defined module_start directly. DEPLOYED.

## Key Technical Decisions
1. **Plugin over PKG:** `.prx` plugin via GoldHEN chosen for rapid iteration vs full PKG rebuild
2. **Sacrifice Song:** "Start Me Up" (Rolling Stones) selected as the hijack target
3. **Sacrifice Replacement:** `CustomSong` bundle (clone of $100 Bills) as test replacement
4. **Toolchain:** OpenOrbis SDK for cross-compilation (provides PS4 headers, linker script, `create-fself`)
5. **CUSA scoping:** Plugin registered under `[CUSA12878]` (Beat Saber) so it only loads for this game
6. **crtlib.o limitation (discovered 2026-06-11):** OpenOrbis's `crtlib.o` provides a `module_start` that only runs the init array — it does NOT call any user-defined `plugin_main()`. All user init code must be `__attribute__((constructor))` or we must drop crtlib.o and define `module_start` ourselves. Long-term, the RB4DX pattern (GoldHEN SDK's `crtprx.o` + `-e _init` + custom `module_start`) is the correct approach.
7. **GoldHEN SDK not installed:** Future work may require installing GoldHEN_Plugins_SDK for proper `HOOK` macros with `mprotect` support. Until then, we can implement our own mprotect-based hooking.
