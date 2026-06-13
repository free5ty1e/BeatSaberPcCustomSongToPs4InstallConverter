#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <orbis/libkernel.h>

#define attr_public __attribute__((visibility("default")))

int32_t attr_public module_start(size_t argc, const void *args) {
    (void)argc;
    (void)args;

    // On-screen notification
    OrbisNotificationRequest req;
    memset(&req, 0, sizeof(req));
    req.type = 0;
    req.targetId = -1;
    strcpy(req.message, "BS Deluxe: RB4DX Makefile!");
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    return 0;
}

int32_t attr_public module_stop(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}
