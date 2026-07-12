# Beat Saber Deluxe 🎵⚡

**Custom song replacement for PlayStation 4 Beat Saber (CUSA12878)**

Replace any Rolling Stones DLC song's audio and beatmaps with community-made custom songs — no game modding required. Works via GoldHEN's file redirection hook.

> **⚠️ Current limitations:**
> - **Song menu is untouched** — song names, artists, and cover art still show the original Rolling Stones track. You must remember which custom song is mapped to which slot to find it in-game.
> - **No note color customization** — left/right saber colors are the game's default red/blue. Custom color schemes are planned (M3 on roadmap).
> - **No extra game modes** — custom songs only provide Standard beatmaps. 90-degree, 360-degree, and OneSaber modes are not added.

## Status

🏆 **v0.53 ALPHA** — All 13 Rolling Stones slots replaced. Every song perfectly synchronized, both note colors working.


### 🎥Demo Video of Redirecting a Rolling Stones Song to a Custom Song
https://www.youtube.com/watch?v=J835HDdB-7g

### ✅ What Works

| Feature | Status |
|---------|--------|
| Audio replacement | ✅ PCM16 FSB5 lossless, any song length |
| Beatmap replacement | ✅ All 5 difficulties (Easy → Expert+) |
| V2→V3 beatmap conversion | ✅ Auto-detects legacy format, converts to playable V3 |
| Audio sync (bpmData) | ✅ Uses mapper's actual last-note beat — no progressive desync |
| Note timing (bpmEvents) | ✅ Populated for all songs — no BPM=60 fallback |
| Note colors | ✅ Both red and blue correct (c field fix) |
| All object types | ✅ Arrows, dots, chains, arcs, walls, bombs — all working |
| Score saving | ✅ Clean exit, PlayerData.dat written |
| Debug logging | ✅ Verbose per-file logging to `/data/GoldHEN/AFR/CUSA12878/bs_log.txt` (debug build) |
| Other songs unaffected | ✅ Only the 13 targeted slots are redirected; all other DLC and base songs play normally |
| Plugin hot-reload | ✅ Drop in new `.prx`, restart game — no full PS4 reboot needed |
| CI/CD automation | ✅ Both PRX variants built and uploaded as artifacts on every push/PR |
| GitHub Releases | ✅ Tag `v*` auto-creates release with PRX files + `plugins.ini` |

### ❌ Known Limitations

| Limitation | Impact | Future? |
|------------|--------|---------|
| Song names/artists unchanged | Must remember which slot has which custom song | Post-MVP |
| 13-song redirect config (editable file) | Limited to Rolling Stones slots by default | ✅ Done — edit `redirects.json` to add more |
| No note color customization | Left/right remain default red/blue | M3 |
| No extra game modes | 90-degree, 360-degree, OneSaber not added | Post-MVP |
| HEVAG encoder produces garbage | Can't use compressed audio (PCM16 is lossless anyway) | Unlikely (Sony proprietary) |
| Vorbis FSB5 codec mismatch | FMOD/libvorbis codebook incompatibility | Unlikely |
| 360° beatmaps unplayable | PS4 VR has single-camera ~90° tracking arc | Won't fix |

## Quick Start (5 minutes)

### Deploy Everything to PS4

```bash
cd beat_saber_deluxe
./deploy_all.sh --debug
```

This builds the plugin with verbose logging, uploads it and all 13 custom song bundles to PS4, and clears the log.

### Launch Beat Saber on PS4

Look for the notification: **BS Deluxe v0.53 started** in the top-right corner. Play any Rolling Stones song to hear your custom replacement.

---

## 13 Rolling Stones → Custom Song Replacements

