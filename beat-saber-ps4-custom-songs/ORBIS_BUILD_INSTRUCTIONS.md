# Beat Saber PS4 Custom Songs - Full Build Guide

## Overview

This document explains how to build custom songs PKGs for Beat Saber on PS4 using orbis-pub-gen.exe from PS4 Fake PKG Tools v7.

**Current Status:** We've achieved a breakthrough - orbis-pub-gen can now open our GP4 project files.

## Files Ready for Build

### Location: `beat-saber-ps4-custom-songs/windows_build/`

| File                | Description                                    |
| ------------------- | ---------------------------------------------- |
| `Project_full.gp4`  | Complete project with all 94 songs (829 files) |
| `Project_ref.gp4`   | Reference format (no songs - for testing)      |
| `sce_sys/param.sfo` | System file                                    |
| `sce_sys/icon0.png` | Icon                                           |
| `songs/`            | All 94 song folders with difficulty files      |

### Also in `output/` folder:

| File                     | Description                               |
| ------------------------ | ----------------------------------------- |
| `custom_unlocker_v3.pkg` | Python-generated unlocker (may not work)  |
| `custom_songs_v6.pkg`    | Python-generated songs PKG (may not work) |
| `custom_songs_v7.pkg`    | Python-generated songs PKG (may not work) |

## Step-by-Step: Building with orbis-pub-gen

### Prerequisites

- PS4 Fake PKG Tools v7 (orbis-pub-gen.exe)
- A Windows machine with display, OR use Wine in devcontainer

### Option 1: Using Wine in Devcontainer

1. **Ensure Wine is configured:**

   ```bash
   wine cmd /c "echo test"
   ```

2. **Copy project files to Wine:**

   ```bash
   cp -r windows_build/songs ~/.wine/drive_c/orbis-pub-gen/
   cp windows_build/sce_sys/param.sfo ~/.wine/drive_c/orbis-pub-gen/sce_sys/
   cp windows_build/sce_sys/icon0.png ~/.wine/drive_c/orbis-pub-gen/sce_sys/
   ```

3. **Run orbis-pub-gen GUI:**

   ```bash
   cd ~/.wine/drive_c/orbis-pub-gen
   wine orbis-pub-gen.exe
   ```

4. **In the orbis window:**
   - Go to File → Open Project
   - Select `Project_full.gp4`
   - Build dialog appears with these exact settings:

   **REQUIRED SETTINGS (from screenshot):**
   - Build Type: `pkg` (selected from dropdown)
   - Output Path: Set to your desired output location, e.g., `custom_songs.pkg`
   - Content ID: `UP4882-CUSA12878_00-P1S5XXXXXXXXXXXX`
   - Title: `Beat Saber`
   - Kaufman Option: CHECKED (first checkbox)
   - Kaufman Option: CHECKED (second checkbox)

   - Press F5 or click Build button at bottom

5. **Wait for build to complete**

### Option 2: Using Windows Directly

1. **Transfer files to Windows machine:**
   - Copy entire `windows_build/` folder to Windows
   - Place in easy location like `C:\beat-saber\`

2. **Run orbis-pub-gen.exe**

3. **In the orbis window:**
   - File → Open Project → Select `Project_full.gp4`
   - Configure build:
     - Output: `custom_songs.pkg`
     - Format: PKG (not ISO)
   - Press F5 to build

   **REQUIRED SETTINGS (from screenshot):**
   - Build Type: `pkg` (selected from dropdown)
   - Output Path: Set to your desired output location, e.g., `custom_songs.pkg`
   - Content ID: `UP4882-CUSA12878_00-P1S5XXXXXXXXXXXX`
   - Title: `Beat Saber`
   - Kaufman Option: CHECKED (first checkbox)
   - Kaufman Option: CHECKED (second checkbox)

4. \*\*Copy resulting `custom_songs.pkg` back to PS4

## Installing on PS4

### Order Matters:

1. **First:** Install any unlocker (try `custom_unlocker_v3.pkg` from output folder)
2. **Then:** Install your newly built `custom_songs.pkg`

### Via GoldHEN:

1. Enable FTP server in GoldHEN
2. Transfer PKGs to PS4 using FTP client
3. Or use USB: copy PKGs to `USBDUMP` folder
4. Run fPKG Installer

## Troubleshooting

### orbis opens GP4 but shows "File does not exist (param.sfo)"

- Ensure param.sfo is in correct location in the folder structure the GP4 expects
- Check sce_sys folder is correctly set up

### Build fails

- Check disk space (need ~500MB free)
- Try without digest calculation for faster build
- Make sure all song files exist

### Install fails with CE-36426-1

- This is the header error we've been fighting
- Try a different build method or different unlocker
- The orbis-built version might work even if Python versions didn't

### Install fails with CE-34707-1

- Different error - might indicate wrong content ID or format
- Check param.sfo is correct

## Song Information

**94 total songs** in repository

**Difficulty coverage:**

- Easy: 100%
- Normal: 100%
- Hard: 100%
- Expert: 97%
- ExpertPlus: 90%

All songs have at least Easy, Normal, and Hard difficulties - meets your criteria!

## Content ID

All PKGs use: `UP4882-CUSA12878_00-P1S5XXXXXXXXXXXX`

(This matches the working DLC reference)

## Last Updated

2026-04-30
