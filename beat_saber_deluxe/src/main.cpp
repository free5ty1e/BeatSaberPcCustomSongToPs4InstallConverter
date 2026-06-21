// Beat Saber Deluxe v0.20 — Detour for both hooks (EXACTLY like v0.02)
// v0.02 (jailbreak + 2x Detour) WORKED for 5 calls before the jb crash.
// All sys_sdk_proc_rw versions crashed — theory: proc_rw uses syscall 500
// (same as jailbreak), causing conflict in GoldHEN's handler.
// Fix: Detour (mprotect, different syscall) for all hooks.
// open_hook: silent pass-through (no logging) — exists ONLY as second hook.
// fopen_hook: handles logging + redirect.

#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.20"
#define LOG_PATH "/data/bs_debug.txt"

extern "C" FILE *fopen(const char *path, const char *mode);
extern "C" int open(const char *path, int flags, ...);

HOOK_INIT(hook_fopen);
HOOK_INIT(hook_open);

static int in_hook = 0;
static int log_ok = 0;

static void log_w(const char *s) {
    if (!log_ok) {
        log_ok = 1;
        FILE *f = fopen(LOG_PATH, "w");
        if (f) {
            fprintf(f,"=== BS Deluxe v0.20 ===\nfopen=%p\nJailbreak: active\n============\n",(void*)&fopen);
            fclose(f);
        }
    }
    FILE *f = fopen(LOG_PATH, "a");
    if (f) { fprintf(f,"%s\n",s); fclose(f); }
}

// fopen hook — handles logging and redirect
static FILE *fh(const char *p, const char *m) {
    if (in_hook) return HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), p, m);
    in_hook = 1;

    const char *np = NULL;
    if (p) {
        if (strstr(p,"startmeup")||strstr(p,"StartMeUp")||strstr(p,"start_me_up"))
            np = "/data/custom/bs_deluxe/CustomSong";
        if (strstr(p,"resources.assets")&&!strstr(p,"/data/custom/"))
            np = "/data/custom/bs_deluxe/resources_patched.assets";
    }

    char lb[256]; snprintf(lb,sizeof(lb),"fopen:%s",p?: "NULL"); log_w(lb);
    FILE *r = np ? HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), np, m)
                 : HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), p, m);
    in_hook = 0;
    return r;
}

// open hook — SILENT pass-through only (exists as 2nd Detour for jailbreak stability)
static int open_hook(const char *path, int flags, ...) {
    if (in_hook) return HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    in_hook = 1;
    int r = HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    in_hook = 0;
    return r;
}

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;(void)args;
    OrbisNotificationRequest r;

    memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
    snprintf(r.message,sizeof(r.message),"BS Deluxe %s",PLUGIN_VERSION);
    sceKernelSendNotificationRequest(0,&r,sizeof(r),0);

    // Jailbreak (syscall 500 cmd=2)
    struct jailbreak_backup jb;
    memset(&jb,0,sizeof(jb));
    int jr = sys_sdk_jailbreak(&jb);

    memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
    snprintf(r.message,sizeof(r.message),"JB %s",jr==0?"OK":"FAIL");
    sceKernelSendNotificationRequest(0,&r,sizeof(r),0);

    // Hook #1: fopen via Detour (mprotect — different syscall than jailbreak)
    Detour_Construct(&Detour_hook_fopen, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_fopen, (uint64_t)(void*)&fopen, (void*)fh);

    // Hook #2: open via Detour (second mprotect — matching v0.02 pattern)
    // This hook is a silent pass-through (no logging, no redirect).
    // It exists ONLY to make the second Detour call that stabilized v0.02.
    Detour_Construct(&Detour_hook_open, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_open, (uint64_t)(void*)&open, (void*)open_hook);

    memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
    snprintf(r.message,sizeof(r.message),"hooks: BB OK");
    sceKernelSendNotificationRequest(0,&r,sizeof(r),0);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;(void)args;
    return 0;
}