| Slot ID | Original Song | Custom Song | Artist | BPM |
|---------|--------------|-------------|--------|-----|
| `startmeup` | Start Me Up | Espresso | Sabrina Carpenter | 104 |
| `angry` | Angry | Rhythm Is A Dancer | Pegboard Nerds | 128 |
| `bitemyheadoff` | Bite My Head Off | Escaping the Ruins | MDK | 160 |
| `cantyouhearmeknocking` | Can't You Hear Me Knocking | Spicy | aespa | 115 |
| `deadmanwalking` | Dead Man Walking | Finesse (Remix) | Bruno Mars | 105 |
| `gimmeshelter` | Gimme Shelter | Yes I'm A Mess | AJR | 184 |
| `icantgetnosatisfaction` | (I Can't Get No) Satisfaction | Dreams Come True | aespa | 99 |
| `livebythesword` | Live By The Sword | Take Me to the Beach | Imagine Dragons | 105 |
| `messitup` | Mess It Up | Powersnake | Brothers Of Metal | 175 |
| `paintitblack` | Paint It Black | Time Lapse | TheFatRat | 127 |
| `sugarsoaker` | Sugar Soaker | Venom of Venus | Powerwolf | 164 |
| `sympathyforthedevil` | Sympathy for the Devil | LIT | Polyphia | 99 |
| `wholewideworld` | Whole Wide World | VOLUPTE | Tare | 128 |

Each custom song has 5 difficulty levels (Easy → Expert+) and uses lossless PCM16 FSB5 audio.

---

## Converting Your Own Songs

### Finding Target Song IDs

Every song in Beat Saber PS4 has a unique **slot ID** that corresponds to its bundle path (`BeatmapLevelsData/<slot_id>`). The full database of all 306 official song IDs is in:

> [`.agent/beat_saber_song_ids.json`](.agent/beat_saber_song_ids.json)

To find a slot ID for a different song, search the JSON:
```bash
grep -B2 '"MUSIC STAR"' .agent/beat_saber_song_ids.json
```

### Single Song Convert & Deploy

```bash
python3 beat_saber_deluxe/tools/full_custom_song_pipeline.py \
  --song-dir /path/to/song_directory \
  --target <slot_id> --pcm16 --no-pad --convert-to-v3 \
  --deploy --deploy-plugin
```

### Replace a Specific Rolling Stones Slot

Pick a BeatSaver song, download it to a directory, then run the pipeline with the corresponding `--target`:

| Command | Replaces | Song ID |
|---------|----------|---------|
| `--target startmeup --song-dir ./songs/espresso` | Start Me Up → Espresso | `BeatmapLevelsData/startmeup` |
| `--target angry --song-dir ./songs/rhythm-is-a-dancer` | Angry → Rhythm Is A Dancer | `BeatmapLevelsData/angry` |
| `--target bitemyheadoff --song-dir ./songs/escaping-the-ruins` | Bite My Head Off → Escaping the Ruins | `BeatmapLevelsData/bitemyheadoff` |
| `--target cantyouhearmeknocking --song-dir ./songs/spicy` | Can't You Hear Me Knocking → Spicy | `BeatmapLevelsData/cantyouhearmeknocking` |
| `--target deadmanwalking --song-dir ./songs/finesse-remix` | Dead Man Walking → Finesse (Remix) | `BeatmapLevelsData/deadmanwalking` |
| `--target gimmeshelter --song-dir ./songs/yes-im-a-mess` | Gimme Shelter → Yes I'm A Mess | `BeatmapLevelsData/gimmeshelter` |
| `--target icantgetnosatisfaction --song-dir ./songs/dreams-come-true` | Satisfaction → Dreams Come True | `BeatmapLevelsData/icantgetnosatisfaction` |
| `--target livebythesword --song-dir ./songs/take-me-to-the-beach` | Live By The Sword → Take Me to the Beach | `BeatmapLevelsData/livebythesword` |
| `--target messitup --song-dir ./songs/powersnake` | Mess It Up → Powersnake | `BeatmapLevelsData/messitup` |
| `--target paintitblack --song-dir ./songs/time-lapse` | Paint It Black → Time Lapse | `BeatmapLevelsData/paintitblack` |
| `--target sugarsoaker --song-dir ./songs/venom-of-venus` | Sugar Soaker → Venom of Venus | `BeatmapLevelsData/sugarsoaker` |
| `--target sympathyforthedevil --song-dir ./songs/lit` | Sympathy for the Devil → LIT | `BeatmapLevelsData/sympathyforthedevil` |
| `--target wholewideworld --song-dir ./songs/volupte` | Whole Wide World → VOLUPTE | `BeatmapLevelsData/wholewideworld` |

### Example: Replace Sympathy for the Devil

```bash
python3 beat_saber_deluxe/tools/full_custom_song_pipeline.py \
  --song-dir ./beat-saber-ps4-custom-songs/songs_repo/0a9bb6f525e8ae5edcd590a826b13fa8f3db9120 \
  --target sympathyforthedevil --pcm16 --no-pad --convert-to-v3 \
  --deploy
```

This replaces "Sympathy for the Devil" with Polyphia's "LIT", uploads to PS4 via FTP.

### Deploy All 13 Songs

```bash
./beat_saber_deluxe/deploy_all.sh
```

The deploy script also uploads `redirects.json` alongside the bundles, so the plugin picks up the latest redirects on PS4.

### Managing the Redirect Config

The plugin reads `redirects.json` from the AFR path at startup. To add a new song slot or change an existing redirect without rebuilding the plugin:

```bash
# Build a song and automatically update the local redirects.json:
python3 full_custom_song_pipeline.py --song-dir ./my_song --target startmeup --generate-config

# Build, deploy bundle + config to PS4:
python3 full_custom_song_pipeline.py --song-dir ./my_song --target startmeup --deploy --deploy-config

# Sync config from PS4 (download, merge with local changes, redeploy):
python3 full_custom_song_pipeline.py --song-dir ./my_song --target startmeup --sync-config

# Enforce local config as truth (overwrite PS4 config entirely):
python3 full_custom_song_pipeline.py --enforce-config --deploy
```

---

## Prerequisites

| Item | Required | Notes |
|------|----------|-------|
| PS4 with GoldHEN | ✅ | v2.4b+ recommended |
| FTP server on PS4 | ✅ | Enable in GoldHEN settings |
| Network connection | ✅ | Between PC and PS4 |
| Beat Saber installed | ✅ | CUSA12878 (patched), any region |
| OpenOrbis PS4 Toolchain | ✅ | For building the plugin PRX |
| Python 3.10+ | ✅ | `pip install soundfile numpy pyfmodex UnityPy` |

---

## Pipeline

`beat_saber_deluxe/tools/full_custom_song_pipeline.py` converts a community Beat Saber song (WAV/OGG/FLAC + `.dat` beatmap files) into a PS4-compatible AssetBundle.

```bash
python3 tools/full_custom_song_pipeline.py \
  --song-dir <directory> --target <slot_id> --pcm16 --no-pad --convert-to-v3 \
  [--deploy] [--deploy-plugin] [--debug-logging]
```

### Key Flags

| Flag | Purpose |
|------|---------|
| `--song-dir` | Directory with song audio + `.dat` beatmap files |
| `--target` | Song slot ID (e.g. `startmeup`, `angry`) |
| `--pcm16` | PCM16 FSB5 audio (lossless, best quality) |
| `--no-pad` | Don't extend audio — use when PCM16 exceeds template resource size |
| `--convert-to-v3` | Auto-convert V2 beatmaps (legacy format) to V3 |
| `--deploy` | Upload bundle to PS4 via FTP after building |
| `--deploy-plugin` | Build + deploy plugin PRX |
| `--debug-logging` | Build plugin with `DEBUG=1` (verbose PS4 logging) |

### Redirect Config Management Flags

| Flag | Purpose |
|------|---------|
| `--generate-config` | Create/update `redirects.json` with the current `--target` entry. First call creates the file; subsequent calls add/update entries |
| `--deploy-config` | Deploy the local `redirects.json` to PS4 via FTP (to `/data/GoldHEN/AFR/CUSA12878/redirects.json`) |
| `--sync-config` | Download existing `redirects.json` from PS4, merge with current target, save locally, redeploy. Use when PS4 config has entries your local doesn't |
| `--enforce-config` | Ignore any PS4 config and use only the local `redirects.json` as truth, then deploy it to PS4 |

**Default behavior:** When deploying config, if no `redirects.json` exists locally, one is auto-generated with the current target mapping. When deploying a bundle, the config is automatically updated if the file already exists.

### What the Pipeline Does

1. **Encodes audio** as PCM16 FSB5 (lossless, any length)
2. **Replaces** the original song's `.resource` audio data, `AudioClip` metadata, and `audio.gz` BPM data
3. **Replaces all 5 beatmaps** (Easy → Expert+) with the custom song's beatmaps
4. **Converts V2→V3** if needed — auto-detects legacy `_notes`/`_time` format and converts to `colorNotes`/`b`
5. **Fixes sync** — populates `bpmEvents` so the game knows the song's tempo, scans beatmaps for the actual last-note beat for correct `bpmData`
6. **Fixes note colors** — sets both `a` and `c` fields (the PS4 game uses `c` for color, not `a`)
7. **Deploys** to PS4 via FTP if `--deploy` is set

---

## Plugin

GoldHEN PRX that hooks `open()` to redirect song file requests to custom bundles on the PS4 data partition.

```bash
cd beat_saber_deluxe
make                    # Release build (no verbose PS4 logging)
make DEBUG=1            # Debug build (verbose per-file logging)
```

The plugin source is at `beat_saber_deluxe/src/main.cpp`. Version is defined by the `PLUGIN_VERSION` macro.

### How It Works

```
Game opens BeatmapLevelsData/<slot_id>
    ↓
GoldHEN plugin hook → redirect to /data/GoldHEN/AFR/CUSA12878/<slot_id>_v3
    ↓
Custom AssetBundle loaded (PCM16 FSB5 audio + community beatmaps)
    ↓
Song plays with correct sync, both colors, score saves
```

### Architecture

The plugin intercepts file `open()` calls from Beat Saber at runtime. When the game requests `BeatmapLevelsData/startmeup` (for example), the plugin transparently redirects to a custom AssetBundle stored on the PS4's data partition. No original game files are modified — the redirect is purely in memory.

### Dynamic Redirect Config

The redirect table is no longer hardcoded. On startup, the plugin reads `redirects.json` from the AFR path:

**`/data/GoldHEN/AFR/CUSA12878/redirects.json`**
```json
{
  "redirects": {
    "startmeup": "startmeup_custom_v3",
    "angry": "angry_custom_v3",
    "bitemyheadoff": "bitemyheadoff_custom_v3"
  }
}
```

To add or change a redirect — edit the JSON on PS4 via FTP (at the path above), restart Beat Saber, and the plugin picks up the changes. No plugin rebuild needed.

The source of truth is [`beat_saber_deluxe/redirects.json`](beat_saber_deluxe/redirects.json) — edit this file, then run `./beat_saber_deluxe/deploy_all.sh` to push it alongside the bundles.

---

## CI/CD & Release Automation

The GitHub Actions workflow at [`.github/workflows/plugin-build.yml`](.github/workflows/plugin-build.yml) handles:

### On Push / Pull Request (main branch)
- Installs the OpenOrbis PS4 Toolchain
- Clones and builds the GoldHEN Plugin SDK from source
- Builds both PRX variants (release + debug)
- Generates a minimal `plugins.ini` for CUSA12878
- Generates `redirects.json` with the 13 Rolling Stones slot → bundle mappings
- Uploads all artifacts: PRX files, `plugins.ini`, `redirects.json`

### On Tag Push (`v*`)
When you push a tag like `v0.53`, the workflow additionally:
- Downloads the build artifacts from the previous job
- **Creates a GitHub Release** titled "Beat Saber Deluxe v0.53" with:
  - `beat_saber_deluxe.prx` — Release build
  - `beat_saber_deluxe_debug.prx` — Debug build (verbose logging)
  - `redirects.json` — Song redirect config (edit to add/change slot mappings)
  - `plugins.ini` — GoldHEN configuration for CUSA12878

### Manual Trigger
The workflow also supports `workflow_dispatch:` — you can trigger it from the Actions tab in GitHub without pushing code.

### Tagging a Release

```bash
git tag v0.53
git push origin v0.53
```

Visit GitHub → Actions → the running workflow → wait for release to appear in the Releases section.

---

## Sync & Color Fixes (Bug History)

| Bug | Root Cause | Fix | Version |
|-----|-----------|-----|---------|
| Progressive desync (3-6%) | bpmData `eb` in seconds, not beats | Scan beatmaps for actual last-note beat | v0.52 |
| Notes at ≈2× correct time ("very very late") | `bpmEvents: []` empty → game defaults to BPM=60 | Set `bpmEvents` from Info.dat BPM | v0.52 |
| Same for V3 format songs | Converter only handled V2 beatmaps | Patch `bpmEvents` on ANY beatmap format | v0.52c |
| All notes appear Red | Converter set `a` field but game uses `c` | Set both `a` and `c` from V2 `_type` | v0.53 |
| BPMInfo.dat `eb` smaller than beatmap max beat | Song has BPM change; BPMInfo.dat region eb too short | Cross-check with beatmap scan | v0.52c |

---

## Documentation

| Resource | Location | Description |
|----------|----------|-------------|
| 📚 **Knowledge Base** | [`.agent/llm-wiki-knowledge-base/`](.agent/llm-wiki-knowledge-base/) | Technical docs: audio sync, beatmap format, plugin architecture, PS4 environment. Visualizable in [Obsidian](https://obsidian.md) |
| 🗺️ **Roadmap** | [`.agent/roadmap.md`](.agent/roadmap.md) | Current milestones and planned features |
| 📋 **Song Replacements** | [`.agent/current-song-replacements-on-chris-ps4.md`](.agent/current-song-replacements-on-chris-ps4.md) | Current PS4 deployment state |
| 📖 **Sync Knowledge** | [`.agent/llm-wiki-knowledge-base/beatmap-audio-sync.md`](.agent/llm-wiki-knowledge-base/beatmap-audio-sync.md) | All sync root causes and fixes |
| 🧪 **Experiment Log** | [`.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md`](.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md) | Full experiment/test history |
| 📦 **Song ID Database** | [`.agent/beat_saber_song_ids.json`](.agent/beat_saber_song_ids.json) | 306 official song IDs with bundle paths |
| 🔧 **Legacy Docs** | [`beat_saber_deluxe/development/docs/`](beat_saber_deluxe/development/docs/) | Archived historical documentation and research |

---

## Project Structure

```
workspace/
├── README.md                               # This file
├── CLAUDE.md                               # AI agent guardrails
├── .agent/                                 # Project configuration & knowledge base
│   ├── llm-wiki-knowledge-base/            # Technical knowledge (Obsidian vault)
│   ├── roadmap.md                          # Development roadmap
│   ├── beat_saber_song_ids.json            # 306 official song IDs
│   └── current-song-replacements-on-chris-ps4.md
├── beat_saber_deluxe/                      # Main project directory
│   ├── beat_saber_deluxe.prx              # Plugin (release build)
│   ├── beat_saber_deluxe_debug.prx        # Plugin (debug build)
│   ├── deploy_all.sh                      # Deploy plugin + 13 bundles to PS4
│   ├── Makefile                           # Plugin build system
│   ├── src/main.cpp                       # Plugin source (redirect table)
│   ├── tools/
│   │   ├── full_custom_song_pipeline.py   # Main pipeline
│   │   ├── hevag_encoder.py               # Audio encoder
│   │   ├── lapped_audio.py                # Lapped audio detection
│   │   └── download_beatsaver_songs.py    # BeatSaver downloader
│   └── development/                       # Archived scripts & docs
│       ├── scripts/                       # Old/unused pipeline scripts
│       └── docs/                          # Historical documentation
├── beat-saber-ps4-custom-songs/           # Song repository
│   └── songs_repo/                        # Downloaded custom song files
└── .github/workflows/plugin-build.yml     # CI/CD workflow
```

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| v0.53 | 2026-07-10 | Note color fix (c field), CI/CD passing, repo cleanup |
| v0.52 | 2026-07-09 | bpmEvents/bpmData sync fix, V3 empty bpmEvents patch, BPMInfo.dat cross-check |
| v0.51 | 2026-07-08 | 12-song redirect table, priority-based beatmap fallback |
| v0.50 | 2026-07-01 | Proof of concept, PCM16 FSB5 audio, plugin hook working |
