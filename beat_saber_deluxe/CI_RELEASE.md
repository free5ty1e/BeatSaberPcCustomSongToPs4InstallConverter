<!-- START_PROTECTED -->

# CI/CD Release Instructions

This document describes the CI/CD pipeline for Beat Saber Deluxe and serves as the release body reference. The release workflow is defined in `.github/workflows/plugin-build.yml`.

## Artifacts Per Release

### 📦 Plugin

| File                          | Description                                                        |
| ----------------------------- | ------------------------------------------------------------------ |
| `beat_saber_deluxe.prx`       | Release build — no verbose logging, minimal file size              |
| `beat_saber_deluxe_debug.prx` | Debug build — verbose ps4 logging (`bs_log.txt`), larger file size |
| `plugins.ini`                 | GoldHEN configuration for CUSA12878                                |
| `redirects.json`              | Song redirect config                                               |

### 🎵 Song Conversion Pipeline

| File                                 | Description                                      |
| ------------------------------------ | ------------------------------------------------ |
| `tools/full_custom_song_pipeline.py` | Main pipeline script for converting custom songs |
| `tools/*.py`                         | Supporting tools (downloader, audio encoder, pack-mode bundle builder) |
| `VERSION`                            | Pipeline version                                 |
| `beat_saber_song_ids.json`           | Song-slot catalog: every pack, slot ID, stock song title, bundle name — the pipeline's targeting database |
| `requirements.txt`                    | Python dependencies for the pipeline            |
| `ps4_config.example.json`             | Copy to `ps4_config.json`, fill in your PS4's IP/FTP |

### 📚 Documentation

| File | Description |
| ---- | ----------- |
| `README.md` | Main documentation (pipeline, features, feature flags, clean slate) |
| `PIPELINE-README.md` | Pipeline-internal README |
| `CHANGELOG-PLUGIN.md` / `CHANGELOG-PIPELINE.md` | Full change history |
| `docs/features/*.md` | Feature docs: custom-song replacement, song metadata modification, beatmap mode mapping |
| `docs/examples/`, `docs/how-to-replace-pack.md` | Pack-replacement walkthroughs |
| `docs/example-scripts/example_*` | **All 69 ready-to-run example files** — per-music-pack command docs (`.md`) + shell scripts (`.sh`) for every DLC pack, with verified BeatSaver MAP_IDs for five packs (billie eilish, britney spears, camelia, lizzo, rolling stones) and `[REPLACE_WITH_MAP_ID]` templates for the rest |

## Running the Pipeline

**Prerequisites:**

- Python 3.8+
- `pip install UnityPy` (see `requirements.txt` in this zip)
- A PS4 with GoldHEN, FTP enabled (port 2121), configured in `ps4_config.json`
  (copy `ps4_config.example.json` and fill in your PS4's IP)

**⚠️ REQUIRED — bring your own decrypted game dump (`ps4_dump/`):**

> This release does **NOT** include any dumped game data. The pack-bundle
> patching and catalog merging in the pipeline read the ORIGINAL stock pack
> bundles and Addressables catalog from a decrypted dump of YOUR OWN copy of
> the game. **You are responsible for obtaining your own dump of the correct
> game version with the DLC music packs you intend to modify, and placing the
> files into the `ps4_dump/` folder** next to the repo (the pipeline expects
> `ps4_dump/CUSA12878-patch/...`). We cannot and do not distribute these
> files — they are copyrighted game content. The expected layout is
> documented in the README ("ps4_dump"). Without the dump, per-song deploys
> still work (they only need the dump for the music-pack mode mapping /
> catalog steps); pack-mode deploys will tell you which bundle is missing.

**Quick Start — one command per song (recommended):**

```bash
# Download from BeatSaver, convert, and deploy song + its music pack + plugin +
# feature flags + redirects + catalog, then self-validate — all in ONE command:
python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song <MAP_ID> \
    --target <SLOT_NAME> \
    --deploy-full
```

Each `--deploy-full` is self-contained: it builds and deploys the latest plugin,
deploys only that song's bundle, surgically patches that song's music pack (with
a matching Addressables catalog so the pack passes Unity's CRC check), regenerates
`redirects.json` scoped to exactly what is deployed (existing custom songs in
other packs are preserved), and runs post-deploy validation. **A failed validation
aborts the deploy with a non-zero exit** — the game never boots into a broken
state silently.

Useful variants:

```bash
# Temporarily play only OFFICIAL songs (kill switch — no uninstall, next boot):
python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_plugin=false
# ...and back to custom songs:
python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_plugin=true

# Skip building/deploying the plugin (pin a specific plugin build on the PS4):
python3 tools/full_custom_song_pipeline.py ... --deploy-full --skip-plugin-deployment

# Revert a single song slot to stock without a full clean slate:
python3 tools/full_custom_song_pipeline.py --clear-target-song <SLOT_NAME>
```

See the main `README.md` for full pipeline documentation.

## Runtime Feature Flags (`features.json`)

| Flag | Default | Purpose |
|------|---------|---------|
| `enable_plugin` | `true` (when absent) | Global kill switch — `false` = fully inert plugin, 100% official songs on next boot |
| `enable_custom_song_replacements` | `false` | Gates all bundle redirects |
| `enable_song_metadata_modification` | `false` | Gates song name/artist swaps in the UI |
| `enable_beatmap_mode_mapping` | `false` | Gates extra game modes (OneSaber/NoArrows/90Degree) — OFF serves stock pack bundles + catalog |

On boot the plugin shows one combined toast with its state:
`BS Deluxe vX (ON) / By Chris Primeish / (3/3 features ON)` — or
`BS Deluxe vX (OFF) / By Chris Primeish / (official songs only)`.

## Plugin Installation

1. Copy `beat_saber_deluxe.prx` to `/data/GoldHEN/plugins/` on your PS4
2. Copy `features.json` to `/data/GoldHEN/AFR/CUSA12878/features.json`
3. Add `/data/GoldHEN/plugins/beat_saber_deluxe.prx` under `[CUSA12878]` in `/data/GoldHEN/plugins.ini`
4. Deploy songs with the pipeline (it manages `redirects.json` for you — the
   bundled copy is an empty template)
5. Launch Beat Saber — the boot toast confirms the plugin state
<!-- END_PROTECTED -->
