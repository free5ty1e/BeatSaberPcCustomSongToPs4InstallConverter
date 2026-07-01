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
1.  Edit plugin source (main.cpp) or conversion script (convert_song_v3.py)
2.  Build plugin (make clean && rm -rf obj && make -B)
3.  Build custom bundle (python3 convert_song_v3.py)
4.  Deploy plugin (lftp put beat_saber_deluxe.prx)
5.  Deploy bundle (lftp put custom_song.bundle)
6.  Test on PS4 (launch game, select song)
7.  Download log (lftp get bs_log.txt)
8.  Analyze log (redirects, env loading, errors, PlayerData)
9.  Document results (experiment_log.md, project_summary.md, roadmap.md)
10. Stage in git
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

## Bundle Build Process

1. Load template bundle from PS4 dump: `/workspace/ps4_dump/CUSA12878-patch/Media/StreamingAssets/BeatmapLevelsData/startmeup`
2. Load custom song from BeatSaver directory
3. Convert V2 notes → V3 format (colorNotes + colorNotesData)
4. Insert into template (preserving structure)
5. Gzip compress and write via save_typetree with surrogateescape
6. Save to `custom_songs/<name>.bundle`
7. FTP to PS4

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
