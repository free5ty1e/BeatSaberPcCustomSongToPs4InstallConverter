# Pipeline Changelog

## v0.5301 (2026-07-19)
- **Feature flags support** — Added `--set-feature key=value` CLI argument. Writes `features.json` locally and deploys it to PS4 via FTP.
- **Supported flags:** `enable_custom_song_replacements` (default: false), `enable_song_metadata_modification` (default: false)
- Usage: `--set-feature enable_song_metadata_modification=true` or `--set-feature enable_custom_song_replacements=false`
- **BeatSaver API override** — Added `--beatsaver-api-base` to override the default BeatSaver API URL (useful for mirrors/local servers).

## v1.49 (2026-07-17)
- **Uncompressed block independence test FAILED:** Critical finding that 49 uncompressed blocks (flag=0) are part of a shared decompressed stream, NOT independent storage. Modifying their content changes file_size by ~817-2,177 bytes due to cascading compression ratio effects.
- **Option B BLOCKED:** Uncompressed block injection approach cannot achieve zero size impact — blocks are not independent storage as initially hypothesized.
- **New fallback identified:** Memory injection (patch BeatmapLevelSO in RAM after Addressables load) as alternative to pack bundle modification.

## v1.48 (2026-07-17)
- **Size + CRC dual validation confirmed:** Both `m_BundleSize` and `m_Crc` in Addressables catalog must match simultaneously or game crashes with CE-34878-0
- **Root cause of size difference identified (Exp 155):** Decompressed stream grows by exactly the blob size delta (+817 bytes for Espresso blob replacing original BeatmapLevelSO). Remaining ~1,895 bytes from bundle rebuild overhead.
- **Viable approach identified:** Uncompressed block injection — 49 blocks (flag=0) are stored as fixed-size raw data; modifying content affects CRC but NOT file_size. Provides ~6.1 MB of free variables for CRC control.
- **Knowledge base updated** with detailed size analysis and Option B approach documentation.

## v1.47 (2026-07-17)
- **CRC correction via GF(2) linear algebra works:** Achieved exact CRC match `0xdc8b314f` using alignment padding bytes for correction. Bundle size differs by +2,712 bytes; `m_BundleSize` validation in catalog causes crash when size doesn't match.
- **New tool added:** `build_patched_pack_bundle.py` in `tools/` — proven working CRC correction via GF(2) linear algebra on 9 alignment padding bytes. Produces rollingstones_pack_patched.bundle (7,905,515 bytes).

## v1.46 and earlier
- See previous changelog entries for full history of pipeline development.
