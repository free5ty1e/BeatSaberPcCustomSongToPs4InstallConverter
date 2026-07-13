---
name: plugin-architecture
description: "GoldHEN plugin architecture: hook system, PRX format, CRT initialization, and build pipeline"
metadata:
  type: entity
---

# Plugin Architecture

The Beat Saber Deluxe plugin is a GoldHEN PRX (PS4 PRX plugin) that intercepts file `open()` calls to redirect BeatmapLevelData file loads to custom AssetBundles on the AFR partition.

## Component Overview

The plugin consists of a single file (`src/main.cpp`) that:
1. Hooks the `open()` syscall via GoldHEN's HOOK_INIT/HOOK_CONTINUE macros
2. Intercepts paths containing `BeatmapLevelData/startmeup`
3. Redirects them to an AssetBundle stored in `/data/GoldHEN/AFR/CUSA12878/`
4. Logs all file operations to `bs_log.txt` for debugging

## Key Architecture Decisions

### PRX Format (FSELF)
The final output must be **FSELF** format (SCE magic `4f 15 3d 1d`), not bare OELF (`7f 45 4c 46`). The `create-fself` tool from OpenOrbis generates FSELF when built with `--lib` flag. GoldHEN expects FSELF for plugin loading.

### CRT Initialization
PS4 PRX plugins DO NOT use `plugin_main()` or `__attribute__((constructor))`. Instead:
- Entry point must be `_init` (via `-e _init` linker flag)
- Link against `crtprx.o` (not `crtlib.o`) for proper CRT setup
- TLS sections need `--no-tls-optimize` to avoid musl TLS conflicts
- Final binary uses `.oelf` extension (not `.sprx`)

### Hook System
GoldHEN provides `HOOK_INIT` and `HOOK_CONTINUE` macros for syscall hooking:
```cpp
HOOK_INIT(hook_open);
// ...
int r = HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), np, flags, 0);
```
Re-entry guard with `in_hook` flag prevents infinite recursion:
```cpp
static int in_hook = 0;
if (in_hook) return HOOK_CONTINUE(...);
in_hook = 1;
// do work
in_hook = 0;
```
This guard is critical because inside the hook we call `sceKernelOpen` for logging or redirected paths.

### Logging
- Uses `sceKernelOpen`/`sceKernelWrite`/`sceKernelClose` (not `fopen`/`fwrite` which could deadlock)
- Log path: `/data/GoldHEN/AFR/CUSA12878/bs_log.txt`
- Directory auto-created via `sceKernelMkdir` with 0777 permissions
- File permissions set via `sceKernelFchmod` to 0644
- Notification sent via `/dev/notification0` on plugin load

## Dynamic Redirect Config

As of v1.0, the redirect table is no longer hardcoded in the plugin. Instead, the plugin reads song→bundle mappings from an external JSON config file at runtime.

### Config File
**Path:** `/data/GoldHEN/AFR/CUSA12878/redirects.json`

```json
{
  "titleId": "CUSA12878",
  "afrBase": "/data/GoldHEN/AFR",
  "redirects": {
    "startmeup": "startmeup_custom_v3",
    "angry": "angry_custom_v3"
  }
}
```

### How it Works
1. On startup, `load_redirects()` opens `redirects.json` using POSIX `open()` from the AFR path
2. If found, it parses the JSON to extract key-value pairs from the `redirects` object
3. Each key is a slot ID (prefixed with `BeatmapLevelsData/`) and the value is either:
   - A **bundle name** (resolved to `AFR_BASE/TITLE_ID/<name>`)
   - A **full AFR path** (used as-is if it contains `/`)
4. **No hardcoded fallback table** — if `redirects.json` is missing, empty, or malformed, the plugin loads zero redirects and logs an error
5. All redirects must come from `redirects.json` — enabling/disabling is done by modifying the config file

### ⚠️ Critical: POSIX `open()` vs `sceKernelOpen()` for AFR

**Always use POSIX `open()` (not `sceKernelOpen()`) when reading from the AFR path.**

GoldHEN's Advanced File Redirect (AFR) hooks the POSIX `open()` syscall at the kernel level. When a process calls `open("/data/GoldHEN/AFR/CUSA12878/file")`, GoldHEN intercepts it and maps the path to the actual physical storage location. However, `sceKernelOpen()` is a direct syscall that **bypasses** GoldHEN's hook entirely.

This means:
- Files **created by the plugin** with `sceKernelOpen()` + `O_CREAT` (like `bs_log.txt`) exist at the GoldHEN-mapped AFR path
- Files **uploaded via FTP** (like `redirects.json`) exist at the **physical** path on internal storage
- Reading with `sceKernelOpen()` sees the mapped path — NOT the physical path where FTP put the file
- Reading with POSIX `open()` goes through GoldHEN's hook, which correctly resolves the physical path

**Consequence:** The `load_redirects()` function (as of v0.57) uses `open()` first, then falls back to `sceKernelOpen()`. This ensures FTP-uploaded config files are found. The `log_write()` function correctly uses `sceKernelOpen()` with `O_CREAT` to append to the log file, because it's creating/opening at the mapped path.

### Modifying Redirects Without Rebuilding
To add, remove, or change a redirect:
1. Edit `redirects.json` on the PS4 via FTP at `/data/GoldHEN/AFR/CUSA12878/redirects.json`
2. Restart Beat Saber (no full PS4 reboot needed)
3. Check `bs_log.txt` to verify the loaded count

Example — adding a new redirect:
```json
{
  "redirects": {
    "100bills": "/data/GoldHEN/AFR/CUSA12878/100bills_custom_v3"
  }
}
```

### Config File Source
The `redirects.json` at the project root (`beat_saber_deluxe/redirects.json`) is the source of truth. It's deployed alongside the bundles by `deploy_all.sh`. The pipeline does NOT generate it automatically — edit the file directly when changing slots.

## File Structure
```
beat_saber_deluxe/
  src/main.cpp           — Plugin source code
  redirects.json          — Dynamic redirect config (source of truth)
  include/               — GoldHEN SDK headers
  obj/                   — Build artifacts
  beat_saber_deluxe.prx   — Final FSELF plugin
  beat_saber_deluxe_debug.prx — Debug build (verbose logging)
  Makefile               — Build configuration
  deploy_all.sh          — Deploy script (plugin + bundles + config)
  custom_songs/          — Generated custom AssetBundles
```

See also: [[ps4-file-system-redirects]], [[toolchain-and-build]], [[development-workflow]]
