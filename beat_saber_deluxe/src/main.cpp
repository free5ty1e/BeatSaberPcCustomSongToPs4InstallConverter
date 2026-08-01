// Beat Saber Deluxe — dynamic redirect plugin
// Reads song redirect table from /data/GoldHEN/AFR/<TITLE_ID>/redirects.json
// Feature flags from /data/GoldHEN/AFR/<TITLE_ID>/features.json
// Song metadata from /data/GoldHEN/AFR/<TITLE_ID>/song_metadata.json
// All redirects and metadata come from external config files — no hardcoded fallback.
// v0.8036: External song_metadata.json — replaces hardcoded replacement table.
// v0.8026: TMP_Text.set_text hook — intercepts song name/artist text in UI.
// v0.8025: Removed memory injection code (v0.66–v0.8024 abandoned as dead end).

#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <dlfcn.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.8046"
#define AFR_BASE  "/data/GoldHEN/AFR"
#define TITLE_ID "CUSA12878"
#define LOG_PATH AFR_BASE "/" TITLE_ID "/bs_log.txt"
#define CONFIG_PATH AFR_BASE "/" TITLE_ID "/redirects.json"
#define FEATURES_PATH AFR_BASE "/" TITLE_ID "/features.json"
#define MAX_REDIRECTS 256
#define MAX_PATH 256
#define METADATA_PATH AFR_BASE "/" TITLE_ID "/song_metadata.json"
#define METADATA_MAX 128

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
static int g_feature_beatmap_mode_mapping = 0;

// ── Song metadata replacement table ──────────────────────────────────────────
// Loaded from /data/GoldHEN/AFR/CUSA12878/song_metadata.json
static char *METADATA_NAME_KEYS[METADATA_MAX];
static char *METADATA_NAME_VALS[METADATA_MAX];
static int METADATA_NAME_COUNT = 0;
static char *METADATA_ARTIST_KEYS[METADATA_MAX];
static char *METADATA_ARTIST_VALS[METADATA_MAX];
static int METADATA_ARTIST_COUNT = 0;

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
        } else if (strcmp(key, "enable_beatmap_mode_mapping") == 0) {
            g_feature_beatmap_mode_mapping = val;
        }
    }

    char logmsg[256];
    snprintf(logmsg, sizeof(logmsg), "features: custom_song_replacements=%d metadata_modification=%d beatmap_mode_mapping=%d",
             g_feature_custom_song_replacements, g_feature_song_metadata_modification,
             g_feature_beatmap_mode_mapping);
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
HOOK_INIT(hook_tmp_text_set_text2);
HOOK_INIT(hook_move_next);
static int g_tmp_text_set_text_count = 0;

// ── Phase 2: Beatmap Mode Preview Data Memory Injection ──────────────────────
// Patches BeatmapLevelSO._previewDifficultyBeatmapSets at runtime to add
// OneSaber, NoArrows, 90Degree, 360Degree mode entries. Triggered once from
// MoveNext hook when first custom song's song cell renders (pack bundle loaded).
// Memory reads use sceKernelQueryMemoryProtection — NO signal handlers. The
// v0.8043/44 crash was caused by process-wide SIGSEGV/SIGBUS handlers
// hijacking Unity's own GC page-protection faults during song-list rendering.
// ---------------------------------------------------------------------------
// BeatmapLevelSO field offsets (from il2cpp dump.cs TypeDefIndex 11680):
//   0x18: _version (int32_t)
//   0x20: _levelID (string*)
//   0x98: _previewDifficultyBeatmapSets (PreviewDifficultyBeatmapSet[]*)
// PreviewDifficultyBeatmapSet field offsets (TypeDefIndex 11677):
//   0x10: _beatmapCharacteristic (BeatmapCharacteristicSO*)
//   0x18: _previewDifficultyBeatmaps (PreviewDifficultyBeatmap[]*)
// BeatmapCharacteristicSO field offsets (TypeDefIndex 11575):
//   0x30: _serializedName (string*)
// PreviewDifficultyBeatmap struct: 9 x int32 fields = 36 bytes
// Il2CppSZArray header: 0x00 klass(8) 0x08 monitor(8) 0x10 bounds(8) 0x18 max_length(8) 0x20 data[]
// ---------------------------------------------------------------------------
#define MODE_SCAN_LOW_START  0x1000000ULL    // 16MB
#define MODE_SCAN_LOW_END    0x1000000000ULL  // 64GB — v0.77-proven coverage
#define MODE_SCAN_HIGH_START 0x200000000ULL   // 8GB
#define MODE_SCAN_HIGH_END   0x210000000ULL   // 8.25GB
#define MODE_SCAN_STEP       0x10000ULL       // 64KB pages (high range + hole stepping)
#define MODE_SCAN_PAGE       0x100000ULL      // 1MB page reads (low range, v0.77 pattern)
#define MODE_SCAN_STRIDE     32               // 32-byte stride within page
static uint8_t g_mode_scan_page[MODE_SCAN_PAGE];  // static — 1MB stack buffer crashes (v0.78)
#define BLS_OFFSET_VERSION   0x18
#define BLS_OFFSET_LEVEL_ID  0x20
#define BLS_OFFSET_PREVIEW   0x98
#define PDS_OFFSET_CHAR      0x10
#define PDS_OFFSET_DIFFS     0x18
#define BCS_OFFSET_SER_NAME  0x30
#define ARR_OFFSET_LENGTH    0x18
#define ARR_OFFSET_DATA      0x20
#define PREVIEW_DIFF_SIZE    36

