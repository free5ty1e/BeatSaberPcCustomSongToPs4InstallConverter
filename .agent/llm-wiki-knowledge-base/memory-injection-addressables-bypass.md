---
name: memory-injection-addressables-bypass
description: "Memory injection approach to bypass Addressables catalog CRC validation by patching BeatmapLevelSO in RAM after bundle loads"
metadata:
  type: reference
---

# Memory Injection — Addressables Catalog Bypass Approach

## Summary

When pack bundle modification is blocked by dual validation (m_BundleSize AND m_Crc), fallback to **memory injection**: patch BeatmapLevelSO in RAM after Addressables loads the pack bundle but BEFORE validation runs. This bypasses catalog CRC validation entirely.

**Key Insight:** Evidence suggests Addressables validates CRC LAZILY — when bundle contents are accessed, NOT during LoadFromFile. This makes memory injection feasible.

## Experimental Evidence (Exp 142)

- Game continued loading OTHER bundles after pack bundle loaded
- If CRC validation blocked LoadFromFile, game would crash immediately
- Therefore, validation must happen later — when BeatmapLevelSO is accessed
- **Window exists for interception** between load and use

## Implementation Strategy

### Hook Points to Investigate

1. **`SerializedFile.ReadObject`** — Unity's serialization layer (most promising)
2. **`MonoScriptableObject.InstantiateFromData`** — ScriptableObject instantiation
3. **Addressables internal deserialization methods** — Bundle loading pipeline
4. **`AssetBundle.LoadFromFile`** — Already hooked by AFR plugin, but may be too late

### Patching BeatmapLevelSO in RAM

Once we intercept deserialization:
1. Identify BeatmapLevelSO objects being loaded from pack bundle
2. Replace their metadata (song name, artist, modes) with Espresso data
3. Ensure object references remain valid after patching
4. Return patched object to game — bypasses catalog validation entirely

### Feasibility Check

**Requirements:**
- Find valid IL2CPP hook targets in Beat Saber's code
- Understand BeatmapLevelSO memory layout (TypeTree)
- Implement safe memory patching on PS4 (handle memory protections)
- Test with simple metadata change before full Espresso blob injection

**Risks:**
- Hook targets may be inlined or optimized away by IL2CPP
- Memory layout may vary between game versions
- Patched objects may need to maintain references to other loaded assets

## Status

