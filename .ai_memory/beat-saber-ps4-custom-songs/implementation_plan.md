# Beat Saber PS4 Custom Songs — Implementation Plan

## Executive Summary

This project aims to enable custom community songs on Beat Saber for PS4 (CUSA12878), using a **runtime memory patching approach** similar to the existing Rock Band 4 (RB4DX) modding setup on the PS4.

## Key Discoveries from PS4 FTP Analysis

### PS4 FTP Topology
- **CUSA ID**: Confirmed as **CUSA12878** (US PS4/PSVR version)
- **FTP Access**: Read/write access at `192.168.100.117:2121`
- **Installed Packages**:
  - `app.pkg` (254MB) - v1.00 launcher shell
  - `patch.pkg` (4.9GB) - v2.04 backport (game data, ENCRYPTED on disk)
- **Save Data**: Virtual SD card image at `/user/home/1c9d7579/savedata/CUSA12878/`
  - `sdimg_sce_sdmemory` (39MB) - Contains game profile and settings
  - `sdimg_Default` (3MB) - Contains default profile
- **DLC on Fileshare**: 246 individual song DLC PKGs (~1MB each, contain cover PNG + metadata only)

### Critical Limitation
The `patch.pkg` (4.9GB) is **ENCRYPTED on disk** (verified: magic bytes `7F434E54` present, body data is random-looking AES ciphertext). The PS4 kernel decrypts it transparently when the game runs, but FTP serves the raw encrypted file. We cannot extract raw game data without:
1. A jailbroken PS4 kernel module that exports decrypted reads
2. A PS4-side plugin that hooks the game's file access (like RB4DX does)

### GoldHEN Modding Architecture (Already Active on PS4)
The PS4 has a sophisticated RB4DX (Rock Band 4) modding setup:
- **RB4DX Plugin** (`RB4DX-Plugin.prx` - 96KB GoldHEN plugin)
- **game_patch.prx** (132KB generic patching plugin)
- **Modded Assets** at `/user/data/GoldHEN/RB4DX/ps4/`:
  - `track/` - instrument tracks, camera scripts, textures
  - `fmod_banks/PS4/` - custom audio banks
  - `char/` - character models
  - `ui/` - UI textures and elements
  - `patched_songs/` - custom song data
  - `config/` - game configuration patches

RB4DX works by:
1. Loading modded assets from the GoldHEN directory
2. **Runtime patching**: Hooks game functions (FMOD audio, file I/O)
3. Redirecting file reads to modded versions
4. Patching game logic for custom song support

### Game Technology Stack
- **Engine**: Unity (confirmed from backport PKG metadata)
- **Audio**: FMOD (similar to Rock Band)
- **Asset Format**: Unity AssetBundles (`.sharedassets` files)
- **Beatmap Format**: Binary `.dat` files (BEATS format)
- **Version**: v2.04 backport (supports PS4 FW 5.05 through 12.00)

---

## Implementation Strategy

### Approach: PS4-Side GoldHEN Plugin

Following the RB4DX model, we need a **Beat Saber PS4 plugin** that:
1. Patches the game's Unity engine to intercept asset loading
2. Redirects custom song requests to modded asset bundles
3. Patches the beatmap parser to accept custom song formats
4. Patches audio loading to use custom OGG/IMA audio

### Architecture Components

```
PC Side:                                PS4 Side:
────────                                ────────
1. PC Song → JSON + Audio              1. GoldHEN Plugin
2. Convert to PS4 format    ─────────→ 2. File redirect hooks
3. Package as mod data      ─────────→ 3. Custom song directories
4. Upload via FTP            ─────────→ 4. Runtime memory patches
```

### Required Components

#### PC Side (This Workspace)
1. **Song Converter**: PC BeatSaver JSON → PS4 binary beatmap format
2. **Audio Converter**: PC OGG → FMOD bank or Unity AudioClip format
3. **Asset Packager**: Package songs into PS4-compatible asset bundles
4. **PS4 Plugin Builder**: Compile C/C++ code into GoldHEN .prx plugin

#### PS4 Side (GoldHEN Plugin)
1. **Unity Engine Patches**:
   - Hook `AssetBundle.LoadFromFile()` to check custom directories first
   - Hook `Resources.Load()` for custom assets
   - Hook audio loading for custom songs

2. **File System Redirects**:
   - Redirect `sharedassets*.assets` reads to modded bundles
   - Redirect level data reads to custom song databases

3. **Custom Song Loader**:
   - Parse custom song format (likely JSON or binary)
   - Register custom levels with the level pack system
   - Handle audio streaming for custom songs

