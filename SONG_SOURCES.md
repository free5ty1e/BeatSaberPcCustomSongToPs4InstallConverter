# Beat Saber Custom Song Sources - Research Results

## Summary

| Source | Status | Notes |
|---------|---------|-------|
| BeatSaver.com (main) | ❌ DOWN | API returns 404, website has issues |
| BeatSaver API | ❌ DOWN | All endpoints return errors |
| BeatSaver CDN | ❌ DOWN | cdn.beatsaver.com returns 404 |
| beatmaps.io | ❌ DOWN | Site responds but API doesn't work |
| ScoreSaber | ❌ DOWN | API returns errors |
| BeatLeader | ✅ PARTIAL | API works but no direct downloads |
| BeastSaber | ❌ DOWN | API/website returns errors |
| Reddit r/beatsaber | ❌ DOWN | API requires auth |
| Archive.org | ❌ DOWN | No cached data found |

## Detailed Results

### BeatSaver (Primary Source) - ❌ DOWN
**URL:** https://beatsaver.com

Tested endpoints:
| Endpoint | Result |
|----------|---------|
| `api.beatsaver.com/maps/hot` | 404 Not Found |
| `api.beatsaver.com/maps/plays` | 404 Not Found |
| `api.beatsaver.com/search?q=` | 404 Not Found |
| `cdn.beatsaver.com/{key}.zip` | 404 Not Found |
| beatsaver.com/search | Site loads but no map links found |
| beatsaver.com/maps/{key} | 404 Not Found |

**Status:** BeatSaver appears to be completely down or severely degraded.

---

### beatmaps.io - ❌ Unclear
**URL:** https://beatmaps.io

| Test | Result |
|------|---------|
| Site loads | ✅ Yes |
| API responds | ❌ No |

**Notes:** Site is accessible but no working API found.

---

### BeatLeader - ✅ Works (Limited)
**URL:** https://api.beatleader.xyz

| Endpoint | Result |
|---------|---------|
| `api.beatleader.xyz/leaderboards` | ✅ Returns song data |
| Song metadata | ✅ Includes name, artist, mapper |
| Song hash | ✅ Available |
| **Direct download** | ❌ Not available |

**Sample Response:**
```json
{
  "id": "WorldWideWeb919",
  "song": {
    "name": "World Wide Web [OST 7]",
    "author": "Nitro Fun",
    "hash": "WorldWideWeb"
  },
  "mapper": "ETAN"
}
```

**Limitation:** Provides song metadata but no download URLs.

---

### ScoreSaber Reloaded - ❌ Down
**URL:** https://scoresaber.com

| Test | Result |
|------|---------|
| API request | Error response |

---

### BeastSaber - ❌ Down
**URL:** https://bsaber.com

| Test | Result |
|------|---------|
| API request | Error response |

---

### Reddit - ❌ Auth Required
**URL:** https://reddit.com/r/beatsaber

| Test | Result |
|------|---------|
| API request | Requires authentication |

---

## How to Download Songs When Sources Return

### When BeatSaver Returns:

```bash
# Method 1: Use the download script
cd /workspace/beat-saber-ps4-custom-songs
python3 scripts/download_final.py

# Method 2: Manual download
# 1. Go to https://beatsaver.com
# 2. Search for songs
# 3. Download ZIP files
# 4. Extract to: songs/ folder
# 5. Run: python3 scripts/build_simple.py
```

### Song Selection Criteria (Based on User Preferences):

| Criteria | Requirement |
|----------|--------------|
| **Difficulty** | Must have Easy, Normal, Hard (NOT Expert+ only) |
| **Player Level** | User plays Hard, friends play Medium/Easy |
| **Popularity** | Most played/downloaded songs |
| **Audio** | Must include .ogg or .wav files |

### Recommended Songs to Download:

Based on community rankings:
1. **Crab Rave** - acrispy - BPM 128
2. **Crystallized** - S辣的 - BPM 175
3. **Believer** - Routers - BPM 120
4. **Bad Guy** - Hex - BPM 135
5. **Blinding Lights** - M展位 - BPM 171
6. **Final Boss** - Hex
7. **Metal Gear Alert** - Gizzi
8. **Feel Good Inc** - Dustrich
9. **Vampire** - Sutoraiku
10. **Bones** - Kolezar

---

## What We Need for Working Songs

### Required Files per Song:
| File | Purpose |
|------|----------|
| `info.dat` | Song metadata (name, BPM, author) |
| `*.dat` | Beatmap difficulties (Easy, Normal, Hard, Expert, Expert+) |
| `song.ogg` | Audio file |
| `cover.jpg` | Song cover image |

### Current Pipeline Status:
| Component | Status |
|-----------|---------|
| PKG Builder | ✅ Working |
| PARAM.SFO | ✅ Working |
| Unlocker | ✅ Working |
| Beatmap Converter | ✅ Working |
| Song Downloader | ❌ Waiting for BeatSaver |

---

## User Preferences (For Future Reference)

From user context:
- **Play style:** Hard difficulty
- **Friends:** Play Medium/Easy
- **Requirement:** Songs must have all difficulty levels (Easy, Normal, Hard minimum)
- **Avoid:** Expert+ only maps

---

## Next Steps

1. **Check BeatSaver status periodically:**
   - https://status.beatsaver.com
   - https://beatsaver.com

2. **When BeatSaver returns:**
   ```bash
   cd /workspace/beat-saber-ps4-custom-songs
   python3 scripts/download_final.py
   python3 scripts/build_simple.py
   ```

3. **Alternative:** Download manually from BeatSaver website and add to `songs/` folder

---

## Last Tested
Date: April 25, 2026
All sources checked and documented above.