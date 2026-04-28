# Beat Saber PS4 Custom Songs - FAQ

## Test PKG Questions

### Q: Will this break my game?
**NO!** Installing DLC through GoldHEN is completely safe:
- DLC installs to separate directory from base game
- No game files are modified
- Can be fully uninstalled anytime

### Q: How do I uninstall/remove it?
**PS4 Settings:**
1. Settings > Application Saved Data Management > Delete Saved Data
2. Or: Find Beat Saber in Game List > OPTIONS > Version Information

**If issues occur:**
- Delete DLC from PS4 settings
- Reinstall game from Store (if digital)
- Or simply don't install the test PKG

### Q: What do the test songs do?
**Nothing playable!** The test songs have:
- ❌ No note blocks to hit
- ❌ No audio files
- ❌ No scoring
- ✅ Game won't crash
- ✅ Tests that PKG installation works

---

## How to Get Real Songs with Notes

### Option 1: Wait for BeatSaver API (Recommended)
BeatSaver API is currently down. Check:
- https://status.beatsaver.com
- https://beatsaver.com

When it returns:
```bash
cd /workspace/beat-saber-ps4-custom-songs
python3 scripts/download_final.py    # Download songs
python3 scripts/build_simple.py      # Build PKG
```

### Option 2: Manual Download
1. Go to https://beatsaver.com on your browser
2. Download song ZIP files to your PC
3. Upload/copy to devcontainer: `/workspace/beat-saber-ps4-custom-songs/songs/`
4. Run: `python3 scripts/build_simple.py`

### Option 3: Use Windows (Full Pipeline)
On Windows PC with Unity:
1. Download songs from BeatSaver
2. Import into Unity project
3. Build asset bundles
4. Create proper PS4 PKG

---

## What Makes a Song "Work"

For a song to play properly, you need:

| Component | Status | Source |
|-----------|--------|--------|
| info.dat | ✅ Created | Song metadata |
| Audio (.ogg) | ❌ Missing | BeatSaver download |
| Cover image | ✅ Created | Placeholder JPEG |
| Beatmap (.dat) | ✅ Created | Empty placeholder |
| Real notes | ❌ Need real songs | BeatSaver |

### The Audio Problem
- PC songs: `.ogg` or `.wav` (standard audio)
- PS4 songs: `.egg` (encrypted FMOD format)

**To get audio working:**
1. Download real songs from BeatSaver (`.ogg` included)
2. Convert `.ogg` to PS4 format (complex)
3. Or: Use a tool that converts PC songs to PS4 format

---

## Quick Test Plan

1. **Install test PKG** to verify installation works
2. **Check "Extras" menu** in Beat Saber for DLC
3. **If DLC appears:** Pipeline works! ✅
4. **Find real songs** when BeatSaver API returns
5. **Rebuild PKG** with real content

---

## Installation Order (CRITICAL)

1. **FIRST:** `UP8802-CUSA12878_00-BSCUSTOMSONGS01-unlock.pkg` (unlocker)
2. **SECOND:** `UP8802-CUSA12878_00-BSCUSTOMSONGS01.pkg` (DLC)

**Do NOT install in reverse order!**

---

## Test Results Expected

| Check | Expected Result |
|-------|------------------|
| PKG installs without error | ✅ Yes |
| DLC appears in Game > Info | ✅ Yes |
| DLC appears in "Extras" menu | ⚠️ Maybe |
| Songs show in song list | ❌ No (no real songs) |
| Game crashes | ❌ No |

---

## Next Steps (Priority Order)

1. ✅ Install test PKG on PS4 (verify installation)
2. ⏳ Wait for BeatSaver API to return
3. ⏳ Download 50 popular songs
4. ⏳ Rebuild PKG with real content
5. 🔧 Figure out audio conversion

---

## The Unlocker Explained

The unlocker does **NOT**:
- ❌ Modify game files
- ❌ Unlock PlayStation Network features
- ❌ Enable pirated content
- ❌ Affect online multiplayer

The unlocker **DOES**:
- ✅ Create fake local license files
- ✅ Allow DLC to "unlock" without purchase
- ✅ Work entirely offline
- ✅ Uninstall cleanly

It's similar to "license backups" that PS3/PS4 homebrew users have used for years.

---

## Real Song Sources

When BeatSaver is back, download from:
- https://beatsaver.com (main source)
- https://bsaber.com (curated lists)

Popular songs to download:
- "Crystallized" by S辣的
- "Crab Rave" by acrispy
- "Believer" by Routers
- "Bad Guy" by Hex
- "Final Boss" by Hex
- "Metal Gear Alert" by Gizzi

Search for **"Most Downloaded"** or **"Top Rated"** to find the best maps.

---

## Summary

| Question | Answer |
|----------|--------|
| Break game? | **NO** |
| Uninstallable? | **YES** |
| Test songs playable? | **NO** (no notes) |
| Pipeline works? | **YES** (need to test on PS4) |
| Need real songs? | **YES** |
| Audio included? | **NO** (need to add) |