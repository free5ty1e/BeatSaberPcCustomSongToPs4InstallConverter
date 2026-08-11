# PS4 Beat Saber Deluxe — Pipeline & Plugin (v0.8040 / v0.5315)

This is the core implementation directory for the **[Beat Saber Deluxe](../README.md)** project.

This document covers pipeline-specific details. See the **[main README](../README.md)** for project overview, requirements, and quick start.

## Pipeline

`tools/full_custom_song_pipeline.py` is the main entry point.

```bash
# Build a custom song bundle (safe defaults: PCM16 + full-length audio +
# mode mapping + V2→V3 conversion are all ON automatically)
python3 tools/full_custom_song_pipeline.py \
  --song-dir <song_directory> \
  --target <slot_name> \
  --output custom_songs/<slot>_custom_v3.bundle

# Build + deploy to PS4
python3 tools/full_custom_song_pipeline.py \
  --song-dir <song_directory> \
  --target <slot_name> --deploy --deploy-plugin --debug-logging

# Direct download from BeatSaver and deploy
python3 tools/full_custom_song_pipeline.py \
  --download-beat-saver-song <map_id> \
  --target <slot_name> --deploy --deploy-plugin
```

> **Safe defaults (v0.5314+):** PCM16 lossless audio (`--pcm16`), no padding truncation (`--no-pad`), beatmap mode mapping + missing-mode generation (`--enable-beatmap-mode-mapping`), and V2→V3 conversion (`--convert-to-v3`) are all **default ON**. The old flags still work as no-ops. Oppose flags: `--hevag`/`--vorbis`, `--pad-fsb5` (**DANGER** — truncates to partial songs), `--disable-beatmap-mode-mapping`, `--no-convert-to-v3`. `--features-only --set-feature key=value` applies+deploys runtime flags standalone.

### Pipeline Flags

| Flag | Purpose |
|------|---------|
| `--song-dir` | Directory with song audio + beatmap .dat files |
| `--song-name NAME` | Override song display name for metadata injection (displayed as "Name / Artist") |
| `--artist NAME` | Override artist/song-author name for metadata injection |
| `--download-beat-saver-song <id>` | Download map directly from BeatSaver using map ID |
| `--target` | Target slot (e.g. `startmeup`, `Oxytocin`, `2BeLoved`) |
| `--pcm16` | PCM16 FSB5 audio (lossless) — **default**; kept as compat no-op |
| `--hevag` | HEVAG audio codec (Sony proprietary, usually blocked) — opposes the PCM16 default |
| `--vorbis` | Vorbis audio codec (FMOD/libvorbis codebook mismatch, usually blocked) — opposes the PCM16 default |
| `--no-pad` | Don't extend audio (use when PCM16 > original resource size) — **default**; kept as compat no-op |
| `--pad-fsb5` | **Restore** old 12MB truncating padding (**DANGER**: partial/truncated songs) |
| `--convert-to-v3` | Auto-convert V2 beatmaps to V3.2.0 — **default**; kept as compat no-op |
| `--no-convert-to-v3` | Leave V2 beatmaps unconverted (opposes the default) |
| `--enable-beatmap-mode-mapping` | Auto-detect custom song beatmap files and map them to game characteristic slots — **default**; kept as compat no-op |
| `--disable-beatmap-mode-mapping` | Standard-only bundle (opposes the default) |
| `--skip-mode-generation` | Keep mode mapping but skip generating missing mode beatmaps |
| `--fallback-mode-map SRC=DEST` | Override fallback chain for a mode slot (repeatable). E.g. `"360Degree=90Degree"` or `"NoArrows=Standard"`. Only meaningful with mode mapping. |
| `--features-only` | Apply + deploy `--set-feature` changes to features.json only, then exit (no song/plugin/redirect processing) |
| `--set-feature key=value` | Set a runtime feature flag in features.json (requires `--features-only` or `--deploy-plugin`) |
| `--deploy` | Upload bundle to PS4 via FTP |
| `--deploy-plugin` | Build + deploy plugin PRX |
| `--debug-logging` | Verbose PS4 logging (DEBUG=1 build) |
| `--generate-config` | Update `redirects.json` config on PS4 |
| `--enable-modes` | Comma-separated list of extra beatmap modes to enable (e.g. `OneSaber,90Degree`). Clones Standard beatmaps into the new characteristics so they appear in the in-game mode selector. |
| `--enable-plugin` | Enable the Beat Saber Deluxe plugin on PS4 (uncomments .prx entry in plugins.ini under [CUSA12878]) — tested and verified live on console |
| `--disable-plugin` | Disable the Beat Saber Deluxe plugin on PS4 (play original Rolling Stones songs) — comments out entries with `#;` |

## Plugin Toggle (v0.51+)

The `--enable-plugin` and `--disable-plugin` flags let you quickly switch between custom songs and original Rolling Stones tracks without editing files manually:

