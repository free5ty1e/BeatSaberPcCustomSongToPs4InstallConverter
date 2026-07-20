// Beat Saber Deluxe — dynamic redirect plugin
// Reads song redirect table from /data/GoldHEN/AFR/<TITLE_ID>/redirects.json
// All redirects come from the external config file — no hardcoded fallback.
// v0.79: Memory injection — STRDEBUG logging to determine System_String length offset on PS4.
// v0.76: Memory injection — lowered string ptr validation threshold (4GB→16MB), expanded scan range.
// v0.75: Memory injection — wide-range heap scan (1GB-32GB, coarse). Discovered class strings in global-metadata.dat.
// v0.74: Memory injection — signal handlers installed once per scan, heap scan range reduced.
// v0.73: Memory injection — pattern-based klass finding (string not in module text segment).
// v0.72: Memory injection — fixed bounds check rejecting valid module addresses (<4GB).
// v0.71: Memory injection — fixed with signal-handler-based memory probing (mincore/msync were stubs on PS4).
// v0.70: Memory injection — fixed msync page checking (mincore was a stub on PS4).
// v0.69: Memory injection — fixed. Removed guard timer, trigger on any redirect.
// v0.68: Memory injection — fixed CE-34878-0 crash. Removed pack bundle redirect from redirects.json.
// v0.66: Memory injection — patch BeatmapLevelSO in RAM bypassing CRC validation.
// v0.65: Mode selector — replace StartMeUp BeatmapLevelSO in pack bundle with 5-mode preview data.

#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#include "memory_inject.h"

#define PLUGIN_VERSION "v0.8006"
#define AFR_BASE  "/data/GoldHEN/AFR"
#define TITLE_ID "CUSA12878"
#define LOG_PATH AFR_BASE "/" TITLE_ID "/bs_log.txt"
#define CONFIG_PATH AFR_BASE "/" TITLE_ID "/redirects.json"
#define MAX_REDIRECTS 256
#define MAX_PATH 256

// ── Dynamic redirect table ──────────────────────────────────────────────────
static char *REDIRECT_KEYS[MAX_REDIRECTS];
static char *REDIRECT_VALS[MAX_REDIRECTS];
static char *LOWER_REDIRECT_KEYS[MAX_REDIRECTS];
static int REDIRECT_COUNT = 0;

extern "C" FILE *fopen(const char *path, const char *mode);
extern "C" int open(const char *path, int flags, ...);

HOOK_INIT(hook_fopen);
HOOK_INIT(hook_open);

static int in_hook = 0;
static int log_ok = 0;

// ── Forward declarations ────────────────────────────────────────────────────
static int log_write(const char *msg);

