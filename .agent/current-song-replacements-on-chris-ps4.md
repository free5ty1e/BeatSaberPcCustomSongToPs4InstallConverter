# Current Song Replacements on Chris's PS4

> **Plugin:** Beat Saber Deluxe v0.8040  
> **Pipeline:** v0.5316 (safe defaults: PCM16 + no-pad full audio + beatmap mode mapping/generators + V2→V3)
> **All 38 songs replaced** (13 Rolling Stones + 10 Billie Eilish + 9 Lizzo + 6 Chromeo) with custom community songs.
> **Last rebuilt:** 2026-08-12 — **mass re-run of all 38 songs** through the per-song pipeline (mode mapping + generators). Chromeo 6 rebuilt from PS4 bundle extraction (their source dirs were deleted; beatmaps reconstructed V4→V3.2.0).
> **Status:** ✅ **DEPLOYED (2026-08-12)** — all 38 bundles + `redirects.json` (39 redirects) + `song_metadata.json` verified on PS4 (sizes match local builds exactly). Plugin v0.8040 confirmed. **AWAITING USER TEST** — spot-check Chromeo slots (all 6), new Billie songs (Oxytocin/NDA/ThereforeIAm), 90Degree mode, full audio lengths.
> **Mode mapping:** every slot now carries **Standard 5/5 + OneSaber 5/5 + NoArrows 5/5 + 90Degree 5/5** (generated gap-fill modes).
> **Deploy note:** the old `deploy_all.sh` is **OUTDATED** (13 hardcoded Rolling Stones targets, `_v3` paths, no mode mapping). Use the per-song pipeline invocation (see "How to Deploy").

## Rolling Stones Replacements (13 songs)

| # | Slot ID | Custom Song | Artist | BPM | Beatmaps | First Note | Sync |
|---|---------|-------------|--------|-----|----------|------------|------|
| 1 | `startmeup` | Espresso | Sabrina Carpenter | 104 | 5/5 | 2.3s | ✅ |
| 2 | `angry` | Rhythm Is A Dancer | Pegboard Nerds | 128 | 5/5 | 1.9s | ✅ |
| 3 | `bitemyheadoff` | Escaping the Ruins | MDK / Gareth Coker | 160 | 5/5 | 5.5s | ✅ |
| 4 | `cantyouhearmeknocking` | Spicy | aespa | 115 | 5/5 | 3.7s | ✅ |
| 5 | `deadmanwalking` | Finesse (Remix) | Various | 105 | 5/5 | 2.3s | ✅ |
| 6 | `gimmeshelter` | Yes I'm A Mess | AJR | 184 | 5/5 | 2.6s | ⏳ |
| 7 | `icantgetnosatisfaction` | Dreams Come True | Various | 99 | 5/5 | 2.9s | ✅ |
| 8 | `livebythesword` | Take Me to the Beach | Imagine Dragons | 105 | 5/5 | 2.3s | ⏳ |
| 9 | `messitup` | Powersnake | Brothers of Metal | 175 | 5/5 | 2.7s | ✅ |
| 10 | `paintitblack` | Time Lapse | TheFatRat | 127 | 5/5 | 1.9s | ✅ |
| 11 | `sugarsoaker` | Venom of Venus | Powerwolf | 164 | 5/5 | 2.9s | ✅ |
| 12 | `sympathyforthedevil` | LIT | Polyphia | 99 | 5/5 | 2.4s | ✅ |
| 13 | `wholewideworld` | VOLUPTE | REZZ / Tare | 128 | 5/5 | 2.8s | ✅ |

## Billie Eilish Replacements (10 songs)

| # | Slot ID | Custom Song | Artist | BPM | Beatmaps | First Note | Sync |
|---|---------|-------------|--------|-----|----------|------------|------|
| 1 | `Oxytocin` | Overdose | Natori | 118 | 5/5 | 2.0s | ⏳ |
| 2 | `AllTheGoodGirlsGoToHell` | Mirror | Ado | 114 | 5/5 | 2.1s | ⏳ |
| 3 | `YouShouldSeeMeInACrown` | Show | Ado | 132 | 5/5 | 2.7s | ⏳ |
| 4 | `Bellyache` | ATTITUDE | IVE | 118 | 5/5 | 2.0s | ⏳ |
| 5 | `BuryAFriend` | Baddie | IVE | 160 | 5/5 | 3.4s | ⏳ |
| 6 | `IDidntChangeMyNumber` | Take Me to the Beach | Imagine Dragons | 105 | 5/5 | 2.3s | ⏳ |
| 7 | `HappierThanEver` | Cosmic | Red Velvet | 106 | 5/5 | 1.7s | ⏳ |
| 8 | `BadGuy` | Odo | Ado | 128 | 5/5 | 1.8s | ⏳ |
| 9 | `NDA` | Duvet | Bôa | 186 | 5/5 | 1.6s | ⏳ |
| 10 | `ThereforeIAm` | Who's Laughing Now | Ava Max | 92 | 5/5 | 2.0s | ⏳ |

