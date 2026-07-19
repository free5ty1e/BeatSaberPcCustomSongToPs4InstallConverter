/*
 * memory_inject.cpp — BeatmapLevelSO Memory Injection Module
 *
 * This module patches BeatmapLevelSO objects in RAM at runtime, bypassing
 * Addressables catalog CRC validation. Uses hook-triggered execution from
 * the open_hook callback rather than a separate thread.
 *
 * Key Insight: Addressables validates CRC LAZILY (when contents accessed,
 * not during LoadFromFile). This gives us a window to patch objects in RAM
 * before the game reads their metadata for the song selection screen.
 *
 * Strategy:
 *   1. open_hook detects when the first per-song bundle is opened → trigger
 *   2. Find BeatmapLevelSO class metadata in Il2CppUserAssemblies module
 *   3. Scan a focused memory range for BeatmapLevelSO instances via klass ptr
 *   4. Validate candidates and patch string fields in-place (UTF-16LE)
 *
 * Field Layout (verified from il2cpp dump at il2cpp.h:381195):
 *   BeatmapLevelSO_o:
 *     0x00: klass (BeatmapLevelSO_c*)
 *     0x08: monitor (void*)
 *     0x10: m_CachedPtr (intptr_t)     — from UnityEngine.Object
 *     0x18: _version (int32_t)
 *     0x20: _levelID (System_String_o*)
 *     0x28: _songName (System_String_o*)
 *     0x30: _songSubName (System_String_o*)
 *     0x38: _songAuthorName (System_String_o*)
 *     0x40: _levelAuthorName (System_String_o*)
 *
 *   System_String_o (il2cpp.h:67207):
 *     0x00: klass (System_String_c*)
 *     0x08: monitor (void*)
 *     0x10: _stringLength (int32_t)    — length in UTF-16 code units
 *     0x14: _firstChar (uint16_t)      — first char, rest follow as array
 *
 * v0.66 — Hook-triggered memory injection (no threads)
 */

#include "memory_inject.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <fcntl.h>
#include <orbis/libkernel.h>
#include <sys/mman.h>
#include <GoldHEN/Common.h>
#include <signal.h>
#include <setjmp.h>

// ── Configuration ──────────────────────────────────────────────────────────
#define MODULE_NAME "Il2CppUserAssemblies"
#define CLASS_NAME "BeatmapLevelSO"

// Focused scan range: IL2CPP managed heap on PS4 typically lives here
#define SCAN_START_ADDR 0x0000000200000000ULL
#define SCAN_END_ADDR   0x0000000400000000ULL
#define SCAN_STEP       0x10000ULL    // 64KB pages

// ── BeatmapLevelSO Field Offsets (from il2cpp dump) ──────────────────────
#define OFFSET_VERSION         0x18   // int32
#define OFFSET_LEVEL_ID        0x20   // System_String_o*
#define OFFSET_SONG_NAME       0x28   // System_String_o*
#define OFFSET_SONG_SUB_NAME   0x30   // System_String_o*
#define OFFSET_SONG_AUTHOR     0x38   // System_String_o*
#define OFFSET_LEVEL_AUTHOR    0x40   // System_String_o*

// ── Il2CppClass_1 field offsets ─────────────────────────────────────────
#define CLASS1_OFFSET_NAME         0x10  // const char* — class name

// ── Independent logging ──────────────────────────────────────────────────
// Uses its own sceKernelOpen/sceKernelWrite calls (not main.cpp's static
// log_write) to avoid exporting symbols from the plugin.
#define MEMINJ_LOG_PATH "/data/GoldHEN/AFR/CUSA12878/bs_log.txt"

static void meminj_log(const char* msg) {
    int fd = sceKernelOpen(MEMINJ_LOG_PATH, O_WRONLY|O_CREAT|O_APPEND, 0644);
    if (fd < 0) return;
    sceKernelFchmod(fd, 0644);
    sceKernelWrite(fd, msg, strlen(msg));
    sceKernelWrite(fd, "\n", 1);
    sceKernelClose(fd);
}

