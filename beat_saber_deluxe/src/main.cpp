// Beat Saber Deluxe — GoldHEN Plugin
// Entry: _init (GoldHEN SDK crtprx.o calls module_start)

#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include <orbis/libkernel.h>
#include <GoldHEN/GoldHEN.h>
#include <GoldHEN/Syscall.h>

#define attr_public __attribute__((visibility("default")))

// Plugin metadata — GoldHEN/PS4 may check for these exports
attr_public const char* g_pluginName    = "Beat Saber Deluxe";
attr_public const char* g_pluginDesc    = "Custom song support for Beat Saber on PS4";
attr_public const char* g_pluginAuth    = "BSDeluxe";
attr_public uint32_t    g_pluginVersion = 0x00000100;

extern "C" attr_public int module_start(size_t argc, const void *args) {
    (void)argc;
    (void)args;

    // Call a GoldHEN SDK function to ensure libGoldHEN_Hook is linked in
    struct proc_info info;
    memset(&info, 0, sizeof(info));
    sys_sdk_proc_info(&info);  // gets process info (titleid, name, etc.)

    // Heartbeat notification — shows on PS4 screen if plugin loads
    OrbisNotificationRequest req;
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;  // NotificationRequest
    req.targetId = -1;                            // default target (on-screen)
    strcpy(req.message, "BS Deluxe: SDK Plugin Loaded!");

    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // Also try file write (for FTP-based verification)
    FILE* f = fopen("/data/custom/bs_deluxe/heartbeat.txt", "w");
    if (f) {
        fprintf(f, "Heartbeat: module_start via GoldHEN SDK crtprx.o!\n");
        fclose(f);
    }

    return 0;
}

extern "C" attr_public int module_stop(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}
