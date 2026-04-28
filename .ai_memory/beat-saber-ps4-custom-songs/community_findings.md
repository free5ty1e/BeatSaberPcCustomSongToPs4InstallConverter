# Beat Saber PS4 — Community & Tools Summary

## Web Research Findings

### Existing PS4 Custom Song Projects

| Project | Status | Description |
|---------|--------|-------------|
| **Backporter PS4-Beat-Saber-Converter** | Abandoned (2021) | Converts PC beatmap JSON to PS4 binary `.dat`. No longer maintained. |
| **ORBISPatches CUSA12878** | No custom songs | Only official patches and DLC packs listed |
| **PSXHAX PS4 Beat Saber** | Inactive | Thread from 2021-2022 discussing custom song potential |
| **GoldHEN Patch Repository** | Active | Contains memory patches for many games — NO Beat Saber patches exist |

### Key Finding: **No active PS4 Beat Saber custom song community exists.**

Unlike Rock Band 4 (RB4DX plugin), Beat Saber PS4 has:
- No GoldHEN plugin
- No memory patches
- No game patches on ORBISPatches
- No recent PSXHAX/PS4Scene activity

The only path forward is **creating the plugin from scratch**.

---

## Beat Saber Beatmap Format Documentation

### PC Format (v2/v3 JSON — BeatSaver Standard)

```
song_folder/
├── info.dat              # Song metadata (JSON)
├── Easy.dat              # Difficulty beatmaps (JSON)
├── Normal.dat
├── Hard.dat
├── Expert.dat
├── ExpertPlus.dat
├── song.ogg              # Audio
└── cover.png             # Cover image
```

### info.dat Structure (v2)
```json
{
  "_version": "2.0.0",
  "_songName": "Song Name",
  "_songSubName": "ft. Artist",
  "_songAuthorName": "Song Artist",
  "_levelAuthorName": "Mapper Name",
  "_beatsPerMinute": 120.0,
  "_previewStartTime": 12.0,
  "_previewDuration": 10.0,
  "_songTimeOffset": 0,
  "_shuffle": 0,
  "_shufflePeriod": 0.5,
  "_environmentName": "DefaultEnvironment",
  "_songFilename": "song.ogg",
  "_coverImageFilename": "cover.png",
  "_difficultyBeatmapSets": [{
    "_beatmapCharacteristicName": "Standard",
    "_difficultyBeatmaps": [{
      "_difficulty": "Expert",
      "_difficultyRank": 4,
      "_beatmapFilename": "Expert.dat",
      "_noteJumpMovementSpeed": 10,
      "_noteJumpStartBeatOffset": 0
    }]
  }]
}
```

### Difficulty .dat Structure (v3)
```json
{
  "_version": "2.0.0",
  "_notes": [
    {
      "_time": 8.0,
      "_lineIndex": 1,
      "_lineLayer": 0,
      "_type": 0,
      "_cutDirection": 1
    }
  ],
  "_obstacles": [
    {
      "_time": 16.0,
      "_lineIndex": 0,
      "_type": 0,
      "_duration": 1.0,
      "_width": 1
    }
  ],
  "_events": [
    {
      "_time": 0.0,
      "_type": 0,
      "_value": 1
    }
  ]
}
```

### PS4 Binary Format

Based on Backporter's converter, PS4 uses a binary format:
- `Info.dat` — Binary song metadata
- `*.dat` — Binary difficulty data

**Key differences from PC format:**
- Binary encoding instead of JSON
- Different note encoding (4 bytes per note instead of JSON)
- Compact obstacle and event arrays
- Fixed-size header structures

**Note data encoding (PS4):**
```
[4 bytes] time (float)
[1 byte]  line index (0-3)
[1 byte]  line layer (0-2)
[1 byte]  note type (0=Red, 1=Blue, 3=Bomb)
[1 byte]  color
[1 byte]  cut direction
[4 bytes] angle offset (float)
[1 byte]  tunnel/extra
```

---

## PC Custom Song Format References

| Resource | Link | Description |
|----------|------|-------------|
| BeatSaver API | https://api.beatsaver.com | Download songs |
| BeatSaberSongLoader | https://github.com/Kylemc1413/BeatSaberSongLoader | PC mod loader source |
| SongCore | https://github.com/Kylemc1413/SongCore | PC song loading library |
| Beat Saber Level Format | https://gist.github.com/MCJack123/892b936ef0d18da43ab2764ba97402be | v1→v2 format conversion |
| BeatSaber-JSMap | https://github.com/KivalEvan/BeatSaber-JSMap | Full beatmap schema docs |
| QuestSaberPatch | https://github.com/trishume/QuestSaberPatch | Quest patching approach |
| Backporter Converter | https://github.com/Backporter/PS4-Beat-Saber-Converter | Original PS4 converter |

