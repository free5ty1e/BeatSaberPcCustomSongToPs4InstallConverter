// Beat Saber Deluxe v0.12 — Diagnostic: dump open() bytes, count open calls
// Trying to find WHY the 6th open call crashes.

#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.12"
#define LOG_PATH "/data/bs_debug.txt"

extern "C" FILE *fopen(const char *path, const char *mode);
extern "C" int open(const char *path, int flags, ...);

HOOK_INIT(hook_fopen);
HOOK_INIT(hook_open);

static int in_hook = 0;
static int open_call = 0;

// Fix jb after syscall (0F 05 72/74/75 -> 0F 05 90 90)
static void fix_jb(void *stub, uint32_t size) {
    if (!stub || size < 4) return;
    uint8_t *b = (uint8_t*)stub;
    for (uint32_t i = 0; i < size - 3; i++) {
        if (b[i] == 0x0F && b[i+1] == 0x05 && (b[i+2] == 0x72 || b[i+2] == 0x74 || b[i+2] == 0x75)) {
            b[i+2] = 0x90; b[i+3] = 0x90; break;
        }
    }
}

static int log_inited = 0;
static void init_log() {
    if (log_inited) return; log_inited = 1;
    FILE *f = fopen(LOG_PATH, "w");
    if (f) {
        fprintf(f, "=== BS Deluxe Debug Log ===\n");
        fprintf(f, "Version: %s\n", PLUGIN_VERSION);
        fprintf(f, "fopen=%p open=%p\n", (void*)&fopen, (void*)&open);
        fprintf(f, "============================\n");
        fclose(f);
    }
}
static void log_line(const char *line) {
    init_log();
    FILE *f = fopen(LOG_PATH, "a");
    if (f) { fprintf(f, "%s\n", line); fclose(f); }
}

static const char* redirect_path(const char* path) {
    if (!path) return NULL;
    if (strstr(path, "startmeup") || strstr(path, "StartMeUp") || strstr(path, "start_me_up"))
        return "/data/custom/bs_deluxe/CustomSong";
    if (strstr(path, "resources.assets") && !strstr(path, "/data/custom/"))
        return "/data/custom/bs_deluxe/resources_patched.assets";
    return NULL;
}

static FILE *fopen_hook(const char *path, const char *mode) {
    if (in_hook) return HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), path, mode);
    in_hook = 1;
    const char *safe = path ? path : "NULL";
    const char *newpath = redirect_path(path);
    FILE *result;
    if (newpath) {
        char buf[256]; snprintf(buf, sizeof(buf), "REDIR fopen:%s->%s", safe, newpath); log_line(buf);
        result = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), newpath, mode);
    } else {
        char buf[256]; snprintf(buf, sizeof(buf), "fopen:%s", safe); log_line(buf);
        result = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), path, mode);
    }
    in_hook = 0;
    return result;
}

static int open_hook(const char *path, int flags, ...) {
    if (in_hook) return HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    in_hook = 1;
    open_call++;
    const char *safe = path ? path : "NULL";
    const char *newpath = redirect_path(path);

    // DIAGNOSTIC: Show notification on call #6+ to see what crashes
    if (open_call >= 6) {
        OrbisNotificationRequest req;
        memset(&req, 0, sizeof(req));
        req.type = (OrbisNotificationRequestType)0; req.targetId = -1;
        snprintf(req.message, sizeof(req.message), "open #%d: %.60s", open_call, safe);
        sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);
    }

    int result;
    if (newpath) {
        char buf[256]; snprintf(buf, sizeof(buf), "REDIR open:%s->%s", safe, newpath); log_line(buf);
        result = HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), newpath, flags, 0);
    } else {
        char buf[256]; snprintf(buf, sizeof(buf), "open:%s", safe); log_line(buf);
        result = HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    }
    in_hook = 0;
    return result;
}

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc; (void)args;
    OrbisNotificationRequest req;

    // Startup
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0; req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "BS Deluxe %s", PLUGIN_VERSION);
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // Jailbreak
    struct jailbreak_backup jb;
    memset(&jb, 0, sizeof(jb));
    int jr = sys_sdk_jailbreak(&jb);
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0; req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "JB %s", jr == 0 ? "OK" : "FAIL");
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // Dump first 16 bytes of open() to check what we're hooking
    uint8_t open_bytes[16];
    memcpy(open_bytes, (void*)&open, 16);
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0; req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "open: %02x%02x %02x%02x %02x%02x %02x%02x",
             open_bytes[0], open_bytes[1], open_bytes[2], open_bytes[3],
             open_bytes[4], open_bytes[5], open_bytes[6], open_bytes[7]);
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // fopen hook
    Detour_Construct(&Detour_hook_fopen, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_fopen, (uint64_t)(void*)&fopen, (void*)fopen_hook);

    // open hook
    Detour_Construct(&Detour_hook_open, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_open, (uint64_t)(void*)&open, (void*)open_hook);
    fix_jb(Detour_hook_open.StubPtr, Detour_hook_open.StubSize);

    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0; req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "stub: %s", Detour_hook_open.StubPtr ? "OK" : "NULL");
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc; (void)args;
    return 0;
}
