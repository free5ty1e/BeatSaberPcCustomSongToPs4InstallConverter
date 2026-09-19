# Beat Saber Custom Song Preferences

## User Preferences (from project context)

### Difficulty Requirements

- **MUST HAVE**: difficulty levels Easy, Normal, Hard
- **AVOID**: Songs with only Expert or Expert+ (user cannot play those)

### Song Sources to Try

1. **BeatSaver** (primary) - https://beatsaver.com
   - API confirmed WORKING (2026-09-18, Exp 219 audit): `https://api.beatsaver.com/maps/id/<ID>`
     for metadata + difficulty lists; map ZIPs download from the version's `downloadURL`
     (CDN). The legacy `/maps/id/<ID>/download` endpoint returns 404.
   - Search: `https://api.beatsaver.com/search/text/<page>?q=<query>`
   - Note: `upvotes`/`downvotes`/`downloads` fields return 0 in current API responses —
     don't rely on them for quality ranking; download and inspect chart note counts instead.
2. **BeatLeader** (working) - https://api.beatleader.xyz
   - Has song data but not direct downloads
3. **ScoreSaber Reloaded** - Currently down
4. **BeastSaber** - https://bsaber.com

### Difficulty Selection Rule (enforced in example docs since v0.5339)

- **MUST HAVE native Easy + Normal + Hard** charts from the mapper.
- Expert/Expert+ gaps are fine — the pipeline auto-fills them from the map's own
  closest difficulty (`fill_missing_standard_difficulties`, v0.5338).
- Easy/Normal/Hard must never be clones — if a map lacks any of them, pick a different map.
- Quality check before committing a song to the docs: download the map and verify the
  per-difficulty note counts form a real progression (Easy < Normal < Hard < Expert).
  API-qualified maps with duplicate/flat charts (same note count across difficulties)
  are lazy conversions — reject them.

### What to Download

- Full song packages (ZIP files with info.dat, beatmaps, audio)
- Focus on popular/community-rated songs
- Must include: Easy, Normal, Hard difficulties minimum
- Audio format: .ogg or .wav preferred

### Notes for Future Searches

- User prefers songs with multiple difficulty options
- Avoid tech-only/high-difficulty maps
- Look for "balanced" or "beginner friendly" tags
- Popular artists: DM DOKURO, Kolezar, Hex, etc.

### Preferred song genres

- Electronic and rave music is preferred: Calvin Harris, Prodigy, etc
- Popular songs from the 80s, 90s and 2000s are also welcome: Weezer, Smashing Pumpkins, etc

### Song genres to avoid

- Country
- Songs older than 1980

### Download Process

When BeatSaver API returns:

1. Use search endpoint with difficulty filters
2. Or scrape curated lists from BeastSaber
3. Requirement - songs must have at least "Easy", "Normal", and "Hard" difficulties available