---

## GoldHEN Plugin Development Resources

| Resource | Link | Description |
|----------|------|-------------|
| GoldHEN Plugins Repo | https://github.com/GoldHEN/GoldHEN_Plugins_Repository | Official plugin SDK |
| RB4DX Plugin | On your PS4 at `/user/data/GoldHEN/plugins/RB4DX-Plugin.prx` | **Reference implementation** |
| Game Patch | On your PS4 at `/user/data/GoldHEN/plugins/game_patch.prx` | Memory patching framework |
| AFR Plugin | On your PS4 at `/user/data/GoldHEN/plugins/afr.prx` | File redirection |
| GoldHEN Patch Repository | https://github.com/GoldHEN/GoldHEN_Patch_Repository | Community patches |
| PS4 Plugin SDK | https://github.com/SilenSara/GoldHEN_Plugin_SDK | Plugin development guide |

### RB4DX Plugin Architecture (Reference)

The working RB4DX plugin for Rock Band 4 works by:

1. **File System Hooks** — Hooks `open()`, `read()`, `stat()` in libc
2. **FMOD Hooks** — Intercepts FMOD bank loading
3. **Runtime Patching** — Modifies game functions in memory
4. **Asset Redirects** — Loads modded assets from `/user/data/GoldHEN/RB4DX/ps4/`

### Beat Saber Equivalent Hooks Needed

```
1. libunity.so - Unity engine hooks
   - AssetBundle_LoadFromFile
   - Resources_Load
   - SceneManager_LoadScene

2. Audio hooks
   - FMOD bank loading
   - AudioClip streaming

3. Beatmap parsing hooks
   - Level data loading
   - Difficulty parsing
```

---

## PS4 FTP Topology (Your Console)

See `ps4_topology.md` for full documentation.

**Key paths:**
- Game: `/user/app/CUSA12878/` + `/user/patch/CUSA12878/`
- Modding: `/user/data/GoldHEN/BeatSaber/songs/` (needs creation)
- Save data: `/user/home/1c9d7579/savedata/CUSA12878/`
- Plugins: `/user/data/GoldHEN/plugins/`

---

## Downloaded Resources

### On This Machine

| Path | Description |
|------|-------------|
| `/workspace/investigation/beat_saber_ps4/` | Downloaded PKG files and DLC |
| `/workspace/ps4_dump/` | PS4 FTP dump (patch metadata, save data) |
| `/workspace/ps4_pkg_tool/` | PKG extraction tool |
| `/workspace/beat_saber_ps4_tools/` | PC conversion tools (NEW) |
| `/workspace/.ai_memory/beat-saber-ps4-custom-songs/` | Project documentation |

### On Your PS4 (via FTP)

- `app.pkg` (254MB) — v1.00 launcher shell
- `patch.pkg` (4.9GB) — v2.04 backport (ENCRYPTED)
- `sdimg_sce_sdmemory` (39MB) — Game save/profile
- RB4DX modding setup at `/user/data/GoldHEN/RB4DX/`
- GoldHEN plugins at `/user/data/GoldHEN/plugins/`

---

## Implementation Checklist

### PC Tools (DONE)
- [x] Song converter (beatmap format conversion)
- [x] BeatSaver downloader (API integration)
- [x] PS4 installer (FTP upload)
- [x] README documentation

### PS4 Investigation (DONE)
- [x] FTP access confirmed
- [x] PS4 topology mapped
- [x] Encryption status confirmed
- [x] RB4DX plugin identified as reference

### PS4 Plugin Development (BLOCKED - Needs PS4-side work)
- [ ] Analyze game memory for Unity/FMOD hooks
- [ ] Create GoldHEN plugin skeleton
- [ ] Implement file system redirects
- [ ] Implement beatmap parser hooks
- [ ] Implement audio loading hooks
- [ ] Test with sample songs

### Testing Pipeline (BLOCKED)
- [ ] Create test song package
- [ ] Upload to PS4
- [ ] Test with GoldHEN plugin
- [ ] Verify audio plays
- [ ] Verify beatmaps work
- [ ] Full integration test