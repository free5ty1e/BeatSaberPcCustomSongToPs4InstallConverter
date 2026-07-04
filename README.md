# Beat Saber PS4 Custom Song Support Project

- **[beat-saber-ps4-custom-songs/README.md](./beat-saber-ps4-custom-songs/README.md)** - Main project documentation
- **[beat-saber-ps4-custom-songs/PROGRESS.md](./beat-saber-ps4-custom-songs/PROGRESS.md)** - Development progress

## What Do?

Pipeline to convert custom Beat Saber PC songs into installable PS4 packages compatible with the PS4 Beat Saber VR game, to show up as custom playable songs in-game directly on the PS4

## Status

🚀 **PATH TO VICTORY FOUND!** 
We have verified that the AssetBundle building process is correct. The "audio freeze" was isolated to the HEVAG encoding fidelity. The PS4 hardware decoder requires a wider coefficient range (0-15) and shift range (0-15) than standard HEVAG encoders provide. 

**Current Goal:** Implement high-fidelity HEVAG encoding to support community custom songs.

### Current Capabilities
- ✅ Plugin loads and redirects song files to custom AssetBundles
- ✅ Beatmap data replacement with V3 format conversion (including notes, bombs, walls, arcs, and chains)
- ✅ AssetBundle structure verified (UnityFS format, CAB + .resource)
- ✅ AudioClip and audio.gz metadata automation

### In Progress
- 🔄 **Full Pipeline Automation:** End-to-end conversion from `.json`/`.ogg`/`.wav` to deployed PS4 bundle. Pipeline now supports `.ogg` audio (standard BeatSaver format) via `soundfile` integration.
- 🔄 **PS4 Audio Compatibility:** Testing predictor-0 HEVAG encoder with 12MB padded FSB5 to ensure the decoder stays stable.

## Getting Started
...
