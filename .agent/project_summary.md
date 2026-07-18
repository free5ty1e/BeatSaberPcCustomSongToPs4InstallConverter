# Project Summary: Beat Saber PS4 Custom Song Support
**Last Updated:** 2026-07-17
**Status:** 🟢 **v0.66 plugin / v0.52 pipeline** — Memory injection IMPLEMENTED and integrated. BeatmapLevelSO objects found in RAM by klass pointer scanning; string fields patched in-place with custom metadata. **Awaits PS4 hardware testing.**

## Current Blocker: Addressables Catalog Dual Validation

The game validates BOTH `m_BundleSize` AND `m_Crc` in the catalog for every loaded bundle. Either mismatch causes CE-34878-0 crash. This was confirmed via two separate tests (Exp 146, Exp 148).

**Catalog values:**
- `m_BundleSize`: **7,902,803 bytes** (exact)
- `m_Crc`: **`0xdc8b314f`** (CRC-32 of original bundle)

Both fields must match exactly. The catalog is loaded as plain JSON (not via `AssetBundle.LoadFromFile`), so the AFR plugin cannot redirect it.

## Viable Approaches — Option B BLOCKED, Memory Injection IN PROGRESS

### Option B: Uncompressed Block Injection — ❌ BLOCKED (Exp 157)

**Initial hypothesis:** The 49 uncompressed blocks (flag=0, each 131,072 bytes stored as raw data) are independent storage. Modifying their CONTENT affects CRC but NOT file_size, providing ~6.1 MB of free variables for pure CRC control.

**Critical finding (Exp 157):** Uncompressed blocks are part of a SHARED DECOMPRESSED STREAM that gets LZ4HC compressed as one unit. Modifying content in any block shifts downstream byte positions and alters all subsequent compression ratios, changing file_size by ~817-2,177 bytes.

**Conclusion:** Option B cannot achieve zero size impact. The approach is BLOCKED.

### Memory Injection — ✅ IMPLEMENTED (v0.66, Exp 167)

Memory injection approach now implemented and integrated into the plugin:
- **How it works:** Worker thread waits 30s for game init, then scans the IL2CPP heap via klass pointer matching
- **Finding objects:** Searches process memory for 8-byte-aligned `BeatmapLevelSO_c` klass pointers, validates by checking field integrity
- **Patching:** In-place overwrite of managed string fields (song name, artist, level ID) — new text must fit within original capacity
- **Metadata table:** 13 Rolling Stones replacement songs registered with custom names and artists

**Implementation Details:**
- `src/memory_inject.h` — Public API: `memory_inject_init()`, `memory_inject_register()`, `SongMetadataEntry`
- `src/memory_inject.cpp` — Full implementation (~550 lines) with thread, scanning, and patching
- Field offsets verified from actual IL2CPP dump (`BeatmapLevelSO_Fields` at `il2cpp.h:381156`)
- System_String format: klass(8) + monitor(8) + length(4) + UTF-16LE chars starting at +0x14

**Status:** ✅ Code complete. Awaiting PS4 hardware deployment and testing.

## Size Difference Root Cause (Exp 155)

+2,712 byte difference in rollingstones_pack_patched.bundle breaks down as:
- **+817 bytes:** Decompressed stream grows (original BeatmapLevelSO 440B → Espresso blob 1,257B)
- **~1,895 bytes:** Bundle rebuild overhead (object table shifts, compression ratio changes)

This confirms that ANY decompressed stream modification changes file_size. Uncompressed block injection was the only path to zero size impact — but it's blocked because those blocks aren't independent storage.

## Key Technical Findings

### CRC Correction via GF(2) Linear Algebra
- **Status:** ✅ Works for alignment padding bytes (proven in build_patched_pack_bundle.py achieving CRC=0xdc8b314f)
- **Limitation:** Only works when file_size changes (+2,712 bytes). Cannot maintain both size AND CRC via padding alone.

### UnityFS v8 Bundle Format (PS4 Beat Saber)
- Magic: `UnityFS\0`, version 8, LZ4HC compression (flag=3)
- Block structure: blocks_info → alignment padding → raw block data
- Blocks: 16 compressed + 49 uncompressed = 65 total
- **CRITICAL FINDING:** Uncompressed blocks are part of shared decompressed stream, NOT independent storage.

### Addressables CRC Validation Timing (Exp 160)
- **Finding:** Validates LAZILY — when bundle contents are accessed, NOT during LoadFromFile
- **Evidence:** Other bundles continued loading after pack bundle loaded with mismatched size/CRC
- **Implication:** Window exists for interception between load and access → memory injection feasible!

### IL2CPP Hook Analysis (Exp 161)
- **Finding:** All previous IL2CPP method hooks are DEAD ENDS
- **Reasons:** Constructor never fires, methods inlined by optimizer, conditional execution
- **Remaining options:** Per-song metadata bundles OR GoldHEN cheat code memory injection after game initialization

## Experiment Timeline (Recent Key Experiments)

| Exp | Date | What | Result |
|-----|------|------|--------|
| 139 | 07-16 | Pack redirect removed from PS4 | ✅ Original pack loads normally |
| 142 | 07-17 | CRC correction via GF(2) on alignment padding | ✅ CRC=0xdc8b314f (size +2,712B) |
| 146 | 07-17 | Test: correct CRC but wrong size | ❌ CE-34878-0 crash — size validated |
| 148 | 07-17 | Test: correct size but wrong CRC | ❌ CE-34878-0 crash — CRC validated |
| 153 | 07-17 | Size difference root cause analysis | ✅ Identified +817B stream growth |
| 155 | 07-17 | Option B decision: uncompressed block injection | ⏳ Implementing script |
| **157** | **07-17** | **Uncompressed block independence test** | **❌ BLOCKED — blocks are part of shared decompressed stream** |
| **160** | **07-17** | **Addressables CRC validation timing analysis** | **🟡 LAZY validation confirmed — memory injection feasible** |
| **161** | **07-17** | **IL2CPP hook analysis** | **🔍 All previous hooks dead ends — new approach needed** |
| **162** | **07-17** | **Memory injection prototype created** | **✅ Prototype verified working** |

## Working Tools & Scripts

| Tool | Location | Status |
|------|----------|--------|
| `build_patched_pack_bundle.py` | `tools/` | ✅ Proven — achieves CRC=0xdc8b314f via GF(2) on alignment padding |
| `memory_inject_test.py` | `development/scripts/` | ✅ Verified working — scanning/patching logic confirmed |
| `memory_inject_plugin.cpp` | `development/scripts/` | ⏳ Skeleton created — needs implementation |

## Next Steps (Priority Order)

1. **Implement heap finding logic** — Find IL2CPP heap base address in running game (Task #14)
2. **Implement field patching with IL2CPP runtime** — Allocate new managed strings and patch BeatmapLevelSO fields safely
3. **Test with simple patch** — Change song name only (doesn't require blob injection)
4. **Integrate into main plugin** — Add memory injection as fallback when pack bundle modification fails
5. **Deploy to PS4** — Test on actual hardware

## Active Knowledge Gaps

1. ~~CRC validation blocked~~ → Solved via GF(2) linear algebra (padding bytes)
2. ~~Size validation blocked~~ → Confirmed both size AND CRC must match simultaneously
3. ~~Uncompressed block independence~~ → **BLOCKED** — blocks are part of shared decompressed stream, not independent storage
4. Addressables CRC validation timing — **RESOLVED**: LAZY validation (when contents accessed)
5. IL2CPP hook targets — **RESOLVED**: All previous hooks dead ends; memory injection is new approach
6. Heap scanning implementation — IN PROGRESS (Task #14)

