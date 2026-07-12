// Beat Saber Deluxe — dynamic redirect plugin
// Reads song redirect table from /data/GoldHEN/AFR/<TITLE_ID>/redirects.json
// Falls back to internal hardcoded defaults if config file is missing.

#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.54"
#define AFR_BASE  "/data/GoldHEN/AFR"
#define TITLE_ID "CUSA12878"
#define LOG_PATH AFR_BASE "/" TITLE_ID "/bs_log.txt"
#define CONFIG_PATH AFR_BASE "/" TITLE_ID "/redirects.json"
#define MAX_REDIRECTS 256
#define MAX_PATH 256

// ── Dynamic redirect table ──────────────────────────────────────────────────
// Populated from redirects.json at startup. Falls back to hardcoded defaults.
static char *REDIRECT_KEYS[MAX_REDIRECTS];
static char *REDIRECT_VALS[MAX_REDIRECTS];
static int REDIRECT_COUNT = 0;

// ── Built-in fallback defaults ──────────────────────────────────────────────
// Used when redirects.json is not present on the PS4.
static const char *FALLBACK_TABLE[][2] = {
    {"BeatmapLevelsData/angry",                AFR_BASE "/" TITLE_ID "/angry_v3"},
    {"BeatmapLevelsData/bitemyheadoff",        AFR_BASE "/" TITLE_ID "/bitemyheadoff_v3"},
    {"BeatmapLevelsData/cantyouhearmeknocking",AFR_BASE "/" TITLE_ID "/cantyouhearmeknocking_v3"},
    {"BeatmapLevelsData/deadmanwalking",       AFR_BASE "/" TITLE_ID "/deadmanwalking_v3"},
    {"BeatmapLevelsData/gimmeshelter",         AFR_BASE "/" TITLE_ID "/gimmeshelter_v3"},
    {"BeatmapLevelsData/icantgetnosatisfaction",AFR_BASE "/" TITLE_ID "/icantgetnosatisfaction_v3"},
    {"BeatmapLevelsData/livebythesword",       AFR_BASE "/" TITLE_ID "/livebythesword_v3"},
    {"BeatmapLevelsData/messitup",             AFR_BASE "/" TITLE_ID "/messitup_v3"},
    {"BeatmapLevelsData/paintitblack",         AFR_BASE "/" TITLE_ID "/paintitblack_v3"},
    {"BeatmapLevelsData/startmeup",            AFR_BASE "/" TITLE_ID "/startmeup_v3"},
    {"BeatmapLevelsData/sugarsoaker",          AFR_BASE "/" TITLE_ID "/sugarsoaker_v3"},
    {"BeatmapLevelsData/sympathyforthedevil",  AFR_BASE "/" TITLE_ID "/sympathyforthedevil_v3"},
    {"BeatmapLevelsData/wholewideworld",       AFR_BASE "/" TITLE_ID "/wholewideworld_v3"},
    {NULL, NULL}
};

extern "C" FILE *fopen(const char *path, const char *mode);
extern "C" int open(const char *path, int flags, ...);

HOOK_INIT(hook_fopen);
HOOK_INIT(hook_open);

static int in_hook = 0;
static int log_ok = 0;

// ── Forward declarations ────────────────────────────────────────────────────
static int log_write(const char *msg);

// ── Minimal JSON parser ─────────────────────────────────────────────────────
// Extracts key-value pairs from a flat JSON object like:
//   {"startmeup":"startmeup_custom_v3","angry":"angry_custom_v3"}
// Stores up to max entries. Returns number of pairs found.

