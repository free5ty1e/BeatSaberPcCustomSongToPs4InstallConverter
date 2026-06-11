---
name: rb4dx-plugin-architecture-reference
description: "Reference architecture from working GoldHEN plugin RB4DX — module_start/stop pattern, GoldHEN SDK HOOK macros, CRT differences"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 69fde7e2-048c-4fc0-82f5-02520270bebe
---

RB4DX (Rock Band 4 Deluxe) is a working GoldHEN plugin that demonstrates the correct architecture for PS4 PRX plugins. Key differences from our current approach:

**Entry:** Uses GoldHEN SDK's `crtprx.o` with `-e _init` (NOT OpenOrbis's `crtlib.o` with `-e module_start`). The CRT provides `_init` which calls the plugin's `module_start()`.

**Plugin entry:** Define `int32_t attr_public module_start(size_t argc, const void *args)` with `__attribute__((visibility("default")))`.

**Hook system:** GoldHEN SDK provides `HOOK_INIT`, `HOOK`, and `HOOK_CONTINUE` macros that handle mprotect + trampoline setup automatically.

**Base address:** Use `sys_sdk_proc_info(&procInfo)` from GoldHEN SDK to get the game's load address, then use `base_address + known_offset` for hook targets (offset is game-version-specific).

**Libraries:** `-lGoldHEN_Hook -lkernel -lSceLibcInternal -lSceSysmodule -lScePad`

**Logging:** `klog()` via `final_printf()` macro — writes to kernel debug log (viewable via GoldHEN).

Source: `/workspace/beat-saber-ps4-custom-songs/rb4dx_plugin_source/source/main.c`
Makefile: `/workspace/beat-saber-ps4-custom-songs/rb4dx_plugin_source/Makefile`

See also [[crtlib-o-module-start-analysis]] for why our current approach fails.
