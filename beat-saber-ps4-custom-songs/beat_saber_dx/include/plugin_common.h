#ifndef PLUGIN_COMMON_H
#define PLUGIN_COMMON_H

#define PLUGIN_NAME "BSDX"
#define PLUGIN_VERSION "0.01"

#define GOLDHEN_PATH "/data/GoldHEN"
#define BSDX_PATH GOLDHEN_PATH "/BeatSaberDX"

#define final_printf(a, args...) klog("[" PLUGIN_NAME "] " a, ##args)

#include <GoldHEN/Common.h>

static struct proc_info procInfo;

bool file_exists(const char*);

uint64_t get_base_address();

typedef struct {
    char name[50];
    int value;
} variable;

extern variable variables[100];
extern int num_vars;

void set_plugin_var(const char*, int);
int get_plugin_var(const char*);

#endif