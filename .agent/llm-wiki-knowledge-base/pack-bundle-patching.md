---
name: pack-bundle-patching
description: "Pack bundle modification attempts and why all approaches are blocked by Addressables catalog CRC validation"
metadata:
  type: reference
---

# Pack Bundle Patching — Size + CRC Co-Validation Blocker

## Summary

The Addressables catalog validates BOTH `m_BundleSize` (7,902,803 bytes) AND `m_Crc` (`0xdc8b314f`) for every loaded bundle. Either mismatch causes CE-34878-0 crash. This dual validation blocks all pack bundle modification approaches including CRC correction via GF(2) linear algebra on alignment padding bytes.

**Exp 146 (2026-07-17):** Deployed bundle with correct CRC (`0xdc8b314f`) but wrong size (+2,712 bytes). ❌ CE-34878-0 crash — size validation enforced.
**Exp 148 (2026-07-17):** Deployed bundle with correct size (7,902,803 bytes) but wrong CRC (`0x7218b959`). ❌ CE-34878-0 crash — CRC validation enforced.
**Exp 155 (2026-07-17):** Confirmed root cause of size difference: +817 bytes from blob size increase in decompressed stream, ~1,895 bytes from bundle rebuild overhead. ANY stream modification changes file_size.

**Viable Approach:** Option B — Uncompressed block injection. The 49 uncompressed blocks (flag=0, each 131,072 bytes stored as raw data) can be modified without changing file_size. Use GF(2) linear algebra on alignment padding bytes for CRC correction.

