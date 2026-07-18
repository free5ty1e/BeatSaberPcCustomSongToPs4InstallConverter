/*
 * memory_inject.cpp — BeatmapLevelSO Memory Injection Module
 *
 * This module implements memory injection for patching BeatmapLevelSO objects
 * at runtime, bypassing Addressables catalog CRC validation.
 *
 * Key Insight: Addressables validates CRC LAZILY (when contents accessed, not
 * during LoadFromFile). This gives us a window to patch objects in RAM before
 * the game reads their metadata for the song selection screen.
 *
 * Strategy:
 *   1. After module_start, create a delayed worker thread (waits 30s for init)
 *   2. Find the BeatmapLevelSO class metadata (BeatmapLevelSO_c) in the
 *      Il2CppUserAssemblies module by searching for the "BeatmapLevelSO" string
 *      and locating Il2CppClass_1 structs that reference it via the name field.
 *   3. Scan process memory for IL2CPP objects whose klass pointer matches
 *      BeatmapLevelSO_c — these are BeatmapLevelSO instances.
 *   4. Validate each candidate by checking field integrity (version, string ptrs)
 *   5. Patch string fields in-place (overwrite managed string content with
 *      custom UTF-16 data, ensuring new length ≤ original capacity).
 *
 * Field Layout (verified from il2cpp dump):
 *   BeatmapLevelSO_o:
 *     0x00: klass (BeatmapLevelSO_c*)  — class metadata pointer
 *     0x08: monitor (void*)
 *     0x10: m_CachedPtr (intptr_t)     — from UnityEngine.Object
 *     0x18: _version (int32_t)
 *     0x20: _levelID (System_String_o*)
 *     0x28: _songName (System_String_o*)
 *     0x30: _songSubName (System_String_o*)
 *     0x38: _songAuthorName (System_String_o*)
 *     0x40: _levelAuthorName (System_String_o*)
 *
 *   System_String_o:
 *     0x00: klass (System_String_c*)   — class metadata for String
 *     0x08: monitor (void*)
 *     0x10: _stringLength (int32_t)    — length in UTF-16 code units
 *     0x14: _firstChar (uint16_t)      — first char, rest follow as array
 *
 * v0.66 — Memory Injection Implementation
 */

#include "memory_inject.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <pthread.h>
#include <orbis/libkernel.h>
#include <GoldHEN/Common.h>

// ── Configuration ──────────────────────────────────────────────────────────
#define MODULE_NAME "Il2CppUserAssemblies"
#define CLASS_NAME "BeatmapLevelSO"
#define STRING_CLASS_NAME "System.String"
#define THREAD_DELAY_US 30000000ULL  // 30 seconds before scanning

// Scan range for BeatmapLevelSO objects (PS4 user-space heap area)
#define SCAN_START_ADDR 0x0000000100000000ULL
#define SCAN_END_ADDR   0x0000000800000000ULL
#define SCAN_STEP       0x10000ULL    // 64KB coarse pages

// ── IL2CPP Type IDs ────────────────────────────────────────────────────────
#define TYPE_BEATMAP_LEVEL_SO 11680
#define TYPE_STRING           4

// ── BeatmapLevelSO Field Offsets (from il2cpp dump) ──────────────────────
// BeatmapLevelSO_o = Il2CppObject(16) + UnityEngine.Object(8) + fields
#define OFFSET_VERSION         0x18   // int32
#define OFFSET_LEVEL_ID        0x20   // System_String_o*
#define OFFSET_SONG_NAME       0x28   // System_String_o*
#define OFFSET_SONG_SUB_NAME   0x30   // System_String_o*
#define OFFSET_SONG_AUTHOR     0x38   // System_String_o*
#define OFFSET_LEVEL_AUTHOR    0x40   // System_String_o*

// ── Il2CppClass_1 field offsets (for finding class metadata) ────────────
#define CLASS1_OFFSET_NAME         0x10  // const char* — class name
#define CLASS1_OFFSET_NAMESPAZE    0x18  // const char* — namespace

