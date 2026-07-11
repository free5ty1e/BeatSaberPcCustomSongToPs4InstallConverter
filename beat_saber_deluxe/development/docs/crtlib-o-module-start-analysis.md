---
name: crtlib-o-module-start-analysis
description: "Root cause of failing heartbeat test — crtlib.o's module_start does not call plugin_main()"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 69fde7e2-048c-4fc0-82f5-02520270bebe
---

The OpenOrbis SDK's `crtlib.o` provides a `module_start` function that ONLY iterates the `__init_array` (calling `__attribute__((constructor))` functions) and returns 0. It does NOT call any user-defined function named `plugin_main()`.

This is the root cause of why all heartbeat tests (Experiments 4a-4c) have failed — the plugin loads and returns 0 (success), but our heartbeat code in `plugin_main()` is never executed.

**Fix:** Change `plugin_main()` to use `__attribute__((constructor))` so it gets registered in the init array, OR restructure to define `module_start`/`module_stop` directly and drop `crtlib.o`.

**Why:** We assumed `crtlib.o` called `plugin_main()` by convention, but disassembly proves it only runs the static init array. See [[rb4dx-plugin-architecture-reference]] for the correct pattern.

**How to apply:** In `main.cpp`, change:
```cpp
extern "C" int plugin_main() { ... }
```
to:
```cpp
__attribute__((constructor))
void plugin_init() { ... }
```
