# PS4 Beat Saber Deluxe — Pipeline & Plugin (v0.8040 / v0.5328)

This is the core implementation directory for the **[Beat Saber Deluxe](../README.md)** project.

This document covers pipeline-specific details. See the **[main README](../README.md)** for project overview, requirements, and quick start.

## Pipeline

`tools/full_custom_song_pipeline.py` is the main entry point.

### Quick Start: Download from BeatSaver + Full Deploy (Recommended)

```bash
# Complete end-to-end deployment in ONE command:
# - Downloads song from BeatSaver
# - Converts to V3.2.0 (V2→V3 auto-conversion)
# - Generates all 4 modes (Standard, OneSaber, NoArrows, 90Degree)
# - Builds song bundle with PCM16 lossless audio
# - Builds/deploys pack mode bundles + merged catalog
# - Deploys song bundle, pack bundles, catalog, redirects.json
# - Runs post-deploy validation
python3 tools/full_custom_song_pipeline.py \
  --download-beat-saver-song <MAP_ID> \
  --target <slot_name> \
  --deploy-full
```

### Build Only (No Deploy)

```bash
# Build song bundle locally (safe defaults: PCM16 + full-length audio +
# mode mapping + V2→V3 conversion are all ON automatically)
python3 tools/full_custom_song_pipeline.py \
  --song-dir <song_directory> \
  --target <slot_name> \
  --output custom_songs/<slot>_custom_v3.bundle
```

### Build + Deploy Song Bundle Only (No Pack/Catalog)

```bash
# Build and deploy just the song bundle + update redirects.json
python3 tools/full_custom_song_pipeline.py \
  --song-dir <song_directory> \
  --target <slot_name> \
  --deploy --deploy-config
```

### Direct Download from BeatSaver + Deploy Song Only

```bash
# Download from BeatSaver and deploy song bundle + redirects.json
python3 tools/full_custom_song_pipeline.py \
  --download-beat-saver-song <map_id> \
  --target <slot_name> \
  --deploy --deploy-config
```

### Build & Deploy Plugin (With Debug Logging)

```bash
# Build plugin with verbose PS4 logging for development
python3 tools/full_custom_song_pipeline.py \
  --deploy-plugin --debug-logging
```

## Pipeline Flags

> **Safe defaults (v0.5314+):** PCM16 lossless audio (`--pcm16`), no padding truncation (`--no-pad`), beatmap mode mapping + missing-mode generation (`--enable-beatmap-mode-mapping`), and V2→V3 conversion (`--convert-to-v3`) are all **default ON**. The old flags still work as no-ops. Oppose flags: `--hevag`/`--vorbis`, `--pad-fsb5` (**DANGER** — truncates to partial songs), `--disable-beatmap-mode-mapping`, `--no-convert-to-v3`. `--features-only --set-feature key=value` applies+deploys runtime flags standalone.

| Flag | Purpose |
|------|---------|
| `--song-dir` | Directory with song audio + beatmap .dat files |
| `--song-name NAME` | Override song display name for metadata injection (displayed as "Name / Artist") |
| `--artist NAME` | Override artist/song-author name for metadata injection |
| `--download-beat-saver-song <id>` | Download map directly from BeatSaver using map ID (primary workflow) |
| `--target` | Target slot (e.g. `startmeup`, `Oxytocin`, `2BeLoved`) |
| `--deploy-full` | **Complete orchestration**: song bundle + pack mode bundles + merged catalog + redirects.json + validation (primary workflow) |
| `--deploy` | Upload bundle to PS4 via FTP |
| `--deploy-config` | Deploy local `redirects.json` to PS4 |
| `--generate-config` | Update `redirects.json` config with current target |
| `--deploy-pack-modes` | Build-if-missing + deploy pack mode bundles + merged catalog |
| `--verify-ps4` | Run post-deploy PS4 validation (redirects match, targets exist, pack+catalog pair) |
| `--no-verify-ps4` | Skip automatic post-deploy validation |
| `--deploy-plugin` | Build + deploy plugin PRX |
| `--debug-logging` | Verbose PS4 logging (DEBUG=1 build) |
| `--generate-config` | Update `redirects.json` config on PS4 |
| `--sync-config` | Download config from PS4, merge, save, redeploy |
| `--enforce-config` | Use local `redirects.json` as truth and deploy to PS4 |
| `--pcm16` | PCM16 FSB5 audio (lossless) — **default**; kept as compat no-op |
| `--hevag` | HEVAG audio codec (Sony proprietary, usually blocked) — opposes PCM16 default |
| `--vorbis` | Vorbis audio codec (FMOD/libvorbis codebook mismatch, usually blocked) — opposes PCM16 default |
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
| `--enable-modes` | Comma-separated list of extra beatmap modes to enable (e.g. `OneSaber,90Degree`). Clones Standard beatmaps into new characteristics. |
| `--enable-plugin` | Enable the Beat Saber Deluxe plugin on PS4 (uncomments .prx entry in plugins.ini) — tested and verified live on console |
| `--disable-plugin` | Disable the Beat Saber Deluxe plugin on PS4 (play original songs) — comments out entries with `#;` |
| `--target-ip` | PS4 IP address for FTP deployment (overrides config) |

## Plugin Toggle (v0.51+)

The `--enable-plugin` and `--disable-plugin` flags let you quickly switch between custom songs and original DLC tracks without editing files manually:

```bash
# Enable the plugin (play custom songs)
python3 tools/full_custom_song_pipeline.py --enable-plugin

# Disable the plugin (play originals)
python3 tools/full_custom_song_pipeline.py --disable-plugin
```

