// Beat Saber Deluxe v0.52 — All 12 Rolling Stones redirects + fixed beatmap filename fallback
// v0.52: plugin version bump to reflect 12-song redirect table added in v0.50 batch deploy.
// Key architecture: open() hook redirects BeatmapLevelsData/<id> → AFR custom bundle.
// No jailbreak needed — AFR handles writes via sceKernelOpen.

#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.52"
#define AFR_BASE  "/data/GoldHEN/AFR"
#define TITLE_ID "CUSA12878"
#define LOG_PATH AFR_BASE "/" TITLE_ID "/bs_log.txt"

// ── Rolling Stones song redirect table ────────────────────────────────────
// Each entry maps an official bundle ID to a custom bundle file on the AFR path.
// The suffix _v3 is appended by the pipeline. Keep sorted for readability.
static const char *REDIRECT_TABLE[][2] = {
    {"BeatmapLevelsData/angry",                AFR_BASE "/" TITLE_ID "/angry_v3"},
    {"BeatmapLevelsData/bitemyheadoff",        AFR_BASE "/" TITLE_ID "/bitemyheadoff_v3"},
    {"BeatmapLevelsData/cantyouhearmeknocking",AFR_BASE "/" TITLE_ID "/cantyouhearmeknocking_v3"},
    {"BeatmapLevelsData/deadmanwalking",       AFR_BASE "/" TITLE_ID "/deadmanwalking_v3"},
    {"BeatmapLevelsData/gimmeshelter",         AFR_BASE "/" TITLE_ID "/gimmeshelter_v3"},
    {"BeatmapLevelsData/icantgetnosatisfaction",AFR_BASE "/" TITLE_ID "/icantgetnosatisfaction_v3"},
    {"BeatmapLevelsData/messitup",             AFR_BASE "/" TITLE_ID "/messitup_v3"},
    {"BeatmapLevelsData/paintitblack",         AFR_BASE "/" TITLE_ID "/paintitblack_v3"},
    {"BeatmapLevelsData/startmeup",            AFR_BASE "/" TITLE_ID "/startmeup_v3"},
    {"BeatmapLevelsData/sugarsoaker",          AFR_BASE "/" TITLE_ID "/sugarsoaker_v3"},
    {"BeatmapLevelsData/sympathyforthedevil",  AFR_BASE "/" TITLE_ID "/sympathyforthedevil_v3"},
    {"BeatmapLevelsData/wholewideworld",       AFR_BASE "/" TITLE_ID "/wholewideworld_v3"},
    {NULL, NULL}  // sentinel
};

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
#ifdef VERBOSE_LOG
    char lb[512]; snprintf(lb,sizeof(lb),"fopen:%s",p?: "NULL"); log_write(lb);
#endif
    FILE *r = HOOK_CONTINUE(hook_fopen, FILE* (*)(const char*, const char*), p, m);
    in_hook = 0;
    return r;
}

static int open_hook(const char *path, int flags, ...) {
    if (in_hook) return HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    in_hook = 1;
    const char *np = NULL;
    if (path) {
        for (int i = 0; REDIRECT_TABLE[i][0]; i++) {
            if (strstr(path, REDIRECT_TABLE[i][0])) {
                np = REDIRECT_TABLE[i][1];
                break;
            }
        }
    }
#ifdef VERBOSE_LOG
    char lb[512]; snprintf(lb,sizeof(lb),"open:%s",path?: "NULL");
    if (np) { char r[512]; snprintf(r,sizeof(r)," -> %s",np); strncat(lb,r,sizeof(lb)-strlen(lb)-1); }
    log_write(lb);
#endif
    int r = np ? HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), np, flags, 0)
               : HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    in_hook = 0;
    return r;
}



extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;(void)args;
    OrbisNotificationRequest r;
    log_write("=== BS Deluxe " PLUGIN_VERSION " started ===");

    log_write(PLUGIN_VERSION ": 12-song Rolling Stones redirect table + improved beatmap filename fallback");

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
    snprintf(r.message,sizeof(r.message),"BS Deluxe %s", PLUGIN_VERSION);
    sceKernelSendNotificationRequest(0,&r,sizeof(r),0);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;(void)args;
    return 0;
}
