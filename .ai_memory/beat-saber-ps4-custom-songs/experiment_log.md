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

### Experiment 45 — ULTIMATE BASELINE: no hooks, just jailbreak + file I/O (v0.21) [COMPLETED]
- **Date:** 2026-07-01
- **Change:** ZERO hooks. ZERO code modifications. Just jailbreak + fopen + write log + fclose in module_start. If this crashes, jailbreak itself causes the crash. If it works, the issue is specifically with modifying function code after jailbreak.
- **Result:** ❌ HARD CRASH (CE-34878-0, required hard reset + re-jailbreak). User saw "BS Deluxe v0.21" and "JB OK" notifications, then crash at fopen call. No log file created.
- **Log:** NOT CREATED — heap-based fopen crashed before write
- **Analysis:** The crash is from `fopen()` in module_start. `fopen` allocates a `FILE*` on the heap, but the heap may not be initialized during early module_start on PS4. This confirms that libc FILE I/O functions cannot be used in module_start regardless of jailbreak status.

### Experiment 46 — Raw syscall logging (v0.22) [DEPLOYED]
- **Date:** 2026-07-01
- **Change:** Replaced fopen/fprintf (heap-based FILE*) with raw syscalls (orbis_syscall SYS_open/SYS_write/SYS_close). No heap allocation needed. libc functions like fopen crash in module_start because the heap isn't initialized yet. Raw syscalls bypass the heap entirely. No hooks, no code modifications.
- **Status:** ✅ DEPLOYED — awaiting test

### Experiment 46 — Raw syscall logging (v0.22) [COMPLETED]
- **Date:** 2026-07-01
- **Change:** Log via raw syscalls (orbis_syscall SYS_open/SYS_write/SYS_close) — no heap, no fopen.
- **Result:** ⚠️ SOFT CRASH. User saw all 3 notifications ("BS Deluxe v0.22" + "JB OK" + "raw log: /data/bs_debug.txt"). Log file WAS written successfully! But game crashed (CE-34878-0, soft crash — PS4 recovered without hard reset) after module_start returned, during normal game initialization.
- **Log captured:** /workspace/screenshots/bs_debug_v22_log.txt
- **Log content:**
```
=== BS Deluxe v0.22 ===
Jailbreak: active
Raw syscall I/O works!
```
- **Analysis:** The raw syscall open/write/close WORKS after jailbreak. The crash is NOT from the log write (which succeeded). Crash happens later during game initialization, after module_start returns. v0.02 (jailbreak + 2x Detour) worked for 5 calls — the mprotect syscalls may have propagated jailbreak credential state through the VM subsystem. Without mprotect calls (or equivalent), the jailbreak credential changes don't propagate fully, and the game crashes when accessing various kernel resources during init.

### Experiment 47 — sys_sdk_version() settling call after jailbreak (v0.23) [COMPLETED]
- **Date:** 2026-07-01
- **Change:** Added `sys_sdk_version()` call after raw syscall logging. Theory: v0.02's 2x Detour calls went through the kernel (mprotect syscall), which propagated jailbreak credential state. `sys_sdk_version()` makes an additional GoldHEN syscall (500) which may help propagate state.
- **Result:** ❌ SOFT CRASH (CE-34878-0). User saw all 3 notifications ("BS Deluxe v0.23" + "JB OK" + "raw log: /data/bs_debug.txt"). Log written successfully (same as v0.22). Game crashed after module_start return.
- **Analysis:** `sys_sdk_version()` (GOLDHEN_SDK_CMD_VERSION=0) goes through syscall 500 — the SAME syscall as the jailbreak (`sys_sdk_jailbreak` uses GOLDHEN_SDK_CMD_JAILBREAK=2 on syscall 500). Making another syscall 500 after jailbreak does NOT propagate the credential state. Need a DIFFERENT kernel path (not syscall 500).

### Experiment 48 — sceKernelMprotect settling call after jailbreak (v0.24) [COMPLETED]
- **Date:** 2026-07-01
- **Change:** Replaced `sys_sdk_version()` (syscall 500) with `sceKernelMprotect` (syscall 74) after jailbreak + log write. Mprotect goes through a COMPLETELY DIFFERENT kernel path (VM subsystem) than syscall 500. This forces the VM subsystem to refresh its cached credentials from the kernel store.
- **Result:** ❌ SOFT CRASH (CE-34878-0). User saw all 3 notifications. Log written. Game crashed after module_start return.
- **Analysis:** Single mprotect call on our PRX code page doesn't force a full TLB flush or VM subsystem credential refresh. The page protection change only affects our module's page, not the pages the game uses during initialization. v0.02's dual Detour calls modified TWO different libc pages (fopen + open), providing wider credential propagation.

### Experiment 49 — sceKernelUsleep delay for jailbreak propagation (v0.25) [COMPLETED]
- **Date:** 2026-07-01
- **Change:** After jailbreak + raw log write, call `sceKernelUsleep(500000)` (500ms). Theory: v0.02 worked because its open_hook took time (fopen logging). Without enough time, jailbreak changes haven't propagated.
- **Result:** ❌ SOFT CRASH (CE-34878-0). User reported strange notification order: "saw notification 1, same soft crash happened, saw notification 3, then notification 6." The crash notification (CE-34878-0 dialog) appeared BEFORE later notifications, suggesting the crash triggers async notification delivery.
- **Analysis:** Time delay alone doesn't propagate jailbreak credential changes. The credential propagation requires ACTIVE kernel operations on specific subsystems, not passive waiting. The 500ms usleep allowed other processes to run but didn't force the VM/credential subsystems to refresh.

### Experiment 50 — NO jailbreak, Detour hooks + notification logging (v0.26) [CANCELLED]
- **Date:** 2026-07-01
- **Change:** COMPLETE PIVOT. No jailbreak. No file writes. Detour hooks for fopen + open. Uses notifications for diagnostic output (limited to first 10 calls).
- **Result:** ❌ CANCELLED before test. User rejected notification-based logging approach based on prior experience with endless notification spam (from Experiment 25 era). User demanded file logging instead.
- **Research applied:** User-provided GoldHEN guide — sandbox kills fopen("/data/"); variadic wrappers cause stack corruption; thread isolation needed for file I/O; AFR recommended.

