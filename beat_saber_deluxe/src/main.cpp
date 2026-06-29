// Beat Saber Deluxe v0.35 — TRUE test: redirect startmeup→100bills
// Key discovery: the patched resources.assets ONLY changed "StartMeUp\0"→"CustomSong"
// (10 bytes at offset 871180). It doesn't add any custom songs.
// So we DON'T redirect resources.assets anymore — use the ORIGINAL manifest.
// The only redirect is BeatmapLevelsData/startmeup → 100bills file.
// This tests if the 100bills file works as a replacement (whether asset name matters).

#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.38"
#define AFR_BASE  "/data/GoldHEN/AFR"
#define TITLE_ID "CUSA12878"
#define LOG_PATH AFR_BASE "/" TITLE_ID "/bs_log.txt"

extern "C" FILE *fopen(const char *path, const char *mode);
extern "C" int open(const char *path, int flags, ...);

HOOK_INIT(hook_fopen);
HOOK_INIT(hook_open);

static int in_hook = 0;
static int log_ok = 0;

static void ensure_dir(void) {
    sceKernelMkdir(AFR_BASE, 0777);
    sceKernelMkdir(AFR_BASE "/" TITLE_ID, 0777);
}

static int log_write(const char *msg) {
    if (!log_ok) ensure_dir();
    int fd = sceKernelOpen(LOG_PATH, O_WRONLY|O_CREAT|O_APPEND, 0644);
    if (fd < 0) { log_ok = 0; return 0; }
    sceKernelFchmod(fd, 0644);
    if (!log_ok) log_ok = 1;
    sceKernelWrite(fd, msg, strlen(msg));
    sceKernelWrite(fd, "\n", 1);
    sceKernelClose(fd);
    return 1;
}

static FILE *fh(const char *p, const char *m) {
    if (in_hook) return HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), p, m);
    in_hook = 1;
    char lb[512]; snprintf(lb,sizeof(lb),"fopen:%s",p?: "NULL"); log_write(lb);
    FILE *r = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), p, m);
    in_hook = 0;
    return r;
}

static int open_hook(const char *path, int flags, ...) {
    if (in_hook) return HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    in_hook = 1;
    const char *np = NULL;
    if (path) {
        // Redirect song file: startmeup → renamed 100bills bundle
        // The renamed bundle has asset NAME changed to "StartMeUpBeatmapLevelData"
        // and container path changed to ".../startmeup/startmeupbeatmapleveldata.asset"
        // (via UnityPy: renamed m_Name + AssetBundle.m_Container)
        if (strstr(path, "BeatmapLevelsData/startmeup"))
            np = AFR_BASE "/" TITLE_ID "/startmeup_custom";
    }
    char lb[512]; snprintf(lb,sizeof(lb),"open:%s",path?: "NULL");
    if (np) { char r[512]; snprintf(r,sizeof(r)," -> %s",np); strncat(lb,r,sizeof(lb)-strlen(lb)-1); }
    log_write(lb);
    int r = np ? HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), np, flags, 0)
               : HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    in_hook = 0;
    return r;
}



extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;(void)args;
    OrbisNotificationRequest r;

    log_write("=== BS Deluxe v0.38 started ===");
    log_write("Custom song conversion: replaced beatmaps, startmeup redirect");

    // NO JAILBREAK — AFR handles writes via sceKernelOpen

    // fopen hook via Detour
    Detour_Construct(&Detour_hook_fopen, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_fopen, (uint64_t)(void*)&fopen, (void*)fh);

    // open hook via Detour — handles ALL redirects
    Detour_Construct(&Detour_hook_open, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_open, (uint64_t)(void*)&open, (void*)open_hook);

    log_write("hooks installed");

    // Notification
    memset(&r,0,sizeof(r)); r.type=(OrbisNotificationRequestType)0; r.targetId=-1;
    snprintf(r.message,sizeof(r.message),"BS Deluxe v0.37");
    sceKernelSendNotificationRequest(0,&r,sizeof(r),0);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;(void)args;
    return 0;
}
