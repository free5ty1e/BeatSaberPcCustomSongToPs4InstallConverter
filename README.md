# Beat Saber Deluxe 🎵⚡

**Custom song replacement for PlayStation 4 Beat Saber (CUSA12878, version 2.04)**

> **📋 Prerequisites:**
> - **Beat Saber PS4 version 2.04** (CUSA12878, patch 2.04) — this is the specific version all development targets
> - **Full decrypted game dump** — place the dump in `/workspace/ps4_dump/` with the following structure:
>   ```
>   ps4_dump/CUSA12878-app/          # Base game (v1.00)
>   ps4_dump/CUSA12878-patch/        # Game patch (v2.04)
>   ```
>   The dump must include the unpacked patch files (eboot.bin, Media/ directory, etc.). Tools like PS4 Dumper on a jailbroken PS4 create this via the `split=3` config option.

Replace any DLC song's audio and beatmaps with community-made custom songs — no game modding required. Works via GoldHEN's file redirection hook.

> **⚠️ Current limitations:**
> - **Song menu is untouched** — song names, artists, and cover art still show the original Rolling Stones track. You must remember which custom song is mapped to which slot to find it in-game.
> - **No note color customization** — left/right saber colors are the game's default red/blue. Custom color schemes are planned (M3 on roadmap).
> - **Extra game modes (OneSaber, 90Degree) are experimental** — mode selector buttons may appear via IL2CPP hook (Exp 119), but labels show "Standard" for all modes. Actual mode selection during gameplay works for OneSaber and 90Degree if modes are set via `--add-mode-characteristics` in the pipeline.

## Status

🏆 **v0.65** — All 13 Rolling Stones slots replaced with custom songs. IL2CPP hook infrastructure deployed for mode selector. Experimental OneSaber/90Degree support via `--add-mode-characteristics`. **Pack bundle metadata patching (song name/artist display) is the next major milestone.**

### Key Achievements
- ✅ Custom song audio + beatmaps work in 13 slots
- ✅ All 5 difficulties replaced per slot
- ✅ Audio sync (BPM data) preserved from mapper's original file
- ✅ Score saving works — PlayerData.dat written on clean exit
- ✅ Plugin hot-reload supported — drop new .prx, restart game

### In Progress: Pack Bundle Metadata Patching
**Goal:** Modify the pack bundle (`therollingstones_pack_assets_all_a99482a8a3da9e991e5ae36f2fea209c.bundle`) to display custom song name/artist in-game.

**Blocker:** Addressables catalog validates BOTH `m_BundleSize` (7,902,803 bytes) AND `m_Crc` (`0xdc8b314f`). Either mismatch causes CE-34878-0 crash.

**Viable Approach (Option B):** Uncompressed block injection — the 49 uncompressed blocks (flag=0, each 131,072 bytes stored as raw data) can be modified without changing file_size. Use GF(2) linear algebra on alignment padding bytes for CRC correction.

### Out of Scope
- Base game songs (only Rolling Stones DLC slots are targetable)
- Songs not in the 13 targeted slots
- PS4 system-level modifications beyond GoldHEN plugin

## Development Workflow

1. **Build pipeline:** `full_custom_song_pipeline.py` — takes a song ZIP, produces deploy-ready bundle + config
2. **Plugin build:** `build.sh` in `beat_saber_deluxe/` — compiles PRX with PS4 toolchain
3. **Deploy:** `deploy_all.sh` — uploads plugin + bundles to PS4 via FTP (port 2121)

### Development Scripts
Experimental/dev scripts go in `beat_saber_deluxe/development/scripts/`. Only after proven should they be integrated into production pipeline or plugin source.

## Architecture Overview

```
┌─────────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│  Custom Song ZIP    │────▶│  Pipeline (Python) │────▶│  .bundle + config  │
└─────────────────────┘     └──────────────────┘     └───────────────────┘
                                                              │
                                                              ▼
┌─────────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│  Beat Saber PS4     │◀────│  GoldHEN Plugin   │◀────│  FTP Deploy (2121)  │
│  (CUSA12878 v2.04)  │     │  (beat_saber.prx) │     └───────────────────┘
└─────────────────────┘     └──────────────────┘
```

The plugin hooks file I/O to redirect Rolling Stones asset paths to custom song bundles stored in `/data/GoldHEN/AFR/CUSA12878/`. The pipeline handles audio conversion (lossless → PCM16 FSB5), beatmap V2→V3 conversion, and addressable bundle assembly.

### 🎥 Demo Video
https://www.youtube.com/watch?v=J835HDdB-7g

## Roadmap

| Milestone | Status | Description |
|-----------|--------|-------------|
| M1: Song Replacement | ✅ Complete | 13 slots replaced with custom audio + beatmaps |
| M2: Mode Selector | 🟡 In Progress | OneSaber/90Degree support via IL2CPP hook (labels show "Standard") |
| M3: Note Colors | ⏳ Planned | Custom left/right saber colors per song |
| M4: Pack Bundle Metadata | 🔬 Researching | Display custom song name/artist in-game (uncompressed block injection approach) |

## License & Credits

This project is for educational/research purposes. It does not modify Beat Saber's game code or bypass DRM. Custom songs are sourced from the community and remain the property of their respective creators.
