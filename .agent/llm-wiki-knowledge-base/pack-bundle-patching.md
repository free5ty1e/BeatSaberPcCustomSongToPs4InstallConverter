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

## ⚠️ CORRECTION (Exp 177, 2026-08-07): catalog.json CAN now be redirected

The "cannot redirect catalog.json" conclusion above applied to the **OLD plugin hook model** (v0.66–v0.8024), which only hooked `AssetBundle::LoadFromFile`. The **current v0.8040 plugin hooks libc `open()`** (GoldHEN Detour) and substring-matches every path against `LOWER_REDIRECT_KEYS` (see `src/main.cpp` `open_hook`, ~line 256–301). The Exp 177 PS4 log proves catalog.json passes through the hook:

```
[OPEN #58] /app0/Media/StreamingAssets/aa/catalog.json
```

So adding a redirect key containing `aa/catalog.json` (e.g. `"aa/catalog.json": "catalog_patched.json"`) WOULD intercept the catalog load. This re-opens the pack-bundle patching avenue: because we can now control the expected `m_Crc` + `m_BundleSize` via a redirected catalog, the dual-validation blocker is removable — the patched pack bundle just needs its actual size + CRC written into the patched catalog.

Caveats verified:
- Bundle paths in the catalog are absolute (`{RuntimePath}/PS4/<name>.bundle`), NOT relative to the catalog's directory — so serving the catalog from AFR does not break bundle path resolution.
- `redirects.json` is loaded before the game opens catalog.json (line 4 vs line 83 in the Exp 177 log), so the redirect is active at first use.
- Addressables reads `aa/settings.json` (OPEN #57) then `aa/catalog.json` (OPEN #58) — no `.hash` file observed.

**Exp 178 (in progress):** zero-risk proof — deploy a byte-identical copy of the original catalog as `catalog_test.json` on AFR + redirect key, boot, confirm `-> REDIRECTED` on the catalog open. If stable, proceed to deploy `catalog_patched.json` (already generated in Exp 136 with rolling-stones pack re-pointed to m_Crc=2690266029 / m_BundleSize=7905246) plus a pack bundle patched to exactly those values.

## ✅ CORRECTION (Exp 179, 2026-08-07): catalog `m_Crc` = zlib.crc32 of the DECOMPRESSED stream

**Root cause of all Exp 142–157 "CRC-corrected bundle still crashed" results:** the catalog `m_Crc` is NOT the zlib.crc32 of the compressed bundle file — it is the zlib.crc32 of the bundle's **DECOMPRESSED stream**.

Verified against the original:
- Original bundle file zlib.crc32 = `0x63520032`
- Original catalog `m_Crc` = 3700109647 = `0xdc8b314f`
- Decompressed stream (8,511,228 B) zlib.crc32 = `0xdc8b314f` ✓ = catalog value

**Implication:** the GF(2) alignment-padding CRC forcing (Exp 142) fixed the WRONG metric (file CRC). The runtime validates the decompressed-stream CRC. When we control the catalog (via redirect), CRC forcing is unnecessary — we simply write the patched bundle's ACTUAL decompressed-stream CRC and file size into the fresh catalog.

The decompressed-stream CRC computation:
```python
def crc_decompressed_stream(bundle_bytes):
    # parse UnityFS header: blocks info size @38, uncompressed @42, flags @46
    # decompress blocks info, iterate block list, decompress LZ4HC blocks (flag&2)
    # return zlib.crc32(concatenated decompressed blocks)
```

**Exp 179 build (startmeup_pack_modes.bundle):**
- StartMeUp BeatmapLevelSO blob 440 → 1,028 B: 4 preview sets (Standard/OneSaber/NoArrows/90Degree), difficulty data copied from Standard; identity preserved (`_levelID`="StartMeUp", env, `_contentRating`=1).
- 7,905,425 B; dec-stream CRC `0x8e1f8937` = 2384431415.
- `catalog_startmeup_modes.json`: ONLY the rolling-stones entry differs — `m_Crc` 3700109647→2384431415, `m_BundleSize` 7902803→7905425; `m_Hash`/`m_BundleName` unchanged; UTF-16LE extra-data preserved byte-identical.
- Build tool: `development/scripts/build_startmeup_pack_modes.py`. Verified 81/81 objects parse; only object `2287600824654271910` changed size.

## ✅ SUCCESS (Exp 179, 2026-08-08): Mode Selector Gap CLOSED — Catalog-Redirect + Pack-Bundle Patch Works!

**Complete working approach:**
1. **v0.8040 plugin** hooks libc `open()` (GoldHEN Detour) with substring matching on `LOWER_REDIRECT_KEYS` → can redirect `aa/catalog.json` (OPEN #58 confirmed).
2. **Redirect catalog** to a fresh `catalog_startmeup_modes.json` with corrected `m_Crc` (dec-stream CRC) and `m_BundleSize` for the patched pack bundle.
3. **Patch pack bundle** (`startmeup_pack_modes.bundle`): surgical blob injection adding 3 extra `_previewDifficultyBeatmapSets` (OneSaber/NoArrows/90Degree) to the StartMeUp BeatmapLevelSO, preserving identity (`_levelID`="StartMeUp", m_Script pathID, environment, cover, preview audio).
4. **Redirect pack bundle** to the patched version via same `open()` hook.
5. **Per-song bundle** (`startmeup_v3`) already carries generated mode beatmaps via pipeline `--enable-beatmap-mode-mapping` (v0.5310).

**Result (corrected 2026-08-09):** In-game mode selector for Start Me Up shows **Standard / OneSaber / NoArrows**. 90Degree was NEVER visible — the 90Degree preview slot pointed at the 360Degree characteristic (`4533580413116749821`, `requires360=1`), so the game hid the button. The OneSaber/NoArrows labels appear "swapped" in the preview array but this is cosmetic: each characteristic PID drives BOTH its own selector button AND its gameplay difficulty-set lookup, so pointing each slot at the right characteristic is what matters.

**Verified characteristic PIDs** (from `sharedassets_assets_all_068cd59e9a6fba13da706dc9269bf759.bundle`, CAB `cb38b3e2985c65d4cf8a63437da74a89`):

| Mode | PID | notes |
|---|---|---|
| Standard | `-7286399427822119286` | sortingOrder=0 |
| OneSaber (OneColor) | `-5623662769225589684` | containsRotation=0, sortingOrder=1 |
| NoArrows | `-8583864861369561029` | containsRotation=0, sortingOrder=3 |
| **90Degree** | **`-5995858427784384822`** | containsRotation=1, requires360=0, sortingOrder=5 |
| 360Degree | `4533580413116749821` | requires360=1 → hidden without 360 gameplay |

**Generator status (per-song bundle):**
- Drop Pop Candy (replacement for Start Me Up) had: Standard (5 diffs) + 90Degree Expert (song's own)
- Pipeline v0.5310 generated: OneSaber (5 diffs), NoArrows (5 diffs), 90Degree (Easy/Normal/Hard/ExpertPlus)
- **Known issue (2026-08-08):** NoArrows mode in-game shows arrows instead of dots — generator or data-loading bug under investigation.

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
| **CRC correction via GF(2) linear algebra** | **Exp 142** | **⚠️ CRC "matched" file CRC (0xdc8b314f) but crashed anyway — the game validates the DECOMPRESSED-stream CRC (Exp 179 root cause). Superseded by the catalog-redirect approach which writes actual dec-stream CRC into a fresh catalog.** |
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

## ✅ GENERALIZED (Exp 188, 2026-08-14): Pack Patch is now a production pipeline feature

The rollingstones pack-patch (Exp 179-182) was generalized into the production pipeline (`tools/build_pack_mode_bundles.py`, pipeline v0.5319):

- **ALL 36 DLC packs** patched: every replaced BeatmapLevelSO gets 4 preview mode sets (Standard/OneSaber/NoArrows/90Degree × 5 difficulties) = 303 BeatmapLevelSOs verified.
- **Manifest:** `pack_modes_bundles/manifest.json` records per-pack `patchedBundle`/`size`/`crc` (dec-stream CRC)/`catalogBundleName`. Dev-built bundles adopted via `development/scripts/adopt_pack_modes_manifest.py`.
- **Single merged catalog** `catalog_pack_modes.json` (redirect `aa/catalog.json`) carries updated `m_Crc`/`m_BundleSize` for EXACTLY the redirected packs; regenerated from ORIGIN each run so untouched entries stay byte-identical.
- **Deterministic redirects:** `_get_pack_modes_redirects()` emits a pack redirect only when its patched bundle exists locally; catalog redirect only when merged catalog exists (Exp 180 crash rule). `pack_modes` redirects override the old single-pack prototype (`startmeup_pack_modes.bundle` pair).
- **Deploy ordering:** pack bundles + catalogs deploy BEFORE `redirects.json` generation (Step 9a before Step 9).
- **CLI:** `--build-pack-modes` / `--force-pack-modes` / `--pack-modes-packs` / `--deploy-pack-modes`.
- **Config:** `pack_modes.packs` (default: therollingstones, billieeilish, lizzo, camellia).

### CRITICAL: catalog.json binary entry structure (`m_ExtraDataString`)

The catalog `m_EntryDataString` is NOT whole-string UTF-16. It is a **BINARY concatenation of per-entry blocks**:
`type_byte + 1-byte-length assembly name + 1-byte-length class name + 4-byte JS length (BE) + UTF-16-LE JSON`.

Whole-string UTF-16 decode misaligns blocks and makes the entry marker unfindable (camellia's entry failed this way). The pipeline's `update_catalog_entry()` walks blocks byte-wise and patches only the matching block in place, resizing the length field when digit counts change.

### CRITICAL: `m_EntryDataString` records carry byte offsets into `m_ExtraDataString` (Exp 189)

`m_EntryDataString` is a binary array of **2251 × 28-byte records** (7 int32 LE). Record field `rec[4]` is a **byte dataIndex** into `m_ExtraDataString` pointing at the start (type byte) of that entry's block. Verified on the real catalog: 138 entries carry dataIndexes ≥ 0 (those with AssetBundleRequestOptions blocks); the rest are -1 (sentinel, no block).

**When a patched block's JSON grows/shrinks in byte length, every later block shifts, so EVERY entry dataIndex pointing past the patched block's start MUST be shifted by the same delta.** Exp 188 missed this: lizzo's `m_Crc` grew 7→10 digits (+6 bytes UTF-16), all 70 dataIndexes after it went stale → game read garbage → PS4 crash at OPEN #74 right after the catalog redirect loaded. `update_catalog_entry()` now rewrites `m_EntryDataString`, shifting `rec[4] += delta` for every record whose dataIndex points past the patched block's start, whenever a block edit changes byte length (`delta != 0`). Guarded by `'m_EntryDataString' in catalog_json` so synthetic catalogs without entry data still work.

**Parse fragility (also fixed Exp 189):** `m_Crc`/`m_BundleSize` must be extracted from a block with regex (`"m_Crc":\s*(\d+)`) — splitting the block JSON on commas and taking text after `:` breaks when the field is the block's LAST JSON field (the token then includes the trailing `}` and the value-replace strips the block's closing brace, corrupting the JSON). The real BS catalog puts `m_BundleSize` mid-block so it wasn't hit in production, but it's a latent corruption bug.

### Production fixes baked in (Exp 188)
- Object-table offsets shift by cumulative deltas of patches starting BEFORE each object (own offset unchanged, only size field updates).
- Patched blob's `byte_start` is NOT shifted by its own delta.
- Mode-set extension checks `pid in CHAR_PATH_IDS.values()` (keys are mode-name strings).

### ⚠️ 360Degree must NOT be in `CHAR_PATH_IDS` (Exp 190, 2026-08-15) — reproducibility
360Degree was purged project-wide in Exp 175 (PS4's single camera can't track the full 360° arc; the game hides the 360Degree characteristic from the selector). `build_modes_blob` pads ANY set whose pid is in `CHAR_PATH_IDS.values()` to `TARGET_DIFFS` — so a leftover `"360Degree"` entry made the production module extend the 360Degree preview set 1→5 diffs (+144 B per patched blob) for every pack that ships one, producing bundles that did NOT byte-match the dev-built committed artifacts (10/36 packs diverged; the 4 deployed packs happened to be unaffected). Rule: **`CHAR_PATH_IDS` must contain exactly `TARGET_MODES` (4 entries), never 360Degree.** Guarded by `test_unsupported_360degree_set_not_extended`.

### Production builder is the reproducibility source of truth (Exp 190)
The original 36 `pack_modes_bundles/*.bundle` were built by the OLD dev script (`development/scripts/build_all_pack_modes.py`) and ADOPTED into the manifest — NOT by the production module. After the Exp 190 360Degree cleanup, `tools/build_pack_mode_bundles.py` reproduces ALL 36 committed bundles byte-identically (sizes + dec-stream CRCs, ~46 s for all 36) — a fresh user can reproduce the exact committed artifacts (or any pack subset) with zero manual steps.

### Deployed 2026-08-14
4 packs (therollingstones/billieeilish/lizzo/camellia) + merged catalog + 43-redirect config on PS4, post-deploy validation PASSED. **Exp 189 (2026-08-15):** the deploy crashed the PS4 at boot (stale dataIndexes — see above); fixed + merged catalog regenerated (0 invalid dataIndexes), pending redeploy + boot test. Tests are config-driven (derive packs from `cfg['pack_modes']['packs']`), no hardcoded packs. See [[addressables-crc-validation-timing]] and [[unityfs-v8-bundle-layout]].

### ⚠️ Deploy is not the same as "the pipeline is fixed" — verify CONTENT, not just size (Exp 191, 2026-08-16)
The Exp 189/190 fixes were correct, yet the user STILL crashed: **the fixed catalog was never redeployed to the PS4**. The PS4 kept running the broken v0.5319 `catalog_pack_modes.json` (70/2251 invalid dataIndexes, md5 `0eb8a27deb66c15e918aeec3dbd9a725`), so every launch crashed at OPEN #58/#74 right after the `aa/catalog.json` redirect — the exact same signature as before. Lessons:
- **Broken vs fixed catalogs can be byte-identical in SIZE** (both 795,783 B here) — so size-only post-deploy checks can NEVER detect a stale catalog. Deploy + verify must validate catalog CONTENT.
- `--verify-ps4` now has **check #7 (catalog content validation)**: downloads the deployed `catalog_pack_modes.json` and (a) validates every entry dataIndex points at a type-7 block start via `validate_catalog_dataindexes()` (bad = any dataIndex ≥ 0 not landing on a `0x07` block byte — the exact v0.5319 crash signature), (b) compares the deployed md5 against the local build output, (c) verifies every configured pack's block carries the patched `m_Crc`/`m_BundleSize` via `validate_catalog_entries()`. A stale/broken catalog now FAILS the post-deploy validation loudly instead of passing silently.
- Reusable helpers in `tools/build_pack_mode_bundles.py`: `validate_catalog_dataindexes()`, `find_catalog_entry_js()` (byte-wise type-7 block walk — NEVER whole-string UTF-16 alignment, which misaligns for some blocks and can falsely report an entry "missing", e.g. camellia), `validate_catalog_entries()`.
- **Always download fresh `bs_log.txt` after ANY change** and confirm the session survived past the catalog redirect before declaring success.
- The legacy single-pack prototype (`pack_bundle` → `startmeup_pack_modes.bundle` + `catalog_startmeup_modes.json`) was removed from the DEFAULT config — fully superseded by `pack_modes` (rollingstones is in `pack_modes.packs`). Its code path still works for explicit configs; keeping it in defaults made `--verify-ps4` report phantom "MISSING on PS4" entries for the deleted prototype files.

**Exp 191 (2026-08-16):** fixed catalog deployed (md5 `975bacca0902624c9fb5c6a82cfa90c5`, 0 invalid dataIndexes) + verified on-device; stale prototype files deleted from PS4; 451/451 tests. Awaiting user boot test.

### ⚠️ PREVIEW SET pathIDs must be DISTINCT per mode - the Exp 197 "fix" was INVERTED (Exp 198/199, 2026-08-25)

**Hardware-proven ground truth:** cloned/new `_previewDifficultyBeatmapSets` entries MUST use their OWN characteristic pathID (`CHAR_PATH_IDS[mode]`, e.g. NoArrows `-8583864861369561029`) even though that pathID has no BeatmapData asset anywhere in the pack's BeatmapLevelsData. The game NEVER resolves preview-set PPtrs against BeatmapLevelsData when showing/playing modes - nonexistent pathIDs are harmless.

**The proof (Exp 198/199):** the RS bundle the user successfully PLAYED all 4 modes on (`development/reference_bundles/therollingstones_WORKING_v0.5324era_aug20.bundle`, md5 `5ed23829...`) has 4 DISTINCT set-pathIDs per SO. Exp 197's theory ("game looks up NoArrows pathID in BeatmapLevelsData and crashes") predicted THAT bundle should crash at gameplay - it doesn't. Conversely, v0.5325 rewrote all 4 sets to Standard's pathID and that structure CE-34878-0'd the game AT MENU INIT (before any gameplay): four preview sets sharing one identical PPtr is rejected when the song-select UI builds the per-song mode list (duplicate-key/dictionary-style failure). Boot log: catalog + bundle CRC checks all pass; death is mid-menu-load right after the pack bundle's third redirected read.

**Re-attribution of Exp 196's "lizzo gameplay crash":** the old-structure lizzo bundle boots AND browses fine (verified with a clean catalog). That era's gameplay crash was almost certainly the stale/mismatched catalog of the time (Exp 196 itself found catalog staleness), not blob structure.

**Rule (v0.5326):** every patched SO ends with exactly 4 sets whose pathIDs are exactly `{CHAR_PATH_IDS[m] for m in TARGET_MODES}` - all distinct - each with diffCount 5 and ranks exactly [0,1,2,3,4] (rank-dedup padding kept from v0.5325: short existing sets pad only from template records whose rank isn't already present). Regression tests pin this invariant (`test_new_mode_entries_use_own_pathids_and_clean_ranks`). Reproducibility proven: v0.5326 rebuild of lizzo == known-good deployed bytes (md5 `345d6a0e...`), rebuild of RS == golden working bytes (md5 `5ed23829...`).
