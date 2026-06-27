// Beat Saber Deluxe v0.34 — Find Unity AssetBundle.LoadAsset via dlsym
// Step 1 of Option B (hooking Unity AssetBundle functions).
// This version only SEARCHES for the function — doesn't hook it.
// Reports which Unity function names are found in loaded libraries.

#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <dlfcn.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>
#include <GoldHEN/Syscall.h>

#define PLUGIN_VERSION "v0.34"
#define AFR_BASE  "/data/GoldHEN/AFR"
#define TITLE_ID "CUSA12878"
#define LOG_PATH AFR_BASE "/" TITLE_ID "/bs_log.txt"

extern "C" FILE *fopen(const char *path, const char *mode);
extern "C" int open(const char *path, int flags, ...);

HOOK_INIT(hook_fopen);
HOOK_INIT(hook_open);

static int in_hook = 0;
static int log_ok = 0;

static void ensure_dir(void) {
    sceKernelMkdir(AFR_BASE, 0777);
    sceKernelMkdir(AFR_BASE "/" TITLE_ID, 0777);
}

static int log_write(const char *msg) {
    if (!log_ok) ensure_dir();
    int fd = sceKernelOpen(LOG_PATH, O_WRONLY|O_CREAT|O_APPEND, 0644);
    if (fd < 0) { log_ok = 0; return 0; }
    sceKernelFchmod(fd, 0644);
    if (!log_ok) log_ok = 1;
    sceKernelWrite(fd, msg, strlen(msg));
    sceKernelWrite(fd, "\n", 1);
    sceKernelClose(fd);
    return 1;
}

static FILE *fh(const char *p, const char *m) {
    if (in_hook) return HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), p, m);
    in_hook = 1;
    char lb[512]; snprintf(lb,sizeof(lb),"fopen:%s",p?: "NULL"); log_write(lb);
    FILE *r = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), p, m);
    in_hook = 0;
    return r;
}

static int open_hook(const char *path, int flags, ...) {
    if (in_hook) return HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    in_hook = 1;
    const char *np = NULL;
    if (path) {
        if (strstr(path, "resources.assets") && !strstr(path, "/AFR/"))
            np = AFR_BASE "/" TITLE_ID "/resources_patched.assets";
        if (strstr(path, "BeatmapLevelsData/startmeup"))
            np = AFR_BASE "/" TITLE_ID "/100bills";
    }
    char lb[512]; snprintf(lb,sizeof(lb),"open:%s",path?: "NULL");
    if (np) { char r[512]; snprintf(r,sizeof(r)," -> %s",np); strncat(lb,r,sizeof(lb)-strlen(lb)-1); }
    log_write(lb);
    int r = np ? HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), np, flags, 0)
               : HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    in_hook = 0;
    return r;
}

// Try to find a symbol using both dlsym and sys_dynlib_dlsym
static int try_find_sym(const char* name, void** out) {
    *out = NULL;
    // Try POSIX dlsym first
    *out = dlsym(RTLD_DEFAULT, name);
    if (*out) return 1;
    // Try GoldHEN syscall
    if (sys_dynlib_dlsym(-1, name, out) == 0 && *out) return 1;
    return 0;
}

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;(void)args;
    OrbisNotificationRequest r;

    log_write("=== BS Deluxe v0.34 started ===");
    log_write("Searching for Unity AssetBundle functions via dlsym...");

    // NO JAILBREAK — AFR handles writes via sceKernelOpen

    // fopen hook via Detour
    Detour_Construct(&Detour_hook_fopen, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_fopen, (uint64_t)(void*)&fopen, (void*)fh);

    // open hook via Detour
    Detour_Construct(&Detour_hook_open, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_open, (uint64_t)(void*)&open, (void*)open_hook);

    // Search for Unity AssetBundle functions
    const char* sym_names[] = {
        "UnityEngine_AssetBundle_LoadAsset_Internal_string_Type",
        "UnityEngine_AssetBundle_LoadAsset_Internal",
        "UnityEngine_AssetBundle_LoadFromFile_string",
        "UnityEngine_AssetBundle_LoadFromFile",
        "AssetBundle_LoadAsset_Internal",
        "AssetBundle_LoadFromFile",
        "_ZN13UnityEngine6AssetBundle12LoadFromFileENS_6StringE",
        "_ZN13UnityEngine6AssetBundle22LoadAsset_InternalEPNS_6StringEPNS_4TypeE",
    };
    int found = 0;
    char log_buf[1024];
    snprintf(log_buf, sizeof(log_buf), "=== dlsym results ===");
    log_write(log_buf);

    for (size_t i = 0; i < sizeof(sym_names)/sizeof(sym_names[0]); i++) {
        void* addr = NULL;
        int r = try_find_sym(sym_names[i], &addr);
        if (r && addr) {
            snprintf(log_buf, sizeof(log_buf), "FOUND: %s @ %p", sym_names[i], addr);
            found++;
        } else {
            snprintf(log_buf, sizeof(log_buf), "NOT FOUND: %s", sym_names[i]);
        }
        log_write(log_buf);
    }

    snprintf(log_buf, sizeof(log_buf), "Total Unity symbols found: %d", found);
    log_write(log_buf);

    // Notification
    memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
    if (found > 0) {
        snprintf(r.message,sizeof(r.message),"Unity syms found: %d", found);
    } else {
        snprintf(r.message,sizeof(r.message),"No Unity syms found");
    }
    sceKernelSendNotificationRequest(0,&r,sizeof(r),0);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;(void)args;
    return 0;
}
