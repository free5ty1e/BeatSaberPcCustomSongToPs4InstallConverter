---
name: experiment-log
description: "Complete chronological log of all experiments, tests, and their outcomes"
metadata:
  type: reference
---

# Experiment Log: Beat Saber PS4 Custom Song Support

**Started:** 2026-06-08
**System:** PS4 FW 9.00, GoldHEN 2.3 / 2.4b16.2
**Toolchain:** OpenOrbis PS4 Toolchain + GoldHEN Plugin SDK
**Plugin file:** `beat_saber_deluxe.prx`
**Format:** FSELF (SCE magic `4f 15 3d 1d`) — discovered working format in test #31

---

## Phase 1: Initial Research & Failed Approaches

### Experiment 1: Direct FTP Overwrite
- **Date:** 2026-06-08
- **What:** Modified `resources.assets` and tried to upload directly to game directory via FTP
- **Result:** ❌ FAILED — FTP server rejected writes (read-only game directory)
- **Learned:** Game files are protected. Need a plugin for file redirection.

### Experiment 2: "The First Hijack" (Initial PRX)
- **Date:** 2026-06-08
- **What:** Created `.sprx` plugin, hooked `sceFileUtilsOpen` with `strcmp` path matching, used host clang targeting `x86_64-pc-linux-gnu` (WRONG target)
- **Result:** ❌ FAILED — Binary was Linux ELF, not PS4 PRX. Game played original song.
- **Learned:** Need `--target=x86_64-pc-freebsd12-elf` for PS4. Need `mprotect` for code hooking. Need OpenOrbis toolchain.

### Experiment 3: "Logging & Fuzzy Match"
- **Date:** 2026-06-08
- **What:** Changed hook target from `sceFileUtilsOpen` to `open`, added `strstr` fuzzy matching, added file logging
- **Result:** ❌ FAILED — Still Linux-target binary. No log file created.
- **Learned:** Compiler target triple is critical.

---

## Phase 2: Heartbeat Tests (Proving Plugin Loads)

### Experiment 4a: Heartbeat — Minimal Plugin
- **Date:** 2026-06-10
- **What:** Stripped plugin to minimum: write `heartbeat.txt` on load. Used OpenOrbis toolchain. Plugin listed in plugins.ini.
- **Result:** ❌ FAILED — No heartbeat.txt
- **Learned:** Plugin wasn't registered in plugins.ini (next experiment).

### Experiment 4b: Heartbeat — plugins.ini Fix
- **Date:** 2026-06-10
- **What:** Added plugin to plugins.ini under `[default]` section
- **Result:** ❌ FAILED — Still no heartbeat.txt
- **Learned:** ELF entry point was `0x0` (not set).

### Experiment 4c: Heartbeat — Entry Point Fix
- **Date:** 2026-06-11
- **What:** Added `-e module_start` to linker flags. Scoped to `[CUSA12878]`.
- **Result:** ❌ FAILED — No heartbeat.txt
- **Learned:** `crtlib.o`'s `module_start` only runs init array — does NOT call `plugin_main()`.

### Experiment 4d: Heartbeat — Constructor Fix
- **Date:** 2026-06-11
- **What:** Changed `plugin_main()` to `__attribute__((constructor))` so crtlib.o would call it via init array
- **Result:** ❌ FAILED — Constructor didn't fire either
- **Learned:** GoldHEN might not call module_start at all, or init array iteration doesn't work as expected.

### Experiment 4e: Direct module_start (Drop crtlib.o)
- **Date:** 2026-06-11
- **What:** Dropped `crtlib.o`, created `crt_patch.cpp` for CRT sections, defined `module_start` directly as ELF entry point
- **Result:** ❌ FAILED — No heartbeat.txt
- **Learned:** Entry point fix alone wasn't enough.

### Experiment 4f: _init Entry Point (Match RB4DX)
- **Date:** 2026-06-11
- **What:** Changed to `-e _init` entry point. Moved heartbeat into `_init`. Used crt_patch.cpp for CRT.
- **Result:** ❌ FAILED — Still no heartbeat
- **Learned:** Multiple root causes identified: wrong format (fself vs signed ELF), TLS segment, duplicate LOAD PHDR, wrong plugins.ini path.

### Experiment 4g: GoldHEN SDK crtprx.o
- **Date:** 2026-06-11
- **What:** Installed GoldHEN Plugin SDK. Built `crtprx.o` and `libGoldHEN_Hook.a`. Replaced crt_patch.cpp with crtprx.o.
- **Result:** ❌ FAILED — Still no heartbeat
- **Learned:** All structural fixes applied but plugin still didn't load.

