/*
    main.c - Beat Saber Deluxe (BSDX)
    GoldHEN Plugin for Beat Saber PS4 Custom Songs
    
    Based on RB4DX Plugin architecture: https://github.com/LlysiX/RB4DX-Plugin
*/

#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#define attr_module_hidden __attribute__((weak)) __attribute__((visibility("hidden")))
#define attr_public __attribute__((visibility("default")))

#define GOLDHEN_PATH "/data/GoldHEN"
#define BSDX_PATH GOLDHEN_PATH "/BeatSaberDX"

#include <GoldHEN/Common.h>
#include <orbis/libkernel.h>
#include <orbis/Sysmodule.h>
#include <orbis/Pad.h>

#include "include/plugin_common.h"

// Plugin metadata
attr_public const char *g_pluginName = PLUGIN_NAME;
attr_public const char *g_pluginDesc = "Beat Saber Deluxe - Custom Songs Plugin";
attr_public const char *g_pluginAuth = "BeatSaberDX";
attr_public uint32_t g_pluginVersion = 0x00000001; // 0.01

// Notification helper
void DoNotificationStatic(const char* text) {
    OrbisNotificationRequest Buffer = { 0 };
    Buffer.useIconImageUri = 1;
    Buffer.targetId = -1;
    strcpy(Buffer.message, text);
    strcpy(Buffer.iconUri, "https://raw.githubusercontent.com/BeatSaber/BeatSaber/master/icon.png");
    sceKernelSendNotificationRequest(0, &Buffer, sizeof(Buffer), 0);
}

void DoNotification(const char *FMT, ...) {
    OrbisNotificationRequest Buffer = { 0 };
    va_list args;
    va_start(args, FMT);
    vsprintf(Buffer.message, FMT, args);
    va_end(args);
    Buffer.type = NotificationRequest;
    Buffer.unk3 = 0;
    Buffer.useIconImageUri = 1;
    Buffer.targetId = -1;
    strcpy(Buffer.iconUri, "https://raw.githubusercontent.com/BeatSaber/BeatSaber/master/icon.png");
    sceKernelSendNotificationRequest(0, &Buffer, sizeof(Buffer), 0);
}

// ============================================
// TODO: Beat Saber specific hooks
// ============================================

/*
    IMPORTANT: These addresses need to be found for Beat Saber
    Unlike RB4DX where addresses are known, we need to discover
    Beat Saber's function addresses through reverse engineering.
*/

/*
// Example hook structure (from RB4DX):
void* (*NewFile)(const char*, FileMode);
HOOK_INIT(NewFile);

// For Beat Saber, we likely need:
void* (*AssetBundle_LoadFromFile)(const char*);
HOOK_INIT(AssetBundle_LoadFromFile);

void* (*AssetBundle_LoadAsset)(void*, const char*);
HOOK_INIT(AssetBundle_LoadAsset);
*/

// ============================================
// Module Start/Stop (required by GoldHEN)
// ============================================

int32_t attr_public module_start(size_t argc, const void *args)
{
    // Get process info
    if (sys_sdk_proc_info(&procInfo) != 0) {
        final_printf("Failed to get process info\n");
        return 0;
    }
    
    final_printf("BSDX Plugin starting...\n");
    final_printf("Title ID: %s\n", procInfo.titleid);
    final_printf("Version: %s\n", procInfo.version);
    final_printf("Base Address: 0x%lx\n", procInfo.base_address);
    
    // Check if this is Beat Saber
    if (strcmp(procInfo.titleid, "CUSA12878") != 0) {
        final_printf("Not Beat Saber (CUSA12878), exiting\n");
        return 0;
    }
    
    final_printf("Beat Saber detected!\n");
    DoNotificationStatic("BSDX Plugin loaded!");
    
    // ========================================
    // TODO: Set up Beat Saber specific hooks
    // ========================================
    
    /*
    uint64_t base = get_base_address();
    
    // These addresses are guesses and need to be verified
    // through reverse engineering of Beat Saber's eboot.bin
    
    // AssetBundle hooks (Unity 2022)
    AssetBundle_LoadFromFile = (void*)(base + 0x??????);
    AssetBundle_LoadAsset = (void*)(base + 0x??????);
    
    // Scene/Level loading hooks
    // SceneManager_LoadScene = (void*)(base + 0x??????);
    // LevelLoader_LoadLevel = (void*)(base + 0x??????);
    
    // Apply hooks
    HOOK(AssetBundle_LoadFromFile);
    HOOK(AssetBundle_LoadAsset);
    */
    
    final_printf("BSDX Plugin initialized\n");
    
    return 0;
}

int32_t attr_public module_stop(size_t argc, const void *args)
{
    final_printf("BSDX Plugin stopping...\n");
    
    // ========================================
    // TODO: Unhook all functions
    // ========================================
    
    /*
    UNHOOK(AssetBundle_LoadFromFile);
    UNHOOK(AssetBundle_LoadAsset);
    */
    
    return 0;
}