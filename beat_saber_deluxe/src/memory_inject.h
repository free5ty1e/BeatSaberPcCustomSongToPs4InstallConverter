#ifndef MEMORY_INJECT_H
#define MEMORY_INJECT_H

#include <stdint.h>

// ── Initialization ──────────────────────────────────────────────────────────
// Called from module_start after hooks are installed.
// Creates a delayed worker thread that will scan for BeatmapLevelSO objects
// and patch them with custom metadata once the game has fully initialized.
int memory_inject_init(void);

// ── Song Metadata ───────────────────────────────────────────────────────────
// One entry per song slot that needs its metadata patched.
#define MAX_METADATA_ENTRIES 64

typedef struct {
    const char* level_id;           // e.g. "custom/espresso"
    const char* song_name;          // e.g. "Espresso"
    const char* song_sub_name;      // e.g. "" (optional)
    const char* song_author_name;   // e.g. "Sabrina Carpenter"
    const char* level_author_name;  // e.g. "Mapper Name" (optional)
} SongMetadataEntry;

// Register song metadata for patching.
// Call before memory_inject_init() to populate the patch table.
void memory_inject_register(const SongMetadataEntry* entry);

#endif // MEMORY_INJECT_H