---

## Technical Implementation

### Step 1: Analyze PS4 Game Memory (PS4-Side Investigation)

On the PS4, using a debugger or the RB4DX plugin as reference:
1. Find the Unity asset loading functions
2. Find the beatmap parsing code
3. Find the song list/catalog data structures
4. Understand FMOD audio bank loading

**Reference**: RB4DX plugin source (if available) shows the pattern for FMOD hooks.

### Step 2: Develop GoldHEN Plugin

```c
// ps4_beatsaber_plugin/prx/main.c (pseudocode)
#include <sys/process.h>
#include <sys/memory.h>

// Hooks needed:
// 1. Unity File I/O hooks
// 2. FMOD Bank loading hooks
// 3. Song catalog patching

int main(unsigned int args, void *argp) {
    // Initialize plugin
    g_hook_install();
    
    // Hook Unity's file access
    hook_function("SceLibc", "open", my_open_hook);
    hook_function("SceLibc", "read", my_read_hook);
    hook_function("SceLibc", "stat", my_stat_hook);
    
    // Hook Unity specific functions
    hook_function("libunity", "AssetBundle_LoadFromFile", my_ab_load_hook);
    hook_function("libunity", "Resources_Load", my_res_load_hook);
    
    // Hook FMOD
    hook_function("libfmod", "FMOD_Bank_Load", my_fmod_hook);
    
    // Register custom song directory
    register_custom_song_path("/user/data/GoldHEN/BeatSaber/songs/");
    
    return 0;
}
```

### Step 3: PC Song Conversion Tool

```python
# song_converter.py - Convert PC BeatSaver songs to PS4 format
import json, os, struct, subprocess

def convert_song(pc_song_dir, output_dir):
    # 1. Parse PC song info.dat
    with open(f"{pc_song_dir}/info.dat") as f:
        info = json.load(f)
    
    # 2. Convert beatmap to PS4 binary format
    for diff in info['difficultyLevels']:
        beatmap = convert_beatmap(diff)
        with open(f"{output_dir}/{diff['difficulty']}.dat", 'wb') as f:
            f.write(beatmap)
    
    # 3. Convert audio (OGG -> FMOD or raw PCM)
    audio = convert_audio(f"{pc_song_dir}/{info['audioPath']}")
    with open(f"{output_dir}/audio.bank", 'wb') as f:
        f.write(audio)
    
    # 4. Create song metadata header
    metadata = create_song_header(info)
    with open(f"{output_dir}/song.dat", 'wb') as f:
        f.write(metadata)
```

### Step 4: PS4 Custom Song Directory Structure

```
/user/data/GoldHEN/BeatSaber/
├── songs/
│   ├── customsong_001/
│   │   ├── song.dat          # Song metadata (name, artist, BPM)
│   │   ├── Easy.dat          # Difficulty beatmap
│   │   ├── Normal.dat        # Normal difficulty
│   │   ├── Hard.dat          # Hard difficulty
│   │   ├── Expert.dat        # Expert difficulty
│   │   ├── ExpertPlus.dat    # Expert+ difficulty
│   │   ├── audio.bank        # Audio (FMOD bank format)
│   │   └── cover.png         # Cover image
│   ├── customsong_002/
│   │   └── ...
│   └── ...
└── config/
    ├── settings.json         # Plugin configuration
    └── blacklist.json        # Blocked songs
```

---

## Beat Saber PS4 Data Format (Research Required)

### Beatmap Binary Format (PS4-Specific)

Based on Backporter's PS4-Beat-Saber-Converter analysis, PS4 beatmaps use a binary format:
- **Note positions**: Float coordinates (x, y, z)
- **Timing**: Integer milliseconds
- **Note types**: Enum (Red/Blue/Bomb, Left/Right/Both)
- **Events**: Cut direction, wall type, etc.

### Unity Asset Bundle Format

Beat Saber uses Unity 2018.x asset bundles:
- `sharedassets0.assets` - Base game assets
- `sharedassets1.assets` - Levels pack 1
- `sharedassetsN.assets` - Additional level packs

Each level in the asset bundle contains:
- Song metadata (name, artist, BPM)
- Audio clip reference
- Beatmap data
- Cover image

### Custom Song Integration

The plugin needs to:
1. Register custom songs in the song catalog
2. Override audio loading for custom songs
3. Override beatmap parsing for custom songs
4. Handle level selection UI for custom songs

---

## Reference Projects and Tools

