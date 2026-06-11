// Beat Saber Deluxe — GoldHEN Plugin
// Entry: _init (provided by GoldHEN SDK crtprx.o, calls module_start)

#include <stdio.h>
#include <stddef.h>
#include <string.h>

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;
    (void)args;

    // Heartbeat — prove module_start is called by crtprx.o's _init
    FILE* f = fopen("/data/custom/bs_deluxe/heartbeat.txt", "w");
    if (f) {
        fprintf(f, "Heartbeat: module_start via GoldHEN SDK crtprx.o!\n");
        fprintf(f, "Experiment: GoldHEN SDK crtprx.o CRT\n");
        fclose(f);
    }

    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}
