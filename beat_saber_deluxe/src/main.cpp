// Beat Saber Deluxe — Notification + printf logging
// No fopen — uses notification for visual proof, printf/klog for logging

#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include <orbis/libkernel.h>

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;
    (void)args;

    printf("BS Deluxe: module_start called (FSELF format)\n");
    printf("BS Deluxe: argc=%zu, args=%p\n", argc, args);

    // Show notification (proven to work in earlier test)
    OrbisNotificationRequest req;
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    strcpy(req.message, "BS Deluxe: Plugin Loaded!");
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    printf("BS Deluxe: notification sent, returning 0\n");

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}
