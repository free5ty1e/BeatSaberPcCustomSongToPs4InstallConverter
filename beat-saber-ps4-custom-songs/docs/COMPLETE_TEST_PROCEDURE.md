# Beat Saber PS4 - Complete Test Procedure

## Overview
This document contains step-by-step instructions for testing the custom songs pipeline.
Complete these tests in order - each builds on the previous.

---

## IMPORTANT: Project Folder Path

**CORRECT PATH:**
```
beat-saber-ps4-custom-songs/unity_project/
```

**Note:** The repository has TWO Unity project folders:
- `unity_project/` - NEW (with test audio and new scripts) ← USE THIS ONE
- `unity_project` (legacy, no version specified, ignore)

---

## Prerequisites
- [ ] Unity Hub installed on your PC
- [ ] Unity 2022.3.22f1 installed (LTS version)
- [ ] UABEA tool (https://github.com/nesrak1/UABEA)
- [ ] PkgToolBox available
- [ ] GoldHEN installed on PS4

---

## TEST 1: Unity AssetBundle Creation

### Purpose
Verify Unity 2022.3 can create compatible AssetBundles for Beat Saber PS4.

### Steps

#### 1.1 Open Unity Project
1. Launch **Unity Hub**
2. Click **Open** button
3. Navigate to: `BeatSaberPs4CustomSongSupport/beat-saber-ps4-custom-songs/unity_project/`
4. Click **Select Folder**
5. **IMPORTANT:** When asked which version, select: **2022.3.22f1**
6. Wait for Unity to load (may take a few minutes)

#### 1.2 Install PS4 Build Support (if needed)
If Unity shows errors about PS4:
1. Close Unity
2. Open Unity Hub → **Installs**
3. Click the gear icon next to 2022.3.22f1
4. Click **Add Modules**
5. Check **PS4 Build Support**
6. Wait for install (~2GB)
7. Reopen the project

#### 1.3 Verify Test Audio
1. In Unity, open **Project** window (bottom left)
2. Navigate to: `Assets` → `Audio`
3. You should see: `test_song.ogg` (4.8 MB / 4,853,144 bytes)

#### 1.4 Create Custom Level
1. Unity menu: **BeatSaber** → **Create Custom Level**
2. A new GameObject "CustomBeatmapLevel" appears in Hierarchy
3. Click on it to select it

#### 1.5 Configure Level Properties
In the **Inspector** panel (right side), fill in these fields:

| Field | Enter This Value |
|-------|-----------------|
| **Level ID** | `test_song` |
| **Song Name** | `Test Custom Song` |
| **Artist Name** | `Test Artist` |
| **Level Author Name** | `CustomMapper` |
| **Beats Per Minute** | `120` |
| **Preview Duration** | `30` |

#### 1.6 Assign Audio Clip
1. Find the **Audio Clip** field in the Inspector
2. Drag `test_song.ogg` from the Project window to that field
   - OR click the circle button → select `test_song`

#### 1.7 Build AssetBundle
1. Unity menu: **BeatSaber** → **Build for PS4**
2. Watch the **Console** tab (bottom) for progress
3. Wait until you see: `Build complete!`

#### 1.8 Check Output
1. Unity menu: **BeatSaber** → **Open Output Folder**
2. A file explorer window opens
3. Navigate to the `output` folder → `CustomLevels`
4. **You should see these files:**
   - `CustomLevels` (the main AssetBundle)
   - `CustomLevels.manifest`
   - `CustomLevels.assets`
   - `build_metadata.json`

#### 1.9 Report Results
**Open a text file and record these answers:**

```
=== TEST 1 RESULTS ===

1. Build Success? (Yes/No):
2. Errors in Console? (List any red messages):
3. Files in output/CustomLevels/:
   - 
4. File sizes:
   - 
```

---

## TEST 2: Verify Unity Output with UABEA

### Purpose
Confirm the Unity AssetBundle structure matches Beat Saber's format.

### Steps

#### 2.1 Open Unity AssetBundle in UABEA
1. Launch **UABEA** on your Windows PC
2. Click **File** → **Open**
3. Navigate to: `beat-saber-ps4-custom-songs/output/CustomLevels/`
4. Select the file named: `CustomLevels` (no extension)
5. Click **Open**

#### 2.2 Examine Structure
Look at the **left panel** - what assets do you see?
Look at the **right panel** - what details are shown?

#### 2.3 Compare with Original
1. In a **new** UABEA window
2. Open: `ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/beatsaber`
3. Compare the structures side by side

#### 2.4 Report Results
```
=== TEST 2 RESULTS ===

1. Unity bundle assets found (list them):
   - 
2. Original beatsaber assets found (list them):
   - 
3. Do they match? (Yes/No/Partial):
4. Missing items in Unity version:
   - 
```

---

## TEST 3: UABEA Rename/Import Test

### Purpose
Test if UABEA can import custom resources.

### Steps

#### 3.1 Export Resource File
1. UABEA → File → Open
2. Open: `ps4_dump/.../BeatmapLevelsData/beatsaber`
3. In left panel, click on **AudioClip** (the audio section)
4. Top menu: **Plugin** → **Export Audio File**
5. Save as: `my_audio.ogg`

#### 3.2 Try Import
1. With the same file open in UABEA
2. Top menu: Look for **Import** options
3. Try **Import Dump** or **Import Raw**
4. Select the exported `my_audio.ogg`

#### 3.3 Report Results
```
=== TEST 3 RESULTS ===

1. Import options found:
2. Any working import method:
3. Errors encountered:
```

---

## TEST 4: Basic PKG Build Test

### Purpose
Verify PKG building works.

### Steps

#### 4.1 Check Previous Build
Look at: `beat-saber-ps4-custom-songs/windows_build/`

#### 4.2 Create New PKG (if needed)
```bash
cd beat-saber-ps4-custom-songs
./PkgToolBox/PkgToolBox.Linux/PkgToolBox -mode=create -input=ps4_dump/CUSA12878-patch/ -output=test_pkg.pkg
```

#### 4.3 Report Results
```
=== TEST 4 RESULTS ===

1. PKG created? (Yes/No):
2. PKG size: ___ MB
3. Ready for PS4 testing:
```

---

## TEST 5: Full End-to-End Test (Goal)

### Steps

#### 5.1 Create PKG with Custom Level
1. Copy Unity output to test location
2. Run PkgToolBox to create PKG
3. Transfer to PS4 via USB or FTP

#### 5.2 Install and Test
1. GoldHEN → Settings → Game → Install Package
2. Select PKG
3. Launch Beat Saber

#### 5.3 Report Results
```
=== TEST 5 RESULTS ===

1. PKG installed:
2. Beat Saber launched:
3. New songs visible:
4. Song name shown:
5. Audio plays:
```

---

## Troubleshooting

### "Wrong version" error in Unity Hub
- The project version was set to "UnknownUnityVersion"
- **FIX:** I just updated `ProjectSettings/ProjectVersion.txt`
- Try opening again

### "PS4 SDK not found"
- **FIX:** Install PS4 Build Support via Unity Hub

### Build fails with errors
- Check the **Console** tab for details
- Common fix: Install missing modules

---

## File Locations Reference

| File | Path |
|------|------|
| Test audio | `unity_project/Assets/Audio/test_song.ogg` |
| Unity output | `unity_project/../output/CustomLevels/` |
| Original level | `ps4_dump/.../BeatmapLevelsData/beatsaber` |
| This doc | `docs/COMPLETE_TEST_PROCEDURE.md` |