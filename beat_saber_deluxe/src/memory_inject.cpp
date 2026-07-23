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
 *     0x10: _stringLength (int32_t)    — length in UTF-16 code units  [standard IL2CPP]
 *     0x14: _firstChar (uint16_t)      — first char, rest follow as array
 *   NOTE: PS4 mono may have 16-byte monitor, pushing _stringLength to 0x18.
 *         Detected dynamically via offset probing in pattern matcher.
 *
 * v0.8020 — Scan metadata region (±256MB around 0x293280000), 10s timeout
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

// Scan the global-metadata.dat mmap region where string literals are stored.
// Metadata base found at ~0x293280000 in v0.8003. Scan ±256MB around it.
// This is much faster than scanning the full 4GB–17GB range.
#define SCAN_START_ADDR 0x000000291000000ULL   // ~10.5GB — below metadata
#define SCAN_END_ADDR   0x000000296000000ULL   // ~10.8GB — above metadata
#define SCAN_STEP       0x10000ULL    // 64KB pages
#define SCAN_TIMEOUT_US 10000000ULL   // 10 seconds — should be enough for 512MB
#define PRE_SWEEP_STEP  0x10000ULL    // 64KB — same page size for pre-sweep

// ── BeatmapLevelSO Field Offsets (from il2cpp dump) ──────────────────────
#define OFFSET_VERSION         0x18   // int32
#define OFFSET_LEVEL_ID        0x20   // System_String_o*
#define OFFSET_SONG_NAME       0x28   // System_String_o*
#define OFFSET_SONG_SUB_NAME   0x30   // System_String_o*
#define OFFSET_SONG_AUTHOR     0x38   // System_String_o*
#define OFFSET_LEVEL_AUTHOR    0x40   // System_String_o*

// ── Il2CppClass_1 field offsets ─────────────────────────────────────────
#define CLASS1_OFFSET_NAME         0x10  // const char* — class name

// Detected System_String._stringLength offset (set by pattern matcher).
// Standard IL2CPP: 0x10. PS4 mono may use 0x18 (16-byte monitor field).
static int g_strlen_offset = 0x10;

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
static uint64_t g_metadata_base = 0;      // Address of patch global-metadata.dat in memory
static uint64_t g_cached_klass = 0;       // Cached klass addr for close-hook retry
static int g_retry_pending = 0;           // 1 = retry pending on close()
static volatile int g_wide_scan = 0;       // 1 = scan full address range (retry only)

// ── Synchronous scan timeout ─────────────────────────────────────────────
#define SYNCHRONOUS_SCAN_TIMEOUT_US 2000000ULL  // 2 seconds max in hook callback

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
static int patch_strings_by_content(uint64_t scan_start, uint64_t scan_end);
static int find_module_segments(const char* module_name,
                                ModuleSegment* segments, int max_segments);
static int try_read_mem(uint64_t addr, void* buf, size_t size);

// ── Pattern-Based Object Finding ─────────────────────────────────────────
// Find BeatmapLevelSO klass by scanning memory for objects matching the known
// field layout. Scans two ranges:
//   1. 16MB-4GB      - covers the PS4 module/system space (0x80000000-0x90000000)
//   2. 8GB-8.25GB    - covers the IL2CPP GC heap (mmap'd at high addresses)
// The GC heap range is derived from the object scanner's SCAN_START/END_ADDR.
#define PATTERN_SCAN_MIN    0x1000000ULL      // 16MB — start below possible heap
#define PATTERN_SCAN_MAX    0x100000000ULL    // 4GB — lower range (~65520 pages)
#define PATTERN_SCAN_MIN2   0x200000000ULL    // 8GB — GC heap start (SCAN_START_ADDR)
#define PATTERN_SCAN_MAX2   0x210000000ULL    // 8.25GB — GC heap end (SCAN_END_ADDR)
// 64KB pages to stay within PS4 stack limit (typically 256KB per thread).
// 1MB pages overflow the stack and cause every try_read_mem to fault.
#define PATTERN_SCAN_STEP 0x10000ULL      // 64KB pages (safe for stack)

