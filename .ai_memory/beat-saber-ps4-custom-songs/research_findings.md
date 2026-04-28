# Beat Saber PS4 Custom Songs - Research Findings

## Executive Summary
Converting PC custom songs to PS4 is theoretically possible but **no fully working automated pipeline exists**. The closest approach was explored by Backporter in 2021 using a beatmap data converter + UABE (Unity Asset Bundle Extractor) to inject into the game's `sharedassets0.assets` file, but this was a replacement method (replacing existing songs) rather than adding new ones — and the tool is unmaintained. The fundamental challenge is that PS4 Beat Saber lacks the modding hooks (like BMBF on Quest or SongCore on PC) that make custom songs trivially installable.

---

## 1. Communities, Sources & Tools

### Primary Custom Song Platforms
| Name | URL | Purpose |
|------|-----|---------|
| **BeatSaver** | https://beatsaver.com | Primary repository for all Beat Saber custom maps. Every song ever published is here. API available. |
| **BeastSaber** | https://bsaber.com | Community hub, curated songs, featured packs, "Map of the Week", player reviews. Pulls from BeatSaver. |
| **ScoreSaber** | https://scoresaber.com | Leaderboard system for custom songs. Indicates ranked/popular songs. |
| **BSSB (Beat Saber Server Browser)** | https://bssb.app | Play statistics, top 100 most-played custom levels, playlist downloads. |
| **BeatDrop** | https://github.com/StarGazer1258/BeatDrop | Desktop app for downloading/managing songs, mods, playlists. |
| **ModAssistant** | (desktop app) | One-click song/mod installer for PC/Quest Beat Saber. |

### PS4 Modding Communities
| Name | URL | Purpose |
|------|-----|---------|
| **PSXHAX** | https://www.psxhax.com | Primary PS4/PS5 scene forum. Hosts Beat Saber FPKG releases and discussion. |
| **Beat Saber Modding Group Discord** | `#ps4-help` channel | Official modding community help channels (though PS4 help is limited). |

---

## 2. Existing Tools & Projects

### Backporter/PS4-Beat-Saber-Converter (2021, unmaintained)
- **Repo**: https://github.com/Backporter/PS4-Beat-Saber-Converter
- **Purpose**: Converts PC beatmap data (JSON format) to PS4 binary `.dat` format
- **Status**: No longer maintained — last update 2021
- **Workflow** (from TUT.txt):
  1. Extract PC song's `info.dat` and difficulty `.json` files
  2. Use `PS4-Beat-Saber-Dat-Creator.exe` to convert beatmap data to PS4 binary format
  3. Use **UABE** (Unity Asset Bundle Extractor) to inject into the game's `sharedassets0.assets`
  4. Use **Unity 2018.1.6** to build audio into `.resource` format
  5. Repack and create PKG
- **Limitations**: This was designed for *replacing* existing songs, not adding new ones. Required deep Unity asset manipulation.