static int g_mode_preview_done = 0;
static int g_qmp_ok = 0;  // 1 once sceKernelQueryMemoryProtection is verified working

// Safe memory read using sceKernelQueryMemoryProtection — a real libkernel
// syscall that reports the mapped range and protection of an address WITHOUT
// triggering a fault. This eliminates the SIGSEGV/SIGBUS handler approach
// entirely (which crashed the game because Unity's GC uses page-protection
// faults on concurrent threads during song-list rendering).
static int mode_try_read(uint64_t addr, void* buf, size_t size) {
    if (size == 0) return 0;
    if (addr < 0x1000000ULL) return 0;
    // Verify the syscall works once — if it's a stub (like mincore/msync),
    // skip the whole scan rather than risk a crash.
    if (!g_qmp_ok) {
        void *rs = NULL, *re = NULL;
        int32_t prot = 0;
        if (sceKernelQueryMemoryProtection((void*)&g_qmp_ok, &rs, &re, &prot) == 0 &&
            (prot & 1) && rs && re && (uint64_t)rs <= (uint64_t)&g_qmp_ok &&
            (uint64_t)re > (uint64_t)&g_qmp_ok) {
            g_qmp_ok = 1;
            char qmp_msg[128];
            snprintf(qmp_msg, sizeof(qmp_msg), "[MODE] sceKernelQueryMemoryProtection verified (prot=0x%X)", prot);
            log_write(qmp_msg);
        } else {
            log_write("[MODE] sceKernelQueryMemoryProtection is a stub — mode scan disabled");
            return 0;
        }
    }
    void *r_start = NULL, *r_end = NULL;
    int32_t prot = 0;
    if (sceKernelQueryMemoryProtection((void*)addr, &r_start, &r_end, &prot) != 0) return 0;
    if (!(prot & 1)) return 0;  // not CPU-readable
    if (!r_start || !r_end) return 0;
    if ((uint64_t)r_end - (uint64_t)r_start < size) return 0;
    if (addr + size > (uint64_t)r_end) return 0;
    memcpy(buf, (void*)addr, size);
    return 1;
}

static int mode_extract_string(void* str_obj, char* out, int out_size) {
    if (!str_obj || (uint64_t)str_obj < 0x1000000ULL) { out[0] = '\0'; return 0; }
    int result = 0;
    int len_10 = 0, len_14 = 0;
    if (!mode_try_read((uint64_t)str_obj + 0x10, &len_10, 4)) { out[0] = '\0'; return 0; }
    if (!mode_try_read((uint64_t)str_obj + 0x14, &len_14, 4)) { out[0] = '\0'; return 0; }
    // System.String layout on PS4: length at 0x10 OR 0x14, chars right after.
    // len_14 is the first two UTF-16 chars combined — usually a huge number,
    // so it must only be used when len_10 is implausible. (v0.8046 fix: the
    // old `len_14 == 0 ? len_10 : len_14` always picked garbage len_14.)
    int len = 0;
    uint64_t chars_addr = 0;
    if (len_10 > 0 && len_10 < 256 && (len_14 == 0 || len_14 >= 256)) {
        len = len_10;
        chars_addr = (uint64_t)str_obj + 0x14;
    } else if (len_14 > 0 && len_14 < 256) {
        len = len_14;
        chars_addr = (uint64_t)str_obj + 0x18;
    } else {
        len = len_10;
        chars_addr = (uint64_t)str_obj + 0x14;
    }
    if (len > 0 && len < out_size) {
        uint16_t chars[256];
        if (mode_try_read(chars_addr, chars, (size_t)len * 2)) {
            for (int i = 0; i < len; i++) out[i] = (chars[i] < 128) ? (char)chars[i] : '?';
            out[len] = '\0';
            result = len;
        }
    }
    if (result == 0) out[0] = '\0';
    return result;
}

// Validate that addr points to a BeatmapLevelSO by checking the
// _previewDifficultyBeatmapSets array structure at BLS_OFFSET_PREVIEW:
// array klass in range, length 1-10, first element with valid
// characteristic + difficulty-list pointers.
static int mode_preview_arr_ok(uint64_t bsl_addr) {
    uint64_t arr = 0;
    if (!mode_try_read(bsl_addr + BLS_OFFSET_PREVIEW, &arr, 8)) return 0;
    if (arr < 0x1000000ULL) return 0;
    uint64_t arr_klass = 0;
    if (!mode_try_read(arr, &arr_klass, 8)) return 0;
    if ((arr_klass < 0x80000000ULL || arr_klass > 0x90000000ULL) &&
        (arr_klass < 0x200000000ULL || arr_klass > 0x210000000ULL)) return 0;
    uint64_t len = 0;
    if (!mode_try_read(arr + ARR_OFFSET_LENGTH, &len, 8)) return 0;
    if (len < 1 || len > 10) return 0;
    uint64_t first = 0;
    if (!mode_try_read(arr + ARR_OFFSET_DATA, &first, 8)) return 0;
    if (first < 0x1000000ULL) return 0;
    uint64_t set_klass = 0;
    if (!mode_try_read(first, &set_klass, 8)) return 0;
    if ((set_klass < 0x80000000ULL || set_klass > 0x90000000ULL) &&
        (set_klass < 0x200000000ULL || set_klass > 0x210000000ULL)) return 0;
    uint64_t ch = 0;
    if (!mode_try_read(first + PDS_OFFSET_CHAR, &ch, 8)) return 0;
    if (ch < 0x1000000ULL) return 0;
    uint64_t diffs = 0;
    if (!mode_try_read(first + PDS_OFFSET_DIFFS, &diffs, 8)) return 0;
    if (diffs < 0x1000000ULL) return 0;
    return 1;
}

