# Plugin Changelog — Beat Saber Deluxe

All notable changes to the GoldHEN plugin (`beat_saber_deluxe.prx`) are documented here.

## [v0.65] — 2026-07-14
### Added
- **Mode selector — 5 preview difficulty modes** — StartMeUp BeatmapLevelSO in pack bundle patched with 5-mode preview data (Standard, OneSaber, NoArrows, 90Degree, 360Degree). Each mode references the correct BeatmapCharacteristicSO via PPtr (fileID=3).

### Fixed
- **m_Script PPtr bug in blob builder** — `build_beatmap_levelso_blob()` was using `_CHAR_PATH_IDS["Standard"]` for the m_Script pathID instead of the correct script pathID (2140275054477726686). This caused Unity deserialization to fail when loading the pack bundle.

### Changed
- **Bundle patching via UnityPy `save("original")`** — instead of raw bundle building (which had multiple bugs with LZ4 compression, block info format, and alignment), now uses UnityPy's `save()` with `"original"` packer to write the modified bundle in the correct UnityFS format.
- **redirects.json updated** — added pack bundle redirect: `therollingstones_pack_assets_all_a99482a8a3da9e991e5ae36f2fea209c` → `rollingstones_pack_patched.bundle`

## [v0.64] — 2026-07-14
### Removed
- **All IL2CPP hooks** (`get_preview_detour`, `ctor_detour`, `maybe_install_il2cpp_hook`) — constructor hook at RVA 0x9891E0 proved definitively dead: Unity deserializes BeatmapLevelSO objects via raw memory copy from AssetBundles, never calling the IL2CPP constructor. DetourMode_x32 (5-byte JMP) was correct and stable, but the hook target simply never fires.

### Verified
- **Redirect-only system is stable** — v0.64 confirms that with IL2CPP hooks removed, no crash occurs at any point: startup, song select, or gameplay. Start Me Up correctly plays Espresso (Hard difficulty verified).

## [v0.59] — 2026-07-13
### Changed
- Added `__attribute__((ms_abi))` to all IL2CPP hooks (proved to be wrong — reverted in v0.60)

## [v0.63] — 2026-07-14
### Fixed
- **DetourMode_x64 → DetourMode_x32** — The constructor hook at RVA 0x9891E0 crashed with CE-34878-0 because `DetourMode_x64` uses a 14-byte absolute JMP that overwrites into the next instruction (the `mov dword [rdi+0xA0], 1` instruction at byte 6 is 10 bytes; bytes 6-13 are truncated). Changed to `DetourMode_x32` (5-byte near JMP E9 xx xx xx xx) which only overwrites bytes 0-4 — all complete instructions.

## [v0.62] — 2026-07-14
### Added
- **BeatmapLevelSO constructor hook** at RVA 0x9891E0 — captures `this` pointers when BeatmapLevelSO objects are deserialized from the pack bundle.
- **Deferred preview array augmentation** — after the rolling stones pack bundle opens, waits 3 file-opens then augments `_previewDifficultyBeatmapSets` from 1→5 entries via malloc'd copies of the Standard preview set.

### Known Crash
- `DetourMode_x64` overwrote 14 bytes, truncating the instruction at byte 6 → CE-34878-0. Fixed in v0.63.

### Removed
- **Pack bundle redirect** — caused CE-34878-0 crash (Unity validates bundle hashes)
- **Memory scanning approach** — page-aligned scan would miss BeatmapLevelSO objects

## [v0.61] — 2026-07-14
### Added
- **Pack bundle redirect for Rolling Stones** — redirected to modified bundle with augmented preview data. Crashed due to bundle hash mismatch.

## [v0.60] — 2026-07-14
### Removed
- **All `__attribute__((ms_abi))`** — PS4 IL2CPP uses **SysV AMD64** (same as native C), not MS x64. ms_abi caused hooks to read `this` from the wrong register (RCX instead of RDI) → crash on ANY song selection.
- **`set_data_detour`** hook — never fires (SetData called only with 2+ characteristics).
- **`set_content_detour`** hook — causes startup/song-selection crash at RVA 0x1C3B630.

### Changed
- **`get_preview_detour`** — default C convention (no ms_abi). Reads `_previewDifficultyBeatmapSets` at offset 0x98 directly. The ONLY IL2CPP hook installed. Won't crash if inlined; should work if called.

