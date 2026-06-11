#include "bs_deluxe.h"
#include <stdio.h>
#include <string.h>
#include <stddef.h>

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    // Heartbeat is written by _init in crt_patch.cpp
    // module_start is called from _init — do future init here
    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}
