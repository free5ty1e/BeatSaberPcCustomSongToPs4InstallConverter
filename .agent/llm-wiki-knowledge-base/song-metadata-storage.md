# Song Metadata Storage in Beat Saber PS4 (CUSA12878)

## Overview
Song metadata (display names, artists, mapper names, environments) is stored separately from the per-song bundle data. There are two systems:

1. **Base Game Songs (22 songs)** — metadata in `resources.assets`
2. **DLC Songs (~284 songs)** — metadata in Addressables packs (`aa/PS4/`)

## resources.assets Structure
File: `Media/resources.assets`

Contains `MonoBehaviour` objects named `{SongID}BeatmapLevel`. These are serialized as `BeatmapLevelSO` ScriptableObjects with the following binary structure:

```
[4 bytes: uint32 length of object name]
[object name bytes, e.g. "BleedItOutBeatmapLevel"]
[6 bytes null padding]
[4 bytes: uint32 length of internal ID]
[internal ID, e.g. "BleedItOut"]
[2 bytes null padding]
[4 bytes: uint32 length of display name]
[display name, e.g. "Bleed It Out"]
[4 bytes null padding]
[4 bytes: uint32 length of artist name]
[artist name, e.g. "Linkin Park"]
[1+ bytes null padding]
[4 bytes: uint32 length of mapper/level author]
[mapper name, e.g. "Freeek (Narwall, Freeek, ETAN & altrewin Remaster)"]
[null padding + binary data (previewStartTime, audioDuration, etc.)]
[4 bytes: uint32 length of environment name #1]
[environment name, e.g. "LinkinPark2Environment"]
[null padding]
[4 bytes: uint32 length of environment name #2]
[environment name, e.g. "GlassDesertEnvironment"]
```

### Known Environment Names
- `DefaultEnvironment`
- `GlassDesertEnvironment`
- `BigMirrorEnvironment`
- `TriangleEnvironment`
- `RocketEnvironment`
- `MonstercatEnvironment`
- `DaftPunkEnvironment`
- `SkrillexEnvironment`
- `GreenDayGrenadeEnvironment`
- `LinkinPark2Environment`
- `TheWeekndEnvironment`
- `WeaveEnvironment`
- `BritneyEnvironment`

### 22 Base Songs
These are the Extras / base game songs:
- 100Bills, AlreadyOver, AmericanIdiot, Bangarang, BeatSaber, BleedItOut
- Boundless, Circus, DieForYou, Firestarter, Glide, HarderBetterFasterStronger
- Holiday, INeedYou, Lost, Overkill, PrayForMe, PrimeTimeOf...Live2007
- RaggaBomb, RockIt, RumNBass, SomewhereIBelong

## Per-Song Bundle Structure
File: `Media/StreamingAssets/BeatmapLevelsData/{song_id}/`

Unity AssetBundle containing:
- `{SongID}.audio.gz` — JSON metadata: `{"version":"4.0.0","songChecksum":"...","songSampleCount":8311155,"songFrequency":44100,"bpmData":[...],"lufsData":[...]}`
- `{SongID}{Difficulty}.beatmap.gz` — GZIP'd V4 beatmap JSON
- `{SongID}{Difficulty}.lightshow.gz` — GZIP'd V4 lightshow JSON
- `MonoBehaviour` — BeatmapLevelData object (class ID 114)
- `AudioClip` — Unity AudioClip with `m_Format`, `m_Channels`, `m_Frequency`, `m_Length`

### GZIP Asset Format
Each TextAsset in the bundle has a header:
```
[4 bytes: name length][name bytes][unknown 4 bytes][unknown 4 bytes][gzip data from offset 8]
```

### Beatmap V4 Format
Keys: `version`, `colorNotes`, `bombNotes`, `obstacles`, `sliders`, `burstSliders`, `basicEvents`, `waypoints`, `rotationEvents`

### AudioClip Metadata
- `m_Format`: Audio format codec
- `m_Channels`: 2 (stereo)
- `m_Frequency`: 44100 Hz
- `m_Length`: total sample count (audio duration = samples / frequency)

## Addressables Packs (DLC)
DLC songs are organized in `StreamingAssets/aa/PS4/` as bundles named `{pack_name}_pack_assets_all_{hash}.bundle`.

Known DLC packs from the Addressables catalog:
- `rock-mixtape` — e.g., The Pretender
- `linkin-park` — e.g., BleedItOut
- `queen` — e.g., We Are The Champions
- `skrillex` — e.g., Bangarang, Ragga Bomb
- `the-weeknd` — e.g., Die For You, Pray For Me
- `rocket-league` — Rocket League pack
- `timbaland` — Timbaland pack
- `panic` — Panic! At The Disco pack
- `electronic-mixtape`, `imagine-dragons`, `linkin-park2`, `britney-spears`, `green-day`, `monstercat`, `shockdrop`, `the-rolling-stones`

Each pack has a `BeatmapLevelPack` asset that defines the collection.

## Entry Points for Modification

### Method 1: Redirection (Current Approach)
GoldHEN AFR redirects bundle loads from the original path to the AFR path.

### Method 2: Modifying resources.assets
- Song names/artists in `resources.assets` can be edited to change display names
- Requires understanding the serialized MonoBehaviour format
- Can change: display name, artist, mapper name, environment

### Method 3: Adding Songs to Existing Albums
- The `BeatmapLevelPack` ScriptableObject in globalgamemanagers.assets defines album contents
- Adding a new song ID to a pack's level list would add it to the album
- This requires modifying the serialized data

### Method 4: Creating Custom Albums
- Define a new `BeatmapLevelPack` object with a unique pack ID
- Reference song bundles by their level IDs
- Requires registering the pack in the game's level collection

### Beatmap Characteristics
Defined in `BeatmapCharacteristicSO` objects:
- `Standard` — normal mode
- `OneSaber` — single saber mode
- `90Degree` — 90-degree mode
- `360Degree` — 360-degree mode
- `NoArrows` — no arrows mode
- `OneColor` — one color mode
- `LegacyStandard` — legacy mode

Adding a characteristic to a song requires modifying the `_difficultyBeatmapSets` in the song's bundle data.
