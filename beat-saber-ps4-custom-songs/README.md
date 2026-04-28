# Beat Saber PS4 Custom Songs - Repository

Build custom song PKGs for Beat Saber on PS4.

---

## Status

| Component | Status |
|-----------|--------|
| Song Downloader | ✅ Working - 94 songs downloaded |
| Beatmap Converter | ✅ Working |
| PKG Builder (LibOrbisPkg) | ⚠️ Needs configuration |

---

## Quick Start

### 1. Download Songs

```bash
cd /workspace/beat-saber-ps4-custom-songs
python3 scripts/download_repo.py
```

Songs go to `songs_repo/` (94 songs)

### 2. Build PKG

```bash
export PATH="$HOME/.dotnet:$PATH"
cd /workspace/beat-saber-ps4-custom-songs
python3 scripts/build_pkg.py songs_test/ --output test_10songs.pkg
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/download_repo.py` | Download songs from BeatSaver |
| `scripts/build_pkg.py` | Convert & build PKG (uses LibOrbisPkg) |
| `scripts/generate_unlocker.py` | Generate game-specific unlocker |

---

## Installation on PS4

### Files Needed (2 files):

1. **Unlocker** (game-specific)
   - `output/UP8802-CUSA12878_00-BSCUSTOMSONGS01-unlock.pkg`

2. **Songs PKG**
   - `output/test_10songs.pkg`

### Steps:

1. Copy both PKGs to USB root
2. GoldHEN > Install Package > Install Package Files
3. Install unlocker FIRST, then songs PKG
4. Launch Beat Saber > find songs at bottom of list

---

## Game IDs

| Region | Game ID |
|--------|---------|
| US | CUSA12878 |
| EU | CUSA12940 |
| JP | CUSA12942 |

---

## PKG Format

PKG files must follow Sony's format. The current build script uses **LibOrbisPkg** from OpenOrbis:
- GitHub: https://github.com/OpenOrbis/LibOrbisPkg
- Built from source: `LibOrbisPkg/LibOrbisPkg.Core.sln`

### Requirements:
- .NET SDK 8.0
- LibOrbisPkg PkgTool (already built in this repo)

---

## Known Issues

1. **PKG Installation Error (CE-34706-0)**: Our initial custom PKGs used wrong format. Need proper PKG structure.

2. **LibOrbisPkg GP4 paths**: The GP4 project file needs careful path handling (backslash vs forward slash).

3. **Content ID length**: Must be exactly 36 characters.

---

## Pre-built Unlocker

An unlocker for US version (CUSA12878) is included:
- `output/UP8802-CUSA12878_00-BSCUSTOMSONGS01-unlock.pkg`

---

## Current Songs (10 test songs)

1. VOLUPTE - Tare (BPM 128)
2. Yes I'm A Mess - AJR (BPM 184)
3. We All Lift Together (BPM 134)
4. YONA YONA DANCE - Akiko Wada (BPM 145)
5. Overdose - Natori (BPM 118)
6. LIT - Polyphia (BPM 99)
7. MUSIC STAR - M.G.G. Original (BPM 160)
8. KING - Ayunda Risu (BPM 166)
9. Megalovania - Toby Fox (BPM 120)
10. Mirror - Ado (BPM 114)

All have: Easy + Normal + Hard + Expert + ExpertPlus

---

## Song Download Criteria

Downloaded songs must have:
- ✅ **Easy** difficulty
- ✅ **Normal** difficulty  
- ✅ **Hard** difficulty

This ensures user (plays Hard) and friends (play Easy/Normal) can all play.

---

## BeatSaver API

**Status:** ✅ Working

```bash
curl https://api.beatsaver.com/search/text/0
```

**Download pattern:**
```
https://r2cdn.beatsaver.com/{hash}.zip
```

---

## Repository Structure

```
beat-saber-ps4-custom-songs/
├── songs_repo/              # Downloaded songs (94)
├── songs_test/             # 10 test songs
├── output/
│   └── *.pkg             # Built PKGs
├── scripts/
│   ├── download_repo.py
│   ├── build_pkg.py
│   └── generate_unlocker.py
└── LibOrbisPkg/          # Open-source PKG tools (built)
```

---

## Next Steps

1. Fix PKG format to work with PS4 (CE-34706-0 error)
2. Test with proper PKG generation
3. Install on PS4 and verify songs appear

---

**Last Updated:** April 2026