#ifndef BEAT_SABER_DELUXE_H
#define BEAT_SABER_DELUXE_H

#include <ps4_sdk.h> // Hypothetical SDK header

// Redirection Map
typedef struct {
    const char* original_path;
    const char* redirect_path;
} PathRedirect;

// Global redirection table
extern PathRedirect g_redirects[];
extern int g_redirect_count;

// Hook function for sceFileUtilsOpen
int (*orig_sceFileUtilsOpen)(const char* path, int flags, int mode);
int hooked_sceFileUtilsOpen(const char* path, int flags, int mode);

#endif
