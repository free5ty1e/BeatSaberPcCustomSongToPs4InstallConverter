// Beat Saber Deluxe — GoldHEN Plugin
// Entry: _init (GoldHEN SDK crtprx.o calls module_start)

#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include <orbis/libkernel.h>

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;
    (void)args;

    // Heartbeat notification — shows on PS4 screen if plugin loads
    // This bypasses file system permissions that block fopen/fprintf
    OrbisNotificationRequest req;
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;  // NotificationRequest
    req.targetId = -1;                            // default target (on-screen)
    strcpy(req.message, "BS Deluxe: Plugin Loaded via GoldHEN SDK!");

    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    // Also try file write (for FTP-based verification)
    FILE* f = fopen("/data/custom/bs_deluxe/heartbeat.txt", "w");
    if (f) {
        fprintf(f, "Heartbeat: module_start via GoldHEN SDK crtprx.o!\n");
        fclose(f);
    }

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}