// ── Song Metadata Table ──────────────────────────────────────────────────
static SongMetadataEntry g_metadata_table[MAX_METADATA_ENTRIES];
static int g_metadata_count = 0;
static volatile int g_patching_done = 0;  // 0=not yet, 1=success, -1=attempted but failed

// ── Signal-handler memory probing ─────────────────────────────────────────
static sigjmp_buf g_mem_jmpbuf;

static void mem_fault_handler(int sig) {
    (void)sig;
    siglongjmp(g_mem_jmpbuf, 1);
}

// ── IL2CPP Structs ───────────────────────────────────────────────────────
typedef struct {
    uint64_t klass;    // 0x00: class pointer
    uint64_t monitor;  // 0x08: monitor/gc
} Il2CppObjectHeader;

// ── Module Segment Info ──────────────────────────────────────────────────
typedef struct {
    uint64_t base;
    uint64_t size;
    int is_exec;
    int is_readable;
    int is_writable;
} ModuleSegment;

// ── Forward Declarations ─────────────────────────────────────────────────
static int find_beatmap_level_so_klass(uint64_t* klass_out);
static int scan_for_beatmap_level_objects(uint64_t klass_addr,
                                          uint64_t* obj_addrs, int max_objs);
static int validate_beatmap_level_object(uint64_t addr);
static int patch_beatmap_level_object(uint64_t obj_addr,
                                      const SongMetadataEntry* meta);
static int patch_il2cpp_string(uint64_t string_addr, const char* new_text);
static int find_module_segments(const char* module_name,
                                ModuleSegment* segments, int max_segments);
static int try_read_mem(uint64_t addr, void* buf, size_t size);

// ── Pattern-Based Object Finding ─────────────────────────────────────────
// Alternative to klass string search: find BeatmapLevelSO objects on the GC
// heap by matching their field layout, then extract the klass pointer.
static int find_beatmap_level_objects_by_pattern(uint64_t* klass_out) {
    int seg_count;
    ModuleSegment mod_segs[4];
    {
        ModuleSegment segs[4];
        seg_count = find_module_segments(MODULE_NAME, segs, 4);
        if (seg_count <= 0) seg_count = 0;
        for (int i = 0; i < seg_count; i++) mod_segs[i] = segs[i];
    }

    uint8_t page[SCAN_STEP];
    for (uint64_t page_addr = SCAN_START_ADDR; page_addr < SCAN_END_ADDR; page_addr += SCAN_STEP) {
        if (!try_read_mem(page_addr, page, SCAN_STEP))
            continue;

        for (uint64_t offset = 0; offset < SCAN_STEP - 64; offset += 8) {
            uint64_t klass_ptr = *(uint64_t*)(page + offset + 0x00);
            int32_t version   = *(int32_t*)(page + offset + 0x18);
            uint64_t lid      = *(uint64_t*)(page + offset + 0x20);
            uint64_t sn       = *(uint64_t*)(page + offset + 0x28);
            uint64_t an       = *(uint64_t*)(page + offset + 0x38);

            // Klass pointer must be in module range
            if (klass_ptr < 0x80000000ULL || klass_ptr > 0x90000000ULL) continue;

            // Version must be a typical BeatmapLevelSO version
            if (version < 1 || version > 50) continue;

            // String pointer basic validation
            if (lid < 0x100000000ULL || lid > 0x8000000000ULL) continue;
            if (sn  < 0x100000000ULL || sn  > 0x8000000000ULL) continue;
            if (an  < 0x100000000ULL || an  > 0x8000000000ULL) continue;

            // Verify strings have plausible System_String header: length > 0, <= 255
            int32_t lid_len = 0, sn_len = 0;
            if (!try_read_mem(lid + 0x10, &lid_len, 4)) continue;
            if (!try_read_mem(sn  + 0x10, &sn_len,  4)) continue;
            if (lid_len <= 0 || lid_len > 255) continue;
            if (sn_len  <= 0 || sn_len  > 255) continue;

            // Found a valid BeatmapLevelSO candidate — use its klass
            *klass_out = klass_ptr;
            return 0;
        }
    }
    return -1;
}

