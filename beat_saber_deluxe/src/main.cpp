// Beat Saber Deluxe — GOT dereference test
// Tests reading the real function address from our own GOT

#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

extern "C" int printf(const char *fmt, ...);

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;
    (void)args;

    OrbisNotificationRequest req;
    char msg[256];

    // (void*)&printf gives the address of the GOT entry in our PRX
    // which contains the REAL address of printf in libc
    void *got_entry = (void*)&printf;
    // Read the value at the GOT entry — this is the real printf address
    void *real_printf = *(void**)&printf;

    snprintf(msg, sizeof(msg), "GOT=%p REAL=%p", got_entry, real_printf);

    memset(&req, 0, sizeof(req));
    req.type = (OrbisNotificationRequestType)0;
    req.targetId = -1;
    strncpy(req.message, msg, sizeof(req.message) - 1);
    sceKernelSendNotificationRequest(0, &req, sizeof(req), 0);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}
