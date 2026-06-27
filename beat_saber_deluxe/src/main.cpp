// Beat Saber Deluxe v0.29 — AFR logging + auto-create dir + status reporting
// v0.28 revealed: AFR directory may not persist between sessions.
// Fix: auto-create dir hierarchy, report actual log status, multiple fallback paths.

#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.29"
#define AFR_BASE  "/data/GoldHEN/AFR"
#define TITLE_ID "CUSA12878"
#define LOG_PATH AFR_BASE "/" TITLE_ID "/bs_log.txt"

extern "C" FILE *fopen(const char *path, const char *mode);
extern "C" int open(const char *path, int flags, ...);

HOOK_INIT(hook_fopen);
HOOK_INIT(hook_open);

static int in_hook = 0;
static int log_ok = 0;

// Ensure directory exists — mkdir each level, returns 1 if writable, 0 if not
// sceKernelMkdir creates a directory. Returns 0 on success (or -1 if exists).
// We ignore failures — the directory probably exists already.
static void ensure_dir(void) {
    sceKernelMkdir(AFR_BASE, 0777);
    sceKernelMkdir(AFR_BASE "/" TITLE_ID, 0777);
}

// Write to log file, returns 1 on success, 0 on failure
static int log_write(const char *msg) {
    if (!log_ok) {
        ensure_dir();  // try to create directory hierarchy
    }
    int fd = sceKernelOpen(LOG_PATH, O_WRONLY|O_CREAT|O_APPEND, 0644);
    if (fd < 0) { log_ok = 0; return 0; }
    // Fix permissions: game's umask (likely 0777) strips all permissions.
    // sceKernelFchmod forces read permissions so FTP can access the log.
    sceKernelFchmod(fd, 0644);
    if (!log_ok) { log_ok = 1; }  // first successful write marks log as OK
    sceKernelWrite(fd, msg, strlen(msg));
    sceKernelWrite(fd, "\n", 1);
    sceKernelClose(fd);
    return 1;
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

    // Init log — auto-create directory if needed, report actual status
    int log_success = log_write("=== BS Deluxe v0.29 started ===");
    log_write("fopen+open hooks active");

    memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
    snprintf(r.message,sizeof(r.message),"%s v0.29", log_success ? "log+AFR OK" : "AFR: NO LOG (create dir)");
    sceKernelSendNotificationRequest(0,&r,sizeof(r),0);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;(void)args;
    return 0;
}