static int parse_json_pairs(const char *json, int max, char keys[][MAX_PATH], char vals[][MAX_PATH]) {
    int count = 0;
    const char *p = json;
    while (*p && count < max) {
        // Find opening brace or comma for next key
        while (*p && *p != '{' && *p != ',' && *p != '}') p++;
        if (*p == '}') break;
        if (*p == '{' || *p == ',') p++;
        // Skip whitespace
        while (*p && (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r')) p++;
        if (*p != '"') continue;
        // Read key
        p++; int ki = 0;
        while (*p && *p != '"' && ki < MAX_PATH-1) keys[count][ki++] = *p++;
        keys[count][ki] = '\0';
        if (*p) p++;
        // Skip colon and whitespace
        while (*p && (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r' || *p == ':')) p++;
        if (*p != '"') continue;
        // Read value
        p++; int vi = 0;
        while (*p && *p != '"' && vi < MAX_PATH-1) vals[count][vi++] = *p++;
        vals[count][vi] = '\0';
        if (*p) p++;
        count++;
    }
    return count;
}

// ── Helper: fall back to built-in table ────────────────────────────────────

static int use_fallback_table(void) {
    int count = 0;
    for (int i = 0; FALLBACK_TABLE[i][0] && i < MAX_REDIRECTS; i++) {
        REDIRECT_KEYS[i] = (char *)malloc(strlen(FALLBACK_TABLE[i][0]) + 1);
        REDIRECT_VALS[i] = (char *)malloc(strlen(FALLBACK_TABLE[i][1]) + 1);
        if (REDIRECT_KEYS[i] && REDIRECT_VALS[i]) {
            strcpy(REDIRECT_KEYS[i], FALLBACK_TABLE[i][0]);
            strcpy(REDIRECT_VALS[i], FALLBACK_TABLE[i][1]);
            count++;
        }
    }
    log_write("using built-in fallback redirect table");
    return count;
}

// ── Load redirects from JSON config file ────────────────────────────────────

static void load_redirects(void) {
    // Try to open the config file
    int fd = sceKernelOpen(CONFIG_PATH, O_RDONLY, 0);
    if (fd < 0) {
        REDIRECT_COUNT = use_fallback_table();
        return;
    }

    // Read file content
    char buf[16384];
    ssize_t got = sceKernelRead(fd, buf, sizeof(buf) - 1);
    sceKernelClose(fd);
    if (got <= 0) {
        REDIRECT_COUNT = use_fallback_table();
        return;
    }
    buf[got] = '\0';

    // Find the "redirects" object in the JSON
    char *rp = strstr(buf, "\"redirects\"");
    if (!rp) {
        REDIRECT_COUNT = use_fallback_table();
        return;
    }
    rp += 10;
    while (*rp && (*rp == ' ' || *rp == '\t' || *rp == '\n' || *rp == '\r' || *rp == ':')) rp++;
    if (*rp != '{') {
        REDIRECT_COUNT = use_fallback_table();
        return;
    }

    // Parse the redirects object
    char keys[MAX_REDIRECTS][MAX_PATH];
    char vals[MAX_REDIRECTS][MAX_PATH];
    int n = parse_json_pairs(rp, MAX_REDIRECTS, keys, vals);
    if (n <= 0) {
        REDIRECT_COUNT = use_fallback_table();
        return;
    }

    // Allocate and populate the redirect table
    for (int i = 0; i < n && i < MAX_REDIRECTS; i++) {
        char buf_key[MAX_PATH + 32];
        snprintf(buf_key, sizeof(buf_key), "BeatmapLevelsData/%s", keys[i]);
        char buf_val[MAX_PATH];
        if (strchr(vals[i], '/')) {
            snprintf(buf_val, sizeof(buf_val), "%s", vals[i]);
        } else {
            snprintf(buf_val, sizeof(buf_val), AFR_BASE "/" TITLE_ID "/%s", vals[i]);
        }
        REDIRECT_KEYS[i] = (char *)malloc(strlen(buf_key) + 1);
        REDIRECT_VALS[i] = (char *)malloc(strlen(buf_val) + 1);
        if (REDIRECT_KEYS[i] && REDIRECT_VALS[i]) {
            strcpy(REDIRECT_KEYS[i], buf_key);
            strcpy(REDIRECT_VALS[i], buf_val);
            REDIRECT_COUNT++;
        }
    }

    char logmsg[128];
    snprintf(logmsg, sizeof(logmsg), "loaded %d redirects from config", REDIRECT_COUNT);
    log_write(logmsg);
    // Log first entry as a sample for log verification
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
        for (int i = 0; i < REDIRECT_COUNT; i++) {
            if (strstr(path, REDIRECT_KEYS[i])) {
                np = REDIRECT_VALS[i];
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
    OrbisNotificationRequest notif;

    ensure_dir();
    log_write("=== BS Deluxe " PLUGIN_VERSION " started ===");
    log_write("v" PLUGIN_VERSION " — dynamic redirect config (reads redirects.json from AFR)");

    // Log the config path being checked for debugging
    log_write("config: " CONFIG_PATH);

    // Load redirects from external config (or fall back to built-in)
    load_redirects();

    // fopen hook via Detour
    Detour_Construct(&Detour_hook_fopen, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_fopen, (uint64_t)(void*)&fopen, (void*)fh);

    // open hook via Detour — handles ALL redirects
    Detour_Construct(&Detour_hook_open, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_open, (uint64_t)(void*)&open, (void*)open_hook);

    log_write("hooks installed");

    // Notification
    memset(&notif,0,sizeof(notif)); notif.type=(OrbisNotificationRequestType)0; notif.targetId=-1;
    snprintf(notif.message,sizeof(notif.message),"BS Deluxe %s", PLUGIN_VERSION);
    sceKernelSendNotificationRequest(0,&notif,sizeof(notif),0);

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;(void)args;
    free_redirects();
    return 0;
}
