# Beat Saber PS4 Deluxe - Project Status & TO DO

## Date: 2026-05-01

## Current Status

### ✅ Completed Research

1. **RB4DX Analysis** (docs/RB4DX_ARCHITECTURE.md)
   - Cloned full RB4DX source from GitHub
   - Analyzed GoldHEN plugin structure
   - Understood file redirection mechanism
   - Downloaded RB4DX installer package (812MB)

2. **Backporter Converter Analysis** (docs/BACKPORTER_CONVERTER_ANALYSIS.md)
   - Downloaded PS4-Beat-Saber-Dat-Creator.exe
   - Tool converts PC JSON → PS4 binary beatmap format
   - Tool is unmaintained (2021) and does SONG REPLACEMENT, not addition
   - Not directly usable for our goal

3. **Asset Format Analysis** (docs/ASSET_FORMAT_ANALYSIS.md)
   - Game uses Unity 2022.3 with LZ4HAM AssetBundles
   - Levels stored in `Media/StreamingAssets/BeatmapLevelsData/`
   - Each song is a folder with AssetBundle (e.g., `beatsaber/`, `believer/`)
   - DLC songs organized in `aa/PS4/` as addressable bundles (e.g., `billieeilish_pack_*`)

### 🔍 Key Discovery: "Option 3" Path is Viable

Looking at game structure, **Option 3 (insert into "Extras" album)** may work by:
1. Adding custom level folders to `BeatmapLevelsData/`
2. Modifying level catalog to include custom songs
3. **OR** creating a plugin that hooks level loading

But we need to understand the level catalog structure first.

## TO DO List

### Phase 1: Understand Game Structure (Current Focus)

- [ ] **1.1** Analyze level catalog structure in `globalgamemanagers.assets`
- [ ] **1.2** Find where "Extras" album is defined
- [ ] **1.3** Understand how levels are added to the song list
- [ ] **1.4** Extract a sample level with UABEA to see internal structure

### Phase 2: Build Conversion Pipeline

- [ ] **2.1** Create beatmap converter (PC JSON → PS4 binary format)
- [ ] **2.2** Create level AssetBundle builder (Unity 2022 format)
- [ ] **2.3** Test conversion with one song

### Phase 3: Build Beat Saber Deluxe Plugin

- [ ] **3.1** Create minimal GoldHEN plugin skeleton for Beat Saber
- [ ] **3.2** Find Beat Saber function addresses (requires PS4 debugging)
- [ ] **3.3** Implement level loading hook
- [ ] **3.4** Implement file redirection (like RB4DX)

### Phase 4: Integration & Testing

- [ ] **4.1** Build test PKG with plugin + custom song
- [ ] **4.2** Test on PS4
- [ ] **4.3** Iterate and fix issues
- [ ] **4.4** Document final workflow

## Immediate Next Steps

### Priority 1: Extract Level Structure with UABEA
1. Download UABEA from https://github.com/nesrak1/UABEA/releases
2. Open `BeatmapLevelsData/beatsaber/` AssetBundle
3. Analyze MonoBehaviour structure
4. Understand what data needs to be converted

### Priority 2: Find Level Catalog
1. Search `globalgamemanagers.assets` for level list
2. Look for `BeatmapLevelPack` or similar classes
3. Find where songs are enumerated for the menu

### Priority 3: Test Simple File Addition
1. Try adding a new folder to `BeatmapLevelsData/` in our PKG
2. See if Beat Saber recognizes it (unlikely without catalog change)
3. This will confirm if we need a plugin

## Dependencies Needed

- **UABEA**: For extracting/analyzing Beat Saber AssetBundles
- **OpenOrbis SDK**: For building GoldHEN plugin
- **Unity 2022.3**: For building custom AssetBundles

## References

- RB4DX Plugin Source: https://github.com/LlysiX/RB4DX-Plugin
- RB4DX Full Source: https://github.com/hmxmilohax/Rock-Band-4-Deluxe
- Backporter Converter: https://github.com/Backporter/PS4-Beat-Saber-Converter
- UABEA (Asset Editor): https://github.com/nesrak1/UABEA
- GoldHEN Plugin SDK: https://github.com/GoldHEN/GoldHEN_Plugin_SDK

## Notes

- RB4DX works by hooking `NewFile()` function and redirecting file reads
- Beat Saber uses Unity Addressables, making simple file redirect insufficient
- We likely need to hook `AssetBundle.LoadFromFile` or `Resources.Load`
- Beat Saber plugin development requires finding PS4 function addresses (hard part)