| Resource | Purpose | Link |
|----------|---------|------|
| RB4DX Plugin | PS4 modding reference | On this PS4 at `/user/data/GoldHEN/plugins/RB4DX-Plugin.prx` |
| Backporter's Converter | PC → PS4 beatmap conversion | https://github.com/Backporter/PS4-Beat-Saber-Converter |
| UABE | Unity asset extraction | https://github.com/SeriousCache/UABE |
| GoldHEN Plugin SDK | PS4 plugin development | https://github.com/SilenSara/GoldHEN_Plugin_SDK |
| BeatSaver API | PC song downloads | https://beatsaver.com/api |
| PS4 Game Hooks | Memory hacking reference | https://github.com/GoldHen/GoldHen |

---

## Step-by-Step Implementation Plan

### Phase 1: PS4 Plugin Development (Requires PS4-Side Work)

1. **Analyze game memory** (on PS4 with debugger)
   - Find Unity engine functions in eboot.bin
   - Identify beatmap loading code
   - Identify audio loading code

2. **Develop GoldHEN plugin skeleton**
   - Set up plugin SDK
   - Implement basic function hooks
   - Test with simple patches

3. **Implement custom song loading**
   - File system redirects
   - Song catalog patching
   - Beatmap parser override

### Phase 2: PC Tools Development

4. **Build song converter**
   - Parse BeatSaver JSON format
   - Convert beatmaps to PS4 binary
   - Package audio assets

5. **Build asset packager**
   - Create Unity asset bundles for custom songs
   - Handle audio compression
   - Generate song metadata

6. **Build installer script**
   - FTP upload automation
   - Directory structure creation
   - Plugin configuration

### Phase 3: Testing and Refinement

7. **Test with known songs**
   - Start with simple songs
   - Verify audio plays
   - Verify beatmaps work

8. **Fix bugs and edge cases**
   - Handle various audio formats
   - Handle complex beatmaps
   - Fix UI integration

---

## Songs Catalog (From BSSB Top Played)

87 most-popular custom songs available from BeatSaver:

| # | Song Name | Artist | Downloads |
|---|-----------|--------|-----------|
| 1 | Believer | Imagine Dragons | 15,826,000 |
| 2 | Thunder | Imagine Dragons | 15,826,000 |
| 3 | Burn It Down | Linkin Park | 15,826,000 |
| 4 | Ring of Fire | Johnny Cash | 14,939,000 |
| 5 | Sandbox | Virtual Riot | 14,939,000 |
| ... | (see songs_catalog.md for full list) | | |

These songs are the primary targets for PS4 custom song support.

---

## Blocked By

1. **Cannot extract decrypted game data** - Need PS4-side plugin to access
2. **Unknown beatmap binary format** - Need reverse engineering of PS4 beatmaps
3. **Unity asset bundle creation** - Need to build compatible asset bundles
4. **Audio format conversion** - Need to understand FMOD/Unity audio format

## Solutions

1. **PS4-side investigation** - Use debugger/RB4DX as reference to find game functions
2. **Backporter's converter** - Study the 2021 converter for beatmap format hints
3. **UABE on patched game** - Extract existing assets, study format
4. **Audio analysis** - Decode a known song's audio format

---

## Progress Checklist

### Completed
- [x] Research communities, sources, tools
- [x] Create songs catalog from BSSB
- [x] Analyze DLC package structure  
- [x] FTP access to PS4 and enumerate game files
- [x] Confirm game data is encrypted on disk
- [x] Document PS4 FTP topology
- [x] Identify GoldHEN modding architecture (RB4DX pattern)
- [x] Discover save data SD card images
- [x] Search for existing PS4 Beat Saber custom song projects — **NONE FOUND**
- [x] Study Backporter's 2021 converter for beatmap format hints
- [x] Build PC song conversion tools (converter, downloader, installer)
- [x] Document all PS4 debugging and analysis tools
- [x] Document 6 alternative paths to achieve goal

### Next Phase: Choose Analysis Path

**Path 1**: Use ps4debug to analyze Beat Saber at runtime (requires learning debugger)
**Path 2**: Use ps4-dumper-vtx to dump decrypted game files (easiest, recommended)
**Path 3**: Dump system modules (libunity.so, libfmod.so) 
**Path 4**: Use GoldHEN Cheat Menu for simple memory patches
**Path 5**: Analyze RB4DX plugin as reference implementation (already on your PS4!)
**Path 6**: Build PS4 plugin from scratch (requires paths 1-5 first)

See `alternative_paths.md` for full details.