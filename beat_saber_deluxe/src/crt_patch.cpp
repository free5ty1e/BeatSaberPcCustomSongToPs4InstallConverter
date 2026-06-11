// CRT replacement data sections for PS4 PRX format.
// Replaces what crtlib.o normally provides, so we can define
// our own module_start/module_stop without symbol conflicts.

#include <stdint.h>
#include <stddef.h>
#include <stdio.h>

// module_start is defined in main.cpp — we call it from _init
extern "C" int module_start(size_t argc, const void *args);
extern "C" int module_stop(size_t argc, const void *args);

// --- .data.sce_module_param (required by create-fself for PRX) ---
// Content mirrors crtlib.o's _sceProcessParam data.
// Format: SceModuleParam structure.
struct __attribute__((packed)) SceModuleParam {
    uint32_t size;     // 0x18 = 24 bytes total
    uint32_t pad;      // 0
    uint64_t magic;    // module param magic
    uint64_t flags;    // module flags
};

static const SceModuleParam sce_module_param
__attribute__((section(".data.sce_module_param"), used)) = {
    .size = 0x18,
    .pad = 0,
    .magic = 0x000000013c13f4bf,
    .flags = 0x0000000100000051,
};

// --- .data (minimal CRT data) ---
// __dso_handle: used by libc++ for __cxa_atexit / destructor registration.
// The value is typically a pointer to itself.
static void* __dso_handle_trap
__attribute__((section(".data"), used)) = nullptr;

// _sceLibc: libc control block. Needed by libc on PS4.
// Contains heap/pthread params. NULL = defaults.
static void* _sceLibc
__attribute__((section(".data"), used)) = nullptr;

// --- _init / _fini ---
// GoldHEN calls _init when loading the plugin (not module_start).
// _init does PRX initialization then calls module_start for plugin init.
extern "C" void _init(void) {
    // Heartbeat: write file to prove _init was called by GoldHEN
    FILE* f = fopen("/data/custom/bs_deluxe/heartbeat.txt", "w");
    if (f) {
        fprintf(f, "Heartbeat: _init called successfully!\n");
        fclose(f);
    }
    // Call module_start for proper plugin initialization
    module_start(0, NULL);
}

extern "C" void _fini(void) {
    module_stop(0, NULL);
}
