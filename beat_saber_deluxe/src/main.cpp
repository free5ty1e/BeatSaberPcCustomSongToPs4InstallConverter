// Beat Saber Deluxe v0.06 — Redirect with path display
// Uses fopen hook proven in Experiment 24 (no jailbreak, no crash).
// Shows a single notification when redirect triggers, revealing the path.
// No logging, no jailbreak, no open hook, no crash.

#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.06"

extern "C" FILE *fopen(const char *path, const char *mode);

HOOK_INIT(hook_fopen);

static int in_hook = 0;

static FILE *fopen_hook(const char *path, const char *mode) {
    if (in_hook) return HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), path, mode);
    in_hook = 1;

    // Check for sacrifice song
    if (path && (strstr(path, "startmeup") || strstr(path, "StartMeUp") || strstr(path, "start_me_up"))) {
        char msg[256];
        snprintf(msg, sizeof(msg), "BS path: %.80s", path);

        OrbisNotificationRequest req;
        memset(&req, 0, sizeof(req));
        req.type = (OrbisNotificationRequestType)0;
        req.targetId = -1;
        strncpy(req.message, msg, sizeof(req.message) - 1);
        sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

        // Redirect to custom song
        FILE *result = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), "/data/custom/bs_deluxe/CustomSong", mode);
        in_hook = 0;
        return result;
    }

    // Check for resources.assets
    if (path && strstr(path, "resources.assets") && !strstr(path, "/data/custom/")) {
        FILE *result = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), "/data/custom/bs_deluxe/resources_patched.assets", mode);
        in_hook = 0;
        return result;
    }

    FILE *result = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), path, mode);
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

    // fopen hook only — no jailbreak, no logging
    Detour_Construct(&Detour_hook_fopen, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_fopen, (uint64_t)(void*)&fopen, (void*)fopen_hook);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}
