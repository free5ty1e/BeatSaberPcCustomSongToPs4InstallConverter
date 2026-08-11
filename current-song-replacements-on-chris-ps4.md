# drop pop candy Replacement (Start Me Up slot)

## Current Status (2026-08-11)

**✅ MODE SELECTOR GAP CLOSED** (Exp 180, 2026-08-08) — Standard/OneSaber/NoArrows visible + working on-device.
**✅ NoArrows BUG FIXED IN PIPELINE v0.5311** (Exp 181, 2026-08-09) — root cause was `_create_text_asset_object()` serialization (type_id + binary format). Rebuilt bundle verified locally (all NoArrows diffs = dots `d=8`).
**✅ 90DEGREE ROOT CAUSE FOUND + FIXED** (Exp 182, 2026-08-09) — 90Degree had NEVER been visible: the pack bundle's 90Degree preview slot pointed at the **360Degree** characteristic (requires360=1) which the game hides. Characteristic pathIDs were mislabeled repo-wide; all corrected to verified values (90Degree=`-5995858427784384822`).
**🔄 FULL-AUDIO REBUILD + IDEMPOTENCY FIX** (Exp 183, 2026-08-11) — previously-deployed bundle was **TRUNCATED to 69.76s** (built `--pcm16` without `--no-pad` → clipped to 12MB resource). v0.5314 baked PCM16 + no-pad + mode mapping + V2→V3 into the pipeline defaults; v0.5315 fixed the mode-mapping idempotency bug. Rebuilt `startmeup_v3.bundle` = **39,697,727 B, full 224.31s audio, all 4 modes** — reproducibly from the source song dir. **🔴 DEPLOY PENDING (PS4 FTP down / PS4 off).**

## Song Details
- **Display Name:** drop pop candy / Reol
- **Artist:** Reol
- **BPM:** 130
- **Level ID:** custom/drop_pop_candy
- **Modes:** Standard, OneSaber, NoArrows, 90Degree (4 modes; 360Degree purged in Exp 175 — PS4 single-camera ~90° tracking)

## Deployed Files on PS4 (AFR base `/data/GoldHEN/AFR/CUSA12878/`)
| File | Content | Status |
|------|---------|--------|
| `BeatmapLevelsData/startmeup/startmeup_v3` | Per-song bundle (audio + 4 mode sets × 5 difficulties) | 🔴 **STALE (12,534,145 B, Aug 9 — truncated 69.76s audio). REPLACE with 39,697,727 B full-audio build.** |
| `startmeup_pack_modes.bundle` | Patched Rolling Stones pack bundle (StartMeUp BeatmapLevelSO with 4 preview sets, CORRECTED 90Degree pid) | ✅ Deployed (7,905,425 B, Aug 9) |
| `catalog_startmeup_modes.json` | Catalog (only rolling-stones entry changed, dec-stream CRC 3924036563) | ✅ Deployed (801,445 B, Aug 9) |

## Redirects.json Keys
- `"BeatmapLevelsData/startmeup"` → `"startmeup_v3"`
- `"aa/catalog.json"` → `"catalog_startmeup_modes.json"`
- `"therollingstones_pack_assets_all_a99482a8a3da9e991e5ae36f2fea209c.bundle"` → `"startmeup_pack_modes.bundle"`

## Deploy Checklist (Exp 183 — ready, awaiting PS4)
1. Upload `/workspace/startmeup_v3.bundle` (39,697,727 B) → `BeatmapLevelsData/startmeup/startmeup_v3` (replaces the truncated Aug 9 build).
2. Upload `beat_saber_deluxe/features.json` (2 runtime flags only — mode-mapping flag removed in v0.5314).
3. Clear `/data/GoldHEN/AFR/CUSA12878/bs_log.txt` before the boot test.

## Pending Test (Exp 182 + 183 — after deploy)
1. Boot → Start Me Up → confirm **90Degree** button NOW APPEARS in the selector (was hidden before).
2. Confirm song plays **full 224.31s** (previous bundle was truncated at 69.76s — the audio-truncation bug).
3. Test the source song's **90Degree Expert** (Drop Pop Candy ships its own 90Degree Expert).
4. Test generated **90Degree Easy/Normal/Hard/ExpertPlus** (rotation events every 8 beats) — confirm rotation works on PS4.
5. Sanity: NoArrows (dots) + OneSaber still work after bundle swap; lighting events use correct `et` types.
6. On-device confirmation → integrate pack-patch build script into production pipeline (`tools/`).