// ── Minimal JSON parser ─────────────────────────────────────────────────────
static int parse_json_pairs(const char *json, int max, char keys[][MAX_PATH], char vals[][MAX_PATH]) {
    int count = 0;
    const char *p = json;
    while (*p && count < max) {
        while (*p && *p != '{' && *p != ',' && *p != '}') p++;
        if (*p == '}') break;
        if (*p == '{' || *p == ',') p++;
        while (*p && (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r')) p++;
        if (*p != '"') continue;
        p++; int ki = 0;
        while (*p && *p != '"' && ki < MAX_PATH-1) keys[count][ki++] = *p++;
        keys[count][ki] = '\0';
        if (*p) p++;
        while (*p && (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r' || *p == ':')) p++;
        if (*p != '"') continue;
        p++; int vi = 0;
        while (*p && *p != '"' && vi < MAX_PATH-1) vals[count][vi++] = *p++;
        vals[count][vi] = '\0';
        if (*p) p++;
        count++;
    }
    return count;
}

// ── Load redirects from JSON config file ────────────────────────────────────
static void load_redirects(void) {
    int fd = open(CONFIG_PATH, O_RDONLY, 0);
    if (fd < 0) fd = sceKernelOpen(CONFIG_PATH, O_RDONLY, 0);
    if (fd < 0) {
        log_write("ERROR: no config file found and no fallback available");
        return;
    }

    char buf[16384];
    ssize_t got = read(fd, buf, sizeof(buf) - 1);
    close(fd);
    if (got <= 0) {
        log_write("ERROR: config file exists but is empty");
        return;
    }
    buf[got] = '\0';

    char *rp = strstr(buf, "\"redirects\"");
    if (!rp) {
        log_write("ERROR: redirects.json has no 'redirects' key");
        return;
    }
    rp += 10;
    while (*rp && (*rp == ' ' || *rp == '\t' || *rp == '\n' || *rp == '\r' || *rp == ':' || *rp == '"')) rp++;
    if (*rp != '{') {
        log_write("ERROR: redirects object not found in config");
        return;
    }

    char keys[MAX_REDIRECTS][MAX_PATH];
    char vals[MAX_REDIRECTS][MAX_PATH];
    int n = parse_json_pairs(rp, MAX_REDIRECTS, keys, vals);
    if (n <= 0) {
        log_write("ERROR: no valid redirect pairs found in config");
        return;
    }

    for (int i = 0; i < n && i < MAX_REDIRECTS; i++) {
        char buf_val[MAX_PATH];
        if (strchr(vals[i], '/')) {
            snprintf(buf_val, sizeof(buf_val), "%s", vals[i]);
        } else {
            snprintf(buf_val, sizeof(buf_val), AFR_BASE "/" TITLE_ID "/%s", vals[i]);
        }
        REDIRECT_KEYS[i] = (char *)malloc(strlen(keys[i]) + 1);
        REDIRECT_VALS[i] = (char *)malloc(strlen(buf_val) + 1);
        LOWER_REDIRECT_KEYS[i] = (char *)malloc(strlen(keys[i]) + 1);
        if (REDIRECT_KEYS[i] && REDIRECT_VALS[i] && LOWER_REDIRECT_KEYS[i]) {
            strcpy(REDIRECT_KEYS[i], keys[i]);
            strcpy(REDIRECT_VALS[i], buf_val);
            char *lk = LOWER_REDIRECT_KEYS[i];
            for (int j = 0; keys[i][j]; j++) lk[j] = (keys[i][j] >= 'A' && keys[i][j] <= 'Z') ? (keys[i][j] + 32) : keys[i][j];
            lk[strlen(keys[i])] = '\0';
            REDIRECT_COUNT++;
        }
    }

    char logmsg[128];
    snprintf(logmsg, sizeof(logmsg), "loaded %d redirects from config", REDIRECT_COUNT);
    log_write(logmsg);
    if (REDIRECT_COUNT > 0) {
        char sample[256];
        snprintf(sample, sizeof(sample), "  e.g. %s -> %s", REDIRECT_KEYS[0], REDIRECT_VALS[0]);
        log_write(sample);
    }
}

static void free_redirects(void) {
    for (int i = 0; i < REDIRECT_COUNT; i++) {
        free(REDIRECT_KEYS[i]);
        free(REDIRECT_VALS[i]);
        free(LOWER_REDIRECT_KEYS[i]);
    }
    REDIRECT_COUNT = 0;
}

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
        char lower_path[MAX_PATH];
        int len = strlen(path);
        if (len < MAX_PATH) {
            for (int i = 0; i < len; i++) lower_path[i] = (path[i] >= 'A' && path[i] <= 'Z') ? (path[i] + 32) : path[i];
            lower_path[len] = '\0';

            // ── User redirects from redirects.json ────────────────────────────
            if (!np) {
                for (int i = 0; i < REDIRECT_COUNT; i++) {
                    if (strstr(lower_path, LOWER_REDIRECT_KEYS[i])) {
                        np = REDIRECT_VALS[i];
                        break;
                    }
                }
            }

            // ── Trigger memory injection on any redirect ─────────────────────
            // All 32 redirects are per-song bundles (BeatmapLevelsData/*).
            // Fires every time a song bundle is opened; memory_inject_try_patch
            // has internal re-entrancy guard and only scans once.
            if (np) {
                memory_inject_try_patch();
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

// ── IL2CPP module base (reserved for future mode control) ───────────────────
static uint64_t find_il2cpp_module_base(void) {
    OrbisKernelModule modules[64];
    size_t available = 0;
    if (sceKernelGetModuleList(modules, 64, &available) < 0) return 0;
    for (size_t i = 0; i < available; i++) {
        OrbisKernelModuleInfo info;
        memset(&info, 0, sizeof(info));
        info.size = sizeof(info);
        if (sceKernelGetModuleInfo(modules[i], &info) < 0) continue;
        if (strstr(info.name, "Il2Cpp") != NULL && info.segmentCount > 0)
            return (uint64_t)info.segmentInfo[0].address;
    }
    return 0;
}

// ── Register Song Metadata for Memory Injection ─────────────────────────
// Matches the 13 Rolling Stones pack replacement slots.
// level_id must match the _levelID in the BeatmapLevelSO for the slot.
static void register_song_metadata(void) {
    SongMetadataEntry entries[] = {
        {"startmeup",               "Espresso",           "", "Sabrina Carpenter",       ""},
        {"angry",                   "Rhythm Is A Dancer", "", "Pegboard Nerds",          ""},
        {"bitemyheadoff",           "Escaping the Ruins", "", "MDK / Gareth Coker",      ""},
        {"cantyouhearmeknocking",   "Spicy",              "", "aespa",                   ""},
        {"deadmanwalking",          "Finesse (Remix)",    "", "Various",                 ""},
        {"gimmeshelter",            "Yes I'm A Mess",     "", "AJR",                     ""},
        {"icantgetnosatisfaction",  "Dreams Come True",   "", "Various",                 ""},
        {"livebythesword",          "Take Me to the Beach","", "Imagine Dragons",         ""},
        {"messitup",                "Powersnake",         "", "Brothers of Metal",       ""},
        {"paintitblack",            "Time Lapse",         "", "TheFatRat",               ""},
        {"sugarsoaker",             "Venom of Venus",     "", "Powerwolf",               ""},
        {"sympathyforthedevil",     "LIT",                "", "Polyphia",                ""},
        {"wholewideworld",          "VOLUPTE",            "", "REZZ / Tare",             ""},
    };

    int count = sizeof(entries) / sizeof(entries[0]);
    for (int i = 0; i < count; i++) {
        memory_inject_register(&entries[i]);
    }

    char buf[128];
    snprintf(buf, sizeof(buf), "Registered %d song metadata entries for memory injection", count);
    log_write(buf);
}


extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;(void)args;
    OrbisNotificationRequest notif;

    ensure_dir();
    log_write("=== BS Deluxe " PLUGIN_VERSION " started ===");
    log_write(PLUGIN_VERSION " — dynamic redirect config (reads redirects.json from AFR)");
    log_write("config: " CONFIG_PATH);
    load_redirects();

    // fopen hook
    Detour_Construct(&Detour_hook_fopen, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_fopen, (uint64_t)(void*)&fopen, (void*)fh);

    // open hook — handles ALL redirects
    Detour_Construct(&Detour_hook_open, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_open, (uint64_t)(void*)&open, (void*)open_hook);

    log_write("hooks installed");

    // Memory injection — register song metadata and start patcher thread
    register_song_metadata();
    memory_inject_init();

    // Notification
    memset(&notif,0,sizeof(notif)); notif.type=(OrbisNotificationRequestType)0; notif.targetId=-1;
    snprintf(notif.message,sizeof(notif.message),"Beat Saber Deluxe %s\nBy Chris Primeish", PLUGIN_VERSION);
    sceKernelSendNotificationRequest(0,&notif,sizeof(notif),0);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;(void)args;
    free_redirects();
    return 0;
}
