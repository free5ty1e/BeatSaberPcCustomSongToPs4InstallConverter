# Simplified Approach: Song Replacement

## The Shortest Path to Victory

**No plugin needed!** We can modify existing level AssetBundles directly.

---

## Approach: Replace Existing Songs

### How It Works

Each song in `BeatmapLevelsData/` is a single AssetBundle file containing:
1. **BeatSaberBeatmapLevelData** - Level metadata
2. **AudioClip** - The song audio (embedded!)
3. **PPtr references** - Pointers to assets within the bundle

### Strategy

1. **Copy** an existing level (e.g., "beatsaber")
2. **Modify** its metadata (song name, BPM, etc.)
3. **Replace** the AudioClip with new audio
4. **Rename** to new level ID
5. **Add** to PKG build
6. **Play!** - Game auto-loads all levels from BeatmapLevelsData/

### Advantages

- No plugin required
- No PS4 debugging needed
- Works with existing game code
- Songs appear in game automatically

### Limitations

- Limited number of level slots (depends on free space)
- Need to fit within PKG size limits
- May need to remove existing songs to make room

---

## Step-by-Step Process

### Step 1: Prepare Your Songs

For each custom song, prepare:
1. **Audio file** - OGG format, 128-320 kbps
2. **Song metadata** - Name, artist, BPM, difficulties

### Step 2: Copy Existing Level

1. Copy `beatsaber` to `mysong` in BeatmapLevelsData/
2. Open in UABEA
3. Export the AudioClip

### Step 3: Replace Audio

1. In UABEA, select the AudioClip
2. Click **Plugin** → **AudioClip** → **Import**
3. Select your new OGG file
4. Save the AssetBundle

### Step 4: Update Metadata

1. Select BeatSaberBeatmapLevelData in UABEA
2. Modify these fields:
   - `levelID` → your song ID
   - `beatsPerMinute` → song BPM
   - `songTimeOffset` → usually 0
   - `previewDuration` → 30 seconds

### Step 5: Build PKG

1. Add modified levels to project
2. Build PKG
3. Install and test

---

## File Structure After Modification

```
CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/
├── beatsaber          (original tutorial)
├── mysong1            (custom song 1)
├── mysong2            (custom song 2)
├── mysong3            (custom song 3)
└── ... (more songs)
```

Game automatically sees all levels - no plugin needed!

---

## Size Considerations

| Song Format | Approximate Size per Song |
|-------------|---------------------------|
| 128 kbps OGG | ~3 MB per 3-minute song |
| 192 kbps OGG | ~5 MB per 3-minute song |
| 320 kbps OGG | ~8 MB per 3-minute song |

**Tip:** Use 128-192 kbps for more songs fit.

---

## Album/Category Question

The game likely auto-categorizes songs based on:
- Official songs (built-in packs)
- DLC songs (from Addressables)
- Custom songs (from BeatmapLevelsData)

**Our custom songs will appear in-game**, likely in "Extras" or a custom section.

We don't need to modify the album system - just add songs to BeatmapLevelsData!

---

## Next Steps

1. Create Python script to automate the replacement process
2. Test with one custom song
3. Build PKG and verify game loads it
4. Scale up to more songs

This is MUCH simpler than building a plugin!