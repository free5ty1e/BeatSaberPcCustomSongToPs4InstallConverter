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
1. Deploy bundle + plugin: `python3 full_custom_song_pipeline.py --song-dir songs_repo/50e4c2101cc079a98f88e80aa7091e60bb6d1d31 --target startmeup --pcm16 --no-pad --convert-to-v3 --enable-beatmap-mode-mapping --deploy --generate-config --deploy-config`
2. Also deploy v0.8042 plugin: `lftp -u anonymous, -p 2121 192.168.100.117 -e "put beat_saber_deluxe.prx -o /data/GoldHEN/plugins/beat_saber_deluxe.prx; chmod 755 /data/GoldHEN/plugins/beat_saber_deluxe.prx; quit"`
3. Launch Beat Saber Deluxe (restart game required for new plugin)
4. Navigate to Rolling Stones pack → Start Me Up (now drop pop candy)
5. Select song → **check if mode selector shows OneSaber, NoArrows, 90Degree, 360Degree buttons**
6. Try playing in 90Degree and 360Degree modes (they have actual .dat files)
7. If crash: check PS4 log at `/data/GoldHEN/AFR/CUSA12878/bs_log.txt`
8. Verify plugin version in notification (should show v0.8042)

**Notes:**
- Phase 1 clones Standard beatmap assets — all modes play Standard's difficulty patterns. The mode selector buttons come from Phase 2 memory injection.
- 90Degree and 360Degree Expert beatmaps exist in song_dir but are NOT yet compiled into unique TextAssets (future work)
- **CRITICAL:** The v0.8042 plugin MUST be deployed. Phase 2 runs on the PS4 in the plugin, not in the pipeline.
