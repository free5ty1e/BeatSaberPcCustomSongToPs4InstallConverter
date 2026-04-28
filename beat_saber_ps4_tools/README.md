# Beat Saber PS4 Custom Songs - PC Tools

## Overview

Python tools for converting PC BeatSaver custom songs to PlayStation 4 format and installing them via FTP.

**Status**: Initial development - requires PS4 plugin to fully work.

## Requirements

- Python 3.8+
- `requests` library (`pip install requests`)
- PS4 with GoldHEN jailbreak
- FTP enabled on PS4

## Tools

### 1. Song Converter (`converter/song_converter.py`)

Converts PC BeatSaver songs to PS4 binary format.

```bash
# Convert a single song folder
python3 converter/song_converter.py /path/to/BeatSaverSong

# Batch convert all songs in a folder
python3 converter/song_converter.py --list /path/to/songs

# Specify output directory
python3 converter/song_converter.py /path/to/song --output output_folder
```

### 2. Song Downloader (`converter/downloader.py`)

Downloads songs directly from BeatSaver API.

```bash
# Download by BeatSaver key
python3 converter/downloader.py abc12

# Search for songs
python3 converter/downloader.py --search "imagine dragons"

# Get hot songs
python3 converter/downloader.py --hot --count 10

# Get latest songs
python3 converter/downloader.py --latest --count 20
```

### 3. PS4 Installer (`converter/ps4_installer.py`)

Uploads converted songs to PS4 via FTP.

```bash
# Upload converted songs to PS4
python3 converter/ps4_installer.py --upload converted_songs/ --ps4 192.168.100.117

# Initialize folder structure on PS4
python3 converter/ps4_installer.py --init

# List songs already on PS4
python3 converter/ps4_installer.py --list

# Install a plugin
python3 converter/ps4_installer.py --plugin BeatSaber-Plugin.prx
```

## Complete Workflow

```bash
# 1. Download songs from BeatSaver
python3 converter/downloader.py --hot --count 5 --output songs/

# 2. Convert to PS4 format
python3 converter/song_converter.py --list songs/ --output converted/

# 3. Upload to PS4
python3 converter/ps4_installer.py --upload converted/ --ps4 192.168.100.117 --init
```

## Architecture

```
PC Side:                              PS4 Side:
────────                              ────────
BeatSaver API                          GoldHEN Plugin
     ↓                                      
Download song (.zip)                   Hooks:
     ↓                                    - Unity AssetBundle loading
Extract → info.dat + audio + cover      - FMOD audio loading
     ↓                                    - Beatmap parsing
Song Converter                          - File system redirects
     ↓                                   
PS4 Binary Format              ←→     /user/data/GoldHEN/BeatSaber/songs/
     ↓                                        
PS4 Installer (FTP)                             ↓
     ↓                                    Beat Saber Game (Runtime)
Upload to PS4                                 ↓
                                    Custom Songs Loaded!
```

## File Format Notes

### PC Format (BeatSaver)
- `info.dat` / `info.json` - Song metadata
- `*.dat` (JSON) - Difficulty beatmaps
- `*.ogg` - Audio
- `*.png` / `*.jpg` - Cover art

### PS4 Binary Format
Based on Backporter's converter (2021):
- `Info.dat` - Binary song metadata
- `*.dat` (binary) - Difficulty beatmaps
- Audio format TBD (needs Unity asset bundle creation)
- Cover image format TBD

## Known Limitations

1. **Audio Conversion**: Full audio conversion requires Unity asset bundle creation with UABE
2. **PS4 Plugin**: A GoldHEN plugin is needed to intercept game file loading
3. **Beatmap Format**: PS4 binary format is partially documented; more reverse engineering needed

## References

- [Backporter PS4-Beat-Saber-Converter](https://github.com/Backporter/PS4-Beat-Saber-Converter) - Original converter
- [BeatSaberSongLoader](https://github.com/Kylemc1413/BeatSaberSongLoader) - PC mod loader reference
- [BeatSaber Level Format](https://gist.github.com/MCJack123/892b936ef0d18da43ab2764ba97402be) - Format documentation
- [GoldHEN Plugin SDK](https://github.com/GoldHEN/GoldHEN_Plugins_Repository) - PS4 plugin development

## License

MIT License - Use freely, no warranty provided.