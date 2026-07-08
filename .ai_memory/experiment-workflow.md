# Experiment Workflow: Beat Saber PS4 Custom Songs

> **Purpose:** This document defines the complete, repeatable workflow for every experiment/test cycle. A fresh agent should be able to pick up the project exactly where it was left off by following this document.

---

## 1. Fixed Context (always true)

| Item | Value |
|------|-------|
| PS4 IP | `192.168.100.117:2121` |
| FTP creds | anonymous (no password) |
| PS4 FW | 9.00 |
| GoldHEN | 2.3 / 2.4b16.2 |
| CUSA ID | `CUSA12878` |
| Plugin deploy path | `/data/GoldHEN/plugins/` |
| Plugin config | `/data/GoldHEN/plugins.ini` (root level, NOT `plugins/`) |
| AFR path | `/data/GoldHEN/AFR/CUSA12878/` |
| PS4 status | **ONLINE** (FTP accessible) |

## 2. File Layout

```
/workspace/
  beat_saber_deluxe/              # Plugin + pipeline source
    src/main.cpp                  # GoldHEN plugin (open hook, redirects, logging)
    Makefile                      # Build system
    tools/
      full_custom_song_pipeline.py  # End-to-end pipeline
      hevag_encoder.py              # FSB5 audio builders (HEVAG, Vorbis, PCM16)
      lapped_audio.py               # Lapped audio detection/generation
    custom_songs/                 # Prepped song bundles
      startmeup_custom.bundle     # Last built bundle
      360_prepped/                # Prepped "360" by Charli XCX
      espresso_prepped/           # Prepped "Espresso" by Sabrina Carpenter
    ps4_config.json               # PS4 IP, CUSA, paths
  ps4_dump/CUSA12878-patch/       # Dumped game files (read-only reference)
    Media/StreamingAssets/BeatmapLevelsData/  # 306 official song bundles
  beat-saber-ps4-custom-songs/
    songs_repo/                   # 96 downloaded community songs
  .agent/
    project_summary.md            # Current project status
    roadmap.md                    # Milestone tracking
    llm-wiki-knowledge-base/      # 24-page wiki (durable knowledge)
  .ai_memory/
    beat-saber-ps4-custom-songs/
      experiment_log.md           # Sequential experiment log
      song_testing_log.md         # Song test results table
      beat_saber_song_ids.json    # All 306 official song bundles
      user_preferences.md         # User constraints/preferences
    project-summary-update-rule.md # Enforcement: what to update and when
    experiment-workflow.md        # THIS FILE — the workflow
```

## 3. The Experiment Cycle

Each experiment follows this exact sequence:

### Phase A: Understand Current State

1. Read all active docs to establish context:
   - `.agent/project_summary.md` — current status, what's being tested, next steps
   - `.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md` — latest entries
   - `.ai_memory/beat-saber-ps4-custom-songs/song_testing_log.md` — song test results
   - `CLAUDE.md` — danger mode guardrails
2. Read any relevant source files that need to change.

### Phase B: Make Changes

1. **Edit source files** (plugin `main.cpp`, pipeline Python, beatmap converter, etc.)
2. **Build plugin** if needed (see section 4 below)
3. **Run the pipeline** to create the song bundle (see section 5 below)
4. **Verify** the output files exist and look correct

### Phase C: Deploy to PS4

Uses the pipeline script:
```bash
# Deploy bundle + plugin (release — no verbose PS4 logging)
python3 tools/full_custom_song_pipeline.py \
  --song-dir ./custom_songs/espresso_prepped \
  --target startmeup \
  --pcm16 \
  --no-pad \
  --deploy \
  --deploy-plugin

# Or deploy bundle + plugin with verbose PS4 logging for debugging:
python3 tools/full_custom_song_pipeline.py \
  --song-dir ./custom_songs/espresso_prepped \
  --target startmeup \
  --pcm16 \
  --no-pad \
  --deploy \
  --deploy-plugin \
  --debug-logging

# Or just build & deploy plugin (no bundle):
python3 tools/full_custom_song_pipeline.py \
  --song-dir ./custom_songs/espresso_prepped \
  --target startmeup \
  --deploy-plugin
```

The pipeline:
- `--deploy-plugin`: builds the plugin with `make`, deploys `.prx` to `/data/GoldHEN/plugins/`, and idempotently updates `plugins.ini`
- `--debug-logging`: builds plugin with `#ifdef VERBOSE_LOG` enabled (per-file logging on PS4). Only meaningful with `--deploy-plugin`.

### Phase D: Prepare for User Test

**BEFORE PRESENTING TO THE USER, YOU MUST:**

1. **Stage all changed files in git** — `git add` so the user can see the full diff:
   - Source file changes (`.cpp`, `.py`, `.md`, etc.)
   - Pipeline output (bundles in `custom_songs/`)
   - Documentation updates
   - New memory/knowledge-base files

