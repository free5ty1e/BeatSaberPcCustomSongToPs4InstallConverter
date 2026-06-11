# Project Summary: Beat Saber PS4 Custom Song Support
**Last Updated:** 2026-06-10
**Current Status:** Experiment 4c (Heartbeat) - Awaiting Test with Entry Point Fix

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

### Experiment 4c: Heartbeat (entry point fix) [CURRENT]
- **Status:** AWAITING TEST
- **What we tried:**
  - Added `-e module_start` to linker flags in Makefile
  - Verified `e_entry` = `0x53e0` (points to `module_start`)
  - Scoped `plugins.ini` to Beat Saber only: `[CUSA12878]` instead of `[default]`
  - Rebuilt and re-uploaded plugin + `plugins.ini`
- **Expected Result:** `heartbeat.txt` appears in `/data/custom/bs_deluxe/` after boot + game launch
- **Next step if successes:** Build proper hooking plugin with `mprotect` and `sceFileUtilsOpen`
- **Next step if fails:** Investigate GoldHEN plugin format requirements more deeply (check RB4DX-Plugin.prx as reference)

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
```

### Critical compiler flags (Makefile)
- **Target triple:** `--target=x86_64-pc-freebsd12-elf` (MUST be this, NOT linux-gnu)
- **Sysroot:** `-isysroot $(OO_PS4_TOOLCHAIN)`
- **Linker:** `ld.lld` with script `$(TOOLCHAIN)/link.x`
- **Entry point:** `-e module_start` (CRITICAL - must be set explicitly)
- **CRT for libraries:** `$(TOOLCHAIN)/lib/crtlib.o` (NOT `crt1.o` which is for eboot)
- **Output packaging:** `create-fself --lib=beat_saber_deluxe.prx --paid 0x3800000000000011`

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

### Phase 5: Iterate
Based on results:
- **heartbeat.txt found:** Plugin loads. Move to Experiment 5 (safe hooking with mprotect)
- **No heartbeat:** Check entry point, check plugins.ini format, check GoldHEN compatibility

## File Reference
- `/workspace/beat_saber_deluxe/src/main.cpp` - Plugin entry point (`plugin_main`)
- `/workspace/beat_saber_deluxe/src/hooks.cpp` - Hook utilities (`find_symbol`, `install_hook`)
- `/workspace/beat_saber_deluxe/include/bs_deluxe.h` - Plugin definitions
- `/workspace/beat_saber_deluxe/include/hooks.h` - Hook function declarations
- `/workspace/beat_saber_deluxe/Makefile` - Build system
- `/workspace/beat_saber_deluxe/beat_saber_deluxe.prx` - Compiled binary
- `/workspace/plugins.ini` - GoldHEN plugin configuration (deployed to PS4)
- `/workspace/resources_patched.assets` - Modified manifest
- `/workspace/CustomSong` - Test song AssetBundle
- `/workspace/.devcontainer/openorbis/` - OpenOrbis SDK installation
- `/workspace/.agent/project_summary.md` - This file

## Key Technical Decisions
1. **Plugin over PKG:** `.prx` plugin via GoldHEN chosen for rapid iteration vs full PKG rebuild
2. **Sacrifice Song:** "Start Me Up" (Rolling Stones) selected as the hijack target
3. **Sacrifice Replacement:** `CustomSong` bundle (clone of $100 Bills) as test replacement
4. **Toolchain:** OpenOrbis SDK for cross-compilation (provides PS4 headers, linker script, `create-fself`)
5. **CUSA scoping:** Plugin registered under `[CUSA12878]` (Beat Saber) so it only loads for this game