### UABE (Unity Asset Bundle Extractor)
- **Repo**: https://github.com/SeriousCache/UABE (original), https://github.com/nesrak1/UABEA (modern fork)
- **Purpose**: Edit `.assets` and AssetBundle files for Unity games
- **Key for Beat Saber PS4**: The PS4 game stores songs in `sharedassets0.assets` (among others). UABE can extract and replace AudioClip and BeatMapData assets.
- **Requirements**: Unity 2018.1.6f1 (matching Beat Saber's engine version, identified as `U2019.2.0f1` in the TUT.txt — need to verify)

### QuestSongManager
- **Repo**: https://github.com/exelix11/QuestSongManager
- **Purpose**: Song and playlist manager for Quest Beat Saber. Not directly applicable to PS4, but demonstrates the ecosystem of tools for other platforms.

### Tristan Hume's Beat Saber Patcher (2019)
- **Blog**: http://thume.ca/2019/07/26/writing-a-beat-saber-patcher/
- **Purpose**: Detailed writeup of how the author reverse-engineered Beat Saber's Unity asset format to create a custom song patcher for Android APK. The approach (reading Unity asset files, modifying, disabling signature checks, repacking) is directly applicable to understanding PS4 injection.

### emulamer/QuestomAssets
- **Repo**: https://github.com/emulamer/QuestomAssets
- **Purpose**: Core library for reading/writing Beat Saber APKs and asset files. Could provide reference for binary format understanding.

---

## 3. PS4-Specific Scene Activity

### FPKG Releases (PSXHAX)
- **Opoisso893** (aka backport893) is the primary scene member maintaining Beat Saber PS4 FPKG releases:
  - Beat Saber CUSA12878 v1.00 [5.05]
  - Beat Saber CUSA12878 v1.84 [9.00] backport
  - Beat Saber CUSA12878 DLC PACK v10 (194 songs), v11 (204 songs)
- **Latest**: v1.92 [9.00/11.00] as of Sep 2024
- These are already-dumped game packages with official DLC packs. They do NOT contain custom/community songs.

### Your PS4 Fileshare
Based on `context_beat_saber_fileshare.md`:
- Main game: `Beat.Saber_CUSA18278_[...]/` (appears to be a different CUSA ID from the scene releases — scene uses CUSA12878, fileshare shows CUSA18278)
- DLC packages: `Beat.Saber_CUSA18278_DCLPACK.v14_[246]_OPOISSO893` (194 songs in DLC pack v14)
- **CUSA18278** vs **CUSA12878**: These are different game IDs — CUSA18278 is likely the PSVR bundle edition. The scene's releases are CUSA12878.

---

## 4. Song Format Understanding

### PC/Quest Format (JSON-based)
- **info.dat** (or info.json in newer maps): Song metadata, points to audio, cover, difficulty files
- **audio**: `.ogg` or `.egg` (encrypted OGG)
- **cover**: `.jpg` or `.png` (256x256)
- **difficulty files**: JSON per difficulty (Easy.dat, Normal.dat, Hard.dat, Expert.dat, ExpertPlus.dat)
- **Version history**: v1 (info.json) → v2 (info.dat binary) → v3 → v4 (current JSON format)

### PS4 Format (Binary Unity Asset)
- Beat Saber PS4 stores songs as **Unity serialized binary assets** inside `.assets` files
- Audio is stored as **AudioClip** assets (Unity's native format, not OGG)
- Beatmap data is stored as **BeatMapData / BeatmapLevelSO** MonoBehaviour objects in binary
- The format is the **v2 binary format** (`_version = "2.0.0"` per MCJack123's conversion gist)
- Key fields in the binary format:
  - `_songName`, `_songSubName`, `_songAuthorName`, `_levelAuthorName`
  - `_beatsPerMinute`, `_songTimeOffset`, `_shuffle`, `_shufflePeriod`
  - `_songFilename` (internal audio reference)
  - `_coverImageFilename`
  - `_difficultyBeatmapSets[]` (each with `_beatmapCharacteristicName` and `_difficultyBeatmaps[]`)
  - Each difficulty: `_difficulty`, `_difficultyRank`, `_noteJumpMovementSpeed`, `_noteJumpStartBeatOffset`, `_beatmapFilename`

### Hex Fiend Template
A template for reverse-engineering the binary format exists as a Gist: https://gist.github.com/trishume/138ef8f6c66fabd2d76b9fdf8d5c4c67 (by Tristan Hume, author of the 2019 patcher blog post above)

---

## 5. Proposed Investigation Approach

### Avenues to Explore

#### Avenues Completed (above research):
1. ✅ Located communities (BeatSaver, BeastSaber, ScoreSaber, BSSB)
2. ✅ Found Backporter's PS4-Beat-Saber-Converter (2021, unmaintained)
3. ✅ Found detailed TUT.txt workflow (UABE + Unity 2018.1.6 + asset injection)
4. ✅ Found Tristan Hume's patcher writeup (2019, Quest-focused but applicable concepts)
5. ✅ Found Hex Fiend template for binary format

#### Still Needed:
1. **Obtain and analyze actual PS4 game assets** — Extract `sharedassets0.assets` and other `.assets` files from your PS4 fileshare packages to understand the exact binary format used
2. **Verify Unity version** — Need to confirm whether the PS4 version uses Unity 2018.x or 2019.2 (from TUT.txt hints)
3. **Test PC-to-PS4 conversion pipeline** — Take a known simple song, attempt the conversion using Backporter's tool, inject via UABE, repack as PKG
4. **Investigate adding new songs vs replacing** — The existing tools only replace existing songs. Investigating whether there's a way to extend the level pack or if new assets need their own entries
5. **Explore Rock Band 4 parallels** — Your existing Rock Band 4 mod workflow (ForgeTool, LibForge) converted DLC CON songs to FPKG. Is there a similar direct asset extraction → modification → FPKG repack flow possible?

### Key Unknowns
1. **Can new songs be added to the level pack, or only replacements?** The existing tools were designed for replacement. Adding new entries may require modifying the level pack's internal references.
2. **Audio format on PS4** — Is audio stored as OGG/Egg (like PC), or converted to Unity's AudioClip format? Audio will likely need re-encoding via Unity 2018.1.6 + UABE workflow.
3. **PKG signing** — After modifying game assets, the FPKG must be re-signed or created as a new FPKG. Your existing PkgToolBox may handle this.

---

## 6. Parallel to Rock Band 4 Workflow

You already have a working pipeline for Rock Band 4 custom songs on PS4:
1. Get custom songs (CON files or Magma-riff files)
2. Use LibForge / ForgeTool to convert to PS4-compatible format
3. Use Onyx Toolkit to package as FPKG
4. Install via PS4 FTP/file share

For Beat Saber PS4, the equivalent would be:
1. Get custom songs from BeatSaver (PC JSON format)
2. Convert beatmap data to PS4 binary format → **NEEDS TOOL (Backporter's or new)**
3. Convert audio to Unity AudioClip format → **NEEDS TOOL (UABE + Unity 2018.1.6 workflow)**
4. Inject into game assets → **NEEDS TOOL (UABE)**
5. Repack as FPKG → **EXISTING (PkgToolBox in workspace)**

**The gap is steps 2 and 3** — there is no modern tool that automates the PC JSON → PS4 binary conversion and audio conversion. This is where the primary development effort would need to go.

---

## 7. References

- Backporter/PS4-Beat-Saber-Converter: https://github.com/Backporter/PS4-Beat-Saber-Converter
- UABE: https://github.com/SeriousCache/UABE
- UABEA (modern fork): https://github.com/nesrak1/UABEA
- Tristan Hume's Beat Saber Patcher: http://thume.ca/2019/07/26/writing-a-beat-saber-patcher/
- QuestomAssets: https://github.com/emulamer/QuestomAssets
- Hex Fiend Beat Saber Template: https://gist.github.com/trishume/138ef8f6c66fabd2d76b9fdf8d5c4c67
- BSMG Wiki Map Format: https://bsmg.wiki/mapping/map-format.html
- BeatSaver (primary song repo): https://beatsaver.com
- PSXHAX Beat Saber FPKG thread: https://www.psxhax.com/threads/new-ps4-game-fpkgs-in-ps4scene-by-opoisso893-golemnight.17380/
- Info.dat v2 format conversion: https://gist.github.com/MCJack123/892b936ef0d18da43ab2764ba97402be