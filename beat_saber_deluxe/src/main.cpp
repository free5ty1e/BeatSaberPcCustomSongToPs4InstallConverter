// Beat Saber Deluxe — fopen() hook via GOT (safer: fopen is much longer than open)
// fopen has FILE buffering logic (~100+ bytes), so x64 detour won't overflow

#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

extern "C" FILE *fopen(const char *path, const char *mode);

HOOK_INIT(hook_fopen);

static int in_hook = 0;

static const char* redirect_path(const char* path) {
    if (!path) return NULL;
    if (strstr(path, "startmeup") || strstr(path, "StartMeUp") || strstr(path, "start_me_up"))
        return "/data/custom/bs_deluxe/CustomSong";
    if (strstr(path, "resources.assets") && !strstr(path, "/data/custom/"))
        return "/data/custom/bs_deluxe/resources_patched.assets";
    return NULL;
}

static FILE *fopen_hook(const char *path, const char *mode) {
    if (in_hook) {
        return HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), path, mode);
    }
    in_hook = 1;
    FILE *result;
    const char *newpath = redirect_path(path);
    if (newpath) {
        result = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), newpath, mode);
    } else {
        result = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), path, mode);
    }
    in_hook = 0;
    return result;
}

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;
    (void)args;

    // Get real fopen address from libc directly
    void *real_fopen = (void*)&fopen;

    OrbisNotificationRequest req;

    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "fopen @ %p", real_fopen);
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // Install the fopen hook
    Detour_Construct(&Detour_hook_fopen, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_fopen, (uint64_t)real_fopen, (void*)fopen_hook);

    // NO notification after hook install — sceKernelSendNotificationRequest may
    // internally call fopen(), triggering our hook. The reentrancy guard handles
    // this, but we skip the test for now to eliminate potential crash sources.

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}
