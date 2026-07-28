
## Espresso Replacement (PENDING TEST — 2026-07-17)

**Status:** Bundle built and deployed, AWAITING USER TEST

**Song Details:**
- **Display Name:** EspressoCustomBeatmapLevel
- **Artist:** Sabrina Carpenter
- **BPM:** 126.5
- **Level ID:** custom/espresso
- **Modes:** Standard, OneSaber, NoArrows, 90Degree, 360Degree (5 modes)

**Bundle File:** `rollingstones_pack_patched.bundle`
- Size: 7,905,515 bytes (+2,712 from original)
- CRC: `0xdc8b314f` ✅ (matches Addressables catalog)

**Redirect Config:**
```json
"therollingstones_pack_assets_all_a99482a8a3da9e991e5ae36f2fea209c": "rollingstones_pack_patched.bundle"
```

**Test Plan:**
1. Launch Beat Saber Deluxe
2. Navigate to Rolling Stones pack → Espresso song
3. Verify: custom display name, artist, 5 modes visible in selector
4. If crash: check ps4_bs_log.txt for CE-34878-0 or m_BundleSize validation error

**Notes:**
- This is the first attempt at modifying the Rolling Stones pack bundle to add display metadata and mode support
- Previous attempts (Exp 136-142) all failed due to Addressables catalog CRC validation
- Exp 142 achieved CRC matching but crashed — likely due to size validation or invalid pathIDs
- If this test fails, next approach: uncompressed block injection (zero size impact) + GF(2) CRC correction