// ── Logging ─────────────────────────────────────────────────────────────────
// Use the same logging mechanism as main.cpp (appends to bs_log.txt)
extern int log_write(const char* msg);
extern uint64_t find_il2cpp_module_base(void);

// ── Song Metadata Table ────────────────────────────────────────────────────
// Registered by calls to memory_inject_register()
static SongMetadataEntry g_metadata_table[MAX_METADATA_ENTRIES];
static int g_metadata_count = 0;
static volatile int g_patching_done = 0;

// ── IL2CPP Structs (from verified il2cpp dump) ────────────────────────────
typedef struct {
    uint64_t klass;    // 0x00: class pointer
    uint64_t monitor;  // 0x08: monitor/gc
} Il2CppObjectHeader;

typedef struct {
    Il2CppObjectHeader header;  // 0x00-0x0F
    int32_t _stringLength;      // 0x10
    uint16_t _firstChar;        // 0x14 — followed by remaining chars
} SystemStringHeader;

// ── Module Segment Info ────────────────────────────────────────────────────
typedef struct {
    uint64_t base;
    uint64_t size;
    int is_exec;
    int is_readable;
    int is_writable;
} ModuleSegment;

// ── Forward Declarations ───────────────────────────────────────────────────
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
static void* patch_worker(void* arg);

// ══════════════════════════════════════════════════════════════════════════
// Public API
// ══════════════════════════════════════════════════════════════════════════

void memory_inject_register(const SongMetadataEntry* entry) {
    if (g_metadata_count >= MAX_METADATA_ENTRIES) {
        char buf[256];
        snprintf(buf, sizeof(buf),
                 "[MEMINJ] WARNING: metadata table full (%d entries)",
                 MAX_METADATA_ENTRIES);
        log_write(buf);
        return;
    }
    g_metadata_table[g_metadata_count++] = *entry;

    char buf[256];
    snprintf(buf, sizeof(buf),
             "[MEMINJ] Registered: %s → %s",
             entry->level_id ? entry->level_id : "NULL",
             entry->song_name ? entry->song_name : "NULL");
    log_write(buf);
}

int memory_inject_init(void) {
    log_write("[MEMINJ] Initializing memory injection subsystem...");

    if (g_metadata_count == 0) {
        log_write("[MEMINJ] WARNING: No metadata registered — nothing to patch");
    }

    // Create a detached worker thread for delayed patching
    pthread_t thread;
    int ret = pthread_create(&thread, NULL, (void* (*)(void*))patch_worker, NULL);

    if (ret != 0) {
        char buf[128];
        snprintf(buf, sizeof(buf), "[MEMINJ] ERROR: pthread_create failed: %d", ret);
        log_write(buf);
        return -1;
    }

    pthread_detach(thread);

    log_write("[MEMINJ] Worker thread created — will patch after delay");
    return 0;
}

// ══════════════════════════════════════════════════════════════════════════
// Worker Thread
// ══════════════════════════════════════════════════════════════════════════

