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

## Addressables Catalog CRC Validation — BLOCKER for Pack Bundle Modification

**Experiment 136 (2026-07-15) discovered that the Addressables catalog validates per-bundle integrity using CRC32 checksums, file sizes, and MD5 hashes.**

The catalog (`aa/catalog.json`) is NOT loaded via `AssetBundle.LoadFromFile` — it's loaded as a plain JSON file by Unity's `ContentCatalogProvider`. This means the AFR plugin (which only hooks `LoadFromFile`) **cannot redirect or patch it**.

**Exp 142 (2026-07-16):** Achieved exact CRC match via GF(2) linear algebra — but file_size mismatch (+2,712 bytes vs original 7,902,803) still crashes due to `m_BundleSize` validation.

**Exp 157 (2026-07-17):** Critical finding that uncompressed blocks are part of a shared decompressed stream, NOT independent storage. Modifying their content changes file_size by ~817-2,177 bytes due to cascading compression ratio effects. **Option B (uncompressed block injection) is BLOCKED.**

### Catalog Storage Format (m_ExtraDataString)

The catalog's `m_ExtraDataString` field (116,334 bytes) contains **concatenated UTF-16 LE encoded JSON blocks**, one per bundle. Example for the Rolling Stones pack:

```json
{"m_Hash":"a99482a8a3da9e991e5ae36f2fea209c","m_Crc":3700109647,
 "m_BundleSize":7902803,"m_UseCrcForCachedBundles":true,
 "m_BundleName":"51dc790300eb3d900786837beb3ac335",
 "m_UseUWRForLocalBundles":false,"m_ClearOtherCachedVersionsWhenLoaded":false}
```

Key fields:
- `m_Hash` — MD5 of the bundle file (also used as part of the filename)
- `m_Crc` — CRC32 of the bundle file (validated at load time when `m_UseCrcForCachedBundles=true`)
- `m_BundleSize` — Expected file size of the bundle
- `m_UseCrcForCachedBundles` — When `true`, the game validates CRC on load

### Impact

- **Any modification** to a bundle file changes its CRC and file size → game detects mismatch → CE-34878-0 crash
- The ORIGINAL bundle works via redirect because its CRC/size still match the catalog values
- The catalog cannot be redirected (not loaded via AssetBundle.LoadFromFile)
- Only options: (a) match original CRC AND size simultaneously, or (b) bypass pack bundle entirely via memory injection

## Memory Injection Approach — Viable Fallback (Exp 158)

If pack bundle modification fails entirely (which appears likely given current blockers), fallback to **memory injection**:

**Concept:** Patch BeatmapLevelSO in RAM after Addressables loads the pack bundle but BEFORE validation runs. This bypasses catalog CRC validation entirely.

**Feasibility Check Needed:**
1. When does Addressables validate CRC? (during LoadFromFile or after?)
2. Can we hook into the deserialization process on PS4?
3. Where is BeatmapLevelSO stored in memory after deserialization?

**Exp 142 showed game continued loading other bundles after pack bundle loaded**, suggesting there may be a window for interception.

**Hook Points to Investigate:**
- `SerializedFile.ReadObject` — Unity's serialization layer
- `MonoScriptableObject.InstantiateFromData` — ScriptableObject instantiation
- `AssetBundle.LoadFromFile` — Bundle loading (already hooked by AFR plugin)
- Addressables' internal deserialization methods

## Hooking Strategy — ALL IL2CPP Approaches DEAD

Previous hooking attempts have ALL failed experimentally:

| Approach | Experiment | Result |
|----------|-----------|--------|
| `get_DisplayName()` hook | Multiple | Inlined by IL2CPP — hook never fires |
| `get_songName()` hook | Multiple | Inlined by IL2CPP — hook never fires |
| Constructor hook | Exp 123-131 | Never fires for Addressables-deserialized objects |
| `SetData` hook | Exp 131 | Conditional in code — never reaches our payload |
| `SetContent` hook | Exp 131 | Crashes the game |

## Current Strategy — Per-Song Bundle Modifications (Bypassing Pack Bundle)

Since pack bundle modification is blocked by CRC validation, and IL2CPP hooks are proven dead, the current approach is to modify **per-song bundles** instead:

1. **Mode Selector** (Exp 138): Build per-song bundles with `--enable-modes OneSaber,90Degree,...` to add extra characteristic modes. These bundles are loaded per-song, not at startup, and their redirects work independently of the pack bundle.
2. **Song Name Display**: The BeatmapLevelSO with display info is in the pack bundle, not in per-song bundles. Changing display names requires pack bundle modification, which is currently blocked.
3. The pipeline's `add_mode_characteristics()` in `full_custom_song_pipeline.py` adds mode entries to per-song bundles.

## Per-Song Bundle Mode Support

Our pipeline creates `BeatmapLevel` objects with only `"Standard"` characteristics by default. The `--enable-modes` flag adds additional entries:
```bash
python3 full_custom_song_pipeline.py --song-dir ./MySong --enable-modes OneSaber,90Degree --deploy
```

To add other modes, we would need to:
1. Add `_difficultyBeatmapSets` entries for OneSaber/90Degree/etc.
2. Create (or proxy) the `.beatmap.gz` and `.lightshow.gz` assets for those modes
3. The game uses class ID 114 for `BeatmapLevel` objects