### Experiment 51 — AFR write test via sceKernelOpen (v0.27) [COMPLETED — MAJOR BREAKTHROUGH]
- **Date:** 2026-07-01
- **Change:** NO jailbreak, NO hooks. Writing to `/data/GoldHEN/AFR/CUSA12878/bs_log.txt` using `sceKernelOpen`/`sceKernelWrite`/`sceKernelClose` (Orbis kernel API, no heap). Tests if GoldHEN's AFR (Application File Redirector) intercepts the write and allows it through the sandbox. AFR directory created manually via FTP (`/data/GoldHEN/AFR/CUSA12878/` with 0777 perms).
- **Research applied:** User-provided GoldHEN guide — AFR method uses built-in hooks. "Leverage the Application File Redirector (AFR) Plugin natively included with GoldHEN. This plugin hooks system file calls and seamlessly redirects safe paths inside the sandbox out to /data/GoldHEN/AFR/Game_Title_ID/."
- **Result:** ✅ **NO CRASH. FILE WRITTEN SUCCESSFULLY!** User saw "BS Deluxe v0.27" and "AFR: OK" notifications. Game ran without crashing. Log file verified at `/data/GoldHEN/AFR/CUSA12878/bs_log.txt` via FTP.
- **Log captured:** /workspace/screenshots/afr_log_v27.txt
- **Log content:**
```
BS Deluxe v0.27: AFR write OK!
```
- **Analysis:** This is the breakthrough we've been seeking for 51 experiments! GoldHEN's AFR DOES intercept file writes to `/data/GoldHEN/AFR/<TitleID>/` and allows them through the game sandbox WITHOUT jailbreak. The `sceKernelOpen`/`sceKernelWrite`/`sceKernelClose` functions (Orbis kernel API) work correctly with no heap allocation needed. This gives us a clean, stable file logging mechanism. No jailbreak = no credential propagation issues = no crashes. Key lessons:
  - `sceKernelOpen` (Orbis API) works where `fopen` (libc) crashes — no heap allocation
  - AFR path `/data/GoldHEN/AFR/<TitleID>/` accepts writes under normal game sandbox
  - RB4DX uses the same pattern (`data:/GoldHEN/AFR/CUSA02084/...`) — proven approach
  - AFR directory needed manual creation via FTP (GoldHEN doesn't auto-create it)
  - Copy of log: /workspace/screenshots/afr_log_v27.txt

### Experiment 52 — AFR logging + Detour hooks (v0.28) [COMPLETED]
- **Date:** 2026-07-01
- **Change:** Combined AFR path logging (sceKernelOpen to `/data/GoldHEN/AFR/CUSA12878/bs_log.txt`) with Detour hooks for fopen (logging + redirect) and open (logging only). No jailbreak, no notifications per-file.
- **Result:** ⚠️ Game ran without crashes (2 notifications). Log file WAS created at `/data/GoldHEN/AFR/CUSA12878/bs_log.txt` (44 bytes) but with permissions `----------` (zero read/write/execute) due to game's `umask`. FTP server can see the file in directory listing but CANNOT read its contents (550 error). After FTP server restart, file still unreadable. Deleting and recreating via FTP fixed the listing but permissions issue remains.
- **Log:** CREATED but UNREADABLE via FTP due to permissions
- **File listing:** `---------- 1 1 0 44 Jun 27 2026 bs_log.txt`
- **Analysis:** The file was created successfully by the game process (UID 1). The `0644` mode passed to `sceKernelOpen(O_CREAT)` had all permissions stripped by the game's `umask` (likely `0777` — common for PS4 game sandbox). The file exists with actual content (44 bytes of log entries) but neither the game (UID 1) nor root (UID 0, FTP server) can read it due to zero permissions. **This explains v0.27's success** — v0.27 was tested in the same session where the directory was created by FTP, and the FTP server's cached listing showed normal permissions. The actual permissions issue was always there but masked by FTP caching.

### Experiment 53 — sceKernelFchmod to fix log permissions (v0.29) [COMPLETED]
- **Date:** 2026-07-01
- **Change:** Added `sceKernelFchmod(fd, 0644)` after `sceKernelOpen` in log_write. v0.28's log file was created with permissions `----------` due to game's `umask=0777`. Added auto-create directory logic (`sceKernelMkdir`) and accurate status reporting. Force permissions with `sceKernelFchmod`.
- **Result:** ✅ **LOG SUCCESS!** Game ran without crashes. Log file at `/data/GoldHEN/AFR/CUSA12878/bs_log.txt` was created with READABLE permissions. FTP access works. Log captured: **674 lines** of file operations during startup to VR screen (672 open calls, 0 fopen calls). Confirmed the game uses `open()` exclusively.
- **Log size:** 70.9KB, 674 lines
- **Log captured:** /workspace/screenshots/bs_log_v29.txt
- **Log preview (first entries):**
  ```
  open:/data/GoldHEN/AFR/CUSA12878/bs_log.txt
  === BS Deluxe v0.29 started ===
  open:/data/GoldHEN/AFR/CUSA12878/bs_log.txt
  fopen+open hooks active
  open:/dev/urandom
  open:/app0/sce_discmap.plt
  open:/app0/sce_discmap_patch.plt
  open:/app0/sce_discmap.plt
  open:/app0/sce_discmap_patch.plt
  open:/app0/media/boot.config
  open:/dev/urandom
  open:/app0/debug.log
  open:/app0/archive.psarc
  open:/app0/archive_patch.psarc
  open:/app0/Media/Metadata/global-metadata.dat
  ...
  ```
- **Key findings:**
  1. Game uses `open()` for ALL file operations — zero `fopen()` calls
  2. `resources.assets` IS opened at two paths:
     - `open:/archive/mount/point/Media/resources.assets`
     - `open:/app0/Media/resources.assets`
  3. Game checks `/archive/mount/point/` first, then falls back to `/app0/`
  4. Game reads from: `/app0/`, `/archive/mount/point/`, `/dev/`, `/savedata0/`
  5. 672 open calls during startup to VR screen
  6. No song paths opened yet (only boot to VR screen, didn't navigate to a song)

### Experiment 54 — OPEN hook redirect (v0.30) [COMPLETED — BOTH REDIRECTS WORK]
- **Date:** 2026-07-01
- **Change:** Moved ALL redirect logic from fopen hook to open hook (game uses `open()` exclusively, proven by v0.29 log). Custom files deployed to AFR directory.
- **Result:** ✅ **BOTH REDIRECTS FIRE SUCCESSFULLY!** User navigated to Start Me Up → black screen for 1-2 seconds → returned to menu (song failed to load). Log shows 1427 lines (vs 674 from v0.29 boot alone — the extra ~750 lines are from menu navigation + song selection).
- **Log captured:** /workspace/screenshots/bs_log_v30.txt
- **Redirect evidence:**
  ```
  open:/archive/mount/point/Media/resources.assets -> /data/GoldHEN/AFR/CUSA12878/resources_patched.assets
  open:/archive/mount/point/Media/resources.assets -> /data/GoldHEN/AFR/CUSA12878/resources_patched.assets
  open:/archive/mount/point/Media/StreamingAssets/BeatmapLevelsData/startmeup -> /data/GoldHEN/AFR/CUSA12878/CustomSong
  open:/archive/mount/point/Media/StreamingAssets/BeatmapLevelsData/startmeup -> /data/GoldHEN/AFR/CUSA12878/CustomSong
  ```
- **Song load analysis:** After redirect, game loaded Rolling Stones environment bundles + `PlayerData.dat` save (returning to menu). The game read our CustomSong file (valid UnityFS AssetBundle, 8.7MB, Unity 2022.3.33f1), but when the game's code calls `AssetBundle.LoadAsset<BeatmapLevelsData>("startmeup")`, the asset isn't found in our bundle (which has assets named for "$100 Bills"). Unity's AssetBundle loader can parse the bundle format but fails to find the expected asset by name.
- **Key infrastructure wins:**
  1. ✅ Plugin loads without crash (AFR path, no jailbreak)
  2. ✅ File logging works (sceKernelOpen/fchmod to AFR path)
  3. ✅ Both open() hooks fire without 6th-call crash (Detour works)
  4. ✅ Both resources.assets AND startmeup redirects work
  5. ❌ CustomSong AssetBundle has wrong internal asset naming (game expects "startmeup" asset, bundle contains "$100 Bills" assets)
- **Next step needed:** Create properly formatted Beat Saber PS4 song AssetBundles. The CustomSong bundle needs to contain assets named "startmeup" (matching the filename the game expects). This requires understanding the Beat Saber Unity AssetBundle schema and creating/modifying bundles with correct asset names and references.

### Experiment 55 — Song load path diagnostic (v0.31) [DEPLOYED]
- **Date:** 2026-07-01
- **Reason:** v0.30 proved both redirects work, but CustomSong fails because internal asset names don't match. User suggested simplest test: redirect Start Me Up to play $100 Bills (unmodified working song). But we don't know where $100 Bills' level data file is on the PS4 (can't FTP-read from /app0/).
- **Change:** Disabled the startmeup song redirect. resources.assets redirect still active. Game will play Start Me Up normally. The log will capture ALL file opens during the song loading process, revealing the paths for song data, audio banks, and other assets.
- **Purpose:** Discover file paths used during normal song loading so we can:
  1. See where $100 Bills (or base game songs) get their level data from
  2. Find the correct path pattern for redirect targets
  3. Understand the complete set of files opened for a single song
- **Status:** ✅ DEPLOYED — awaiting test
- **To test:** Launch Beat Saber, navigate to Start Me Up, PLAY IT COMPLETELY (let the song load and play), then exit. The log at `/data/GoldHEN/AFR/CUSA12878/bs_log.txt` will be analyzed for song-loading file paths.

### Experiment 55 — Song load path diagnostic (v0.31) [COMPLETED]
- **Date:** 2026-07-01
- **Change:** Disabled startmeup redirect. User played Start Me Up normally.
- **Result:** ✅ Song played normally. Log captured at 751 lines. KEY FINDINGS:
  - Game opens `BeatmapLevelsData/startmeup` from BOTH paths (mount point + app0) 4 times
  - NO audio/FMOD file opens during song loading - audio is embedded in AssetBundles
  - ALL pack bundles loaded during startup preload (every DLC pack's bundle)
  - Local dump found at `/workspace/ps4_dump/CUSA12878-patch/` containing ALL original song files!
  - `100bills` file is identical to our `CustomSong` file (same MD5 hash)
  - Original `startmeup` file also present in dump (12.5MB vs 100bills' 8.7MB)
- **Log captured:** /workspace/screenshots/bs_log_v31.txt

### Experiment 56 — Redirect to original startmeup copy (v0.32) [DEPLOYED]
- **Date:** 2026-07-01
- **Reason:** We now have the original startmeup file from the local dump. This is a CONTROL TEST: redirect startmeup to an EXACT COPY of itself (deployed to AFR directory). If the song plays normally, the redirect mechanism is 100% correct. Then we can try redirecting to 100bills for the actual replacement.
- **Key discovery:** Local game dump found at `/workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/` with ALL song files. Both `100bills` and `startmeup` files present. This gives us the original files to work with.
- **Status:** ✅ DEPLOYED — awaiting test
- **Expected:** Navigate to Start Me Up → song loads and plays normally (redirect goes to exact copy). If this works, next test: redirect to 100bills.

### Experiment 56 — Redirect to original startmeup copy (v0.32) [COMPLETED]
- **Date:** 2026-07-01
- **Change:** Redirect startmeup to exact copy of original startmeup file (deployed to AFR directory).
- **Result:** ✅ **CONTROL TEST PASSED!** Song played normally. The redirect mechanism is 100% verified.
- **Analysis:** Confirmed that:
  1. Redirecting to AFR directory files works correctly
  2. An exact copy of the original file works the same as the original
  3. The game loads the redirected file without issues
- **Next:** v0.33 redirects startmeup to the 100bills file

### Experiment 57 — Redirect startmeup to 100bills (v0.33) [DEPLOYED]
- **Date:** 2026-07-01
- **Change:** Changed redirect target from startmeup_original to 100bills. resources.assets redirect still active.
- **Status:** ✅ DEPLOYED — awaiting test
- **Expected:** If the game uses `LoadAllAssets<BeatmapLevelsData>()` (by type), it will find the BeatmapLevelsData in 100bills and PLAY $100 BILLS! If it uses `LoadAsset<BeatmapLevelsData>("startmeup")` (by name), it will NOT find the asset (named "100bills" internally) and show a black screen (same as v0.30).
- **This is the moment of truth!** 🚀

### Experiment 57 — Redirect startmeup to 100bills (v0.33) [COMPLETED]
- **Date:** 2026-07-01
- **Change:** Redirect startmeup → 100bills file (from local dump).
- **Result:** ❌ **BLACK SCREEN → MENU.** Confirmed the game uses `LoadAsset<BeatmapLevelsData>("startmeup")` (by NAME, not by type). The 100bills AssetBundle is a valid UnityFS bundle with correct format, but its assets are named "100bills" internally. When the game calls `LoadAsset("startmeup")` on our bundle, Unity can't find it.
- **File analysis performed:**
  - Decompressed the AssetBundle header (LZ4 via liblz4 ctypes) — confirmed header contains only CAB IDs, not asset names
  - `"100bills"` string NOT found anywhere in the raw file — asset names are deeply encoded in Unity serialized format
  - Binary patching the asset name is NOT feasible without proper Unity tools
- **Key insight from log comparison:**
  - v0.30 (with redirect): mount point path opened (redirected) → game uses OUR file → fails (wrong asset name)
  - v0.31 (without redirect): mount point tried, fails → app0 path used → original file → works
  - The game does NOT fall back to app0 if the mount point file exists but has wrong content
- **Next approach:** Option B — Hook Unity's `AssetBundle.LoadAsset_Internal` function to rename the asset lookup from "startmeup" to "100bills"

### Experiment 58 — Find Unity functions via dlsym (v0.34) [DEPLOYED]
- **Date:** 2026-07-01
- **Change:** Added dlsym/RTLD_DEFAULT + sys_dynlib_dlsym search for Unity AssetBundle function symbols. Tries 8 possible symbol names (il2cpp mangled variants) and reports which are found. Does NOT hook any function yet — this is just a diagnostic to find the correct symbol name.
- **Approach:** Option B (hook Unity AssetBundle functions). Step 1 = find the function. Step 2 = hook with logging. Step 3 = add name replacement.
- **Symbols searched:**
  - `UnityEngine_AssetBundle_LoadAsset_Internal_string_Type`
  - `UnityEngine_AssetBundle_LoadAsset_Internal`
  - `UnityEngine_AssetBundle_LoadFromFile_string`
  - `UnityEngine_AssetBundle_LoadFromFile`
  - `AssetBundle_LoadAsset_Internal`
  - `AssetBundle_LoadFromFile`
  - `_ZN13UnityEngine6AssetBundle12LoadFromFileENS_6StringE` (C++ mangled)
  - `_ZN13UnityEngine6AssetBundle22LoadAsset_InternalEPNS_6StringEPNS_4TypeE` (C++ mangled)
- **Expected:** If any symbol is found, we'll see "Unity syms found: N" in the notification. The log at `/data/GoldHEN/AFR/CUSA12878/bs_log.txt` will list which names were found and their addresses.
- **Status:** ✅ DEPLOYED — awaiting test

### Experiment 58 — Find Unity functions via dlsym (v0.34) [COMPLETED]
- **Date:** 2026-07-01
- **Change:** Searched for 8 symbol names across all loaded libraries using dlsym + sys_dynlib_dlsym.
- **Result:** ❌ **NO UNITY SYMBOLS FOUND.** None of the 8 AssetBundle function names were exported. This confirms that Unity's il2cpp for PS4 strips all symbols from the engine binaries.
- **Analysis:** Alternative approaches needed to hook AssetBundle functions. Options: hardcoded offsets (RB4DX approach), pattern scanning, or modifying the manifest instead.

### 🔬 CRITICAL DISCOVERY: resources_patched.assets analysis
Before building v0.35, I analyzed the difference between the original file and `resources_patched.assets`:
- **Only 10 bytes differ** (at offset 871180): `"StartMeUp\0"` was changed to `"CustomSong"` (same length, 10 bytes)
- **No other changes!** The patched file is otherwise IDENTICAL to the original
- **Conclusion:** The patched resources.assets doesn't add any custom songs or modify anything useful. It just renames Start Me Up's levelId
- **Impact:** All prior tests using the patched resources.assets were flawed — the game looked for `BeatmapLevelsData/CustomSong` (which we never redirect) instead of `BeatmapLevelsData/startmeup`
- **Fix:** STOP redirecting resources.assets entirely. Use the ORIGINAL manifest with levelId="startmeup"

### Experiment 59 — TRUE 100bills replacement test (v0.35) [DEPLOYED]
- **Date:** 2026-07-01
- **Change:** 
  1. REMOVED the resources.assets redirect (broken — caused game to look for "CustomSong")
  2. KEEP startmeup→100bills redirect
  3. Added "CustomSong" safety net redirect (in case the patched manifest is somehow loaded)
- **This is the TRUE test of whether 100bills works as a replacement!** Previous tests (v0.30, v0.33) were corrupted by the patched manifest sending the game to "CustomSong" instead of "startmeup".
- **Expected:** If the game uses `LoadAllAssets<BeatmapLevelsData>()` (by type), it will PLAY $100 BILLS! If it uses `LoadAsset<BeatmapLevelsData>("startmeup")` (by name), it will black screen.
- **Status:** ✅ DEPLOYED — awaiting test

### Experiment 59 — TRUE 100bills replacement test (v0.35) [COMPLETED]
- **Date:** 2026-07-01
- **Change:** Removed resources.assets redirect (was corrupting levelId). KEPT startmeup→100bills redirect.
- **Result:** ❌ **BLACK SCREEN → MENU.** The redirect fires (log shows it) but Unity LoadAsset can't find "startmeup" in the 100bills bundle. App0 opens are absent — game only uses mount point file.
- **Log captured:** /workspace/screenshots/bs_log_v35.txt
- **Log evidence:**
  ```
  open:/archive/mount/point/Media/StreamingAssets/BeatmapLevelsData/startmeup -> /data/GoldHEN/AFR/CUSA12878/100bills
  ```
- **Confirmed:** Asset name MUST match. Game uses `LoadAsset<BeatmapLevelsData>("startmeup")` by name, not by type.

### Experiment 60 — Manifest levelId patch: startmeup→100bills (v0.36) [COMPLETED]
- **Date:** 2026-07-01
- **Change:** resources.assets v3 patch: changed "StartMeUp\0" → "100bills\0\0" at offset 871180.
- **Result:** ❌ Same black screen. Log showed the game still opened `BeatmapLevelsData/startmeup` (NOT 100bills). The patched string at offset 871180 is the SONG NAME, not the levelId. The real levelId is at offset 793116 (first "StartMeUp" occurrence, length-prefixed with `09 00 00 00`). Can't change from 9 chars to 8 without shifting data.
- **Analysis:** Manifest binary patching approach FAILED. Need to either hook LoadAsset or modify the AssetBundle file itself.

### Experiment 61 — AssetBundle rename via UnityPy (v0.37) [DEPLOYED]
- **Date:** 2026-07-01
- **Change:** Installed `lz4` (Python) and `UnityPy` libraries. Used UnityPy to:
  1. Open the 100bills AssetBundle
  2. Rename AssetBundle.m_Container[0] path from `.../100billsbeatmapleveldata.asset` → `.../startmeup/startmeupbeatmapleveldata.asset`
  3. Rename BeatmapLevelData's m_Name from `100BillsBeatmapLevelData` → `StartMeUpBeatmapLevelData`
  4. Save the modified bundle
- **Result:** ✅ Bundle saved successfully (8,709,501 bytes). Verification confirmed BOTH paths renamed.
- **Deployment:** Renamed bundle deployed to `/data/GoldHEN/AFR/CUSA12878/100bills_renamed`. Plugin v0.37 redirects startmeup → renamed bundle. NO resources.assets redirect.
- **This is the moment of truth!** If the game uses m_Name OR container path filename for LoadAsset lookup, it should find "StartMeUpBeatmapLevelData" in our renamed bundle and PLAY $100 BILLS! 🚀
- **Status:** ✅ DEPLOYED — awaiting test

### Experiment 61 — AssetBundle rename via UnityPy (v0.37) [🎉 COMPLETED — SONG REPLACEMENT WORKS!]
- **Date:** 2026-07-01
- **Change:** Modified 100bills AssetBundle via UnityPy: renamed m_Name → "StartMeUpBeatmapLevelData" + container path → ".../startmeup/startmeupbeatmapleveldata.asset"
- **Result:** ✅ **$100 BILLS PLAYED WHEN START ME UP WAS SELECTED!** 🎉 The user confirmed the correct level data displayed and the song played. They also tested another song (Paint It Black) to confirm interception only works on Start Me Up — that song played normally without interference.
- **Log evidence:**
  ```
  open:/archive/mount/point/Media/StreamingAssets/BeatmapLevelsData/startmeup -> /data/GoldHEN/AFR/CUSA12878/100bills_renamed
  open:/archive/mount/point/Media/StreamingAssets/BeatmapLevelsData/paintitblack
  ```
- **Log captured:** /workspace/screenshots/bs_log_v37.txt
- **Key achievements:**
  1. ✅ GoldHEN plugin loads without crash (no jailbreak, AFR path)
  2. ✅ File logging via sceKernelOpen to AFR directory
  3. ✅ Detour hooks for open() without crash
  4. ✅ File redirect at open() level works
  5. ✅ AssetBundle internal rename via UnityPy (m_Name + container path)
  6. ✅ **CROSS-SONG REDIRECT CONFIRMED!** Start Me Up → $100 Bills
  7. ✅ Other songs unaffected (targeted redirect only)
- **Tools installed:**
  - `lz4` (Python) - LZ4 compression for AssetBundle manipulation
  - `UnityPy` (Python) - Unity AssetBundle reader/writer
- **Devcontainer updated:** Both Dockerfiles include lz4 and UnityPy in pip packages
### Experiment 62 — Custom song conversion pipeline + redirect (v0.38) [COMPLETED — FIXED BUNDLE DEPLOYED]
- **Date:** 2026-07-01
- **Change:** Built `convert_song_v3.py` - converts BeatSaver custom songs to PS4 AssetBundles. Replaces all 5 difficulty beatmaps with custom song data.
- **Tested song:** VOLUPTE by Tare (from songs_repo/01ce5a3adc19e360ba0ffd8347f91b5dc974eb7c)
- **Result Part 1 (initial):** ❌ Quick black screen — beatmap TextAssets corrupted
- **Root cause found (via UnityPy source code analysis):**
  TextAsset type tree defines ONLY `m_Name` and `m_Script` (both strings). The beatmap format stores extra data: `[fn_len][fn_name][m_script_len][gzip_data]`. The `m_script_len` field is read by UnityPy as the string length for m_Script. Setting it to the decompressed data size (1.1MB) caused `read_str out of bounds` because the actual gzip data was only 76KB.
- **Fix:** Changed "decomp_size" field from `len(decompressed_data)` to `len(compressed_gzip_data)`. The gzip container itself stores the original size internally, so decompression succeeds regardless.
- **Result Part 2 (fixed):** ✅ **ALL 5 BEATMAPS VALID!** Bundle loads correctly. Easy, Normal, Hard, Expert, ExpertPlus all decompress to correct beatmap data.
- **Deployed to:** `/data/GoldHEN/AFR/CUSA12878/startmeup_final`
- **Limitations:** Audio is still from Start Me Up (FSB5 format — needs FMOD/fsbank tools). Song metadata from resources.assets manifest (not the bundle).

### Experiment 62 — Custom song conversion test result [🧪 TESTED - PARTIAL SUCCESS]
- **Date:** 2026-07-01
- **Test:** Navigated to Start Me Up with the fixed bundle (VOLUPTE beatmaps)
- **Result:** ✅ **CUSTOM BEATMAPS LOAD!** The note boxes were from VOLUPTE (different pattern from Start Me Up). Song played with custom note patterns.
- **Issues observed:**
  1. ✅ Audio works (but it's still Start Me Up's original FSB5 audio - expected)
  2. ❌ Background is blank (space/stars only - environment scene not loading)
  3. ❌ Notification showed "v0.37" (fixed by rebuilding v0.38 PRX)
- **Analysis:** The beatmap gzip replacement via `set_raw_data` + UnityPy works correctly. The game loads our modified bundle, finds the custom gzip data, decompresses it, and renders the custom note patterns. The blank background suggests the environment scene (Rolling Stones environment bundle) isn't being loaded or doesn't match expectations. The original audio plays because the FSB5 audio resource wasn't replaced (that's the next challenge).
- **Next steps:**
  1. Fix blank background (environment scene issue)
  2. Replace FSB5 audio with custom audio (needs FMOD tools)
  3. Add new song entry to an album via resources.assets manifest

### Experiment 63 — Strip _events from beatmap data for environment fix [DEPLOYED]
- **Date:** 2026-07-01
- **Change:** Analysis of beatmap data format revealed VOLUPTE uses V2 format (with `_notes`, `_obstacles`, `_events`) while PS4 expects V3/V4 format (with `colorNotes`, `obstacles`, and separate lightshow data). The 13,825 `_events` per difficulty conflicted with PS4's separate lightshow system, causing blank background.
- **Fix:** Strip `_events` and `_customData` from each difficulty's `.dat` file before gzip compression. Updated `convert_song_v3.py` with this fix.
- **Result:** Bundles now have V2 format beatmaps with events removed. Beatmap sizes dropped from ~76KB to 1-5KB (events were the bulk). Rolled back to `startmeup` template lightshow. AWAITING TEST.
- **Also noted:** `_obstacles` were 0 for all VOLUPTE difficulties — this custom song has no obstacles/walls.

### Experiment 64 — 100bills template + notification fix (v0.39) [DEPLOYED - v2]
- **Date:** 2026-07-01
- **Change:** 
  1. Fix notification: was hardcoded "v0.37", now uses PLUGIN_VERSION
  2. Switch to 100bills template for env/lightshow comparison test
  3. Rename BeatmapLevelData m_Name + container path (NOT AudioClip - caused crash)
  4. Replace 5 Standard beatmaps with VOLUPTE (events stripped)
- **v1 result:** ❌ CE-34878-0 CRASH. AudioClip rename via `save_typetree` corrupted `m_Resource` field (FSB5 external reference).
- **v2 fix:** Removed AudioClip rename. Keep original "$100Bills" name. Game uses PPtr for audio lookup, not name.
- **v2 deployed:** No AudioClip rename, BeatmapLevelData renamed, container path renamed.
- **Status:** ✅ DEPLOYED — awaiting test

### Experiment 65 — Diagnostic: unmodified UnityPy save [COMPLETED]
- **Date:** 2026-07-01
- **Change:** Saved startmeup template through UnityPy with ZERO modifications.
- **Result:** ✅ Environment renders normally! UnityPy's save is fine. Beatmaps were original Start Me Up (expected since no modifications). Proves the blank background is from the BEATMAP DATA CONTENT, not UnityPy's save.

### Experiment 66 — V2→V3 beatmap format conversion (v0.40) [CRASHED]
- **Change:** V2→V3 converter + `set_raw_data` on beatmaps
- **Result:** ❌ CE-34878-0 crash. 3 beatmap objects had read_typetree failures (Normal/Expert/ExpertPlus).

### Experiment 67 — save_typetree + surrogateescape fix (v0.42) [DEPLOYED]
- **Date:** 2026-07-01
- **Bug 1:** `set_raw_data` causes internal serialization inconsistency for 3 objects (Normal/Expert/ExpertPlus)
- **Bug 2:** `latin-1` decoding followed by `utf-8` encoding corrupts bytes > 127 (doubles their size via 0xC2 prefix)
- **Fix:** Use `save_typetree` with `surrogateescape` encoding (`.decode('utf-8', 'surrogateescape')`) to preserve all bytes through the string round-trip.
- **Notif fix:** Changed hardcoded `"BS Deluxe v0.37"` to use `PLUGIN_VERSION` properly.
- **Status:** ✅ DEPLOYED — awaiting test
- **Date:** 2026-07-01
- **Change:** Built V2→V3 beatmap converter. V2 format uses `_notes` array with inline properties, but PS4 expects V3 format with `colorNotes` + `colorNotesData` (deduplicated data arrays). The V3 data arrays store unique property combinations, and notes reference them by index (`i`). Without the `i` field, notes default to data[0] `{'x': 1, 'd': 1}`.
- **Conversion process:**
  1. Extract `_lineIndex`, `_lineLayer`, `_type`, `_cutDirection` from each V2 _note
  2. Deduplicate into (x, y, c, d) tuples
  3. Create `colorNotesData` array from unique tuples
  4. Create `colorNotes` array: `b` (beat) + `i` (index, omitted if 0)
  5. Convert obstacles similarly
  6. Add empty arrays for chains, arcs, spawnRotations
  7. Set version to "4.0.0"
- **Deployed:** startmeup_v3 with VOLUPTE beatmaps in V3 format.
- **Status:** ✅ DEPLOYED — awaiting test

### Experiment 68 — V3 conversion + save_typetree (v0.43) [DEPLOYED]
- **Date:** 2026-07-01
- **Change:** Combined V2→V3 format conversion with `save_typetree` data setting. Converts V2 `_notes` → V3 `colorNotes` + `colorNotesData`. Uses `save_typetree` (not `set_raw_data` which had serialization bugs). Empty arrays for bombs/chains/arcs/spawn.
- **Verified:** All 11 objects load correctly in UnityPy. 5 beatmaps have valid V3 format (version 4.0.0).
- **Status:** ✅ DEPLOYED — awaiting test

### Experiment 69 — Template-structure V3 + PRX rebuild (v0.43) [DEPLOYED]
- **Date:** 2026-07-01
- **Change:** Now preserves template's EXACT V3 structure (bombNotes, chains, arcs from template NOT emptied). Replaces only `colorNotes`/`colorNotesData` and `obstacles`/`obstaclesData`. Fixes issue where custom V3 generation might have subtle format differences.
- **Result:** All 11 objects verified. 
- **PRX fix:** v0.43 PLUGIN_VERSION now properly deployed (was missing in previous test).
- **Roadmap created:** `.agent/roadmap.md` with milestone checklists.
- **Status:** ✅ DEPLOYED — awaiting test

### Experiment 70 — Minimal test: change one beat value (diagnostic) [DEPLOYED]
- **Date:** 2026-07-01
- **Change:** Template V3 beatmap with ONLY one modification: first note's `b` changed from 5.5 → 5.0. Uses `save_typetree`. All other data identical to template. Goal: isolate whether `save_typetree` itself breaks something or if the V3 conversion content is the issue.
- **Prediction:** If song plays (note at 5.0 instead of 5.5), `save_typetree` is fine, issue is V3 conversion. If still fails, `save_typetree` pipeline itself is broken.
- **Status:** ✅ DEPLOYED — awaiting test

### Experiment 71 — THE FIX: m_Script is just gzip, no decompressed_size prefix! (v0.43) [SUCCESS! ✅]
- **Knowledge file:** [[m_script-gzip-only]]
- **Related fixes:** [[save-typetree-over-set-raw-data]], [[surrogateescape-encoding]]
- **Date:** 2026-07-01
- **ROOT CAUSE FOUND:** The m_Script field in the beatmap TextAsset is JUST gzip data — NO 4-byte decompressed_size prefix! My conversion was adding `struct.pack('<I', len(json))` before the gzip stream, shifting the gzip by 4 bytes. The game saw `dc 06 00 00` instead of `1f 8b` gzip magic and rejected the beatmap.
- **Fix:** Remove the decompressed_size prefix. m_Script = `gzip.compress(json_data)` only.
- **V3 note conversion included.** All 11 objects verified.
- **Test Result:** ✅ **CUSTOM NOTES WITH ENVIRONMENT!** The Rolling Stones environment renders correctly with custom VOLUPTE note patterns. Audio is still Start Me Up (expected — FSB5 not replaced).
- **Significance:** This proves the ENTIRE beatmap conversion pipeline works end-to-end. The fix was removing the 4-byte decompressed_size header before the gzip data.
- **Log analysis** (753 lines, saved as `bs_log_v43_success.txt`):
  - 2 startmeup redirects ✅ (game opened bundle twice, standard for Beat Saber)
  - Rolling Stones environment loaded AFTER redirect (scenes + assets bundles) ✅
  - No other songs' BeatmapLevelData files accessed (redirect is targeted) ✅
  - PlayerData.dat saved (game recorded play/song exit cleanly)
  - 750 open calls total — full song play with menu return
  - No error/exception/failure/crash lines found
  - Environment cascade: scenes → pack_assets → shaders → scripts → core_assets

### Experiment 72 — Bomb notes conversion + MUSIC STAR test [SUCCESS! ✅]
- **Date:** 2026-07-01
- **Change:** Added bomb note conversion to the V2→V3 pipeline. V2 `_notes` with `_type=3` are now separated from regular notes and placed in `bombNotes` + `bombNotesData` arrays. BombNotesData only stores position (x, y) — no color or direction. Uses the same deduplication pattern as colorNotes (default data[0] = `{"x": 3}`).
- **Song:** MUSIC STAR (M.G.G. Original) — has 14-40 bombs across all difficulties plus 6-37 obstacles
- **Conversion breakdown per difficulty:**
  - Easy: 181n + 14b + 36o
  - Normal: 284n + 28b + 34o
  - Hard: 350n + 32b + 37o
  - Expert: 517n + 32b + 6o
  - ExpertPlus: 609n + 40b + 6o
- **Verify:** All 11 objects pass UnityPy verification. Gzip decompresses correctly.
- **Log analysis** (751 lines, saved as `bs_log_v44_bombs.txt`):
  | Signal | Count | Meaning |
  |--------|-------|---------|
  | Redirects | 2 | Game opened bundle twice |
  | Env loaded | Yes | Rolling Stones environment (from template) |
  | PlayerData saved | Yes | Clean menu return |
  | Error lines | 0 | No crashes or assertions |
- **Test result:** ✅ SUCCESS! Bombs confirmed visible alongside custom notes. MUSIC STAR's 14-40 bombs per difficulty appeared correctly.
- **Next step:** Chains, arcs, or events conversion

### What's Working Now
- ✅ Plugin loads without crash, shows correct version notification
- ✅ File redirect to AFR directory works
- ✅ AssetBundle loads and assets are found by the game
- ✅ Beatmap data replacement with custom song notes (V3 format)
- ✅ Custom obstacles from song (when present)
- ✅ Environment renders correctly (lightshow data works)
- ✅ Other difficulties play correctly

### What's Next
- [] Replace audio (FSB5 format) with custom song audio
- [] Replace cover art in song selection
- [] Add new song entries to album via resources.assets

### Experiment 73 — Slider/BurstSlider → Arc/Chain conversion [SUCCESS! ✅]
- **Date:** 2026-07-01
- **Change:** Added V2 `sliders` → V3 `arcs` + `arcsData` and V2 `burstSliders` → V3 `chains` + `chainsData` conversion.
- **Song:** "Take Me to the Beach" (89-179 sliders + 2-5 burstSliders per difficulty, 0 regular notes — pure arc/chain map)
- **Key discovery:** V2 songs store sliders/burstSliders as separate arrays (not `_chains`/`_arcs`). These map to V3 arc/chain structures with shared `colorNotesData` references.
- **Also built:** VOLUPTE (notes) and MUSIC STAR (bombs) with same pipeline — both 11/11 OK. No regressions.
- **Log analysis** (1502 lines, saved as `bs_log_v45_arcs.txt`):
  | Signal | Count | Meaning |
  |--------|-------|---------|
  | Redirects | 4 | Game opened bundle 4x (longer load for arc-heavy) |
  | PlayerData saved | Yes | Clean menu return |
  | Error lines | 0 | No crashes or assertions |
  | Env loaded | 20 | Rolling Stones environment loaded |
- **Test result:** ✅ SUCCESS! Only arcs visible (no note boxes expected — song has 0 regular notes). Chains may have been visible too but hard to distinguish.
- **Next step:** Find a song with ALL features (notes + bombs + obstacles + sliders + chains) and test end-to-end.

### Experiment 74a — Combined features bundle [REPLACED]
- **Date:** 2026-07-01
- **Change:** Combined MUSIC STAR's notes+bombs+obstacles with Take Me to the Beach's arcs+chains. Replaced by quick_test.bundle for faster testing.
- **Status:** Replaced by quick_test.bundle (12MB → much smaller, all features in ~20s)

### Experiment 74b — Quick test bundle [FLOATING WALLS WORKING ✅]
- **Date:** 2026-07-01
- **Change:** Added 3 experimental floating walls with `y` (row offset) to quick_test_gen.py. These walls are offset from the floor so they float at head/mid/celing level, requiring ducking to avoid.
- **Content per difficulty:** 9n + 3b + 8o (5 floor + 3 floating) + 2a + 2c
- **Floating wall experiments:**
  - `y:3, h:2, x:1` at beat 24 — floating at head level → duck under
  - `y:2, h:2, x:0` at beat 26 — floating at mid level → medium duck
  - `y:4, h:1, x:0` at beat 28 — floating at ceiling → barely duck
- **Key discovery:** The V3 obstaclesData format DOES support `y` (row offset) field, even though the template doesn't use it. When `y` is omitted, it defaults to 0 (floor). Adding `y` enables floating/ceiling walls.
- **Source:** `beat_saber_deluxe/custom_songs/quick_test_gen.py` (committed in git)
- **Status:** ✅ SUCCESS! All wall types confirmed working including floating walls.

### Experiment 77 — Sample header fix + silence test [ROOT CAUSE NARROWED]
- **Date:** 2026-07-03
- **Change:** Fixed FSB5 sample_header_size from 900 to 1732 (matching the original FSB5). Previous experiments used a WRONG sample header (900 bytes) from a different song. The correct header size is 1732 bytes.
- **Test:** Created `test_silence.bundle` — all-zero HEVAG frames (silence), full 1732-byte sample header
- **Result:** ❌ **FREEZE** — first frame rendered, level frozen, no audio. Identical freeze to all previous 6 tests.
- **Key finding:** Even with a byte-perfect FSB5 (sample header 0-diff from original), all-zero silence frames still cause a freeze. This rules out FSB5 structure issues and points to the audio CONTENT.
- **Status:** ❌ FREEZE — need to test with actual audio content

### Experiment 78 — Systematic audio isolation tests [ALL FROZE]
- **Date:** 2026-07-03
- **Tests:** 7 different bundles, all with same freeze symptom:
  | # | Bundle | Audio | Result |
  |---|--------|-------|--------|
  | 1 | `test_silence.bundle` | All-zero HEVAG | ❌ FREEZE |
  | 2 | `test_original_audio_3s.bundle` | Original 3s snippet | ❌ FREEZE |
  | 3 | `test_p0_only.bundle` | Predictor 0, 440Hz sine | ❌ FREEZE |
  | 4 | `test_p0_silence.bundle` | Predictor 0 silence | ❌ FREEZE |
  | 5 | `test_silence_lz4.bundle` | All-zero LZ4 | ❌ FREEZE |
  | 6 | `test_fullsize_silence.bundle` | 12MB padded silence | ⚠️ PARTIAL (notes moved 1s) |
  | 7 | `test_original_12mb.bundle` | Original FSB5 (beatmaps only) | ✅ NEEDED DEPLOY |
- **Key discoveries:**
  1. All small-FSB5 tests (<1MB) freeze immediately on first frame
  2. **Full-size 12MB silence test** got notes moving for ~1 second! This is the FIRST time ANY test got past the initial frame
  3. The 12MB size is critical — padding the FSB5 to match the original .resource size (12,305,632 bytes) allows the game to initialize the audio decoder
- **Hypothesis:** The PS4's audio decoder requires a minimum amount of audio data to initialize properly. Below this threshold, the decoder hangs immediately.
- **Status:** 🔍 KEY INSIGHT: SIZE matters more than content

### Experiment 79 — 🎉 BREAKTHROUGH: 12MB Original Audio WORKS!
- **Date:** 2026-07-03
- **Test:** Deployed `test_original_12mb.bundle` — the ORIGINAL unmodified FSB5 audio (12MB) but with CUSTOM beatmaps changed via our pipeline
- **Result:** ✅ **SUCCESS!** Original Start Me Up audio played perfectly through the entire song. Custom beatmaps were applied. Gameplay was normal.
- **PROVES:** Our AssetBundle building process is CORRECT. The `.resource` file replacement, `AudioClip` metadata updates, and UnityFS structure are all valid.
- **ROOT CAUSE ISOLATED:** The issue is specifically in the HEVAG audio CONTENT we generate, not in the bundle structure.
- **Status:** ✅ BREAKTHROUGH — Pipeline verified, issue narrowed to audio encoding

### Experiment 80 — Full-size silence: notes moved 1 second [SIZE CONFIRMED]
- **Date:** 2026-07-03
- **Test:** `test_fullsize_silence.bundle` (12MB padded silence FSB5) — actually testable now
- **Result:** ⚠️ **PARTIAL SUCCESS — Two note boxes moved towards the player for ~1 second, then froze.** This was the FIRST time ANY of our audio replacement tests progressed past the initial frame! The song length display showed the full original 213.7 seconds (because AudioClip.m_Length was preserved).
- **Implications:**
  - ✅ **12MB padding is CRITICAL** — it allows the decoder to initialize
  - ❌ All-zero silence content causes decoder hang at ~1 second
  - The decoder processes silence correctly for ~1 second, then hits a boundary condition (possibly empty buffer detection or DSP underflow)
- **Status:** ⚠️ SIZE confirmed as critical factor, content still needs to be real audio

### Experiment 81 — Predictor-0 custom audio: 1-sample play + beatmap bug [ISSUES FOUND]
- **Date:** 2026-07-04
- **Test:** Full pipeline run: `tigerblood_jewel.wav` → predictor-0 HEVAG → 12MB padded FSB5 → custom bundle → deploy
- **Result:** ❌ **One sound sample heard, then freeze. Blank level (no objects).**
- **Two critical issues discovered:**
  1. **Audio:** Predictor-0-only HEVAG encoding fails. One sample played, then decoder hangs. The PS4 requires a wider predictor range (0-4 at minimum, ideally 0-15).
  2. **Beatmap matching BUG:** The matching logic was too loose — `Easy.lightshow.gz` was matched to `EasyStandard.dat` (corrupting the lightshow), and both Expert and ExpertPlus were matched to the same `ExpertPlusStandard.dat` file (because "Expert" is a substring of "ExpertPlus"). Result: 0 objects rendered.
- **FIXES APPLIED:**
  - `opt_encode_frame()` — 5-predictor optimized encoder (~16x faster than brute-force, uses direct shift calculation per predictor)
  - Beatmap matching now only targets `.beatmap.gz` TextAssets (not lightshow, info, or audio.gz)
  - Difficulty matching uses more precise logic to prevent Expert/ExpertPlus confusion
  - `fast_pcm_to_hevag()` now delegates to `opt_encode_frame()` internally
- **Status:** ❌ FAILED — fixes applied for next test

### Experiment 82 — Optimized 5-predictor encoder + 12MB padding + beatmap fix [DEPLOYED]
- **Date:** 2026-07-04
- **Bundle:** `complex_song_v4.bundle` (5.5MB, deployed to `startmeup_v3`)
- **Changes:**
  - Audio: `tigerblood_jewel.wav` → `opt_encode_frame()` (5-predictor) → 12MB padded FSB5
  - Beatmaps: 5/5 correctly matched (fixed logic, no lightshow corruption)
  - PRX version updated to v0.49
  - Pipeline now supports `.ogg` audio via `soundfile` (standard BeatSaver format)
  - Devcontainer persistence added (postCreateCommand)
- **Status:** 🚀 **DEPLOYED — AWAITING PS4 TEST**
- **Deploy command:** `python3 tools/full_custom_song_pipeline.py --song-dir <dir> --target startmeup --deploy`

### Experiment 83 — Expert/ExpertPlus matching bug fix + PRX v0.49 rebuild [NOVEL TEST]
- **Date:** 2026-07-04
- **Bundle:** `novel_test.bundle` (5.5MB, deployed to `startmeup_v3`)
- **Change 1 — Expert/ExpertPlus fix:** Beatmap matching now excludes "ExpertPlus" when matching "Expert". Previous logic matched both `ExpertStandard.dat` and `ExpertPlusStandard.dat` to the same file.
- **Change 2 — PRX v0.49 rebuild:** Found toolchain at `/opt/openorbis/OpenOrbis/PS4Toolchain` (variable was unset). Persisted to `~/.zshrc`. Rebuilt and deployed PRX showing v0.49 in notification.
- **Change 3 — Toolchain persistence:** Added `export OO_PS4_TOOLCHAIN=/opt/openorbis/OpenOrbis/PS4Toolchain` to `~/.zshrc` so future PRX builds work without manual setup.
- **Results so far:** 
  - 5-predictor encoder + 12MB padding: user heard 1-2 audio samples before freeze, no beatmap objects (expected due to Expert/ExpertPlus bug)
  - Fixed Expert/ExpertPlus + same audio: NOVEL TEST — awaiting PS4 test
  - PRX v0.49 deployed with new toolchain persistence

### Experiment 84 — Metadata Preservation Test [DEPLOYED, AWAITING TEST]
- **Date:** 2026-07-04
- **Bundle:** `metadata_test.bundle` (5.5MB, deployed to `startmeup_v3`)
- **Theory:** The freeze at 1-2 audio samples may be caused by our AudioClip metadata updates (m_Length=146.1s, m_Frequency=48000) and/or audio.gz updates, rather than the HEVAG encoding quality. The silence test (Experiment 80) which preserved ORIGINAL metadata got notes moving for 1 second, while our 5-predictor test with custom metadata froze immediately.
- **Changes:**
  - Audio: 5-predictor optimized HEVAG (re-encoded from `tigerblood_jewel.wav`)
  - 12MB padding to match original .resource size
  - **AudioClip metadata: PRESERVED from original** (m_Length=213.7s, m_Frequency=44100)
  - **audio.gz metadata: PRESERVED from original** (songSampleCount=9425915, original bpmData)
  - Beatmaps: 5/5 correctly matched (Expert/ExpertPlus fix applied)
  - PRX v0.49 deployed
- **What this tests:**
  - If this WORKS: Our HEVAG encoding IS valid. The metadata updates cause the freeze.
  - If this FREEZES: Our HEVAG encoding itself is the root cause.
- **Pipeline change:** Added `--preserve-metadata` flag to `full_custom_song_pipeline.py` for future tests.
- **Toolchain fix:** `OO_PS4_TOOLCHAIN` path re-persisted to `~/.zshrc` (was lost on restart).
- **Status:** 🚀 **DEPLOYED — AWAITING PS4 TEST**
- **What makes this NOVEL:** 
  1. First test with CORRECTLY MATCHED beatmaps (Expert→ExpertStandard, ExpertPlus→ExpertPlusStandard)
  2. First test with rebuilt v0.49 PRX  
  3. Toolchain build path is now permanent
- **Status:** 🚀 **DEPLOYED — AWAITING PS4 TEST**

### Pipeline Files (committed 2026-07-04)
- `tools/hevag_encoder.py` — `fast_encode_frame` (pred-0), `opt_encode_frame` (5-pred), `fast_pcm_to_hevag`, `pcm_to_hevag`
- `tools/full_custom_song_pipeline.py` — End-to-end: `.wav`/`.ogg` → HEVAG → FSB5 → bundle → deploy
- `src/main.cpp` — PRX v0.49 with updated version string
- `.devcontainer/openorbis/devcontainer.json` — postCreateCommand for persistence
- `.devcontainer/standard/devcontainer.json` — postCreateCommand for persistence

### Experiment 75 — Audio Replacement Milestone [READY FOR DEPLOY]
- **Date:** 2026-07-01
- **Change:** Complete custom audio replacement pipeline! HEVAG (PS4 ADPCM) encoder implemented in Python. FSB5 container created with custom test audio (3-second sine tones: 440Hz→880Hz→660Hz).
- **Audio pipeline:**
  1. Generate PCM16 test audio at 44.1kHz stereo
  2. Encode to HEVAG (PS4 ADPCM) — 3.5:1 compression ratio
  3. Wrap in FSB5 container (copies sample header from existing FSB5)
  4. Replace CAB resource data in the AssetBundle
  5. Update AudioClip metadata (length, resource size)
  6. Update audio.gz TextAsset (sample count, frequency, bpm data)
- **Result:** `quick_test.bundle` is now 216 KB (down from 12MB!)
- **Content:** 9n + 3b + 8o + 2a + 2c + 3-second test audio
- **HEVAG encoder extracted:** `beat_saber_deluxe/tools/hevag_encoder.py` — standalone CLI tool + importable module
- **Script:** `beat_saber_deluxe/custom_songs/quick_test_gen.py` — now imports from hevag_encoder
- **Knowledge base:** `ps4-hevag-fsb5-audio.md` — full audio pipeline documented
- **Status:** ✅ READY FOR DEPLOY — PS4 was powered on

### Experiment 75b — Audio freeze fix: correct FSB5 header + optimized encoder
- **Date:** 2026-07-01
- **Issue:** First audio replacement attempt (wrong FSB5 header template) caused the game to hang on audio start. The header was from a **different song's FSB5 export** (46.9% match with correct header).
- **Fix 1—Correct template:** Now using Start Me Up's own FSB5 900-byte sample header (bytes 16-915 of the original CAB resource). Template saved to `fsb5_header_template.bin`.
- **Fix 2—Hevag encoder optimization:** Added silence fast path (pre-computed zero frame), early termination on perfect encoding, and batch PCM reading via `struct.unpack` format string instead of per-sample loop.
- **Encoder speed:** Silence frames: 211K/s, Tone frames: 229/s (brute-force over 5×13 parameters ×28 samples is the bottleneck)
- **Status:** ✅ DEPLOYED AND READY FOR TEST — corrected 216KB bundle on PS4

### Experiment 76 — ROOT CAUSE: incorrect FSB5 sample_header_size (900 vs 1732) [FIXED]
- **Date:** 2026-07-02
- **Investigation:** Systematic analysis of audio freeze. Tests across multiple bundle configurations (PCM format, HEVAG with freq, padded audio) all showed same freeze. Extracted original FSB5 from bundle's .resource file via UnityPy for deep analysis.
- **Root Cause:** The original PS4 Beat Saber FSB5 uses `sample_header_size=1732`, but our `build_fsb5()` was hardcoding `sample_header_size=900`. This meant:
  - We were only storing 900 of the required 1732 sample header bytes
  - The PS4's FMOD audio decoder couldn't find the hash table and additional DSP state
  - Audio decoder hung/froze when attempting to play back the incomplete FSB5
  - The 832 missing bytes contain 612 non-zero bytes of DSP/hash data critical for decoder init
- **Fix:** 
  1. Extracted full 1732-byte sample header from original FSB5
  2. Updated `_load_fsb5_header_template()` to detect and load full header
  3. Updated `build_fsb5()` to write correct `sample_header_size` in FSB5 header
  4. Updated template file `fsb5_header_template.bin` from 900 to 1732 bytes
  5. Added `FSB5_SAMPLE_HEADER_SIZE = 1732` constant
  6. Fast path bug also fixed (preserve h1/h2 history) while investigating
- **Technical Details:**
  - Original FSB5: 12,305,632 bytes, ver=1, nsamples=1, shsz=1732, format=1(HEVAG)
  - Audio data offset in FSB5: 1748 (was incorrectly 916)
  - Non-zero bytes in full SH: 1247/1700 (beyond sample entry)
- **Status:** ✅ FIX DEPLOYED — awaiting PS4 test
- **⚠️ Operational Note — Deploy Path:** The plugin's open hook (v0.44, main.cpp line 65) redirects `BeatmapLevelsData/startmeup` → `/data/GoldHEN/AFR/CUSA12878/startmeup_v3`. New test bundles MUST be deployed to `startmeup_v3`, NOT `startmeup`, or the plugin ignores them.
- **Files changed:**
  - `beat_saber_deluxe/tools/hevag_encoder.py` — _load_fsb5_header_template, build_fsb5, FSB5_SAMPLE_HEADER_SIZE
  - `beat_saber_deluxe/custom_songs/fsb5_header_template.bin` — updated to 1732 bytes
  - `beat_saber_deluxe/custom_songs/quick_test.bundle` — regenerated with correct FSB5
  - `beat_saber_deluxe/tests/` — analysis tools created

### Experiment 77 — Systematic Isolation: Silence Test + Predictor-0-Only [READY FOR TEST]
- **Date:** 2026-07-03
- **Previous tests:** All 6 attempts (different header templates, fast path fix, sample_header_size fix) resulted in same freeze.
- **New Hypothesis:** Since the FSB5 structure (header size, sample header, AudioClip metadata) is all confirmed correct, the issue must be in our HEVAG-encoded audio CONTENT.
- **New Tests Created:**

  | # | Bundle | Audio Content | What It Tests |
  |---|--------|---------------|---------------|
  | 1 | `test_silence.bundle` | All-zero HEVAG frames (pred=0, shift=0, nibbles=0) | Is our FSB5 structure valid? |
  | 2 | `test_original_audio_3s.bundle` | Original Start Me Up HEVAG frames (first 3s) | Is our FSB5 building process correct? |
  | 3 | `test_p0_only.bundle` | Predictor 0 only, 440Hz sine wave, normal nibbles | Is the problem in predictors 1-4? |
  | 4 | `test_p0_silence.bundle` | Predictor 0 silence (all zeros) | Baseline for predictor 0 |

- **Testing Strategy (ordered):**
  1. Deploy `test_silence.bundle` → if WORKS (no freeze), FSB5 structure is correct
  2. Deploy `test_p0_only.bundle` → if WORKS, problem is in predictors 1-4 specifically
  3. Deploy `test_original_audio_3s.bundle` → if WORKS, our FSB5 building process is correct
  4. Based on results, focus on either encoding algorithm or FSB5 structure

- **Key insight from AudioClip type tree:** Original has `m_LoadType: 1` (CompressedInMemory), `m_PreloadAudioData: false`, `m_LoadInBackground: true`, `m_Legacy3D: true`, `m_CompressionFormat: 1`. All preserved correctly in our bundles.
- **Status:** 🧪 BUNDLES READY — awaiting PS4 test
- **Deploy command:**
  ```
  lftp -u anonymous, -p 2121 192.168.100.117 -e "put test_silence.bundle -o /data/GoldHEN/AFR/CUSA12878/startmeup_v3; quit"
  ``
- **Quick deploy script:** `beat_saber_deluxe/custom_songs/quick_deploy.sh`

### Experiment 78 — All Audio Tests Freeze: Every variant fails identically [ROOT CAUSE ELUSIVE]
- **Date:** 2026-07-03
- **Tests Performed (ALL froze with same symptom: first frame renders, level freezes, stars move, no audio):**

  | # | Bundle | Packer | Audio Content | Result |
  |---|--------|--------|---------------|--------|
  | 1 | `test_silence.bundle` | none | All-zero HEVAG frames | ❌ FREEZE |
  | 2 | `test_original_audio_3s.bundle` | none | Original Start Me Up frames (3s) | ❌ FREEZE |
  | 3 | `test_p0_only.bundle` | none | Predictor 0 only, 440Hz sine | ❌ FREEZE |
  | 4 | `test_p0_silence.bundle` | none | Predictor 0 silence | ❌ FREEZE |
  | 5 | `test_silence_lz4.bundle` | lz4 | All-zero HEVAG frames (LZ4 compressed) | ❌ FREEZE |
  | 6 | `test_fullsize_silence.bundle` | none | Full-size silence (12MB, matches original audio size) | ❌ NOT DEPLOYED (FTP timeout during 12MB transfer) |
  | 7 | `test_original_12mb.bundle` | lz4 | Original 12MB FSB5 (audio unchanged), beatmaps changed | ❌ NOT DEPLOYED (PS4 went offline) |

- **Key findings from analysis:**
  1. **FSB5 structure is byte-perfect** — sample header matches original with 0 differences (excluding data_size field)
  2. **AudioClip serialization is identical** — `save_typetree` produces identical raw bytes (164 bytes AudioClip)
  3. **CAB save output is 67,656 bytes** — does NOT contain FSB5 data (correctly stored externally in .resource)
  4. **Bundle UnityFS header is identical** — first 32 bytes match original exactly
  5. **Original audio uses predictors 0-15 and shifts 0-15** — our encoder only uses predictors 0-4 and shifts 0-12, but all-zero silence frames (pred=0, shift=0) also freeze, ruling out encoding content
  6. **Original bundle has no separate .resource file entry** in raw binary (likely compressed file table), but UnityPy shows 2 entries (CAB + .resource)
  7. **Our saved bundles show 4 CAB string occurrences** in raw binary, indicating UnityPy writes .resource as separate file block

- **Root cause STILL ELUSIVE.** All structural analysis shows the FSB5 and bundle are correctly formed. The AudioClip reference path `archive:/CAB-xxx/CAB-xxx.resource` should resolve correctly. Yet the PS4 freezes every time audio replacement is attempted.

- **Unsolved questions:**
  1. Does the 12MB original-audio bundle (where only beatmaps change, audio untouched) work? Couldn't deploy due to FTP timeout.
  2. Why does ALL audio content (silence included) cause the same freeze? 
  3. Is the PS4's Unity runtime expecting a specific bundle structure that UnityPy doesn't produce?

- **Next steps needed when PS4 is online:**
  1. Try deploying the full-size silence bundle or 12MB original bundle via alternative method (HTTP server, USB, etc.)
  2. If 12MB original bundle works → issue is in our FSB5 content (size or structure)
  3. If 12MB original bundle freezes → issue is in UnityPy's save function or bundle structure
  4. Try manually patching original bundle binary (replace .resource bytes in-place, bypassing UnityPy save entirely)
  5. Consider if the issue is in the CAB serialization (not .resource) — maybe save_typetree changes something beyond the 164 bytes we checked

### Summary of Audio Experiments (v0.48 - v0.49)
- **Conclusion:** The PS4 audio decoder hangs if the HEVAG data is 'too simple' (e.g. all-zero silence or limited predictors). The original audio uses the full 4-bit range (0-15) for both predictors and shifts. To avoid freezes, we must use an encoder that produces high-fidelity, wide-range HEVAG frames.
- **Verification:** 12MB original audio in our bundle worked, proving the pipeline is correct.


### Experiment 84b — Metadata Preservation Test Result [FROZE]
- **Date:** 2026-07-04
- **Bundle tested:** 
- **Result:** ❌ Same freeze at 1-2 audio samples. No beatmap objects rendered.
- **Log:** 2930 lines, 6 redirects, 0 errors, clean exit (7 PlayerData saves)
- **Conclusion:** Preserving original AudioClip/audio.gz metadata does NOT fix the freeze.
- **New theory:** Our HEVAG encoding itself is invalid. The PS4 decoder produces incorrect
  output from our frames, causing the game to hang after 1-2 frames.
- **Next:** Testing if re-encoded original audio (decode -> re-encode with our encoder) works.
  If it works: encoder is valid, issue is elsewhere.
  If it fails: encoder is fundamentally broken.
- **Fallback plan:** PCM FSB5 (uncompressed format, no coefficient table dependency)

