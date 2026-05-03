# Beat Saber PS4 - Complete Test Procedure

## Overview
This document contains step-by-step instructions for testing the custom songs pipeline.
Complete these tests in order - each builds on the previous.

---

## Prerequisites
- [ ] Unity Hub installed
- [ ] Unity 2022.3 LTS installed
- [ ] UABEA tool downloaded (https://github.com/nesrak1/UABEA)
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
3. Navigate to: `beat-saber-ps4-custom-songs/unity_project/`
4. Click **Select Folder**
5. Wait for Unity to load (may take a few minutes)

#### 1.2 Install PS4 Build Support (if needed)
1. Unity menu: **Edit** → **Preferences** → **External Tools**
2. Scroll to **PS4**
3. If shows "Not installed", close Unity
4. Unity Hub → **Installs** → Click 2022.3 version
5. Click **Add Modules** → Check **PS4 Build Support**
6. Install (~2GB download)

#### 1.3 Verify Test Audio
1. In Unity, open **Project** window (bottom left)
2. Navigate to: `Assets` → `Audio`
3. You should see: `test_song.ogg` (4.8 MB)
4. If not, copy from: `/workspace/beat-saber-ps4-custom-songs/unity_project/Assets/Audio/test_song.ogg`

#### 1.4 Create Custom Level
1. Unity menu: **BeatSaber** → **Create Custom Level**
2. A new GameObject "CustomBeatmapLevel" appears in Hierarchy
3. Select it (click on it)

#### 1.5 Configure Level Properties
In the **Inspector** panel (right side), configure:

| Field | Value |
|-------|-------|
| **Level ID** | `test_song` |
| **Song Name** | `Test Custom Song` |
| **Artist Name** | `Test Artist` |
| **Level Author Name** | `CustomMapper` |
| **Beats Per Minute** | `120` |
| **Preview Duration** | `30` |

#### 1.6 Assign Audio Clip
1. In Project window, drag `test_song.ogg` to the **Audio Clip** field
   OR
2. Click the circle button next to Audio Clip → Select `test_song`

#### 1.7 Build AssetBundle
1. Unity menu: **BeatSaber** → **Build for PS4**
2. Watch Console window (bottom) for progress
3. Wait for completion (may take 1-2 minutes)

#### 1.8 Check Output
1. Unity menu: **BeatSaber** → **Open Output Folder**
2. Navigate to: `output` → `CustomLevels`
3. You should see:
   - `CustomLevels`
   - `CustomLevels.manifest`
   - `CustomLevels.assets`
   - `build_metadata.json`

#### 1.9 Report Results
**Report these answers:**
1. Did the build succeed? (Any red errors?)
2. How many files were created in `output/CustomLevels/`?
3. List the files: `ls -la output/CustomLevels/`

---

## TEST 2: Verify Unity Output with UABEA

### Purpose
Confirm the Unity AssetBundle structure matches Beat Saber's format.

### Steps

#### 2.1 Open Unity AssetBundle in UABEA
1. Launch **UABEA**
2. Click **File** → **Open**
3. Navigate to: `beat-saber-ps4-custom-songs/output/CustomLevels/`
4. Select `CustomLevels` (no extension)
5. Click **Open**

#### 2.2 Examine Structure
In the left panel, you should see:
- Expandable tree of assets
- Look for: `AudioClip`, `GameObject`, `MonoBehaviour`

#### 2.3 Compare with Original
1. Open a **new** UABEA window
2. Open: `/workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/beatsaber`
3. Compare the structures

#### 2.4 Report Results
**Report these answers:**
1. What assets are in the Unity-built bundle?
2. Is there an `AudioClip` listed?
3. Are there any `BeatSaberBeatmapLevelData` objects?
4. How does it differ from the original `beatsaber` level?

---

## TEST 3: UABEA Rename/Import Test

### Purpose
Test if we can rename and import custom resources into existing levels.

### Steps

#### 3.1 Copy Resource File
1. Copy this file to a work folder:
   ```
   /workspace/temp/beatsaber_level_study/CAB-0183cf5e66ff23724b3e1bc22e7ea951.resource
   ```
2. Rename it to:
   ```
   CAB-mytcust.resource
   ```

#### 3.2 Open Original Level
1. UABEA → File → Open
2. Open: `/workspace/temp/beatsaber_level_study/beatsaber_uncompressed`
3. This is the uncompressed version for easier editing

#### 3.3 Try Import
1. Top menu: Click **Import Dump** (or similar import option)
2. Select your renamed `.resource` file
3. Answer "Is this asset serialized?" → **Yes**
4. Check if a new entry appears

#### 3.4 Report Results
**Report these answers:**
1. Did UABEA import the renamed file?
2. Did it appear as a new/different entry?
3. Any error messages?

---

## TEST 4: Basic PKG Build Test

### Purpose
Verify PKG building works with existing (unmodified) files.

### This test is already partially complete from previous work.
Your previous PKG build exists at:
```
/workspace/beat-saber-ps4-custom-songs/windows_build/
```

### Steps to Verify

#### 4.1 Check Previous Build
1. Look at existing files in: `beat-saber-ps4-custom-songs/windows_build/`
2. Find the `.pkg` file (if any)
3. Note its size

#### 4.2 Document Status
**Report:**
1. Do we have a working PKG file?
2. What is its size?
3. Have we tested it on PS4?

#### 4.3 If No Working PKG Exists
Run PkgToolBox:
```bash
cd /workspace/beat-saber-ps4-custom-songs
./PkgToolBox/PkgToolBox.Linux/PkgToolBox \
  -mode=create \
  -input=windows_build/ \
  -output=test_pkg.pkg
```

#### 4.4 Report Results
**Report:**
1. PKG file created? (Yes/No)
2. File size: ______ MB
3. Ready for PS4 testing? (Yes/No)

---

## TEST 5: Modified Level in PKG (Final Test)

### Purpose
Create a PKG with a Unity-built level and test on PS4.

### Steps

#### 5.1 Create Test Level Folder
1. Copy Unity output: `output/CustomLevels/CustomLevels`
2. To: `/workspace/temp/test_level`
3. Rename to: `test_song`

#### 5.2 Create Test PKG
Use PkgToolBox:
```bash
cd /workspace/beat-saber-ps4-custom-songs
./PkgToolBox/PkgToolBox.Linux/PkgToolBox \
  -mode=create \
  -input=/workspace/ps4_dump/CUSA12878-patch/ \
  -output=test_with_custom.pkg
```

#### 5.3 Transfer to PS4
1. Copy `test_with_custom.pkg` to USB drive
2. OR use FTP: `ftp://PS4-IP:2121` → `/data/`

#### 5.4 Install on PS4
1. GoldHEN → Settings → Debug Settings → Game → Install Package
2. Select `test_with_custom.pkg`
3. Wait for installation
4. Launch Beat Saber

#### 5.5 Report Results
**Report:**
1. Did PKG install successfully?
2. Did Beat Saber launch?
3. Did any new songs appear?
4. If so, what song name/ID?
5. Any errors or crashes?

---

## Troubleshooting

### Unity Build Fails
- **Error**: "PS4 SDK not found"
  - **Fix**: Install PS4 Build Support via Unity Hub

### UABEA Won't Open File
- **Error**: "Invalid AssetBundle"
- **Fix**: Ensure you selected file without extension (UABEA auto-detects)

### PKG Won't Install
- **Error**: "Cannot install"
- **Fix**: Enable "Allow installation of PKG files" in GoldHEN settings

---

## Progress Tracking

| Test | Status | Notes |
|------|--------|-------|
| Test 1: Unity Build | ⏳ Pending | |
| Test 2: UABEA Verify | ⏳ Pending | |
| Test 3: UABEA Import | ⏳ Pending | |
| Test 4: Basic PKG | ⏳ Pending | |
| Test 5: Modified PKG | ⏳ Pending | |

---

## Files Reference

| File | Location |
|------|----------|
| Test audio | `unity_project/Assets/Audio/test_song.ogg` |
| Unity output | `output/CustomLevels/` |
| Original level | `ps4_dump/.../BeatmapLevelsData/beatsaber` |
| UABEA tool | User's Windows machine |
| This document | `docs/COMPLETE_TEST_PROCEDURE.md` |