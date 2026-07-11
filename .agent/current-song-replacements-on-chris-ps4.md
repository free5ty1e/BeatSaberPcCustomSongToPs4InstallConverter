# Current Song Replacements on Chris's PS4

> **Plugin:** Beat Saber Deluxe v0.53  
> **All 13 Rolling Stones slots replaced** with custom community songs.  
> **Last rebuilt:** 2026-07-10 (v0.53 - c field color fix)  
> **Status:** ✅ All songs fully synchronized

## Replacement Table

| # | Slot ID | Custom Song | Artist | BPM | Beatmaps | First Note | Sync |
|---|---------|-------------|--------|-----|----------|------------|------|
| 1 | `startmeup` | Espresso | Sabrina Carpenter | 104 | 5/5 | 2.3s | ✅ |
| 2 | `angry` | Rhythm Is A Dancer | Pegboard Nerds | 128 | 5/5 | 1.9s | ✅ |
| 3 | `bitemyheadoff` | Escaping the Ruins | Various | 160 | 5/5 | 5.5s | ✅ |
| 4 | `cantyouhearmeknocking` | Spicy | aespa | 115 | 5/5 | 3.7s | ✅ |
| 5 | `deadmanwalking` | Finesse (Remix) | Various | 105 | 5/5 | 2.3s | ✅ |
| 6 | `gimmeshelter` | Yes I'm A Mess | AJR | 184 | 5/5 | 2.6s | ✅ |
| 7 | `icantgetnosatisfaction` | Dreams Come True | Various | 99 | 5/5 | 2.9s | ✅ |
| 8 | `livebythesword` | Take Me to the Beach | Imagine Dragons | 105 | 5/5 | 2.3s | ✅ |
| 9 | `messitup` | Powersnake | Various | 175 | 5/5 | 2.7s | ✅ |
| 10 | `paintitblack` | Time Lapse | Various | 127 | 5/5 | 1.9s | ✅ |
| 11 | `sugarsoaker` | Venom of Venus | Various | 164 | 5/5 | 2.9s | ✅ |
| 12 | `sympathyforthedevil` | LIT | Various | 99 | 5/5 | 2.4s | ✅ |
| 13 | `wholewideworld` | VOLUPTE | Various | 128 | 5/5 | 2.8s | ✅ |

## How to Deploy

```bash
cd /workspace/beat_saber_deluxe
./deploy_all.sh --debug
```

This deploys:
- Plugin (v0.53) → `/data/GoldHEN/plugins/beat_saber_deluxe.prx`
- All 13 bundles → `/data/GoldHEN/AFR/CUSA12878/{slot}_v3`

## How to Rebuild a Single Song

```bash
python3 /workspace/beat_saber_deluxe/tools/full_custom_song_pipeline.py \
  --song-dir <song_repo_hash_dir> \
  --pcm16 --no-pad \
  --target <slot_name> \
  --output /workspace/beat_saber_deluxe/custom_songs/<slot>_custom_v3.bundle \
  --convert-to-v3
```

## Build History

| Date | Reason | Songs Rebuilt |
|------|--------|---------------|
| 2026-07-10 | Full rebuild all 13 — bpmEvents fix for V3, long-intro replacements | All 13 |
