# Custom Level: test_song

## Files Needed

1. `test_song_metadata.json` - Level metadata (edit this)
2. `test_song_Easy.dat` through `test_song_ExpertPlus.dat` - Beatmap data
3. `audio.ogg` - Song audio (320kbps OGG format)
4. `cover.png` - Cover image (512x512 PNG)

## Metadata Fields

| Field | Description | Example |
|-------|-------------|---------|
| levelId | Unique identifier | test_song |
| levelName | Display name | My Custom Song |
| songName | Song title | My Custom Song |
| songAuthorName | Artist | Artist Name |
| levelAuthorName | Mapper | Mapper Name |
| beatsPerMinute | BPM | 120.0 |
| previewDuration | Preview length (sec) | 30.0 |

## Difficulty Settings

| Difficulty | Rank | NJMS | Notes |
|------------|------|------|-------|
| Easy | 1 | 10 | Beginner |
| Normal | 3 | 12 | Medium |
| Hard | 5 | 14 | Hard |
| Expert | 7 | 16 | Expert |
| ExpertPlus | 9 | 18 | Expert+ |

## Next Steps

1. Edit the metadata JSON
2. Create beatmap data (use Beat Saber Editor or tools)
3. Add audio and cover art
4. Use Unity 2022.3 to package into AssetBundle
5. Test with the plugin
