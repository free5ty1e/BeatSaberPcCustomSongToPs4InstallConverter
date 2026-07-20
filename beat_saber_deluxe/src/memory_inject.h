#ifndef MEMORY_INJECT_H
#define MEMORY_INJECT_H

#include <stdint.h>

// ── Initialization ──────────────────────────────────────────────────────────
// Called from module_start after hooks are installed.
int memory_inject_init(void);

// ── Hook-Triggered Patching ────────────────────────────────────────────────
// Called from open_hook when a per-song bundle open is detected.
// Runs synchronously inside the open() callback.
// Checks internal timer (15s min since boot) before scanning.
int memory_inject_try_patch(void);

// ── Song Metadata ───────────────────────────────────────────────────────────
#define MAX_METADATA_ENTRIES 64

typedef struct {
    const char* level_id;
    const char* song_name;
    const char* song_sub_name;
    const char* song_author_name;
    const char* level_author_name;
    // Original strings for content-based patching (NULL = skip)
    const char* orig_song_name;
    const char* orig_song_sub_name;
    const char* orig_song_author_name;
} SongMetadataEntry;

void memory_inject_register(const SongMetadataEntry* entry);

// ── Retry Support (close() hook) ─────────────────────────────────────────────
// Returns non-zero if a memory injection retry is pending (klass was found
// but no BeatmapLevelSO objects were found during the initial scan).
// Called from the close hook to avoid re-scanning the full memory for klass.
int memory_inject_is_retry_pending(void);

#endif // MEMORY_INJECT_H
