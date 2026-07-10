---
name: supported-songs
description: "Track record of all custom song deployments and their sync status"
metadata:
  type: project
---

# Supported Songs & Deployment Status

## Active Deployments (13 Rolling Stones Slots)

| # | Slot ID | Custom Song | Artist | BPM | Beatmaps | Status | Notes |
|---|---------|-------------|--------|-----|----------|--------|-------|
| 1 | `startmeup` | Espresso | Sabrina Carpenter | 104 | 5/5 | ✅ Perfect sync (reference) | V3.3.0 native, BPMInfo.dat |
| 2 | `angry` | Rhythm Is A Dancer | Pegboard Nerds | 128 | 5/5 | ✅ Good sync | Replaced We All Lift Together |
| 3 | `bitemyheadoff` | Escaping the Ruins | | 160 | 5/5 | ✅ Good sync | |
| 4 | `cantyouhearmeknocking` | Spectre | ICHIRO | 128 | 5/5 | ⚠️ Sync OK, intro 9.4s | First note at b=20 (long intro) |
| 5 | `deadmanwalking` | Finesse (Remix) | | 105 | 5/5 | ✅ Good sync | |
| 6 | `gimmeshelter` | How You Like That | BLACKPINK | 130 | 5/5 | ⚠️ Sync OK, intro 6.9s | First note at b=15 (long intro) |
| 7 | `icantgetnosatisfaction` | Dreams Come True | | 99 | 5/5 | ✅ Good sync | |
| 8 | `livebythesword` | Take Me to the Beach | Imagine Dragons | 105 | 5/5 | ✅ Perfect sync | Has arcs, chains. Replaced MUSIC STAR |
| 9 | `messitup` | Powersnake | | 175 | 5/5 | ✅ Good sync | |
| 10 | `paintitblack` | Time Lapse | | 127 | 5/5 | ✅ Good sync | |
| 11 | `sugarsoaker` | Venom of Venus | | 164 | 5/5 | ✅ Good sync | |
| 12 | `sympathyforthedevil` | LIT | | 99 | 5/5 | ✅ Good sync | |
| 13 | `wholewideworld` | VOLUPTE | | 128 | 5/5 | ✅ Good sync | |

## Timeline of Sync Fixes

### v0.52 (Current)
- **Root Cause #1 - bpmData eb**: Pipeline computed bpmData.eb from Info.dat _beatsPerMinute instead of the beatmap's actual last-note time. Mappers use a slightly different effective BPM than Info.dat declares, causing progressive 3-6% desync.
- **Fix**: `load_bpm_regions()` now scans beatmap .dat files for the highest _time/b value and uses that as eb.

- **Root Cause #2 - bpmEvents empty**: V2→V3 converter set `bpmEvents=[]`. The PS4 game's BeatmapDataLoader requires bpmEvents to determine tempo — without it, the game defaults to BPM=60, causing 2x/0.5x speed desync.
- **Fix**: Converter now reads BPM from Info.dat and sets `bpmEvents=[{"b": 0, "m": <BPM>}]`.

### v0.51
- Initial 12-song redirect table
- V2→V3 beatmap converter
- Beatmap filename fallback (5-tier priority)

### v0.50
- Plugin proof of concept
- GoldHEN PRX hook on open() for AFR redirect
- PCM16 FSB5 audio

## Known Issues

| Issue | Affected Songs | Status |
|-------|---------------|--------|
| Long intro (>6s before first note) | gimmeshelter (6.9s), cantyouhearmeknocking (9.4s) | By design (mapper choice) |
| "Very very late" perception | gimmeshelter, cantyouhearmeknocking | User perceives as bug, but timing is correct per beatmap |
