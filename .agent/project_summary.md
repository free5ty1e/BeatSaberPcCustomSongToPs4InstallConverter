# Project Summary: Beat Saber PS4 Custom Song Support
**Last Updated:** 2026-07-17
**Status:** 🟡 **v0.65 plugin / v0.52 pipeline** — Pack bundle metadata patching blocked by Addressables catalog dual validation (size + CRC). Uncompressed block injection approach BLOCKED — blocks are part of shared decompressed stream, not independent storage.

## Current Blocker: Addressables Catalog Dual Validation

The game validates BOTH `m_BundleSize` AND `m_Crc` in the catalog for every loaded bundle. Either mismatch causes CE-34878-0 crash. This was confirmed via two separate tests (Exp 146, Exp 148).

**Catalog values:**
- `m_BundleSize`: **7,902,803 bytes** (exact)
- `m_Crc`: **`0xdc8b314f`** (CRC-32 of original bundle)

## Viable Approaches — Both Blocked or In Progress

### Option B: Uncompressed Block Injection — ❌ BLOCKED (Exp 157)

**Initial hypothesis:** The 49 uncompressed blocks (flag=0, each 131,072 bytes stored as raw data) are independent storage. Modifying their CONTENT affects CRC but NOT file_size, providing ~6.1 MB of free variables for pure CRC control.

**Critical finding (Exp 157):** Uncompressed blocks are part of a SHARED DECOMPRESSED STREAM that gets LZ4HC compressed as one unit. Modifying content in any block shifts downstream byte positions and alters all subsequent compression ratios, changing file_size by ~817-2,177 bytes.

**Conclusion:** Option B cannot achieve zero size impact. The approach is BLOCKED.

### Memory Injection — 🟡 In Progress (Exp 158)

If pack bundle modification fails entirely, fallback to memory injection:
- Patch BeatmapLevelSO in RAM after Addressables loads the pack bundle
- Bypass catalog CRC validation entirely
- Exp 142 showed game continued loading other bundles after pack bundle loaded — suggests window for interception exists

**Feasibility check needed:**
1. When does Addressables validate CRC? (during LoadFromFile or after?)
2. Can we hook into the deserialization process on PS4?
3. Where is BeatmapLevelSO stored in memory after deserialization?

## Size Difference Root Cause (Exp 155)

+2,712 byte difference in rollingstones_pack_patched.bundle breaks down as:
- **+817 bytes:** Decompressed stream grows (original BeatmapLevelSO 440B → Espresso blob 1,257B)
- **~1,895 bytes:** Bundle rebuild overhead (object table shifts, compression ratio changes)

This confirms that ANY decompressed stream modification changes file_size. Uncompressed block injection was the only path to zero size impact — but it's blocked because those blocks aren't independent storage.

## Key Technical Findings

### CRC Correction via GF(2) Linear Algebra
- **Status:** ✅ Works for alignment padding bytes (proven in build_patched_pack_bundle.py achieving CRC=0xdc8b314f)
- **Limitation:** Only works when file_size changes (+2,712 bytes). Cannot maintain both size AND CRC via padding alone.
- **Theory:** CRC is linear over GF(2): `table[a XOR b] = table[a] XOR table[b]`. Enables computing exact padding values for target CRC.

### UnityFS v8 Bundle Format (PS4 Beat Saber)
- Magic: `UnityFS\0`, version 8, LZ4HC compression (flag=3)
- Block structure: blocks_info → alignment padding → raw block data
- Blocks: 16 compressed + 49 uncompressed = 65 total
- Each block max size: 131,072 bytes

### BeatmapLevelSO Object Location
- Original location in decompressed stream: offset ~72,620
- Original blob size: ~440 bytes
- Espresso blob size (with 5 modes): ~1,257 bytes (+817 byte difference)

## Experiment Timeline (Recent Key Experiments)

| Exp | Date | What | Result |
|-----|------|------|--------|
| 139 | 07-16 | Pack redirect removed from PS4 | ✅ Original pack loads normally |
| 142 | 07-17 | CRC correction via GF(2) on alignment padding | ✅ CRC=0xdc8b314f (size +2,712B) |
| 146 | 07-17 | Test: correct CRC but wrong size | ❌ CE-34878-0 crash — size validated |
| 148 | 07-17 | Test: correct size but wrong CRC | ❌ CE-34878-0 crash — CRC validated |
| 153 | 07-17 | Size difference root cause analysis | ✅ Identified +817B stream growth |
| 155 | 07-17 | Option B decision: uncompressed block injection | ⏳ Implementing script |
| **157** | **07-17** | **Uncompressed block independence test** | **❌ BLOCKED — blocks are part of shared decompressed stream; modifying content changes file_size by ~817-2,177 bytes due to cascading compression ratio effects** |
| 158 | 07-17 | Memory injection approach planning | 🔬 Researching feasibility |

## Working Tools & Scripts

| Tool | Location | Status |
|------|----------|--------|
| `build_patched_pack_bundle.py` | `tools/` | ✅ Proven — achieves CRC=0xdc8b314f via GF(2) on alignment padding |
| `crc_corrector.py` | `development/scripts/` | ⚠️ Built but needs refinement for convergence |
| `build_espresso_final_v2.py` | `development/scripts/` | ❌ Timed out — stream injection changes file_size |

## Next Steps (Priority Order)

1. **Research memory injection feasibility** — Can we patch BeatmapLevelSO in RAM after Addressables load? This bypasses catalog validation entirely.
2. **If memory injection works:** Implement hook in GoldHEN plugin to intercept Addressables loading and patch objects in memory.
3. **If memory injection fails:** Explore other approaches (per-song bundle modification, etc.).
4. **Documentation enforcement** — Create Claude hooks plugin for auto documentation updates.

## Active Knowledge Gaps

1. ~~CRC validation blocked~~ → Solved via GF(2) linear algebra (padding bytes)
2. ~~Size validation blocked~~ → Confirmed both size AND CRC must match simultaneously
3. ~~Uncompressed block independence~~ → **BLOCKED** — blocks are part of shared decompressed stream, not independent storage
4. Memory injection feasibility — need to research Unity Addressables loading pipeline on PS4
5. Whether uncompressed block content can be safely modified without corrupting game data structures

