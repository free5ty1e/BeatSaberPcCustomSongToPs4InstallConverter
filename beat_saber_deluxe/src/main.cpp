#include "bs_deluxe.h"
#include <stdio.h>
#include <string.h>
#include <stddef.h>

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    FILE* f = fopen("/data/custom/bs_deluxe/heartbeat.txt", "w");
    if (f) {
        fprintf(f, "Heartbeat: Plugin Loaded Successfully!\n");
        fclose(f);
    }
    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}
