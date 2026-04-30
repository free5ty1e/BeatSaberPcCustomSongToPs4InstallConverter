# Orb is CLI Build Approach (orbis-pub-cmd.exe)

## Status: ❌ BLOCKED - sc.exe version check failing

## Overview
Use the command-line tool `orbis-pub-cmd.exe` to build PKGs programmatically.

## What Works
- Wine runs Windows executables (using Wine Mono for .NET)
- orbis-pub-cmd.exe launches and shows help text
- The tool validates commands correctly
- Project.gp4 file is recognized

## What Doesn't Work
The build always fails with:
```
[Error] The version of sc.exe is invalid or missing.
```

## Root Cause Analysis
1. **sc.exe conflict**: Windows has a built-in `sc.exe` (Service Controller) in `C:\windows\system32\`
2. The PS4 sc.exe from the tools bundle is being shadowed by Windows' native sc.exe
3. Even when copied to Wine system32, orbis-pub-cmd can't find/validate the PS4 sc.exe version

## Attempts Made
| Attempt | Result | Notes |
|---------|--------|-------|
| Copy sc.exe to ~/.wine/drive_c/orbis-pub-gen/ | ❌ | Still fails |
| Copy sc.exe to ~/.wine/drive_c/windows/system32/ | ❌ | Windows sc.exe takes precedence |
| Rename PS4 sc.exe to ps4_sc.exe | ❌ | Hardcoded to look for "sc.exe" |
| Run from different directories | ❌ | Same error |
| Set PATH in Windows cmd | ❌ | Same error |
| Run from Wine cmd | ❌ | Same error |

## Technical Details
```bash
# Command that should work:
cd /workspace/beat-saber-ps4-custom-songs/orbis-pub-gen
WINEDEBUG=fixme-all xvfb-run -a wine C:\\orbis-pub-gen\\orbis-pub-cmd.exe img_create C:\\orbis-pub-gen\\Project.gp4 C:\\orbis-pub-gen\\custom.pkg

# Returns: [Error] The version of sc.exe is invalid or missing.
```

## Environment Setup
```dockerfile
# In .devcontainer/Dockerfile:
RUN wine msiexec /i /tmp/wine-mono.msi /qn  # Required for .NET

RUN mkdir -p ~/.wine/drive_c/orbis-pub-gen
COPY orbis-pub-gen/*.exe ~/.wine/drive_c/orbis-pub-gen/
COPY orbis-pub-gen/*.dll ~/.wine/drive_c/orbis-pub-gen/
COPY orbis-pub-gen/ext/* ~/.wine/drive_c/orbis-pub-gen/
```

## Manual Workaround (if found)
1. Would need to disable Windows' sc.exe or rename it
2. Or find a way to make orbis look in the correct directory

## Future Attempts
- Try older version of PS4 Fake PKG Tools (v4-v6)
- Try patching sc.exe detection
- Try running with Windows Defender disabled in Wine

## Date Tested
2026-04-29