// Beat Saber Deluxe v0.07 — Open hook via Detour + jb fix in stub
// Uses Detour_DetourFunction normally, then patches the jb in the
// RWX stub memory to prevent erroneous PC-relative jumps on error.

#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.07"
#define LOG_PATH "/data/bs_debug.txt"

extern "C" FILE *fopen(const char *path, const char *mode);
extern "C" int open(const char *path, int flags, ...);

HOOK_INIT(hook_fopen);
HOOK_INIT(hook_open);

static int in_hook = 0;
static int log_inited = 0;
static FILE *log_fp = NULL;

// Fix PC-relative jb/jne/je instructions in stub memory
// The stub (allocated RWX by Detour) contains saved function bytes.
// Short functions like open() have jb error_handler whose PC-relative
// offset is wrong when relocated to the stub. We replace jb with nop;nop.
static void fix_stub_jumps(Detour *det) {
    if (!det->StubPtr || det->StubSize < 2) return;
    uint8_t *bytes = (uint8_t*)det->StubPtr;
    for (uint32_t i = 0; i < det->StubSize - 1; i++) {
        // jb rel8 (0x72 XX) / jne rel8 (0x75 XX) / je rel8 (0x74 XX)
        if (bytes[i] == 0x72 || bytes[i] == 0x74 || bytes[i] == 0x75) {
            bytes[i] = 0x90;
            bytes[i+1] = 0x90;
            break;  // Only fix the first one (open's jb error)
        }
    }
}

// --- Logging ---
static void init_log() {
    if (log_inited) return;
    log_inited = 1;
    log_fp = fopen(LOG_PATH, "w");
    if (log_fp) {
        fprintf(log_fp, "=== BS Deluxe Debug Log ===\n");
        fprintf(log_fp, "Version: %s\n", PLUGIN_VERSION);
        fprintf(log_fp, "fopen=%p open=%p\n", (void*)&fopen, (void*)&open);
        fprintf(log_fp, "============================\n");
        fflush(log_fp);
    }
}
static void log_line(const char *line) {
    if (!log_inited) init_log();
    if (log_fp) { fprintf(log_fp, "%s\n", line); fflush(log_fp); }
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
    if (!log_inited) init_log();
    const char *safe = path ? path : "NULL";
    const char *newpath = redirect_path(path);
    FILE *result;
    if (newpath) {
        char buf[256]; snprintf(buf, sizeof(buf), "REDIR fopen:%s->%s", safe, newpath);
        log_line(buf);
        result = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), newpath, mode);
    } else {
        char buf[256]; snprintf(buf, sizeof(buf), "fopen:%s", safe);
        log_line(buf);
        result = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), path, mode);
    }
    in_hook = 0;
    return result;
}

static int open_hook(const char *path, int flags, ...) {
    if (in_hook) return HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    in_hook = 1;
    if (!log_inited) init_log();
    const char *safe = path ? path : "NULL";
    const char *newpath = redirect_path(path);
    int result;
    if (newpath) {
        char buf[256]; snprintf(buf, sizeof(buf), "REDIR open:%s->%s", safe, newpath);
        log_line(buf);
        result = HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), newpath, flags, 0);
    } else {
        char buf[256]; snprintf(buf, sizeof(buf), "open:%s", safe);
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

    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "BS Deluxe %s Started!", PLUGIN_VERSION);
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // Jailbreak for write access
    struct jailbreak_backup jb;
    memset(&jb, 0, sizeof(jb));
    int jr = sys_sdk_jailbreak(&jb);
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "Jailbreak %s", jr == 0 ? "OK" : "FAIL");
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // Install fopen hook (standard Detour - safe, long function)
    Detour_Construct(&Detour_hook_fopen, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_fopen, (uint64_t)(void*)&fopen, (void*)fopen_hook);

    // Install open hook (standard Detour + jb fix in stub)
    // 1. Install hook (creates stub with saved bytes + jump back)
    Detour_Construct(&Detour_hook_open, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_open, (uint64_t)(void*)&open, (void*)open_hook);
    // 2. Fix jb/jne/je in the stub (stub is RWX, writable)
    fix_stub_jumps(&Detour_hook_open);

    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "open stub fixed: %s",
             Detour_hook_open.StubPtr ? "OK" : "FAIL");
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    if (log_fp) fclose(log_fp);
    (void)argc;
    (void)args;
    return 0;
}
