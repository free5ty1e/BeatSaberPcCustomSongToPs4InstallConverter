---
name: ps4-il2cpp-metadata-loading
description: "How IL2CPP loads class metadata on PS4: class name strings live in global-metadata.dat, NOT in the compiled module PRX"
metadata:
  type: reference
---

# PS4 IL2CPP Metadata Loading

## Key Discovery

**The class name strings (like "BeatmapLevelSO") are NOT compiled into the Il2CppUserAssemblies module PRX.** They are loaded at runtime from `global-metadata.dat`, a separate 8MB metadata file. This contradicts the common assumption that IL2CPP compiles class metadata into the generated C++ module.

## Evidence from PS4 Dump

| File | Size | Contains "BeatmapLevelSO"? |
|------|------|---------------------------|
| `Il2CppUserAssemblies.prx` (app) | 36.6 MB | **NO** |
| `global-metadata.dat` (app) | 8 MB | **NO** (base game only) |
| `global-metadata.dat` (patch) | 8 MB | **YES** at offset 0x23CB6E |

The string was found ONLY in the **patch** version of `global-metadata.dat`, confirming that BeatmapLevelSO is part of a DLC pack, not the base game.

## How IL2CPP Metadata Works

In Unity's IL2CPP, class metadata is stored in two places:

1. **Generated C++ code** (`Il2CppUserAssemblies` module) — Contains `Il2CppClass_1` struct instances with embedded pointers to class name strings, field definitions, method tables, etc.

2. **global-metadata.dat** — A binary file containing all the STRING DATA that the struct instances point to. Class names, field names, method names, type information — all stored here as packed string tables.

At runtime:
1. IL2CPP loads `global-metadata.dat` into memory (typically via `mmap` or `read`)
2. The `Il2CppClass_1` instances in the module have their `name` field set to point into the loaded metadata buffer
3. The class **metadata structs** are in the module's data section, but the **string data** they reference is in the metadata mapping

## Implications for Memory Injection

### String Search Approach is Fundamentally Wrong

Since v0.66, the memory injection code tried to find the "BeatmapLevelSO" klass by:
1. Searching the Il2CppUserAssemblies module segments for the C string "BeatmapLevelSO"
2. Finding 8-byte pointers to that string (the klass's `name` field)

This CANNOT work on this game version because:
- The string is NOT in the module at all
- The string is in `global-metadata.dat`, loaded at a different memory address
- The klass's `name` pointer points into the metadata mapping, not the module

### Alternative: Pattern-Based Klass Finding

Without the ability to find the klass via string search, the approach shifts to:
1. Scan the GC heap for objects matching BeatmapLevelSO field layout (version in [1,50], valid string pointers)
2. Extract the klass pointer from the first valid object
3. Use that klass to scan for all matching objects

This approach doesn't depend on where class names are stored — it identifies objects by their memory structure.

### Alternative: Search for the String in the Metadata Mapping

Since `global-metadata.dat` IS mapped into process memory, the string "BeatmapLevelSO" IS somewhere in the address space. Searching for it directly:
- Provides the metadata base address
- Can be used to navigate the metadata to find class definitions
- But requires understanding the IL2CPP metadata format (version-specific)

### Heap Address Uncertainty

On PS4, the IL2CPP GC heap address is **not guaranteed** to be at any specific location. The assumed range of `0x200000000–0x400000000` (8GB–16GB) is UNVERIFIED. The pattern matcher now scans a wide range (1GB–32GB) to find objects.

## See Also

- [[memory-injection-addressables-bypass]]
- [[ps4-memory-layout-for-module-scanning]]
- [[plugin-architecture]]
