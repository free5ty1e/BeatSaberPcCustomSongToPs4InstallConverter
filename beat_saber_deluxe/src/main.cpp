// Beat Saber Deluxe — File Hook Test
// Hooks sceFileUtilsOpen to intercept and redirect song asset requests
// to our custom assets in /data/custom/bs_deluxe/

#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <dlfcn.h>
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

    // Try to find file functions using dlsym(RTLD_DEFAULT, ...)
    // dlsym searches all loaded modules — more reliable than sys_dynlib_dlsym
    const char* func_names[] = {
        "sceFileUtilsOpen",   // Orbis file open (often in libkernel or libSceFilesystem)
        "open",               // POSIX open (from libc or libkernel)
        "fopen",              // fopen from libc
        "sceKernelOpen",      // Orbis kernel open
        "read",               // POSIX read
        "write",              // POSIX write
        "stat",               // POSIX stat
        "printf",             // libc printf (we KNOW this works - verify dlsym works)
        "dlopen",             // dlopen itself
        NULL
    };

    // Build a notification with all found functions
    char notify_msg[256];
    char temp[64];
    int found_count = 0;
    notify_msg[0] = '\0';

    for (int i = 0; func_names[i]; i++) {
        void *ptr = dlsym(RTLD_DEFAULT, func_names[i]);
        if (ptr) {
            found_count++;
            if (found_count > 1) strncat(notify_msg, " ", sizeof(notify_msg) - strlen(notify_msg) - 1);
            snprintf(temp, sizeof(temp), "%s", func_names[i]);
            strncat(notify_msg, temp, sizeof(notify_msg) - strlen(notify_msg) - 1);
        }
    }

    if (found_count == 0) {
        snprintf(notify_msg, sizeof(notify_msg), "No functions found");
    }

    // Show notification with results — ONLY the found names
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    strncpy(req.message, notify_msg, sizeof(req.message) - 1);
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);
    klog("BS Deluxe: dlsym found %d functions: %s\n", found_count, notify_msg);

    // If sceFileUtilsOpen was found, install the hook
    void *fsfunc_ptr = dlsym(RTLD_DEFAULT, "sceFileUtilsOpen");
    if (fsfunc_ptr) {
        klog("BS Deluxe: Found sceFileUtilsOpen at %p\n", fsfunc_ptr);

        // Construct and install hook
        Detour_Construct(&Detour_sceFileUtilsOpen, DetourMode_x64);
        void *hook_ret = Detour_DetourFunction(&Detour_sceFileUtilsOpen,
                                              (uint64_t)fsfunc_ptr,
                                              (void*)sceFileUtilsOpen_hook);

        // Show hook notification
        memset(&req, 0, sizeof(req));
        req.type = (OrbisNotificationRequestType)0;
        req.targetId = -1;
        snprintf(req.message, sizeof(req.message), "sceFileUtilsOpen %s",
                 hook_ret != NULL ? "HOOKED OK" : "HOOK FAILED");
        sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);
        klog("BS Deluxe: sceFileUtilsOpen hook %s\n",
             hook_ret != NULL ? "installed OK" : "FAILED");
    }

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}
