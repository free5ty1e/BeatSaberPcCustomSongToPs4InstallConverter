---
name: beatmap-levelso-in-patch-metadata
description: "BeatmapLevelSO string exists in patch global-metadata.dat (version 31), not in app version (24) or module segments"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 5c5e7f21-d234-40f8-a25e-8f4c10e1928e
---

The class name "BeatmapLevelSO" as a contiguous C string is stored **only** in the **patch** global-metadata.dat file (version 31, file offset 0x23cb6e, string index 84256). It does NOT exist in:
- The app global-metadata.dat (version 24) — only has "BeatmapLevel" and "LevelSO" separately
- Any module segment of Il2CppUserAssemblies (0x806C0000-0x85018000)

Previous search attempts failed because:
- `search_for_string()` in `find_beatmap_level_so_klass()` only searched within module segments
- Early metadata analysis checked the app metadata (version 24) instead of the patch metadata (version 31)

**Runtime approach:** Find the patch metadata in memory by scanning for magic bytes 0xFAB11BAF (little-endian: AF 1B B1 FA), validate version == 31 and string count > 1M, then compute string_addr = metadata_base + 0x23CB6E. Pass this to the existing Il2CppClass pointer search in the data segment.

**Why:** IL2CPP with global-metadata stores class type definitions in the metadata file. The generated C++ code references the string within the metadata via the `name` field of `Il2CppClass`. The metadata file is mmap'd into memory by the runtime at startup.

**Why:** IL2CPP with global-metadata stores class type definitions in the metadata file. The generated C++ code references the string within the metadata via the `name` field of `Il2CppClass`. The metadata file is mmap'd into memory by the runtime at startup.
