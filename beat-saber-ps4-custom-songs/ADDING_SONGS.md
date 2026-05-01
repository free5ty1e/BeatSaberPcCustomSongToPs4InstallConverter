# Adding New Songs to Beat Saber PS4

## Overview

The current approach builds one monolithic custom songs package from all songs in the `songs_repo/` folder. To add new songs:

## Process

### 1. Add New Songs to Repository
Download new songs from BeatSaver and add them to `songs_repo/`:
```
songs_repo/
├── existing_song_1/
├── existing_song_2/
└── new_song_to_add/
```

### 2. Rebuild the PKGs
Run the pipeline to regenerate all PKGs with the new song count:
```bash
cd beat-saber-ps4-custom-songs
python3 pipeline.py --clean
```

This will:
- Generate new PKGs with ALL songs (old + new)
- Update `windows_build/Project.gp4` with new song entries

### 3. Re-install on PS4
1. Uninstall the existing custom songs DLC (if installed)
2. Install the new unlocker (v2 or v3)
3. Install the new custom songs PKG

**Important:** You must uninstall and reinstall - updating over existing doesn't work reliably.

## Why Monolithic?

The current implementation builds one single PKG containing ALL songs. This is simpler but requires:
- Reinstalling all songs when adding new ones
- Fixed difficulty mapping (all songs include Easy through Expert to satisfy your friend's Medium/Easy requirement)

## Future Improvements (If This Works)

Once we debug the CE-36426-1 error, consider:
- Separate smaller song packs (e.g., by genre or difficulty)
- Incremental updates instead of full reinstall
- Multiple content IDs for different song groupings

## Song Repository

The pipeline reads from `songs_repo/` folder. Any new songs added there will be included in the next build.

## Last Updated
2026-04-30