2. **Update all documentation** in this order:
   - `experiment_log.md` — new entry for this experiment
   - `song_testing_log.md` — if testing a new song
   - Project summary docs (see `project-summary-update-rule.md` for full list)
   - Knowledge base (if new findings affect durable knowledge)

3. **Present a clear summary** to the user with:
   - What changed and why
   - What was deployed (plugin version, bundle, audio format, song)
   - What the user should expect to see on PS4
   - Where to find logs afterward (`bs_log.txt` via FTP)
   - What specific test to perform (e.g., "launch Beat Saber, play Start Me Up, check sync")

### Phase E: User Test

The user will:
1. Launch Beat Saber on PS4
2. Play the target song
3. Report results (crashes, sync quality, visual issues, notification text)
4. The user will use my summary + their response as the commit message

### Phase F: Analyze Results

1. **Download the PS4 log**:
   ```bash
   lftp -u anonymous, -p 2121 192.168.100.117 \
     -e "get /data/GoldHEN/AFR/CUSA12878/bs_log.txt -o /tmp/bs_log_v<version>.txt; quit"
   ```
2. **Analyze** the log for:
   - Total line count (~150 = quick menu, ~750+ = full song play)
   - Redirect count (`BeatmapLevelsData/startmeup -> ...`)
   - Error lines (grep for `error`, `exception`, `fail`, `crash`)
   - PlayerData.dat save (indicates clean exit)
   - Notification confirmation line
3. **Save a copy**: `cp /tmp/bs_log_v<version>.txt /workspace/screenshots/`
4. **Update docs** with findings

### Phase G: Iterate

- Based on results, either deploy a fix or move to the next task
- The user and agent agree on next steps
- Repeat from Phase A

---

## 4. Building the Plugin

### Prerequisites
- OpenOrbis PS4 Toolchain at `/opt/openorbis/OpenOrbis/PS4Toolchain`
- GoldHEN Plugin SDK headers at `${TOOLCHAIN}/include/GoldHEN/`
- `OO_PS4_TOOLCHAIN` env var set

### Build Commands

```bash
# Release build (no verbose logging — fast, production)
export OO_PS4_TOOLCHAIN=/opt/openorbis/OpenOrbis/PS4Toolchain
make clean && rm -rf obj && make -B
# Output: beat_saber_deluxe.prx

# Debug build (verbose logging on PS4, for development)
make clean && rm -rf obj && DEBUG=1 make -B
# Output: beat_saber_deluxe_debug.prx
```

### Key Build Details
- **Target:** `--target=x86_64-pc-freebsd12-elf` (MUST match PS4's FreeBSD kernel)
- **Entry point:** `-e _init` (GoldHEN calls `_init`, not `module_start`)
- **CRT:** `crtprx.o` from GoldHEN SDK
- **Linker:** `ld.lld` with script `link.x`
- **Format:** FSELF (`create-fself --lib`, SCE magic `4f 15 3d 1d`)
- **Paid:** `0x3800000000000011`
- **Libraries:** `-lGoldHEN_Hook -lSceLibcInternal -lkernel`
- **Avoid:** `-lc`, `-lc++` (pull in musl TLS which PS4 rejects)

### Verify Build
```bash
# Check SCE magic (must be FSELF)
xxd beat_saber_deluxe.prx | head -1
# Should show: 4f 15 3d 1d

# Check entry point
readelf -h obj/beat_saber_deluxe.elf | grep Entry
# Should show: _init

# Check no TLS segment
readelf -l obj/beat_saber_deluxe.elf | grep TLS
# Should be empty
```

---

## 5. Running the Pipeline

### Full song conversion (PCM16 FSB5, lossless, no padding)
```bash
cd /workspace/beat_saber_deluxe
python3 tools/full_custom_song_pipeline.py \
  --song-dir ./custom_songs/espresso_prepped \
  --target startmeup \
  --pcm16 \
  --no-pad
```

### With deploy to PS4
```bash
python3 tools/full_custom_song_pipeline.py \
  --song-dir ./custom_songs/espresso_prepped \
  --target startmeup \
  --pcm16 \
  --no-pad \
  --deploy
```

### Key Parameters
| Flag | Purpose |
|------|---------|
| `--song-dir` | Path to song folder (contains audio + .dat/.json beatmaps) |
| `--target` | Which official song to hijack (e.g., `startmeup`) |
| `--pcm16` | Use PCM16 codec (lossless, recommended) |
| `--no-pad` | Don't pad FSB5 to 12MB (PCM16 doesn't need it) |
| `--deploy` | Upload bundle to PS4 via FTP |
| `--deploy-plugin` | Build + deploy plugin (release by default) |
| `--debug-logging` | Build plugin with verbose PS4 logging |
| `--ignore-non-standard-beatmaps` | Only use Standard difficulty beatmaps |
| `--preserve-metadata` | Don't update AudioClip/audio.gz metadata |
| `--audio` | Pre-encoded FSB5 file (skip audio conversion) |

---

## 6. Song Selection Criteria

