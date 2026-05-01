/*
    plugin_common.c - Common plugin utilities for BSDX
*/

#include <stdint.h>
#include <stdio.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>
#include <sys/stat.h>

#include <GoldHEN/Common.h>
#include "include/plugin_common.h"

static uint64_t base_address = 0;

uint64_t get_base_address() {
    if (base_address != 0) {
        return base_address;
    }
    if (sys_sdk_proc_info(&procInfo) != 0) {
        // Fallback for emulator or when proc info unavailable
        base_address = 0x400000; // Common PS4 base
    } else {
        base_address = procInfo.base_address;
    }
    return base_address;
}

bool file_exists(const char* filename) {
    struct stat buff;
    return stat(filename, &buff) == 0 ? true : false;
}

variable variables[100];
int num_vars = 0;

void set_plugin_var(const char* name, int value) {
    for (int i = 0; i < num_vars; i++) {
        if (strcmp(variables[i].name, name) == 0) {
            variables[i].value = value;
            return;
        }
    }
    if (num_vars < 100) {
        strcpy(variables[num_vars].name, name);
        variables[num_vars].value = value;
        num_vars++;
    }
}

int get_plugin_var(const char* name) {
    for (int i = 0; i < num_vars; i++) {
        if (strcmp(variables[i].name, name) == 0) {
            return variables[i].value;
        }
    }
    return 0;
}