// Beat Saber Deluxe — GoldHEN SDK linkage test
// Tests if linking AND calling GoldHEN SDK functions causes crashes

#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include <orbis/libkernel.h>

// Declare GoldHEN SDK functions we want to call
extern "C" int sys_sdk_version(void);

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;
    (void)args;

    // Call a GoldHEN SDK function to ensure libGoldHEN_Hook is linked
    int sdk_ver = sys_sdk_version();

    // Show notification
    OrbisNotificationRequest req;
    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    sprintf(req.message, "BS Deluxe: SDK v%d", sdk_ver);
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}
