#include "hooks.h"
#include <dlfcn.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <orbis/libkernel.h>
#include <sys/mman.h>

void* find_symbol(const char* symbol_name) {
    return dlsym(RTLD_DEFAULT, symbol_name);
}

void install_hook(void* original, void* replacement) {
    uint8_t* target = (uint8_t*)original;
    
    // Change protection to read-write-execute
    size_t page_size = 0x4000; // 16KB
    uintptr_t aligned_addr = (uintptr_t)target & ~(page_size - 1);
    sceKernelMprotect((void*)aligned_addr, page_size, PROT_READ | PROT_WRITE | PROT_EXEC);

    uint8_t jump_code[] = {
        0x48, 0xb8, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0xe0
    };
    
    uintptr_t replacement_addr = (uintptr_t)replacement;
    memcpy(&jump_code[2], &replacement_addr, sizeof(uintptr_t));
    memcpy(target, jump_code, sizeof(jump_code));

    // Restore original protection (read-execute)
    sceKernelMprotect((void*)aligned_addr, page_size, PROT_READ | PROT_EXEC);
}
