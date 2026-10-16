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
#include <ctype.h>
#include <setjmp.h>
#include <signal.h>
#include <fcntl.h>
#include <unistd.h>
#include <dlfcn.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

#define PLUGIN_VERSION "v0.8050"
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
// EXCEPTION: enable_plugin is the GLOBAL KILL SWITCH and defaults TRUE when
// the key is ABSENT (only an explicit false disables the plugin). This lets a
// bare/missing features.json keep a fully-deployed setup working, while
// `--features-only --set-feature enable_plugin=false` instantly reverts the
// game to 100% stock behavior (no redirects, no metadata swaps) without
// touching plugins.ini or clearing the AFR directory.
static int g_feature_plugin_enabled = 1;
static int g_feature_custom_song_replacements = 0;
static int g_feature_song_metadata_modification = 0;
static int g_feature_beatmap_mode_mapping = 0;
static int g_feature_song_previews = 0;
static int g_feature_in_game_plugin_toggle = 0;  // M11: Move button+trigger hotkey (gates ONLY this feature)

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
static void try_install_pad_hook(void);   // M11 in-game toggle — pad path (defined after the hooks)
static void try_install_move_hook(void);  // M11 in-game toggle — Move path (the primary on this game)

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

        if (strcmp(key, "enable_plugin") == 0) {
            g_feature_plugin_enabled = val;
        } else if (strcmp(key, "enable_custom_song_replacements") == 0) {
            g_feature_custom_song_replacements = val;
        } else if (strcmp(key, "enable_song_metadata_modification") == 0) {
            g_feature_song_metadata_modification = val;
        } else if (strcmp(key, "enable_beatmap_mode_mapping") == 0) {
            g_feature_beatmap_mode_mapping = val;
        } else if (strcmp(key, "enable_song_previews") == 0) {
            g_feature_song_previews = val;
        } else if (strcmp(key, "enable_in_game_plugin_toggle") == 0) {
            g_feature_in_game_plugin_toggle = val;
        }
    }

    char logmsg[256];
    snprintf(logmsg, sizeof(logmsg), "features: plugin=%d custom_song_replacements=%d metadata_modification=%d beatmap_mode_mapping=%d song_previews=%d in_game_plugin_toggle=%d",
             g_feature_plugin_enabled, g_feature_custom_song_replacements, g_feature_song_metadata_modification, g_feature_beatmap_mode_mapping, g_feature_song_previews, g_feature_in_game_plugin_toggle);
    log_write(logmsg);
    if (!g_feature_plugin_enabled) {
        log_write("DISABLED: enable_plugin is false — ALL plugin behavior off (stock game)");
    }
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
// JSON string unescape: converts \uXXXX, \n, \t, \\, \" etc. in place.
// The PS4-deployed song_metadata.json may carry \uXXXX escapes (Python's
// json.dump default ensure_ascii=True writes them for any non-ASCII key).
// Exp 228: '…Baby One More Time' shipped as "…Baby One More Time" and
// the byte-verbatim key parse made the metadata lookup miss forever.
static void json_unescape_inplace(char *s) {
    char *r = s;  // read
    char *w = s;  // write
    while (*r) {
        if (*r != '\\') { *w++ = *r++; continue; }
        r++;
        switch (*r) {
            case 'n': *w++ = '\n'; r++; break;
            case 't': *w++ = '\t'; r++; break;
            case 'r': *w++ = '\r'; r++; break;
            case 'b': *w++ = '\b'; r++; break;
            case 'f': *w++ = '\f'; r++; break;
            case '"': *w++ = '"';  r++; break;
            case '\\': *w++ = '\\'; r++; break;
            case '/': *w++ = '/';  r++; break;
            case 'u': {
                // \uXXXX -> UTF-8 (surrogate pairs not supported; song titles
                // with astral chars are folded to '?' at comparison anyway)
                if (isxdigit((unsigned char)r[1]) && isxdigit((unsigned char)r[2]) &&
                    isxdigit((unsigned char)r[3]) && isxdigit((unsigned char)r[4])) {
                    unsigned cp = 0;
                    for (int i = 1; i <= 4; i++) {
                        char c = r[i];
                        cp <<= 4;
                        if (c >= '0' && c <= '9') cp |= (unsigned)(c - '0');
                        else if (c >= 'a' && c <= 'f') cp |= (unsigned)(c - 'a' + 10);
                        else if (c >= 'A' && c <= 'F') cp |= (unsigned)(c - 'A' + 10);
                    }
                    r += 5;
                    if (cp < 0x80) {
                        *w++ = (char)cp;
                    } else if (cp < 0x800) {
                        *w++ = (char)(0xC0 | (cp >> 6));
                        *w++ = (char)(0x80 | (cp & 0x3F));
                    } else {
                        *w++ = (char)(0xE0 | (cp >> 12));
                        *w++ = (char)(0x80 | ((cp >> 6) & 0x3F));
                        *w++ = (char)(0x80 | (cp & 0x3F));
                    }
                } else {
                    *w++ = '\\';  // malformed — keep literal backslash
                }
                break;
            }
            default:
                *w++ = '\\';
                if (*r) *w++ = *r++;
                break;
        }
        *w = '\0';
    }
}

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
    // Unescape AFTER parsing so keys/vals hold real UTF-8 bytes, matching what
    // extract_utf16_string() produces from the game's System.String objects.
    for (int i = 0; i < count; i++) {
        json_unescape_inplace(keys[i]);
        json_unescape_inplace(vals[i]);
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
    // Count redirect types for diagnostic summary
    int n_songs = 0, n_packs = 0, n_catalog = 0;
    for (int i = 0; i < REDIRECT_COUNT; i++) {
        if (strstr(REDIRECT_KEYS[i], "catalog")) n_catalog++;
        else if (strstr(REDIRECT_KEYS[i], "pack_assets")) n_packs++;
        else n_songs++;
    }
    {
        char sbuf[256];
        snprintf(sbuf, sizeof(sbuf), "  breakdown: %d songs, %d packs, %d catalog", n_songs, n_packs, n_catalog);
        log_write(sbuf);
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

    // Deferred pad hook (M11): libScePad loads with the game (it imports
    // libScePad), so the first open-hook attempts resolve it.
    try_install_pad_hook();

    // Deferred Move hook (M11 v0.8050): the PRIMARY hotkey path — Beat Saber
    // reads both Moves every frame via sceMoveReadStateRecent (the only Move
    // state read in the eboot's imports). libSceMove also loads with the game.
    try_install_move_hook();

    const char *np = NULL;
    if (path) {
        char lower_path[MAX_PATH];
        int len = strlen(path);
        if (len < MAX_PATH) {
            for (int i = 0; i < len; i++) lower_path[i] = (path[i] >= 'A' && path[i] <= 'Z') ? (path[i] + 32) : path[i];
            lower_path[len] = '\0';

            // ── User redirects from redirects.json ────────────────────────────
            // Only active when enable_custom_song_replacements feature flag is ON
            // AND the global kill switch (enable_plugin) is not FALSE.
            if (!np && g_feature_plugin_enabled && g_feature_custom_song_replacements) {
                for (int i = 0; i < REDIRECT_COUNT; i++) {
                    if (strstr(lower_path, LOWER_REDIRECT_KEYS[i])) {
                        // GATE (Exp 222): enable_beatmap_mode_mapping controls the
                        // extra game-mode buttons (OneSaber/NoArrows/90Degree).
                        // Those live in the PATCHED PACK BUNDLE preview sets —
                        // when the flag is OFF we must serve the STOCK pack
                        // bundle (Standard-only preview sets), not the patched
                        // one. Pack-bundle redirects (keys containing
                        // "pack_assets") are skipped so the stock bundle loads.
                        // The CATALOG redirect must be skipped with it: the
                        // patched catalog carries the m_Crc/m_BundleSize of the
                        // PATCHED pack bundles — serving it against STOCK pack
                        // bundles fails Unity's CRC validation and crashes at
                        // the pack scan (Exp 180 invariant). Per-song redirects
                        // still fire (custom audio + Standard beatmaps keep
                        // working).
                        // GATE (Exp 269 / M10): enable_song_previews ALSO lives
                        // inside the patched pack bundle (the preview AudioClips
                        // ride in its .resource). Either flag ON → serve the
                        // patched pair; both OFF → serve stock. The bundle
                        // VARIANT the pipeline deployed matches the flag state
                        // at deploy time, so the redirect VALUE is already
                        // correct — this gate only decides patched vs stock.
                        if (!(g_feature_beatmap_mode_mapping || g_feature_song_previews)
                            && (strstr(LOWER_REDIRECT_KEYS[i], "pack_assets")
                                || strstr(LOWER_REDIRECT_KEYS[i], "catalog"))) {
                            continue;
                        }
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
HOOK_INIT(hook_pad_read);
HOOK_INIT(hook_move_read);
static int g_tmp_text_set_text_count = 0;

// Forward-declare IL2CPP's MethodInfo (opaque type)
struct MethodInfo;

// Fold a UTF-8 C string to the same ASCII projection that
// extract_utf16_string() applies to game System.String objects: every
// non-ASCII codepoint collapses to a single '?'. In-place; ASCII-only
// strings pass through unchanged. Keys loaded from song_metadata.json are
// folded at load time so key comparison matches the folded extraction of
// the game's song titles exactly (Exp 228: '…Baby One More Time' extracted
// as '?Baby One More Time' never matched the raw UTF-8 key).
// NOTE: astral-plane chars (emoji, > U+FFFF) occupy TWO UTF-16 code units
// in the game string (two '?') but only one UTF-8 codepoint here (one '?')
// — known limitation; no current song title uses astral chars.
static void fold_utf8_to_ascii(char *s) {
    char *r = s, *w = s;
    while (*r) {
        unsigned char c = (unsigned char)*r;
        if (c < 0x80) { *w++ = *r++; continue; }
        // Multibyte UTF-8: consume the full sequence, emit one '?' per UTF-16
        // code unit it decodes to (BMP = 1 unit / 1 '?', astral = 2 units / 2
        // '?') — an exact mirror of extract_utf16_string's fold so key
        // comparison is byte-identical for any Unicode title.
        int seq = (c >= 0xF0) ? 4 : (c >= 0xE0) ? 3 : 2;
        if ((c == 0xC0) || (c == 0xC1)) seq = 2;  // overlong — treat as 2
        int nq = (seq == 4) ? 2 : 1;
        r += seq;
        if (*(r-1) == '\0') r--;  // don't step past terminator on truncation
        while (nq-- > 0) *w++ = '?';
    }
    *w = '\0';
}

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
                fold_utf8_to_ascii(keys[i]);  // match extract_utf16_string's '?' fold
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
                fold_utf8_to_ascii(keys[i]);  // match extract_utf16_string's '?' fold
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
    // len is an upper bound — multibyte UTF-8 sequences shrink the count
    int total = 16 + 4 + (len * 2) + 2;
    void* str_mem = malloc(total);
    if (!str_mem) return NULL;

    // Copy klass pointer (8 bytes)
    memcpy(str_mem, klass_ptr, 8);
    // Zero monitor (8 bytes)
    memset((char*)str_mem + 8, 0, 8);

    // Decode UTF-8 -> UTF-16LE (Exp 228: ASCII-per-byte produced mojibake for
    // non-ASCII replacement values; il2cpp_string_new already handles UTF-8,
    // this manual fallback must too). Malformed bytes fold to U+FFFD-replacement
    // '?' to stay defensive against garbage values.
    uint16_t* chars = (uint16_t*)((char*)str_mem + 20);
    int nch = 0;
    for (int i = 0; i < len; ) {
        unsigned char c = (unsigned char)cstr[i];
        uint32_t cp = 0;
        int seq = 1;
        if (c < 0x80) { cp = c; seq = 1; }
        else if ((c & 0xE0) == 0xC0) { cp = c & 0x1F; seq = 2; }
        else if ((c & 0xF0) == 0xE0) { cp = c & 0x0F; seq = 3; }
        else if ((c & 0xF8) == 0xF0) { cp = c & 0x07; seq = 4; }
        else { cp = '?'; seq = 1; }  // stray continuation byte
        for (int j = 1; j < seq && (i + j) < len; j++) {
            unsigned char cc = (unsigned char)cstr[i + j];
            if ((cc & 0xC0) != 0x80) { cp = '?'; seq = 1; break; }
            cp = (cp << 6) | (cc & 0x3F);
        }
        if (cp >= 0x10000) cp = '?';  // astral chars don't fit one UTF-16 unit here
        chars[nch++] = (uint16_t)cp;
        i += seq;
    }
    *(uint32_t*)((char*)str_mem + 16) = (uint32_t)nch;  // actual char count
    chars[nch] = 0;  // null terminator

    return str_mem;
}

// Shared replacement logic for both set_text and SetText hooks
static void* apply_metadata_replacement(void* this_ptr, void* value) {
    if (!g_feature_plugin_enabled || !g_feature_song_metadata_modification || !value) return value;

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
    if (g_feature_plugin_enabled && g_feature_song_metadata_modification && state_machine) {
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
        }
    }
    HOOK_CONTINUE(hook_move_next, void (*)(void*), state_machine);
}

// ── In-game plugin toggle (M11): Move button + trigger hotkey ───────────────
// v0.8050 REDESIGN (Exp 278c). The v0.8049 L3+R3 DS4 hotkey never fired on
// hardware, and the boot log showed the ROOT CAUSE: dlsym(RTLD_DEFAULT,
// "scePadRead") FAILED because Sony system libraries export functions under
// their NIDs, not readable names — the game imports scePadRead as NID
// q1cHNfGycLI (readable-name dlsym only ever worked for il2cpp_string_new,
// which the game's eboot genuinely exports by name). All hooks are now
// resolved BY NID first (readable name kept as fallback).
//
// The real input path on this game is the MOVE controller (the DS4 is
// ignored in VR mode — user-verified). Beat Saber reads both Moves every
// frame through native sceMoveReadStateRecent (NID f2bcpK6kJfg) — the ONLY
// Move state read in the eboot's imports (sceMoveReadStateLatest is NOT
// imported). Hotkey (user-chosen): hold the Move BUTTON + TRIGGER together
// for 2 full seconds — a combination used nowhere else in the game.
//
// Move bit layout (reconstructed from the game's OWN enum in dump.cs —
// PSVRDeviceManager.PSMoveButton: Select=1, [2 = trigger], Move=4, Start=8,
// Triangle=16, Circle=32, Cross=64, Square=128; the enum skips 2 because the
// game reads the trigger via GetPSMoveAnalog — the trigger's DIGITAL bit is
// 0x2): SceMoveData.button_data u16 @ +0x18, trigger analog u16 @ +0x1A
// (struct layout per shadPS4Plus's SDK-derived OrbisMoveData). The hook logs
// the raw data words whenever they change, so the first boot log CONFIRMS or
// CORRECTS these offsets empirically before we rely on them further.
//
// Signature note: shadPS4 documents sceMoveReadStateRecent as 4-arg
// (handle, timestamp, data, out_count), but the hook detects the form at
// RUNTIME by validating candidate pointers with sceKernelQueryMemoryProtection
// (the v0.8045-proven signal-free technique): a 3-arg call leaves RDX holding
// the sample count (an int, fails validation), a 4-arg call leaves RSI holding
// a timestamp value (fails validation). ALL FOUR registers are always passed
// through untouched, so either form works; unknown forms pass through clean.
//
// Persist-only semantics + one-way-door prevention: UNCHANGED from v0.8049
// — the hotkey flips "enable_plugin" inside features.json for the NEXT boot
// (restart to apply; the current session never changes), and it is gated
// ONLY by enable_in_game_plugin_toggle — NOT by the enable_plugin kill
// switch (a toggled-OFF user must always be able to flip back from the
// couch, or the feature would be a one-way door).
#define NID_PAD_READ "q1cHNfGycLI"           // scePadRead — verified: eboot imports + aerolib
#define NID_MOVE_READ_RECENT "f2bcpK6kJfg"   // sceMoveReadStateRecent — same verification
#define PAD_BUTTON_L3 0x0002u                // DS4 combo (secondary path — kept for pad-mode sessions)
#define PAD_BUTTON_R3 0x0004u
#define PAD_COMBO (PAD_BUTTON_L3 | PAD_BUTTON_R3)             // 0x0006
#define MOVE_BUTTON_TRIGGER 0x0002u          // SceMoveData.button_data digital bits
#define MOVE_BUTTON_MOVE 0x0004u
#define MOVE_COMBO (MOVE_BUTTON_TRIGGER | MOVE_BUTTON_MOVE)   // 0x0006
#define MOVE_TRIGGER_ANALOG_THRESH 0x0080u   // trigger analog u16 @ +0x1A (fallback when bit 0x2 absent)
#define MOVE_DATA_BUTTON_OFF 0x18            // button_data u16 offset in SceMoveData
#define MOVE_DATA_TRIGGER_OFF 0x1A           // trigger u16 offset in SceMoveData
#define COMBO_HOLD_US 2000000ULL             // 2 s hold (sceKernelGetProcessTime is µs)
#define COMBO_GAP_US 250000ULL               // poll-to-poll continuity window (two Move handles interleave)
#define TOGGLE_COOLDOWN_US 3000000ULL        // global re-toggle cooldown (shared by both hook paths)
#define MOVE_DIAG_FIRST_N 10                 // log the first N move calls raw
#define MOVE_DIAG_CHANGE_MAX 40               // cap on button-change diagnostic logs
#define PAD_DIAG_N 8                          // log the first N pad calls

// Shared combo-hold state (fed by BOTH hook paths). A 2-second hold must be
// continuous within a 250 ms poll-gap window — the two Move handles
// interleave calls, so the non-holding handle's polls must not reset a hold
// in progress. Latched until the combo has been RELEASED for a full gap
// window; a 3 s cooldown after a fired toggle prevents double-fires.
static uint64_t g_combo_first_us = 0;       // when the current hold started (0 = none)
static uint64_t g_combo_last_us = 0;        // last poll that saw the combo
static uint64_t g_toggle_last_fired_us = 0;  // cooldown guard
static int g_combo_latched = 0;              // require combo release before the next fire
static int g_move_call_count = 0;
static int g_move_change_logs = 0;
static uint32_t g_move_prev_words[8] = {0};  // last-seen raw SceMoveData words (change logging)
static int g_pad_call_count = 0;             // total scePadRead calls seen (diagnostics/liveness)

// Flip "enable_plugin" inside features.json in place, preserving every other
// key/byte (the pipeline's Exp-248 pull-before-push reads the LIVE file, so
// in-game flips flow into webapp/ps4_state/pipeline deploys automatically).
// Returns the NEW state (1=enabled, 0=disabled), or -1 on failure.
static int in_game_toggle_plugin(void) {
    char buf[4096];
    int fd = sceKernelOpen(FEATURES_PATH, O_RDONLY, 0);
    if (fd < 0) {
        log_write("[TOGGLE] ERROR: cannot open features.json — toggle aborted");
        return -1;
    }
    ssize_t got = sceKernelRead(fd, buf, sizeof(buf) - 1);
    sceKernelClose(fd);
    if (got <= 0 || got >= (ssize_t)sizeof(buf) - 1) {
        log_write("[TOGGLE] ERROR: features.json unreadable — toggle aborted");
        return -1;
    }
    buf[got] = '\0';

    int new_state = -1;
    char *p = strstr(buf, "\"enable_plugin\"");
    if (p) {
        p = strchr(p + 15, ':');  // 15 == strlen("\"enable_plugin\""); land after the key
        if (p) {
            p++;
            while (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r') p++;
            if (*p == 't') {
                // "true" -> "false": grow by one byte
                memmove(p + 1, p, strlen(p) + 1);
                memcpy(p, "false", 5);
                got += 1;
                new_state = 0;
            } else if (*p == 'f') {
                // "false" -> "true": shrink by one byte
                memcpy(p, "true", 4);
                memmove(p + 4, p + 5, strlen(p + 5) + 1);
                got -= 1;
                new_state = 1;
            }
        }
    } else {
        // Key absent (hand-edited file): absent defaults ON, so the flip is
        // OFF — rewrite the file with all known keys from the boot parse.
        // (The pipeline always materializes enable_plugin, so this is rare;
        // any unknown keys are lost here but re-materialized by the next
        // pipeline deploy per the Exp 221 merge rule.)
        new_state = 0;
        got = snprintf(buf, sizeof(buf),
                       "{\n"
                       "  \"enable_plugin\": false,\n"
                       "  \"enable_custom_song_replacements\": %s,\n"
                       "  \"enable_song_metadata_modification\": %s,\n"
                       "  \"enable_beatmap_mode_mapping\": %s,\n"
                       "  \"enable_song_previews\": %s\n"
                       "}\n",
                       g_feature_custom_song_replacements ? "true" : "false",
                       g_feature_song_metadata_modification ? "true" : "false",
                       g_feature_beatmap_mode_mapping ? "true" : "false",
                       g_feature_song_previews ? "true" : "false");
    }

    if (new_state < 0) {
        log_write("[TOGGLE] ERROR: could not locate the enable_plugin value — toggle aborted");
        return -1;
    }

    fd = sceKernelOpen(FEATURES_PATH, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) {
        log_write("[TOGGLE] ERROR: cannot write features.json — toggle aborted");
        return -1;
    }
    sceKernelFchmod(fd, 0644);
    sceKernelWrite(fd, buf, got);
    sceKernelClose(fd);

    {
        char tlog[192];
        snprintf(tlog, sizeof(tlog),
                 "[TOGGLE] enable_plugin flipped to %s in features.json (persist-only; restart to apply)",
                 new_state ? "true (ON)" : "false (OFF)");
        log_write(tlog);
    }
    {
        OrbisNotificationRequest notif;
        memset(&notif, 0, sizeof(notif));
        notif.type = (OrbisNotificationRequestType)0;
        notif.targetId = -1;
        snprintf(notif.message, sizeof(notif.message),
                 "BS Deluxe: Plugin %s\nRestart game to apply",
                 new_state ? "ENABLED" : "DISABLED");
        sceKernelSendNotificationRequest(0, &notif, sizeof(notif), 0);
    }
    return new_state;
}

// Shared combo-hold detector — see the globals block for the state-machine
// contract. Feeds from BOTH hooks; each call reports whether THAT poll saw
// the combo (either path can carry it).
static void combo_feed(int combo_now) {
    uint64_t now = sceKernelGetProcessTime();
    if (combo_now) {
        if (g_combo_first_us == 0 || (now - g_combo_last_us) > COMBO_GAP_US) {
            g_combo_first_us = now ? now : 1;   // fresh hold (previous one expired)
        }
        g_combo_last_us = now;
        if (!g_combo_latched && (now - g_combo_first_us) >= COMBO_HOLD_US) {
            g_combo_latched = 1;  // require combo release before the next fire
            if (g_toggle_last_fired_us == 0 ||
                (now - g_toggle_last_fired_us) >= TOGGLE_COOLDOWN_US) {
                g_toggle_last_fired_us = now;
                in_game_toggle_plugin();
            } else {
                log_write("[TOGGLE] combo held but cooldown active — ignored");
            }
        }
    } else {
        if ((now - g_combo_last_us) > COMBO_GAP_US) {
            g_combo_first_us = 0;   // hold broken for a full gap window
            g_combo_latched = 0;
        }
    }
}

// Signal-free pointer validation (the v0.8045-proven sceKernelQueryMemory
// Protection technique): resolves the 3-arg vs 4-arg signature ambiguity of
// sceMoveReadStateRecent at runtime. Only accepts readable+ writable buffers
// — the output buffer the callee is about to write must be RW-mapped.
static int is_mapped_rw_pointer(void *p) {
    if ((uint64_t)p < 0x1000000ULL) return 0;  // below the PS4 module base range
    void *start = NULL, *end = NULL;
    int32_t prot = 0;
    if (sceKernelQueryMemoryProtection(p, &start, &end, &prot) < 0) return 0;
    return (prot & 0x3) == 0x3;
}

// scePadRead(handle, OrbisPadData*, num) — SECONDARY path (DS4 L3+R3; kept
// for any session where the game polls pads). Most recent sample is
// data[n-1]; the buttons u32 sits at offset 0 of each OrbisPadData
// (dual-verified). Feeds the shared combo detector.
static int pad_read_hook(int32_t handle, void *data, int32_t num) {
    int n = HOOK_CONTINUE(hook_pad_read, int (*)(int32_t, void*, int32_t), handle, data, num);
    if (!g_feature_in_game_plugin_toggle) return n;  // flag OFF (belt + braces: hook is not installed)

    g_pad_call_count++;
    if (data && n >= 1) {
        uint32_t buttons = ((uint32_t *)data)[n - 1];

        if (g_pad_call_count <= PAD_DIAG_N) {
            char dlog[160];
            snprintf(dlog, sizeof(dlog), "[TOGGLE] padRead#%d handle=%d num=%d ret=%d buttons=0x%08x",
                     g_pad_call_count, handle, num, n, buttons);
            log_write(dlog);
        } else if (g_pad_call_count % 10000 == 0) {
            char clog[96];
            snprintf(clog, sizeof(clog), "[TOGGLE] pad poll counter: %d calls", g_pad_call_count);
            log_write(clog);
        }

        combo_feed(buttons == PAD_COMBO);
    } else {
        combo_feed(0);
    }
    return n;
}

// sceMoveReadStateRecent — the PRIMARY hotkey path. Form detected at runtime
// (see is_mapped_rw_pointer): 4-arg form carries the SceMoveData buffer in
// RDX (a3), 3-arg form in RSI (a2). All four registers always pass through,
// so either form is safe. Button check runs on entry 0 — a 2-second hold
// spans 100+ frames, so every entry in every call shows the same held-state
// bits regardless of which entry is "most recent". Raw words are logged on
// the first calls and whenever they change (a button press lights up the
// log — empirically confirming the +0x18/+0x1A offsets).
static int move_read_hook(int32_t handle, int64_t a2, void *a3, int64_t a4) {
    int rc = HOOK_CONTINUE(hook_move_read, int (*)(int32_t, int64_t, void*, int64_t),
                           handle, a2, a3, a4);
    if (!g_feature_in_game_plugin_toggle) return rc;

    g_move_call_count++;

    void *data = NULL;
    int form = 0;
    if (is_mapped_rw_pointer(a3) && !is_mapped_rw_pointer((void *)a2)) {
        data = a3; form = 4;   // (handle, timestamp, data, out_count)
    } else if (is_mapped_rw_pointer((void *)a2) && !is_mapped_rw_pointer(a3)) {
        data = (void *)a2; form = 3;   // (handle, data, num)
    }

    if (data) {
        uint32_t *w = (uint32_t *)data;
        int changed = 0;
        for (int i = 2; i < 8; i++) {
            if (w[i] != g_move_prev_words[i]) changed = 1;
        }
        if (g_move_call_count <= MOVE_DIAG_FIRST_N ||
            (changed && g_move_change_logs < MOVE_DIAG_CHANGE_MAX)) {
            char dlog[288];
            snprintf(dlog, sizeof(dlog),
                     "[TOGGLE] moveRead#%d form=%d handle=%d rc=%d w=[%08x %08x %08x %08x %08x %08x %08x %08x]",
                     g_move_call_count, form, handle, rc,
                     w[0], w[1], w[2], w[3], w[4], w[5], w[6], w[7]);
            log_write(dlog);
            if (changed && g_move_call_count > MOVE_DIAG_FIRST_N) g_move_change_logs++;
        }
        for (int i = 0; i < 8; i++) g_move_prev_words[i] = w[i];

        uint16_t bd = *(uint16_t *)((char *)data + MOVE_DATA_BUTTON_OFF);
        uint16_t trig = *(uint16_t *)((char *)data + MOVE_DATA_TRIGGER_OFF);
        int move_held = (bd & MOVE_BUTTON_MOVE) != 0;
        int trig_held = ((bd & MOVE_BUTTON_TRIGGER) != 0) || (trig > MOVE_TRIGGER_ANALOG_THRESH);
        int clean = (bd & ~MOVE_COMBO) == 0;   // no other button bit set
        combo_feed(move_held && trig_held && clean);
    } else {
        combo_feed(0);
    }
    return rc;
}

// Lazy installs: dlsym BY NID (the v0.8050 root-cause fix — Sony system
// libraries export NIDs, not readable names; the readable-name dlsym only
// ever worked for eboot-exported symbols like il2cpp_string_new) + GoldHEN
// Detour. At module_start only 3 modules are visible; libScePad/libSceMove
// load with the game (the eboot imports both), so the first open_hook
// attempts resolve them. Give-up flags stop the retry loop cleanly (the
// v0.8049 build re-logged its ERROR on every open after giving up).
static int g_pad_hook_installed = 0;
static int g_pad_hook_attempts = 0;
static int g_pad_hook_gave_up = 0;
static int g_move_hook_installed = 0;
static int g_move_hook_attempts = 0;
static int g_move_hook_gave_up = 0;

static void try_install_pad_hook(void) {
    if (g_pad_hook_installed || g_pad_hook_gave_up) return;
    if (!g_feature_in_game_plugin_toggle) return;  // NOT gated by the kill switch (one-way-door rule)

    g_pad_hook_attempts++;
    void *fn = dlsym(RTLD_DEFAULT, NID_PAD_READ);
    if (!fn) fn = dlsym(RTLD_DEFAULT, "scePadRead");  // readable-name fallback
    if (!fn) {
        if (g_pad_hook_attempts <= 3 || g_pad_hook_attempts % 20 == 0) {
            char alog[128];
            snprintf(alog, sizeof(alog), "[TOGGLE] scePadRead not found yet (attempt %d, open #%d)",
                     g_pad_hook_attempts, g_open_count);
            log_write(alog);
        }
        if (g_pad_hook_attempts < 100) return;  // keep retrying
        g_pad_hook_gave_up = 1;
        log_write("[TOGGLE] ERROR: scePadRead never found — DS4 path unavailable this session (Move path may still work)");
        return;
    }

    Detour_Construct(&Detour_hook_pad_read, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_pad_read, (uint64_t)fn, (void *)pad_read_hook);
    g_pad_hook_installed = 1;

    char ilog[160];
    snprintf(ilog, sizeof(ilog),
             "[TOGGLE] scePadRead hooked at %p (NID-resolved) — DS4 L3+R3 secondary path",
             fn);
    log_write(ilog);
}

static void try_install_move_hook(void) {
    if (g_move_hook_installed || g_move_hook_gave_up) return;
    if (!g_feature_in_game_plugin_toggle) return;

    g_move_hook_attempts++;
    void *fn = dlsym(RTLD_DEFAULT, NID_MOVE_READ_RECENT);
    if (!fn) fn = dlsym(RTLD_DEFAULT, "sceMoveReadStateRecent");  // readable-name fallback
    if (!fn) {
        if (g_move_hook_attempts <= 3 || g_move_hook_attempts % 20 == 0) {
            char alog[128];
            snprintf(alog, sizeof(alog), "[TOGGLE] sceMoveReadStateRecent not found yet (attempt %d, open #%d)",
                     g_move_hook_attempts, g_open_count);
            log_write(alog);
        }
        if (g_move_hook_attempts < 100) return;
        g_move_hook_gave_up = 1;
        log_write("[TOGGLE] ERROR: sceMoveReadStateRecent never found — in-game toggle unavailable this session");
        return;
    }

    Detour_Construct(&Detour_hook_move_read, DetourMode_x64);
    Detour_DetourFunction(&Detour_hook_move_read, (uint64_t)fn, (void *)move_read_hook);
    g_move_hook_installed = 1;

    char ilog[160];
    snprintf(ilog, sizeof(ilog),
             "[TOGGLE] sceMoveReadStateRecent hooked at %p (NID-resolved) — hold Move button + trigger for 2s to toggle the plugin",
             fn);
    log_write(ilog);
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
    if (!g_feature_plugin_enabled || g_feature_song_metadata_modification == 0) return;

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
        snprintf(flog, sizeof(flog), "FEATURE FLAGS: plugin=%s  custom_song_replacements=%s  metadata_modification=%s  beatmap_mode_mapping=%s  song_previews=%s  in_game_plugin_toggle=%s",
                 g_feature_plugin_enabled ? "ON" : "OFF",
                 g_feature_custom_song_replacements ? "ON" : "OFF",
                 g_feature_song_metadata_modification ? "ON" : "OFF",
                 g_feature_beatmap_mode_mapping ? "ON" : "OFF",
                 g_feature_song_previews ? "ON" : "OFF",
                 g_feature_in_game_plugin_toggle ? "ON" : "OFF");
        log_write(flog);
    }

    if (g_feature_in_game_plugin_toggle) {
        log_write("[TOGGLE] in-game hotkey ARMED: hold the Move button + trigger together for 2s to flip enable_plugin (restart to apply)");
    }

    if (!g_feature_custom_song_replacements) {
        log_write("DISABLED: custom_song_replacements is OFF — redirects will NOT fire");
    }
    if (!g_feature_song_metadata_modification) {
        log_write("DISABLED: song_metadata_modification is OFF — metadata replacements disabled");
    }
    if (!g_feature_beatmap_mode_mapping) {
        log_write("DISABLED: beatmap_mode_mapping is OFF — pack bundle + catalog redirects skipped (stock packs, Standard-only modes; per-song customs still active)");
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

    // Notification: version + feature-flag status in ONE toast (Exp 221).
    // Two separate toasts were compressed into one because the PS4VR
    // switch-over swallows the second notification when the headset is
    // already powered on at game launch (user-verified: second toast only
    // appears when launching without the headset active).
    {
        int enabled_count = g_feature_custom_song_replacements
                          + g_feature_song_metadata_modification
                          + g_feature_beatmap_mode_mapping
                          + g_feature_song_previews
                          + g_feature_in_game_plugin_toggle;
        memset(&notif,0,sizeof(notif)); notif.type=(OrbisNotificationRequestType)0; notif.targetId=-1;
        if (g_feature_plugin_enabled) {
            snprintf(notif.message,sizeof(notif.message),
                     "BS Deluxe %s (ON)\nBy Chris Primeish\n(%d/5 features ON)",
                     PLUGIN_VERSION, enabled_count);
        } else {
            snprintf(notif.message,sizeof(notif.message),
                     "BS Deluxe %s (OFF)\nBy Chris Primeish\n(official songs only)",
                     PLUGIN_VERSION);
        }
        sceKernelSendNotificationRequest(0,&notif,sizeof(notif),0);
    }

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;(void)args;
    free_redirects();
    free_metadata();
    return 0;
}