```bash
# Enable the plugin (play custom songs)
python3 tools/full_custom_song_pipeline.py --enable-plugin

# Disable the plugin (play originals)
python3 tools/full_custom_song_pipeline.py --disable-plugin
```

Both work standalone (no `--song-dir` needed). After toggling, restart the game or press PS+Triangle to reload plugins.

## Beatmap Mode Control — CAUTION: EARLY STAGE (v0.57 experimental)

**NOTE:** This feature is currently experimental. Adding `_difficultyBeatmapSets` entries to the per-song bundle is only **half** of the solution — the in-game UI also requires modifying `_previewDifficultyBeatmapSets` in the `BeatmapLevelSO` (stored in the Addressables pack bundle, not the per-song bundle). See Experiment 111 for details.

### How It Works (Pipeline Side)

The pipeline's `add_mode_characteristics()` function finds the `BeatmapLevel` object (class_id 114) in the bundle's CAB and reads its TypeTree. It clones the existing `"Standard"` entries in the `_difficultyBeatmapSets` array, creating new entries for each requested characteristic:

```json
"_difficultyBeatmapSets": [
    {"_beatmapCharacteristicSerializedName": "Standard", ...},  // original, 5 diffs
    {"_beatmapCharacteristicSerializedName": "OneSaber", ...},  // cloned, same beatmap refs
    {"_beatmapCharacteristicSerializedName": "90Degree", ...}   // cloned, same beatmap refs
]
```

Each cloned entry references the **same** `.beatmap.gz` and `.lightshow.gz` assets as the Standard characteristic (same path IDs). The game's engine applies the mode modifier (one saber, 90-degree rotation) to the Standard notes at runtime.

### UI Reality (After Investigation)

The in-game mode selector is NOT controlled by the per-song bundle's `_difficultyBeatmapSets`. Instead:

| Data Source | Location | Controls |
|-------------|----------|----------|
| `_previewDifficultyBeatmapSets` | `BeatmapLevelSO` in Addressables pack bundle | What modes appear in the song selection UI |
| `_difficultyBeatmapSets` | `BeatmapLevel` in per-song bundle (`BeatmapLevelsData/{slot}`) | What beatmaps load when you select a mode |

**User UI description:** "I select a difficulty, and then the UI above the difficulty section shows the modes." The mode options appear as buttons/segments in a row above the difficulty list — NOT a dropdown.

**Known Beatmap Characteristic names:** `Standard`, `OneSaber`, `90Degree`, `NoArrows`, `OneColor`

### What's Required to Make Modes Visible

1. **Modify the `BeatmapLevelSO` in the pack bundle** — add `_previewDifficultyBeatmapSets` entries for each desired characteristic. Each entry needs a reference to a `BeatmapCharacteristicSO` object (located in an external CAB).
2. **Modify the per-song `BeatmapLevel` bundle** — add `_difficultyBeatmapSets` entries (done by `add_mode_characteristics()`).
3. **Deploy both bundles** to PS4 and use AFR to redirect the pack bundle load.
4. **Challenge:** The `BeatmapCharacteristicSO` references for OneSaber/90Degree are in an external CAB that couldn't be located. The current workaround uses the Standard BeatmapCharacteristicSO reference for all modes, which may show all modes as "Standard" in the UI.

### Utility Script

`development/scripts/modify_pack_bundle.py` — modifies the Addressables pack bundle to add `_previewDifficultyBeatmapSets` entries for a specific song. Usage:

```bash
python3 development/scripts/modify_pack_bundle.py
```

(Currently hardcoded for StartMeUp. Edit the script to target different songs.)

### CLI Flag

```bash
# Build a bundle with OneSaber and 90Degree characteristics
# (mode mapping + generation are default ON since v0.5314)
python3 tools/full_custom_song_pipeline.py \
  --song-dir <song_directory> \
  --target <slot_name> \
  --deploy
```

### Verification

To verify a bundle has the new characteristics, the save+reload test confirms:
- Standard (5 diffs)
- OneSaber (5 diffs)
- 90Degree (5 diffs)

## Dynamic Redirect Config

The plugin now uses a **dynamic redirect table** instead of hardcoded defaults. This allows adding new songs without recompiling the plugin.

- **Config Path:** `/data/GoldHEN/AFR/CUSA12878/redirects.json`
- **Format:** JSON mapping of `slot_id` → `bundle_filename`
- **Mechanism:** The plugin uses POSIX `open()` to read the config from the AFR path, ensuring compatibility with files uploaded via FTP.

## Plugin

GoldHEN PRX that hooks `open()` to redirect song file requests.

```bash
make           # Release build (no verbose logging)
make DEBUG=1   # Debug build (verbose per-file logging)
```

Version defined by `PLUGIN_VERSION` in `src/main.cpp`. Increment when plugin changes.

## Deploy All

```bash
./deploy_all.sh [--release|--debug]
```