static void* patch_worker(void* arg) {
    (void)arg;
    log_write("[MEMINJ] Worker thread started — waiting for game to initialize...");

    // Wait for game to fully initialize and load the pack bundle
    usleep(THREAD_DELAY_US);

    // Step 1: Find BeatmapLevelSO class metadata (klass pointer)
    uint64_t klass_addr = 0;
    if (find_beatmap_level_so_klass(&klass_addr) < 0) {
        log_write("[MEMINJ] ERROR: Could not find BeatmapLevelSO klass");
        g_patching_done = -1;
        return NULL;
    }

    char buf[256];
    snprintf(buf, sizeof(buf), "[MEMINJ] Found BeatmapLevelSO klass at 0x%lX", klass_addr);
    log_write(buf);

    // Step 2: Scan memory for BeatmapLevelSO objects
    uint64_t obj_addrs[256];
    int found = scan_for_beatmap_level_objects(klass_addr, obj_addrs, 256);

    snprintf(buf, sizeof(buf), "[MEMINJ] Found %d potential BeatmapLevelSO objects", found);
    log_write(buf);

    // Step 3: Patch each validated object
    int patched = 0;
    for (int i = 0; i < found && patched < g_metadata_count; i++) {
        // Get the level_id string to identify which song this is
        uint64_t level_id_ptr = 0;
        if (!try_read_mem(obj_addrs[i] + OFFSET_LEVEL_ID, &level_id_ptr, 8))
            continue;

        if (!level_id_ptr) continue;

        // Read the level_id string content (first 64 chars max)
        char level_id_str[128];
        int32_t str_len = 0;
        if (!try_read_mem(level_id_ptr + 0x10, &str_len, 4))
            continue;
        if (str_len <= 0 || str_len > 100) continue;

        uint16_t str_buf[128] = {0};
        int read_len = str_len < 100 ? str_len * 2 : 100 * 2;
        if (!try_read_mem(level_id_ptr + 0x14, str_buf, read_len))
            continue;

        for (int c = 0; c < str_len && c < 100; c++)
            level_id_str[c] = (char)str_buf[c];
        level_id_str[str_len < 100 ? str_len : 100] = '\0';

        // Check if this object matches any registered metadata
        for (int m = 0; m < g_metadata_count; m++) {
            if (g_metadata_table[m].level_id &&
                strcmp(level_id_str, g_metadata_table[m].level_id) == 0) {
                // Match! Patch this object
                snprintf(buf, sizeof(buf),
                         "[MEMINJ] Patching object at 0x%lX: %s",
                         obj_addrs[i], level_id_str);
                log_write(buf);

                if (patch_beatmap_level_object(obj_addrs[i], &g_metadata_table[m]) == 0) {
                    patched++;
                }
                break;
            }
        }
    }

    snprintf(buf, sizeof(buf), "[MEMINJ] Successfully patched %d/%d objects",
             patched, g_metadata_count);
    log_write(buf);

    g_patching_done = patched;
    return NULL;
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

        if (sceKernelGetModuleInfo(modules[i], &info) < 0)
            continue;

        if (strstr(info.name, module_name) == NULL)
            continue;

        int seg_count = 0;
        for (int s = 0; s < 4 && s < max_segments; s++) {
            if (info.segmentInfo[s].size == 0)
                continue;

            segments[seg_count].base = (uint64_t)info.segmentInfo[s].address;
            segments[seg_count].size = info.segmentInfo[s].size;

            // Decode protection flags (OrbisKernelSegment: prot field)
            uint64_t prot = info.segmentInfo[s].prot;
            segments[seg_count].is_exec = (prot & 0x1) != 0;
            segments[seg_count].is_readable = (prot & 0x4) != 0;
            segments[seg_count].is_writable = (prot & 0x2) != 0;

            seg_count++;
        }
        return seg_count;
    }
    return -1;  // Module not found
}

// Search a memory region for a C string (needle) and return its address
static uint64_t search_for_string(uint64_t region_start, uint64_t region_size,
                                   const char* needle) {
    size_t needle_len = strlen(needle);
    if (needle_len == 0) return 0;

    // Scan in 4KB chunks for efficiency
    uint8_t buffer[4096];

    for (uint64_t offset = 0; offset < region_size; offset += sizeof(buffer)) {
        uint64_t addr = region_start + offset;
        size_t chunk_size = sizeof(buffer);
        if (offset + chunk_size > region_size)
            chunk_size = region_size - offset;

        if (!try_read_mem(addr, buffer, chunk_size))
            continue;

        // Simple byte-by-byte search within the chunk
        for (size_t i = 0; i <= chunk_size - needle_len; i++) {
            if (memcmp(buffer + i, needle, needle_len) == 0) {
                return addr + i;
            }
        }
    }
    return 0;  // Not found
}

