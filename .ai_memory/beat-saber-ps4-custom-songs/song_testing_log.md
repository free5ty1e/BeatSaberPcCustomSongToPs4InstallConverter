# Song Testing Log

Records which custom songs have been tested on PS4, their sync status, and any issues.

## Status Legend
- ✅ **Perfect** — Sync is correct, full song plays without issues, score saves
- ⚠️ **Minor Issues** — Sync slightly off, but playable
- ❌ **Broken** — Major desync, crashes, or doesn't load
- ⏳ **Not yet tested** — Deployed but not gameplay tested

## Test Results

### Rolling Stones Replacements

| Date | Song | Artist | BPM | Duration | Audio Format | Sync | Score Saves | Notes |
|------|------|--------|-----|----------|-------------|------|-------------|-------|
| 2026-07-08 | Espresso | Sabrina Carpenter | 104 | 177.5s | PCM16 FSB5 | ✅ Perfect | ✅ | **bpmData sync fixed!** All note types visible. |
| 2026-06-28 | Rhythm Is A Dancer | Pegboard Nerds | 128 | ~155s | PCM16 FSB5 | ✅ | ✅ | Tested and confirmed working with bomb notes. |
| 2026-06-28 | Escaping the Ruins | MDK / Gareth Coker | 160 | ~140s | PCM16 FSB5 | ✅ | ✅ | 5/5 beatmaps, all sync correctly. |
| 2026-06-28 | Spicy | aespa | 115 | ~192s | PCM16 FSB5 | ✅ | ✅ | K-pop, all diffs playable. |
| 2026-06-28 | Finesse (Remix) | Various | 105 | ~190s | PCM16 FSB5 | ✅ | ✅ | Pop, good sync. |
| 2026-06-28 | Dreams Come True | Various | 99 | ~230s | PCM16 FSB5 | ✅ | ✅ | K-pop, all note types work. |
| 2026-06-28 | Powersnake | Brothers of Metal | 175 | ~200s | PCM16 FSB5 | ✅ | ✅ | Power metal, high energy. |
| 2026-06-28 | Time Lapse | TheFatRat | 127 | ~210s | PCM16 FSB5 | ✅ | ✅ | Electronic, excellent sync. |
| 2026-06-28 | Venom of Venus | Powerwolf | 164 | ~220s | PCM16 FSB5 | ✅ | ✅ | Power metal, heavy song. |
| 2026-06-28 | LIT | Polyphia | 99 | ~210s | PCM16 FSB5 | ✅ | ✅ | Instrumental rock, technical. |
| 2026-06-28 | VOLUPTE | REZZ / Tare | 128 | ~190s | PCM16 FSB5 | ✅ | ✅ | Electronic/bass. |
| 2026-06-29 | Yes I'm A Mess | AJR | 184 | ~165s | PCM16 FSB5 | ⏳ | ⏳ | Not yet tested on PS4. |
| 2026-06-29 | Take Me to the Beach | Imagine Dragons | 105 | ~190s | PCM16 FSB5 | ⏳ | ⏳ | Not yet tested on PS4. |

### Other Songs Tested

| Date | Song | Artist | BPM | Duration | Audio Format | Sync | Score Saves | Notes |
|------|------|--------|-----|----------|-------------|------|-------------|-------|
| 2026-06-28 | Drop Pop Candy | Reol | 130 | 224s | PCM16 FSB5 | ✅ | ✅ | v0.50 alpha — first working custom song. 8 beatmaps including 360-degree. |
| 2026-06-28 | Bruises | Fox Stevenson | 174 | 224.8s | PCM16 FSB5 | ❌ | N/A | Desynced — beatmap appears poorly authored. |
| 2026-06-28 | Bruises (lapped) | Fox Stevenson | 174 | 678.6s | PCM16 FSB5 | ❌ | N/A | Lapped version — wrongfully extended audio. |
| 2026-07-11 | 360 | Charli xcx | 120 | ~203s | PCM16 FSB5 | ❌ | N/A | **Removed.** Song has 360-degree characteristics. Not suitable for PS4 VR. Replaced with Duvet. |
| 2026-07-14 | Espresso (Start Me Up slot) | Sabrina Carpenter | 104 | ~177s | PCM16 FSB5 | ✅ Perfect | ✅ | **v0.64 redirect test** — No crash, full gameplay verified on Hard difficulty. v0.64 removes all IL2CPP hooks; redirect-only stable. |
| 2026-08-09 | drop pop candy (Start Me Up slot) | Reol | 130 | 224s | PCM16 FSB5 | ✅ | ✅ | **Mode mapping (v0.5311):** NoArrows ✅ (dots confirmed on-device), OneSaber ✅ (single saber). Standard not re-tested this cycle. **90Degree NOT tested yet** — selector button was hidden until Exp 182 pid fix (was pointing at 360Degree characteristic); rebuilt pack bundle deployed Aug 9, awaiting boot test. |

### Billie Eilish Replacements (Deployed 2026-07-11, Not Yet Tested)