// Find the BeatmapLevelSO klass by scanning for the first object matching
// the structural signature (klass in valid range + version 1-50 + valid
// _levelID/_songName/_songAuthorName string pointers + valid preview array).
// All BeatmapLevelSO objects share the same klass, so the first match suffices.
// Returns the klass address or 0.
//
// Scan design (v0.8046):
//   - Low range 16MB-64GB at 1MB page reads (v0.77-proven: found 17 candidates).
//   - High range 8-8.25GB at 64KB page reads (dense GC-heap supplement).
//   - When a page read fails (hole/partial mapping), jump to the next mapping
//     boundary via sceKernelQueryMemoryProtection instead of stepping every page.
//   - Diagnostic counters log exactly which structural check rejects candidates.
static uint64_t mode_find_beatmap_level_so_klass(void) {
    uint64_t result_klass = 0;
    char logbuf[256];
    int diag_ok = 0, diag_klass = 0, diag_ver = 0, diag_ptrs = 0, diag_arrfail = 0, diag_strfail = 0;
    int cand_logged = 0;
    for (int r = 0; r < 2 && result_klass == 0; r++) {
        uint64_t start = (r == 0) ? MODE_SCAN_LOW_START : MODE_SCAN_HIGH_START;
        uint64_t end   = (r == 0) ? MODE_SCAN_LOW_END   : MODE_SCAN_HIGH_END;
        uint64_t page_step = (r == 0) ? MODE_SCAN_PAGE : MODE_SCAN_STEP;
        for (uint64_t page_addr = start; page_addr < end && result_klass == 0;) {
            if (!mode_try_read(page_addr, g_mode_scan_page, page_step)) {
                // Skip past whatever mapping made this read fail (hole/partial).
                void *rs = NULL, *re = NULL;
                int32_t prot = 0;
                if (sceKernelQueryMemoryProtection((void*)page_addr, &rs, &re, &prot) == 0 && re) {
                    uint64_t next = (uint64_t)re;
                    page_addr = (next > page_addr) ? next : page_addr + page_step;
                } else {
                    page_addr += page_step;
                }
                continue;
            }
            diag_ok++;
            for (uint64_t off = 0; off + 64 < page_step && result_klass == 0; off += MODE_SCAN_STRIDE) {
                uint64_t k = *(uint64_t*)(g_mode_scan_page + off);
                if ((k < 0x80000000ULL || k > 0x90000000ULL) &&
                    (k < 0x200000000ULL || k > 0x210000000ULL)) continue;
                diag_klass++;
                int ver = *(int*)(g_mode_scan_page + off + BLS_OFFSET_VERSION);
                if (ver < 1 || ver > 50) continue;
                diag_ver++;
                uint64_t lid = *(uint64_t*)(g_mode_scan_page + off + BLS_OFFSET_LEVEL_ID);
                uint64_t sn  = *(uint64_t*)(g_mode_scan_page + off + 0x28);
                uint64_t an  = *(uint64_t*)(g_mode_scan_page + off + 0x38);
                if (lid < 0x1000000ULL || sn < 0x1000000ULL || an < 0x1000000ULL) continue;
                diag_ptrs++;
                if (cand_logged < 12) {
                    snprintf(logbuf, sizeof(logbuf), "[MODE]   cand klass=0x%lX @0x%lX ver=%d lid=0x%lX", k, page_addr + off, ver, lid);
                    log_write(logbuf);
                    cand_logged++;
                }
                if (!mode_preview_arr_ok(page_addr + off)) { diag_arrfail++; continue; }
                char lid_buf[128];
                if (!mode_extract_string((void*)lid, lid_buf, sizeof(lid_buf)) || lid_buf[0] == '\0') { diag_strfail++; continue; }
                snprintf(logbuf, sizeof(logbuf), "[MODE] BeatmapLevelSO klass=0x%lX (first via '%s' @0x%lX)", k, lid_buf, page_addr + off);
                log_write(logbuf);
                result_klass = k;
            }
            page_addr += page_step;
        }
    }
    if (!result_klass) {
        snprintf(logbuf, sizeof(logbuf), "[MODE] Scan diag: ok=%d klass=%d ver=%d ptrs=%d arrfail=%d strfail=%d",
                 diag_ok, diag_klass, diag_ver, diag_ptrs, diag_arrfail, diag_strfail);
        log_write(logbuf);
        log_write("[MODE] BeatmapLevelSO klass not found -- game may not have loaded pack yet");
    }
    return result_klass;
}

