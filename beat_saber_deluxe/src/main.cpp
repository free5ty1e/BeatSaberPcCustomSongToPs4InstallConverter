/*
 * Beat Saber Deluxe - GoldHEN Plugin
 * Version: v0.8050
 */
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <dlfcn.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>
#include <ctype.h>
#include "../include/hooks.h"

#define PLUGIN_VERSION "v0.8051"
#define AFR_BASE  "/data/GoldHEN/AFR"
#define TITLE_ID "CUSA12878"
#define LOG_PATH AFR_BASE "/" TITLE_ID "/bs_log.txt"
#define CONFIG_PATH AFR_BASE "/" TITLE_ID "/redirects.json"
#define MAX_REDIRECTS 256
#define MAX_PATH 256

extern "C" {
    int module_start(size_t argc, const void **argv);
    int module_stop(size_t argc, const void **argv);
}

static char *REDIRECT_KEYS[MAX_REDIRECTS];
static char *REDIRECT_VALS[MAX_REDIRECTS];
static char *LOWER_REDIRECT_KEYS[MAX_REDIRECTS];
static int g_redirect_count = 0;

static void log_write(const char *msg) {
    int fd = open(LOG_PATH, O_WRONLY | O_CREAT | O_APPEND, 0644);
    if (fd >= 0) {
        write(fd, msg, strlen(msg));
        write(fd, "\n", 1);
        close(fd);
    }
}

static void parse_json_pairs(const char *json, char **keys, char **vals, int *count) {
    const char *p = json;
    while (*p) {
        while (*p && *p != '\"') p++;
        if (!*p) break;
        p++;
        const char *key_start = p;
        while (*p && *p != '\"') p++;
        int key_len = p - key_start;
        p++;
        while (*p && (*p == ' ' || *p == '\"' || *p == ':')) p++;
        while (*p && *p == '\"') p++;
        const char *val_start = p;
        while (*p && *p != '\"') p++;
        int val_len = p - val_start;
        
        if (*count < MAX_REDIRECTS) {
            keys[*count] = (char*)malloc(key_len + 1);
            memcpy(keys[*count], key_start, key_len);
            keys[*count][key_len] = 0;
            vals[*count] = (char*)malloc(val_len + 1);
            memcpy(vals[*count], val_start, val_len);
            vals[*count][val_len] = 0;
            LOWER_REDIRECT_KEYS[*count] = (char*)malloc(key_len + 1);
            for(int i=0; i<key_len; i++) LOWER_REDIRECT_KEYS[*count][i] = (char)tolower(keys[*count][i]);
            LOWER_REDIRECT_KEYS[*count][key_len] = 0;
            (*count)++;
        }
        while (*p && *p != '}') p++;
        if (*p == '}') break;
    }
}

static int (*sys_open)(const char *path, int flags, int mode);

static int open_hook(const char *path, int flags, int mode) {
    char lower_path[MAX_PATH];
    for(int i=0; i<MAX_PATH-1 && path[i]; i++) lower_path[i] = (char)tolower(path[i]);
    lower_path[strlen(path)] = 0;

    for (int i = 0; i < g_redirect_count; i++) {
        if (strstr(lower_path, LOWER_REDIRECT_KEYS[i])) {
            char logbuf[MAX_PATH + 64];
            snprintf(logbuf, sizeof(logbuf), "[OPEN #%d] %s -> %s", g_redirect_count, path, REDIRECT_VALS[i]);
            log_write(logbuf);
            return sys_open(REDIRECT_VALS[i], flags, mode);
        }
    }
    return sys_open(path, flags, mode);
}

int module_start(size_t argc, const void **argv) {
    log_write("=== BS Deluxe " PLUGIN_VERSION " started ===");
    
    int fd = open(CONFIG_PATH, O_RDONLY);
    if (fd >= 0) {
        char buf[4096];
        int n = read(fd, buf, sizeof(buf)-1);
        if (n > 0) {
            buf[n] = 0;
            parse_json_pairs(buf, REDIRECT_KEYS, REDIRECT_VALS, &g_redirect_count);
        }
        close(fd);
    }
    
    void *libkernel = dlopen("libkernel.prx", 0);
    sys_open = (int (*)(const char *, int, int))dlsym(libkernel, "open");
    
    install_hook((void*)sys_open, (void*)open_hook);
    
    return 0;
}

int module_stop(size_t argc, const void **argv) {
    return 0;
}
