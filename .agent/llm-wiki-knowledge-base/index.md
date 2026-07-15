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
- [[ps4-file-system-redirects|PS4 File System & Redirects]] — AFR directory, open() hook, permissions model

## AssetBundle & Unity Serialization
- [[assetbundle-structure|AssetBundle Structure]] — Unity SerializedFile format, object table, TextAsset
- [[pack-bundle-patching|Pack Bundle Patching via UnityPy save()]] — How to patch UnityFS pack bundles: `bf.save("original")` breakthrough, 5-mode mode selector, m_Script PPtr bug fix
- [[unitypy-serialization|UnityPy Serialization]] — save_typetree vs set_raw_data, surrogateescape encoding

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
- [[song-metadata-addressables-structure|Song Metadata & Addressables Structure]] — Addressables catalog, BeatmapLevel vs BeatmapLevelSO hierarchy, characteristic modes, IL2CPP hook targets
- [[il2cpp-dump-mode-selector-hook|IL2CPP Dump & Mode Selector Hook]] — BeatmapLevelSO class layout, get_previewDifficultyBeatmapSets at RVA 0x988E80, field offsets, hook implementation plan
- [[ps4-environment-system|PS4 Environment System]] — How the game maps songs to environments via the Addressable song database

## Key Root Causes Found
- [[m-script-gzip-format|m_Script = Just Gzip]] — The blocker: was adding decompressed_size prefix before gzip
- [[unitypy-serialization|save_typetree vs set_raw_data]] — set_raw_data causes serialization bugs for 3/5 objects
- [[surrogateescape-encoding|Surrogateescape Encoding]] — latin-1 + utf-8 = corrupted binary data

## Pipeline Tooling
- [[pipeline-plugin-toggle-cli-flags|Pipeline Plugin Toggle CLI Flags]] — `--enable-plugin`/`--disable-plugin` flags for toggling the Beat Saber Deluxe plugin on PS4 without rebuilding files. Tested and verified live on console.
- [[pipeline-song-metadata-blob-injection|BeatmapLevelSO Metadata Blob Injection & CAB Binary Patching]] — Blob builder + raw binary CAB replacement at verified offset 79924. Patched CABs generated for Espresso(1257B), Duvet(1222B), Time Lapse(1251B). Size delta handled by extending CAB file. deploy path: AFR redirect or direct bundle patching (NOT UnityPy save_bundle — crashes with CE-34878-0 per Exp 116).

## Plans
- [[plans/song-list-modes|Song List & Mode Control Plan]] — Implementation plan for showing custom names/artists in song list and enabling OneSaber/90Degree modes in custom bundles. Updated with Exp 129 findings: typetree approach dead-end, blob format verified via hex dump against StartMeUp.
