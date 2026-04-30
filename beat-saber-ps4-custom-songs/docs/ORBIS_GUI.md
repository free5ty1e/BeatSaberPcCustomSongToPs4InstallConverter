# Orb is GUI Build Approach (orbis-pub-gen.exe)

## Status: ⚠️ RUNNING - process starts but needs GUI interaction to build

## Overview
Use the GUI tool `orbis-pub-gen.exe` to build PKGs through the graphical interface.

## What Works
- Wine runs Windows executables with wine-mono installed
- orbis-pub-gen.exe launches as a GUI window (xvfb for headless)
- Process starts and stays running (not immediately crashing)
- The DLL (orbis-pub-prx.dll) is found when running from Wine C: drive

## What Doesn't Work (Yet)
- GUI runs but doesn't automatically build PKG
- Requires user interaction to:
  1. Open the GP4 project file
  2. Press F5 or click Build
  3. Select output location
- Running headless without X11 interaction means the build never completes

## Root Cause Analysis
1. **GUI requires X11 interaction**: The build process needs user clicks/keypresses
2. **Headless Wine has no UI**: Running with xvfb-run provides a virtual display but no interactivity
3. **Need automation**: Would need a tool to send keystrokes/mouse clicks to Wine

## Attempts Made
| Attempt | Result | Notes |
|---------|--------|-------|
| Run from project folder | ❌ | Can't find orbis-pub-prx.dll |
| Run wine C:\\orbis-pub-gen\orbis-pub-gen.exe | ⚠️ | Starts but no build |
| Set WINEDLLPATH | ⚠️ | Same - starts but no build |
| Run in background with nohup | ⚠️ | Process runs indefinitely |
| Wait 30+ seconds | ⚠️ | No output PKG generated |

## Technical Details
```bash
# Start GUI (runs but waits for input):
cd /workspace/beat-saber-ps4-custom-songs/orbis-pub-gen
WINEDLLPATH="C:\\orbis-pub-gen" WINEDEBUG=fixme-all \
  xvfb-run -a wine C:\\orbis-pub-gen\\orbis-pub-gen.exe

# Process starts:
# vscode   76865  0.9  0.6 2711968 53876 ?  SNl  C:\orbis-pub-gen\orbis-pub-gen.exe
# (stays running - waiting for user input)
```

## Environment Setup
```dockerfile
# Same as CLI - wine-mono required:
RUN wget -q "https://dl.winehq.org/wine/wine-mono/8.1.0/wine-mono-8.1.0-x86.msi" -O /tmp/wine-mono.msi
RUN wine msiexec /i /tmp/wine-mono.msi /qn

# Files in Wine:
RUN mkdir -p ~/.wine/drive_c/orbis-pub-gen
COPY orbis-pub-gen/*.exe ~/.wine/drive_c/orbis-pub-gen/
COPY orbis-pub-gen/*.dll ~/.wine/drive_c/orbis-pub-gen/
COPY orbis-pub-gen/ext/* ~/.wine/drive_c/orbis-pub-gen/
```

## Paths to Try
- C:\orbis-pub-gen\orbis-pub-gen.exe ✅ (process starts)
- C:\orbis-pub-gen\orbis-pub-cmd.exe ❌ (sc.exe check fails)
- PSX-PS2-FPKG\pkg.exe ⚠️ (untried - PS4/PS2 version)

## Solutions to Try Next

### Option 1: Automation Script
Use xdotool or xte to send keystrokes:
```bash
# Run GUI, wait for window, send F5, send Enter
xdotool key F5
```

### Option 2: Use CLI Alternative (PSX-PS2-FPKG)
The PSX-PS2-FPKG version may use a different sc.exe check:
```
/orbis-pub-gen/PSX-PS2-FPKG/pkg.exe
```

### Option 3: PowerShell Automation
Use PowerShell to interact with Wine GUI via SendKeys or UI automation APIs

### Option 4: Manual Build (Current Workaround)
Run manually in the Docker volume with GUI:
```bash
# In container with display/GUI access:
wine C:\orbis-pub-gen\orbis-pub-gen.exe
# Then manually:
# 1. File > Open Project
# 2. Select Project.gp4
# 3. Press F5 or Build button
# 4. Save as custom.pkg
```

## Environment Requirements
- Wine 9.0+ (Ubuntu 24.04 packages)
- wine-mono 8.1.0.msi
- winbind (for NTLM auth)
- xvfb (for headless virtual display)
- PS4 Fake PKG Tools v7 (CyB1K/PS4-Fake-PKG-Tools-3.87)

## Date Tested
2026-04-29