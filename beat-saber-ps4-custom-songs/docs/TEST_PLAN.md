# Test Plan: Audio Replacement Approaches

## Date: 2026-05-02

## Objective
Replace audio in an existing Beat Saber level with custom audio.

---

## Approach 1: UABEA Import Test ✅ Tested
**Status:** FAILED - UABEA cannot directly import audio

### What We Tried
- Exported .resource file (FSB5 format)
- Tried importing back via "Import Dump" (expects JSON)
- Tried importing raw .dat file

### Result
- Import asks "Is this asset serialized?" - selected YES
- File appears unchanged
- No way to inject new audio directly

### Conclusion
UABEA cannot import external audio into FSB5 resources.

---

## Approach 2: Unity 2022.3 Project ✅ Created
**Status:** READY TO TEST

### What We Created
- `unity_project/` - Complete Unity 2022.3 project
- `CustomBeatmapLevel.cs` - Level component
- `BeatSaberMenu.cs` - Editor menu tools
- `AudioImporter.cs` - Audio import settings

### Instructions

#### Step 1: Open Unity Project
1. Open Unity Hub
2. Click **Open** → Navigate to `beat-saber-ps4-custom-songs/unity_project/`
3. Wait for Unity to load

#### Step 2: Configure PS4 Build Support
1. If prompted, install **PS4 Build Support** module
2. Unity → **Edit** → **Preferences** → **External Tools**
3. Verify PS4 SDK is available

#### Step 3: Add Test Audio
1. Copy any OGG file to `unity_project/Assets/Audio/test_song.ogg`
2. Unity will auto-import

#### Step 4: Create Level
1. Unity menu: **BeatSaber** → **Create Custom Level**
2. Select the new GameObject in Hierarchy
3. In Inspector:
   - Set **Level ID**: `test_song`
   - Set **Song Name**: `Test Song`
   - Set **Artist**: `Test Artist`
   - Set **BPM**: `120`
   - Drag `test_song.ogg` to **Audio Clip**

#### Step 5: Build AssetBundle
1. Unity menu: **BeatSaber** → **Build for PS4**
2. Check `output/CustomLevels/` for the bundle

#### Step 6: Copy to Project
1. Copy the built file to `CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/test_song`

#### Step 7: Build PKG
1. Use PkgToolBox to create PKG
2. Install on PS4

---

## Approach 3: Binary FSB5 Replacement ⚠️ EXPERIMENTAL
**Status:** THEORETICAL

### Concept
Since we understand FSB5 format, we could:
1. Convert new audio to FSB5 format
2. Replace audio data in .resource file
3. Keep original headers

### Requirements
- FSB5 encoder or FMOD Studio
- Match original audio size (or adjust headers)

### Not Recommended
Too complex - Unity approach is better.

---

## Approach 4: AssetRipper Workflow ⚠️ Alternative
**Status:** DEPENDS ON ASSETRIPPER INSTALL

### Concept
1. Use AssetRipper to extract game assets
2. Modify in Unity
3. Re-export as AssetBundle

### Issues
- AssetRipper may not work well with PS4-specific formats
- Re-export may not be compatible

---

## Recommended Test Sequence

### Test 1: Unity Basic Test (Do First!)
1. Open `unity_project` in Unity 2022.3
2. Create test level with any audio
3. Build AssetBundle for PS4
4. Verify with UABEA that structure matches

**Expected Outcome:** Confirms Unity can create compatible bundles

### Test 2: Simple Level Replacement
1. Take `beatsaber` level
2. Use Unity to create NEW level with different audio
3. Name it `beatsaber2`
4. Add to PKG alongside original
5. Install and check if game loads both

**Expected Outcome:** Confirms game auto-loads new levels

### Test 3: Audio-Only Replacement
1. Copy `beatsaber` to `beatsaber_replaced`
2. Use Unity to swap only the audio clip
3. Keep all other assets
4. Build PKG
5. Install and verify audio plays

**Expected Outcome:** Confirms audio replacement works

---

## What to Report Back

After each test, please report:

1. **Test Name:** Which test you tried
2. **Result:** Success / Partial / Failed
3. **Errors:** Any error messages
4. **Screenshots:** Useful if showing UI issues
5. **Observations:** What the game showed/didn't show

---

## Current Blocker

We need to verify that Unity 2022.3 can create AssetBundles that:
1. Are in the correct format for Beat Saber PS4
2. Load properly when added to the game

Once we confirm this, we can build the full automation pipeline.

---

## Files Created

| File | Purpose |
|------|---------|
| `unity_project/README.md` | Setup instructions |
| `unity_project/Assets/Scripts/CustomBeatmapLevel.cs` | Level component |
| `unity_project/Assets/Editor/BeatSaberMenu.cs` | Editor menus |
| `unity_project/Assets/Editor/AudioImporter.cs` | Audio settings |
| `unity_project/Assets/Scripts/TestAudioPlayback.cs` | Test script |