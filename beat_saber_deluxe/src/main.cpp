// Beat Saber Deluxe — dynamic redirect plugin
// Reads song redirect table from /data/GoldHEN/AFR/<TITLE_ID>/redirects.json
// Feature flags from /data/GoldHEN/AFR/<TITLE_ID>/features.json
// All redirects come from the external config file — no hardcoded fallback.
// v0.8023: Trigger scan at BeatmapLevelsData redirect (OPEN #740) instead of pack load (OPEN #738). Objects deserialized lazily.
// v0.8022: Scan BOTH GC heap (0x200000000-0x210000000) AND metadata mmap (±256MB).
// v0.8021: Scan trigger moved to therollingstones_pack_assets_all (OPEN #738) instead of first pack_assets_all (OPEN #207).
// v0.8020: Scan metadata region (±256MB around 0x293280000), log all file opens.
// v0.8012: Feature flags — enable_custom_song_replacements, enable_song_metadata_modification
// v0.8011: Memory injection — optimized string search (8× faster, dual-format matching).
// v0.79: Memory injection — STRDEBUG logging to determine System_String length offset on PS4.
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

#define PLUGIN_VERSION "v0.8023"
#define AFR_BASE  "/data/GoldHEN/AFR"
#define TITLE_ID "CUSA12878"
#define LOG_PATH AFR_BASE "/" TITLE_ID "/bs_log.txt"
#define CONFIG_PATH AFR_BASE "/" TITLE_ID "/redirects.json"
#define FEATURES_PATH AFR_BASE "/" TITLE_ID "/features.json"
#define MAX_REDIRECTS 256
#define MAX_PATH 256

// ── Dynamic redirect table ──────────────────────────────────────────────────
static char *REDIRECT_KEYS[MAX_REDIRECTS];
static char *REDIRECT_VALS[MAX_REDIRECTS];
static char *LOWER_REDIRECT_KEYS[MAX_REDIRECTS];
static int REDIRECT_COUNT = 0;

// ── Feature flags ────────────────────────────────────────────────────────────
// Read from /data/GoldHEN/AFR/CUSA12878/features.json at startup.
// Missing file or missing key = false (default off for safety).
static int g_feature_custom_song_replacements = 0;
static int g_feature_song_metadata_modification = 0;

// ── Forward declarations ────────────────────────────────────────────────────
static int log_write(const char *msg);

static void load_features(void) {
    int fd = open(FEATURES_PATH, O_RDONLY, 0);
    if (fd < 0) fd = sceKernelOpen(FEATURES_PATH, O_RDONLY, 0);
    if (fd < 0) {
        log_write("features.json not found — all feature flags OFF (default)");
        return;
    }

    char buf[4096];
    ssize_t got = read(fd, buf, sizeof(buf) - 1);
    close(fd);
    if (got <= 0) {
        log_write("features.json is empty — all feature flags OFF");
        return;
    }
    buf[got] = '\0';

    // Simple key:true/false parser
    const char *p = buf;
    while (*p) {
        // Find a key (quoted string)
        while (*p && *p != '"') p++;
        if (!*p) break;
        p++; int ki = 0;
        char key[128];
        while (*p && *p != '"' && ki < (int)sizeof(key)-1) key[ki++] = *p++;
        key[ki] = '\0';
        if (*p) p++;

        // Skip to value
        while (*p && *p != ':' && *p != 't' && *p != 'f') p++;
        if (*p == ':') p++;
        while (*p && *p != 't' && *p != 'f' && *p != 'n' && *p != '"') p++;

        int val = 0;
        if (*p == 't') { val = 1; while (*p && *p != ',' && *p != '}') p++; }
        else if (*p == 'f') { val = 0; while (*p && *p != ',' && *p != '}') p++; }

        if (strcmp(key, "enable_custom_song_replacements") == 0) {
            g_feature_custom_song_replacements = val;
        } else if (strcmp(key, "enable_song_metadata_modification") == 0) {
            g_feature_song_metadata_modification = val;
        }
    }

    char logmsg[256];
    snprintf(logmsg, sizeof(logmsg), "features: custom_song_replacements=%d metadata_modification=%d",
             g_feature_custom_song_replacements, g_feature_song_metadata_modification);
    log_write(logmsg);
}

extern "C" FILE *fopen(const char *path, const char *mode);
extern "C" int open(const char *path, int flags, ...);
extern "C" int close(int fd);

HOOK_INIT(hook_fopen);
HOOK_INIT(hook_open);
HOOK_INIT(hook_close);

static int in_hook = 0;
static int log_ok = 0;

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

// ── Diagnostic counters ──────────────────────────────────────────────────────
static int g_redirect_count = 0;
static int g_open_count = 0;