// Search the module for the "BeatmapLevelSO" string, then find the
// Il2CppClass_1 struct that references it via the name field.
static int find_beatmap_level_so_klass(uint64_t* klass_out) {
    ModuleSegment segs[4];
    int seg_count = find_module_segments(MODULE_NAME, segs, 4);

    if (seg_count < 0) {
        log_write("[MEMINJ] ERROR: Could not find Il2CppUserAssemblies module");
        return -1;
    }

    // Search readable segments for the "BeatmapLevelSO" C string
    uint64_t class_string_addr = 0;
    for (int s = 0; s < seg_count; s++) {
        if (!segs[s].is_readable) continue;

        class_string_addr = search_for_string(
            segs[s].base, segs[s].size, CLASS_NAME);

        if (class_string_addr) {
            char buf[256];
            snprintf(buf, sizeof(buf),
                     "[MEMINJ] Found '%s' string at 0x%lX (segment %d: 0x%lX+0x%lX)",
                     CLASS_NAME, class_string_addr, s, segs[s].base, segs[s].size);
            log_write(buf);
            break;
        }
    }

    if (!class_string_addr) {
        log_write("[MEMINJ] ERROR: Could not find 'BeatmapLevelSO' string in module");
        return -1;
    }

    // Now search the module's readable segments for 8-byte pointers to this
    // string. At offset 0x10 of Il2CppClass_1, the `name` field should point
    // to the class string. The containing struct is BeatmapLevelSO_c.
    //
    // We search for: 8-byte aligned values == class_string_addr
    // When found at address P, check if P is at offset 0x10 from a struct start
    // (meaning P - 0x10 could be the start of Il2CppClass_1)

    for (int s = 0; s < seg_count; s++) {
        if (!segs[s].is_readable) continue;

        uint64_t scan_start = segs[s].base;
        uint64_t scan_end = scan_start + segs[s].size;

        // Scan in 8-byte steps
        for (uint64_t addr = scan_start; addr < scan_end; addr += 8) {
            uint64_t val = 0;
            if (!try_read_mem(addr, &val, 8)) continue;

            if (val == class_string_addr) {
                // Potential name field at Il2CppClass_1+0x10
                // The class struct would start at addr - 0x10
                uint64_t candidate = addr - 0x10;

                // Validate: namespaze at +0x18 should be a valid pointer
                uint64_t ns_ptr = 0;
                if (!try_read_mem(candidate + CLASS1_OFFSET_NAMESPAZE, &ns_ptr, 8))
                    continue;

                // The namespace should be readable (not null, within reasonable range)
                if (ns_ptr < 0x10000 || ns_ptr > 0x8000000000ULL)
                    continue;

                // Also check that +0x20 (byval_arg.data) looks reasonable
                uint64_t bv_ptr = 0;
                if (!try_read_mem(candidate + 0x20, &bv_ptr, 8))
                    continue;

                // Found a valid-looking Il2CppClass_1 / BeatmapLevelSO_c
                *klass_out = candidate;
                return 0;
            }
        }
    }

    log_write("[MEMINJ] ERROR: Could not find BeatmapLevelSO_c in module data");
    return -1;
}

// ══════════════════════════════════════════════════════════════════════════
// Memory Scanning for BeatmapLevelSO Objects
// ══════════════════════════════════════════════════════════════════════════

// Attempt to safely read memory. Returns 1 on success, 0 on fault.
// NOTE: On PS4, we validate the address range and then attempt a direct read.
// Unmapped addresses will cause a crash, so we validate ranges defensively.
static int try_read_mem(uint64_t addr, void* buf, size_t size) {
    // Bounds check: address must be in user-space range
    if (addr < 0x100000000ULL || addr > 0x8000000000ULL)
        return 0;
    if (addr + size > 0x8000000000ULL || addr + size < addr)
        return 0;

    memcpy(buf, (void*)addr, size);
    return 1;
}