// Collect all BeatmapLevelSO objects matching a known klass address.
static int mode_collect_beatmap_level_sos(
    uint64_t klass,
    uint64_t* out_addrs, char out_ids[][128], int max_count)
{
    int count = 0;
    char logbuf[256];
    for (int r = 0; r < 2 && count < max_count; r++) {
        uint64_t start = (r == 0) ? MODE_SCAN_LOW_START : MODE_SCAN_HIGH_START;
        uint64_t end   = (r == 0) ? MODE_SCAN_LOW_END   : MODE_SCAN_HIGH_END;
        uint64_t page_step = (r == 0) ? MODE_SCAN_PAGE : MODE_SCAN_STEP;
        for (uint64_t page_addr = start; page_addr < end && count < max_count;) {
            if (!mode_try_read(page_addr, g_mode_scan_page, page_step)) {
                void *rs = NULL, *re = NULL;
                int32_t prot = 0;
                if (sceKernelQueryMemoryProtection((void*)page_addr, &rs, &re, &prot) == 0 && re) {
                    uint64_t next = (uint64_t)re;
                    page_addr = (next > page_addr) ? next : page_addr + page_step;
                } else {
                    page_addr += page_step;
                }
                continue;
            }
            for (uint64_t off = 0; off + 64 < page_step && count < max_count; off += MODE_SCAN_STRIDE) {
                uint64_t k = *(uint64_t*)(g_mode_scan_page + off);
                if (k != klass) continue;
                uint64_t lid = *(uint64_t*)(g_mode_scan_page + off + BLS_OFFSET_LEVEL_ID);
                if (lid < 0x1000000ULL) continue;
                int ver = *(int*)(g_mode_scan_page + off + BLS_OFFSET_VERSION);
                if (ver < 1 || ver > 50) continue;
                uint64_t sn = *(uint64_t*)(g_mode_scan_page + off + 0x28);
                uint64_t an = *(uint64_t*)(g_mode_scan_page + off + 0x38);
                if (sn < 0x1000000ULL || an < 0x1000000ULL) continue;
                if (!mode_preview_arr_ok(page_addr + off)) continue;
                char lid_buf[128];
                if (!mode_extract_string((void*)lid, lid_buf, sizeof(lid_buf))) continue;
                if (lid_buf[0] == '\0') continue;
                out_addrs[count] = page_addr + off;
                strncpy(out_ids[count], lid_buf, 127);
                out_ids[count][127] = '\0';
                count++;
            }
            page_addr += page_step;
        }
    }
    return count;
}

// Find all 5 BeatmapCharacteristicSO by scanning near a known one for matching klass.
static int mode_find_characteristic_sos(uint64_t standard_charso, uint64_t out[5]) {
    memset(out, 0, 5 * sizeof(uint64_t));
    uint64_t klass = 0;
    if (!mode_try_read(standard_charso, &klass, 8)) return -1;
    out[0] = standard_charso;
    const char* names[4] = {"OneSaber", "NoArrows", "90Degree", "360Degree"};
    uint64_t base = standard_charso;
    // Scan ±16MB around the Standard charSO — all characteristic SOs come from
    // the same shared asset bundle, so they land near each other in the heap.
    uint64_t scan_start = (base > 0x1000000) ? base - 0x1000000 : MODE_SCAN_HIGH_START;
    uint64_t scan_end = base + 0x1000000;
    uint8_t page[MODE_SCAN_STEP];
    for (uint64_t addr = scan_start; addr < scan_end; addr += MODE_SCAN_STEP) {
        if (!mode_try_read(addr, page, MODE_SCAN_STEP)) continue;
        for (uint64_t off = 0; off < MODE_SCAN_STEP - 64; off += 8) {
            if (addr + off == base) continue;
            uint64_t k = *(uint64_t*)(page + off);
            if (k != klass) continue;
            uint64_t sn_ptr = 0;
            if (off + BCS_OFFSET_SER_NAME + 8 <= MODE_SCAN_STEP) {
                sn_ptr = *(uint64_t*)(page + off + BCS_OFFSET_SER_NAME);
            } else {
                mode_try_read(addr + off + BCS_OFFSET_SER_NAME, &sn_ptr, 8);
            }
            if (sn_ptr < 0x1000000ULL) continue;
            char name[64];
            if (!mode_extract_string((void*)sn_ptr, name, sizeof(name))) continue;
            for (int i = 0; i < 4; i++) {
                if (out[i+1] == 0 && strcmp(name, names[i]) == 0) {
                    out[i+1] = addr + off;
                    break;
                }
            }
            int all = 1;
            for (int i = 0; i < 5; i++) if (out[i] == 0) { all = 0; break; }
            if (all) return 5;
        }
    }
    int found = 0;
    for (int i = 0; i < 5; i++) if (out[i]) found++;
    return found;
}