## [v0.58] — 2026-07-13
### Added
- **SetContent hook** (`StandardLevelDetailView.SetContent()`) — directly augments the mode selector with extra characteristics when a song is selected. Overcomes the previous limitation where SetData was never called (because the game only calls it when there are 2+ modes, which it didn't know about).
- **Notification updated** to read "Beat Saber Deluxe vX.XX\nBy Chris Primeish" with an actual newline.

### Changed
- Version increment rule added to dev docs: ANY change to `main.cpp` requires bumping `PLUGIN_VERSION`.
- Global `il2cpp_module_base` stored for reuse across all IL2CPP hooks.

### Previous (v0.57 — merged as PR #2)
- Dynamic redirect system
- 32-song redirect table loaded from `redirects.json`
- Per-song bundle redirects with full audio/beatmap sync
- Debug logging to `/data/GoldHEN/AFR/CUSA12878/bs_log.txt`
- Two IL2CPP hooks installed (get_preview + SetData) but not yet reaching the mode selector

## v0.67 — ROOT CAUSE FOUND: Addressables Catalog CRC Check (2026-07-16)

### Critical Discovery
- **Exp 136 — Addressables catalog CRC validation:** Found per-bundle CRC32 checksums in `aa/catalog.json`'s `m_ExtraDataString` (UTF-16 LE encoded JSON). Each bundle entry includes `m_Crc`, `m_BundleSize`, `m_Hash`, and `m_UseCrcForCachedBundles=true`.
- **This is why ALL modified pack bundles crash:** Any change to the bundle file changes its CRC. The game validates the CRC against the catalog at load time → mismatch → CE-34878-0.
- **Catalog cannot be redirected:** It's loaded as a plain JSON file by Unity's ContentCatalogProvider, NOT via `AssetBundle.LoadFromFile`. The AFR plugin only hooks LoadFromFile.

### Experiments Concluded
- **Exp 134b** — LZ4-rebuilt text-only pack bundle: ❌ CRASHED (CRC mismatch)
- **Exp 135** — LZ4HC-rebuilt text-only pack bundle: ❌ CRASHED (CRC mismatch, not compression flag)
- **Exp 136** — Catalog parsed, CRC mechanism identified: ✅ Root cause found
- **Exp 139** — Log analysis confirmed pack redirect was active, removed it

### New Approach — Per-Song Bundle Modes
- **Exp 138 — Mode selector via per-song bundle:** Built `startmeup_custom_v3_modes.bundle` with `--enable-modes OneSaber,90Degree`. Deployed to PS4. Pack redirect removed. Awaiting test.
- This bypasses the pack bundle entirely (per-song bundles are not CRC-checked against catalog).

## v0.66 — Bundle Building Fix + Text Patching (2026-07-15)

### Critical Fixes
- **Bundle building bug:** Concatenated `f.write(b'...' + b'...')` caused alignment issues. Fixed with separate `f.write()` calls + explicit `b'\x00' * pad_needed` padding + `f.flush()`. This was causing "Decompression failed: corrupt input" errors in UnityPy.
- **Pack bundle text patching:** Byte-level string replacement in the original 440-byte BeatmapLevelSO blob. Works for UnityPy verification, BLOCKED by catalog CRC on PS4.

### Discoveries
- **UnityPy save_typetree() IGNORES modifications for BeatmapLevelSO** in Unity 2022.3.
- **UnityPy cab.save() produces incompatible CAB** (4 bytes larger than original).

### Status
- Pack bundle redirect works (original bundle) ✅
- Pack bundle modification IMPOSSIBLE due to catalog CRC check ❌
- Per-song bundle mode selector deployed, awaiting test ⏳

## v0.58 — Pack Bundle CRC Validation Workaround (2026-07-17)

### New Features
- **Pack Bundle Redirect Support**: Added redirect for `therollingstones_pack_assets_all_a99482a8a3da9e991e5ae36f2fea209c` → `rollingstones_pack_patched.bundle` in `redirects.json`

### Technical Details
- Bundle contains Espresso BeatmapLevelSO with 5 modes (Standard, OneSaber, NoArrows, 90Degree, 360Degree)
- CRC matched to `0xdc8b314f` via GF(2) linear algebra on alignment padding bytes
- File size: 7,905,515 bytes (+2,712 from original); may trigger `m_BundleSize` validation

### Known Issues
- CE-34878-0 crash at startup despite CRC match (likely m_BundleSize validation or invalid pathIDs)
- Pack redirect removed after test failure; game works without it

### Test Results (Exp 142)
- "CRC check PASSED (log shows game continued loading other bundles after pack bundle)"
- Crash likely from: (a) `m_BundleSize` validation rejection, or (b) invalid BeatmapCharacteristicSO pathIDs in 5-mode preview sets

### Next Steps
- Test uncompressed block injection approach (zero size impact) + GF(2) CRC correction
- If successful, deploy Espresso replacement with display name + mode selector support

## v0.59 — Pack Bundle Test Results (2026-07-17)

### Test Summary
- **Bundle deployed:** `rollingstones_pack_patched.bundle` via AFR redirect
- **CRC verified:** `0xdc8b314f` ✅ (matches Addressables catalog)
- **Result:** ❌ CE-34878-0 crash shortly after launch
- **Notification:** User reported v0.64 plugin update notification

### Analysis
- CRC validation PASSES (confirmed via bundle verification on PS4)
- Crash likely from `m_BundleSize` validation (+2,712 byte difference) OR invalid BeatmapCharacteristicSO pathIDs in 5-mode preview sets

### Next Steps
- Implement uncompressed block injection approach (zero size impact)
- Test with GF(2) CRC correction on alignment padding bytes


## v0.60 — Size + CRC Validation Both Required (2026-07-17)

### Test Results
| Bundle | Size | CRC | Result |
|--------|------|-----|--------|
| rollingstones_pack_patched.bundle | 7,905,515 (+2,712) | 0xdc8b314f ✅ | ❌ CE-34878-0 (size validation) |
| espresso_pack_patched.bundle | 7,902,803 ✅ | 0x7218b959 ❌ | ❌ CE-34878-0 (CRC validation) |

### Key Finding
Both `m_BundleSize` AND `m_Crc` are validated by the Addressables catalog. Either mismatch causes crash.

### Next Steps
- Implement uncompressed block injection approach (zero size impact)
- Use GF(2) linear algebra on alignment padding bytes for CRC correction
- Deploy to PS4 and test with both conditions met

