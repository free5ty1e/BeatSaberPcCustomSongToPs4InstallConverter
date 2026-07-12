---
name: development-workflow
description: "End-to-end development cycle: edit, build, deploy, test, log analyze, document"
metadata:
  type: concept
---

# Development Workflow

## One Development Cycle

Each iteration follows this sequence:

```
1.  Edit plugin source (main.cpp), redirect config (redirects.json), or pipeline
2.  Build plugin (make clean && rm -rf obj && make -B)
3.  Build custom bundle (python3 tools/full_custom_song_pipeline.py)
4.  Deploy plugin + bundle + config (deploy_all.sh or pipeline --deploy flags)
5.  Test on PS4 (launch game, select song)
6.  Download log (lftp get bs_log.txt)
7.  Analyze log (redirects, env loading, errors, PlayerData)
8.  Document results (experiment_log.md, project_summary.md, roadmap.md)
9.  Stage in git
```

## Redirect Config Management

The redirect table is no longer hardcoded. The plugin reads `redirects.json` from the AFR path at startup.

### Adding a New Song Slot
```bash
python3 tools/full_custom_song_pipeline.py \
  --song-dir ./my_song \
  --target newslot \
  --pcm16 --no-pad --convert-to-v3 \
  --generate-config --deploy --deploy-config
```

This builds the bundle, adds the `newslot → newslot_custom_v3` mapping to `redirects.json`, deploys both to PS4.

### Syncing Config from PS4
When you've made changes directly on the PS4 (via FTP) and want to merge them locally:
```bash
python3 tools/full_custom_song_pipeline.py \
  --song-dir ./my_song --target startmeup \
  --sync-config
```
This downloads the PS4 config, merges with local changes, saves, and redeploys.

### Enforcing Local Config
To overwrite the PS4 config with your local version:
```bash
python3 tools/full_custom_song_pipeline.py --enforce-config --deploy
```

## FTP Deployment Commands

### Deploy plugin
```bash
lftp -u anonymous, -p 2121 192.168.100.117 -e "
  put beat_saber_deluxe.prx -o /data/GoldHEN/plugins/beat_saber_deluxe.prx
  quit"
```

### Deploy custom bundle
```bash
lftp -u anonymous, -p 2121 192.168.100.117 -e "
  put custom_song.bundle -o /data/GoldHEN/AFR/CUSA12878/startmeup_v3
  quit"
```

### Download log
```bash
lftp -u anonymous, -p 2121 192.168.100.117 -e "
  get /data/GoldHEN/AFR/CUSA12878/bs_log.txt -o /tmp/bs_log.txt
  quit"
```

## Log Analysis Signals

| Signal | Meaning |
|--------|---------|
| Redirect count (2) | Game opened bundle twice (standard) |
| Environment bundles loaded after redirect | Environment rendering correctly |
| PlayerData.dat saved | Clean menu return |
| Error/exception lines | Game crash or assertion failure |
| < 150 total lines | Quick menu only (song didn't start) |
| 750+ total lines | Full song play cycle |
| `v0.NN` version log line | Confirms which plugin version loaded |

## Pipeline Usage

### From song directory (including .egg audio files)
```bash
python3 tools/full_custom_song_pipeline.py \
  --song-dir ./my_song \
  --target startmeup \
  --pcm16 \
  [--no-pad] \
  [--deploy]
```

- `.egg` files are auto-detected as audio (renamed OGG Vorbis from BeatSaver)
- Audio is automatically normalized (OGG overshoot samples outside [-1,1] are scaled down)
- `--no-pad`: required for songs longer than the target's original resource (~70s for startmeup)

### Pipeline Steps
1. Load template bundle from PS4 dump: `/workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/startmeup`
2. Load custom song from BeatSaver directory (auto-detects .egg/.wav/.ogg audio)
3. Normalize audio (float32 read → scale to 0.99 peak → int16 conversion)
4. Convert V2 notes → V3 format (colorNotes + colorNotesData)
5. Insert into template (preserving structure)
6. Gzip compress and write via save_typetree with surrogateescape
7. Save to `custom_songs/<name>.bundle`
8. FTP to PS4

## PS4 Test Procedure

1. Launch PS4 main menu
2. Launch Beat Saber
3. Watch for notification: "BS Deluxe v<N>"
4. Navigate to Start Me Up (or whatever song is redirected)
5. Select song and difficulty
6. Observe: notification text, background rendering, notes, audio
7. Press PS button to exit if game crashes
8. Return to main menu (game saves PlayerData.dat)
9. Download log via FTP

## Documentation Requirements
Every cycle must update:
1. `experiment_log.md` — New experiment entry with log findings
2. `project_summary.md` — Status header
3. `roadmap.md` — Milestone checklists
4. `README.md` — Public-facing status
5. Knowledge base if root cause was found
6. Stage all changes in git

See also: [[plugin-architecture]], [[toolchain-and-build]], [[ps4-file-system-redirects]], [[beatmap-conversion-pipeline]]
