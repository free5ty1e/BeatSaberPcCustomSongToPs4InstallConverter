# Orb is Build Status

## Current State

### CLI Approach (orbis-pub-cmd.exe) - ❌ BLOCKED
- Fails with `[Error] The version of sc.exe is invalid or missing`
- Windows sc.exe (Service Controller) conflicts with PS4 sc.exe

### GUI Approach (orbis-pub-gen.exe) - ⚠️ RUNS BUT NO PKG
- Process starts successfully with pyautogui automation
- No windowing system available in headless container - needs real DISPLAY
- Would work with GPU/display attached

### Python PKGs (v6, v7) - ✅ READY
- Already generated in `output/` folder
- Ready for testing on PS4

## Installed in Devcontainer
All tools are installed and configured:
- Wine + wine-mono (8.1.0)
- PS4 Fake PKG Tools v7 (CyB1K)
- pyautogui automation
- Files copied to ~/.wine/drive_c/orbis-pub-gen/

## Working Approach for PKG Build
```bash
# On a machine with display (not headless):
cd /workspace/beat-saber-ps4-custom-songs/orbis-pub-gen
wine C:\orbis-pub-gen\orbis-pub-gen.exe
# Then manually: File > Open Project > Project.gp4 > Press F5
```

## Date: 2026-04-29