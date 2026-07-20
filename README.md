# Beat Saber Deluxe 🎵⚡

**Custom song replacement for PlayStation 4 Beat Saber (CUSA12878, version 2.04)**

Replace any Beat Saber DLC song's audio and beatmaps with community-made custom songs — no game modding required. Works via GoldHEN's file redirection hook and a PS4 plugin. The pipeline can target **any song** present in the game's `BeatmapLevelsData/` directory — not just the default set listed below.

> **📋 Prerequisites:**
> - **Beat Saber PS4 version 2.04** (CUSA12878, patch 2.04) — this is the specific version all development targets
> - **Full decrypted game dump** — place the dump in `/workspace/ps4_dump/` with the following structure:
>   ```
>   ps4_dump/CUSA12878-app/          # Base game (v1.00)
>   ps4_dump/CUSA12878-patch/        # Game patch (v2.04)
>   ```
>   The dump must include the unpacked patch files (eboot.bin, Media/ directory, etc.). Tools like PS4 Dumper on a jailbroken PS4 create this via the `split=3` config option.

> **⚠️ Current limitations:**
> - **Song menu is untouched** — song names, artists, and cover art in the menu still show the original song's metadata. You must remember which custom song is mapped to which slot.
> - **No note color customization** — left/right saber colors are the game's default red/blue. Custom color schemes are planned.
> - **Extra game modes (OneSaber, 90Degree) are experimental** — mode selector buttons may appear via IL2CPP hook, but labels show "Standard" for all modes. Actual mode selection during gameplay works for OneSaber and 90Degree if modes are set via `--add-mode-characteristics`.

## Available Song Slots (Default Targets)

The pipeline replaces songs by targeting specific filenames in the game's `BeatmapLevelsData/` directory. Below are the 13 default target slots currently configured. Use the `--target <name>` argument to specify which slot a custom song goes into.

The pipeline can target **any** song present in the game's dump — if the song has a `.bundle` file in `BeatmapLevelsData/`, you can replace it. To use a non-default target, point `--target` at any other bundle name from that directory.

