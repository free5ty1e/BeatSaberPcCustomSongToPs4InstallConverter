# Beat Saber PS4 Custom Songs - INSTALLATION GUIDE

## Files Created

| File | Size | Purpose |
|------|------|---------|
| `UP8802-CUSA12878_00-BSCUSTOMSONGS01.pkg` | ~1.1 MB | Main DLC with 5 test songs |
| `UP8802-CUSA12878_00-BSCUSTOMSONGS01-unlock.pkg` | ~1.3 KB | License unlocker |

**Location:** `/workspace/beat-saber-ps4-custom-songs/output/`

---

## Installation Steps

### Step 1: Copy Files to USB

1. Format USB drive as **FAT32**
2. Copy both PKG files to the root of the USB drive:
   ```
   F:/
   ├── UP8802-CUSA12878_00-BSCUSTOMSONGS01.pkg
   └── UP8802-CUSA12878_00-BSCUSTOMSONGS01-unlock.pkg
   ```

### Step 2: Install on PS4

1. **Connect USB** to PS4
2. **Launch GoldHEN** homebrew enabler
3. Navigate to: **Game > Install Package > / Packages**
4. **Install in this order:**
   - First: `UP8802-CUSA12878_00-BSCUSTOMSONGS01-unlock.pkg` (unlocker)
   - Second: `UP8802-CUSA12878_00-BSCUSTOMSONGS01.pkg` (DLC)

### Step 3: Play Custom Songs

After installation:

1. **Launch Beat Saber**
2. Look for custom songs in these locations:
   - **Extras menu** (recommended - DLC appears here)
   - **Song Selection** > Look for new songs at the end of the list
   - **Online menu** if enabled

### Step 4: Troubleshooting

**Songs don't appear?**
- Make sure unlocker is installed FIRST
- Check that DLC appears in Game > Information
- Try restarting Beat Saber

**Game crashes?**
- This is test content with placeholder data
- Audio files are missing in this test version
- Try official songs first to verify installation works

---

## Songs Included (Test Version)

| Song | Difficulty Levels |
|------|-------------------|
| Crab Rave | Easy, Normal, Hard, Expert, Expert+ |
| Believer | Easy, Normal, Hard, Expert, Expert+ |
| Counting Stars | Easy, Normal, Hard, Expert, Expert+ |
| Blinding Lights | Easy, Normal, Hard, Expert, Expert+ |
| Feel Good Inc | Easy, Normal, Hard, Expert, Expert+ |

**Note:** These test songs have placeholder beatmaps (no actual notes). Real custom songs need to be downloaded from BeatSaver.com.

---

## How to Get Real Custom Songs

### Option 1: Download Now (BeatSaver API is down)

The BeatSaver API is currently unavailable. Check:
- https://status.beatsaver.com
- https://beatsaver.com

When available:
1. Go to https://beatsaver.com
2. Download song ZIP files
3. Extract to: `/workspace/beat-saber-ps4-custom-songs/songs/`
4. Run: `python3 scripts/build_simple.py`

### Option 2: Manual Download
1. Use a browser to download songs from BeatSaver
2. Transfer to your dev environment
3. Follow the conversion steps in `COMPLETE_STEP_BY_STEP_GUIDE.md`

---

## Project Status

### ✅ Completed
- PS4 PKG creation pipeline
- DLC structure creation
- PARAM.SFO generation
- Unlocker generation
- Test beatmap conversion

### ⚠️ Current Limitation
- **BeatSaver API is down** - Cannot auto-download songs
- **Audio conversion** needs development (PS4 uses encrypted audio)
- Test songs have placeholder beatmaps

### 📋 Next Steps (When API returns)
1. Download 50 popular songs from BeatSaver
2. Convert beatmaps to PS4 format
3. Add audio files (if format conversion works)
4. Rebuild PKG with real content

---

## Technical Details

| Item | Value |
|------|-------|
| Game ID | CUSA12878 |
| Content ID | UP8802-CUSA12878_00-BSCUSTOMSONGS01 |
| Unity Version | 2022.3.33f1 |
| Beatmap Format | gzipped JSON v4.0.0 |
| Audio Format | OGG (PC) → needs conversion |
| PKG Magic | 0x7FD8CF63 |

---

## File Locations

```
/workspace/beat-saber-ps4-custom-songs/
├── output/
│   ├── UP8802-CUSA12878_00-BSCUSTOMSONGS01.pkg         ← Main DLC
│   └── UP8802-CUSA12878_00-BSCUSTOMSONGS01-unlock.pkg   ← Unlocker
├── songs/                    ← Download songs here
├── scripts/
│   ├── build_simple.py       ← PKG builder
│   ├── download_final.py     ← Song downloader
│   ├── convert_songs.py      ← Beatmap converter
│   └── create_paramsfo.py    ← PARAM.SFO creator
└── extracted/
    └── COMPLETE_STEP_BY_STEP_GUIDE.md
```

---

## Testing Results

The pipeline has been tested with:
- ✅ PKG structure creation
- ✅ PARAM.SFO generation
- ✅ Beatmap format conversion (JSON → gzipped v4.0.0)
- ✅ DLC file packaging
- ✅ Unlocker generation

**Awaiting:** Real songs with audio files for full testing on PS4.

---

## Important Notes

1. **This is a proof-of-concept** - Test songs have placeholder data
2. **Audio encryption** - PS4 uses encrypted `.egg` format, not standard OGG
3. **Unity required for real bundles** - Asset bundles need Unity 2022.3.x to build
4. **GoldHEN required** - Standard PS4 cannot install custom PKGs

---

## Need Help?

Check the full guide at: `extracted/COMPLETE_STEP_BY_STEP_GUIDE.md`

Or review the pipeline progress: `.ai_memory/beat-saber-ps4-custom-songs/pipeline_progress.md`