// Beat Saber Deluxe — File Hooks with USB logging
// Logs file paths to USB for post-test FTP analysis.
// NO notification spam — just two startup confirmations.
// Writing from within hooks is safe (game heap/sandbox initialized).

#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

extern "C" FILE *fopen(const char *path, const char *mode);
extern "C" int open(const char *path, int flags, ...);

HOOK_INIT(hook_fopen);
HOOK_INIT(hook_open);

// Shared reentrancy guard — one for BOTH hooks.
// When ANY hook is active and a call comes in, we pass through immediately.
// This prevents infinite recursion when logging triggers fopen/open.
static int in_hook = 0;
static int log_count = 0;

// Write a line to the USB log file — called from within hooks.
// fopen_hook/open_hook already handle reentrancy (in_hook guard passes
// through the internal fopen calls). No guard needed here.
static void log_line(const char *line) {
    FILE *f = fopen("/mnt/usb0/bs_debug.txt", "a");
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

// fopen hook
static FILE *fopen_hook(const char *path, const char *mode) {
    if (in_hook)
        return HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), path, mode);
    in_hook = 1;

    const char *newpath = redirect_path(path);
    FILE *result;
    if (newpath) {
        char buf[256];
        snprintf(buf, sizeof(buf), "REDIR fopen:%s -> %s", path ? path : "NULL", newpath);
        log_line(buf);
        result = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), newpath, mode);
    } else {
        if (path && strstr(path, ".assets") && log_count < 200) {
            char buf[256];
            snprintf(buf, sizeof(buf), "fopen:%s", path);
            log_line(buf);
            log_count++;
        }
        result = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), path, mode);
    }
    in_hook = 0;
    return result;
}

// open hook
static int open_hook(const char *path, int flags, ...) {
    if (in_hook)
        return HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    in_hook = 1;

    const char *newpath = redirect_path(path);
    int result;
    if (newpath) {
        char buf[256];
        snprintf(buf, sizeof(buf), "REDIR open:%s -> %s", path ? path : "NULL", newpath);
        log_line(buf);
        result = HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), newpath, flags, 0);
    } else {
        if (path && strstr(path, "/app0") && log_count < 200) {
            char buf[256];
            snprintf(buf, sizeof(buf), "open:%s", path);
            log_line(buf);
            log_count++;
        }
        result = HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    }
    in_hook = 0;
    return result;
}

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;
    (void)args;

    // Write header to USB log
    FILE *f = fopen("/mnt/usb0/bs_debug.txt", "w");
    if (f) {
        fprintf(f, "=== BS Deluxe Debug Log ===\n");
        fprintf(f, "Start: fopen=%p open=%p\n", (void*)&fopen, (void*)&open);
        fclose(f);
    }

    OrbisNotificationRequest req;

    // Show fopen address notification
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "fopen @ %p", (void*)&fopen);
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // Install fopen hook
    Detour_Construct(&Detour_hook_fopen, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_fopen, (uint64_t)(void*)&fopen, (void*)fopen_hook);

    // Show open address notification
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "open @ %p", (void*)&open);
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // Install open hook
    Detour_Construct(&Detour_hook_open, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_open, (uint64_t)(void*)&open, (void*)open_hook);

    // Log hook install to USB
    f = fopen("/mnt/usb0/bs_debug.txt", "a");
    if (f) {
        fprintf(f, "Hooks installed. fopen=%p open=%p\n", (void*)&fopen, (void*)&open);
        fprintf(f, "Redirect: startmeup -> /data/custom/bs_deluxe/CustomSong\n");
        fclose(f);
    }

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}
