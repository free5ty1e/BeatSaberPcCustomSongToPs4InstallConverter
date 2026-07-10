---
name: song-selection-criteria
description: "Criteria for selecting custom Beat Saber songs to deploy"
metadata:
  type: reference
---

# Song Selection Criteria

Use this checklist when selecting a custom song for deployment.

## Requirements (ALL must be met)

- [ ] **3+ beatmaps**: At least Easy, Normal, AND Hard difficulties
  - Standard format preferred (e.g., `EasyStandard.dat`)
  - 90-degree or OneSaber acceptable for E/N/H if Standard not available (e.g., `Easy90Degree.dat`)
- [ ] **Not country music**: Any other genre is fine
- [ ] **Adequate quality**: Song should have a reasonable rating on BeatSaver (proving others find it playable)
- [ ] **Has audio file**: Must have `.egg` or `.wav` audio in the song directory
- [ ] **Info.dat accessible**: Must have `Info.dat` or `info.dat` with `_beatsPerMinute` and `_songTimeOffset`

## Nice-to-haves (bonus points, not required)

- Has visual variety: arcs (`sliders`), chains (`burstSliders`), walls (`_obstacles`)
- Has bomb notes (`_type: 3`)
- Pop, electronic, rock, or dance genres (known favorites)
- Under 3 minutes (faster test cycles)
- High note density (more engaging gameplay)

## Known Good Songs (already deployed)

| Slot | Custom Song | Artist | BPM |
|------|-------------|--------|-----|
| startmeup | Espresso | Sabrina Carpenter | 104 |
| angry | (TO BE REPLACED) | | |
| bitemyheadoff | Escaping the Ruins | | 160 |
| cantyouhearmeknocking | Spectre | ICHIRO | 128 |
| deadmanwalking | Finesse (Remix) | | 105 |
| gimmeshelter | How You Like That | BLACKPINK | 130 |
| icantgetnosatisfaction | Dreams Come True | | 99 |
| messitup | Powersnake | | 175 |
| paintitblack | Time Lapse | | 127 |
| sugarsoaker | Venom of Venus | | 164 |
| sympathyforthedevil | LIT | | 99 |
| wholewideworld | VOLUPTE | | 128 |

## How to Check

```bash
# List beatmaps for a song:
ls <song_dir>/*Standard.dat

# Check if sliders/arcs exist:
python3 -c "import json; d=json.load(open('<song_dir>/ExpertStandard.dat')); print('Sliders:', bool(d.get('_sliders'))); print('BurstSliders:', bool(d.get('_burstSliders')))"

# Check BPM and offset:
python3 -c "import json; d=json.load(open('<song_dir>/Info.dat')); print('BPM:', d.get('_beatsPerMinute')); print('Offset:', d.get('_songTimeOffset', 0))"
```
