# Beat Saber Deluxe (BSDX)

## Overview

This is a GoldHEN plugin for Beat Saber PS4 that enables custom songs, similar to how RB4DX works for Rock Band 4.

## Architecture

### Based on: RB4DX Plugin
- Reference: https://github.com/LlysiX/RB4DX-Plugin
- Used as template for GoldHEN plugin development

### Key Differences from RB4DX

| Aspect | Rock Band 4 (RB4DX) | Beat Saber |
|--------|---------------------|------------|
| Engine | Proprietary | Unity 2022 |
| Audio | FMOD | Unity AudioClip |
| Asset Format | .mid/.dta | AssetBundle |
| File Hook | `NewFile()` | `AssetBundle.LoadFromFile()` |
| Song Format | .mid files | .ogg + beatmap JSON |

### Target Game
- **Title ID**: CUSA12878
- **Firmware**: 9.00 (backported)
- **Version**: v2.04

## File Structure

```
beat_saber_dx/
├── source/
│   ├── main.c              # Plugin entry point
│   ├── plugin_common.c     # Common plugin utilities
│   └── hooks.c             # Beat Saber specific hooks
├── include/
│   ├── plugin_common.h     # Common definitions
│   └── beat_saber.h        # Beat Saber specific definitions
├── Makefile                # Build script
└── README.md               # This file
```

## Build Requirements

- OpenOrbis PS4 Toolchain
- GoldHEN Plugin SDK

## Current Status

**IN DEVELOPMENT** - We are working on:
1. Understanding Beat Saber PS4 function addresses
2. Identifying AssetBundle loading hooks
3. Creating minimal working plugin skeleton

## References

- RB4DX Plugin: https://github.com/LlysiX/RB4DX-Plugin
- GoldHEN Plugin SDK: https://github.com/GoldHEN/GoldHEN_Plugin_SDK
- OpenOrbis: https://github.com/OpenOrbis