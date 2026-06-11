// CRT replacement data sections for PS4 PRX format.
// Replaces what crtlib.o normally provides, so we can define
// our own module_start/module_stop without symbol conflicts.

#include <stdint.h>
#include <stddef.h>

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

// --- _init / _fini stubs ---
// These are called by the dynamic linker on load/unload.
// We keep them empty since our init/deinit is in module_start/module_stop.
extern "C" void _init(void) {}
extern "C" void _fini(void) {}
