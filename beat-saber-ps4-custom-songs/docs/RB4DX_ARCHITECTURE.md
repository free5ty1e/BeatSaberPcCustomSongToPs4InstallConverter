# RB4DX Architecture Analysis

## Date: 2026-05-01

## Overview

RB4DX (Rock Band 4 Deluxe) is a working example of PS4 game modding via GoldHEN plugin + custom data files.

## RB4DX Components

### 1. GoldHEN Plugin (`RB4DX-Plugin.prx`)
- Size: 96,080 bytes
- Hooks game functions in eboot.bin
- Serves custom files from `/data/GoldHEN/RB4DX/ps4/`

### 2. Custom Data Files
Located in `_build/GoldHEN/RB4DX/ps4/`:
```
ps4/
├── char/musician/          # Character models
├── config/                 # Game config DTA files
│   ├── include/            # System configs
│   ├── rb_config.dta       # Main config
│   └── rb_venues.dta       # Venue settings
├── dx/                     # Deluxe modifications
│   ├── custom_sounds/      # FMOD audio banks
│   ├── custom_textures/    # UI/background textures
│   ├── funcs/              # Custom game functions
│   ├── overshell/          # Menu modifications
│   ├── track/              # Track themes
│   └── ui/                 # UI elements
├── fmod_banks/             # Audio banks
├── patched_songs/          # Modified song data
├── shared/                 # Shared assets
└── track/                  # Instrument tracks
```

### 3. File Format Conversion

Build process (`_build.bat`):
1. **DTA → DTX**: Game config text → binary format
   - Tool: `dtacheck` + `dtxtool`
   - Extension: `.dta` → `.dta_dta_ps4`

2. **PNG → PS4 Texture**: 
   - Tool: `forgetool`
   - Extension: `.png` → `.png_ps4`

3. **Output**: `_build/GoldHEN/RB4DX/ps4/`

## How RB4DX Plugin Works

### Plugin Source Analysis (from RB4DX-Plugin repository)

**Main hooks in `main.c`:**
```c
// File redirection hook - intercepts file open requests
NewFile = (void*)(base_address + 0x00376d40);

// Game restart hook - for speed/mod features
GameRestart = (void*)(base_address + 0x00a46710);

// Title/Artist hooks - for song display mods
GetTitle = (void*)(base_address + 0x00f28d20);
GetArtist = (void*)(base_address + 0x00f28d30);

// Sorting hooks - for song list organization
SortByArtist = (void*)(base_address + 0x00ca5e30);
SortByTitle = (void*)(base_address + 0x00ca5d60);

// Color hooks - for gem customization
UpdateColors = (void*)(base_address + 0x00f94a70);
DoSetColor = (void*)(base_address + 0x001a7320);
```

### File Redirection Logic
```c
void NewFile_hook(const char* path, FileMode mode) {
    // Check /data/GoldHEN/RB4DX/ first
    // If found, serve from there instead of game files
    // Otherwise, pass to original function
}
```

### Plugin Structure
- Defined exports: `g_pluginName`, `g_pluginDesc`, `g_pluginAuth`, `g_pluginVersion`
- `module_start()`: Initialize hooks, check game version
- `module_stop()`: Clean up hooks

## Beat Saber PS4 Comparison

### Differences from Rock Band 4

| Aspect | Rock Band 4 | Beat Saber |
|--------|-------------|------------|
| Engine | Proprietary | Unity 2022 |
| Audio | FMOD | Unity Audio |
| Asset Format | DTA + custom | AssetBundle |
| Song Format | .mid/.dta | .ogg + JSON |
| Hook Point | NewFile() | AssetBundle.LoadFromFile() |

### Beat Saber Known Strings (from eboot.bin)
```
UnityEngine.AssetBundle::LoadFromFile_Internal
UnityEngine.AssetBundle::LoadAsset_Internal
UnityEngine.AssetBundle::Unload
```

## Required for Beat Saber Deluxe

### 1. Plugin Development
- Need to find Beat Saber function addresses
- Hook `AssetBundle.LoadFromFile`
- Hook `Resources.Load`
- Implement file redirection

### 2. Data Format Conversion
- Convert PC song format → Unity AssetBundle
- Create level prefab structure
- Convert cover images

### 3. File Structure
```
/data/GoldHEN/BeatSaber/
├── ps4/
│   ├── songs/              # Custom songs
│   ├── config/            # Game configs
│   └── textures/          # Custom textures
└── BeatSaberDX-Plugin.prx
```

## Next Steps

1. Analyze Beat Saber eboot.bin for Unity hooks
2. Find AssetBundle loading functions
3. Create minimal plugin skeleton
4. Build test PKG with empty plugin
5. Verify plugin loads on PS4

## References

- RB4DX Plugin: https://github.com/LlysiX/RB4DX-Plugin
- RB4DX Main: https://github.com/hmxmilohax/Rock-Band-4-Deluxe
- GoldHEN Plugin SDK: https://github.com/GoldHEN/GoldHEN_Plugin_SDK