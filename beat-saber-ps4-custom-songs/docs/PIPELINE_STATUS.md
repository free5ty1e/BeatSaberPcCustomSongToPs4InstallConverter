# Beat Saber PS4 Custom Songs - Pipeline Status

## End-to-End Pipeline Overview

```mermaid
flowchart TD
    subgraph DOWNLOAD["1. Download from BeatSaver"]
        A1[BeatSaver Download] --> A2[BeatSaver ZIP Archive]
    end

    subgraph EXTRACT["2. Extract Archive"]
        A2 --> B1[Extract ZIP]
        B1 --> B2[BeatSaver Song Folder]
        B2 --> B3{Valid Song Structure?}
        B3 -->|Yes| B4[Info.dat / song.dat]
        B3 -->|No| B5[ERROR: Invalid Format]
    end

    subgraph PARSE["3. Parse Song Data"]
        B4 --> C1[Extract Metadata]
        C1 --> C2[Song Name, Artist, BPM]
        C1 --> C3[Difficulty Files]
        C1 --> C4[Audio File]
        C2 --> C5[Validated Song Data]
    end

    subgraph CONVERT["4. Convert Audio to FSB5"]
        C4 --> D1{Audio Format}
        D1 -->|OGG| D2[FSB5 Converter Tool]
        D1 -->|WAV| D2
        D1 -->|MP3| D3[Convert to OGG first]
        D3 --> D2
        D2 --> D4[FSB5 .resource file]
    end

    subgraph BUILD["5. Build Level AssetBundle"]
        D4 --> E1[Create BeatSaberBeatmapLevelData]
        E1 --> E2[Bundle Audio + Metadata]
        E2 --> E3[Beat Saber Level AssetBundle]
    end

    subgraph PKG["6. Create PS4 PKG"]
        E3 --> F1[Copy to BeatmapLevelsData]
        F1 --> F2[Generate Project.gp4]
        F2 --> F3[Build PKG with PkgToolBox]
        F3 --> F4[BeatSaber Custom PKG]
    end

    subgraph INSTALL["7. Install on PS4"]
        F4 --> G1[Transfer to USB/FTP]
        G1 --> G2[Install via Debug Settings]
        G2 --> G3[Launch Beat Saber]
        G3 --> G4[✓ Custom Song Available!]
    end

    style DOWNLOAD fill:#90EE90
    style EXTRACT fill:#90EE90
    style PARSE fill:#90EE90
    style CONVERT fill:#FFB347
    style BUILD fill:#FFB347
    style PKG fill:#FFB347
    style INSTALL fill:#FFB347
```

## Step Status Legend

```mermaid
pie title Pipeline Progress
    "✓ Completed" : 3
    "🔄 In Progress" : 1
    "⏳ Pending" : 3
```

## Detailed Step Status

| Step | Status | Description | Evidence |
|------|--------|-------------|----------|
| **1. Download from BeatSaver** | ✅ Done | BeatSaver ZIP format confirmed | `songs_repo/` contains 20+ songs |
| **2. Extract Archive** | ✅ Done | ZIP extraction works | `python zipfile` handles correctly |
| **3. Parse Song Data** | ⚠️ Partial | Info.dat parsing works, need beatmap converter | `beatsaber_asset_tool.py` has template |
| **4. Convert Audio to FSB5** | ⚠️ Unity | **Unity 2022.3 project created!** | `unity_project/` ready to test |
| **5. Build Level AssetBundle** | ⚠️ Unity | Unity project can build AssetBundles | Script ready, needs testing |
| **6. Create PS4 PKG** | ⚠️ Partial | PKG building works | `PkgToolBox` tested, working |
| **7. Install on PS4** | ⏳ Pending | Need full pipeline test | GoldHEN + debug settings ready |

## Key Discoveries

### Audio Format: FSB5
- Beat Saber PS4 uses **FSB5** (FMOD Sound Bank 5) for audio
- NOT raw OGG - audio is wrapped in FSB5 container
- UABEA can **export** audio as OGG, but import needs FSB5 format
- .resource file size: 7,269,312 bytes (including 900 byte FSB5 header)

### AssetBundle Structure
- Each level is a single AssetBundle file (e.g., `beatsaber`)
- Contains: `BeatSaberBeatmapLevelData` + `AudioClip` + other assets
- AudioClip points to external .resource file via `archive:/CAB-.../resource` path
- Levels auto-load from `BeatmapLevelsData/` directory

### PKG Building
- `PkgToolBox` successfully creates valid PKGs
- Previous build: 94 songs, 1.1 GB (working!)
- PKG installs via GoldHEN debug settings

## Current Blocker

### Audio Replacement
**Problem:** UABEA cannot import external audio directly

**Options:**
1. Build FSB5 encoder (complex - requires FMOD SDK)
2. Use Unity 2022.3 to rebuild AssetBundles (requires Unity install)
3. Direct hex replacement if sizes match (risky)

**Recommendation:** Test Unity + UABEA workflow for AssetBundle creation

## Immediate Next Steps

```mermaid
sequenceDiagram
    participant User
    participant UABEA
    participant Unity
    participant PkgToolBox
    participant PS4

    User->>UABEA: Open existing level
    UABEA-->>User: Export audio as OGG
    User->>Unity: Create new scene with audio
    Unity-->>Unity: Build AssetBundle
    User->>UABEA: Open new AssetBundle
    UABEA-->>User: Verify structure matches
    User->>PkgToolBox: Create PKG
    PkgToolBox-->>PS4: Install PKG
    PS4-->>User: Test in game
```

## File Inventory

| File | Purpose | Status |
|------|---------|--------|
| `song_replacer.py` | Song metadata templates | ✅ Working |
| `beatsaber_asset_tool.py` | AssetBundle analysis | ✅ Working |
| `docs/FSB5_FORMAT_DISCOVERY.md` | Audio format documentation | ✅ Done |
| `docs/SIMPLIFIED_APPROACH.md` | No-plugin approach | ✅ Done |
| `docs/MANUAL_UNITY_WORKFLOW.md` | UABEA/Unity guide | ✅ Updated |
| `docs/PIPELINE_STATUS.md` | This document | ✅ Current |

## Questions to Answer

1. Can Unity 2022.3 create Beat Saber-compatible AssetBundles?
2. Does UABEA import work for .resource files with FSB5?
3. Can we test PKG build with existing (unmodified) levels first?

## Success Criteria

- [ ] Replace audio in one level (beatsaber → test song)
- [ ] Build PKG with modified level
- [ ] Install and verify on PS4
- [ ] Audio plays correctly in game
- [ ] Expand to batch processing