static int find_beatmap_level_objects_by_pattern(uint64_t* klass_out) {
    int scan_count = 0, mapped_pages = 0;
    int chk_klass = 0, chk_version = 0, chk_ptrs = 0, chk_strlen = 0;
    uint8_t page[PATTERN_SCAN_STEP];

    // Scan two ranges: module/system space (16MB-4GB) and GC heap (8GB-8.25GB)
    struct { uint64_t start; uint64_t end; } ranges[] = {
        { PATTERN_SCAN_MIN,  PATTERN_SCAN_MAX },   // low range: module/system
        { PATTERN_SCAN_MIN2, PATTERN_SCAN_MAX2 },   // high range: GC heap
    };
    const int num_ranges = sizeof(ranges) / sizeof(ranges[0]);

    for (int r = 0; r < num_ranges; r++) {
        for (uint64_t page_addr = ranges[r].start; page_addr < ranges[r].end; page_addr += PATTERN_SCAN_STEP) {
            scan_count++;
            if (!try_read_mem(page_addr, page, PATTERN_SCAN_STEP))
                continue;
            mapped_pages++;

            for (uint64_t offset = 0; offset < PATTERN_SCAN_STEP - 64; offset += 32) {
            uint64_t klass_ptr = *(uint64_t*)(page + offset + 0x00);
            int32_t version   = *(int32_t*)(page + offset + 0x18);
            uint64_t lid      = *(uint64_t*)(page + offset + 0x20);
            uint64_t sn       = *(uint64_t*)(page + offset + 0x28);
            uint64_t an       = *(uint64_t*)(page + offset + 0x38);

            // Accept klass in module space (0x80000000-0x90000000) or GC heap (0x200000000+).
            if ((klass_ptr < 0x80000000ULL || klass_ptr > 0x90000000ULL) &&
                (klass_ptr < 0x200000000ULL || klass_ptr > 0x210000000ULL)) continue;
            chk_klass++;
            if (version < 1 || version > 50) continue;
            chk_version++;
            if (lid < 0x1000000ULL || lid > 0x8000000000ULL) continue;
            if (sn  < 0x1000000ULL || sn  > 0x8000000000ULL) continue;
            if (an  < 0x1000000ULL || an  > 0x8000000000ULL) continue;
            chk_ptrs++;

            // Reject false positives: klass must NOT equal string pointers.
            // Real BeatmapLevelSO has klass -> data segment (0x84AC0000+) and
            // lid/sn/an -> GC heap (0x200000000+). False positives have klass==lid.
            if (klass_ptr == lid || klass_ptr == sn || klass_ptr == an) continue;

            // Debug: dump hex header of lid pointer to understand System_String layout on PS4
            // Shows the first 32 bytes (4 uint64 values) at lid:
            //   [0] = bytes 0-7  (klass ptr)
            //   [1] = bytes 8-15 (monitor)
            //   [2] = bytes 16-23 (standard: _stringLength at 0x10 + _firstChar at 0x14)
            //   [3] = bytes 24-31 (alt: _stringLength at 0x18 + _firstChar at 0x1C)
            {
                uint64_t obj_addr = page_addr + offset;
                uint64_t lid_hdr[4] = {0};
                if (try_read_mem(lid, lid_hdr, 32)) {
                    char buf[512];
                    snprintf(buf, sizeof(buf),
                             "[MEMINJ] OBJ[%d]: obj=0x%lX klass=0x%lX ver=%d "
                             "lid=0x%lX sn=0x%lX an=0x%lX | "
                             "lid[0]=0x%016lX [1]=0x%016lX [2]=0x%016lX [3]=0x%016lX",
                             chk_ptrs, obj_addr, klass_ptr, version,
                             lid, sn, an,
                             lid_hdr[0], lid_hdr[1], lid_hdr[2], lid_hdr[3]);
                    meminj_log(buf);
                    // Also log what a 32-bit read at each candidate offset gives
                    for (int oi = 0; oi < 4; oi++) {
                        int32_t val = 0;
                        try_read_mem(lid + (size_t[]){0x10, 0x14, 0x18, 0x1C}[oi], &val, 4);
                        char obuf[128];
                        snprintf(obuf, sizeof(obuf),
                                 "  LID OFFSET 0x%lX -> %d (0x%08X)",
                                 (unsigned long)(size_t[]){0x10, 0x14, 0x18, 0x1C}[oi],
                                 val, (uint32_t)val);
                        meminj_log(obuf);
                    }
                }
            }

            // Try multiple string length offsets to handle PS4's unknown System_String layout.
            // Standard IL2CPP: _stringLength at 0x10, but PS4 mono may have a larger
            // monitor field (16 bytes) pushing it to 0x18. Probe several candidates.
            static const int strlen_offsets[] = { 0x10, 0x14, 0x18, 0x1C };
            int found_offset = -1;
            for (int si = 0; si < (int)(sizeof(strlen_offsets)/sizeof(strlen_offsets[0])); si++) {
                int32_t lid_len = 0, sn_len = 0;
                if (!try_read_mem(lid + strlen_offsets[si], &lid_len, 4)) continue;
                if (!try_read_mem(sn  + strlen_offsets[si], &sn_len,  4)) continue;
                if (lid_len <= 0 || lid_len > 255) continue;
                if (sn_len  <= 0 || sn_len  > 255) continue;
                found_offset = strlen_offsets[si];
                break;
            }
            // Diagnostic: on first few candidates, log all offset attempts
            if (chk_strlen == 0 && found_offset < 0) {
                for (int si = 0; si < (int)(sizeof(strlen_offsets)/sizeof(strlen_offsets[0])); si++) {
                    int32_t lid_len = 0, sn_len = 0;
                    int lid_ok = try_read_mem(lid + strlen_offsets[si], &lid_len, 4);
                    int sn_ok  = try_read_mem(sn  + strlen_offsets[si], &sn_len,  4);
                    char dbuf[256];
                    snprintf(dbuf, sizeof(dbuf),
                             "[MEMINJ] OFFSET PROBE: lid=0x%lX offset=0x%X "
                             "lid_read=%d lid_len=%d sn_read=%d sn_len=%d",
                             lid, strlen_offsets[si],
                             lid_ok, lid_len, sn_ok, sn_len);
                    meminj_log(dbuf);
                }
            }
            if (found_offset < 0) continue;
            if (chk_strlen == 0) {
                char obuf[128];
                snprintf(obuf, sizeof(obuf),
                         "[MEMINJ] String length offset detected: 0x%X (standard=0x10, PS4_alt=0x18)",
                         found_offset);
                meminj_log(obuf);
            }
            g_strlen_offset = found_offset;
            chk_strlen++;

            *klass_out = klass_ptr;
            return 0;
        }
    }
}

    // Log diagnostics
    {   char buf[256];
        snprintf(buf, sizeof(buf),
                 "[MEMINJ] Pattern diag: %d pages (%d mapped). "
                 "klass=%d ver=%d ptrs=%d strlen=%d strlen_offset=0x%X",
                 scan_count, mapped_pages,
                 chk_klass, chk_version, chk_ptrs, chk_strlen, g_strlen_offset);
        meminj_log(buf);
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
    meminj_log("[MEMINJ] Initialized (synchronous string content search, fires on pack load)");
    if (g_metadata_count == 0) {
        meminj_log("[MEMINJ] WARNING: No metadata registered");
    }
    return 0;
}

int memory_inject_is_retry_pending(void) {
    return g_retry_pending;
}

// Called from open_hook when pack bundle is detected.
// Scans memory synchronously for UTF-16LE song name strings and patches them.
// Runs with a 2-second timeout to avoid blocking the hook callback.
// Only scans ONCE — does not retry on redirect (strings not in memory at startup).
// Returns 0 if scan completed, -1 if already done.
int memory_inject_try_patch(void) {
    // If already done (succeeded or failed), skip entirely
    if (g_patching_done) return -1;

    // Lock to prevent re-entry
    if (__sync_lock_test_and_set(&g_patching_done, 1)) {
        return -1;  // Another caller already doing this
    }

    char buf[256];
    snprintf(buf, sizeof(buf),
             "[MEMINJ] String content scan (%d patterns, 2s timeout)",
             g_metadata_count);
    meminj_log(buf);

    // Install signal handlers for this scan
    struct sigaction sa, old_segv, old_bus;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = mem_fault_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sigaction(SIGSEGV, &sa, &old_segv);
    sigaction(SIGBUS, &sa, &old_bus);

    // Run the string content scan with the full address range
    int result = patch_strings_by_content(SCAN_START_ADDR, SCAN_END_ADDR);

    // Restore signal handlers
    sigaction(SIGSEGV, &old_segv, NULL);
    sigaction(SIGBUS, &old_bus, NULL);

    if (result > 0) {
        g_patching_done = result;
        snprintf(buf, sizeof(buf),
                 "[MEMINJ] Scan complete: patched %d strings", result);
        meminj_log(buf);
    } else {
        // Mark as done — do NOT retry on redirect (strings not in memory at startup)
        // The scan found nothing because song name strings are only loaded
        // when the song list UI renders, not during pack bundle loading.
        g_patching_done = -1;
        meminj_log("[MEMINJ] Scan complete: no strings found (strings likely not loaded yet)");
    }

    return 0;
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

// ══════════════════════════════════════════════════════════════════════════
// global-metadata.dat Magic Search
// ══════════════════════════════════════════════════════════════════════════

// Magic bytes for global-metadata.dat: 0xFAB11BAF
// "BeatmapLevelSO" is at file offset 0x23cb6e in the PATCH metadata (version 31).
// At runtime the metadata is mmap'd into memory — finding the magic gives us
// its base address, then we compute the string address as base + file_offset.
#define METADATA_MAGIC_BYTES "\xAF\x1B\xB1\xFA"
#define METADATA_MAGIC_LEN   4
#define BEATMAP_LEVEL_SO_STRING_OFFSET 0x23CB6EULL

// Search for patch global-metadata.dat (version 31) across all readable memory.
// Returns the base address (where magic is found), or 0 if not found.
// Validates by checking version field == 31 and string count > 1M.
static uint64_t search_for_patch_metadata(void) {
    // Scan all readable memory at 64KB granularity (matches pattern scan step)
    for (uint64_t page_addr = 0x1000000ULL; page_addr < 0x2000000000ULL; page_addr += PATTERN_SCAN_STEP) {
        // First check if ANY of this page is readable
        uint64_t probe = 0;
        if (!try_read_mem(page_addr, &probe, 8)) continue;

        // Page is readable — scan it for the magic at 4KB granularity
        for (uint64_t offset = 0; offset < PATTERN_SCAN_STEP; offset += 4096) {
            uint64_t chunk_addr = page_addr + offset;

            // Quick pre-check: look for first magic byte (0xAF)
            uint8_t first_byte = 0;
            if (!try_read_mem(chunk_addr, &first_byte, 1)) continue;
            if (first_byte != 0xAF) continue;

            // Read the full 4096-byte chunk to check
            uint8_t chunk[4096];
            if (!try_read_mem(chunk_addr, chunk, sizeof(chunk))) continue;

            for (size_t i = 0; i <= sizeof(chunk) - METADATA_MAGIC_LEN; i++) {
                if (memcmp(chunk + i, METADATA_MAGIC_BYTES, METADATA_MAGIC_LEN) == 0) {
                    // Found magic — validate it's the patch metadata (version 31)
                    int32_t version = 0;
                    if (i + 8 <= sizeof(chunk)) {
                        version = *(int32_t*)(chunk + i + 4);
                    } else {
                        if (!try_read_mem(chunk_addr + i + 4, &version, 4)) continue;
                    }
                    if (version != 31) continue;

                    // Sanity check: string count should be > 1M for the patch metadata
                    int32_t str_count = 0;
                    if (i + 32 <= sizeof(chunk)) {
                        str_count = *(int32_t*)(chunk + i + 28);
                    } else {
                        if (!try_read_mem(chunk_addr + i + 28, &str_count, 4)) continue;
                    }
                    if (str_count < 1000000) continue;

                    // Verified! This is the patch global-metadata.dat
                    return chunk_addr + i;
                }
            }
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
    uint64_t metadata_base = 0;
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
        // String not found in module — try finding it via global-metadata.dat magic
        char msgbuf[256];
        meminj_log("[MEMINJ] String not in module — searching for global-metadata.dat magic...");
        metadata_base = search_for_patch_metadata();
        if (metadata_base) {
            class_string_addr = metadata_base + BEATMAP_LEVEL_SO_STRING_OFFSET;
            g_metadata_base = metadata_base;
            snprintf(msgbuf, sizeof(msgbuf),
                     "[MEMINJ] Found metadata at 0x%lX, class string at 0x%lX",
                     metadata_base, class_string_addr);
            meminj_log(msgbuf);
        }
    }

    if (!class_string_addr) {
        // String not found in any segment — pattern matcher will be tried by caller
        return -1;
    }

    // Search for 8-byte pointers to this string (the `name` field in Il2CppClass_1)
    // Scan ALL segments — Seg[1] (data segment at 0x84AC0000) has is_readable=0
    // but try_read_mem can still read it via signal handlers. The signal handler
    // safely catches faults on genuinely inaccessible pages.
    for (int s = 0; s < seg_count; s++) {
        if (segs[s].base == 0 || segs[s].size == 0) continue;
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

    // Fallback: search GC heap and metadata range for the pointer
    // Il2CppClass struct may be dynamically allocated outside module segments
    if (metadata_base) {
        uint8_t fb_page[PATTERN_SCAN_STEP]; // 64KB buffer
        uint64_t fb_val;

        // Define broader search ranges
        struct { uint64_t start; uint64_t end; } fb_ranges[] = {
            { 0x200000000ULL, 0x210000000ULL },          // GC heap
            { metadata_base - 0x100000,                   // ±1MB around metadata
              metadata_base + 0x1000000 },
        };
        for (int f = 0; f < 2; f++) {
            for (uint64_t page_addr = fb_ranges[f].start; page_addr < fb_ranges[f].end; page_addr += PATTERN_SCAN_STEP) {
                if (!try_read_mem(page_addr, fb_page, sizeof(fb_page))) continue;
                for (size_t i = 0; i < sizeof(fb_page) / sizeof(uint64_t); i++) {
                    if (((uint64_t*)fb_page)[i] != class_string_addr) continue;
                    uint64_t addr = page_addr + i * sizeof(uint64_t);
                    uint64_t candidate = addr - 0x10;
                    uint64_t ns_ptr = 0;
                    if (!try_read_mem(candidate + 0x18, &ns_ptr, 8)) continue;
                    if (ns_ptr < 0x10000 || ns_ptr > 0x8000000000ULL) continue;
                    if (!try_read_mem(candidate + 0x20, &fb_val, 8)) continue;
                    // Dump Il2CppClass struct bytes to verify field layout
                    uint64_t klass_hdr[4] = {0};
                    if (try_read_mem(candidate, klass_hdr, 32)) {
                        char dbuf[512];
                        snprintf(dbuf, sizeof(dbuf),
                                 "[MEMINJ] KLASS_STRUCT addr=0x%lX "
                                 "[0x00]=0x%lX (klass) "
                                 "[0x08]=0x%lX (image) "
                                 "[0x10]=0x%lX (name) "
                                 "[0x18]=0x%lX (ns/td)",
                                 candidate,
                                 klass_hdr[0], klass_hdr[1],
                                 klass_hdr[2], klass_hdr[3]);
                        meminj_log(dbuf);
                    }
                    *klass_out = candidate;
                    return 0;
                }
            }
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

    // Signal handlers are installed once at the start of memory_inject_try_patch
    // and restored at the end. Here we just use sigsetjmp to catch any faults.
    int result = 0;
    if (sigsetjmp(g_mem_jmpbuf, 1) == 0) {
        memcpy(buf, (void*)addr, size);
        result = 1;
    }
    return result;
}

static int scan_for_beatmap_level_objects(uint64_t klass_addr,
                                          uint64_t* obj_addrs, int max_objs) {
    int found = 0;
    int raw_matches = 0;
    int pages_read = 0;
    int pages_failed = 0;
    char buf[256];
    snprintf(buf, sizeof(buf), "[MEMINJ] Scanning (klass=0x%lX)...", klass_addr);
    meminj_log(buf);

    // Define scan ranges: [primary GC heap, extended near metadata, FULL if retry]
    struct { uint64_t start; uint64_t end; } scan_ranges[] = {
        { SCAN_START_ADDR, SCAN_END_ADDR },
        { g_metadata_base ? g_metadata_base - 0x200000 : 0,  // 2MB before metadata
          g_metadata_base ? g_metadata_base + 0x1000000 : 0 }, // 16MB after
        { g_wide_scan && g_metadata_base ? SCAN_END_ADDR : 0,   // Gap: end of GC heap
          g_wide_scan && g_metadata_base ? g_metadata_base - 0x200000 : 0 }, // → metadata - 2MB
    };
    int range_count = g_wide_scan ? 3 : (g_metadata_base ? 2 : 1);

    uint8_t page[SCAN_STEP];
    uint64_t scan_start_time = sceKernelGetProcessTime();  // microseconds
    for (int r = 0; r < range_count && found < max_objs; r++) {
        snprintf(buf, sizeof(buf), "[MEMINJ] Range %d: 0x%lX - 0x%lX (%d ranges)",
                 r, scan_ranges[r].start, scan_ranges[r].end, range_count);
        meminj_log(buf);

        for (uint64_t page_addr = scan_ranges[r].start;
             page_addr < scan_ranges[r].end && found < max_objs;
             page_addr += SCAN_STEP) {

            if (!try_read_mem(page_addr, page, SCAN_STEP)) {
                pages_failed++;
                continue;
            }
            pages_read++;

            // Check timeout every 256 pages (~16MB)
            if ((pages_read & 0xFF) == 0) {
                uint64_t now = sceKernelGetProcessTime();
                if (now - scan_start_time > SCAN_TIMEOUT_US) {
                    snprintf(buf, sizeof(buf),
                             "[MEMINJ] SCAN TIMEOUT after %d pages (%dms), aborting",
                             pages_read, (int)((now - scan_start_time) / 1000));
                    meminj_log(buf);
                    goto scan_done;
                }
            }

            // Log first page of each range for diagnostics
            if (pages_read == 1 || (pages_read & 0xFFF) == 0) {
                uint64_t first_val = *(uint64_t*)(page + 0);
                uint64_t second_val = *(uint64_t*)(page + 8);
                snprintf(buf, sizeof(buf),
                         "[MEMINJ] PAGE 0x%lX: [0]=0x%lX [8]=0x%lX (want 0x%lX)%s",
                         page_addr, first_val, second_val, klass_addr,
                         first_val == klass_addr ? " MATCH!" : "");
                meminj_log(buf);
            }

            for (uint64_t offset = 0; offset < SCAN_STEP - 24; offset += 8) {
                uint64_t val = *(uint64_t*)(page + offset);
                if (val == klass_addr) {
                    raw_matches++;
                    uint64_t candidate = page_addr + offset;
                    snprintf(buf, sizeof(buf),
                             "[MEMINJ] RAW MATCH at 0x%lX (page=0x%lX off=0x%lX)",
                             candidate, page_addr, offset);
                    meminj_log(buf);
                    if (validate_beatmap_level_object(candidate)) {
                        obj_addrs[found++] = candidate;
                        if (found >= max_objs) break;
                    }
                }
            }
        }
    }

scan_done:
    // Log diagnostic: how many raw klass matches vs validated
    snprintf(buf, sizeof(buf), "[MEMINJ] Klass diag: %d raw matches, %d validated (%d pages read, %d failed)",
             raw_matches, found, pages_read, pages_failed);
    meminj_log(buf);

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
    if (lid < 0x1000000ULL || lid > 0x8000000000ULL) return 0;

    // _songName must be a valid pointer
    uint64_t sn = 0;
    if (!try_read_mem(addr + OFFSET_SONG_NAME, &sn, 8)) return 0;
    if (sn < 0x1000000ULL || sn > 0x8000000000ULL) return 0;

    // _songAuthorName must be a valid pointer
    uint64_t an = 0;
    if (!try_read_mem(addr + OFFSET_SONG_AUTHOR, &an, 8)) return 0;
    if (an < 0x1000000ULL || an > 0x8000000000ULL) return 0;

    return 1;
}

// ══════════════════════════════════════════════════════════════════════════
// String & Object Patching
// ══════════════════════════════════════════════════════════════════════════

static int patch_il2cpp_string(uint64_t string_addr, const char* new_text) {
    if (!string_addr || !new_text) return -1;

    int32_t old_length = 0;
    if (!try_read_mem(string_addr + g_strlen_offset, &old_length, 4)) return -1;

    int new_length = (int)strlen(new_text);
    if (new_length > old_length) {
        new_length = old_length;  // Truncate if doesn't fit
    }

    // Write new length
    *(int32_t*)(string_addr + g_strlen_offset) = new_length;

    // Write UTF-16LE characters
    uint16_t* char_buf = (uint16_t*)(string_addr + g_strlen_offset + 4);
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

// ══════════════════════════════════════════════════════════════════════════
// Direct String Search & Patch (No klass required)
// ══════════════════════════════════════════════════════════════════════════

// Search for song name/author strings by their UTF-16LE content and patch
// them directly, without needing to find the BeatmapLevelSO objects.
static int patch_strings_by_content(uint64_t scan_start, uint64_t scan_end) {
    int patched = 0;
    char buf[256];

    // ── Build lookup tables ──────────────────────────────────────────────
    uint8_t length_lut[256];                   // length→pattern_index+1 (0=none)
    int     pat_meta[64];                      // metadata index per pattern
    uint64_t pat_16[64];                       // UTF-16LE uint64 pattern
    uint64_t pat_8[64];                        // UTF-8    uint64 pattern
    int pat_count = 0;
    memset(length_lut, 0, sizeof(length_lut));
    memset(pat_16, 0, sizeof(pat_16));
    memset(pat_8, 0, sizeof(pat_8));

    for (int m = 0; m < g_metadata_count && pat_count < 64; m++) {
        const char* orig = g_metadata_table[m].orig_song_name;
        if (!orig || !orig[0]) continue;
        int len = (int)strlen(orig);
        if (len < 1 || len > 254) continue;

        uint64_t p16 = (uint64_t)(uint32_t)len;
        p16 |= ((uint64_t)(uint16_t)(unsigned char)orig[0]) << 32;
        if (len > 1) p16 |= ((uint64_t)(uint16_t)(unsigned char)orig[1]) << 48;

        uint64_t p8 = (uint64_t)(uint32_t)len;
        p8 |= ((uint64_t)(unsigned char)orig[0]) << 32;
        p8 |= ((uint64_t)(unsigned char)orig[1]) << 40;
        p8 |= ((uint64_t)(unsigned char)orig[2]) << 48;
        p8 |= ((uint64_t)(unsigned char)orig[3]) << 56;

        int dup = 0;
        for (int p = 0; p < pat_count; p++)
            if (pat_16[p] == p16 && strcmp(orig, g_metadata_table[pat_meta[p]].orig_song_name) == 0)
                { dup = 1; break; }

        if (!dup) {
            pat_16[pat_count] = p16;
            pat_8[pat_count]  = p8;
            pat_meta[pat_count] = m;
            length_lut[len] = (uint8_t)(pat_count + 1);
            pat_count++;
        }
    }

    snprintf(buf, sizeof(buf), "[MEMINJ] String scan (opt): %d patterns", pat_count);
    meminj_log(buf);
    if (pat_count == 0) return 0;

    // ── Main scan loop with timeout ──────────────────────────────────────
    uint8_t page[SCAN_STEP];
    uint64_t scan_start_time = sceKernelGetProcessTime();
    int pages_read = 0;
    for (uint64_t page_addr = scan_start; page_addr < scan_end; page_addr += SCAN_STEP) {
        if (!try_read_mem(page_addr, page, SCAN_STEP)) continue;
        pages_read++;

        // Check timeout every 256 pages (~16MB)
        if ((pages_read & 0xFF) == 0) {
            uint64_t now = sceKernelGetProcessTime();
            if (now - scan_start_time > SYNCHRONOUS_SCAN_TIMEOUT_US) {
                char timeout_buf[128];
                snprintf(timeout_buf, sizeof(timeout_buf),
                         "[MEMINJ] String scan TIMEOUT after %d pages (%dms)",
                         pages_read, (int)((now - scan_start_time) / 1000));
                meminj_log(timeout_buf);
                break;
            }
        }

        for (uint64_t off = 0; off < SCAN_STEP - 8; off += 8) {
            uint64_t page_val = *(uint64_t*)(page + off);
            uint32_t str_len = (uint32_t)(page_val & 0xFFFFFFFFULL);
            if (str_len >= 256) continue;
            int lut_idx = (int)length_lut[str_len] - 1;
            if (lut_idx < 0) continue;

            int fmt = 0;  // 0 = none, 1 = UTF-16LE, 2 = UTF-8
            if (page_val == pat_16[lut_idx]) fmt = 1;
            else if (page_val == pat_8[lut_idx]) fmt = 2;
            if (!fmt) continue;

            int m = pat_meta[lut_idx];
            const char* orig = g_metadata_table[m].orig_song_name;
            int orig_len = (int)strlen(orig);
            if (orig_len < 1) continue;

            int match = 1;
            if (fmt == 1) {
                for (int c = 0; c < orig_len && match; c++) {
                    uint16_t e = (uint16_t)(unsigned char)orig[c];
                    uint16_t a = *(uint16_t*)(page + off + 4 + c * 2);
                    if (a != e) match = 0;
                }
            } else {
                for (int c = 0; c < orig_len && match; c++) {
                    uint8_t e = (uint8_t)(unsigned char)orig[c];
                    uint8_t a = *(uint8_t*)(page + off + 4 + c);
                    if (a != e) match = 0;
                }
            }
            if (!match) continue;

            // ── Patch in-place ────────────────────────────────────────────
            const char* new_val = g_metadata_table[m].song_name;
            int new_len = new_val ? (int)strlen(new_val) : 0;
            uint64_t data_addr = page_addr + off + 4;

            if (new_len < 1 || new_len > orig_len) {
                snprintf(buf, sizeof(buf), "[MEMINJ] String skip 0x%lX: '%s' (len %d/%d)",
                         data_addr, orig, new_len, orig_len);
                meminj_log(buf);
                continue;
            }

            uint32_t new_len_le = (uint32_t)new_len;
            if (fmt == 1) {  // UTF-16LE
                memcpy((void*)(page_addr + off), &new_len_le, 4);
                for (int c = 0; c < new_len; c++) {
                    uint16_t ch = (uint16_t)(unsigned char)new_val[c];
                    memcpy((void*)(data_addr + c * 2), &ch, 2);
                }
            } else {  // UTF-8
                memcpy((void*)(page_addr + off), &new_len_le, 4);
                memcpy((void*)(data_addr), new_val, new_len);
            }

            snprintf(buf, sizeof(buf),
                     "[MEMINJ] String patched 0x%lX: '%s' -> '%s' (%s)",
                     data_addr, orig, new_val, fmt == 1 ? "UTF16" : "UTF8");
            meminj_log(buf);
            patched++;
        }
    }
    return patched;
}
