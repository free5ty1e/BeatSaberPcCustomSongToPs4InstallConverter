#include "bs_deluxe.h"
#include <string.h>
#include <stdio.h>
#include <time.h>

// Define our redirection rules
PathRedirect g_redirects[] = {
    {"resources.assets", "/data/custom/bs_deluxe/resources_patched.assets"},
    {"startmeup", "/data/custom/bs_deluxe/CustomSong"}
};

int g_redirect_count = sizeof(g_redirects) / sizeof(PathRedirect);

void log_message(const char* msg) {
    FILE* f = fopen("/data/custom/bs_deluxe/plugin.log", "a");
    if (f) {
        time_t now = time(NULL);
        char* ts = ctime(&now);
        if (ts) {
            ts[strlen(ts) - 1] = '\0'; // Remove newline
            fprintf(f, "[%s] %s\n", ts, msg);
        }
        fclose(f);
    }
}

int hooked_open(const char* pathname, int flags, mode_t mode) {
    if (pathname == NULL) return orig_open(pathname, flags, mode);

    // Log every file request to see what the game is actually doing
    char log_buf[512];
    snprintf(log_buf, sizeof(log_buf), "Request: %s", pathname);
    log_message(log_buf);

    // Fuzzy match: check if the path contains the target string
    for (int i = 0; i < g_redirect_count; i++) {
        if (strstr(pathname, g_redirects[i].original_path) != NULL) {
            char log_redir[512];
            snprintf(log_redir, sizeof(log_redir), "REDIRECT: %s -> %s", pathname, g_redirects[i].redirect_path);
            log_message(log_redir);
            
            return orig_open(g_redirects[i].redirect_path, flags, mode);
        }
    }

    return orig_open(pathname, flags, mode);
}

// Plugin entry point
extern "C" int plugin_main() {
    log_message("Beat Saber Deluxe Plugin Loaded!");

    void* sym = find_symbol("open");
    if (sym) {
        orig_open = (int (*)(const char*, int, mode_t))sym;
        install_hook((void*)orig_open, (void*)hooked_open);
        log_message("Hooked 'open' successfully.");
    } else {
        log_message("Failed to find 'open' symbol.");
    }

    return 0;
}