// ══════════════════════════════════════════════════════════════════════════
// Public API
// ══════════════════════════════════════════════════════════════════════════

void memory_inject_register(const SongMetadataEntry* entry) {
    if (g_metadata_count >= MAX_METADATA_ENTRIES) {
        char buf[256];
        snprintf(buf, sizeof(buf),
                 "[MEMINJ] WARNING: metadata table full (%d entries)",
                 MAX_METADATA_ENTRIES);
        meminj_log(buf);
        return;
    }
    g_metadata_table[g_metadata_count++] = *entry;
}

int memory_inject_init(void) {
    meminj_log("[MEMINJ] Initialized (no guard timer, fires on any redirect)");
    if (g_metadata_count == 0) {
        meminj_log("[MEMINJ] WARNING: No metadata registered");
    }
    return 0;
}

// Called from open_hook when a per-song bundle is detected.
// Runs synchronously inside the open() callback.
// Returns 0 on success, -1 if not yet time or already done.
int memory_inject_try_patch(void) {
    // If already succeeded (1) or failed in the past (-1), skip
    if (g_patching_done) return -1;

    // Lock to prevent re-entry during scan
    if (__sync_lock_test_and_set(&g_patching_done, 1)) {
        return -1;  // Another caller already doing this
    }

    meminj_log("[MEMINJ] Scanning...");

    // Step 1: Find BeatmapLevelSO class metadata
    uint64_t klass_addr = 0;
    if (find_beatmap_level_so_klass(&klass_addr) < 0) {
        meminj_log("[MEMINJ] ERROR: Could not find BeatmapLevelSO klass");
        g_patching_done = -1;
        return -1;
    }

    char buf[256];
    snprintf(buf, sizeof(buf), "[MEMINJ] Klass at 0x%lX", klass_addr);
    meminj_log(buf);

    // Step 2: Scan for BeatmapLevelSO objects
    uint64_t obj_addrs[256];
    int found = scan_for_beatmap_level_objects(klass_addr, obj_addrs, 256);

    snprintf(buf, sizeof(buf), "[MEMINJ] Found %d candidates", found);
    meminj_log(buf);

    // Step 3: Patch matching objects
    int patched = 0;
    for (int i = 0; i < found && patched < g_metadata_count; i++) {
        // Read _levelID to identify this song
        uint64_t level_id_ptr = 0;
        if (!try_read_mem(obj_addrs[i] + OFFSET_LEVEL_ID, &level_id_ptr, 8) || !level_id_ptr)
            continue;

        // Read _levelID string length
        int32_t str_len = 0;
        if (!try_read_mem(level_id_ptr + 0x10, &str_len, 4) || str_len <= 0 || str_len > 100)
            continue;

        // Read _levelID string content (UTF-16LE → ASCII)
        char level_id_str[128];
        uint16_t str_buf[128] = {0};
        int read_len = str_len < 100 ? str_len * 2 : 200;
        if (!try_read_mem(level_id_ptr + 0x14, str_buf, read_len))
            continue;

        for (int c = 0; c < str_len && c < 100; c++)
            level_id_str[c] = (char)str_buf[c];
        level_id_str[str_len < 100 ? str_len : 100] = '\0';

        // Match against registered metadata
        for (int m = 0; m < g_metadata_count; m++) {
            if (g_metadata_table[m].level_id &&
                strcmp(level_id_str, g_metadata_table[m].level_id) == 0) {
                snprintf(buf, sizeof(buf),
                         "[MEMINJ] Patching 0x%lX: %s", obj_addrs[i], level_id_str);
                meminj_log(buf);

                if (patch_beatmap_level_object(obj_addrs[i], &g_metadata_table[m]) == 0) {
                    patched++;
                }
                break;
            }
        }
    }

    snprintf(buf, sizeof(buf), "[MEMINJ] Patched %d/%d objects", patched, g_metadata_count);
    meminj_log(buf);

    g_patching_done = patched ? patched : -1;
    return patched > 0 ? 0 : -1;
}

