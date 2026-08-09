# drop pop candy Replacement (Start Me Up slot)

## Current Status (2026-08-09)

**✅ MODE SELECTOR GAP CLOSED** (Exp 180, 2026-08-08) — all 4 modes visible in selector (Standard/OneSaber/NoArrows/90Degree).
**✅ NoArrows BUG FIXED IN PIPELINE v0.5311** (Exp 181, 2026-08-09) — root cause was `_create_text_asset_object()` serialization (type_id + binary format). Rebuilt bundle verified locally (all NoArrows diffs = dots `d=8`).
**🔲 AWAITING RE-DEPLOY** — PS4 unreachable during Exp 181; the rebuilt `startmeup_v3.bundle` still needs uploading + boot test to confirm dots on-device.

## Song Details
- **Display Name:** drop pop candy / Reol
- **Artist:** Reol
- **BPM:** 130
- **Level ID:** custom/drop_pop_candy
- **Modes:** Standard, OneSaber, NoArrows, 90Degree (4 modes; 360Degree purged in Exp 175 — PS4 single-camera ~90° tracking)

## Deployed Files on PS4 (AFR base `/data/GoldHEN/AFR/CUSA12878/`)
| File | Content | Status |
|------|---------|--------|
| `BeatmapLevelsData/startmeup/startmeup_v3` | Per-song bundle (audio + 4 mode sets × 5 difficulties) | 🔄 Needs v0.5311 rebuild upload (12,534,145 B, Aug 9) |
| `aa/PS4/startmeup_pack_modes.bundle` | Patched Rolling Stones pack bundle (StartMeUp BeatmapLevelSO with 4 preview sets) | ✅ Deployed (7,905,425 B) |
| `aa/PS4/catalog_startmeup_modes.json` | Catalog (only rolling-stones entry changed, correct dec-stream CRC) | ✅ Deployed |

## Redirects.json Keys
- `"BeatmapLevelsData/startmeup"` → `"startmeup_v3"`
- `"aa/catalog.json"` → `"catalog_startmeup_modes.json"`
- `"therollingstones_pack_assets_all_a99482a8a3da9e991e5ae36f2fea209c.bundle"` → `"startmeup_pack_modes.bundle"`

## Pending Test (when PS4 is back online)
1. Rebuild per-song bundle with v0.5311 pipeline (already done — `/workspace/startmeup_v3.bundle`, 12,534,145 B).
2. Deploy to `startmeup_v3`, clear `bs_log.txt`.
3. Boot → Start Me Up → **NoArrows** → confirm notes are dots (no arrows).
4. Confirm **OneSaber** (single saber, all notes color 0) and **90Degree** (rotation events) play correctly.
5. On-device confirmation → integrate pack-patch build script into production pipeline (`tools/`).
