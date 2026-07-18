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
   - **Selected approach:** Thread-based delayed scanning + klass pointer matching
3. Implement memory injection prototype (Task #14) — **COMPLETED in v0.66 plugin**

### Implementation Status — v0.66 Plugin (Exp 167)

**Memory injection is now fully implemented and integrated into the plugin:**
- `src/memory_inject.h` / `src/memory_inject.cpp` — New files added to the plugin source
- Worker thread (pthread) waits 30s for game init, then scans
- Finds BeatmapLevelSO klass by searching Il2CppUserAssemblies for the "BeatmapLevelSO" string
- Scans process memory for objects with matching klass pointer
- Patches string fields in-place (UTF-16LE overwrite)

**Implementation Details:**
| Component | Approach |
|-----------|----------|
| Thread | `pthread_create` + `pthread_detach`, 30s delay via `usleep` |
| Klass finding | Search module data for "BeatmapLevelSO" C string, find Il2CppClass_1 references via name pointer |
| Object scanning | 64KB page reads from 0x100000000–0x800000000, search for 8-byte klass ptr values |
| Validation | Check _version(0x18) in range, _levelID(0x20) is valid string ptr, _songName(0x28) valid |
| String patching | Write new length at +0x10, UTF-16LE chars at +0x14, zero-fill remainder |
| Metadata table | 13 Rolling Stones slots mapped to custom names/artists |

### Key Design Decisions

1. **No heap scanning** — Instead of finding the GC heap base, we scan a broad memory range for klass pointers. Simpler but slower (mitigated by coarse 64KB page scanning).
2. **In-place string patching** — Avoids GC complexity by overwriting existing managed strings. New text MUST fit within original capacity.
3. **Thread-based delay** — 30s delay ensures Addressables has loaded the pack bundle and deserialized BeatmapLevelSO objects before we scan.
4. **Level ID matching** — We match objects by their _levelID string (e.g., "startmeup") against a registered metadata table, rather than positional assumptions.

### Next Steps

1. **PS4 hardware testing** — Deploy v0.66 and verify:
   - Game doesn't crash on launch
   - Custom song names/artists display correctly in song selection
   - Mode selector still works (5 preview modes)
   - All 13 Rolling Stones songs show correct metadata
2. **Edge case handling** — Handle songs where custom name is longer than original (alloc new string)
3. **Cover image patching** — Replace album art in BeatmapLevelSO (Sprite* at offset 0x70)
4. **Expand to Billie Eilish + Lizzo packs** — Register metadata for all 32 slots

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
