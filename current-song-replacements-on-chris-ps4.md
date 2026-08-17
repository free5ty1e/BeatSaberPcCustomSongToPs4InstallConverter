# Current Custom Song Replacements on Chris's PS4

## Current Status (2026-08-16)

**✅ GENERALIZED PACK PATCH DEPLOYED + VERIFIED ON-DEVICE** (Exp 188–191) — all configured DLC packs get 4 preview mode sets (Standard/OneSaber/NoArrows/90Degree × 5 difficulties) via patched pack bundles + a single merged catalog (`catalog_pack_modes.json`), plus 38 custom song bundle redirects.

**✅ EXP 191 CATALOG CRASH FIX DEPLOYED (2026-08-16)** — the PS4 was running the OLD BROKEN v0.5319 catalog (70/2251 invalid dataIndexes, md5 `0eb8a27d…`) which crashed every launch right after the `aa/catalog.json` redirect (OPEN #58/#74). The fixed catalog (md5 `975bacca0902624c9fb5c6a82cfa90c5`, 0 invalid dataIndexes) is now deployed + verified on-device. **AWAITING USER BOOT TEST.**

## Song Details (per-slot)

| Slot | Custom song | Artist |
|------|-------------|--------|
| `startmeup` | Espresso | Sabrina Carpenter |
| 37 other slots (Chromeo, Billie Eilish, Lizzo, Camellia packs) | custom songs | various |

All songs: 4 modes × 5 difficulties (Standard/OneSaber/NoArrows/90Degree), full-length PCM16 audio, V3.2.0 beatmaps.

## Deployed Files on PS4 (AFR base `/data/GoldHEN/AFR/CUSA12878/`)

| File | Content | Status |
|------|---------|--------|
| `<slot>_v3.bundle` (38) | Per-song bundles (audio + 4 mode sets × 5 difficulties) | ✅ Deployed |
| `therollingstones_pack_modes_assets_all_*.bundle` (7,906,184 B) | Patched Rolling Stones pack bundle (4 preview sets) | ✅ Deployed |
| `billieeilish_pack_modes_assets_all_*.bundle` (6,422,547 B) | Patched Billie Eilish pack bundle | ✅ Deployed |
| `lizzo_pack_modes_assets_all_*.bundle` (6,893,737 B) | Patched Lizzo pack bundle | ✅ Deployed |
| `camellia_pack_modes_assets_all_*.bundle` (5,188,380 B) | Patched Camellia pack bundle | ✅ Deployed |
| `catalog_pack_modes.json` (795,783 B, md5 `975bacca…`) | Merged catalog: patched m_Crc/m_BundleSize for the 4 configured packs | ✅ Deployed + verified (0 invalid dataIndexes) |
| `redirects.json` (43 redirects) | 38 song redirects + 4 pack bundle redirects + `aa/catalog.json` | ✅ Deployed + matches local |
| `features.json` | 2 runtime flags (`enable_custom_song_replacements`, `enable_song_metadata_modification`) | ✅ Deployed |

Legacy prototype files (`startmeup_pack_modes.bundle`, `catalog_startmeup_modes.json`) were **deleted from the PS4** (Exp 191 cleanup — superseded by the generalized pack_modes system).

## Redirects.json Keys (43)
- 38 × `BeatmapLevelsData/<slot>` → `<slot>_v3.bundle`
- `therollingstones_pack_assets_all_a99482a8a3da9e991e5ae36f2fea209c.bundle` → `therollingstones_pack_modes_assets_all_a99482a8a3da9e991e5ae36f2fea209c.bundle`
- `billieeilish_pack_assets_all_ba4a0db5570760b21ebcbb2ec7a8d321.bundle` → `billieeilish_pack_modes_assets_all_ba4a0db5570760b21ebcbb2ec7a8d321.bundle`
- `lizzo_pack_assets_all_8bf3db217732cc18af0b9a2a32d13a9a.bundle` → `lizzo_pack_modes_assets_all_8bf3db217732cc18af0b9a2a32d13a9a.bundle`
- `camellia_pack_assets_all_91d9d25ee1641047d08834b4bb3ec0ac.bundle` → `camellia_pack_modes_assets_all_91d9d25ee1641047d08834b4bb3ec0ac.bundle`
- `aa/catalog.json` → `catalog_pack_modes.json`

## Pending Test (Exp 191)
1. Boot Beat Saber — confirm **STABLE boot** through the `aa/catalog.json` redirect + pack scan (no crash at OPEN #58/#74).
2. Confirm all 4 packs' songs show in the mode selector with all 4 modes (Standard/OneSaber/NoArrows/90Degree) on Hard+.
3. Play a few songs from each pack to confirm bundle loads + audio.
4. After test: pull `bs_log.txt` → archive to `.ai_memory/experiment_logs/` → clear it on the PS4 → record results in `song_testing_log.md`.

## Useful Commands
- **Deploy pack_modes + verify:** `python3 tools/full_custom_song_pipeline.py --deploy-pack-modes --deploy-config --verify-ps4`
- **Verify only (validates deployed catalog CONTENT, not just size):** `python3 tools/full_custom_song_pipeline.py --verify-ps4`
- **Pull log:** FTP `get /data/GoldHEN/AFR/CUSA12878/bs_log.txt` (port 2121)
