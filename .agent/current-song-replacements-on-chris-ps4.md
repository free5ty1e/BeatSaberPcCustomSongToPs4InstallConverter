# Current Song Replacements on Chris's PS4

> **Plugin:** Beat Saber Deluxe v0.8041 (v0.8040 baseline + redirect diagnostics)  
> **Pipeline:** v0.5327 (safe defaults: PCM16 + no-pad full audio + beatmap mode mapping/generators + V2→V3; stable `mass_bundles/` dir; build-all→deploy-once automation)
> **All 38 songs replaced** (13 Rolling Stones + 10 Billie Eilish + 9 Lizzo + 6 Chromeo-in-Camellia) with custom community songs.
> **Status:** 🟡 **EXP 200 FULL-FLEET REBUILD IN PROGRESS (2026-08-25)** — all 38 songs being rebuilt through the current pipeline (previous on-console song bundles were Aug-21-era stale: user saw only Standard mode on an RS custom song; blue-OneSaber fix from v0.5323 had never reached hardware). Deploy = one-shot pipeline pass: 38 songs + 4 fully-patched packs + catalog + redirects.json (43). See "Reproducible Deployment" below for the exact command list.
> **Verified on hardware (2026-08-25):** v0.5326 lizzo-only config boots clean, No Arrows gameplay OK (Exp 199 structure fix confirmed); log archived in `.ai_memory/experiment_logs/v0.5326_lizzo_noarrows_SUCCESS_boot.txt`.
> **Mode mapping:** every custom slot carries all 4 modes x the source's playable difficulties as beatmap TextAssets (verified in fresh builds; sources lacking a difficulty — e.g. CuzILoveYou has no ExpertPlus — correctly ship only what exists). The 4 configured DLC packs have all their BeatmapLevelSOs patched to expose the 4 preview modes with DISTINCT characteristic pathIDs (hardware-proven requirement, Exp 199). **Selector mechanics (Exp 200):** the in-game mode selector is driven by the PACK bundle's preview sets, not by per-song bundles — which is why custom slots showed Standard-only under the lizzo-only config (RS pack redirect absent) and why full-config deployment is required for customs to show 4 modes.

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

## How to Deploy

**SUPERSEDED** by "Reproducible Deployment" above (v0.5327). The old per-song
`--deploy` loop re-uploaded all pack bundles + catalog 38x and is no longer used.
`deploy_all.sh` remains OUTDATED (13 hardcoded Rolling Stones targets, pre-mode-mapping).
## How to Download & Deploy a New Song from BeatSaver

```bash
python3 /workspace/beat_saber_deluxe/tools/full_custom_song_pipeline.py \
  --download-beat-saver-song <beatsaver_map_key> \
  --target <slot_name> \
  --deploy
```

Find songs at https://beatsaver.com. The map key is the short ID in the URL (e.g. `2b641` from `beatsaver.com/maps/2b641`).

## Reproducible Deployment (fresh PS4 / fresh container) — v0.5327, 2026-08-25

**Everything below is pipeline automation — zero manual file manipulation.** Run from
`/workspace/beat_saber_deluxe/`. Prerequisites: `ps4_dump/CUSA12878-patch/` origin dump
present (source of the Addressables catalog + original pack bundles), song sources in
`/workspace/beat-saber-ps4-custom-songs/songs_repo/` (+ `songs/chromeo_backout/`),
PS4 online at 192.168.100.117:2121 (GoldHEN AFR), plugin `beat_saber_deluxe.prx` v0.8040+
already in `/data/GoldHEN/plugins/`.

```bash
cd /workspace/beat_saber_deluxe

# 0. Sanity: tests must pass before touching the console
python3 -m pytest tests/ -q

# 1. Build ALL 36 DLC pack bundles (4-mode preview patch, distinct pathIDs) +
#    regenerate the merged catalog for exactly the configured packs.
#    (--packs omitted = all 36; catalog output covers only configured packs)
python3 tools/build_pack_mode_bundles.py --write \
  --dump-dir /workspace/ps4_dump/CUSA12878-patch

# 2. Build all 38 custom songs through the per-song pipeline (v0.5314+ defaults:
#    --pcm16 --no-pad full audio, V2->V3 conversion, mode mapping + generators),
#    then deploy EVERYTHING in one consistent pass:
#      - mass-uploads all 38 song bundles
#      - uploads the 4 configured pack bundles + merged catalog (bundles BEFORE redirects)
#      - regenerates + uploads redirects.json (38 songs + 4 pack pairs + aa/catalog.json)
#      - runs full post-deploy validation (--verify-ps4)
python3 development/scripts/build_deploy_all38.py            # build + deploy
#   variants:
#   python3 development/scripts/build_deploy_all38.py --build-only   # local builds only
#   python3 development/scripts/build_deploy_all38.py --dry-run      # print commands

# 2b. Equivalent manual two-step (what the script wraps):
#   per song (38x): python3 tools/full_custom_song_pipeline.py \
#       --song-dir <source_dir> --target <slot> --pcm16 --no-pad \
#       --output /workspace/beat_saber_deluxe/mass_bundles/<slot>_v3.bundle
#     (the 6 Chromeo backout sources additionally need: --audio <source_dir>/audio.fsb)
#   then once:
#   python3 tools/full_custom_song_pipeline.py \
#       --deploy-mass-bundles --deploy-pack-modes --deploy-config --verify-ps4

# 3. Optional re-deploy of just the pack/catalog/redirect layer (songs untouched):
python3 tools/full_custom_song_pipeline.py \
    --deploy-pack-modes --deploy-config --verify-ps4

# 4. Single-pack isolation testing (e.g. lizzo only): use a config whose
#    pack_modes.packs lists only that pack (catalog stays a matched pair):
python3 tools/full_custom_song_pipeline.py \
    --config development/ps4_config_lizzo_only.json \
    --deploy-pack-modes --deploy-config --verify-ps4

# 5. Clear the boot log before a user test (log hygiene only):
lftp -u anonymous, -p 2121 192.168.100.117 -e "rm /data/GoldHEN/AFR/CUSA12878/bs_log.txt; bye"
```

**Expected end state:** 42 files deployed into `/data/GoldHEN/AFR/CUSA12878/`
(38 `<slot>_v3.bundle` songs + 4 `<pack>_pack_modes_assets_all_<hash>.bundle`) plus
`catalog_pack_modes.json`, `redirects.json` (43 redirects: 38 songs + 4 packs +
aa/catalog.json), `song_metadata.json`, `features.json`. Every custom song and every
song in the 4 patched packs shows **Standard / OneSaber / NoArrows / 90Degree**
(5 difficulties each). Post-deploy validation prints `Post-deploy validation PASSED`.

## Build History

| Date | Reason | Songs Built/Modified |
|------|--------|---------------------|
| 2026-08-25 | Full-fleet rebuild through v0.5327 (blue OneSaber sources verified, distinct-pathID pack structure, stable mass_bundles dir); first fully-pipeline-automated deploy of all 38 songs + 4 packs after Exp 199 structure fix. User verified lizzo No Arrows gameplay OK on v0.5326 lizzo-only config. | All 38 |
| 2026-08-12 | Mass re-run all 38 songs (pipeline v0.5316): mode mapping + generators, full audio, V2→V3. Chromeo 6 rebuilt from PS4 extraction (V4→V3.2.0 decode). Fixed generator KeyError on omitted V3 fields. | All 38 |
| 2026-08-11 | Espresso → `startmeup` (V2.1.0, 5 diffs); boot test PASSED; first full-audio no-pad build | startmeup |
