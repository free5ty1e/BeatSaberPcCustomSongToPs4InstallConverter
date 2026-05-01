# Beat Saber PS4 - Comprehensive Analysis & Plan

## Current Situation

### What We've Accomplished
- Downloaded 94 custom songs from BeatSaver (Easy/Normal/Hard difficulties)
- Converted songs to PS4 format with cover art
- Built valid PKG using orbis-pub-gen: 1.1GB
- PKG installed successfully on PS4 via GoldHEN Package Installer

### What's Not Working
- Songs don't appear in Beat Saber game
- No feedback/error message - they just don't show up

---

## Root Cause Analysis

### How Rock Band 4 (RB4DX) Works

The RB4DX plugin works because:

1. **File redirection hook** (`NewFile` at address `0x00376d40`):
   - Intercepts file open requests from the game
   - Checks `/data/GoldHEN/RB4DX/` for the file first
   - If found, serves from there instead of game files
   - This allows custom songs to be loaded

2. **Hardcoded game addresses**: The plugin uses specific memory addresses for Rock Band 4 version 2.21. These addresses were reverse-engineered by the RB4DX team.

3. **Game-specific hooks**: Multiple hooks for sorting, metadata, colors, etc.

### Why Beat Saber Is Different

**Beat Saber has NO such plugin** because:

1. **No one has reverse-engineered Beat Saber PS4's memory addresses**
2. **Different game structure**: Beat Saber uses Unity engine with different function names/addresses
3. **Unity asset system**: Beat Saber loads songs via `AssetBundle.LoadFromFile` and `Resources.Load`, not file system hooks
4. **DRM complexity**: Game data is encrypted, making reverse engineering harder

---

## Paths Forward

### Option 1: Create a Beat Saber Plugin (Complex)

**Requirements:**
- Reverse engineer Beat Saber PS4's eboot.bin (find Unity/engine hooks)
- Identify song loading functions
- Create plugin that intercepts file/asset loading
- Redirect to custom song folder

**Timeline**: Weeks to months of work
**Difficulty**: Very high (requires PS4 devkit or extensive reverse engineering)

### Option 2: Extract & Modify Main Game (Very Complex)

**Requirements:**
- Extract main game PKG (requires decryption on PS4)
- Use Unity tools to modify `sharedassets`
- Inject custom song assets
- Rebuild and repack game PKG

**Timeline**: Days to weeks
**Difficulty**: High (Unity asset manipulation)

### Option 3: Request Existing Plugin (If Available)

Search PS4 modding communities for existing Beat Saber plugin. No known plugin exists as of 2026.

### Option 4: Quest Modding (Easiest)

Beat Saber Quest has BMBF modding - trivial custom song installation. If user has a Quest, this is the easiest path.

---

## What We Actually Need for Beat Saber

The game loads songs via Unity's asset system:
```
1. Game scans song list from internal database
2. Loads song metadata from AssetBundle
3. Loads audio from AudioClip assets
4. Loads beatmaps from serialized data
```

For custom songs to work, we need:
1. **Plugin hook** on Unity asset loading functions
2. **Custom song scanner** that reads our song folder
3. **Asset converter** that converts PC format to Unity AssetBundle
4. **Song registry** that adds our songs to Beat Saber's song list

---

## Recommended Next Steps

1. **Verify PKG installation**: After FTP is working, check where files were installed
2. **Research Beat Saber Unity hooks**: Look for any existing research on Beat Saber PS4 memory structure
3. **Consider Quest**: If user has a Quest, custom songs work immediately
4. **Community request**: Post on PSXHAX asking if anyone is working on Beat Saber PS4 plugin

---

## Technical Notes

### RB4DX Plugin Architecture (Reference)
- Uses GoldHEN Plugin SDK
- Hooks libc file functions
- Serves files from `/data/GoldHEN/RB4DX/`
- Memory addresses are version-specific

### Beat Saber Needs
- Hook `AssetBundle.LoadFromFile`
- Hook `Resources.Load`
- Convert songs to Unity AssetBundle format
- Add to song list (likely needs memory hook)

### Required Tools
- OpenOrbis PS4 Toolchain
- GoldHEN Plugin SDK
- Unity 2018.x (for asset editing)
- PS4 with jailbreak for testing

---

## If User Wants to Continue on PS4

The most realistic path forward:
1. Find Beat Saber PS4 function addresses (requires PS4-side debugging)
2. Create minimal plugin that hooks file I/O
3. Build custom song converter to match game format
4. Test iteratively

This is essentially creating new modding infrastructure that doesn't exist yet.

---

*Last updated: 2026-05-01*
*Status: Blocked - need PS4 FTP access or new approach*