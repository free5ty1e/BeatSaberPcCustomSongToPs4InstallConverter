// Beat Saber Deluxe v0.14 — No stub hooking for open()
// Save original bytes, CALL ORIGINAL DIRECTLY (no stub), rehook after return.
// fopen hook still via Detour (safe, long function).
// Logging via file.

#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.15"
#define LOG_PATH "/data/bs_debug.txt"
#define JUMP_SIZE 12

extern "C" FILE *fopen(const char *path, const char *mode);
extern "C" int open(const char *path, int flags, ...);

HOOK_INIT(hook_fopen);

static int in_hook = 0;
static int hook_depth = 0;
static uint8_t open_saved[JUMP_SIZE];  // saved original bytes of open()
static int (*real_open)(const char*, int, int) = NULL;

// GoldHEN kernel memory write (no mprotect)
static void mem_write(uint64_t addr, void *data, uint64_t len) {
    struct proc_rw rw;
    memset(&rw, 0, sizeof(rw));
    rw.address = addr; rw.data = data; rw.length = len; rw.write_flags = 1;
    sys_sdk_proc_rw(&rw);
}

// Install/reinstall the hook jump at open()
static void write_jump(void *target, void *hook) {
    uint8_t j[JUMP_SIZE] = {0x48,0xB8,0,0,0,0,0,0,0,0,0xFF,0xE0};
    *(uint64_t*)&j[2] = (uint64_t)hook;
    mem_write((uint64_t)target, j, JUMP_SIZE);
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

// open hook: restore bytes, call original, rehook only at outermost level
static int open_hook(const char *path, int flags, ...) {
    if (in_hook) {
        // Reentrant: restore, call original — outer call will rehook
        mem_write((uint64_t)real_open, open_saved, JUMP_SIZE);
        hook_depth++;
        int r = real_open(path, flags, 0);
        hook_depth--;
        return r;
    }
    in_hook = 1;
    hook_depth++;

    const char *safe = path ? path : "NULL";
    const char *newpath = redirect_path(path);
    int result;

    // Restore original bytes so we can call open() directly
    mem_write((uint64_t)real_open, open_saved, JUMP_SIZE);

    if (newpath) {
        char buf[256]; snprintf(buf, sizeof(buf), "REDIR open:%s->%s", safe, newpath); log_line(buf);
        result = real_open(newpath, flags, 0);
    } else {
        char buf[256]; snprintf(buf, sizeof(buf), "open:%s", safe); log_line(buf);
        result = real_open(path, flags, 0);
    }

    // Rehook only if we're the outermost call
    hook_depth--;
    if (hook_depth == 0)
        write_jump((void*)real_open, (void*)open_hook);

    in_hook = 0;
    return result;
}

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc; (void)args;
    OrbisNotificationRequest req;

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

    // Save real open address and original bytes BEFORE hooking
    real_open = (int (*)(const char*, int, int))(void*)&open;
    memcpy(open_saved, (void*)&open, JUMP_SIZE);

    // Show saved bytes in notification
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0; req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "saved: %02x%02x %02x%02x %02x%02x %02x%02x",
             open_saved[0], open_saved[1], open_saved[2], open_saved[3],
             open_saved[4], open_saved[5], open_saved[6], open_saved[7]);
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // Install fopen hook (Detour — safe for long functions)
    Detour_Construct(&Detour_hook_fopen, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_fopen, (uint64_t)(void*)&fopen, (void*)fopen_hook);

    // Install open hook via sys_sdk_proc_rw (no stub, no mprotect)
    // First write restores will use open_saved
    write_jump((void*)real_open, (void*)open_hook);

    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0; req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "hooks: fopen=OK open=OK");
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    // Restore original open bytes (cleanup)
    if (real_open) mem_write((uint64_t)real_open, open_saved, JUMP_SIZE);
    (void)argc; (void)args;
    return 0;
}
