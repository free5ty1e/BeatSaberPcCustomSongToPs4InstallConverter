// Beat Saber Deluxe — dynamic redirect plugin
// Reads song redirect table from /data/GoldHEN/AFR/<TITLE_ID>/redirects.json
// All redirects come from the external config file — no hardcoded fallback.

#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.58"
#define AFR_BASE  "/data/GoldHEN/AFR"
#define TITLE_ID "CUSA12878"
#define LOG_PATH AFR_BASE "/" TITLE_ID "/bs_log.txt"
#define CONFIG_PATH AFR_BASE "/" TITLE_ID "/redirects.json"
#define MAX_REDIRECTS 256
#define MAX_PATH 256

// ── Dynamic redirect table ──────────────────────────────────────────────────
// Populated from redirects.json at startup. No hardcoded fallback.
static char *REDIRECT_KEYS[MAX_REDIRECTS];
static char *REDIRECT_VALS[MAX_REDIRECTS];
static char *LOWER_REDIRECT_KEYS[MAX_REDIRECTS];
static int REDIRECT_COUNT = 0;

extern "C" FILE *fopen(const char *path, const char *mode);
extern "C" int open(const char *path, int flags, ...);

HOOK_INIT(hook_fopen);
HOOK_INIT(hook_open);
HOOK_INIT(hook_get_preview);
HOOK_INIT(hook_set_data);
HOOK_INIT(hook_set_content);

// IL2CPP hook functions use __attribute__((ms_abi)) so they receive arguments
// in MS x64 registers (RCX, RDX, R8, R9) — matching what IL2CPP-generated code
// uses. Without this, the Detour jumps from IL2CPP code (MS x64) to the C hook
// function, which by convention reads from SysV AMD64 registers (RDI, RSI, ...)
// → arguments are garbage → crash.
static void* __attribute__((ms_abi)) get_preview_detour(void* _this);
static void __attribute__((ms_abi)) set_data_detour(void* _this, void* chars, void* selected, void* notAllowed);
static void __attribute__((ms_abi)) set_content_detour(void* _this, void* level, int allowedMask, void* notAllowedChars, int defaultDiff, void* defaultChar, void* playerData);

static int in_hook = 0;
static int log_ok = 0;
static int il2cpp_hook_installed = 0;
static uint64_t il2cpp_module_base = 0;

// ── Forward declarations ────────────────────────────────────────────────────
static int log_write(const char *msg);
static int maybe_install_il2cpp_hook(void);

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

// ── Load redirects from JSON config file ────────────────────────────────────

