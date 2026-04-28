# Beat Saber PS4 Custom Songs - Complete Step-by-Step Guide

## Your Setup
- PS4 with GoldHEN jailbreak
- Decrypted Beat Saber game (CUSA12878)
- **Unity 2022.3.33f1** (LTS) - **REQUIRED** (game uses this version)
- AssetRipper (installed)

---

# CRITICAL DISCOVERY: Unity 2022.3.33f1

The PS4 game uses **Unity 2022.3.33f1**, NOT 2018.x!

## Download Unity 2022 LTS
1. Go to: https://unity.com/download
2. Install Unity Hub
3. Install **Unity 2022.3 LTS** (specifically 2022.3.33 or newer)
4. Include: **Linux Build Support**, **PS4 Build Support**

---

# PHASE 1: Analyze Your Exported Song

## Step 1.1: Review Exported Structure

You exported to: `ExportedSongs/100bills/AssetRipper_export_*/`

**Key files found:**

```
100bills/
├── 100BillsBeatmapLevelData.asset   # Level metadata (YAML)
├── $100Bills.ogg                     # Audio (OGG format!)
├── *.beatmap.gz.bytes                # GZIPPED beatmaps
│   ├── 100BillsEasy.beatmap.gz.bytes
│   ├── 100BillsNormal.beatmap.gz.bytes
│   ├── 100BillsHard.beatmap.gz.bytes
│   ├── 100BillsExpert.beatmap.gz.bytes
│   └── 100BillsExpertPlus.beatmap.gz.bytes
└── *.lightshow.gz.bytes              # Light show data
```

## Step 1.2: Beatmap Format (v4.0.0 JSON)

The beatmaps are **gzipped JSON** with format v4.0.0:

```json
{
  "version": "4.0.0",
  "colorNotes": [{"b": 8.0}, {"b": 12.0}],
  "colorNotesData": [
    {"x": 0, "d": 0, "c": 0},  // position, direction, color
    {"x": 2, "d": 1, "c": 1}
  ],
  "bombNotes": [],
  "obstacles": [],
  "chains": [],
  "arcs": []
}
```

**Key format differences from PC:**
- `b` = beat/time
- `x` = line index (0-3)
- `d` = direction (0-7)
- `c` = color (0=red, 1=blue)
- Bombs/obstacles use separate data arrays

---

# PHASE 2: Download Custom Songs (PC Format)

## Step 2.1: Get Songs from BeatSaver

1. **Go to**: https://beatsaver.com

2. **Download 10 popular songs:**
   - Search and download as ZIP files
   - Extract each to: `C:\beat-saber-ps4\songs\`

3. **Target songs:**
   - Crystallized (S辣的)
   - Crab Rave (acrispy)
   - Believer (Routers)
   - Bad Guy (Hex)
   - Blinding Lights (M展位)
   - About Damn Time (Benzel)
   - Abracadabra (Sot)
   - Accelerate (Checkthebpm)
   - 100 Bills Remix (Elliot)
   - Beloved (Manon)

## Step 2.2: Expected PC Structure

```
songs/
├── crystallized/
│   ├── info.dat
│   ├── Easy.dat
│   ├── Normal.dat
│   ├── Hard.dat
│   ├── Expert.dat
│   ├── ExpertPlus.dat
│   ├── song.ogg
│   └── cover.jpg
```

---

# PHASE 3: Convert PC Songs to PS4 Format

## Step 3.1: Automated Conversion

I've created a conversion script at:
```
scripts/convert_songs.py
```

**Run it:**
```bash
cd /workspace/beat-saber-ps4-custom-songs
python3 scripts/convert_songs.py
```

This converts:
- Beatmaps: JSON to gzipped JSON v4.0.0
- Audio: Copy OGG file
- Cover: Copy JPG
- Creates level data asset

## Step 3.2: What Conversion Does

| PC Format | PS4 Format |
|-----------|------------|
| `info.dat` (JSON) | `*BeatmapLevelData.asset` (YAML) |
| `Easy.dat` (JSON) | `Easy.beatmap.gz` (gzipped JSON) |
| `song.ogg` | `song.ogg` + `song.audio.gz` |
| `cover.jpg` | `cover.jpg` |

## Step 3.3: Manual Verification

After conversion, check output:
```
output/converted_songs/
├── crystallized/
│   ├── crystallizedBeatmapLevelData.asset
│   ├── Easy.beatmap.gz
│   ├── Normal.beatmap.gz
│   ├── Hard.beatmap.gz
│   ├── Expert.beatmap.gz
│   ├── ExpertPlus.beatmap.gz
│   ├── song.ogg
│   └── cover.jpg
```

---

# PHASE 4: Build Unity Asset Bundles

## Step 4.1: Open Unity Project

1. Open Unity Hub
2. Open: `beat-saber-ps4-custom-songs/unity-project/`
3. Unity version should auto-detect: **2022.3.33f1**

## Step 4.2: Import Converted Songs

1. Copy converted song folders into:
   ```
   Assets/Songs/
   ```

2. **Import Audio:**
   - Select each `song.ogg`
   - Inspector: Load Type = **Streaming**
   - Inspector: Compression = **Vorbis**

3. **Import Beatmaps:**
   - TextAssets with `.beatmap.gz` extension
   - Keep as Read/Write enabled

## Step 4.3: Create Level Prefab

For each song, create a GameObject with:
- CustomLevel component (I'll provide script)
- Reference to audio clip
- References to beatmap TextAssets

## Step 4.4: Build Asset Bundle

1. **Window > Asset Bundle Browser**
2. Add your song prefabs
3. Build platform: **PS4**
4. Output to: `../output/asset_bundles/`

---

# PHASE 5: Create PS4 PKG

## Step 5.1: Download Tools

### FPKG Tools 3.87
1. Go to: https://github.com/CyB1K/PS4-Fake-PKG-Tools-3.87/releases/tag/v7
2. Download: `PS4-Fake-PKG-Tools-3.87.7z`
3. Extract to: `C:\beat-saber-ps4\tools\FPKG-Tools\`

### psDLC (Unlocker)
1. Go to: https://github.com/codemasterv/psDLC-2.1-stooged-Mogi-PPSA-gui/releases
2. Download latest release
3. Extract to: `C:\beat-saber-ps4\tools\psDLC\`

## Step 5.2: Create DLC Structure

```
C:\beat-saber-ps4\output\dlc_package\
├── sce_sys\
│   └── param.sfo              (created next)
└── StreamingAssets\
    ├── BeatmapLevelsData\     (your custom songs)
    └── HmxAudioAssets\
        └── songs\             (audio files)