| Slot | Custom Song | Artist | BPM | Duration | Beatmaps | Sync | Notes |
|------|-------------|--------|-----|----------|----------|------|-------|
| Oxytocin | Overdose | Natori | 118 | 193.9s | 5/5 | ⏳ | J-pop/rock. V2→V3 converted. PCM16. |
| AllTheGoodGirlsGoToHell | Mirror | Ado | 114 | 180.6s | 5/5 | ⏳ | J-pop. V2→V3 converted. PCM16. |
| YouShouldSeeMeInACrown | Show | Ado | 132 | 191.3s | 5/5 | ⏳ | J-pop. V2→V3 converted. PCM16. |
| Bellyache | ATTITUDE | IVE | 118 | 197.7s | 5/5 | ⏳ | K-pop. V2→V3 converted. PCM16. |
| BuryAFriend | Baddie | IVE | 160 | 156.7s | 5/5 | ⏳ | K-pop. V2→V3 converted. PCM16. |
| IDidntChangeMyNumber | Take Me to the Beach | Imagine Dragons | 105 | 167.0s | 5/5 | ⏳ | Pop rock. V2→V3 converted. PCM16. |
| HappierThanEver | Cosmic | Red Velvet | 106 | 227.3s | 5/5 | ⏳ | K-pop. V2→V3 converted. PCM16. |
| BadGuy | Odo | Ado | 128 | 209.1s | 5/5 | ⏳ | J-pop. V2→V3 converted. PCM16. |
| NDA | Duvet | Bôa | 186 | 203.4s | 5/5 | ⏳ | Alt-rock. V2→V3. PCM16. Replaced 360. |
| ThereforeIAm | Who's Laughing Now | Ava Max | 92 | 182.0s | 5/5 | ⏳ | Pop. V2→V3 converted. PCM16. |

### Lizzo Replacements (Deployed 2026-07-11, Not Yet Tested)

| Slot | Custom Song | Artist | BPM | Duration | Beatmaps | Sync | Notes |
|------|-------------|--------|-----|----------|----------|------|-------|
| 2BeLoved | Yes I'm A Mess | AJR | 184 | 166.6s | 5/5 | ⏳ | Pop. V2→V3. PCM16. Also used in gimmeshelter. |
| AboutDamnTime | The Middle | Jimmy Eat World | 162 | 168.6s | 5/5 | ⏳ | Pop punk. V2→V3. PCM16. |
| CuzILoveYou | Bring It On | Giga-P | 160 | 235.5s | 4/5 | ⏳ | Electronic. V2→V3. Missing one diff. |
| EverybodysGay | Queencard | (G)I-DLE | 130 | 163.5s | 5/5 | ⏳ | K-pop. V2→V3. PCM16. |
| GoodAsHell | Do You Wanna Taste It | Wig Wam | 184 | 178.8s | 5/5 | ⏳ | Rock. V2→V3. PCM16. |
| Juice | Blame | Calvin Harris | 128 | 208.1s | 5/5 | ⏳ | EDM/pop. V2→V3. PCM16. |
| Tempo | Bruises | Fox Stevenson | 174 | 224.8s | 5/5 | ⏳ | Drum&Bass. **Previously desynced!** |
| TruthHurts | Genie In A Bottle | DisasterTheory | 177 | 208.0s | 5/5 | ⏳ | EDM. V2→V3. PCM16. |
| Worship | Best Day Of My Life | American Authors | 100 | 194.5s | 5/5 | ⏳ | Indie pop. V2→V3. PCM16. |

## Known Issues
1. **Bruises desync** — "Bruises" by Fox Stevenson previously had audio/beatmap mismatch. The same song hash is reused for the Tempo slot. May need testing.
2. **360 removed** — "360" by Charli xcx was deployed to NDA slot but removed due to 360-degree characteristics. Replaced with "Duvet" by Bôa.
3. **CuzILoveYou only 4 beatmaps** — "Bring It On" by Giga-P has only 4 Standard difficulty beatmaps.

## Pipeline Notes
- Use `--pcm16` flag for lossless audio (PCM16 FSB5, codec=2)
- V2 beatmaps use `_time` in BEATS — pipeline converts to seconds using BPM from `info.dat`
- Lapped detection: triggers when `max_note_time_in_seconds > audio_duration * 1.3`
- BEATS→seconds conversion: `time_seconds = time_beats * (60.0 / bpm)`
- `--download-beat-saver-song <key>` downloads from BeatSaver CDN (requires map key from beatsaver.com/maps/<key>)
- `--deploy` now auto-generates and auto-deploys redirects.json (no separate --deploy-config needed)

---
### 2026-07-15 — Plugin Toggle System Test (Exp 129)
| Date | Feature | Method | Result | Notes |
|------|---------|--------|--------|-------|
| 2026-07-15 | `--enable-plugin` | Pipeline CLI flag → FTP plugins.ini edit | ✅ Verified on PS4 | Uncommented entry under [CUSA12878] |
| 2026-07-15 | `--disable-plugin` | Pipeline CLI flag → FTP plugins.ini edit | ✅ Verified on PS4 | Commented out release + debug entries with `#;` |
| 2026-07-15 | BeatmapLevelSO CAB binary injection | inject_pack_bundle.py → raw byte replacement at CAB offset 79924 | 📦 Build complete / deploy blocked | Patched Espresso(1257B), Duvet(1222B), Time Lapse(1251B) CABs verified on disk. PS4 offline — needs AFR redirect or direct bundle patching when powered on.
