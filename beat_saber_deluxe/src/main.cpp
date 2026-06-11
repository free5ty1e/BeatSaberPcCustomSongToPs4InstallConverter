#include "bs_deluxe.h"
#include <stdio.h>
#include <string.h>

__attribute__((constructor))
void plugin_init() {
    FILE* f = fopen("/data/custom/bs_deluxe/heartbeat.txt", "w");
    if (f) {
        fprintf(f, "Heartbeat: Plugin Loaded Successfully!\n");
        fclose(f);
    }
}