// Patch one BeatmapLevelSO to have 5 mode preview sets.
static int mode_patch_one_bsl(uint64_t bsl_addr, const char* level_id, uint64_t char_sos[5]) {
    char logbuf[256];
    uint64_t existing_arr = 0;
    if (!mode_try_read(bsl_addr + BLS_OFFSET_PREVIEW, &existing_arr, 8)) return -1;
    if (existing_arr < 0x1000000ULL) return -1;
    uint64_t first_set_ptr = 0;
    if (!mode_try_read(existing_arr + ARR_OFFSET_DATA, &first_set_ptr, 8)) return -1;
    if (first_set_ptr < 0x1000000ULL) return -1;
    uint64_t standard_diffs = 0;
    mode_try_read(first_set_ptr + PDS_OFFSET_DIFFS, &standard_diffs, 8);
    if (standard_diffs < 0x1000000ULL) return -1;
    uint64_t diff_count = 0;
    mode_try_read(standard_diffs + ARR_OFFSET_LENGTH, &diff_count, 8);
    if (diff_count == 0 || diff_count > 10) return -1;
    uint64_t set_klass = 0, arr_klass = 0;
    mode_try_read(first_set_ptr, &set_klass, 8);
    mode_try_read(existing_arr, &arr_klass, 8);
    // Build 5 PreviewDifficultyBeatmapSet objects
    size_t set_size = 0x20;
    uint8_t* sets = (uint8_t*)malloc(5 * set_size);
    if (!sets) return -1;
    memset(sets, 0, 5 * set_size);
    for (int i = 0; i < 5; i++) {
        uint8_t* s = sets + i * set_size;
        *(uint64_t*)(s + 0x00) = set_klass;
        *(uint64_t*)(s + PDS_OFFSET_CHAR) = char_sos[i];
        size_t diff_arr_size = ARR_OFFSET_DATA + diff_count * PREVIEW_DIFF_SIZE;
        uint8_t* da = (uint8_t*)malloc(diff_arr_size);
        if (!da) continue;
        mode_try_read(standard_diffs, da, diff_arr_size);
        *(uint64_t*)(s + PDS_OFFSET_DIFFS) = (uint64_t)da;
    }
    // Build new Il2CppSZArray (5 element pointers)
    size_t arr_size = ARR_OFFSET_DATA + 5 * 8;
    uint8_t* new_arr = (uint8_t*)malloc(arr_size);
    if (!new_arr) { free(sets); return -1; }
    memset(new_arr, 0, arr_size);
    *(uint64_t*)(new_arr + 0x00) = arr_klass;
    *(uint64_t*)(new_arr + ARR_OFFSET_LENGTH) = 5;
    for (int i = 0; i < 5; i++)
        *(uint64_t*)(new_arr + ARR_OFFSET_DATA + i * 8) = (uint64_t)(sets + i * set_size);
    // Atomic replace
    *(uint64_t*)(bsl_addr + BLS_OFFSET_PREVIEW) = (uint64_t)new_arr;
    snprintf(logbuf, sizeof(logbuf), "[MODE] Patched '%s': added 5 preview sets", level_id);
    log_write(logbuf);
    return 5;
}

// Main orchestrator: find klass, collect BSL objects, find charSOs, patch all.
// Runs synchronously on the game thread. All reads go through mode_try_read
// (sceKernelQueryMemoryProtection) so NO signal handlers are installed — the
// v0.8043/44 crash was caused by process-wide SIGSEGV/SIGBUS handlers hijacking
// Unity's GC page-protection faults during song-list rendering.
static void mode_patch_all(void) {
    char logbuf[256];
    log_write("[MODE] Starting BeatmapLevelSO memory scan...");
    uint64_t klass = mode_find_beatmap_level_so_klass();
    if (!klass) {
        log_write("[MODE] BeatmapLevelSO klass not found -- game may not have loaded pack yet");
        g_mode_preview_done = -1;
        return;
    }
    snprintf(logbuf, sizeof(logbuf), "[MODE] BeatmapLevelSO klass=0x%lX", klass);
    log_write(logbuf);
    // Collect all BeatmapLevelSO objects
    enum { MAX_BSL = 64 };
    uint64_t bsl_addrs[MAX_BSL];
    char bsl_level_ids[MAX_BSL][128];
    int bsl_count = mode_collect_beatmap_level_sos(klass, bsl_addrs, bsl_level_ids, MAX_BSL);
    snprintf(logbuf, sizeof(logbuf), "[MODE] Found %d BeatmapLevelSO objects", bsl_count);
    log_write(logbuf);
    if (bsl_count == 0) { g_mode_preview_done = -1; return; }
    // Log every found levelID for diagnostics
    for (int i = 0; i < bsl_count; i++) {
        snprintf(logbuf, sizeof(logbuf), "[MODE]   BSL[%d] levelID='%s' @0x%lX", i, bsl_level_ids[i], bsl_addrs[i]);
        log_write(logbuf);
    }
    // Find BeatmapCharacteristicSO objects from last BeatmapLevelSO's Standard entry
    uint64_t char_sos[5] = {0};
    for (int i = bsl_count - 1; i >= 0 && char_sos[4] == 0; i--) {
        uint64_t existing_arr = 0;
        if (!mode_try_read(bsl_addrs[i] + BLS_OFFSET_PREVIEW, &existing_arr, 8)) continue;
        if (existing_arr < 0x1000000ULL) continue;
        uint64_t first_set_ptr = 0;
        if (!mode_try_read(existing_arr + ARR_OFFSET_DATA, &first_set_ptr, 8)) continue;
        if (first_set_ptr < 0x1000000ULL) continue;
        uint64_t standard_charso = 0;
        if (!mode_try_read(first_set_ptr + PDS_OFFSET_CHAR, &standard_charso, 8)) continue;
        if (standard_charso < 0x1000000ULL) continue;
        if (mode_find_characteristic_sos(standard_charso, char_sos) >= 5) {
            snprintf(logbuf, sizeof(logbuf), "[MODE] Found 5 BeatmapCharacteristicSO via '%s'", bsl_level_ids[i]);
            log_write(logbuf);
            break;
        }
    }
    if (char_sos[0] == 0) {
        log_write("[MODE] Failed to find BeatmapCharacteristicSO objects");
        g_mode_preview_done = -1;
        return;
    }
    // Patch ALL BeatmapLevelSO objects (every pack on this PS4 is fully custom)
    int patched = 0;
    for (int i = 0; i < bsl_count; i++) {
        if (mode_patch_one_bsl(bsl_addrs[i], bsl_level_ids[i], char_sos) > 0) patched++;
    }
    snprintf(logbuf, sizeof(logbuf), "[MODE] Patch complete: %d BeatmapLevelSO objects updated", patched);
    log_write(logbuf);
    g_mode_preview_done = 1;
}

