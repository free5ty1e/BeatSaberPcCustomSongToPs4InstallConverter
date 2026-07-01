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
- [[m-script-gzip-format|m_Script = Just Gzip]] — The critical format of beatmap data storage (no decompressed_size prefix!)
- [[unitypy-serialization|UnityPy Serialization]] — save_typetree vs set_raw_data, surrogateescape encoding

## Beatmap Formats & Conversion
- [[beatmap-format-v3|PS4 Beatmap Format (V3)]] — colorNotes + colorNotesData, obstaclesData, all V3 structures
- [[beatmap-conversion-pipeline|Beatmap Conversion Pipeline]] — V2→V3 conversion process for notes, obstacles, bombs, chains, arcs

## Tooling & Workflow
- [[toolchain-and-build|PS4 Toolchain & Build System]] — OpenOrbis toolchain, make, create-fself
- [[development-workflow|Development Workflow]] — Deploy cycle, log analysis, FTP, experiment iteration

## Audio & Future Work
- [[ps4-fsb5-audio|PS4 FSB5 Audio Format]] — Audio format analysis, FSB5 structure (for future replacement)

## Key Root Causes Found
- [[m-script-gzip-format|m_Script = Just Gzip]] — The blocker: was adding decompressed_size prefix before gzip
- [[unitypy-serialization|save_typetree vs set_raw_data]] — set_raw_data causes serialization bugs for 3/5 objects
- [[surrogateescape-encoding|Surrogateescape Encoding]] — latin-1 + utf-8 = corrupted binary data
