# Rolling Stones Song Replacement Mapping

## The 12 Rolling Stones Songs in Beat Saber

These are the 12 official bundles that belong to the Rolling Stones music pack. Each will be hijacked by a custom community song.

| # | Bundle ID | Song Name | Album | Year | Custom Replacement | Status |
|---|-----------|-----------|-------|------|-------------------|--------|
| 1 | `startmeup` | Start Me Up | Tattoo You | 1981 | Espresso — Sabrina Carpenter | ✅ **Deployed** |
| 2 | `gimmeshelter` | Gimme Shelter | Let It Bleed | 1969 | TBD | ⬜ Pending |
| 3 | `icantgetnosatisfaction` | (I Can't Get No) Satisfaction | Out of Our Heads | 1965 | TBD | ⬜ Pending |
| 4 | `paintitblack` | Paint It Black | Aftermath | 1966 | TBD | ⬜ Pending |
| 5 | `sympathyforthedevil` | Sympathy for the Devil | Beggars Banquet | 1968 | TBD | ⬜ Pending |
| 6 | `cantyouhearmeknocking` | Can't You Hear Me Knocking | Sticky Fingers | 1971 | TBD | ⬜ Pending |
| 7 | `angry` | Angry | Hackney Diamonds | 2023 | TBD | ⬜ Pending |
| 8 | `bitemyheadoff` | Bite My Head Off | Hackney Diamonds | 2023 | TBD | ⬜ Pending |
| 9 | `messitup` | Mess It Up | Hackney Diamonds | 2023 | TBD | ⬜ Pending |
| 10 | `sugarsoaker` | Sugar Soaker | Hackney Diamonds | 2023 | TBD | ⬜ Pending |
| 11 | `deadmanwalking` | Dead Man Walking | Hackney Diamonds | 2023 | TBD | ⬜ Pending |
| 12 | `wholewideworld` | Whole Wide World | Hackney Diamonds | 2023 | TBD | ⬜ Pending |

## Plugin Redirect Table

The plugin's `open_hook()` needs to be extended with 12 redirect paths:

```cpp
if (strstr(path, "BeatmapLevelsData/startmeup"))
    np = AFR_BASE "/" TITLE_ID "/startmeup_v3";
else if (strstr(path, "BeatmapLevelsData/gimmeshelter"))
    np = AFR_BASE "/" TITLE_ID "/gimmeshelter_v3";
// ... etc for all 12
```

Each redirects to a unique bundle file at `/data/GoldHEN/AFR/CUSA12878/<bundleid>_v3`.

## Pipeline Command for Each Song

```bash
python3 tools/full_custom_song_pipeline.py \
  --song-dir ./custom_songs/<prepped_song> \
  --target <bundle_id> --pcm16 --no-pad --deploy
```

## Bundle Template Paths

Each Rolling Stones song has a template in the game dump:
```
/workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/<bundle_id>
```

The pipeline will use these as templates, replacing audio + beatmaps + metadata.

## Selection Criteria for Custom Replacements

- Must have Easy/Normal/Hard as Standard, 90Degree, or OneSaber
- Avoid 360Degree-only songs (unplayable on PS4 VR)
- PCM16 FSB5 format (lossless, no padding needed)
- Prefer songs with diverse note types (arrows, dots, chains, arcs, walls, bombs)