A song MUST have Easy, Normal, and Hard difficulties with one of these beatmap types:
- **Standard** ✅ (best choice — works perfectly)
- **90Degree** ✅ (acceptable — limited angle)
- **OneSaber** ✅ (acceptable)

**AVOID:**
- **360Degree** ❌ (maps load but unplayable on PS4 VR — single camera can't track behind-player notes)
- Songs missing any of Easy/Normal/Hard (base game expects all 3)
- Expert-only songs (may crash if game expects easier diffs)

---

## 7. Debug Logging (Plugin)

### How it works
- Plugin `main.cpp` wraps per-file-access logging in `#ifdef VERBOSE_LOG`
- Release build: `make` → `VERBOSE_LOG` NOT defined → no per-file logs, only startup notification
- Debug build: `make DEBUG=1` → `-DVERBOSE_LOG` → every `open()`/`fopen()` call is logged to `bs_log.txt`

### What gets logged in each mode
| Log line | Release | Debug |
|----------|---------|-------|
| "=== BS Deluxe vX.XX started ===" | ✅ | ✅ |
| "vX.XX: description" | ✅ | ✅ |
| "hooks installed" | ✅ | ✅ |
| PS4 notification | ✅ | ✅ |
| `open:/some/path` | — | ✅ |
| `open:/some/path -> /data/GoldHEN/AFR/...` | — | ✅ |
| `fopen:/some/path` | — | ✅ |

### When to use each
- **Debug logging** (`--debug-logging`): during development to trace file opens, verify redirects, debug crashes
- **Release logging** (default): final deployments — only essential startup/reference messages, no runtime overhead

---

## 8. Important Constraints & Gotchas

### PS4
- **FTP is read-only** for game directories (`/app0/`, `/patch0/`)
- **AFR path** (`/data/GoldHEN/AFR/CUSA12878/`) is writeable — used for logs and asset bundles
- **No reboot needed** for plugin updates — GoldHEN re-reads on game launch
- **Jailbreak in plugin** destabilizes the game process — DON'T use it
- **`fopen`/`fprintf` crashes** in `module_start` — use `sceKernelOpen`/`sceKernelWrite` instead

### Audio
- **PCM16 FSB5 (codec=2)** is the only confirmed working format — lossless, bit-identical
- **HEVAG encoder** produces garbage (lacks Sony's proprietary coefficient table for predictors 5-15)
- **Vorbis FSB5** codec mismatch between libvorbis and FMOD's Vorbis decoder
- **No padding needed** for PCM16 (`--no-pad`)

### Sync
- BeatSaver beatmaps are **V2 format** — `_time` is in **BEATS**, not seconds
- Pipeline converts to V3 and corrects bpmData
- **bpmData `eb` field MUST be in beats** (NOT seconds) — this was root cause of desync in v0.49
- BPMInfo.dat (BeatSaver) is preferred for bpmData; fallback computes from `_beatsPerMinute`

### Pipeline
- `.egg` files are renamed OGG Vorbis — auto-detected
- Audio normalization prevents OGG encoder overshoot crackling
- Lapped audio (overlapping beats) is detected and extended automatically

### Documentation
- **Always stage files** before presenting to user
- **Always update docs** before reporting
- Summary + user response = future commit message
- Every experiment gets an entry in `experiment_log.md`

---

## 9. Commit Convention

The user uses the pattern: my summary + their response = commit message.

Example commit message:
```
v0.50: Fixed bpmData sync (beats not seconds)

Root cause: update_audio_gz() set eb to duration (seconds) instead
of beats. At 120 BPM this halved the tempo, causing progressive
desync. Fixed by reading BPMInfo.dat regions or computing
total_beats = duration * bpm / 60.0.

Deployed: Espresso (104 BPM, 177.5s, Standard E/N/H/Ex/Ex+)
```

---

## 10. Quick Reference Commands

```bash
# Build plugin (release)
cd /workspace/beat_saber_deluxe
export OO_PS4_TOOLCHAIN=/opt/openorbis/OpenOrbis/PS4Toolchain
make clean && rm -rf obj && make -B

# Build plugin (debug)
make clean && rm -rf obj && DEBUG=1 make -B

# Run pipeline for Espresso with deploy
python3 tools/full_custom_song_pipeline.py \
  --song-dir ./custom_songs/espresso_prepped \
  --target startmeup --pcm16 --no-pad --deploy

# Run pipeline with plugin deploy (debug mode)
python3 tools/full_custom_song_pipeline.py \
  --song-dir ./custom_songs/espresso_prepped \
  --target startmeup --pcm16 --no-pad --deploy \
  --deploy-plugin --debug-logging

# Download PS4 log
lftp -u anonymous, -p 2121 192.168.100.117 \
  -e "get /data/GoldHEN/AFR/CUSA12878/bs_log.txt -o /tmp/bs_log.txt; quit"

# Browse PS4 filesystem
lftp -u anonymous, -p 2121 192.168.100.117 \
  -e "ls /data/GoldHEN/AFR/CUSA12878/; quit"
```
