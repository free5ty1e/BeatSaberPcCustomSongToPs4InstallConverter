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

## File Structure
```
beat_saber_deluxe/
  src/main.cpp           — Plugin source code
  include/               — GoldHEN SDK headers
  obj/                   — Build artifacts
  beat_saber_deluxe.prx   — Final FSELF plugin
  Makefile               — Build configuration
  custom_songs/          — Generated custom AssetBundles
```

See also: [[ps4-file-system-redirects]], [[toolchain-and-build]], [[development-workflow]]
