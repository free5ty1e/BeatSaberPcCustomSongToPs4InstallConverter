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

### Experiment 28 — Multi-Path Log Probe (from hooks) [DEPLOYED]
- **Date:** 2026-06-29
- **Change:** Tries 7 paths for logging from within hooks (game fully initialized). First working path gets the log. Notifications: "BS Deluxe v0.01b Started!" + "Log: /path/that/worked" (from first hook call). Paths tried: /data/, /tmp/, /data/custom/bs_deluxe/, /data/cache0001/, /data/GoldHEN/, /mnt/usb0/, /mnt/usb1/. Logs ALL fopen/open calls. Cleared on each launch.
- **Status:** ✅ DEPLOYED — awaiting test
- **Expected result:** Two notifications. Log file created at first writable path. Then navigate to Start Me Up → log captures all file paths.

### Experiment 28 — Multi-Path Log Probe (from hooks) [COMPLETED]
- **Date:** 2026-06-29
- **Change:** Tried 7 paths for logging from within hooks. No file I/O in module_start.
- **Result:** ❌ No logging notification appeared. All 7 paths blocked by game sandbox even from hooks. "BS Deluxe v0.01b Started!" notification appeared but no "Log: ..." notification — meaning init_log() found NO writable path.
- **Learned:** Game sandbox blocks writes to /data/, /tmp/, /data/custom/, /data/cache0001/, /data/GoldHEN/, /mnt/usb0/, /mnt/usb1/ even from hooks. Need to lift sandbox.

### Experiment 29 — GoldHEN Jailbreak for Write Access [DEPLOYED]
- **Date:** 2026-06-29
- **Change:** Added `sys_sdk_jailbreak()` in module_start to lift sandbox restrictions. Notifications: "BS Deluxe v0.02 Started!" + "Jailbreak OK" + "Log: /data/bs_debug.txt" (from first hook). Uses jailbreak to allow writes anywhere.
- **Status:** ✅ DEPLOYED — awaiting test
- **Expected result:** Three notifications. Log file created at /data/bs_debug.txt with all file paths captured. Navigate to Start Me Up → log shows the redirected paths.

### Experiment 29 — GoldHEN Jailbreak for Write Access [COMPLETED]
- **Date:** 2026-06-29
- **Change:** Added `sys_sdk_jailbreak()` in module_start. Log initialized on first hook.
- **Result:** ✅ Jailsbreak OK. Log CREATED at `/data/bs_debug.txt` (6 entries captured). However game crashed with CE-34878-0 after logging only 6 entries. Likely cause: overhead of fopen/fclose in log_line for every hook call during heavy startup.
- **Log captured:** /workspace/screenshots/bs_debug_capture_v02.txt
- **Learned:** Jailbreak works! Logging works (from hooks, after jailbreak). But opening/closing the log file for EVERY file operation is too slow during game startup. Need persistent FILE pointer.

### Experiment 30 — Persistent Log File (v0.03) [DEPLOYED]
- **Date:** 2026-06-29
- **Change:** Changed to persistent `static FILE *log_fp`. Opened once in init_log, kept open. log_line now just fprintf + fflush (no fopen/fclose per call). Drastically reduces overhead.
- **Status:** ✅ DEPLOYED — awaiting test
- **Expected result:** Same 3 notifications. No crash (persistent file is much faster). Log captures ALL file paths during startup and gameplay.

### Experiment 30 — fopen Only + Persistent Log (v0.04) [DEPLOYED]
- **Date:** 2026-06-30
- **Change:** Removed open hook entirely (causing crash — likely PC-relative `jb` in short-function trampoline). Kept fopen hook only (long function, safe detour). Persistent FILE* logging. Jailbreak for write access. NULL-safe path logging (`safe = path ? path : "NULL"`).
- **Status:** ✅ DEPLOYED — awaiting test
- **Expected result:** 3 notifications, no crash. Log at /data/bs_debug.txt captures fopen calls only.

