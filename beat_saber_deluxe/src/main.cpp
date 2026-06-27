// Beat Saber Deluxe v0.28 — AFR logging + Detour hooks (fopen+open)
// BREAKTHROUGH: AFR paths work without jailbreak or crashes!
// Uses sceKernelOpen/write/close to log to /data/GoldHEN/AFR/CUSA12878/
// Detour hooks for fopen (logging + redirect) and open (logging only)

#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.28"
#define LOG_PATH "/data/GoldHEN/AFR/CUSA12878/bs_log.txt"

extern "C" FILE *fopen(const char *path, const char *mode);
extern "C" int open(const char *path, int flags, ...);

HOOK_INIT(hook_fopen);
HOOK_INIT(hook_open);

static int in_hook = 0;

// Thread-safe file append via Orbis kernel API (no heap, no libc, no reentrancy)
static void log_write(const char *msg) {
    int fd = sceKernelOpen(LOG_PATH, O_WRONLY|O_CREAT|O_APPEND, 0644);
    if (fd >= 0) {
        sceKernelWrite(fd, msg, strlen(msg));
        sceKernelWrite(fd, "\n", 1);
        sceKernelClose(fd);
    }
}

// fopen hook — logs path, handles redirects
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

    char lb[512]; snprintf(lb,sizeof(lb),"fopen:%s",p?: "NULL");
    if (np) { char r[512]; snprintf(r,sizeof(r)," -> %s",np); strncat(lb,r,sizeof(lb)-strlen(lb)-1); }
    log_write(lb);

    FILE *r = np ? HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), np, m)
                 : HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), p, m);
    in_hook = 0;
    return r;
}

// open hook — logs path, no redirect
static int open_hook(const char *path, int flags, ...) {
    if (in_hook) return HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    in_hook = 1;

    char lb[512]; snprintf(lb,sizeof(lb),"open:%s",path?: "NULL");
    log_write(lb);

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

    // NO JAILBREAK — AFR path handles file writes via sceKernelOpen

    // fopen hook via Detour
    Detour_Construct(&Detour_hook_fopen, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_fopen, (uint64_t)(void*)&fopen, (void*)fh);

    // open hook via Detour
    Detour_Construct(&Detour_hook_open, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_open, (uint64_t)(void*)&open, (void*)open_hook);

    // Init log
    log_write("=== BS Deluxe v0.28 started ===");
    log_write("fopen+open hooks active, AFR logging OK");

    memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
    snprintf(r.message,sizeof(r.message),"hooks+AFR OK");
    sceKernelSendNotificationRequest(0,&r,sizeof(r),0);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;(void)args;
    return 0;
}