**Viable fallback approach.** Requires:
1. Research Unity Addressables CRC validation timing on PS4 (Task #12) — **COMPLETED**
   - Evidence strongly suggests LAZY validation (when contents accessed, not during LoadFromFile)
   - Window exists for interception between load and access
2. Identify IL2CPP hook points in Beat Saber code (Task #13) — **COMPLETED**
   - All previous IL2CPP method hooks are DEAD ENDS:
     - Constructor hook: Never fires for AssetBundle-deserialized objects (Unity uses raw memory copy)
     - get_previewDifficultyBeatmapSets(): Inlined by IL2CPP optimizer
     - SetData/SetContent hooks: Conditional or crash on install
   - **Remaining option:** GoldHEN cheat code memory injection after game initialization OR hook into bundle loading pipeline
3. Implement memory injection prototype (Task #14) — **IN PROGRESS**

### Implementation Progress

**Test Script Created:** `development/scripts/memory_inject_test.py`
- Simulates IL2CPP heap with BeatmapLevelSO objects
- Tests scanning logic to find objects by type signature
- Tests patching logic for field modification
- **Status:** ✅ Logic verified working

**Plugin Skeleton Created:** `development/scripts/memory_inject_plugin.cpp`
- Framework for actual plugin implementation
- Includes hook installation and logging infrastructure
- **Status:** ⏳ Needs heap scanning implementation

### Key Implementation Details

**BeatmapLevelSO Field Offsets (from il2cpp dump):**
```c
#define FIELD_VERSION         0x18   // int32
#define FIELD_LEVEL_ID        0x20   // string*
#define FIELD_SONG_NAME       0x28   // string*
#define FIELD_ARTIST_NAME     0x38   // string*
#define FIELD_PREVIEW_SETS    0x98   // PreviewDifficultyBeatmapSet[]*
```

**IL2CPP Type IDs:**
- BeatmapLevelSO: 11680
- System.String: 4
- System.Single (float): 7
- System.Int32: 5

### Next Steps

1. **Implement heap scanning logic** — Find IL2CPP heap base and scan for BeatmapLevelSO objects by type signature
2. **Test with simple patch** — Change song name only (doesn't require blob injection)
3. **Integrate into main plugin** — Add memory injection as fallback when pack bundle modification fails
4. **Deploy to PS4** — Test on actual hardware

See [[song-metadata-addressables-structure#Memory-Injection-Approach-Viable-Fallback]] for full details.

---

## Critical Findings — Uncompressed Blocks NOT Independent Storage (Exp 157)

**Initial hypothesis:** The 49 uncompressed blocks (flag=0, each 131,072 bytes stored as raw data) are independent storage. Modifying their CONTENT affects CRC but NOT file_size, providing ~6.1 MB of free variables for pure CRC control.

**Actual behavior (Exp 157):** Uncompressed blocks are part of a SHARED DECOMPRESSED STREAM that gets LZ4HC compressed as one unit. Modifying content in any block shifts downstream byte positions and alters all subsequent compression ratios, changing file_size by ~817-2,177 bytes.

**Conclusion:** Option B (uncompressed block injection) CANNOT achieve zero size impact. The approach is BLOCKED.

### Technical Details

The 49 "uncompressed" blocks in UnityFS v8 bundle are NOT stored independently:
- They're part of a concatenated decompressed stream
- This stream gets LZ4HC compressed as one unit (flag=3)
- Modifying content in any block shifts all downstream byte positions
- Cascading compression ratio changes affect file_size by ~817-2,177 bytes

### Implications for Pack Bundle Patching

**Before Exp 157:**
- Assumed uncompressed blocks were independent storage (fixed size, no cascading)
- Thought we could use them for pure CRC control without size impact
- Option B was the primary viable approach

**After Exp 157:**
- Uncompressed blocks affect downstream compression ratios
- Any blob injection changes file_size by ~817-2,177 bytes (not zero)
- Option B blocked — cannot achieve both size=7,902,803 AND CRC=0xdc8b314f simultaneously

### Size Difference Breakdown (Exp 155)

When modifying pack bundle's decompressed stream:
| Source | Bytes | Explanation |
|--------|-------|-------------|
| Blob replacement | +817 | Original BeatmapLevelSO (440B) → Espresso blob (1,257B) |
| Bundle rebuild overhead | ~1,895 | Object table shifts, compression ratio changes, alignment |
| **Total** | **+2,712** | Matches measured difference in rollingstones_pack_patched.bundle |

Decompressed stream sizes:
- Original: 8,511,228 bytes
- Patched: 8,512,045 bytes (+817 bytes)

This confirms ANY modification to the decompressed stream changes file_size. Uncompressed block injection was the only path to zero size impact — but it's blocked because those blocks aren't independent storage.

---

## Addressables Catalog Dual Validation (Exp 146, 148)

The game validates BOTH `m_BundleSize` AND `m_Crc` in the catalog for every loaded bundle. Either mismatch causes CE-34878-0 crash.

**Catalog values:**
- `m_BundleSize`: **7,902,803 bytes** (exact)
- `m_Crc`: **`0xdc8b314f`** (CRC-32 of original bundle)

Both fields must match exactly. The catalog is loaded as plain JSON (not via `AssetBundle.LoadFromFile`), so the AFR plugin cannot redirect it.

### Experimental Evidence

**Test 1: Correct CRC, Wrong Size (Exp 146)**
- Bundle: rollingstones_pack_patched.bundle (size=7,905,515 bytes, CRC=`0xdc8b314f`)
- Result: ❌ CE-34878-0 crash
- Conclusion: Size validation enforced even with correct CRC

**Test 2: Correct Size, Wrong CRC (Exp 148)**
- Bundle: espresso_pack_patched.bundle (size=7,902,803 bytes, CRC=`0x7218b959`)
- Result: ❌ CE-34878-0 crash
- Conclusion: CRC validation enforced even with correct size

### Solution Requirements

To successfully modify the pack bundle, we MUST:
1. Keep file_size EXACTLY at 7,902,803 bytes (no change)
2. Match CRC exactly to `0xdc8b314f`

Both conditions must be met simultaneously. This is extremely difficult because:
- Any blob injection changes stream size by +817 bytes
- Compression ratio changes cascade into additional size changes (~1,895 bytes)
- Total size change: ~2,712 bytes — cannot be eliminated with current approaches

### Viable Approaches (After Exp 157)

**Option A: Find Unused Regions to Remove** — Search original bundle for unused/padding bytes, remove ~2,712 bytes elsewhere to compensate. Risky — may corrupt bundle structure if we remove wrong bytes.

**Option B: Uncompressed Block Injection** — ~~BLOCKED~~ (Exp 157 confirmed blocks are part of shared decompressed stream).

**Option C: Memory Injection** — Patch BeatmapLevelSO in RAM after Addressables load (bypasses catalog entirely). **Currently the most viable approach.**

See [[pack-bundle-patching#Current-Best-Alternative]] for details.