### Experiment 30 — fopen Only + Persistent Log (v0.04) [COMPLETED]
- **Date:** 2026-06-30
- **Change:** Removed open hook. fopen hook only with persistent FILE* logging. Jailbreak in module_start.
- **Result:** ❌ Crashed BEFORE any hook fired. Log was never created (v0.03's old log still present). User saw "BS Deluxe v0.04 Started!" and "Jailbreak OK" but NOT "Log: ..." notification. Crash after jailbreak but before or during hook installation.
- **Learned:** Jailbreak in module_start combined with hook installation may cause multi-threading issues. Another thread calling fopen while Detour_DetourFunction is modifying it could execute corrupted code. v0.02 (dual hooks + jailbreak in module_start) worked because the timing was different (two hook installs = more delay).

### Experiment 31 — Deferred Jailbreak (v0.05) [DEPLOYED]
- **Date:** 2026-06-30
- **Change:** Moved `sys_sdk_jailbreak()` out of module_start into `init_log()` (first hook call). Module_start now only shows startup notification and installs one hook (fopen). Crash theory: jailbreak + hook install + another thread calling fopen simultaneously causes corruption. Deferring jailbreak to hook call avoids this. Yes, log IS cleared on each launch — `fopen(LOG_PATH, "w")` truncates the old log.
- **Notifications:** Only "BS Deluxe v0.05 Started!" from module_start. Then "Log: /data/bs_debug.txt" from first hook (which also does jailbreak silently).
- **Status:** ✅ DEPLOYED — awaiting test

### Experiment 32 — Clean fopen Hook + Path Display (v0.06) [DEPLOYED]
- **Date:** 2026-06-30
- **Change:** Back to Experiment 24's working approach: fopen hook ONLY, NO jailbreak, NO logging, NO open hook. One notification added when redirect triggers, showing the exact file path the game tried to open. This is the single diagnostic notification we've been needing — no spam, no crash.
- **Notifications:** "BS Deluxe v0.06 Started!" + "BS path: /the/actual/path..." (only when Start Me Up is selected)
- **Status:** ✅ DEPLOYED — awaiting test
- **Expected:** No crash. Navigate to Start Me Up → a notification shows the exact path the game is trying to open. This tells us the file format and location for CustomSong.

### Experiment 32 — Clean fopen Hook (v0.06) [COMPLETED]
- **Date:** 2026-06-30
- **Change:** Back to Experiment 24: fopen hook only, no jailbreak, no logging, no open hook. Added path display notification on redirect.
- **Result:** ❌ Redirect didn't work (Start Me Up played normally). Notifications didn't show in VR. Game runs fine but no intercept.
- **Learned:** Confirmed that the game uses `open()` for song loading, not `fopen()`. fopen-only hook doesn't intercept song files.

### Experiment 33 — Detour + Stub jb Fix for open() (v0.07) [COMPLETED]
- **Date:** 2026-06-30
- **Change:** Full v0.02 approach (both fopen+open hooks, jailbreak, logging) PLUS fix_stub_jumps()
- **Result:** ❌ Same CE-34878-0 crash. 5 log entries captured before crash.
- **Log:** /workspace/screenshots/bs_debug_capture_v02.txt
- **Date:** 2026-06-30
- **Change:** Full v0.02 approach (both fopen+open hooks, jailbreak, logging) PLUS a critical fix: after installing the open hook via standard Detour_DetourFunction, `fix_stub_jumps()` patches the allocated stub memory (RWX) to replace `jb`/`jne`/`je` (PC-relative) with `nop;nop`. This prevents the crash that happened after 6 successful open calls — the jb's PC-relative offset was wrong in the stub because the stub is at a different address than open(). Now error returns are handled correctly (the stub returns -1 to the caller instead of jumping to the wrong error handler).
- **Status:** ✅ DEPLOYED — awaiting test
- **Expected:** Both hooks install. Log created. open() hook works without crashing (even on errors). Redirect for "startmeup" paths works. Navigate to Start Me Up → file redirected → CustomSong loaded (may fail).

### Experiment 34 — Manual Hooks + klog via sys_sdk_proc_rw (v0.09) [COMPLETED]
- **Date:** 2026-06-30
- **Change:** Manual hooks via sys_sdk_proc_rw, klog logging
- **Result:** ❌ Same CE-34878-0 crash. Crashed before any log entries (klog output not retrievable).
- **Date:** 2026-06-30
- **Change:** Complete rewrite. NO Detour functions (manual hooking). Hooks installed via `sys_sdk_proc_rw` (GoldHEN kernel write) — no mprotect at all. Stubs via `sceKernelMmap` (RWX). Open stub has jb fixed. Logging via `sys_sdk_cmd(GOLDHEN_SDK_CMD_KLOG)` — no file I/O, no crash. fopen + open hooks both active.
- **Theory:** The crash was either from Detour's mprotect interacting badly with jailbreak, or from the fopen logging causing file I/O issues during startup. v0.09 avoids BOTH: no mprotect (uses sys_sdk_proc_rw), no file I/O logging (uses klog).
- **Notifications:** "BS Deluxe v0.09" + "JB OK" + "fopen=OK open=OK" (or FAIL)
- **Status:** ✅ DEPLOYED — awaiting test

### Experiment 35 — v0.02 rebuild with jb fix (v0.10) [COMPLETED]
- **Date:** 2026-06-30
- **Change:** Exact v0.02 + fix_stub_jumps (plain 0x72 scan)
- **Result:** ❌ Same CE-34878-0 crash. 5 log entries. fix_jb corrupted mov eax (SYS_open=0x72 matched 0x72 opcode).
- **Log:** 5 entries: /dev/urandom, /app0/sce_discmap.plt (x2), /app0/sce_discmap_patch.plt, /app0/media/boot.config
- **Date:** 2026-06-30
- **Change:** Exact v0.02 approach that created working log file (6 entries captured). Jailbreak + Detour hooks + file logging (fopen/fclose per line, no persistent FILE*). PLUS: `fix_jb()` patches jb in open's RWX stub after Detour installs it. init_log deferred to first hook call (not module_start — avoids pre-jailbreak fopen crash).
- **Status:** ✅ DEPLOYED — awaiting test
- **Expected:** Same as v0.02 (logging to /data/bs_debug.txt) but without the jb crash.

### Experiment 36 — Corrected jb fix for open stub (v0.11) [COMPLETED]
- **Date:** 2026-06-30
- **Change:** fix_jb now looks for syscall(0x0F 0x05) + jb, not plain 0x72
- **Result:** ❌ Same CE-34878-0 crash. 5 log entries. Confirmed open() first bytes are function prologue (55 48 89 e5), not a syscall wrapper. fix_jb was irrelevant.
- **Date:** 2026-06-30
- **Change:** Log showed exact same 6 entries as v0.02 — crash still on 7th open call. Root cause: old `fix_jb()` scanned for plain `0x72` byte, but SYS_open syscall number on PS4 is likely `0x72` (114), which appears in the `mov eax, SYS_open` instruction. fix_jb corrupted the mov eax instruction (NOP'd bytes 1-2) and never fixed the actual jb at offset 7.
- **Fix:** `fix_jb()` now searches for pattern `0x0F 0x05` (syscall) followed by `0x72`/`0x74`/`0x75` (conditional jump), and only replaces that specific byte.
- **Status:** ✅ DEPLOYED — awaiting test

### Experiment 37 — Diagnostic: open bytes + call counter (v0.12) [COMPLETED]
- **Date:** 2026-06-30
- **Change:** Dump first 8 bytes of open() + notification on open call #6+ 
- **Result:** ❌ Same CE-34878-0 crash. First 8 bytes of open() = 55 48 89 e5 41 57 41 56 (function prologue). Notification for call #6 NEVER appeared — confirming crash happens BEFORE the call counter increment.
- **Date:** 2026-06-30
- **Change:** Added TWO diagnostics to determine why the 6th open call crashes:
  1. Dumps first 8 bytes of `open()` in notification (verify correct function)
  2. Shows notification with path on open call #6+ (before HOOK_CONTINUE — if it appears, crash is in stub; if not, crash is in our code)
- **Theory:** Despite fixing the jb in v0.11, the 6th call STILL crashes with same 5 entries logged. The crash is NOT from the jb issue. Possible causes:
  - `open()` address might point to wrong function (dump bytes to verify)
  - Crash might be from the NOTIFICATION called from within the hook (not from hook itself)
  - Stub's trampoline might have InstructionSize mismatch
- **Status:** ✅ BUILT & STAGED — awaiting PS4 power-on to deploy

### Experiment 38 — Remove log_line from open_hook (v0.13) [COMPLETED]
- **Date:** 2026-07-01
- **Change:** Removed log_line from open_hook to break reentrant chain
- **Result:** ❌ Same CE-34878-0 crash. Even without log_line, call #6 notification never appeared. Crash is NOT from reentrant logging.
- **Date:** 2026-07-01
- **Change:** Removed `log_line()` call from `open_hook`. The fopen hook still logs. This eliminates the reentrant chain: `open_hook → log_line → fopen → fopen_hook → original fopen → open() → open_hook reentrant`. Theory: the 6th open call arrives while call #5 is still in log_line (file I/O), causing reentrant HOOK_CONTINUE to crash (possibly from simultaneous stub execution). Without log_line, open_hook returns instantly, in_hook is cleared faster, reducing race window.
- **Version:** v0.13
- **Status:** ✅ DEPLOYED — awaiting test
- **Diagnostic retained:** Notification on open_call >= 6 shows path and count

### Experiment 39 — Restore+Call+Rehook for open() (v0.14) [COMPLETED]
- **Date:** 2026-07-01
- **Change:** Completely new approach - restore original bytes, call open() directly, rehook. No stub/trampoline.
- **Result:** ❌ Same CE-34878-0 crash. 5 log entries. Bug: reentrant path rehooked while outer call was still in real_open → stack overflow.
- **Date:** 2026-07-01
- **Change:** COMPLETELY new approach for open() hook. No Detour, no stub, no trampoline. Save original bytes → write jump via sys_sdk_proc_rw → in hook, restore bytes → call original directly → rehook. This avoids ALL stub-related issues (InstructionSize, PC-relative jumps, HDE bugs). fopen hook still via Detour (safe, long function).
- **Theory:** If the crash was from the stub/trampoline (saved bytes execution + jump back), the restore+call+rehook approach should fix it since it never uses a stub. The reentrant path also restores + calls + rehooks.
- **Status:** ✅ DEPLOYED — awaiting test
- **Notifications:** "BS Deluxe v0.14" + "JB OK" + "saved: XX XX ..." (first 8 bytes of open, for comparison) + "hooks: fopen=OK open=OK"

### Experiment 40 — hook_depth fix for restore+call+rehook (v0.15) [COMPLETED]
- **Date:** 2026-07-01
- **Change:** Hook_depth counter - only outermost call rehooks after all nested calls complete
- **Result:** ❌ Same CE-34878-0 crash. 5 log entries. hook_depth fix didn't help - crash is NOT from rehook issue.
- **Log captured:** /workspace/screenshots/bs_debug_v15_log.txt
- **Log content:**
```
=== BS Deluxe Debug Log ===
Version: v0.15
fopen=8000c2f00 open=80000e050
============================
open:/dev/urandom
open:/app0/sce_discmap.plt
open:/app0/sce_discmap.plt
open:/app0/sce_discmap_patch.plt
open:/app0/media/boot.config
```
- **Screenshots:** /workspace/screenshots/bs_debug_v15_log.txt
- **Date:** 2026-07-01
- **Change:** v0.14 (restore+call+rehook) crashed same way. Root cause: reentrant path called `write_jump` (rehook) while outer call was still in the middle of `real_open`. When outer call continued, it called the REHOOKED function → infinite recursion → stack overflow → crash. Fix: `hook_depth` counter. Reentrant path does NOT rehook (only restores + calls + returns). Only outermost (hook_depth==0) call rehooks after all nested calls complete.
- **Status:** ✅ DEPLOYED — awaiting test

### Experiment 41 — fopen only, no open hook, no jailbreak (v0.16) [DEPLOYED]
- **Date:** 2026-07-01
- **Change:** Removed open() hook entirely. Removed jailbreak. Only fopen hook remains (safe, proven working). This tests whether the game uses fopen() for resources.assets loading. If resources.assets IS loaded via fopen(), the redirect to patched version will be visible via notification. No open hook means no 6th call crash.
- **Theory:** After 40 experiments, modifying open()'s code (even via restore+call+rehook) consistently crashes on the 6th call. This suggests PS4 OS may have integrity checks on system functions that trigger after ~5 modifications. Removing the open hook completely bypasses this. The fopen hook alone may be sufficient for song redirection if the patched resources.assets correctly points to CustomSong.
- **Notifications:** "BS Deluxe v0.16 Started!" + "BS redirect: /app0/Media/resources.assets" (if fopen is called for it)
- **Status:** ✅ DEPLOYED — awaiting test

### Experiment 42 — Jailbreak + delay + fopen via sys_sdk_proc_rw (v0.17) [DEPLOYED]
- **Date:** 2026-07-01
- **Change:** Jailbreak + ~60ms delay before fopen hook installation via sys_sdk_proc_rw (no Detour, no mprotect). No open hook (avoids 6th call crash). hook_depth fix for fopen (only outermost call rehooks). Logging to /data/bs_debug.txt via fopen/fprintf from within hook.
- **Theory:** v0.04 (jailbreak + fopen via Detour) crashed immediately — likely mprotect failing after jailbreak due to credential changes. sys_sdk_proc_rw bypasses mprotect entirely. hook_depth prevents reentrant rehook crash. Delay gives jailbreak time to stabilize. No open hook → no 6th call crash. If this works, we have logging + jailbreak without crashes.
- **Notifications:** "BS Deluxe v0.17" + "JB OK" + "fopen hook installed"
- **Status:** ✅ DEPLOYED — awaiting test

### Experiment 43 — Two fopen hooks after jailbreak (v0.19) [DEPLOYED]
- **Date:** 2026-07-01
- **Change:** v0.18 crashed before first hook call. Pattern discovered: v0.02 (jailbreak + TWO hooks) worked for 5 calls, but ALL versions with ONE hook after jailbreak crash immediately. Theory: the PS4/kernel needs TWO code modifications after jailbreak for stability, or the second `sys_sdk_proc_rw` call provides necessary kernel-side state. v0.19 installs the SAME fopen hook TWICE — second `ji()` call is a no-op (writes same bytes) but provides the second kernel write operation.
- **Status:** ✅ DEPLOYED — awaiting test

### Experiment 44 — Detour for both hooks, open=silent (v0.20) [DEPLOYED]
- **Date:** 2026-07-01
- **Change:** Back to EXACT v0.02 pattern: jailbreak + 2x Detour (not sys_sdk_proc_rw). Theory: `sys_sdk_proc_rw` uses syscall 500 (same as jailbreak) → conflict in GoldHEN handler. Detour uses `mprotect` (different syscall) → no conflict. open_hook is silent pass-through (no logging) — eliminates reentrant chain that may have caused v0.02's 6th call crash. fopen_hook handles logging + redirect.
- **Status:** ✅ DEPLOYED — awaiting test
- **Expected:** 3 notifications. No crash. Log at /data/bs_debug.txt captures fopen calls.

### Experiment 45 — ULTIMATE BASELINE: no hooks, just jailbreak + file I/O (v0.21) [DEPLOYED]
- **Date:** 2026-07-01
- **Change:** ZERO hooks. ZERO code modifications. Just jailbreak + fopen + write log + fclose in module_start. If this crashes, jailbreak itself causes the crash. If it works, the issue is specifically with modifying function code after jailbreak.
- **Status:** ✅ DEPLOYED — awaiting test

### Experiment 46 — Raw syscall logging (v0.22) [DEPLOYED]
- **Date:** 2026-07-01
- **Change:** Replaced fopen/fprintf (heap-based FILE*) with raw syscalls (orbis_syscall SYS_open/SYS_write/SYS_close). No heap allocation needed. libc functions like fopen crash in module_start because the heap isn't initialized yet. Raw syscalls bypass the heap entirely. No hooks, no code modifications.
- **Status:** ✅ DEPLOYED — awaiting test
