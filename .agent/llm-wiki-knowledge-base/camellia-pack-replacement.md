---
name: camellia-pack-replacement
description: "Camellia Music Pack replacement: first full pack replacement (6 songs), PCM16 requirement confirmed, metadata behavior documented"
metadata:
  type: finding
  date: 2026-07-28
  experiments: [158, 159]
---

# Camellia Music Pack Replacement

The Camellia Music Pack was the first full song pack replacement (6 songs), confirming the pipeline works end-to-end for pack-level replacements.

## Songs Replaced

| Slot | BeatSaver ID | Replacement | Artist |
|------|-------------|-------------|--------|
| Crystallized | 12a | Bloom | ODESZA |
| CycleHit | 133 | Powerful | Major Lazer |
| ExitThisEarthsAtomosphere | 156 | Red Lips | GTA / Mendus |
| Ghost | 1bf | Lone Digger | Caravan Palace |
| LightItUp | 7e | Batshit | Sofi Tukker |
| WhatTheCat | 7f | G.O.M.D | Sickick |

## Required Pipeline Flags

All flags are **mandatory** for Camellia songs (and generally for all current pipeline usage):

```bash
python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song <MAP_ID> \
    --target <slot_name> \
    --song-name "Song Name" \
    --artist "Artist Name" \
    --pcm16 --no-pad --convert-to-v3 \
    --deploy --generate-config --deploy-config
```

- `--pcm16` — PCM16 FSB5 encoding (codec=2). HEVAG is blocked (Sony proprietary), Vorbis is blocked (FMOD/libvorbis codebook mismatch).
- `--no-pad` — Skip 12MB audio padding. PCM16 output is often larger than the original resource, so padding would waste space.
- `--convert-to-v3` — Convert V2 beatmaps to V3.2.0 format. Required for Beat Saber PS4.
- `--song-name` / `--artist` — Override display name. Format: "SongName / Artist" on the song name line; original artist blanked.

## Song Metadata Behavior

The `manage_song_metadata()` function (v0.5302+) has these behaviors:

1. **Combined display name:** `song_names[original_name] = f"{song_name} / {artist}"` — combines custom name and artist on the song name line
2. **Original artist blanking:** Looks up the original author via `beat_saber_song_ids.json` and sets `song_artists[original_author] = " "` (single space)
3. **Slot resolution:** Target name (e.g. "Crystallized") is resolved to the exact game song name via `_load_song_details()` and `_lookup_song_name()`

## Redirect Key Prefix

The `manage_redirect_config()` function auto-prepends `BeatmapLevelsData/` to target names if missing. This is critical because the plugin uses `strstr()` on full file paths — missing the prefix causes the redirect to never fire.

## Key Finding: PCM16 is Consistent Requirement

Confirmed across all experiments: PCM16 is the **only** working audio format for the current plugin and pipeline. Both HEVAG and Vorbis approaches are definitively blocked.

## See Also

- [[ps4-fsb5-pcm16-format]] — PCM16 FSB5 format details
- [[beatmap-conversion-pipeline]] — V2→V3 conversion
- [[song-metadata-storage]] — How metadata is stored and modified
- [[ps4-file-system-redirects]] — AFR redirect mechanism