// Called from MoveNext hook when a song BeatmapLevel is first detected.
// Triggers the one-time synchronous scan that patches BeatmapLevelSO
// _previewDifficultyBeatmapSets (pack bundle UI data). Runs on the game
// thread; the game pauses briefly. Uses signal-free reads (v0.8045+).
static void mode_try_patch_from_move_next(void* beatmapLevel) {
    if (g_mode_preview_done) return;
    if (!g_feature_beatmap_mode_mapping) return;
    if (!beatmapLevel) return;
    log_write("[MODE] Triggered from MoveNext -- running synchronous scan");
    mode_patch_all();
}

// Forward-declare IL2CPP's MethodInfo (opaque type)
struct MethodInfo;

// ── Load song metadata from JSON config file ────────────────────────────────
// Parses "song_names" and "song_artists" sections from song_metadata.json
// Uses same parse_json_pairs() as redirects loading.
static void load_song_metadata(void) {
    int fd = open(METADATA_PATH, O_RDONLY, 0);
    if (fd < 0) fd = sceKernelOpen(METADATA_PATH, O_RDONLY, 0);
    if (fd < 0) {
        log_write("song_metadata.json not found — no metadata replacements active");
        return;
    }

    char buf[16384];
    ssize_t got = read(fd, buf, sizeof(buf) - 1);
    close(fd);
    if (got <= 0) {
        log_write("song_metadata.json is empty");
        return;
    }
    buf[got] = '\0';

    // Parse "song_names" section
    char *sn = strstr(buf, "\"song_names\"");
    if (sn) {
        sn += 12;
        while (*sn && (*sn == ' ' || *sn == '\t' || *sn == '\n' || *sn == '\r' || *sn == ':' || *sn == '"')) sn++;
        if (*sn == '{') {
            char keys[METADATA_MAX][MAX_PATH];
            char vals[METADATA_MAX][MAX_PATH];
            int n = parse_json_pairs(sn, METADATA_MAX, keys, vals);
            for (int i = 0; i < n && i < METADATA_MAX; i++) {
                METADATA_NAME_KEYS[i] = (char*)malloc(strlen(keys[i]) + 1);
                METADATA_NAME_VALS[i] = (char*)malloc(strlen(vals[i]) + 1);
                if (METADATA_NAME_KEYS[i] && METADATA_NAME_VALS[i]) {
                    strcpy(METADATA_NAME_KEYS[i], keys[i]);
                    strcpy(METADATA_NAME_VALS[i], vals[i]);
                    METADATA_NAME_COUNT++;
                }
            }
        }
    }

    // Parse "song_artists" section
    char *sa = strstr(buf, "\"song_artists\"");
    if (sa) {
        sa += 14;
        while (*sa && (*sa == ' ' || *sa == '\t' || *sa == '\n' || *sa == '\r' || *sa == ':' || *sa == '"')) sa++;
        if (*sa == '{') {
            char keys[METADATA_MAX][MAX_PATH];
            char vals[METADATA_MAX][MAX_PATH];
            int n = parse_json_pairs(sa, METADATA_MAX, keys, vals);
            for (int i = 0; i < n && i < METADATA_MAX; i++) {
                METADATA_ARTIST_KEYS[i] = (char*)malloc(strlen(keys[i]) + 1);
                METADATA_ARTIST_VALS[i] = (char*)malloc(strlen(vals[i]) + 1);
                if (METADATA_ARTIST_KEYS[i] && METADATA_ARTIST_VALS[i]) {
                    strcpy(METADATA_ARTIST_KEYS[i], keys[i]);
                    strcpy(METADATA_ARTIST_VALS[i], vals[i]);
                    METADATA_ARTIST_COUNT++;
                }
            }
        }
    }

    char logmsg[256];
    snprintf(logmsg, sizeof(logmsg), "loaded song_metadata: %d name replacements, %d artist replacements",
             METADATA_NAME_COUNT, METADATA_ARTIST_COUNT);
    log_write(logmsg);
}

