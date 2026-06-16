// Beat Saber Deluxe — fopen + open hooks with path logging
// Logs opened file paths to notifications so we can discover
// which function the game uses for song file access.

#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

// --- fopen hook ---
extern "C" FILE *fopen(const char *path, const char *mode);
HOOK_INIT(hook_fopen);

// --- open hook ---
extern "C" int open(const char *path, int flags, ...);
HOOK_INIT(hook_open);

// Reentrancy guards (one per hook)
static int fopen_in_hook = 0;
static int open_in_hook = 0;

// Notification helper (sends only if not already in a hook)
static void try_notify(const char *msg) {
    // Only send if not already inside a hook (prevent recursion)
    if (fopen_in_hook || open_in_hook) return;
    OrbisNotificationRequest req;
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    strncpy(req.message, msg, sizeof(req.message) - 1);
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);
}

// Redirect paths
static const char* redirect_path(const char* path) {
    if (!path) return NULL;
    if (strstr(path, "startmeup") || strstr(path, "StartMeUp") || strstr(path, "start_me_up"))
        return "/data/custom/bs_deluxe/CustomSong";
    if (strstr(path, "resources.assets") && !strstr(path, "/data/custom/"))
        return "/data/custom/bs_deluxe/resources_patched.assets";
    return NULL;
}

// fopen hook
static FILE *fopen_hook(const char *path, const char *mode) {
    if (fopen_in_hook)
        return HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), path, mode);
    fopen_in_hook = 1;

    // Log the path being opened (first 40 chars) for diagnostics
    char log_msg[128];
    snprintf(log_msg, sizeof(log_msg), "fopen: %.40s", path ? path : "NULL");
    try_notify(log_msg);

    const char *newpath = redirect_path(path);
    FILE *result;
    if (newpath) {
        char redir_msg[128];
        snprintf(redir_msg, sizeof(redir_msg), "REDIR: %.30s -> CustomSong", path ? path : "");
        try_notify(redir_msg);
        result = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), newpath, mode);
    } else {
        result = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), path, mode);
    }
    fopen_in_hook = 0;
    return result;
}

// open hook
static int open_hook(const char *path, int flags, ...) {
    if (open_in_hook)
        return HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    open_in_hook = 1;

    // Log the path being opened
    char log_msg[128];
    snprintf(log_msg, sizeof(log_msg), "open: %.40s", path ? path : "NULL");
    try_notify(log_msg);

    const char *newpath = redirect_path(path);
    int result;
    if (newpath) {
        char redir_msg[128];
        snprintf(redir_msg, sizeof(redir_msg), "REDIR open: %.30s", path ? path : "");
        try_notify(redir_msg);
        result = HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), newpath, flags, 0);
    } else {
        result = HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    }
    open_in_hook = 0;
    return result;
}

// Helper to get function address — PS4 uses direct binding,
// so (void*)&func gives the real address in libc
#define GET_REAL_ADDR(func) ((void*)(&func))

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;
    (void)args;

    OrbisNotificationRequest req;

    // Get fopen address
    void *real_fopen = GET_REAL_ADDR(fopen);
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "fopen @ %p", real_fopen);
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // Install fopen hook
    Detour_Construct(&Detour_hook_fopen, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_fopen, (uint64_t)real_fopen, (void*)fopen_hook);

    // Get open address
    void *real_open = GET_REAL_ADDR(open);
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "open @ %p", real_open);
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // Install open hook
    Detour_Construct(&Detour_hook_open, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_open, (uint64_t)real_open, (void*)open_hook);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}