// ══════════════════════════════════════════════════════════════════════════
// Module & Class Metadata Finding
// ══════════════════════════════════════════════════════════════════════════

static int find_module_segments(const char* module_name,
                                ModuleSegment* segments, int max_segments) {
    OrbisKernelModule modules[64];
    size_t available = 0;

    if (sceKernelGetModuleList(modules, 64, &available) < 0)
        return -1;

    for (size_t i = 0; i < available; i++) {
        OrbisKernelModuleInfo info;
        memset(&info, 0, sizeof(info));
        info.size = sizeof(info);
        if (sceKernelGetModuleInfo(modules[i], &info) < 0) continue;
        if (strstr(info.name, module_name) == NULL) continue;

        int seg_count = 0;
        for (int s = 0; s < 4 && s < max_segments; s++) {
            if (info.segmentInfo[s].size == 0) continue;
            segments[seg_count].base = (uint64_t)info.segmentInfo[s].address;
            segments[seg_count].size = info.segmentInfo[s].size;
            uint64_t prot = info.segmentInfo[s].prot;
            segments[seg_count].is_exec = (prot & 0x1) != 0;
            segments[seg_count].is_readable = (prot & 0x4) != 0;
            segments[seg_count].is_writable = (prot & 0x2) != 0;
            seg_count++;
        }
        return seg_count;
    }
    return -1;
}

static uint64_t search_for_string(uint64_t region_start, uint64_t region_size,
                                   const char* needle) {
    size_t needle_len = strlen(needle);
    if (needle_len == 0) return 0;

    uint8_t buffer[4096];
    for (uint64_t offset = 0; offset < region_size; offset += sizeof(buffer)) {
        uint64_t addr = region_start + offset;
        size_t chunk_size = sizeof(buffer);
        if (offset + chunk_size > region_size)
            chunk_size = region_size - offset;

        if (!try_read_mem(addr, buffer, chunk_size))
            continue;

        for (size_t i = 0; i <= chunk_size - needle_len; i++) {
            if (memcmp(buffer + i, needle, needle_len) == 0)
                return addr + i;
        }
    }
    return 0;
}

static int find_beatmap_level_so_klass(uint64_t* klass_out) {
    ModuleSegment segs[4];
    int seg_count = find_module_segments(MODULE_NAME, segs, 4);
    if (seg_count < 0) {
        meminj_log("[MEMINJ] ERROR: Module not found");
        return -1;
    }

    // Log all segments (including non-readable) for diagnostics
    {   char buf[256];
        snprintf(buf, sizeof(buf), "[MEMINJ:VERBOSE] Il2CppUserAssemblies: %d segments", seg_count);
        meminj_log(buf);
        for (int s = 0; s < seg_count; s++) {
            snprintf(buf, sizeof(buf), "[MEMINJ:VERBOSE] Seg[%d]: base=0x%lX size=0x%lX prot=r%dw%dx%d",
                     s, segs[s].base, segs[s].size,
                     segs[s].is_readable, segs[s].is_writable, segs[s].is_exec);
            meminj_log(buf);
            // Test first chunk readability with signal handlers (works even on non-readable mappings)
            uint8_t test_buf[16];
            int readable = try_read_mem(segs[s].base, test_buf, 16);
            snprintf(buf, sizeof(buf), "[MEMINJ:VERBOSE] Seg[%d]: try_read_mem(first 16) = %s",
                     s, readable ? "OK" : "FAIL");
            meminj_log(buf);
        }
    }

    // Find "BeatmapLevelSO" C string in module (try ALL segments, signal handler catches faults)
    uint64_t class_string_addr = 0;
    for (int s = 0; s < seg_count; s++) {
        // Skip segments with no readable base (bounds check would reject)
        if (segs[s].base == 0 || segs[s].size == 0) continue;
        class_string_addr = search_for_string(segs[s].base, segs[s].size, CLASS_NAME);
        if (class_string_addr) {
            char buf[256];
            snprintf(buf, sizeof(buf), "[MEMINJ] Found 'BeatmapLevelSO' in Seg[%d] at 0x%lX",
                     s, class_string_addr);
            meminj_log(buf);
            break;
        }
    }

    if (!class_string_addr) {
        // String not in module — try broader search in IL2CPP heap and other mapped regions
        meminj_log("[MEMINJ] String not in module — trying heap scan for BeatmapLevelSO...");
        if (find_beatmap_level_objects_by_pattern(klass_out) == 0) {
            meminj_log("[MEMINJ] Found BeatmapLevelSO objects via pattern matching");
            return 0;
        }
        meminj_log("[MEMINJ] ERROR: Class string not found");
        return -1;
    }

    // Search for 8-byte pointers to this string (the `name` field in Il2CppClass_1)
    for (int s = 0; s < seg_count; s++) {
        if (!segs[s].is_readable) continue;
        uint64_t scan_end = segs[s].base + segs[s].size;

        for (uint64_t addr = segs[s].base; addr < scan_end; addr += 8) {
            uint64_t val = 0;
            if (!try_read_mem(addr, &val, 8)) continue;
            if (val != class_string_addr) continue;

            // Candidate at addr — check if addr-0x10 is start of Il2CppClass_1
            uint64_t candidate = addr - 0x10;

            // Check namespaze at +0x18
            uint64_t ns_ptr = 0;
            if (!try_read_mem(candidate + 0x18, &ns_ptr, 8)) continue;
            if (ns_ptr < 0x10000 || ns_ptr > 0x8000000000ULL) continue;

            // Check byval_arg at +0x20
            uint64_t bv_ptr = 0;
            if (!try_read_mem(candidate + 0x20, &bv_ptr, 8)) continue;

            *klass_out = candidate;
            return 0;
        }
    }

    meminj_log("[MEMINJ] ERROR: Klass not found in module data");
    return -1;
}

