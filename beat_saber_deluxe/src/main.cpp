#include "bs_deluxe.h"
#include <stdio.h>
#include <string.h>

extern "C" int plugin_main() {
    FILE* f = fopen("/data/custom/bs_deluxe/heartbeat.txt", "w");
    if (f) {
        fprintf(f, "Heartbeat: Plugin Loaded Successfully!\n");
        fclose(f);
    }
    return 0;
}
