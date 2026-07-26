// Beat Saber Deluxe — dynamic redirect plugin
// Reads song redirect table from /data/GoldHEN/AFR/<TITLE_ID>/redirects.json
// Feature flags from /data/GoldHEN/AFR/<TITLE_ID>/features.json
// All redirects come from the external config file — no hardcoded fallback.
// v0.8026: TMP_Text.set_text hook — intercepts song name/artist text in UI.
// v0.8025: Removed memory injection code (v0.66–v0.8024 abandoned as dead end).

#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>
#include <signal.h>
#include <fcntl.h>
#include <unistd.h>
#include <dlfcn.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.8035"
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

// Forward declaration — deferred TMP_Text hook (defined after open_hook)
static void try_install_tmp_hook(void);

static int open_hook(const char *path, int flags, ...) {
    if (in_hook) return HOOK_CONTINUE(hook_open, int (*)(const char*, int, int), path, flags, 0);
    in_hook = 1;
    g_open_count++;

    // Deferred TMP_Text hook — install once after game modules are loaded
    try_install_tmp_hook();

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
            {
                char dbuf[512];
                snprintf(dbuf, sizeof(dbuf), "[OPEN #%d] %s%s",
                         g_open_count, path,
                         np ? " -> REDIRECTED" : "");
                log_write(dbuf);
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

// ── Close hook ──────────────────────────────────────────────────────────────
static int close_hook(int fd) {
    if (in_hook) return HOOK_CONTINUE(hook_close, int (*)(int), fd);
    in_hook = 1;
    int r = HOOK_CONTINUE(hook_close, int (*)(int), fd);
    in_hook = 0;
    return r;
}

// ── TMP_Text.set_text hook (song metadata modification) ────────────────────
// Hooks TMPro.TMP_Text::set_text(string) to intercept song name/artist text.
// Gated behind g_feature_song_metadata_modification feature flag.
// RVA: 0x2D35BE0 (virtual method, slot 66)
// Calling convention: SysV AMD64 (this in RDI, value in RSI, method in RDX)
HOOK_INIT(hook_tmp_text_set_text);
static int g_tmp_text_set_text_count = 0;

// Forward-declare IL2CPP's MethodInfo (opaque type)
struct MethodInfo;

// Song name/artist replacement table
typedef struct {
    const char* original;
    const char* replacement;
} SongNameReplacement;

static const SongNameReplacement SONG_REPLACEMENTS[] = {
    {"Start Me Up",                    "Espresso"},
    {"The Rolling Stones",             "Sabrina Carpenter"},
    {"Angry",                          "Rhythm Is A Dancer"},
    {"Bite My Head Off",               "Escaping the Ruins"},
    {"Can't You Hear Me Knocking",     "Spicy"},
    {"Dead Man Walking",               "Finesse (Remix)"},
    {"Gimme Shelter",                  "Yes I'm A Mess"},
    {"(I Can't Get No) Satisfaction",  "Dreams Come True"},
    {"Live by the Sword",              "Take Me to the Beach"},
    {"Mess It Up",                     "Powersnake"},
    {"Paint It Black",                 "Time Lapse"},
    {"Sugar Soaker",                   "Venom of Venus"},
    {"Sympathy for the Devil",         "LIT"},
    {"The Whole Wide World",           "VOLUPTE"},
    {NULL, NULL}
};

static const char* find_replacement(const char* text) {
    if (!text) return NULL;
    for (int i = 0; SONG_REPLACEMENTS[i].original; i++) {
        if (strcmp(text, SONG_REPLACEMENTS[i].original) == 0) {
            return SONG_REPLACEMENTS[i].replacement;
        }
    }
    return NULL;
}

// UTF-16LE string extraction from IL2CPP System.String
// System.String layout: klass(8) + monitor(8) + _stringLength(4) + first_char(UTF-16LE)
// _stringLength may be at offset 0x10 or 0x14 on PS4 — try both
// Protected by signal handler — value may not always be a valid string
static sigjmp_buf g_extract_jmp_buf;

static int extract_utf16_string(void* str_obj, char* out, int out_size) {
    if (!str_obj) { out[0] = '\0'; return 0; }

    // Basic sanity check — reject clearly invalid pointers
    if ((uint64_t)str_obj < 0x1000000ULL) { out[0] = '\0'; return 0; }

    // Use signal handler to catch SIGSEGV from invalid pointer dereference
    struct sigaction old_sa, new_sa;
    memset(&new_sa, 0, sizeof(new_sa));
    new_sa.__sa_handler.__sa_sigaction = [](int, struct __siginfo*, void*) {
        siglongjmp(g_extract_jmp_buf, 1);
    };
    new_sa.sa_flags = SA_SIGINFO;
    sigaction(SIGSEGV, &new_sa, &old_sa);
    sigaction(SIGBUS, &new_sa, &old_sa);

    int result = 0;
    if (sigsetjmp(g_extract_jmp_buf, 1) == 0) {
        uint32_t len_10 = *(uint32_t*)((char*)str_obj + 0x10);
        uint32_t len_14 = *(uint32_t*)((char*)str_obj + 0x14);

        uint32_t len = 0;
        uint16_t* chars = NULL;

        if (len_10 > 0 && len_10 < 256 && len_14 == 0) {
            len = len_10;
            chars = (uint16_t*)((char*)str_obj + 0x14);
        } else if (len_14 > 0 && len_14 < 256) {
            len = len_14;
            chars = (uint16_t*)((char*)str_obj + 0x18);
        } else {
            len = len_10;
            chars = (uint16_t*)((char*)str_obj + 0x14);
        }

        if (len > 0 && len < (uint32_t)out_size) {
            int i;
            for (i = 0; i < (int)len && i < out_size - 1; i++) {
                out[i] = (chars[i] < 128) ? (char)chars[i] : '?';
            }
            out[i] = '\0';
            result = len;
        }
    } else {
        out[0] = '\0';
    }

    sigaction(SIGSEGV, &old_sa, NULL);
    sigaction(SIGBUS, &old_sa, NULL);
    return result;
}

// ── IL2CPP runtime string creation ──────────────────────────────────────────
// Try to use il2cpp_string_new() for proper GC-managed strings
typedef void* (*il2cpp_string_new_func)(const char*);
static il2cpp_string_new_func g_il2cpp_string_new = NULL;
static int g_il2cpp_string_new_tried = 0;

static void* try_il2cpp_string_new(const char* cstr) {
    if (!g_il2cpp_string_new_tried) {
        g_il2cpp_string_new_tried = 1;
        g_il2cpp_string_new = (il2cpp_string_new_func)dlsym(RTLD_DEFAULT, "il2cpp_string_new");
        if (g_il2cpp_string_new) {
            log_write("[METADATA] il2cpp_string_new found via dlsym");
        } else {
            log_write("[METADATA] il2cpp_string_new NOT found — using manual string creation");
        }
    }
    if (g_il2cpp_string_new) {
        return g_il2cpp_string_new(cstr);
    }
    return NULL;
}

// Create a new IL2CPP System.String from a C string (manual fallback)
// System.String layout: klass(8) + monitor(8) + _stringLength(4) + first_char(UTF-16LE)
// Uses the klass pointer from an existing string object
static void* create_il2cpp_string(void* klass_ptr, const char* cstr) {
    if (!klass_ptr || !cstr) return NULL;

    int len = strlen(cstr);
    // Size: 16 (klass+monitor) + 4 (length) + (len * 2) (UTF-16LE chars) + 2 (null terminator)
    int total = 16 + 4 + (len * 2) + 2;
    void* str_mem = malloc(total);
    if (!str_mem) return NULL;

    // Copy klass pointer (8 bytes)
    memcpy(str_mem, klass_ptr, 8);
    // Zero monitor (8 bytes)
    memset((char*)str_mem + 8, 0, 8);
    // Set string length
    *(uint32_t*)((char*)str_mem + 16) = (uint32_t)len;
    // Convert ASCII to UTF-16LE
    uint16_t* chars = (uint16_t*)((char*)str_mem + 20);
    for (int i = 0; i < len; i++) {
        chars[i] = (uint16_t)(unsigned char)cstr[i];
    }
    // Null terminator (optional but safe)
    chars[len] = 0;

    return str_mem;
}

static void tmp_text_set_text_hook(void* this_ptr, void* value, const MethodInfo* method) {
    g_tmp_text_set_text_count++;

    // Log first 15 calls unconditionally — verify hook fires
    if (g_tmp_text_set_text_count <= 15) {
        char logmsg[256];
        snprintf(logmsg, sizeof(logmsg), "[METADATA] set_text #%d: this=%p value=%p",
                 g_tmp_text_set_text_count, this_ptr, value);
        log_write(logmsg);
    }

    // Read string and check for matches (with null guard)
    void* new_value = value;
    if (g_feature_song_metadata_modification && value) {
        char text_buf[256] = {0};
        int len = extract_utf16_string(value, text_buf, sizeof(text_buf));

        if (len > 0) {
            const char* replacement = find_replacement(text_buf);
            if (replacement) {
                // Log this pointer to identify song name vs artist vs detail fields
                char logmsg[512];
                snprintf(logmsg, sizeof(logmsg), "[METADATA] REPLACE #%d: this=%p '%s' -> '%s'",
                         g_tmp_text_set_text_count, this_ptr, text_buf, replacement);
                log_write(logmsg);

                // Create replacement string — try IL2CPP runtime first, manual fallback
                void* replacement_str = try_il2cpp_string_new(replacement);
                if (!replacement_str) {
                    replacement_str = create_il2cpp_string(value, replacement);
                }
                if (replacement_str) {
                    new_value = replacement_str;
                }

                // Hex dump first 24 bytes of original string for layout diagnosis
                if (g_tmp_text_set_text_count <= 300) {
                    uint8_t* raw = (uint8_t*)value;
                    char hex[128];
                    snprintf(hex, sizeof(hex), "[METADATA] RAW this=%p val=%p: "
                             "%02x %02x %02x %02x %02x %02x %02x %02x | "
                             "%02x %02x %02x %02x %02x %02x %02x %02x | "
                             "%02x %02x %02x %02x %02x %02x %02x %02x",
                             this_ptr, value,
                             raw[0],raw[1],raw[2],raw[3],raw[4],raw[5],raw[6],raw[7],
                             raw[8],raw[9],raw[10],raw[11],raw[12],raw[13],raw[14],raw[15],
                             raw[16],raw[17],raw[18],raw[19],raw[20],raw[21],raw[22],raw[23]);
                    log_write(hex);
                }
            }
        }
    }

    // Call original function with (possibly replaced) value
    HOOK_CONTINUE(hook_tmp_text_set_text, void (*)(void*, void*, const MethodInfo*),
                  this_ptr, new_value, method);

    // DO NOT free replacement string — set_text stores the reference internally
    // for deferred rendering. Freeing it causes use-after-free → "?" in UI.
    // Strings are small (~50 bytes each), leak is acceptable for now.
}

// ── IL2CPP module base ──────────────────────────────────────────────────────
static uint64_t find_il2cpp_module_base(void) {
    OrbisKernelModule modules[256];
    size_t available = 0;
    if (sceKernelGetModuleList(modules, 256, &available) < 0) {
        log_write("[METADATA] sceKernelGetModuleList failed");
        return 0;
    }

    char logmsg[256];
    snprintf(logmsg, sizeof(logmsg), "[METADATA] Found %zu modules", available);
    log_write(logmsg);

    for (size_t i = 0; i < available; i++) {
        OrbisKernelModuleInfo info;
        memset(&info, 0, sizeof(info));
        info.size = sizeof(info);
        if (sceKernelGetModuleInfo(modules[i], &info) < 0) continue;
        if (strstr(info.name, "Il2Cpp") != NULL && info.segmentCount > 0) {
            snprintf(logmsg, sizeof(logmsg), "[METADATA] Found IL2CPP module: %s at 0x%lx (%d segments)",
                     info.name, (uint64_t)info.segmentInfo[0].address, info.segmentCount);
            log_write(logmsg);
            return (uint64_t)info.segmentInfo[0].address;
        }
    }

    // Log first 20 module names for diagnostics
    log_write("[METADATA] IL2CPP module not found. First 20 modules:");
    for (size_t i = 0; i < available && i < 20; i++) {
        OrbisKernelModuleInfo info;
        memset(&info, 0, sizeof(info));
        info.size = sizeof(info);
        if (sceKernelGetModuleInfo(modules[i], &info) < 0) continue;
        snprintf(logmsg, sizeof(logmsg), "  [%zu] %s", i, info.name);
        log_write(logmsg);
    }
    return 0;
}


// ── Deferred TMP_Text hook installation ─────────────────────────────────────
// Must be called from open_hook() — at plugin load time, only 3 modules are
// visible. By the time the game opens files, all modules are loaded.
// Retries on each open until module is found (max 50 attempts).
static int g_tmp_hook_attempts = 0;
static int g_tmp_hook_installed = 0;

static void try_install_tmp_hook(void) {
    if (g_tmp_hook_installed) return;
    if (g_feature_song_metadata_modification == 0) return;

    // Skip early opens — our own log file and system devices load before game modules
    if (g_tmp_hook_attempts > 0 && g_open_count < 10) return;
    g_tmp_hook_attempts++;

    uint64_t il2cpp_base = find_il2cpp_module_base();
    if (!il2cpp_base) {
        if (g_tmp_hook_attempts <= 3 || g_tmp_hook_attempts % 20 == 0) {
            char logmsg[256];
            snprintf(logmsg, sizeof(logmsg), "[METADATA] Module not found (attempt %d, open #%d) — retrying",
                     g_tmp_hook_attempts, g_open_count);
            log_write(logmsg);
        }
        if (g_tmp_hook_attempts < 50) return;  // keep retrying
        log_write("[METADATA] ERROR: IL2CPP module not found after 50 attempts — giving up");
        return;
    }

    char logmsg[256];
    uint64_t target = il2cpp_base + 0x2D35BE0;
    snprintf(logmsg, sizeof(logmsg), "[METADATA] IL2CPP base: 0x%lx, set_text target: 0x%lx (attempt %d, open #%d)",
             il2cpp_base, target, g_tmp_hook_attempts, g_open_count);
    log_write(logmsg);

    Detour_Construct(&Detour_hook_tmp_text_set_text, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_tmp_text_set_text, target, (void*)tmp_text_set_text_hook);
    g_tmp_hook_installed = 1;
    log_write("[METADATA] TMP_Text.set_text hook installed");
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
        log_write("DISABLED: song_metadata_modification is OFF — awaiting new approach");
    }

    // fopen hook
    Detour_Construct(&Detour_hook_fopen, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_fopen, (uint64_t)(void*)&fopen, (void*)fh);

    // open hook — handles ALL redirects
    Detour_Construct(&Detour_hook_open, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_open, (uint64_t)(void*)&open, (void*)open_hook);

    // close hook
    Detour_Construct(&Detour_hook_close, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_close, (uint64_t)(void*)&close, (void*)close_hook);

    log_write("hooks installed");

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
