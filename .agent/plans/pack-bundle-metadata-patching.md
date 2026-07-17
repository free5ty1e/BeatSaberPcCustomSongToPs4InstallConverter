# Plan: Pack Bundle Metadata Patching for Beat Saber PS4

**Created:** 2026-07-17  
**Status:** 🟡 In Progress — Option B exploration continuing  
**Last Updated:** 2026-07-17

---

## Problem Statement

We need to modify the Rolling Stones pack bundle (`therollingstones_pack_assets_all_a99482a8a3da9e991e5ae36f2fea209c.bundle`) to display custom song metadata (Espresso by Sabrina Carpenter with 5 modes) in-game.

**Blocker:** Addressables catalog validates BOTH `m_BundleSize` (7,902,803 bytes) AND `m_Crc` (`0xdc8b314f`). Either mismatch causes CE-34878-0 crash.

---

## Approach Options (Priority Order)

### Option A: Memory Injection (Fallback — Not Yet Explored)
**Status:** ⏳ Researched, prototype created  
**Concept:** Patch BeatmapLevelSO in RAM after Addressables loads the pack bundle but BEFORE validation runs. Bypasses catalog CRC validation entirely.  
**Feasibility:** ✅ Viable — Addressables validates CRC LAZILY (when contents accessed, not during LoadFromFile). Window exists for interception.  
**Status:** Will explore if Option B fails.

### Option B: Uncompressed Block Injection with Size Compensation
**Status:** 🟡 In Progress — Exploring fully before moving on  
**Concept:** Modify uncompressed blocks (flag=0) to inject Espresso blob, then compensate for size change by finding unused regions in original bundle to remove equivalent bytes.  
**Blocker Discovered (Exp 157):** Uncompressed blocks are NOT independent storage — they're part of a shared decompressed stream. Modifying content changes file_size by ~817-2,177 bytes due to cascading compression ratio effects.  
**Current Strategy:** Find unused/padding regions in original bundle to remove ~2,712 bytes to compensate for size increase from blob injection.

### Option C: Alternative Approaches
**Status:** 🔬 Research phase if Options A and B fail  
**Ideas:**
- Per-song bundle modification (add display metadata to per-song bundles)
- GoldHEN cheat code memory patches after game initialization
- Modify catalog JSON (if possible via hooking)

---

## Option B: Detailed Exploration Plan

### Phase 1: Analyze Size Difference Root Cause (COMPLETED — Exp 155)
**Finding:** +2,712 byte difference breaks down as:
| Source | Bytes | Explanation |
|--------|-------|-------------|
| Blob replacement | +817 | Original BeatmapLevelSO (440B) → Espresso blob (1,257B) |
| Bundle rebuild overhead | ~1,895 | Object table shifts, compression ratio changes, alignment |

**Conclusion:** ANY modification to decompressed stream changes file_size. Cannot inject into stream without size impact.

### Phase 2: Identify Uncompressed Block Behavior (COMPLETED — Exp 157)
**Finding:** Uncompressed blocks are part of shared decompressed stream, NOT independent storage.  
**Impact:** Modifying content affects downstream compression ratios → file_size changes by ~817-2,177 bytes.

### Phase 3: Find Unused Regions to Remove (IN PROGRESS — Current Work)
**Goal:** Find ~2,712 bytes in original bundle that can be safely removed without affecting functionality.  
**Approach:** Search for padding, unused regions, or redundant data in original bundle structure.

### Phase 4: Implement Size Compensation (FUTURE)
**Goal:** Remove identified unused bytes while maintaining CRC correctness.  
**Challenge:** Removing bytes shifts all subsequent byte positions → breaks GF(2) weight matrices used for CRC correction.

### Phase 5: Test on PS4 (FUTURE)
**Goal:** Deploy patched bundle to PS4 and verify both size AND CRC match catalog simultaneously.

---

## Key Technical Constraints

1. **Dual Validation:** Both `m_BundleSize` AND `m_Crc` must match catalog values exactly.
2. **Catalog Location:** `aa/catalog.json` — loaded as plain JSON, cannot be redirected via AFR plugin.
3. **CRC Correction Method:** GF(2) linear algebra on alignment padding bytes (proven to work for CRC alone).
4. **Size Constraint:** Must maintain exactly 7,902,803 bytes (original bundle size).

---

## Timeline & Milestones

| Date | Milestone | Status |
|------|-----------|--------|
| 2026-07-15 | Discover dual validation blocker | ✅ Complete |
| 2026-07-17 | Confirm CRC correction works (size +2,712B) | ✅ Complete |
| 2026-07-17 | Test size validation enforcement | ✅ Complete |
| 2026-07-17 | Analyze size difference root cause (Exp 155) | ✅ Complete |
| 2026-07-17 | Test uncompressed block independence (Exp 157) | ✅ Complete — BLOCKED |
| 2026-07-17 | Research memory injection approach (Exp 160-162) | ✅ Prototype created |
| **TODAY** | Continue exploring Option B fully | 🟡 In Progress |
| TBD | Deploy working solution to PS4 | ⏳ Pending |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Cannot find unused regions to remove | High | Critical | Fallback to Option A (memory injection) |
| Removing bytes breaks CRC correction weights | Medium | High | Recalculate weights after size changes |
| Memory injection fails (validation timing wrong) | Low | Medium | Have Option C as backup |

---

## Next Immediate Actions

1. **Search original bundle for unused/padding regions** (~2,712 bytes to remove)
2. **Implement size compensation logic** in build script
3. **Recalculate GF(2) weight matrices** after size changes
4. **Test on PS4** if powered on (user said "try, it might be powered on")

---

## Related Documents

- [[experiment_log]] — Full experiment history with results
- [[pack-bundle-patching]] — Technical details of CRC correction and bundle format
- [[song-metadata-addressables-structure]] — Addressables catalog structure and validation
- [[addressables-crc-validation-timing]] — When Addressables validates CRC (LAZY vs immediate)
- [[memory-injection-addressables-bypass]] — Memory injection fallback approach

