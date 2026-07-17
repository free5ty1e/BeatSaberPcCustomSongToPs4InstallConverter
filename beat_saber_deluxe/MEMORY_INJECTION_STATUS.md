# Memory Injection — Status Report (2026-07-17)

## Executive Summary

**Status:** ✅ Viable fallback approach identified and partially implemented  
**Blocker Resolved:** Option B (uncompressed block injection) BLOCKED due to shared decompressed stream  
**New Approach:** Memory injection bypasses Addressables CRC validation entirely  

## Progress Summary

### Completed
- [x] **Research Phase** — Determined Addressables validates CRC LAZILY (when contents accessed, not during LoadFromFile)
- [x] **IL2CPP Hook Analysis** — Confirmed all previous IL2CPP method hooks are dead ends (inlined/never called)
- [x] **Test Script Created** — `development/scripts/memory_inject_test.py` verifies scanning and patching logic
- [x] **Plugin Skeleton Created** — `development/scripts/memory_inject_plugin.cpp` provides framework
- [x] **Implementation Plan Documented** — `development/scripts/memory_scan_implementation.md` details approach

### In Progress
- [ ] Heap scanning implementation (find IL2CPP heap base, scan for BeatmapLevelSO objects)
- [ ] Field patching with proper IL2CPP string allocation
- [ ] Integration with AFR plugin bundle loading hooks
- [ ] Testing on PS4 hardware

## Key Technical Findings

### Addressables CRC Validation Timing
**Finding:** Addressables validates CRC LAZILY — when bundle contents are accessed, NOT during LoadFromFile.  
**Evidence:** Exp 142 showed other bundles continued loading after pack bundle loaded with mismatched size/CRC.  
**Implication:** Window exists for interception between load and use → memory injection is feasible!

### Uncompressed Blocks Finding (Exp 157)
**Finding:** 49 uncompressed blocks are part of shared decompressed stream, NOT independent storage.  
**Impact:** Option B BLOCKED — any blob injection changes file_size by ~817-2,177 bytes due to cascading compression ratio effects.  
**Conclusion:** Cannot achieve both size=7,902,803 AND CRC=0xdc8b314f simultaneously via bundle modification.

### Memory Injection Approach
**Concept:** Patch BeatmapLevelSO in RAM after Addressables loads the pack bundle but BEFORE validation runs.  
**Mechanism:** 
1. Hook into bundle loading pipeline (after load completes)
2. Scan IL2CPP heap for BeatmapLevelSO objects by type signature
3. Patch their fields (song name, artist, modes) with Espresso metadata
4. Return patched object to game — bypasses catalog validation entirely

## Implementation Details

### BeatmapLevelSO Field Offsets (from il2cpp dump)
```c
#define FIELD_VERSION         0x18   // int32
#define FIELD_LEVEL_ID        0x20   // string*
#define FIELD_SONG_NAME       0x28   // string*
#define FIELD_ARTIST_NAME     0x38   // string*
```

### IL2CPP Type IDs
- BeatmapLevelSO: 11680
- System.String: 4
- System.Single (float): 7
- System.Int32: 5

### Heap Scanning Algorithm
```c
for (uint64_t objAddr = heapBase; objAddr < heapEnd; objAddr += sizeof(Il2CppObjectHeader)) {
    Il2CppObjectHeader* obj = (Il2CppObjectHeader*)objAddr;
    
    if (obj->klass == BEATMAP_LEVEL_SO_VTABLE) {
        // Found a BeatmapLevelSO! Patch it.
        patch_beatmap_level((BeatmapLevelSO*)obj);
    }
}
```

## Next Steps (Priority Order)

1. **Implement heap finding logic** — Find IL2CPP heap base address in running game
2. **Implement field patching** — Allocate new managed strings and patch BeatmapLevelSO fields
3. **Test with simple patch** — Change song name only (doesn't require blob injection)
4. **Integrate into main plugin** — Add memory injection as fallback when pack bundle modification fails
5. **Deploy to PS4** — Test on actual hardware

## Files Created/Updated

### Development Scripts
- `development/scripts/memory_inject_test.py` — Test script (✅ verified working)
- `development/scripts/memory_inject_plugin.cpp` — Plugin skeleton (⏳ needs implementation)
- `development/scripts/memory_scan_implementation.md` — Implementation plan document

### Knowledge Base Updates
- `.agent/llm-wiki-knowledge-base/addressables-crc-validation-timing.md` — CRC validation timing analysis
- `.agent/llm-wiki-knowledge-base/memory-injection-addressables-bypass.md` — Memory injection approach details
- `.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md` — Added Exp 157-160

### Project Documentation
- `.agent/project_summary.md` — Updated with latest findings (Option B blocked, memory injection viable)
- `README.md` — Updated status section
- `CHANGELOG-PIPELINE.md` — Updated to v1.49
- `CHANGELOG-PLUGIN.md` — Updated (still v0.65 — no plugin changes yet)

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Heap layout changes between game versions | Medium | High | Make heap scanning configurable/patchable |
| String patching breaks reference counting | Medium | High | Use IL2CPP runtime API for string allocation |
| Hook timing issues (bundle not fully loaded) | Medium | Medium | Add delay or callback mechanism |
| Memory corruption from unsafe patches | Low | Critical | Validate object integrity after patching |

## Conclusion

Memory injection is a **viable fallback approach** when pack bundle modification is blocked by dual validation. The key insight is that Addressables validates CRC LAZILY, giving us a window to intercept and patch objects in RAM before the game uses them.

Next priority: Implement heap scanning logic and test with simple field patching (song name only).