// ══════════════════════════════════════════════════════════════════════════
// Memory Scanning for BeatmapLevelSO Objects
// ══════════════════════════════════════════════════════════════════════════

static int try_read_mem(uint64_t addr, void* buf, size_t size) {
    // Bounds check: must be in user space (PS4 modules load ~2GB, GC heap ~8-16GB)
    // Lower bound 16MB to avoid null/near-null pointers, upper bound 128GB for safety
    if (addr < 0x1000000ULL || addr > 0x2000000000ULL) return 0;
    if (addr + size > 0x2000000000ULL || addr + size < addr) return 0;

    // Install signal handlers for safe memory probing.
    // SIGSEGV/SIGBUS fire if the target address range is not readable,
    // mem_fault_handler longjmps back, and we return 0.
    struct sigaction sa, old_segv, old_bus;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = mem_fault_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;

    if (sigaction(SIGSEGV, &sa, &old_segv) != 0) return 0;
    if (sigaction(SIGBUS, &sa, &old_bus) != 0) {
        sigaction(SIGSEGV, &old_segv, NULL);
        return 0;
    }

    int result = 0;
    if (sigsetjmp(g_mem_jmpbuf, 1) == 0) {
        memcpy(buf, (void*)addr, size);
        result = 1;
    }

    sigaction(SIGSEGV, &old_segv, NULL);
    sigaction(SIGBUS, &old_bus, NULL);
    return result;
}

static int scan_for_beatmap_level_objects(uint64_t klass_addr,
                                          uint64_t* obj_addrs, int max_objs) {
    int found = 0;
    char buf[256];
    snprintf(buf, sizeof(buf), "[MEMINJ] Scanning (klass=0x%lX)...", klass_addr);
    meminj_log(buf);

    uint8_t page[SCAN_STEP];
    for (uint64_t page_addr = SCAN_START_ADDR;
         page_addr < SCAN_END_ADDR && found < max_objs;
         page_addr += SCAN_STEP) {

        if (!try_read_mem(page_addr, page, SCAN_STEP))
            continue;

        for (uint64_t offset = 0; offset < SCAN_STEP - 24; offset += 8) {
            uint64_t val = *(uint64_t*)(page + offset);
            if (val == klass_addr) {
                uint64_t candidate = page_addr + offset;
                if (validate_beatmap_level_object(candidate)) {
                    obj_addrs[found++] = candidate;
                    if (found >= max_objs) break;
                }
            }
        }
    }
    return found;
}

