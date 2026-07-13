---
name: song-metadata-addressables-structure
description: "How song metadata (names, artists, characteristic modes) is stored in the game's Addressables system and how to intercept/interact with it"
metadata:
  type: reference
---

# Song Metadata & Addressables Structure

## Overview
The game stores song metadata (display names, artists, mappers, environments, characteristic modes) in two separate systems:

1. **Base Game Songs (22 songs)** — metadata in `Media/resources.assets`
2. **DLC Songs** — metadata in Addressables packs (`Media/StreamingAssets/aa/PS4/*.bundle`)

The metadata is NOT in the per-song bundles (`BeatmapLevelsData/{song_id}`). Those bundles only contain `BeatmapLevel` objects with:
- Audio clip references
- Audio data (`audio.gz`)
- Difficulty beatmap sets (characteristic + difficulty level → beatmap .gz assets)

## Object Hierarchy

```
BeatmapLevelPackSO (ScriptableObject)
├── BeatmapLevelSO (ScriptableObject) — contains displayName, artistName, mapper, etc.
│   ├── BeatmapLevel (MonoBehaviour) — contains audio/beatmap references
│   │   ├── _audioClip (AudioClip reference)
│   │   ├── _audioDataAsset (TextAsset reference — audio.gz)
│   │   └── _difficultyBeatmapSets
│   │       └── [Set] — controls which "characteristics" are available
│   │           ├── _beatmapCharacteristicSerializedName: "Standard" | "OneSaber" | "90Degree" | etc.
│   │           └── _difficultyBeatmaps [{_difficulty, _beatmapAsset, _lightshowAsset}]
│   └── (metadata fields like _displayName, _artistName)
├── BeatmapLevelCollectionSO (ScriptableObject) — groups levels into packs
└── BeatmapLevelsPromoDataSO
```

## Key IL2CPP Method Names (from global-metadata.dat)

Methods used to access song metadata at runtime:

| Method | Likely Purpose |
|--------|---------------|
| `get_DisplayName` | Returns the song's display name string |
| `get_songName` | Returns the song identifier or name |
| `get_selectedBeatmapLevel` | Gets the currently selected BeatmapLevel object |
| `LoadBeatmapLevelDataAsync` | Asynchronously loads level data |
| `_selectedBeatmapLevel` | Private backing field for selected level |
| `HandleDidSelectAnnotatedBeatmapLevelCollection` | Called when user selects a song from UI |

## Addressables Bundle Structure

The Addressables catalog (`aa/catalog.json`) maps internal asset paths to `.bundle` files:
```
m_InternalIds contains paths like:
  "Packages/com.beatgames.beatsaber.packs.linkin-park/SO/BleedItOut/BleedItOutBeatmapLevel.asset"
  
m_ClassName values:
  "BeatmapLevelSO" — the ScriptableObject with metadata
  "BeatmapLevelPackSO" — a pack containing multiple levels
```

The bundles are named by hash (e.g., `0f6ffd5..._monoscripts_0033b...bundle`) in `aa/PS4/`.

## Beatmap Characteristic Modes (from BeatmapLevel TypeTree)

The `_difficultyBeatmapSets` array in `BeatmapLevel` controls which characteristics (modes) are available:

```json
"_difficultyBeatmapSets": [
    {
        "_beatmapCharacteristicSerializedName": "Standard",
        "_difficultyBeatmaps": [...]
    }
]
```

Known characteristic serialization names:
- `"Standard"` — Normal mode
- `"OneSaber"` — One saber mode
- `"90Degree"` — 90-degree mode (360-degree mapping)
- `"NoArrows"` — No arrows mode
- `"OneColor"` — Single color mode

Each characteristic has its own set of difficulty beatmaps. If a characteristic is NOT in this array, the player cannot select it from the UI.

The game does NOT dynamically generate a Standard → OneSaber mapping. Each mode requires its own set of mapped notes in a `.beatmap.gz` asset.

## Hooking Strategy

To change song list metadata at runtime, hook options:
1. `get_DisplayName()` — return custom strings for redirected songs
2. `get_songName()` — return custom song identifiers
3. Hook the Addressables bundle load for `BeatmapLevelSO` assets

## Current Custom Bundles

Our pipeline creates `BeatmapLevel` objects with only `"Standard"` characteristics. To add other modes, we would need to:
1. Add `_difficultyBeatmapSets` entries for OneSaber/90Degree/etc.
2. Create (or proxy) the `.beatmap.gz` and `.lightshow.gz` assets for those modes
3. The game uses class ID 114 for `BeatmapLevel` objects