Both work standalone (no `--song-dir` needed). After toggling, restart the game or press PS+Triangle to reload plugins.

## Beatmap Mode Mapping — STABLE (v0.5314+ Default)

The pipeline now includes full beatmap mode mapping as a **default feature** (not experimental). It auto-detects custom song beatmap files and maps them to game characteristic slots (Standard, OneSaber, NoArrows, 90Degree) using a fallback chain, and generates missing mode beatmaps from Standard.

### How It Works

The pipeline's mode mapping system:
1. **Detects** existing mode-specific beatmap files in the song directory (Standard, OneSaber, 90Degree, NoArrows)
2. **Generates** missing mode beatmaps from the Standard source using procedural generators:
   - **OneSaber**: Recolors all notes to single color (blue/right saber), drops simultaneous notes, respects minimum gap
   - **NoArrows**: Converts all arrow notes to dots (direction=8), preserves bombs/walls/sliders
   - **90Degree**: Alternating ±90° rotation events every N beats (default 8.0 = 2 measures)
3. **Injects** generated beatmaps as TextAsset objects into the bundle
4. **Adds** `_difficultyBeatmapSets` entries for each enabled mode (Standard, OneSaber, NoArrows, 90Degree)

### In-Game Mode Selector

The in-game mode selector is driven by **pack-level BeatmapLevelSO preview sets**, not per-song bundles. The pipeline's generalized pack patch (`tools/build_pack_mode_bundles.py`) patches ALL 36 DLC packs to expose 4 modes × 5 difficulties in their `_previewDifficultyBeatmapSets`. The in-game mode selector shows Standard / OneSaber / NoArrows / 90Degree on Hard+ difficulties.

This is handled automatically by `--deploy-full` / `--deploy-pack-modes`.

### CLI Flags for Mode Mapping

```bash
# Full pipeline with mode mapping (default ON since v0.5314)
python3 tools/full_custom_song_pipeline.py \
  --song-dir <song_directory> \
  --target <slot_name> \
  --deploy-full

# Skip generating missing mode beatmaps (still enables mode sets in bundle)
python3 tools/full_custom_song_pipeline.py \
  --song-dir <song_directory> \
  --target <slot_name> \
  --skip-mode-generation \
  --deploy-full

# Custom OneSaber minimum gap (beats between same-cell arrowed notes)
python3 tools/full_custom_song_pipeline.py \
  --song-dir <song_directory> \
  --target <slot_name> \
  --one-saber-min-gap 0.25 \
  --deploy-full

# Custom 90Degree rotation cycle (beats per flip)
python3 tools/full_custom_song_pipeline.py \
  --song-dir <song_directory> \
  --target <slot_name> \
  --rotation-cycle-beats 8.0 \
  --deploy-full

# Override fallback chain (e.g., chain 90Degree→Standard directly)
python3 tools/full_custom_song_pipeline.py \
  --song-dir <song_directory> \
  --target <slot_name> \
  --fallback-mode-map 90Degree=Standard \
  --deploy-full

# Disable mode mapping entirely (Standard-only bundle)
python3 tools/full_custom_song_pipeline.py \
  --song-dir <song_directory> \
  --target <slot_name> \
  --disable-beatmap-mode-mapping \
  --deploy-full
```

## Dynamic Redirect Config

The plugin uses a **dynamic redirect table** instead of hardcoded defaults. This allows adding new songs without recompiling the plugin.

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

## Generalized Pack Mode Patch (Production Ready)

All 36 DLC packs can now be patched to expose 4 preview modes (Standard/OneSaber/NoArrows/90Degree) via a production pipeline module:

```bash
# Build all 36 pack mode bundles + merged catalog
python3 tools/build_pack_mode_bundles.py --write \
  --dump-dir /workspace/ps4_dump/CUSA12878-patch

# Deploy pack mode bundles + catalog + redirects (production)
python3 tools/full_custom_song_pipeline.py \
  --deploy-pack-modes --deploy-config --verify-ps4
```

This is automatically handled by `--deploy-full` when `pack_modes.packs` is configured in the PS4 config.

## Deploy All (Automated)

```bash
# Complete fleet deployment: 38 custom songs + 4 pack mode bundles + catalog + redirects
python3 development/scripts/build_deploy_all38.py
```

## Documentation

- **[Main README](../README.md)** — Full project docs, knowledge base links, roadmap
- **[Knowledge Base](../.agent/llm-wiki-knowledge-base/)** — Technical details (audio, beatmaps, plugin, PS4 env)
- **[Song Replacements](../.agent/current-song-replacements-on-chris-ps4.md)** — Current PS4 deployment state with BeatSaver MAP_IDs
- **[Legacy Scripts](development/scripts/)** — Archived old pipeline scripts
- **[Historical Docs](development/docs/)** — Archived research and PKG-method documentation

## Addressables Catalog CRC Validation — SOLVED

**Status:** ✅ **SOLVED** — Pack bundle modification works with exact CRC matching via GF(2) linear algebra on uncompressed blocks.

## Known Limitations & Workarounds

### m_BundleSize Validation
The Addressables catalog stores per-bundle sizes. Modified bundles with different sizes crash even with correct CRC.

**Workaround:** Use uncompressed block injection approach (zero size impact) combined with GF(2) CRC correction.

### IL2CPP Hooking Dead Ends
All previous hooking attempts have been experimentally proven dead:
- `get_DisplayName()` and `get_songName()` are inlined by IL2CPP
- Constructor hooks never fire for Addressables-deserialized objects
- `SetData`/`SetContent` hooks crash or never reach payload

## Testing

```bash
# Run full test suite (571 tests)
python3 -m pytest tests/ -v
```