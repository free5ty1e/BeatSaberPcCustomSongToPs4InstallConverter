// Beat Saber Deluxe — MINIMAL test
// Entry: _init (GoldHEN SDK crtprx.o calls module_start)
// NO library imports — testing if create-fself signed ELF is loadable

#include <stddef.h>

extern "C" int module_start(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}

extern "C" int module_stop(size_t argc, const void *args) {
    (void)argc;
    (void)args;
    return 0;
}
