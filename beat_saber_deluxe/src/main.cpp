// Beat Saber Deluxe — File Hook Test
// Hooks sceFileUtilsOpen to intercept and redirect song asset requests
// to our custom assets in /data/custom/bs_deluxe/

#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

// sceFileUtilsOpen signature (found via sys_dynlib_dlsym at runtime)
// int sceFileUtilsOpen(const char *path, int flags, int *fd, ...);

// Declare the Detour struct for our hook
HOOK_INIT(sceFileUtilsOpen);

// Redirect paths
static const char* redirect_asset(const char* path) {
    if (!path) return NULL;

    // Redirect "Start Me Up" song assets to our custom song
    // (Path contains "startmeup" or similar pattern)
    if (strstr(path, "startmeup") || strstr(path, "start_me_up") || strstr(path, "StartMeUp")) {
        return "/data/custom/bs_deluxe/CustomSong";
    }

    // Redirect resources.assets (the main resource catalog)
    // to our patched version (avoid circular redirect by checking /data/custom/)
    if (strstr(path, "resources.assets") && !strstr(path, "/data/custom/")) {
        return "/data/custom/bs_deluxe/resources_patched.assets";
    }

    return NULL; // No redirect needed
}

// Hook function — called instead of the real sceFileUtilsOpen
static int sceFileUtilsOpen_hook(const char *path, int flags, int *fd, ...) {
    if (path) {
        const char* newpath = redirect_asset(path);
        if (newpath) {
            klog("BS Deluxe: Redirecting %s -> %s\n", path, newpath);
            // Show notification about redirect
            OrbisNotificationRequest req;
            memset(&req, 0, sizeof(req));
            req.type = (OrbisNotificationRequestType)0;
            req.targetId = -1;
            strcpy(req.message, "BS: Redirecting song!");
            sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);
            // Call original function with redirected path
            return HOOK_CONTINUE(sceFileUtilsOpen, int (*)(const char*, int, int*, ...), newpath, flags, fd);
        }
    }
    // Not a path we care about — pass through to original
    return HOOK_CONTINUE(sceFileUtilsOpen, int (*)(const char*, int, int*, ...), path, flags, fd);
}

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;
    (void)args;

    // Show startup notification
    OrbisNotificationRequest req;
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    strcpy(req.message, "BS Deluxe: Loading hooks...");
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // Get process info for debugging
    struct proc_info info;
    memset(&info, 0, sizeof(info));
    if (sys_sdk_proc_info(&info) == 0) {
        klog("BS Deluxe: Started for %s (titleid: %s)\n", info.name, info.titleid);
    }

    // Look up sceFileUtilsOpen address using sys_dynlib_dlsym
    void *func_ptr = NULL;
    int ret = sys_dynlib_dlsym(-1, "sceFileUtilsOpen", &func_ptr);

    // Show notification with result
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    snprintf(req.message, sizeof(req.message), "FS: %s at %p",
             func_ptr ? "FOUND" : "NOT FOUND", func_ptr);
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // Install the hook if function was found
    if (func_ptr) {
        // Construct the Detour
        Detour_Construct(&Detour_sceFileUtilsOpen, DetourMode_x64);

        // Install the hook — replaces sceFileUtilsOpen with our hook
        void *hook_ret = Detour_DetourFunction(&Detour_sceFileUtilsOpen,
                                              (uint64_t)func_ptr,
                                              (void*)sceFileUtilsOpen_hook);

        klog("BS Deluxe: Hook install %s (ret=%p)\n",
             hook_ret != NULL ? "OK" : "FAILED", hook_ret);

        // Show final notification
        memset(&req, 0, sizeof(req));
        req.type = (OrbisNotificationRequestType)0;
        req.targetId = -1;
        snprintf(req.message, sizeof(req.message), "BS Deluxe: Hook %s",
                 hook_ret != NULL ? "OK" : "FAIL");
        sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);
    }

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}