> **Note:** NDA slot was originally assigned "360" by Charli xcx but replaced with Duvet by Bôa because the 360-degree characteristics made it unsuitable for PS4 VR play.

## Lizzo Replacements (9 songs)

| # | Slot ID | Custom Song | Artist | BPM | Beatmaps | First Note | Sync |
|---|---------|-------------|--------|-----|----------|------------|------|
| 1 | `2BeLoved` | Yes I'm A Mess | AJR | 184 | 5/5 | 2.6s | ⏳ |
| 2 | `AboutDamnTime` | The Middle | Jimmy Eat World | 162 | 5/5 | 3.0s | ⏳ |
| 3 | `CuzILoveYou` | Bring It On | Giga-P | 160 | 5/5 (4/5 in Lizzo?) | 3.0s | ⏳ |
| 4 | `EverybodysGay` | Queencard | (G)I-DLE | 130 | 5/5 | 2.8s | ⏳ |
| 5 | `GoodAsHell` | Do You Wanna Taste It | Wig Wam | 184 | 6/5 | 4.4s | ⏳ |
| 6 | `Juice` | Blame | Calvin Harris | 128 | 5/5 | 1.9s | ⏳ |
| 7 | `Tempo` | Bruises | Fox Stevenson | 174 | 5/5 (note: prev desync!) | 2.1s | ⏳ |
| 8 | `TruthHurts` | Genie In A Bottle | DisasterTheory | 177 | 5/5 | 2.0s | ⏳ |
| 9 | `Worship` | Best Day Of My Life | American Authors | 100 | 5/5 | 1.8s | ⏳ |

> **Note:** The Tempo slot uses "Bruises" which was previously tested and had desync issues. May need lapped audio handling.


## Camellia Music Pack Replacements (6 songs — Chromeo Expansion)

| # | Slot ID | Custom Song | Artist | BPM | Beatmaps | First Note | Sync |
|---|---------|-------------|--------|-----|----------|------------|------|
| 1 | `Crystallized` | Sexy Socialite | Chromeo | 142 | 5/5 | 1.8s | ✅ |
| 2 | `CycleHit` | Jealous (I Ain't With It) | Chromeo | 129 | 5/5 | 2.1s | ✅ |
| 3 | `ExitThisEarthsAtomosphere` | 'Roni Got Me Stressed Out | Chromeo | 117 | 5/5 | 2.2s | ✅ |
| 4 | `Ghost` | Green Light (Chromeo Remix) | Lorde, Chromeo | 121 | 5/5 | 1.9s | ✅ |
| 5 | `LightItUp` | 1999 | Charli XCX & Troye Sivan | 124 | 5/5 | 1.9s | ✅ |
| 6 | `WhatTheCat` | FANCY | TWICE | 132 | 5/5 | 2.3s | ✅ |

## Total: 38 Custom Songs Deployed

## How to Deploy (Full — per-song pipeline)

```bash
cd /workspace/beat_saber_deluxe
# For each song: build + deploy with the pipeline (mode mapping + generators baked in)
python3 tools/full_custom_song_pipeline.py \
  --song-dir <source_dir> \
  --audio <source_dir>/audio.fsb \     # only for Chromeo back-out dirs
  --target <slot> \
  --template /workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/<slot> \
  --output /tmp/opencode/mass_build/<slot>_v3.bundle \
  --deploy
```

This deploys:
- Plugin (v0.8040) → `/data/GoldHEN/plugins/beat_saber_deluxe.prx`
- Bundles → `/data/GoldHEN/AFR/CUSA12878/{slot}_v3` (redirected via `redirects.json`)
- `redirects.json` / `song_metadata.json` → `/data/GoldHEN/AFR/CUSA12878/`

> **⚠️ `deploy_all.sh` is OUTDATED** — it hardcodes 13 Rolling Stones targets with `_v3` paths and predates beatmap mode mapping. Do not use it for full deploys.

## How to Download & Deploy a New Song from BeatSaver

```bash
python3 /workspace/beat_saber_deluxe/tools/full_custom_song_pipeline.py \
  --download-beat-saver-song <beatsaver_map_key> \
  --target <slot_name> \
  --deploy
```

Find songs at https://beatsaver.com. The map key is the short ID in the URL (e.g. `2b641` from `beatsaver.com/maps/2b641`).

## Build History

| Date | Reason | Songs Built/Modified |
|------|--------|---------------------|
| 2026-08-12 | Mass re-run all 38 songs (pipeline v0.5316): mode mapping + generators, full audio, V2→V3. Chromeo 6 rebuilt from PS4 extraction (V4→V3.2.0 decode). Fixed generator KeyError on omitted V3 fields. | All 38 |
| 2026-08-11 | Espresso → `startmeup` (V2.1.0, 5 diffs); boot test PASSED; first full-audio no-pad build | startmeup |