```

## Step 5.3: Create PARAM.SFO

1. **Open** `orbis-pub-sfo.exe` (in FPKG Tools)

2. **Settings:**
   - Category: `(PS4) Additional Content`
   - Content ID: `UP8802-CUSA12878_00-BSCUSTOMSONGS01`
   - Title: `Beat Saber Custom Songs`

3. **Save** to: `dlc_package\sce_sys\param.sfo`

## Step 5.4: Build PKG

1. **Open** `orbis-pub-gen.exe`

2. **New Project > Additional Content Package with Extra Data**

3. **Drag to Image0:**
   - `sce_sys` folder
   - `StreamingAssets` folder

4. **Project Settings:**
   - Content ID: `UP8802-CUSA12878_00-BSCUSTOMSONGS01`
   - Passcode: `00000000000000000000000000000000`

5. **Build** with "Skip digest" checked

6. **Output:** `UP8802-CUSA12878_00-BSCUSTOMSONGS01.pkg`

## Step 5.5: Create Unlocker

1. **Open** `psDLC.exe`

2. **Manual Input:**
   - Content ID: `UP8802-CUSA12878_00-BSCUSTOMSONGS01`

3. **Create FPKG**

4. **Rename** output to: `UP8802-CUSA12878_00-BSCUSTOMSONGS01-unlock.pkg`

---

# PHASE 6: Install on PS4

## Step 6.1: Prepare USB

1. Format USB as FAT32
2. Copy both PKGs to root:
   ```
   F:\
   ├── UP8802-CUSA12878_00-BSCUSTOMSONGS01.pkg
   └── UP8802-CUSA12878_00-BSCUSTOMSONGS01-unlock.pkg
   ```

## Step 6.2: Install

1. Connect USB to PS4
2. Launch GoldHEN
3. **Game > Install Package > / Packages**
4. **Install unlocker FIRST**, then DLC
5. Launch Beat Saber
6. Check "Extras" for custom songs

---

# QUICK REFERENCE

| Item | Value |
|------|-------|
| Game ID | CUSA12878 |
| Unity Version | **2022.3.33f1** (REQUIRED) |
| Content ID | UP8802-CUSA12878_00-BSCUSTOMSONGS01 |
| Audio Format | OGG (also gzip for streaming) |
| Beatmap Format | gzipped JSON v4.0.0 |
| Level Data | YAML asset file |

---

# FILES CREATED

```
/workspace/beat-saber-ps4-custom-songs/
├── unity-project/                  # Unity 2022.3.33 project
│   └── ProjectSettings/ProjectVersion.txt
├── scripts/
│   └── convert_songs.py            # PC to PS4 converter
├── output/
│   └── converted_songs/             # Converted songs go here
├── extracted/
│   └── COMPLETE_STEP_BY_STEP_GUIDE.md
└── tools/
    └── SONGS_LIST.md
```