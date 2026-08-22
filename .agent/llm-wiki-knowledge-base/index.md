---
name: index
description: "Content catalog of the Beat Saber Deluxe LLM Wiki knowledge base"
metadata:
  type: index
---

# Beat Saber Deluxe — LLM Wiki Knowledge Base

> Durable, compiled knowledge about the Beat Saber PS4 Custom Song Support project.

## Architecture & Plugin System
- [[plugin-architecture|Plugin Architecture]] — GoldHEN plugin, hook system, PRX format, CRT initialization
- [[ps4-file-system-redirects|PS4 File System & Redirects]] — AFR directory vs plugins directory, open() hook, permissions model
- [[ps4-memory-layout-for-module-scanning|PS4 Memory Layout for Module Scanning]] — Where modules (~2GB) and IL2CPP heap (~8-16GB) live, bounds check lessons
- [[ps4-il2cpp-metadata-loading|PS4 IL2CPP Metadata Loading]] — Class name strings live in global-metadata.dat, NOT in compiled module PRX
- [[feature-flags|Feature Flags]] — `features.json` configuration: `enable_custom_song_replacements`, `enable_song_metadata_modification`, `enable_beatmap_mode_mapping`

## AssetBundle & Unity Serialization
- [[assetbundle-structure|AssetBundle Structure]] — Unity SerializedFile format, object table, TextAsset
- [[pack-bundle-patching|Pack Bundle Patching (CRC Correction Achieved)]] — Exp 142 CRC correction via GF(2) linear algebra. Padding bytes adjusted to match original CRC (0xdc8b314f). All prior failed approaches documented. LZ4HC requirement, CAB format, m_Script PPtr fix. Includes Exp 188-191: generalized pack patch, m_EntryDataString dataIndex shifting, 360Degree reproducibility, and "verify catalog CONTENT not size" (stale-catalog lesson).
- [[unitypy-serialization|UnityPy Serialization]] — save_typetree vs set_raw_data, surrogateescape encoding
- [[unityfs-v8-bundle-layout|UnityFS v8 Bundle Layout]] — UnityFS bundle header format, compression flags, block metadata

## Beatmap Formats, Conversion & Sync
- [[beatmap-format-v3|PS4 Beatmap Format (V3)]] — colorNotes + colorNotesData, obstaclesData, all V3 structures
- [[beatmap-conversion-pipeline|Beatmap Conversion Pipeline]] — V2→V3 conversion, .egg (OGG) handling, audio normalization, --no-pad for long songs
- [[beatmap-audio-sync|Beatmap ↔ Audio Sync]] — bpmData structure, eb must be in beats not seconds, BPMInfo.dat, sync root cause
- [[beatmap-filename-conventions|Beatmap Filename Conventions]] — All BeatSaver naming patterns (Standard, bare, .beatmap.dat, 90Degree, OneSaber, 360Degree) and 5-tier pipeline selection priority

## Tooling & Workflow
- [[toolchain-and-build|PS4 Toolchain & Build System]] — OpenOrbis toolchain, make, create-fself
- [[development-workflow|Development Workflow]] — Deploy cycle, log analysis, FTP, experiment iteration

## Audio — Working Format
- [[ps4-fsb5-pcm16-format|PS4 FSB5 PCM16 Format]] — ✅ **WORKING** — Recommended audio format (codec=2, lossless, no padding required)

## Audio — Blocked/Historical Approaches
- [[ps4-fsb5-vorbis|PS4 FSB5 Vorbis]] — ❌ Blocked (FMOD/libvorbis codebook mismatch)
- [[ps4-hevag-fsb5-audio|PS4 HEVAG + FSB5 Audio Format]] — ❌ Blocked (Sony proprietary coefficient table for predictors 5-15)
- [[ps4-fsb5-audio|PS4 FSB5 Audio Format (Hub)]] — Hub page redirecting to correct format
- [[ps4-audio-decoder-behavior|PS4 Audio Decoder Behavior]] — 📜 Historical: HEVAG-era freeze analysis (resolved by PCM16)
- [[encoder-decoder-inconsistency|HEVAG Encoder/Decoder Inconsistency]] — 📜 Historical: HEVAG bug analysis (resolved by PCM16)
- [[fsb5-padding-required|FSB5 Padding Required]] — 📜 Historical: 12MB padding "requirement" (was HEVAG artifact)

