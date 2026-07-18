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
} SongMetadataEntry;

void memory_inject_register(const SongMetadataEntry* entry);

#endif // MEMORY_INJECT_H
