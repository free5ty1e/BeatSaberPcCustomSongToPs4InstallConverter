# Beat Saber PS4 Custom Songs Pipeline

A build system to download Beat Saber PC songs and create installable PS4 fPKG files for GoldHEN jailbroken PlayStation 4.

## Project Overview

This pipeline:
1. Downloads songs from BeatSaver API (PC version)
2. Converts to PS4-compatible format  
3. Generates installable fPKG packages

## Quick Start

### Prerequisites
- Docker (for devcontainer)
- OR Python 3.10+ on host machine

### Build Pipeline

```bash
cd /workspace/beat-saber-ps4-custom-songs
python3 pipeline.py
```

### Output Files
- `output/custom_songs_v*.pkg` - Main DLC package
- `output/custom_unlocker_v*.pkg` - Unlocker package

---

## Documentation Index

### Core Documentation
- **[PROGRESS.md](./PROGRESS.md)** - Current development progress and test results
- **[pipeline.py](./pipeline.py)** - Main build orchestrator

### Build Scripts
- **[scripts/build_pkg_v6.py](./scripts/build_pkg_v6.py)** - Custom header PKG builder
- **[scripts/build_pkg_v7.py](./scripts/build_pkg_v7.py)** - Template clone PKG builder (reference-based)
- **[scripts/create_unlocker_v3.py](./scripts/create_unlocker_v3.py)** - Unlocker PKG builder

### AI Memory
- **[.ai_memory/beat-saber-ps4-custom-songs/conversation_history.md](../.ai_memory/beat-saber-ps4-custom-songs/conversation_history.md)** - Full conversation history
- **[.ai_memory/beat-saber-ps4-custom-songs/research_findings.md](../.ai_memory/beat-saber-ps4-custom-songs/research_findings.md)** - Technical research

---

## Test Results

| Version | Method | Status | Error |
|---------|--------|--------|-------|
| v1-v4 | Python custom | CE-34707-1 | Various |
| v5 | Python (64-bit BE) | CE-36426-1 | Wrong endianness |
| v6 | Python (32-bit LE) | CE-36426-1 | Header issue |
| v7 | Template clone | TEST PENDING | - |

### Known Errors
- **CE-36426-1**: PKG header format issue - PS4 rejects the package
- **CE-34707-1**: Different header error in earlier versions  
- **Orbis-pub-gen "File does not exist"**: GP4 path or duplicate entries issue

---

## Windows Build (Orbis-Pub-Gen)

### File Structure
```
windows_build/
├── Project.gp4              ← GP4 project file
├── CUSA12878-app/          ← Main app folder
│   ├── sce_sys/
│   │   ├── param.sfo
│   │   └── icon0.png
│   └── songs/              ← Song folders (by hash)
│       └── [hash]/
│           └── ...
└── output/                 ← PKG output
```

### GUI Instructions
1. Open `orbis-pub-gen.exe` or double-click `Project.gp4`
2. File → Open Project → Select `Project.gp4`
3. Click "Build PKG" or press F5
4. Output goes to `./output/` folder

**IMPORTANT**: Run from the `windows_build` folder itself, not a subfolder.

### CLI Instructions
```bash
cd C:\path\to\windows_build
orbis-pub-gen image Project.gp4
```

### Troubleshooting

**"File does not exist: param.sfo"**
- Check GP4 file paths match actual folder structure
- Ensure you're running from windows_build folder
- Try CLI for detailed errors

**"Duplicate entry" warning**
- Check Project.gp4 doesn't list same file twice

---

## Key Technical Details

### Reference PKG Structure
- **Magic**: `7fCNT` (0x7f434e54)
- **Content ID**: `UP4882-CUSA12878_00-P1S5XXXXXXXXXXXX`
- **Title ID**: `CUSA12878`
- **DRM Type**: 0x0f (free)
- **Content Type**: 0x1b (DLC)

### Header Fields (32-bit LE)
| Offset | Description |
|--------|-------------|
| 0x10 | Entry table offset |
| 0x14 | Entry count |
| 0x18 | Body offset |
| 0x20 | Body size |
| 0x28 | PFS offset |

### Songs Data
- **94+ songs** downloaded from BeatSaver API
- Located in: `songs_repo/` and `windows_build/CUSA12878-app/songs/`

---

## References

- [BeatSaver API](https://beatsaver.com/) - PC song database
- [GoldHEN](https://github.com/GoldHEN/GoldHEN/) - PS4 jailbreak
- [OpenOrbis LibOrbisPkg](https://github.com/OpenOrbis/LibOrbisPkg) - PKG tools

---

*Project: Beat Saber PS4 Custom Songs Pipeline*  
*Documentation Last Updated: 2026-04-27*