---

## Phase 3: Diagnostic Tests (Proving Control)

### Test 1 — CUSA Scoping Test
- **Date:** 2026-06-11
- **Change:** Added plugin to `[CUSA02084]` (same section as working RB4DX)
- **Result:** ❌ No notification. RB4DX loaded normally.
- **Learned:** Issue is not CUSA scoping — same section that loads RB4DX rejects ours.

### Test 2 — Order Test
- **Date:** 2026-06-11
- **Change:** Put our PRX FIRST in `[CUSA02084]`, RB4DX second
- **Result:** ❌ RB4DX at position 2 loaded
- **Learned:** GoldHEN processes entries sequentially. Our PRX fails loading. RB4DX attempted next.

### Test 3 — Copy Test
- **Date:** 2026-06-11
- **Change:** Deployed working RB4DX binary at our filename/path
- **Result:** ❌ RB4DX at position 2 loaded (our copy didn't — likely FTP corruption or duplicate detection)
- **Learned:** Path/filename not the issue.

### Test 4 — ptype: system_dynlib
- **Date:** 2026-06-11
- **Change:** Built with `-ptype system_dynlib (0x9)` for kernel module permissions
- **Result:** ❌ No notification
- **Learned:** ptype doesn't affect loadability.

### Test 5 — ptype: fake
- **Date:** 2026-06-11
- **Change:** Built with `-ptype fake (0x1)` (original make_fself.py default)
- **Result:** ❌ No notification
- **Learned:** ptype not the issue.

### Test 6 — Minimal PRX (Zero Imports)
- **Date:** 2026-06-11
- **Change:** Built PRX with NO library imports, module_start just returns 0
- **Result:** ❌ Still failed (RB4DX at position 2 loaded)
- **Learned:** Even empty PRX fails — issue is not with our code or imports.

### Test 7 — create-fself v1.3
- **Date:** 2026-06-11
- **Change:** Built create-fself from source at tag v1.3 (changelog: "Fixed various miscalculation bugs")
- **Result:** ❌ Still failed
- **Learned:** create-fself version not the (sole) issue, or v1.3 still has bugs.

### Test 8 — Module Param Segment Fix
- **Date:** 2026-06-11
- **Change:** Reverted to original toolchain link.x (no merged sections). LOOS+0x1000002 now 0x18 bytes (matching RB4DX) instead of 0x50.
- **Result:** ❌ Still failed
- **Learned:** Module param segment size was correct but not the root cause.

### Test 9 — Control Test (Disable RB4DX)
- **Date:** 2026-06-12
- **Change:** REMOVED RB4DX entirely from ALL plugins.ini sections
- **Result:** ✅ **RB4DX notification DISAPPEARED**
- **Learned:** **We control plugins.ini. GoldHEN reads our file. All prior tests have been valid.** This is the first definitive proof of control.

### Test 10 — FSELF Format Test (RB4DX FSELF)
- **Date:** 2026-06-12
- **Change:** Deployed RB4DX FSELF from local repo (96048 bytes, SCE magic) to our path. RB4DX removed from [CUSA02084].
- **Result:** ❌ RB4DX FSELF at our path didn't load. No notification.
- **Learned:** FSELF at our path doesn't work for RB4DX build. But later discovered download corruption may have affected this.

---

## Phase 4: Breakthrough — FSELF Format Works!

### Test 11 — FSELF Format (OUR Build!)
- **Date:** 2026-06-12
- **Change:** Deployed OUR plugin as FSELF format (`--lib` output, 70560 bytes, SCE magic) instead of OELF signed ELF
- **Result:** ✅ **"BS Deluxe: SDK Plugin Loaded!" notification appeared! FIRST TIME!**
- **Learned:** **GoldHEN expects FSELF format, NOT OELF signed ELF!** All prior tests deployed the wrong format (they used `-out` OELF, should have used `--lib` FSELF wrapper). Makefile updated.

### Test 12 — Notification + fopen Crash
- **Date:** 2026-06-12
- **Change:** FSELF with notification + fopen/fprintf file write. Plugin registered only under [CUSA12878].
- **Result:** ❌ Notification appeared, then **game CRASHED**
- **Learned:** Plugin loads and notification works, but game crashes after. Unclear if notification or fopen causes crash.

### Test 13 — Path Probe (No Notification)
- **Date:** 2026-06-12
- **Change:** FSELF path probe (tries 14 paths with fopen/fprintf/fclose). No notification.
- **Result:** ❌ **Crashed** (same as Test 12)
- **Learned:** Crash happens even without notification — suggests fopen/fprintf is the real cause.

### Test 14 — Minimal PRX (No Code)
- **Date:** 2026-06-12
- **Change:** FSELF, crtprx.o + main.o (just returns 0). No hooks.cpp, no extra libraries.
- **Result:** ✅ **NO CRASH! Beat Saber booted successfully to VR screen.**
- **Learned:** Crash isolated to excluded components. The basic FSELF + crtprx.o + kernel/SceLibcInternal is stable.

### Test 15 — fopen-only Test
- **Date:** 2026-06-12
- **Change:** Minimal + fopen/fprintf in module_start. No hooks, no GoldHEN_Hook, no notification.
- **Result:** ❌ **Crashed** (theory confirmed: fopen is the issue)
- **Learned:** **fopen/fprintf causes crashes during module_start.** PS4 file sandbox not initialized at early startup.

### Test 16 — printf/klog Test
- **Date:** 2026-06-12
- **Change:** Minimal + printf/klog instead of fopen. No notification.
- **Result:** ✅ **NO CRASH**
- **Learned:** printf/klog works safely during module_start. Output goes to kernel log (not accessible via FTP in log.bin).

### Test 17 — Notification + printf
- **Date:** 2026-06-12
- **Change:** Notification + printf, no fopen
- **Result:** ✅ **NO CRASH. Notification works.**
- **Learned:** Notification + printf is the safe combination. No more rebooting needed — plugins.ini is solidified.

### Test 18 — POSIX File Write (open/write/close)
- **Date:** 2026-06-12
- **Change:** Used open/write/close (POSIX syscall wrappers) instead of fopen/fprintf. Wrote to USB + /data + /tmp.
- **Result:** ✅ **NO CRASH. Notification appeared. No files created (open returned -1).**
- **Learned:** open/write/close fails gracefully (no crash) but doesn't work during module_start either. Sandbox blocks all file creation.

### Test 19 — GoldHEN SDK Linkage
- **Date:** 2026-06-12
- **Change:** Added -lGoldHEN_Hook back, called sys_sdk_version(). No file I/O. FSELF format.
- **Result:** ✅ **NO CRASH. Notification showed "BS Deluxe: SDK v1".**
- **Learned:** GoldHEN SDK functions are safe to call from module_start. Can use GoldHEN SDK for hooking.

---

## Phase 5: Current State & Next Steps

### Working Configuration (as of Test 19)
- **Format:** FSELF (`--lib` output, SCE magic `4f 15 3d 1d`)
- **CRT:** GoldHEN SDK `crtprx.o`
- **Entry point:** `_init` (provided by crtprx.o, calls our `module_start`)
- **Libraries:** `-lGoldHEN_Hook -lSceLibcInternal -lkernel`
- **link.x:** Original toolchain version (no merged sections)
- **create-fself:** v1.3 (built from source)
- **plugins.ini:** Scoped to `[CUSA12878]` (Beat Saber only)
- **Evidence:** Notification API (`sceKernelSendNotificationRequest`) works
- **Logging:** `printf()`/klog works but output not file-accessible. Need deferred logging via hooks.

### What We Know
1. ✅ FSELF format is required (OELF is rejected)
2. ✅ Notification API is safe (no crash)
3. ✅ GoldHEN SDK functions are safe
4. ❌ fopen/fprintf crashes during module_start (heap/FILE* allocation fails)
5. ❌ open/write/close fails gracefully (sandbox not initialized)
6. 🔄 Deferred logging via hooking is the planned solution

### Test Workflow (Current)
1. Build plugin: `export OO_PS4_TOOLCHAIN=... && make clean && rm -rf obj && make -B`
2. Deploy: `lftp -u anonymous, ... -e "put beat_saber_deluxe.prx -o /data/GoldHEN/plugins/beat_saber_deluxe.prx; quit"`
3. User launches Beat Saber (no reboot needed — plugins.ini is solidified)
4. User reports notification text and whether game crashed
5. Check FTP for any log files (if applicable)

**See also:** [[project-summary]], [[experiment-4f-init-entry-point]], [[plugins-ini-path-discovery]], [[rb4dx-plugin-architecture-reference]]

## Phase 5: Hooking Game Functions

### Experiment 20 — sceFileUtilsOpen Hook Test
- **Date:** 2026-06-12
- **Change:** First hook test using GoldHEN SDK Detour system. Hooks `sceFileUtilsOpen` (found via `sys_dynlib_dlsym`). Redirects "Start Me Up" song paths to `/data/custom/bs_deluxe/CustomSong` and `resources.assets` to `/data/custom/bs_deluxe/resources_patched.assets`. No file I/O — uses only GoldHEN SDK + notification + klog.
- **Notifications expected:**
  1. "BS Deluxe: Loading hooks..." (startup)
  2. "FS: FOUND at 0x..." (sceFileUtilsOpen found)
  3. "BS Deluxe: Hook OK" (hook installed)
  4. "BS: Redirecting song!" (when sacrifice song is accessed)
- **Result:** ⏳ AWAITING TEST
- **Learned:** — (pending)

### Experiment 21 — dlsym Function Search
- **Date:** 2026-06-12
- **Change:** Changed from `sys_dynlib_dlsym(-1, ...)` to `dlsym(RTLD_DEFAULT, ...)` (POSIX dlsym). Searches for: sceFileUtilsOpen, open, fopen, sceKernelOpen, read, write, stat, printf, dlopen. Reports ALL found functions in notification. Hooks sceFileUtilsOpen if found via dlsym.
- **Result:** ⏳ AWAITING TEST
- **Notifications expected:**
  1. "BS Deluxe: Loading hooks..." (startup)
  2. List of found functions (e.g., "open printf read ...")
  3. If sceFileUtilsOpen found: "sceFileUtilsOpen HOOKED OK"
- **Learned:** — (pending)

### Experiment 22 — open() Hook via GOT Dereference
- **Date:** 2026-06-12
- **Change:** Used `*(void**)&open` to read the real address of `open()` in libc from our PRX's GOT (confirmed working with printf: GOT=0x23fff9d0 REAL=0x24059810). Hooks the real `open()` function in libc to intercept all file opens. Creates redirects for "startmeup" song paths to CustomSong.
- **Notifications expected:**
  1. "open @ 0x..." (real address)
  2. "open hook: OK" or "FAIL"
  3. "BS: Song redirected!" (when sacrifice song is accessed)
- **Result:** ⏳ AWAITING TEST
- **Learned:** — (pending)

### Experiment 22 — open() Hook (no reentrancy guard) [COMPLETED]
- **Date:** 2026-06-12
- **What:** Hooked the real `open()` function in libc via GOT dereference (`*(void**)&open`). Had klog + notification in hook. No reentrancy protection.
- **Result:** ❌ **Crashed (error 34878)** — hook installed successfully (confirmed by "open @ 0x..." notification), but immediate crash. Likely reentrancy: hook called klog/notification which internally call open() → infinite recursion.
- **Learned:** The GOT dereference technique WORKS — we can find and hook real function addresses in libc. But hooks that call I/O functions need reentrancy protection.

### Experiment 23 — open() Hook with Reentrancy Guard [READY]
- **Date:** 2026-06-12
- **What:** Added `static int in_hook` guard to prevent reentrancy. Hook function now only calls `strstr()` and `HOOK_CONTINUE()` — no klog, no notifications. Notifications moved to module_start (before/after hook install).
- **Status:** ✅ BUILT AND STAGED IN GIT — awaiting PS4 test
- **Expected notifications:**
  1. "open @ 0x..." (real open() address via GOT)
  2. "open hook: OK" (hook installed successfully)
  3. No crash — hook passes through silently, redirects matching paths

### Experiment 23 — open() Hook with Reentrancy Guard [COMPLETED]
- **Date:** 2026-06-29
- **Change:** Added `static int in_hook` guard to prevent reentrancy. Hook was minimal (strstr + HOOK_CONTINUE only).
- **Result:** ❌ **Crashed (error CE-34878-0)** — Same crash as before. GOT dereference works (confirmed by "open @ 0x..." notification) but hook at `open()` in libc crashes immediately. Likely cause: `open()` is a very short function (~8-13 bytes, syscall wrapper) and the 12-byte GoldHEN x64 detour may overflow into adjacent functions, corrupting the trampoline.
- **Learned:** The GOT dereference technique works, but hooking very short functions like `open()` is unsafe with the GoldHEN SDK's current detour implementation.

### Experiment 24 — fopen() Hook via GOT [DEPLOYED]
- **Date:** 2026-06-29
- **Change:** Switched from `open()` to `fopen()`. `fopen` is much longer (~100+ bytes with FILE buffering logic), so the x64 detour won't overflow. Uses same GOT dereference technique (`*(void**)&fopen`). Added reentrancy guard. Removed second notification after hook install to avoid triggering the hook via sceKernelSendNotificationRequest.
- **Status:** ✅ DEPLOYED — awaiting test
- **Expected result:** "fopen @ 0x..." notification, then no crash. If the game uses fopen() for file operations, navigating to the sacrifice song should trigger the redirect (no notification visible).

### Experiment 24 — fopen() Hook via Direct Address [COMPLETED]
- **Date:** 2026-06-29
- **Change:** Fixed address resolution: used `(void*)&fopen` directly instead of `*(void**)&fopen` (which was reading fopen's machine code bytes as a pointer). Hooked fopen only, no second notification after install.
- **Result:** ✅ **NO CRASH!** fopen address shown: 0x8000c2f00. Game booted normally, VR headset worked. But redirect did NOT trigger — navigated to Start Me Up, heard original song.
- **Learned:** PS4 uses direct binding for imported function references. `(void*)&func` gives the real function address in libc, NOT a GOT entry address. Double dereference reads machine code bytes as a pointer — garbage. Game likely uses `open()` instead of `fopen()` for song file access.

### Experiment 25 — Dual fopen+open Hook with Path Logging [DEPLOYED]
- **Date:** 2026-06-29
- **Change:** Hooked BOTH fopen AND open with correct address resolution. Added path logging notifications (shows first 40 chars of opened file path). Separate reentrancy guards for each hook. `try_notify()` helper that only sends notifications when not already inside a hook (prevents recursion).
- **Status:** ✅ DEPLOYED — awaiting test
- **Expected result:** Flood of notifications showing opened file paths. Look for path containing "startmeup" or similar when navigating to sacrifice song. Then we can fix the redirect pattern.

### Experiment 25 — Dual fopen+open Hook with Path Logging [COMPLETED]
- **Date:** 2026-06-29
- **Change:** Hooked BOTH fopen and open with correct address resolution `(void*)&func`. Added `try_notify()` helper for path logging. Separate reentrancy guards per hook.
- **Result:** 🔴 **No path notifications appeared (try_notify bug).** BUT: Start Me Up failed to load (black screen → menu) while other songs worked. This proves the redirect IS triggering! The CustomSong replacement file is likely invalid or incompatible format. Other significant findings:
  - `fopen @ 0x8000c2f00` ✅ confirmed
  - `open @ 0x80000e050` ✅ confirmed — open hook also works! No crash!
  - **Path logging suppressed** because `try_notify` checked `fopen_in_hook || open_in_hook` which was always TRUE when inside a hook
- **Learned:** The redirect works at a basic level — we intercepted *something* related to Start Me Up. The CustomSong file isn't working as a replacement. Need to:
  1. Fix try_notify logging (separate guard)
  2. Investigate what file format/type the game expects for songs
  3. Create a proper CustomSong replacement

### Experiment 26 — Fixed Path Logging via try_notify [DEPLOYED]
- **Date:** 2026-06-29
- **Change:** Added separate `notify_in_progress` guard for try_notify (no longer shares hook guards which always suppressed notifications). Now notifications should actually appear when hooks are triggered.
- **Status:** ✅ DEPLOYED — awaiting test
- **Expected result:** Notification flood showing file paths via "fopen: ..." and "open: ..." messages. When navigating to Start Me Up, we'll see what path the game actually uses.

### Experiment 26 — USB Logging (no notification spam) [DEPLOYED]
- **Date:** 2026-06-29
- **Change:** Removed ALL notification-based path logging (was unusable — endless spam). Replaced with USB file logging via `log_line()` function that writes to `/mnt/usb0/bs_debug.txt`. Uses shared `in_hook` reentrancy guard for BOTH fopen and open hooks. `log_count` limits non-REDIR entries to 200. REDIR entries always logged. Module_start writes header and hook status to USB.
- **Status:** ✅ DEPLOYED — awaiting test
- **Expected behavior:**
  1. **Notifications:** Only two: "fopen @ 0x..." and "open @ 0x..." — NO spam
  2. **USB log:** `/mnt/usb0/bs_debug.txt` created with file paths
  3. Navigate to Start Me Up → log shows which paths are accessed (esp. "REDIR" entries)
  4. After test, download & review log via FTP

### Experiment 27 — Deferred USB Logging (no early fopen) [DEPLOYED]
- **Date:** 2026-06-29
- **Change:** Removed ALL `fopen` calls from `module_start`. Log file initialization deferred to first hook call (when game is fully initialized). Added version notification ("BS Deluxe v0.01a Started!"). Added logging notification with path. Log captures ALL fopen and open calls (no count limit). File cleared on each game launch (first hook truncates the log).
- **Status:** ✅ DEPLOYED — awaiting test
- **Expected result:** "BS Deluxe v0.01a Started!" + "Log: /mnt/usb0/bs_debug.txt" notifications. No crash. Log file created on USB with all file paths.
- **To test:** Launch Beat Saber → navigate to Start Me Up → exit → we check USB log via FTP