// Scan for BeatmapLevelSO objects in process memory by looking for
// 8-byte-aligned values that match the klass pointer.
static int scan_for_beatmap_level_objects(uint64_t klass_addr,
                                          uint64_t* obj_addrs, int max_objs) {
    int found = 0;

    // We'll scan a broad range of process memory. To avoid excessive scanning,
    // we use a two-pass approach:
    // 1. Coarse scan: scan in 64KB steps, looking for klass_addr pattern
    // 2. Fine scan: within matching 64KB pages, scan each 8-byte aligned position

    char buf[256];
    snprintf(buf, sizeof(buf),
             "[MEMINJ] Scanning memory for objects (klass=0x%lX)...", klass_addr);
    log_write(buf);

    uint64_t scan_start = SCAN_START_ADDR;
    uint64_t scan_end = SCAN_END_ADDR;

    // Read one 64KB page at a time and search for the klass pointer within it
    uint8_t page[SCAN_STEP];

    for (uint64_t page_addr = scan_start;
         page_addr < scan_end && found < max_objs;
         page_addr += SCAN_STEP) {

        // Try to read the page
        if (!try_read_mem(page_addr, page, SCAN_STEP))
            continue;

        // Search the page for the klass address (8-byte aligned, little-endian)
        uint64_t klass_le = klass_addr;

        for (uint64_t offset = 0; offset < SCAN_STEP - 24; offset += 8) {
            uint64_t val = *(uint64_t*)(page + offset);

            if (val == klass_le) {
                uint64_t candidate_addr = page_addr + offset;

                // Validate this is actually a BeatmapLevelSO object
                if (validate_beatmap_level_object(candidate_addr)) {
                    obj_addrs[found++] = candidate_addr;

                    if (found >= max_objs) break;
                }
            }
        }
    }

    return found;
}

// Validate that a memory address looks like a BeatmapLevelSO object
// Checks: _version, _levelID pointer, _songName pointer
static int validate_beatmap_level_object(uint64_t addr) {
    // Check _version (should be a small positive int32)
    int32_t version = 0;
    if (!try_read_mem(addr + OFFSET_VERSION, &version, 4)) return 0;
    if (version < 1 || version > 100) return 0;  // Usually 1 or 2

    // Check _levelID — should be a valid pointer to a System_String_o
    uint64_t level_id_ptr = 0;
    if (!try_read_mem(addr + OFFSET_LEVEL_ID, &level_id_ptr, 8)) return 0;
    if (level_id_ptr < 0x100000000ULL || level_id_ptr > 0x8000000000ULL) return 0;

    // Quick check: the string klass should be valid
    uint64_t str_klass = 0;
    if (!try_read_mem(level_id_ptr, &str_klass, 8)) return 0;
    if (str_klass < 0x100000000ULL || str_klass > 0x8000000000ULL) return 0;

    // Check _songName — should be a valid pointer
    uint64_t song_name_ptr = 0;
    if (!try_read_mem(addr + OFFSET_SONG_NAME, &song_name_ptr, 8)) return 0;
    if (song_name_ptr < 0x100000000ULL || song_name_ptr > 0x8000000000ULL) return 0;

    // Check _songAuthorName — should be a valid pointer
    uint64_t author_ptr = 0;
    if (!try_read_mem(addr + OFFSET_SONG_AUTHOR, &author_ptr, 8)) return 0;
    if (author_ptr < 0x100000000ULL || author_ptr > 0x8000000000ULL) return 0;

    return 1;  // Looks valid
}

// ══════════════════════════════════════════════════════════════════════════
// String & Object Patching
// ══════════════════════════════════════════════════════════════════════════

