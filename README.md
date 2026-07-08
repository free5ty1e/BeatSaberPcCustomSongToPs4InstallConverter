# Beat Saber PS4 Custom Song Support Project

- **[beat-saber-ps4-custom-songs/README.md](./beat-saber-ps4-custom-songs/README.md)** - Main project documentation
- **[beat-saber-ps4-custom-songs/PROGRESS.md](./beat-saber-ps4-custom-songs/PROGRESS.md)** - Development progress

## What Do?

Pipeline to convert custom Beat Saber PC songs into installable PS4 packages compatible with the PS4 Beat Saber VR game, to show up as custom playable songs in-game directly on the PS4

## Status

🏆 **v0.50 ALPHA — Full song plays, score saves, bpmData sync fixed!**

PCM16 FSB5 confirmed working — lossless audio, bit-identical, any song length (`--no-pad`). Plugin uses GoldHEN AFR writeable path for logs and asset bundles. 306 official songs cataloged.

### Current Capabilities
- ✅ Plugin loads and redirects song files to custom AssetBundles (FSELF format)
- ✅ PCM16 FSB5 (codec=2) audio — lossless, confirmed working end-to-end
- ✅ bpmData sync fixed (beats not seconds — root cause of progressive desync)
- ✅ Beatmap data replacement with V3 format conversion (notes, bombs, walls, arcs, chains)
- ✅ AudioClip and audio.gz metadata automation
- ✅ Lapped audio detection and extended audio generation
- ✅ GoldHEN AFR logging (no jailbreak needed, no crashes)
- ✅ Debug/release plugin builds (verbose PS4 logging behind `#ifdef VERBOSE_LOG`)
- ✅ Pipeline has `--deploy-plugin` + `--debug-logging` for full iteration cycle
- ✅ `plugins.ini` idempotent management (reads existing, preserves other plugins)

### Known Issues
- HEVAG encoder produces garbage (lacks Sony's proprietary coefficient table)
- Vorbis FSB5 codec mismatch (libvorbis vs FMOD codebook incompatibility)
- 360-degree beatmaps unplayable on PS4 VR (single camera ~90-degree tracking arc)

## Getting Started

### Build the plugin
```bash
cd beat_saber_deluxe
export OO_PS4_TOOLCHAIN=/opt/openorbis/OpenOrbis/PS4Toolchain
# Release (no verbose PS4 logging):
make clean && rm -rf obj && make -B
# Debug (verbose PS4 logging for development):
make clean && rm -rf obj && DEBUG=1 make -B
```

### Run the pipeline
```bash
cd beat_saber_deluxe
# Convert song + build bundle + deploy to PS4
python3 tools/full_custom_song_pipeline.py \
  --song-dir ./custom_songs/espresso_prepped \
  --target startmeup --pcm16 --no-pad --deploy

# Same, but also build + deploy plugin with verbose logging
python3 tools/full_custom_song_pipeline.py \
  --song-dir ./custom_songs/espresso_prepped \
  --target startmeup --pcm16 --no-pad --deploy \
  --deploy-plugin --debug-logging
```

### Deploy a song to PS4
The pipeline handles bundle deployment (`--deploy`) and plugin deployment (`--deploy-plugin`), including idempotent `plugins.ini` management.

### Download PS4 logs
```bash
lftp -u anonymous, -p 2121 192.168.100.117 \
  -e "get /data/GoldHEN/AFR/CUSA12878/bs_log.txt -o /tmp/bs_log.txt; quit"
```

For full workflow details, see `.ai_memory/experiment-workflow.md`.