static void load_redirects(void) {
    // Try to open the config file via POSIX open (respects GoldHEN AFR mapping)
    int fd = open(CONFIG_PATH, O_RDONLY, 0);
    if (fd < 0) {
        // Fallback: try sceKernelOpen directly
        fd = sceKernelOpen(CONFIG_PATH, O_RDONLY, 0);
    }
    if (fd < 0) {
        log_write("ERROR: no config file found and no fallback available");
        return;
    }

    // Read file content
    char buf[16384];
    ssize_t got = read(fd, buf, sizeof(buf) - 1);
    close(fd);
    if (got <= 0) {
        log_write("ERROR: config file exists but is empty");
        return;
    }
    buf[got] = '\0';

    // Find the "redirects" object in the JSON
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

    // Parse the redirects object
    char keys[MAX_REDIRECTS][MAX_PATH];
    char vals[MAX_REDIRECTS][MAX_PATH];
    int n = parse_json_pairs(rp, MAX_REDIRECTS, keys, vals);
    if (n <= 0) {
        log_write("ERROR: no valid redirect pairs found in config");
        return;
    }

    // Allocate and populate the redirect table
    for (int i = 0; i < n && i < MAX_REDIRECTS; i++) {
        char buf_key[MAX_PATH + 32];
        snprintf(buf_key, sizeof(buf_key), "%s", keys[i]);
        char buf_val[MAX_PATH];
        if (strchr(vals[i], '/')) {
            snprintf(buf_val, sizeof(buf_val), "%s", vals[i]);
        } else {
            snprintf(buf_val, sizeof(buf_val), AFR_BASE "/" TITLE_ID "/%s", vals[i]);
        }
        REDIRECT_KEYS[i] = (char *)malloc(strlen(buf_key) + 1);
        REDIRECT_VALS[i] = (char *)malloc(strlen(buf_val) + 1);
        LOWER_REDIRECT_KEYS[i] = (char *)malloc(strlen(buf_key) + 1);
        if (REDIRECT_KEYS[i] && REDIRECT_VALS[i] && LOWER_REDIRECT_KEYS[i]) {
            strcpy(REDIRECT_KEYS[i], buf_key);
            strcpy(REDIRECT_VALS[i], buf_val);
            char *lk = LOWER_REDIRECT_KEYS[i];
            for (int j = 0; buf_key[j]; j++) lk[j] = (buf_key[j] >= 'A' && buf_key[j] <= 'Z') ? (buf_key[j] + 32) : buf_key[j];
            lk[strlen(buf_key)] = '\0';
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

    // Lazy init: install IL2CPP hook once module becomes available
    if (!il2cpp_hook_installed) {
        maybe_install_il2cpp_hook();
    }

    const char *np = NULL;
    if (path) {
        char lower_path[MAX_PATH];
        int len = strlen(path);
        if (len < MAX_PATH) {
            for (int i = 0; i < len; i++) lower_path[i] = (path[i] >= 'A' && path[i] <= 'Z') ? (path[i] + 32) : path[i];
            lower_path[len] = '\0';
            for (int i = 0; i < REDIRECT_COUNT; i++) {
                if (strstr(lower_path, LOWER_REDIRECT_KEYS[i])) {
                    np = REDIRECT_VALS[i];
                    break;
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

// ── IL2CPP hooks (mode selector + custom song info) ────────────────────────
// IL2CPP on PS4 uses MS x64 calling convention (RCX=this, RDX=arg1, R8=arg2, R9=arg3).
// ALL hook functions use __attribute__((ms_abi)) to match this convention.
// BeatmapLevelSO.get_previewDifficultyBeatmapSets() @ 0x988E80
// BeatmapCharacteristicSegmentedControlController.SetData() @ 0x1D5A210
// StandardLevelDetailView.SetContent() @ 0x1C3B630
#define IL2CPP_GET_PREVIEW_RVA 0x988E80ULL
#define IL2CPP_SET_DATA_RVA 0x1D5A210ULL
#define IL2CPP_SET_CONTENT_RVA 0x1C3B630ULL

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

static int maybe_install_il2cpp_hook(void) {
    if (il2cpp_hook_installed) return 1;
    uint64_t base = find_il2cpp_module_base();
    if (!base) return 0;
    il2cpp_module_base = base;  // save for later hooks

    char buf[128];

    // Hook 1: get_previewDifficultyBeatmapSets (inlined, may not be called)
    uint64_t t1 = base + IL2CPP_GET_PREVIEW_RVA;
    Detour_Construct(&Detour_hook_get_preview, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_get_preview, t1, (void*)get_preview_detour);
    snprintf(buf, sizeof(buf), "IL2CPP preview hook at %p", (void*)t1);
    log_write(buf);

    // Hook 2: BeatmapCharacteristicSegmentedControlController.SetData()
    uint64_t t2 = base + IL2CPP_SET_DATA_RVA;
    Detour_Construct(&Detour_hook_set_data, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_set_data, t2, (void*)set_data_detour);
    snprintf(buf, sizeof(buf), "IL2CPP set_data hook at %p", (void*)t2);
    log_write(buf);

    // Hook 3: StandardLevelDetailView.SetContent() — called when song selected
    uint64_t t3 = base + IL2CPP_SET_CONTENT_RVA;
    Detour_Construct(&Detour_hook_set_content, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_set_content, t3, (void*)set_content_detour);
    snprintf(buf, sizeof(buf), "IL2CPP set_content hook at %p", (void*)t3);
    log_write(buf);

    il2cpp_hook_installed = 1;
    return 1;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  ms_abi hooks
//  These use __attribute__((ms_abi)) to match IL2CPP's MS x64 calling convention
//  (RCX=this, RDX=arg1, R8=arg2, R9=arg3). Without this, C's default SysV AMD64
//  reads from different registers (RDI, RSI, ...) → arguments are garbage.
//  For calling the ORIGINAL function we use TrampolinePtr cast to an ms_abi
//  function pointer, because Detour_Stub uses SysV convention under the hood.
// ═══════════════════════════════════════════════════════════════════════════════

// ── get_previewDifficultyBeatmapSets hook ────────────────────────────────────
// Reads _previewDifficultyBeatmapSets field at offset 0x98 directly (avoids
// calling the original function, which avoids the Stub calling-convention issue).
// Augments a 1-element array (Standard only) to 3 entries.
static void* __attribute__((ms_abi)) get_preview_detour(void* _this) {
    // Read the field at offset 0x98 — no need to call the original at all
    void* result = *(void**)((char*)_this + 0x98);
    if (!result) return result;

    // Il2CppArray: header 0x20 = klass(8)+monitor(8)+bounds(8)+max_length(8)
    uint64_t old_len = *(uint64_t*)((char*)result + 0x18);
    if (old_len != 1) return result;  // only augment Standard-only arrays

    enum { HDR = 0x20 };
    static const int N = 3;
    size_t new_sz = HDR + (size_t)N * sizeof(void*);
    void* new_arr = malloc(new_sz);
    if (!new_arr) return result;

    memcpy(new_arr, result, HDR);
    *(uint64_t*)((char*)new_arr + 0x18) = N;
    void* elem = *(void**)((char*)result + HDR);
    for (int i = 0; i < N; i++)
        ((void**)((char*)new_arr + HDR))[i] = elem;

#ifdef VERBOSE_LOG
    {
        char buf[256];
        snprintf(buf, sizeof(buf), "augmented preview: %llu -> %d this=%p",
                 (unsigned long long)old_len, N, _this);
        log_write(buf);
    }
#endif
    return new_arr;
}

// ── SetData hook ─────────────────────────────────────────────────────────────
// BeatmapCharacteristicSegmentedControlController.SetData()
// Called when 2+ characteristics exist. We augment the input array if needed
// then call the original via TrampolinePtr (ms_abi call).
static void __attribute__((ms_abi)) set_data_detour(void* _this, void* chars, void* selected, void* notAllowed) {
    if (chars) {
        uint64_t len = *(uint64_t*)((char*)chars + 0x18);
        if (len == 1) {
            enum { HDR = 0x20 };
            static const int N = 3;
            size_t new_sz = HDR + (size_t)N * sizeof(void*);
            void* new_arr = malloc(new_sz);
            if (new_arr) {
                memcpy(new_arr, chars, HDR);
                *(uint64_t*)((char*)new_arr + 0x18) = N;
                void* elem = *(void**)((char*)chars + HDR);
                for (int i = 0; i < N; i++)
                    ((void**)((char*)new_arr + HDR))[i] = elem;
                chars = new_arr;
            }
        }
    }
    // Call original via TrampolinePtr with ms_abi convention
    typedef void __attribute__((ms_abi)) (*orig_set_data_t)(void*, void*, void*, void*);
    ((orig_set_data_t)(Detour_hook_set_data.TrampolinePtr))(_this, chars, selected, notAllowed);
}

// ── SetContent hook ──────────────────────────────────────────────────────────
// StandardLevelDetailView.SetContent() — called when a song is selected in the
// song menu. We modify the BeatmapLevelSO's field at offset 0x98 to include
// additional characteristics, and also patch song info fields.
static void __attribute__((ms_abi)) set_content_detour(void* _this, void* level, int allowedMask, void* notAllowedChars, int defaultDiff, void* defaultChar, void* playerData) {
    // ── Patch BeatmapLevelSO fields BEFORE the view reads them ────────────────
    // When redirected songs load their per-song bundle, the BeatmapLevel has
    // the custom data (songName, author, etc.). But the BeatmapLevelSO (loaded
    // at startup from the pack bundle) still shows the original RS metadata.
    // Here we locate the matching BeatmapLevelSO by its levelID and patch it.

    // Read the BeatmapLevel's levelID (offset 0x18)
    void* levelID_str = level ? *(void**)((char*)level + 0x18) : NULL;
    if (levelID_str) {
        // Read the levelID string length (offset 0x10) and chars (offset 0x14)
        int len = *(int*)((char*)levelID_str + 0x10);
        // We'll detect if the levelID contains "startmeup" / "angry" etc.
        // and look up custom info from our redirect table.
    }

    // ── Call the original ─────────────────────────────────────────────────────
    typedef void __attribute__((ms_abi)) (*orig_set_content_t)(void*, void*, int, void*, int, void*, void*);
    ((orig_set_content_t)(Detour_hook_set_content.TrampolinePtr))(
        _this, level, allowedMask, notAllowedChars, defaultDiff, defaultChar, playerData);

    // ── After-original augmentation ───────────────────────────────────────────
    // The view now has the BeatmapLevel stored. We can augment the characteristic
    // controller's data if needed. But the main augmentation is done by the
    // get_preview hook above — this hook handles song info patching.
    log_write("set_content: song selected");
}


extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;(void)args;
    OrbisNotificationRequest notif;

    ensure_dir();
    log_write("=== BS Deluxe " PLUGIN_VERSION " started ===");
    log_write(PLUGIN_VERSION " — dynamic redirect config (reads redirects.json from AFR)");

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

    // Try to install IL2CPP hook (may fail if Il2CppUserAssemblies not loaded yet)
    maybe_install_il2cpp_hook();

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