See [[unityfs-v8-bundle-layout]] for complete offset map and block distribution analysis. See [[song-metadata-addressables-structure#Addressables Catalog CRC Validation]] for catalog validation details.

## Blocking Root Cause: Addressables Catalog Dual Validation

The game validates every loaded bundle's CRC32 against the catalog's `m_Crc` AND checks file_size against `m_BundleSize`. The catalog (`aa/catalog.json`) contains:

```json
{"m_Hash":"a99482a8a3da9e991e5ae36f2fea209c","m_Crc":3700109647,
 "m_BundleSize":7902803,"m_UseCrcForCachedBundles":true,...}
```

Both fields must match exactly. The catalog is loaded as plain JSON (not via `AssetBundle.LoadFromFile`), so the AFR plugin cannot redirect it.

## Size Difference Analysis (Exp 155)

When modifying the pack bundle's decompressed stream, file_size changes due to:

| Source | Bytes | Explanation |
|--------|-------|-------------|
| Blob replacement | +817 | Original BeatmapLevelSO (440B) → Espresso blob (1,257B) |
| Bundle rebuild overhead | ~1,895 | Object table shifts, compression ratio changes, alignment |
| **Total** | **+2,712** | Matches measured difference in rollingstones_pack_patched.bundle |

Decompressed stream sizes:
- Original: 8,511,228 bytes
- Patched: 8,512,045 bytes (+817 bytes)

This confirms that ANY modification to the decompressed stream changes file_size. Uncompressed block injection is the only path to zero size impact — but see Exp 157 for why this doesn't work in practice.

## Critical Finding: Uncompressed Blocks Are NOT Independent Storage (Exp 157)

**Initial assumption:** The 49 uncompressed blocks (flag=0) are stored as raw data with FIXED sizes, so modifying their CONTENT affects CRC but NOT file_size. This would provide ~6.1 MB of free variables for pure CRC control.

**Actual behavior:** Uncompressed blocks are part of a SHARED DECOMPRESSED STREAM that gets LZ4HC compressed as one unit. Modifying content in any block shifts downstream byte positions and alters all subsequent compression ratios, changing file_size by ~817-2,177 bytes.

**Implication:** Option B (uncompressed block injection for pure CRC control) CANNOT achieve zero size impact. Any blob injection changes file_size due to cascading compression ratio effects.

## All Approaches (including Successful CRC Correction)

| Approach | Experiment | Result |
|----------|-----------|--------|
| UnityPy `bf.save("original")` | Exp 132 | ❌ CAB format differs (+4 bytes) → CRC mismatch |
| UnityPy `cab.save()` + manual bundle | Exp 133 | ❌ CAB serialization incompatible (+4 bytes) |
| UnityPy `save_typetree()` | Exp 134 | ❌ Silently ignores BeatmapLevelSO modifications |
| Byte-level text patch + LZ4 rebuild | Exp 134b | ❌ Compressed bytes different → CRC mismatch |
| Byte-level text patch + LZ4HC rebuild | Exp 135 | ❌ Compressed bytes different → CRC mismatch |
| Original bundle (diagnostic) | Exp 134a | ✅ WORKS — CRC unchanged |
| **CRC correction via GF(2) linear algebra** | **Exp 142** | **✅ CRC matches! 0xdc8b314f** (size +2,712B) |
| **Uncompressed block injection (Option B)** | **Exp 157** | **❌ BLOCKED — blocks are part of shared decompressed stream; modifying content changes file_size by ~817-2,177 bytes due to cascading compression ratio effects** |

## CRC Correction Method (Alignment Padding Bytes)

The CRC-32 table is a **linear function over GF(2)**: `table[a XOR b] = table[a] XOR table[b]`. This allows computing the exact padding byte values needed to make the bundle's CRC match the original, using a 32×32 GF(2) matrix approach.

### Algorithm

1. **Precompute M matrix** (32×32 GF(2)): each column j = CRC state after processing 1 zero byte starting from state = (1 << j)
2. **Compute M^L** (L = suffix length): using square-and-multiply matrix exponentiation over GF(2)
3. **Invert M^L** via Gauss-Jordan elimination to solve: `CRC_after_pad = M^(-L) * (CRC_target XOR crc_suf_from_0) XOR 0xFFFFFFFF`
4. **Compute padding byte contributions**: `M^(n-1) * table[p0] XOR M^(n-2) * table[p1] XOR ... XOR table[p_{n-1}] = target`
5. **Search free bytes** to find a combination that lands in the inverse CRC table, fixing remaining bits exactly

### Key Formula

```
CRC_new = M * CRC_old XOR table[byte]
         (affine transformation; M = (CRC >> 8) ^ table[CRC & 0xFF])
CRC_after_pad = M^n * CRC_before_pad XOR sum(M^(n-1-i) * table[pad[i]])
zlib.crc32(suf, crc) = M^L * (crc XOR 0xFFFFFFFF) XOR zlib.crc32(suf, 0)
```

### Affine Nature of CRC — Why Simple GF(2) Doesn't Converge for Stream Injection

CRC-32 is **affine** over GF(2), not purely linear. The affine component comes from the initial state being XOR'd with `0xFFFFFFFF` in zlib.crc32:

```
crc_init = 0xFFFFFFFF  (not 0x00000000)
CRC_final = M^L * (initial_state XOR 0xFFFFFFFF) XOR zlib.crc32(data, 0)
          = M^L * initial_state XOR M^L * 0xFFFFFFFF XOR zlib.crc32(data, 0)
```

For padding bytes: the affine offset `M^L * 0xFFFFFFFF` is constant and must be properly accounted for. Simple GF(2) linear algebra (treating CRC as purely linear) misses this offset, causing residual error that doesn't converge to zero.

**Solution:** Properly compute affine weight matrices that include the initial state XOR contribution. Then solve the full affine system using greedy search over free variables.

## LZ4HC Requirement (Flag=3)

The original bundle uses `flag=3` (LZ4HC) for ALL blocks. When rebuilding, both blocks and blocks info must use LZ4HC:
```python
comp = lz4.block.compress(data, mode='high_compression', compression=9, store_size=False)
# Per-block flag must be 3
n_blocks.append((decomp_size, comp_size, 3))
```

Using LZ4 (flag=2) is also rejected by the PS4 Unity runtime.

## Bundle Building Requirements (for reference)

If the CRC issue is ever resolved, these are the requirements for manual bundle building:
- **Separate `f.write()` calls** — concatenated bytes cause alignment bugs
- **Explicit padding** — `b'\x00' * ((16 - tell % 16) % 16)` not `while tell%16:`
- **`f.flush()`** after header writes
- **LZ4HC** compression with per-block flag=3
- **BlockInfoNeedPaddingAtStart** (flag 0x200) requires alignment between blocks info and data blocks

## CAB Binary Format (v22+)

For Unity 2022.3 CABs (SerializedFile version 22+):
- Header: 48 bytes
- Offset 0x14: metadata_size (BE uint32) = 53401
- Offset 0x1C: file_size (BE uint32) = 89180
- data_offset = align16(48 + metadata_size) = 53456
- Object table entries: pathID(int64 LE) + offset(int64 LE, relative to data_offset) + size(int32 LE)

## m_Script PPtr Correction

The BeatmapLevelSO blob builder originally used `_CHAR_PATH_IDS["Standard"]` for m_Script PPtr (WRONG):
- **Correct m_Script pathID**: `2140275054477726686` (fileID=1)
- **Standard characteristic pathID**: `-7286399427822119286` (fileID=3)

## Option B: Uncompressed Block Injection Approach — BLOCKED

**Initial hypothesis:** The 49 uncompressed blocks (flag=0, each 131,072 bytes stored as raw data) provide **6.1 MB of free CRC control variables with ZERO size impact**.

**Reality (Exp 157):** Uncompressed blocks are part of a SHARED DECOMPRESSED STREAM that gets LZ4HC compressed as one unit. Modifying content in any block shifts downstream byte positions and alters all subsequent compression ratios, changing file_size by ~817-2,177 bytes.

**Conclusion:** Option B cannot achieve zero size impact. The approach is BLOCKED.

## Current Best Alternative: Memory Injection

If pack bundle modification fails, fallback to memory injection — patch BeatmapLevelSO in RAM after Addressables load (bypasses catalog entirely). Exp 142 showed game continued loading other bundles after pack bundle loaded, suggesting this may be feasible.

### Quick Build Reference (for if/when CRC blocker is resolved)
```bash
python3 /workspace/beat_saber_deluxe/tools/build_patched_pack_bundle.py
```