static int validate_beatmap_level_object(uint64_t addr) {
    // _version must be [1, 100]
    int32_t version = 0;
    if (!try_read_mem(addr + OFFSET_VERSION, &version, 4)) return 0;
    if (version < 1 || version > 100) return 0;

    // _levelID must be a valid string pointer
    uint64_t lid = 0;
    if (!try_read_mem(addr + OFFSET_LEVEL_ID, &lid, 8)) return 0;
    if (lid < 0x100000000ULL || lid > 0x8000000000ULL) return 0;

    // _songName must be a valid pointer
    uint64_t sn = 0;
    if (!try_read_mem(addr + OFFSET_SONG_NAME, &sn, 8)) return 0;
    if (sn < 0x100000000ULL || sn > 0x8000000000ULL) return 0;

    // _songAuthorName must be a valid pointer
    uint64_t an = 0;
    if (!try_read_mem(addr + OFFSET_SONG_AUTHOR, &an, 8)) return 0;
    if (an < 0x100000000ULL || an > 0x8000000000ULL) return 0;

    return 1;
}

// ══════════════════════════════════════════════════════════════════════════
// String & Object Patching
// ══════════════════════════════════════════════════════════════════════════

static int patch_il2cpp_string(uint64_t string_addr, const char* new_text) {
    if (!string_addr || !new_text) return -1;

    int32_t old_length = 0;
    if (!try_read_mem(string_addr + 0x10, &old_length, 4)) return -1;

    int new_length = (int)strlen(new_text);
    if (new_length > old_length) {
        new_length = old_length;  // Truncate if doesn't fit
    }

    // Write new length
    *(int32_t*)(string_addr + 0x10) = new_length;

    // Write UTF-16LE characters
    uint16_t* char_buf = (uint16_t*)(string_addr + 0x14);
    for (int i = 0; i < new_length; i++) {
        char_buf[i] = (uint16_t)(unsigned char)new_text[i];
    }
    for (int i = new_length; i < old_length; i++) {
        char_buf[i] = 0;
    }
    return 0;
}

static int patch_beatmap_level_object(uint64_t obj_addr,
                                      const SongMetadataEntry* meta) {
    int patched = 0;
    char buf[256];

    #define TRY_PATCH_FIELD(offset, field_name, value) \
        do { \
            uint64_t str_addr = 0; \
            if (try_read_mem(obj_addr + (offset), &str_addr, 8) && str_addr) { \
                if (patch_il2cpp_string(str_addr, value) == 0) { \
                    patched++; \
                    snprintf(buf, sizeof(buf), \
                             "[MEMINJ]   %s -> '%s'", field_name, value); \
                    meminj_log(buf); \
                } \
            } \
        } while(0)

    if (meta->song_name && meta->song_name[0])
        TRY_PATCH_FIELD(OFFSET_SONG_NAME, "songName", meta->song_name);

    if (meta->song_author_name && meta->song_author_name[0])
        TRY_PATCH_FIELD(OFFSET_SONG_AUTHOR, "songAuthor", meta->song_author_name);

    if (meta->level_id && meta->level_id[0])
        TRY_PATCH_FIELD(OFFSET_LEVEL_ID, "levelID", meta->level_id);

    if (meta->song_sub_name && meta->song_sub_name[0])
        TRY_PATCH_FIELD(OFFSET_SONG_SUB_NAME, "songSubName", meta->song_sub_name);

    if (meta->level_author_name && meta->level_author_name[0])
        TRY_PATCH_FIELD(OFFSET_LEVEL_AUTHOR, "levelAuthor", meta->level_author_name);

    #undef TRY_PATCH_FIELD

    snprintf(buf, sizeof(buf),
             "[MEMINJ] Object 0x%lX: %d fields patched", obj_addr, patched);
    meminj_log(buf);
    return patched > 0 ? 0 : -1;
}
