---
name: addressables-crc-validation-timing
description: "When Unity's Addressables system validates bundle CRC on PS4 — lazy vs immediate validation"
metadata:
  type: reference
---

# Addressables CRC Validation Timing on PS4

## Summary

**Hypothesis:** Unity's Addressables system validates bundle CRC LAZILY — when bundle contents are actually accessed, NOT during `AssetBundle.LoadFromFile`. This makes memory injection feasible as a fallback approach if pack bundle modification is blocked.

**Evidence (Exp 142):** Game continued loading OTHER bundles after pack bundle loaded with mismatched size/CRC. If validation happened during LoadFromFile, game would crash immediately — no other bundles would load.

## Experimental Evidence

### Test 1: Correct CRC, Wrong Size
- **Bundle:** `rollingstones_pack_patched.bundle` (size=7,905,515 bytes, CRC=`0xdc8b314f`)
- **Result:** ❌ CE-34878-0 crash — size validation enforced

### Test 2: Correct Size, Wrong CRC
- **Bundle:** `espresso_pack_patched.bundle` (size=7,902,803 bytes, CRC=`0x7218b959`)
- **Result:** ❌ CE-34878-0 crash — CRC validation enforced

### Critical Observation
**Both tests crashed**, but the key insight is that OTHER bundles continued loading AFTER the pack bundle loaded in both cases. This suggests:
- Validation happens, but NOT during LoadFromFile
- Validation happens LATER — when bundle contents are accessed
- Window exists for memory injection between load and access

## Addressables Loading Pipeline (Hypothesis)

```
1. Game requests pack bundle via Addressables.LoadAssetAsync()
2. Addressables calls AssetBundle.LoadFromFile() → reads file from disk
3. During LoadFromFile, Unity performs INITIAL validation:
   - Check if bundle exists (yes)
   - Parse UnityFS header (magic, version, flags)
   - Decompress blocks_info to get block metadata
   - BUT: Does NOT validate CRC yet (lazy validation)
4. Game continues loading other bundles in background
5. When game ACTUALLY accesses BeatmapLevelSO from pack bundle:
   - Addressables validates CRC against catalog
   - If CRC/size mismatch → CE-34878-0 crash
   - If valid → deserialize objects and return to game
```

## Memory Injection Feasibility

**If validation is LAZY (happens when contents are accessed):**

✅ **MEMORY INJECTION IS FEASIBLE!**

Window for interception:
```
LoadFromFile → [DECOMPRESS] → [VALIDATE CRC?] → Deserialize Objects → Return to Game
                                    ↑
                              WE CAN PATCH HERE
```

Hook points to investigate:
1. **After decompression, before validation** — patch in memory
2. **During object deserialization** — intercept BeatmapLevelSO creation
3. **After validation passes** — patch objects before game uses them

## Next Steps for Research

1. **Verify hypothesis by checking if other bundles load successfully**
   - If they do, CRC validation is definitely LAZY

2. **Find Addressables source code or documentation for PS4**
   - Unity's Addressables API may have platform-specific behavior

3. **Analyze pack bundle loading sequence in Beat Saber**
   - When exactly is the pack bundle loaded?
   - What triggers validation?

4. **Look for existing modding tools that bypass Addressables CRC**
   - PS4 modding community may have solutions

## Related Knowledge Base Pages

- [[song-metadata-addressables-structure]] — Overall Addressables structure and catalog format
- [[pack-bundle-patching]] — Pack bundle modification approaches and blockers
- [[memory-injection-addressables-bypass]] — Memory injection fallback approach details

