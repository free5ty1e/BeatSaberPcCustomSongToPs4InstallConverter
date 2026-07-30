## drop pop candy Replacement (PENDING PS4 TEST — 2026-07-28)

**Status:** Bundle built, **AWAITING DEPLOY + TEST**

**Song Details:**
- **Display Name:** drop pop candy / Reol
- **Artist:** Reol
- **BPM:** 130
- **Level ID:** custom/drop_pop_candy
- **Modes:** Standard, OneSaber, NoArrows, **90Degree**, **360Degree** (5 modes — 90Degree + 360Degree detected from actual beatmap files)

**Bundle File:** `custom_songs/startmeup_custom.bundle`
- Size: 39,570,295 bytes
- Audio: PCM16 FSB5, 224.3s

**Redirect:** `BeatmapLevelsData/startmeup → startmeup_v3`

**Test Plan:**
1. Deploy: `python3 full_custom_song_pipeline.py --song-dir songs_repo/50e4c2101cc079a98f88e80aa7091e60bb6d1d31 --target startmeup --pcm16 --no-pad --convert-to-v3 --enable-beatmap-mode-mapping --deploy --generate-config --deploy-config`
2. Launch Beat Saber Deluxe
3. Navigate to Rolling Stones pack → Start Me Up (now drop pop candy)
4. Select song → **check if mode selector shows OneSaber, NoArrows, 90Degree, 360Degree buttons**
5. Try playing in 90Degree and 360Degree modes (they have actual .dat files)
6. If crash: check PS4 log at `/data/GoldHEN/AFR/CUSA12878/bs_log.txt`

**Notes:**
- Phase 1 only clones Standard beatmap assets — all modes play Standard's difficulty patterns
- 90Degree and 360Degree Expert beatmaps exist in song_dir but are NOT yet compiled into unique TextAssets (Phase 2 work)
- This is the first test of `--enable-beatmap-mode-mapping` on PS4 hardware
