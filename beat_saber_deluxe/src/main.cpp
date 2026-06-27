// Beat Saber Deluxe v0.30 — OPEN hook redirect + AFR logging
// v0.29 log proved: game uses open() for EVERYTHING. No fopen() calls at all.
// Redirect logic moved from fopen hook to open hook where it actually fires.
// Custom files deployed to /data/GoldHEN/AFR/CUSA12878/ (game can read this dir).

#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.31"
#define AFR_BASE  "/data/GoldHEN/AFR"
#define TITLE_ID "CUSA12878"
#define LOG_PATH AFR_BASE "/" TITLE_ID "/bs_log.txt"

extern "C" FILE *fopen(const char *path, const char *mode);
extern "C" int open(const char *path, int flags, ...);

HOOK_INIT(hook_fopen);
HOOK_INIT(hook_open);

static int in_hook = 0;
static int log_ok = 0;

// Ensure directory exists
static void ensure_dir(void) {
    sceKernelMkdir(AFR_BASE, 0777);
    sceKernelMkdir(AFR_BASE "/" TITLE_ID, 0777);
}

// Write to log file, returns 1 on success
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

// fopen hook — kept for compatibility but game NEVER calls fopen (proven by v0.29 log)
static FILE *fh(const char *p, const char *m) {
    if (in_hook) return HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), p, m);
    in_hook = 1;
    char lb[512]; snprintf(lb,sizeof(lb),"fopen:%s",p?: "NULL"); log_write(lb);
    FILE *r = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), p, m);
    in_hook = 0;
    return r;
}

// open hook — logs path, handles ALL redirects (game uses open() exclusively)
static int open_hook(const char *path, int flags, ...) {
    if (in_hook) return HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    in_hook = 1;

    const char *np = NULL;
    if (path) {
        // Redirect resources.assets to patched version in AFR directory
        if (strstr(path, "resources.assets") && !strstr(path, "/AFR/"))
            np = AFR_BASE "/" TITLE_ID "/resources_patched.assets";

        // NOTE: startmeup redirect DISABLED for diagnostic pass-through.
        // We want to log what files the game opens during NORMAL song loading
        // so we can find where $100 Bills' level data is and redirect to it.
        // Re-enable when we know the correct target path:
        // if (strstr(path, "startmeup") || ...)
    }

    char lb[512]; snprintf(lb,sizeof(lb),"open:%s",path?: "NULL");
    if (np) { char r[512]; snprintf(r,sizeof(r)," -> %s",np); strncat(lb,r,sizeof(lb)-strlen(lb)-1); }
    log_write(lb);

    int r = np ? HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), np, flags, 0)
               : HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    in_hook = 0;
    return r;
}

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;(void)args;
    OrbisNotificationRequest r;

    memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
    snprintf(r.message,sizeof(r.message),"BS Deluxe %s",PLUGIN_VERSION);
    sceKernelSendNotificationRequest(0,&r,sizeof(r),0);

    // NO JAILBREAK — AFR handles writes via sceKernelOpen

    // fopen hook via Detour (kept for compatibility)
    Detour_Construct(&Detour_hook_fopen, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_fopen, (uint64_t)(void*)&fopen, (void*)fh);

    // open hook via Detour — handles logging + ALL redirects
    Detour_Construct(&Detour_hook_open, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_open, (uint64_t)(void*)&open, (void*)open_hook);

    // Init log
    int log_success = log_write("=== BS Deluxe v0.31 started ===");
    log_write("fopen+open hooks active, startmeup diagnostic mode");

    memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
    snprintf(r.message,sizeof(r.message),"%s v0.30",
        log_success ? "log+AFR OK" : "AFR: NO LOG");
    sceKernelSendNotificationRequest(0,&r,sizeof(r),0);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;(void)args;
    return 0;
}