| Target Name | Original Song |
|-------------|---------------|
| `angry` | Angry |
| `bitemyheadoff` | Bite My Head Off |
| `cantyouhearmeknocking` | Can't You Hear Me Knocking |
| `deadmanwalking` | Dead Man Walking |
| `gimmeshelter` | Gimme Shelter |
| `icantgetnosatisfaction` | (I Can't Get No) Satisfaction |
| `livebythesword` | Live By The Sword |
| `messitup` | Mess It Up |
| `paintitblack` | Paint It Black |
| `startmeup` | Start Me Up (most tested — good starting point) |
| `sugarsoaker` | Sugar Soaker |
| `sympathyforthedevil` | Sympathy For The Devil |
| `wholewideworld` | The Whole Wide World |

---

## Table of Contents

1. [Devcontainer Setup](#1-devcontainer-setup)
2. [Building the Plugin](#2-building-the-plugin)
3. [Deploying to PS4](#3-deploying-to-ps4)
4. [Activating the Plugin on PS4](#4-activating-the-plugin-on-ps4)
5. [Quick Start: Replace a Song from BeatSaver](#5-quick-start-replace-a-song-from-beatsaver)
6. [Full Custom Song Workflow](#6-full-custom-song-workflow)
7. [PS4 Log Management](#7-ps4-log-management)
8. [Architecture Overview](#8-architecture-overview)
9. [Roadmap](#9-roadmap)
10. [License & Credits](#10-license--credits)

---

## 1. Devcontainer Setup

This project uses a VS Code Devcontainer with the OpenOrbis PS4 Toolchain pre-installed. This is the **only supported development environment**.

### 1.1 Prerequisites on your host machine

- **VS Code** with the **Dev Containers** extension (ms-vscode-remote.remote-containers)
- **Docker** (Docker Desktop on Windows/Mac, or Docker Engine on Linux)
- **Git** (to clone the repo)

### 1.2 Open the project in the devcontainer

```bash
# Clone the repository
git clone <repo-url> /path/to/beat-saber-deluxe
cd /path/to/beat-saber-deluxe
```

Then in VS Code:

1. Open the `/path/to/beat-saber-deluxe` folder
2. Press `F1` → **Dev Containers: Reopen in Container**
3. Select the **"OpenOrbis SDK Workspace"** option when prompted
4. Wait for the container to build (first time takes 5-10 minutes — it downloads the OpenOrbis toolchain and all dependencies)

Once the container is ready, you'll have:

- **clang / clang++** — PS4 cross-compiler (x86_64-pc-freebsd12-elf)
- **lld-link** — PS4 linker
- **OpenOrbis PS4 Toolchain** at `/opt/openorbis/OpenOrbis/PS4Toolchain`
- **Python 3** with all required packages
- **lftp** — for FTP deployment to PS4
- **vgmstream-cli** — for audio conversion
- **GoldHEN Plugin SDK** — included in the workspace

### 1.3 Configure PS4 connection

Edit `beat_saber_deluxe/ps4_config.json` with your PS4's IP address:

```json
{
  "ps4": {
    "ip": "192.168.100.117",
    "ftp_port": 2121,
    "ftp_user": "anonymous",
    "ftp_password": ""
  },
  "title": {
    "id": "CUSA12878",
    "name": "Beat Saber"
  }
}
```

Replace `192.168.100.117` with your PS4's IP address. The default FTP port for GoldHEN is `2121`.

---

## 2. Building the Plugin

The plugin is a GoldHEN PRX (PS4-format shared library) that hooks file I/O to redirect song assets.

### 2.1 Quick build

```bash
cd /workspace/beat_saber_deluxe

# Release build (no verbose logging)
make

# Debug build (verbose per-file logging to bs_log.txt)
make DEBUG=1
```

Output files:
- `beat_saber_deluxe.prx` — release plugin
- `beat_saber_deluxe_debug.prx` — debug plugin (verbose logs)

### 2.2 Clean build

```bash
make clean
make
```

### 2.3 What the build does

1. Compiles all `.c` and `.cpp` files in `src/` using clang targeting `x86_64-pc-freebsd12-elf`
2. Links with `ld.lld` using the GoldHEN SDK libraries (`libGoldHEN_Hook`, `libSceLibcInternal`, `libkernel`)
3. Creates a PS4 FSELF (FSigned ELF with SCE magic `4f 15 3d 1d`) using the OpenOrbis `create-fself` tool
4. Outputs the final `.prx` file in the project root

### 2.4 Build system details

- **Makefile:** `/workspace/beat_saber_deluxe/Makefile`
- **Source files:** `/workspace/beat_saber_deluxe/src/`
- **Headers:** `/workspace/beat_saber_deluxe/include/`
- **Toolchain:** `/opt/openorbis/OpenOrbis/PS4Toolchain`

---

## 3. Deploying to PS4

Your PS4 must be:
- On firmware 9.00
- Running GoldHEN (2.3 or 2.4b)
- FTP server enabled (GoldHEN's built-in FTP on port 2121)
- On the same network as your dev machine
- **IP configured in** `beat_saber_deluxe/ps4_config.json`

### 3.1 Quick deploy (plugin + all 13 song bundles + config)

```bash
cd /workspace/beat_saber_deluxe

# Build and deploy release plugin + all bundles + redirects config
./deploy_all.sh

# Or deploy debug plugin
./deploy_all.sh --debug
```

This script:
1. Uploads the plugin to `/data/GoldHEN/plugins/beat_saber_deluxe.prx`
2. Uploads all 13 custom song bundles from `custom_songs/` to `/data/GoldHEN/AFR/CUSA12878/`
3. Uploads `redirects.json` to `/data/GoldHEN/AFR/CUSA12878/redirects.json`
4. Clears the PS4 log file

### 3.2 Manual deploy (individual components)

```bash
# Deploy only the plugin
python3 /workspace/beat_saber_deluxe/tools/full_custom_song_pipeline.py --deploy-plugin

# Deploy plugin with debug logging
python3 /workspace/beat_saber_deluxe/tools/full_custom_song_pipeline.py --deploy-plugin --debug-logging

# Deploy a single custom song bundle (built separately)
python3 /workspace/beat_saber_deluxe/tools/full_custom_song_pipeline.py \
    --target startmeup \
    --deploy

# Deploy the redirects config
python3 /workspace/beat_saber_deluxe/tools/full_custom_song_pipeline.py \
    --target startmeup \
    --deploy-config
```

### 3.3 FTP details

- **IP:** Your PS4's IP (configured in `ps4_config.json`)
- **Port:** 2121 (GoldHEN's default FTP port)
- **User:** `anonymous` (no password)
- **Plugin destination:** `/data/GoldHEN/plugins/beat_saber_deluxe.prx`
- **Bundle destination:** `/data/GoldHEN/AFR/CUSA12878/<target>_v3`
- **Config destination:** `/data/GoldHEN/AFR/CUSA12878/redirects.json`
- **Log file:** `/data/GoldHEN/AFR/CUSA12878/bs_log.txt`

---

## 4. Activating the Plugin on PS4

1. **Ensure GoldHEN is running** on your PS4 (FW 9.00, GoldHEN payload enabled)
2. **Deploy the plugin** — see section 3
3. **Start Beat Saber** on your PS4
4. The plugin activates automatically when GoldHEN loads at startup — no manual enable needed

### 4.1 Verifying the plugin is active

After starting Beat Saber, check the PS4 log:

```bash
# Download the log from PS4
lftp -u anonymous, -p 2121 192.168.100.117 \
    -e "get /data/GoldHEN/AFR/CUSA12878/bs_log.txt -o /tmp/ps4_log.txt; quit"

# Check for the plugin version header
grep "BS Deluxe" /tmp/ps4_log.txt
# Expected: "=== BS Deluxe v0.80 started ==="

# Check for redirects (songs being replaced)
grep "->" /tmp/ps4_log.txt | grep AFR
# Expected: "/.../BeatmapLevelsData/startmeup -> /data/GoldHEN/AFR/CUSA12878/startmeup_v3"
```

### 4.2 Plugin hot-reload

You can deploy an updated plugin while the game is running:

```bash
# Build and deploy without restarting the game
make && ./deploy_all.sh

# Then restart Beat Saber from the PS4 menu
```

The plugin is reloaded by GoldHEN when the game executable is launched. A full PS4 reboot is rarely needed but can help if the plugin isn't loading.

### 4.3 Troubleshooting activation

| Symptom | Cause | Fix |
|---------|-------|-----|
| No "BS Deluxe" in log | Plugin not deployed | Run `deploy_all.sh` |
| Old version shown | Plugin cache | Restart Beat Saber or reboot PS4 |
| CE-34878-0 crash | Bundle CRC/size mismatch | Run pipeline with `--no-pad` or `--preserve-metadata` |
| "redirect" shows in log but song doesn't play | Bundle format issue | Verify bundle deployed correctly |

---

## 5. Quick Start: Replace a Song from BeatSaver

This is the fastest way to get a custom song onto your PS4. Run this single command from the devcontainer:

```bash
cd /workspace/beat_saber_deluxe

python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song <MAP_ID> \
    --target startmeup \
    --pcm16 \
    --no-pad \
    --convert-to-v3 \
    --deploy \
    --generate-config \
    --deploy-config
```

**Parameters explained:**
- `<MAP_ID>` — the BeatSaver map key (e.g. `1d6c7c2`). Find it on [BeatSaver.com](https://beatsaver.com) — it's the short hash in the URL (e.g. `beatsaver.com/maps/1d6c7c2`)
- `--target startmeup` — which PS4 song slot to replace. See [Available Song Slots](#available-song-slots-targets) above
- `--pcm16` — use PCM16 audio encoding instead of Vorbis (better quality, more compatible)
- `--no-pad` — skip audio padding (faster, smaller bundles)
- `--convert-to-v3` — convert beatmaps from V2 to V3 format (required for Beat Saber on PS4)
- `--deploy` — upload the resulting bundle to PS4 via FTP
- `--generate-config` — create/update the redirects config file
- `--deploy-config` — upload the config to PS4

**Example — download "Espresso" by Sabrina Carpenter and replace Start Me Up:**

```bash
python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song 1d6c7c2 \
    --target startmeup \
    --pcm16 --no-pad --convert-to-v3 \
    --deploy --generate-config --deploy-config
```

**After the command completes:**
1. The bundle is built and deployed to `/data/GoldHEN/AFR/CUSA12878/startmeup_v3`
2. The redirect config is updated and deployed
3. Restart Beat Saber on your PS4
4. Navigate to the target song in the game's song pack — your custom song will play!

---

## 6. Full Custom Song Workflow

### 6.1 Download a song from BeatSaver manually

```bash
# Download by map key
python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song <MAP_ID> \
    --target startmeup \
    --pcm16 --no-pad --convert-to-v3 --deploy
```

The pipeline automatically:
1. Downloads the song ZIP from BeatSaver API
2. Extracts the audio (WAV/OGG) and beatmap `.dat` files
3. Converts audio to FSB5 format (PS4-compatible)
4. Converts beatmaps from V2 to V3 format
5. Packages everything into an AssetBundle
6. Deploys to PS4 via FTP

### 6.2 Use a local song directory

If you already have a custom song folder with audio + beatmap files:

```bash
python3 tools/full_custom_song_pipeline.py \
    --song-dir /path/to/song/folder \
    --target startmeup \
    --pcm16 --no-pad --convert-to-v3 --deploy
```

The song folder should contain:
- A single audio file (`.wav`, `.ogg`, or `.mp3`)
- Beatmap `.dat` files (generated by [ChroMapper](https://ChroMapper.com), [MediocreMapper](https://github.com/Kylemc1413/Mediocre-Map-Mapper), or downloaded from BeatSaver)

### 6.3 Pipeline steps in detail

The pipeline (`tools/full_custom_song_pipeline.py`) performs these steps:

1. **Load template** — reads the original song's AssetBundle from the game dump
2. **Convert audio** — WAV/OGG → PCM16 → FSB5 (with optional padding)
3. **Replace audio** — overwrites the `.resource` data in the bundle with new FSB5
4. **Update metadata** — fixes `AudioClip.m_Length` and `m_Resource.m_Size`
5. **Update audio.gz** — fixes `songSampleCount` and BPM data
6. **Replace beatmaps** — converts V2 `.dat` → gzip → TextAsset for all 5 difficulties
7. **Save bundle** — writes the modified bundle with LZ4 compression
8. **Deploy** — uploads to PS4 via FTP (if `--deploy` is set)

### 6.4 Additional pipeline options

| Flag | Description |
|------|-------------|
| `--vorbis` | Use Vorbis audio encoding instead of PCM16 (smaller files, may be slower) |
| `--pcm16` | Use PCM16 audio encoding (recommended, better compatibility) |
| `--no-pad` | Skip 12MB audio padding (reduces bundle size) |
| `--preserve-metadata` | Keep original song metadata (audio length, etc.) |
| `--convert-to-v3` | Convert V2 beatmaps to V3 format (required for PS4) |
| `--add-mode-characteristics` | Add gameplay mode characteristics (OneSaber, 90Degree, etc.) |
| `--enable-modes` | Comma-separated list of modes to enable (e.g. `OneSaber,90Degree`) |
| `--ignore-non-standard-beatmaps` | Skip non-standard difficulty beatmaps |
| `--target <name>` | PS4 song slot to replace (see [Available Song Slots](#available-song-slots-targets)) |
| `--output <path>` | Custom output path for the built bundle |
| `--deploy` | Upload the bundle to PS4 via FTP |
| `--deploy-plugin` | Upload the plugin PRX to PS4 |
| `--debug-logging` | Deploy plugin with verbose logging (only with `--deploy-plugin`) |
| `--generate-config` | Generate/update `redirects.json` |
| `--deploy-config` | Upload `redirects.json` to PS4 |
| `--sync-config` | Upload config and sync all bundles to PS4 |
| `--enable-plugin` | Enable the plugin in GoldHEN's config |
| `--disable-plugin` | Disable the plugin in GoldHEN's config |

---

## 7. PS4 Log Management

The plugin writes a log file to `/data/GoldHEN/AFR/CUSA12878/bs_log.txt` on the PS4. This is essential for debugging.

### 7.1 Clear the log

Before each experiment, clear the log so you only see fresh output:

```bash
# Via FTP
lftp -u anonymous, -p 2121 <PS4_IP> \
    -e "rm /data/GoldHEN/AFR/CUSA12878/bs_log.txt; quit"

# Or via the pipeline
python3 tools/full_custom_song_pipeline.py --deploy-plugin

# deploy_all.sh also clears the log automatically
./deploy_all.sh
```

### 7.2 Download and analyze the log

```bash
# Download the log
lftp -u anonymous, -p 2121 <PS4_IP> \
    -e "get /data/GoldHEN/AFR/CUSA12878/bs_log.txt -o /tmp/ps4_log.txt; quit"

# Check plugin version
grep "BS Deluxe" /tmp/ps4_log.txt

# Check for memory injection (MEMINJ) activity
grep "MEMINJ" /tmp/ps4_log.txt

# Check for redirects (songs being replaced)
grep "->" /tmp/ps4_log.txt | grep AFR

# Check for errors
grep -i "error\|fail\|crash" /tmp/ps4_log.txt

# Archive the log for reference
cp /tmp/ps4_log.txt "/workspace/.ai_memory/experiment_logs/ps4_log_$(date +%Y%m%d_%H%M%S).txt"
```

### 7.3 Log format

```
=== BS Deluxe v0.80 started ===           # Plugin header + version
v0.80 — dynamic redirect config (...)
loaded 32 redirects from config
  e.g. BeatmapLevelsData/startmeup -> /data/GoldHEN/AFR/CUSA12878/startmeup_v3
open:/data/GoldHEN/AFR/CUSA12878/bs_log.txt
[MEMINJ] Initialized                     # Memory injection module ready
...
open:/archive/mount/point/Media/StreamingAssets/BeatmapLevelsData/startmeup -> /data/GoldHEN/AFR/CUSA12878/startmeup_v3   # Redirect fired!
[MEMINJ] Scanning...                     # Memory injection triggered
[MEMINJ] Found klass 0x... via pattern   # BeatmapLevelSO class found
[MEMINJ] Found 1 candidates with klass   # Objects located
...
```

---

## 8. Architecture Overview

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

The plugin hooks file I/O to redirect DLC song asset paths to custom song bundles stored in `/data/GoldHEN/AFR/CUSA12878/`. The pipeline handles audio conversion (lossless → PCM16 FSB5), beatmap V2→V3 conversion, and addressable bundle assembly.

### Key Components

| Component | Location | Description |
|-----------|----------|-------------|
| GoldHEN Plugin | `src/` | C++ plugin that hooks file I/O, detects song loading, and redirects to custom bundles |
| Song Pipeline | `tools/full_custom_song_pipeline.py` | Python script that converts custom songs into PS4-compatible bundles |
| Deploy Script | `deploy_all.sh` | Uploads plugin + bundles + config to PS4 via FTP |
| Development Scripts | `development/scripts/` | Experimental scripts — not production-ready |
| Game Dump | `/workspace/ps4_dump/` | Decrypted PS4 game dump (base app + patch) |
| Bundles | `custom_songs/` | Built custom song bundles ready for deployment |
| Config | `ps4_config.json` | PS4 connection settings (IP, port) |

### 🎥 Demo Video

https://www.youtube.com/watch?v=J835HDdB-7g

---

## 9. Roadmap

| Milestone | Status | Description |
|-----------|--------|-------------|
| M1: Song Replacement | ✅ Complete | 13 slots replaced with custom audio + beatmaps |
| M2: Mode Selector | 🟡 In Progress | OneSaber/90Degree support via IL2CPP hook (labels show "Standard") |
| M3: Note Colors | ⏳ Planned | Custom left/right saber colors per song |
| M4: Pack Bundle Metadata | 🔬 Researching | Display custom song name/artist in-game (memory injection approach) |

---

## 10. License & Credits

This project is for educational/research purposes. It does not modify Beat Saber's game code or bypass DRM. Custom songs are sourced from the community and remain the property of their respective creators.

- **OpenOrbis PS4 Toolchain** — the cross-compilation toolchain used to build the plugin
- **GoldHEN** — the PS4 homebrew enabler that provides the hooking framework
- **vgmstream** — audio conversion library used for FSB5 encoding