static int open_hook(const char *path, int flags, ...) {
    if (in_hook) return HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    in_hook = 1;
    g_open_count++;

    const char *np = NULL;
    if (path) {
        char lower_path[MAX_PATH];
        int len = strlen(path);
        if (len < MAX_PATH) {
            for (int i = 0; i < len; i++) lower_path[i] = (path[i] >= 'A' && path[i] <= 'Z') ? (path[i] + 32) : path[i];
            lower_path[len] = '\0';

            // ── User redirects from redirects.json ────────────────────────────
            // Only active when enable_custom_song_replacements feature flag is ON
            if (!np && g_feature_custom_song_replacements) {
                for (int i = 0; i < REDIRECT_COUNT; i++) {
                    if (strstr(lower_path, LOWER_REDIRECT_KEYS[i])) {
                        np = REDIRECT_VALS[i];
                        break;
                    }
                }
            }

            // ── Diagnostic: log ALL file opens with original path ─────────────
            // Shows the full load sequence. Logs every open with sequential counter.
            {
                char dbuf[512];
                const char *filename = strrchr(path, '/');
                filename = filename ? filename + 1 : path;
                snprintf(dbuf, sizeof(dbuf), "[OPEN #%d] %s%s",
                         g_open_count, path,
                         np ? " -> REDIRECTED" : "");
                log_write(dbuf);
            }

            // ── Trigger memory injection on BeatmapLevelsData redirect ──────────
            // BeatmapLevelSO objects are deserialized lazily — only when the game
            // actually reads the song data. The pack bundle header loads at OPEN #738
            // but objects aren't in GC heap until the game uses them.
            // Trigger at the first BeatmapLevelsData redirect (OPEN #740) when the
            // game actually reads song data and objects should be in memory.
            if (np && g_feature_song_metadata_modification) {
                if (strstr(lower_path, "beatmaplevelsdata/")) {
                    log_write("[MEMINJ] BeatmapLevelsData redirect — scanning now");
                    memory_inject_try_patch();
                }
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

// ── Close hook (no longer retries MEMINJ — strings not in memory at startup) ──
static int close_hook(int fd) {
    if (in_hook) return HOOK_CONTINUE(hook_close, int (*)(int), fd);
    in_hook = 1;
    int r = HOOK_CONTINUE(hook_close, int (*)(int), fd);
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
        {"startmeup",               "Espresso",           "", "Sabrina Carpenter",       "", "Start Me Up",           "", "The Rolling Stones"},
        {"angry",                   "Rhythm Is A Dancer", "", "Pegboard Nerds",          "", "Angry",                 "", "The Rolling Stones"},
        {"bitemyheadoff",           "Escaping the Ruins", "", "MDK / Gareth Coker",      "", "Bite My Head Off",      "", "The Rolling Stones"},
        {"cantyouhearmeknocking",   "Spicy",              "", "aespa",                   "", "Can't You Hear Me Knocking", "", "The Rolling Stones"},
        {"deadmanwalking",          "Finesse (Remix)",    "", "Various",                 "", "Dead Man Walking",      "", "The Rolling Stones"},
        {"gimmeshelter",            "Yes I'm A Mess",     "", "AJR",                     "", "Gimme Shelter",          "", "The Rolling Stones"},
        {"icantgetnosatisfaction",  "Dreams Come True",   "", "Various",                 "", "(I Can't Get No) Satisfaction", "", "The Rolling Stones"},
        {"livebythesword",          "Take Me to the Beach","", "Imagine Dragons",         "", "Live by the Sword",     "", "The Rolling Stones"},
        {"messitup",                "Powersnake",         "", "Brothers of Metal",       "", "Mess It Up",            "", "The Rolling Stones"},
        {"paintitblack",            "Time Lapse",         "", "TheFatRat",               "", "Paint It Black",        "", "The Rolling Stones"},
        {"sugarsoaker",             "Venom of Venus",     "", "Powerwolf",               "", "Sugar Soaker",          "", "The Rolling Stones"},
        {"sympathyforthedevil",     "LIT",                "", "Polyphia",                "", "Sympathy for the Devil", "", "The Rolling Stones"},
        {"wholewideworld",          "VOLUPTE",            "", "REZZ / Tare",             "", "The Whole Wide World",  "", "The Rolling Stones"},
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

    // Load feature flags first — they gate everything else
    load_redirects();
    load_features();

    // Log feature flag state for debugging
    {
        char flog[256];
        snprintf(flog, sizeof(flog), "FEATURE FLAGS: custom_song_replacements=%s  metadata_modification=%s",
                 g_feature_custom_song_replacements ? "ON" : "OFF",
                 g_feature_song_metadata_modification ? "ON" : "OFF");
        log_write(flog);
    }

    if (!g_feature_custom_song_replacements) {
        log_write("DISABLED: custom_song_replacements is OFF — redirects will NOT fire");
    }
    if (!g_feature_song_metadata_modification) {
        log_write("DISABLED: song_metadata_modification is OFF — memory injection will NOT run");
    }

    // fopen hook
    Detour_Construct(&Detour_hook_fopen, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_fopen, (uint64_t)(void*)&fopen, (void*)fh);

    // open hook — handles ALL redirects
    Detour_Construct(&Detour_hook_open, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_open, (uint64_t)(void*)&open, (void*)open_hook);

    // close hook — retries MEMINJ after per-song bundle close
    Detour_Construct(&Detour_hook_close, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_close, (uint64_t)(void*)&close, (void*)close_hook);

    log_write("hooks installed");

    // Memory injection — register song metadata and start patcher thread
    // Only active when enable_song_metadata_modification feature flag is ON.
    if (g_feature_song_metadata_modification) {
        register_song_metadata();
        memory_inject_init();
    } else {
        log_write("DISABLED: song_metadata_modification is OFF — memory injection skipped");
    }

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