## Song Metadata & Database
- [[song-metadata-storage|Song Metadata Storage]] — How song names, artists, mappers, BPM, difficulties, and audio are stored in resources.assets, per-song bundles, and Addressables packs
- [[song-metadata-addressables-structure|Song Metadata & Addressables Structure (incl. CRC Blocker)]] — Addressables catalog, BeatmapLevel vs BeatmapLevelSO hierarchy, characteristic modes, **CRC validation discovery (Exp 136)**, IL2CPP hook targets (all dead)
- [[il2cpp-dump-mode-selector-hook|IL2CPP Dump & Mode Selector Hook]] — BeatmapLevelSO class layout, get_previewDifficultyBeatmapSets at RVA 0x988E80, field offsets, hook implementation plan
- [[structural-beatmaplevelso-scan|Structural BeatmapLevelSO Scan]] — 🔵 **CURRENT (v0.8047+)** — Find/patch BeatmapLevelSO in RAM via structural signature (klass range + version + string ptrs + preview array). Signal-free reads via `sceKernelQueryMemoryProtection` (v0.8043/44 crash: process-wide SIGSEGV handlers hijacked Unity GC page-protection faults during song-list render). Scan 16MB-64GB@1MB; System.String len_14 pitfall; v0.8046 finding: candidates at 0x1C2-0x1D5xxxxx are pack-bundle data (fixed v0.8047 with v0.77 pointer window [16MB,512GB] + arr-failure stage breakdown).
- [[ps4-environment-system|PS4 Environment System]] — How the game maps songs to environments via the Addressable song database
- [[supported-songs|Supported Songs]] — Catalog of official and custom songs
- [[addressables-crc-validation-timing|Addressables CRC Validation Timing]] — When CRC validation happens (lazy vs eager)

## Song Metadata Modification (Current Approach)
- [[textmeshpro-ui-hooking|TextMeshPro UI Hooking]] — 🔵 **CURRENT** — Hook TMP_Text.set_text to intercept song name/artist text in UI. Pointer tracking via SetDataFromLevelAsync.
- [[memory-injection-addressables-bypass|Memory Injection — Addressables Bypass]] — 🔴 **DEAD END** (v0.66–v0.8024): Patch BeatmapLevelSO in RAM. 14+ versions, 0 strings found across all memory regions. Preserved for historical reference.
- [[camellia-pack-replacement|Camellia Pack Replacement]] — First full pack replacement (6 songs). PCM16 requirement confirmed, metadata behavior documented, required flags established.

## Key Root Causes Found
- [[m-script-gzip-format|m_Script = Just Gzip]] — The blocker: was adding decompressed_size prefix before gzip
- [[unitypy-serialization|save_typetree vs set_raw_data]] — set_raw_data causes serialization bugs for 3/5 objects
- [[surrogateescape-encoding|Surrogateescape Encoding]] — latin-1 + utf-8 = corrupted binary data
- [[note-color-field-version-differences|Note Color Field Version Differences]] — V2 uses `a`, V3 uses `c` for note color field

## Pipeline Tooling
- [[pipeline-plugin-toggle-cli-flags|Pipeline Plugin Toggle CLI Flags]] — `--enable-plugin`/`--disable-plugin` flags for toggling the Beat Saber Deluxe plugin on PS4 without rebuilding files. Tested and verified live on console.
- [[pipeline-song-metadata-blob-injection|BeatmapLevelSO Metadata Blob Injection & CAB Binary Patching]] — Blob builder + raw binary CAB replacement at verified offset 79924. Patched CABs generated for Espresso(1257B), Duvet(1222B), Time Lapse(1251B). Size delta handled by extending CAB file. deploy path: AFR redirect or direct bundle patching (NOT UnityPy save_bundle — crashes with CE-34878-0 per Exp 116).
- [[procedural-mode-generators|Procedural Mode Generators]] — v0.5310 non-mutating generators for OneSaber/NoArrows/90Degree; default gap-filling in Step 5a under `--enable-beatmap-mode-mapping`; never overwrites songs' own mode files.
- [[saber-colors-and-one-saber|Saber Colors & OneSaber Convention]] — LEFT=Red, RIGHT=Blue; OneSaber is RIGHT/blue only (red OneSaber maps are unplayable).

## Plans
- [[plans/song-list-modes|Song List & Mode Control Plan]] — Implementation plan for showing custom names/artists in song list and enabling OneSaber/90Degree modes in custom bundles. Updated with Exp 129 findings: typetree approach dead-end, blob format verified via hex dump against StartMeUp.

## Feature Documentation
- `beat_saber_deluxe/docs/features/custom-song-replacement.md` — Custom Song Replacement: `open()` hook file redirection, `redirects.json` config, AFR deploy path, and AssetBundle naming.
- `beat_saber_deluxe/docs/features/song-metadata-modification.md` — Song Metadata Modification: MoveNext() hook, `song_metadata.json`, `beat_saber_song_ids.json` case sensitivity, and TMP_Text replacement.