// Convert a C string to UTF-16LE and write it into a managed String object.
// The new text MUST fit within the existing string's capacity (new length
// must be <= old length). Remaining capacity is zero-filled.
static int patch_il2cpp_string(uint64_t string_addr, const char* new_text) {
    if (!string_addr || !new_text) return -1;

    // Read the current string length to check capacity
    int32_t old_length = 0;
    if (!try_read_mem(string_addr + 0x10, &old_length, 4)) return -1;

    int new_length = (int)strlen(new_text);

    if (new_length > old_length) {
        // New text doesn't fit — truncate to the existing capacity.
        // This may clip the text slightly, but is safe.
        // TODO: For longer strings, allocate new managed strings via
        // il2cpp_string_new (requires finding the function address).
        new_length = old_length;
    }

    // Write the new length
    *(int32_t*)(string_addr + 0x10) = new_length;

    // Convert to UTF-16LE and write character by character
    // We write directly to the string's character buffer
    uint16_t* char_buf = (uint16_t*)(string_addr + 0x14);

    for (int i = 0; i < new_length; i++) {
        char_buf[i] = (uint16_t)(unsigned char)new_text[i];
    }

    // Zero-fill remaining capacity
    for (int i = new_length; i < old_length; i++) {
        char_buf[i] = 0;
    }

    return 0;
}

// Patch a BeatmapLevelSO object's fields with new metadata.
// Uses in-place string overwriting for safety (no GC interaction).
static int patch_beatmap_level_object(uint64_t obj_addr,
                                      const SongMetadataEntry* meta) {
    int patched = 0;
    char buf[256];

    // Patch _songName if provided
    if (meta->song_name && meta->song_name[0]) {
        uint64_t str_addr = 0;
        if (try_read_mem(obj_addr + OFFSET_SONG_NAME, &str_addr, 8) && str_addr) {
            if (patch_il2cpp_string(str_addr, meta->song_name) == 0) {
                patched++;
                snprintf(buf, sizeof(buf),
                         "[MEMINJ]   Patched _songName → '%s'", meta->song_name);
                log_write(buf);
            }
        }
    }

    // Patch _songAuthorName if provided
    if (meta->song_author_name && meta->song_author_name[0]) {
        uint64_t str_addr = 0;
        if (try_read_mem(obj_addr + OFFSET_SONG_AUTHOR, &str_addr, 8) && str_addr) {
            if (patch_il2cpp_string(str_addr, meta->song_author_name) == 0) {
                patched++;
                snprintf(buf, sizeof(buf),
                         "[MEMINJ]   Patched _songAuthorName → '%s'", meta->song_author_name);
                log_write(buf);
            }
        }
    }

    // Patch _levelID if provided (used for Addressables key matching)
    if (meta->level_id && meta->level_id[0]) {
        uint64_t str_addr = 0;
        if (try_read_mem(obj_addr + OFFSET_LEVEL_ID, &str_addr, 8) && str_addr) {
            if (patch_il2cpp_string(str_addr, meta->level_id) == 0) {
                patched++;
                snprintf(buf, sizeof(buf),
                         "[MEMINJ]   Patched _levelID → '%s'", meta->level_id);
                log_write(buf);
            }
        }
    }

    // Patch _songSubName if provided
    if (meta->song_sub_name && meta->song_sub_name[0]) {
        uint64_t str_addr = 0;
        if (try_read_mem(obj_addr + OFFSET_SONG_SUB_NAME, &str_addr, 8) && str_addr) {
            if (patch_il2cpp_string(str_addr, meta->song_sub_name) == 0) {
                patched++;
                snprintf(buf, sizeof(buf),
                         "[MEMINJ]   Patched _songSubName → '%s'", meta->song_sub_name);
                log_write(buf);
            }
        }
    }

    // Patch _levelAuthorName if provided
    if (meta->level_author_name && meta->level_author_name[0]) {
        uint64_t str_addr = 0;
        if (try_read_mem(obj_addr + OFFSET_LEVEL_AUTHOR, &str_addr, 8) && str_addr) {
            if (patch_il2cpp_string(str_addr, meta->level_author_name) == 0) {
                patched++;
                snprintf(buf, sizeof(buf),
                         "[MEMINJ]   Patched _levelAuthorName → '%s'", meta->level_author_name);
                log_write(buf);
            }
        }
    }

    snprintf(buf, sizeof(buf),
             "[MEMINJ] Object at 0x%lX: patched %d fields", obj_addr, patched);
    log_write(buf);

    return patched > 0 ? 0 : -1;
}