static void free_metadata(void) {
    for (int i = 0; i < METADATA_NAME_COUNT; i++) {
        free(METADATA_NAME_KEYS[i]);
        free(METADATA_NAME_VALS[i]);
    }
    for (int i = 0; i < METADATA_ARTIST_COUNT; i++) {
        free(METADATA_ARTIST_KEYS[i]);
        free(METADATA_ARTIST_VALS[i]);
    }
    METADATA_NAME_COUNT = 0;
    METADATA_ARTIST_COUNT = 0;
}

static const char* find_metadata_replacement(const char* text) {
    if (!text) return NULL;
    // Trim trailing spaces for robustness (game data sometimes has trailing spaces)
    int len = strlen(text);
    while (len > 0 && text[len - 1] == ' ') len--;
    // Search song names first
    for (int i = 0; i < METADATA_NAME_COUNT; i++) {
        int klen = strlen(METADATA_NAME_KEYS[i]);
        if (klen == len && memcmp(text, METADATA_NAME_KEYS[i], len) == 0) {
            return METADATA_NAME_VALS[i];
        }
    }
    // Then search song artists
    for (int i = 0; i < METADATA_ARTIST_COUNT; i++) {
        int klen = strlen(METADATA_ARTIST_KEYS[i]);
        if (klen == len && memcmp(text, METADATA_ARTIST_KEYS[i], len) == 0) {
            return METADATA_ARTIST_VALS[i];
        }
    }
    return NULL;
}

// UTF-16LE string extraction from IL2CPP System.String
// System.String layout: klass(8) + monitor(8) + _stringLength(4) + first_char(UTF-16LE)
// _stringLength may be at offset 0x10 or 0x14 on PS4 — try both
// Reads go through mode_try_read (sceKernelQueryMemoryProtection) — signal-free.

