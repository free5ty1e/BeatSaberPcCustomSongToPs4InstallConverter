# PS4 Beat Saber Custom Songs - Status Report

## Current State (2026-05-01)

### Working
- ✅ Downloaded 94 songs from BeatSaver (Easy/Normal/Hard)
- ✅ Built PKG with orbis: 1.1GB (all songs included)
- ✅ PKG installed successfully on PS4 via GoldHEN

### Not Working
- ❌ Songs not visible in Beat Saber game

---

## Key Insight: Why Songs Don't Show

From DLC analysis (`dlc_internal_format.md`):

1. **Official DLC structure**: Each song PKG is ~1MB and contains:
   - Cover PNG (290KB)
   - PARAM.SFO metadata
   - Encrypted audio reference blocks

2. **Critical finding**: DLC packages do NOT contain audio directly. Audio lives in the main game `sharedassets*.assets` files. The DLC only provides:
   - Cover art
   - Metadata
   - Encrypted references that point to audio in the main game

3. **Our custom PKG**: Contains the song files but Beat Saber has no way to find/load them because:
   - No "BeatSaber-Plugin.prx" like RB4DX exists for Beat Saber
   - The game doesn't know to look in our custom folder
   - We need a plugin to hook file I/O and load custom song assets

---

## Required for Success

### Option A: Build a Beat Saber Plugin (complex)
- Create `BeatSaber-Plugin.prx` for GoldHEN
- Hook Unity `AssetBundle.LoadFromFile` 
- Hook `Resources.Load` for song loading
- Redirect file reads to custom songs folder
- This is what RB4DX does for Rock Band 4

### Option B: Inject into Main Game (complex)
- Extract main game PKG
- Modify `sharedassets*.assets` to add custom songs
- Repack and rebuild PKG
- Requires Unity 2018.x tools

### Option C: Find Existing Plugin (unknown)
- Check if someone has created a Beat Saber PS4 modding plugin
- Would need to install in `/user/data/GoldHEN/plugins/`

---

## PS4 FTP Analysis

**Known paths from previous session** (`ps4_topology.md`):

| Path | Contents |
|------|----------|
| `/user/app/CUSA12878/` | Game launcher (254MB) |
| `/user/patch/CUSA12878/` | Game data (4.9GB) |
| `/user/data/GoldHEN/plugins/` | Modding plugins |
| `/user/data/GoldHEN/RB4DX/` | RB4DX mod data |

**Where custom songs would go**: `/user/data/GoldHEN/BeatSaber/songs/`

---

## Next Steps

1. **Verify installation**: Check PS4 FTP for where our PKG installed files
2. **Research plugin**: Search for existing Beat Saber PS4 modding plugins
3. **Analyze main game**: If we can extract main game's `sharedassets`, understand audio format
4. **Consider alternative**: Quest modding (BMBF) is much simpler — does user have Quest?

---

## Files This Project Created

- `windows_build/CUSA12878-app/songs/` - 94 converted songs
- `windows_build/UP4882-CUSA12878_00-P1S5XXXXXXXXXXXX-A0000-V0100.pkg` - 1.1GB installable PKG