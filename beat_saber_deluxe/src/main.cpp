// Beat Saber Deluxe v0.21 — ULTIMATE BASELINE: jailbreak + write file, no hooks
// If this crashes, jailbreak itself is the problem (not hooks).
// If it works, we can add hooks back ONE AT A TIME.

#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.21"
#define LOG_PATH "/data/bs_debug.txt"

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;(void)args;
    OrbisNotificationRequest r;

    memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
    snprintf(r.message,sizeof(r.message),"BS Deluxe %s",PLUGIN_VERSION);
    sceKernelSendNotificationRequest(0,&r,sizeof(r),0);

    struct jailbreak_backup jb;
    memset(&jb,0,sizeof(jb));
    int jr = sys_sdk_jailbreak(&jb);

    memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
    snprintf(r.message,sizeof(r.message),"JB %s",jr==0?"OK":"FAIL");
    sceKernelSendNotificationRequest(0,&r,sizeof(r),0);

    // Write a log file — no hooks, just raw file I/O after jailbreak
    FILE *f = fopen(LOG_PATH, "w");
    if (f) {
        fprintf(f, "=== BS Deluxe v0.21 ===\n");
        fprintf(f, "Jailbreak: %s\n", jr == 0 ? "OK" : "FAIL");
        fprintf(f, "This file exists = jailbreak+file I/O works\n");
        fclose(f);
    }

    memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
    snprintf(r.message,sizeof(r.message),"fopen %s", f ? "OK" : "FAIL");
    sceKernelSendNotificationRequest(0,&r,sizeof(r),0);

    // NO HOOKS — just return
    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;(void)args;
    return 0;
}
