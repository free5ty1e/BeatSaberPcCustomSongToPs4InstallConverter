// Beat Saber Deluxe v0.01 — File I/O hooks with deferred USB logging
// NO file I/O in module_start (crashes — heap/sandbox not initialized).
// Log file created on FIRST hook call (game fully initialized).

#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.01a"
#define LOG_PATH "/mnt/usb0/bs_debug.txt"

extern "C" FILE *fopen(const char *path, const char *mode);
extern "C" int open(const char *path, int flags, ...);

HOOK_INIT(hook_fopen);
HOOK_INIT(hook_open);

static int in_hook = 0;
static int log_inited = 0;

// Init log (called from first hook — game running, heap/sandbox ready)
static void init_log() {
    if (log_inited) return;
    log_inited = 1;
    FILE *f = fopen(LOG_PATH, "w");
    if (f) {
        fprintf(f, "=== BS Deluxe Debug Log ===\n");
        fprintf(f, "Version: %s\n", PLUGIN_VERSION);
        fprintf(f, "fopen=%p open=%p\n", (void*)&fopen, (void*)&open);
        fprintf(f, "Redirect: startmeup->/data/custom/bs_deluxe/CustomSong\n");
        fprintf(f, "============================\n");
        fclose(f);
    }
}

// Append line to log (from within hooks)
static void log_line(const char *line) {
    if (!log_inited) init_log();
    FILE *f = fopen(LOG_PATH, "a");
    if (f) {
        fprintf(f, "%s\n", line);
        fclose(f);
    }
}

static const char* redirect_path(const char* path) {
    if (!path) return NULL;
    if (strstr(path, "startmeup") || strstr(path, "StartMeUp") || strstr(path, "start_me_up"))
        return "/data/custom/bs_deluxe/CustomSong";
    if (strstr(path, "resources.assets") && !strstr(path, "/data/custom/"))
        return "/data/custom/bs_deluxe/resources_patched.assets";
    return NULL;
}

// fopen hook — logs ALL paths
static FILE *fopen_hook(const char *path, const char *mode) {
    if (in_hook)
        return HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), path, mode);
    in_hook = 1;

    if (!log_inited) init_log();

    const char *newpath = redirect_path(path);
    FILE *result;
    if (newpath) {
        char buf[256];
        snprintf(buf, sizeof(buf), "REDIR fopen: %s -> %s", path ? path : "NULL", newpath);
        log_line(buf);
        result = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), newpath, mode);
    } else {
        char buf[256];
        snprintf(buf, sizeof(buf), "fopen: %s", path ? path : "NULL");
        log_line(buf);
        result = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), path, mode);
    }
    in_hook = 0;
    return result;
}

// open hook — logs ALL paths
static int open_hook(const char *path, int flags, ...) {
    if (in_hook)
        return HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    in_hook = 1;

    if (!log_inited) init_log();

    const char *newpath = redirect_path(path);
    int result;
    if (newpath) {
        char buf[256];
        snprintf(buf, sizeof(buf), "REDIR open: %s -> %s", path ? path : "NULL", newpath);
        log_line(buf);
        result = HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), newpath, flags, 0);
    } else {
        char buf[256];
        snprintf(buf, sizeof(buf), "open: %s", path ? path : "NULL");
        log_line(buf);
        result = HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    }
    in_hook = 0;
    return result;
}

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;
    (void)args;

    OrbisNotificationRequest req;

    // Startup notification
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "BS Deluxe %s Started!", PLUGIN_VERSION);
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // Install fopen hook
    Detour_Construct(&Detour_hook_fopen, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_fopen, (uint64_t)(void*)&fopen, (void*)fopen_hook);

    // Install open hook
    Detour_Construct(&Detour_hook_open, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_open, (uint64_t)(void*)&open, (void*)open_hook);

    // Notify log location (actual file created on first hook call)
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "Log: %s", LOG_PATH);
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}