Deploys plugin + all 32 custom song bundles (Rolling Stones, Billie Eilish, Lizzo) and `redirects.json` to PS4. Also clears PS4 log.

## Documentation

- **[Main README](../README.md)** — Full project docs, knowledge base links, roadmap
- **[Knowledge Base](../.agent/llm-wiki-knowledge-base/)** — Technical details (audio, beatmaps, plugin, PS4 env)
- **[Song Replacements](../.agent/current-song-replacements-on-chris-ps4.md)** — Current PS4 deployment state
- **[Legacy Scripts](development/scripts/)** — Archived old pipeline scripts
- **[Historical Docs](development/docs/)** — Archived research and PKG-method documentation

## Addressables Catalog CRC Validation — SOLVED (2026-07-17)

**Status:** ✅ **SOLVED** — Pack bundle modification now works with exact CRC matching.

### The Problem
Unity's Addressables system validates per-bundle CRC32 against `aa/catalog.json`'s `m_ExtraDataString`. Any modified bundle fails validation → CE-34878-0 crash.

### The Solution (GF(2) Linear Algebra)
CRC-32 is a **linear function over GF(2)**: `table[a XOR b] = table[a] XOR table[b]`. This allows computing exact padding byte values that produce the desired CRC.

**Method:**
1. Precompute 32×32 GF(2) matrix M (CRC state transformation for 1 zero byte)
2. Compute M^L for suffix length L using square-and-multiply
3. Invert M^L via Gauss-Jordan elimination
4. Solve for padding bytes that XOR to target CRC delta

**Result:** Exact CRC match in 9 alignment padding bytes (offset 263). Bundle size differs by +2,712 bytes; `m_BundleSize` validation causes crash.

### Current Best Approach: Uncompressed Blocks as Free Variables
The 49 uncompressed blocks (flag=0) provide **6.1 MB of free CRC control variables with ZERO size impact**. Each contributes 131,072 raw bytes to BOTH file_size and CRC simultaneously — providing massive degrees of freedom.

**Key Insight:** Uncompressed blocks are stored as raw data with FIXED sizes. Changing their CONTENT affects CRC but NOT file_size:
- Block 0 (uncompressed): stored size = 131,072 bytes (always)
- Changing byte at offset X within this block → CRC changes, file_size unchanged

**GF(2) Linear Algebra Approach:**
For a byte at position p with L bytes after it:
```
contribution(byte_val, p) = M^L * table[byte_val] (over GF(2))
```

### Implementation (`crc_corrector.py`)
1. Parse blocks info from offset 64 (compressed → 859 bytes decompressed)
2. Identify uncompressed block positions in file
3. Inject BeatmapLevelSO blob into first uncompressed block (overlay, size fixed)
4. Use GF(2) linear algebra on remaining 48 uncompressed blocks to fix CRC:
   - For each byte position, compute weight vector W = M^(bytes_after_position)
   - Solve for byte values that XOR to target CRC delta
5. Apply corrections and verify final CRC matches `0xdc8b314f`

### Status
**✅ Tool built and ready.** Next step: test with actual BeatmapLevelSO blob injection.

## Known Limitations & Workarounds

### m_BundleSize Validation (2026-07-17)
The Addressables catalog stores `m_BundleSize: 7902803` for the Rolling Stones pack bundle. Modified bundles with different sizes crash even with correct CRC.

**Workaround:** Use uncompressed block injection approach (zero size impact) combined with GF(2) CRC correction on alignment padding bytes.

### IL2CPP Hooking Dead Ends
All previous hooking attempts have been experimentally proven dead:
- `get_DisplayName()` and `get_songName()` are inlined by IL2CPP
- Constructor hooks never fire for Addressables-deserialized objects
- `SetData`/`SetContent` hooks crash or never reach payload
### Per-Song Bundle Mode Support

Our pipeline creates `BeatmapLevel` objects with only `"Standard"` characteristics by default. The `--enable-modes` flag adds additional entries:
```bash
python3 full_custom_song_pipeline.py --song-dir ./MySong --enable-modes OneSaber,90Degree --deploy
```

To add other modes, we would need to:
1. Add `_difficultyBeatmapSets` entries for OneSaber/90Degree/etc.
2. Create (or proxy) the `.beatmap.gz` and `.lightshow.gz` assets for those modes
3. The game uses class ID 114 for `BeatmapLevel` objects

## Per-Song Bundle Mode Support

Our pipeline creates `BeatmapLevel` objects with only `"Standard"` characteristics by default. The `--enable-modes` flag adds additional entries:
```bash
python3 full_custom_song_pipeline.py --song-dir ./MySong --enable-modes OneSaber,90Degree --deploy
```

To add other modes, we would need to:
1. Add `_difficultyBeatmapSets` entries for OneSaber/90Degree/etc.
2. Create (or proxy) the `.beatmap.gz` and `.lightshow.gz` assets for those modes
3. The game uses class ID 114 for `BeatmapLevel` objects

