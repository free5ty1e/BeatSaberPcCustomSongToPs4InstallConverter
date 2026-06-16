// Beat Saber Deluxe v0.04 — fopen hook ONLY (no open hook = no crash)
// Persistent log file via jailbreak. Logs only fopen calls.

#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.04"
#define LOG_PATH "/data/bs_debug.txt"

extern "C" FILE *fopen(const char *path, const char *mode);

HOOK_INIT(hook_fopen);

static int in_hook = 0;
static int log_inited = 0;
static FILE *log_fp = NULL;

static void init_log() {
    if (log_inited) return;
    log_inited = 1;
    log_fp = fopen(LOG_PATH, "w");
    if (log_fp) {
        fprintf(log_fp, "=== BS Deluxe Debug Log ===\n");
        fprintf(log_fp, "Version: %s\n", PLUGIN_VERSION);
        fprintf(log_fp, "fopen=%p\n", (void*)&fopen);
        fprintf(log_fp, "============================\n");
        fflush(log_fp);
        OrbisNotificationRequest req;
        memset(&req, 0, sizeof(req));
        req.type = (OrbisNotificationRequestType)0;
        req.targetId = -1;
        snprintf(req.message, sizeof(req.message), "Log: %s", LOG_PATH);
        sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);
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
        char buf[256]; snprintf(buf, sizeof(buf), "REDIR fopen:%s -> %s", safe, newpath);
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

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;
    (void)args;

    OrbisNotificationRequest req;

    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "BS Deluxe %s Started!", PLUGIN_VERSION);
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    struct jailbreak_backup jb;
    memset(&jb, 0, sizeof(jb));
    int jr = sys_sdk_jailbreak(&jb);
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "Jailbreak %s", jr == 0 ? "OK" : "FAIL");
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // fopen hook ONLY — no open hook (causes crash with short function detour)
    Detour_Construct(&Detour_hook_fopen, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_fopen, (uint64_t)(void*)&fopen, (void*)fopen_hook);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    if (log_fp) fclose(log_fp);
    (void)argc;
    (void)args;
    return 0;
}