static int extract_utf16_string(void* str_obj, char* out, int out_size) {
    if (!str_obj) { out[0] = '\0'; return 0; }

    // Basic sanity check — reject clearly invalid pointers
    if ((uint64_t)str_obj < 0x1000000ULL) { out[0] = '\0'; return 0; }

    int result = 0;
    uint32_t len_10 = 0, len_14 = 0;
    if (!mode_try_read((uint64_t)str_obj + 0x10, &len_10, 4)) { out[0] = '\0'; return 0; }
    if (!mode_try_read((uint64_t)str_obj + 0x14, &len_14, 4)) { out[0] = '\0'; return 0; }

    uint32_t len = 0;
    uint64_t chars_addr = 0;

    if (len_10 > 0 && len_10 < 256 && len_14 == 0) {
        len = len_10;
        chars_addr = (uint64_t)str_obj + 0x14;
    } else if (len_14 > 0 && len_14 < 256) {
        len = len_14;
        chars_addr = (uint64_t)str_obj + 0x18;
    } else {
        len = len_10;
        chars_addr = (uint64_t)str_obj + 0x14;
    }

    if (len > 0 && len < (uint32_t)out_size) {
        uint16_t chars[256];
        if (mode_try_read(chars_addr, chars, (size_t)len * 2)) {
            int i;
            for (i = 0; i < (int)len && i < out_size - 1; i++) {
                out[i] = (chars[i] < 128) ? (char)chars[i] : '?';
            }
            out[i] = '\0';
            result = len;
        }
    }
    if (result == 0) out[0] = '\0';
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

// Shared replacement logic for both set_text and SetText hooks
static void* apply_metadata_replacement(void* this_ptr, void* value) {
    if (!g_feature_song_metadata_modification || !value) return value;

    char text_buf[256] = {0};
    int len = extract_utf16_string(value, text_buf, sizeof(text_buf));

    if (len > 0) {
        const char* replacement = find_metadata_replacement(text_buf);
        if (replacement) {
            g_tmp_text_set_text_count++;

            char logmsg[512];
            snprintf(logmsg, sizeof(logmsg), "[METADATA] REPLACE #%d: this=%p '%s' -> '%s'",
                     g_tmp_text_set_text_count, this_ptr, text_buf, replacement);
            log_write(logmsg);

            void* replacement_str = try_il2cpp_string_new(replacement);
            if (!replacement_str) {
                replacement_str = create_il2cpp_string(value, replacement);
            }
            if (replacement_str) {
                return replacement_str;
            }
        }
    }
    return value;
}

static void tmp_text_set_text_hook(void* this_ptr, void* value, const MethodInfo* method) {
    void* new_value = apply_metadata_replacement(this_ptr, value);

    HOOK_CONTINUE(hook_tmp_text_set_text, void (*)(void*, void*, const MethodInfo*),
                  this_ptr, new_value, method);
}

// TMP_Text.SetText(string, bool) — used by song list for song name text
// RVA: 0x2D3E1D0 (non-virtual method)
// Calling convention: SysV AMD64 (this in RDI, value in RSI, syncInput in EDX, method in RCX)
static void tmp_text_set_text2_hook(void* this_ptr, void* value, int sync_input, const MethodInfo* method) {
    void* new_value = apply_metadata_replacement(this_ptr, value);

    HOOK_CONTINUE(hook_tmp_text_set_text2, void (*)(void*, void*, int, const MethodInfo*),
                  this_ptr, new_value, sync_input, method);
}

// ── LevelListTableCell.SetDataFromLevelAsync/d__21.MoveNext hook ─────────────
// Hooks MoveNext() of the async state machine that populates song list cells.
// The async wrapper (SetDataFromLevelAsync at 0x1D36940) is a trampoline that
// gets inlined by AsyncVoidMethodBuilder.Start<T>() — our hook never fires.
// MoveNext() at 0x1D377C0 is where the actual work happens: it reads
// BeatmapLevel.songName/songAuthorName and assigns to TMP_Text fields.
// Modifies BeatmapLevel fields IN-PLACE before the original runs, so the UI
// reads our replacement from the data source directly.
// State machine layout: <>4__this@0x28, beatmapLevel@0x30
// RVA: 0x1D377C0 (private void MoveNext())
static int g_move_next_hook_count = 0;
static void move_next_hook(void* state_machine) {
    if (g_feature_song_metadata_modification && state_machine) {
        void* beatmapLevel = *(void**)((char*)state_machine + 0x30);
        if (beatmapLevel) {
            // Modify songName at BeatmapLevel + 0x20
            void* songNamePtr = *(void**)((char*)beatmapLevel + 0x20);
            if (songNamePtr) {
                char buf[256] = {0};
                int len = extract_utf16_string(songNamePtr, buf, sizeof(buf));
                if (len > 0) {
                    const char* replacement = find_metadata_replacement(buf);
                    if (replacement) {
                        void* newStr = try_il2cpp_string_new(replacement);
                        if (!newStr) newStr = create_il2cpp_string(songNamePtr, replacement);
                        if (newStr) {
                            *(void**)((char*)beatmapLevel + 0x20) = newStr;
                            g_move_next_hook_count++;
                            char logmsg[512];
                            snprintf(logmsg, sizeof(logmsg), "[METADATA] MoveNext #%d: songName '%s' -> '%s'",
                                     g_move_next_hook_count, buf, replacement);
                            log_write(logmsg);
                        }
                    }
                }
            }
            // Modify songAuthorName at BeatmapLevel + 0x30
            void* authorPtr = *(void**)((char*)beatmapLevel + 0x30);
            if (authorPtr) {
                char buf[256] = {0};
                int len = extract_utf16_string(authorPtr, buf, sizeof(buf));
                if (len > 0) {
                    const char* replacement = find_metadata_replacement(buf);
                    if (replacement) {
                        void* newStr = try_il2cpp_string_new(replacement);
                        if (!newStr) newStr = create_il2cpp_string(authorPtr, replacement);
                        if (newStr) {
                            *(void**)((char*)beatmapLevel + 0x30) = newStr;
                            g_move_next_hook_count++;
                            char logmsg[512];
                            snprintf(logmsg, sizeof(logmsg), "[METADATA] MoveNext #%d: author '%s' -> '%s'",
                                     g_move_next_hook_count, buf, replacement);
                            log_write(logmsg);
                        }
                    }
                }
            }
            // Phase 2 trigger: patch BeatmapLevelSO._previewDifficultyBeatmapSets
            // Runs once when first custom song is detected (pack bundle is loaded)
            mode_try_patch_from_move_next(beatmapLevel);
        }
    }
    HOOK_CONTINUE(hook_move_next, void (*)(void*), state_machine);
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
    uint64_t target2 = il2cpp_base + 0x2D3E1D0;
    uint64_t target3 = il2cpp_base + 0x1D377C0;  // MoveNext, not SetDataFromLevelAsync
    snprintf(logmsg, sizeof(logmsg), "[METADATA] IL2CPP base: 0x%lx, set_text: 0x%lx, SetText: 0x%lx, MoveNext: 0x%lx (attempt %d, open #%d)",
             il2cpp_base, target, target2, target3, g_tmp_hook_attempts, g_open_count);
    log_write(logmsg);

    Detour_Construct(&Detour_hook_tmp_text_set_text, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_tmp_text_set_text, target, (void*)tmp_text_set_text_hook);

    Detour_Construct(&Detour_hook_tmp_text_set_text2, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_tmp_text_set_text2, target2, (void*)tmp_text_set_text2_hook);

    Detour_Construct(&Detour_hook_move_next, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_move_next, target3, (void*)move_next_hook);

    g_tmp_hook_installed = 1;
    log_write("[METADATA] TMP_Text.set_text + SetText + MoveNext hooks installed");
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
    if (g_feature_song_metadata_modification) {
        load_song_metadata();
    }

    // Log feature flag state for debugging
    {
        char flog[256];
        snprintf(flog, sizeof(flog), "FEATURE FLAGS: custom_song_replacements=%s  metadata_modification=%s  beatmap_mode_mapping=%s",
                 g_feature_custom_song_replacements ? "ON" : "OFF",
                 g_feature_song_metadata_modification ? "ON" : "OFF",
                 g_feature_beatmap_mode_mapping ? "ON" : "OFF");
        log_write(flog);
    }

    if (!g_feature_custom_song_replacements) {
        log_write("DISABLED: custom_song_replacements is OFF — redirects will NOT fire");
    }
    if (!g_feature_song_metadata_modification) {
        log_write("DISABLED: song_metadata_modification is OFF — metadata replacements disabled");
    }
    if (!g_feature_beatmap_mode_mapping) {
        log_write("DISABLED: beatmap_mode_mapping is OFF — mode mapping disabled");
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
    free_metadata();
    return 0;
}
