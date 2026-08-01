# Memory Index

## 📋 Master Index
- [Research Index](RESEARCH_INDEX.md) — **START HERE.** Comprehensive catalog of all project documents, status, and quick commands.

## 🎯 Project Context
- [Project Goal](../.agent/goal.md) — Mission, three-tier approach, success criteria
- [Project Summary](../.agent/project_summary.md) — Experiment timeline, build system, test procedures
- [Roadmap](../.agent/roadmap.md) — Feature milestones, task checklists, known issues
- [Agent Rules](../.agent/rules.md) — Operating conventions for AI agents

## 📚 LLM Wiki Knowledge Base
- [Knowledge Base (Index)](../.agent/llm-wiki-knowledge-base/index.md) — **Compiled, durable knowledge wiki** with cross-referenced pages covering plugin architecture, AssetBundle structure, beatmap formats, conversion pipeline, root causes, and tooling. Self-contained for LLM consumption.

## 🔬 Key Technical Findings

### Experiment Log
- [📋 Experiment Log (Active — Current Feature)](beat-saber-ps4-custom-songs/experiment_log.md) — **Per-feature active log** (currently Beatmap Mode Mapping, Exp 160+). Holds ONLY the current feature's experiments.
- [🗄️ Experiment Log Archive](beat-saber-ps4-custom-songs/experiment_log_archive/) — **Archived per-feature logs** (Exp 1-159 prior features; read-only). Rotate per rules §3.0.

### Memory Injection & Metadata
- [BeatmapLevelSO in Patch Metadata](beatmap-levelso-in-patch-metadata.md) — The "BeatmapLevelSO" class name is stored only in the game patch's global-metadata.dat (version 31, offset 0x23cb6e). NOT in app metadata or module segments.

### Plugin Architecture
- [crtlib.o module_start analysis](beat-saber-ps4-custom-songs/crtlib-o-module-start-analysis.md) — Root cause: plugin_main() never called by CRT. Fix: use __attribute__((constructor)) or define module_start directly.
- [RB4DX Plugin Architecture Reference](beat-saber-ps4-custom-songs/rb4dx-plugin-architecture-reference.md) — Working GoldHEN plugin pattern: crtprx.o, -e _init, GoldHEN SDK HOOK macros.
- [Experiment 4d: Constructor Fix](beat-saber-ps4-custom-songs/experiment-4d-constructor-fix.md) — Changed plugin_main to __attribute__((constructor)). FAILED.
- [Experiment 4e: Direct module_start](beat-saber-ps4-custom-songs/experiment-4e-direct-module-start.md) — Dropped crtlib.o, defined module_start directly. FAILED.
- [Experiment 4f: _init entry point](beat-saber-ps4-custom-songs/experiment-4f-init-entry-point.md) — Changed entry to _init, fixed THREE root causes: .oelf format, TLS from musl, duplicate LOAD PHDR. Deployed 2026-06-11, awaiting test.
- [⚠️ plugins.ini Path Discovery](beat-saber-ps4-custom-songs/plugins-ini-path-discovery.md) — **Critical:** GoldHEN reads root `/data/GoldHEN/plugins.ini`, not `plugins/plugins.ini`. All prior tests were never registered.

### Game & Console Analysis
- [PS4 File Analysis](beat-saber-ps4-custom-songs/ps4_file_analysis.md) — CUSA IDs, installed file structure, resources.assets analysis
- [PS4 FTP Topology](beat-saber-ps4-custom-songs/ps4_topology.md) — Directory structure, GoldHEN paths, custom asset paths
- [DLC Internal Format](beat-saber-ps4-custom-songs/dlc_internal_format.md) — DLC PKG structure, AssetBundles, FSB5 audio
- [Alternative Paths & Tools](beat-saber-ps4-custom-songs/alternative_paths.md) — PkgToolBox, LibForge, UABEA, AssetRipper analysis

### Beatmap Conversion Pipeline ✅ WORKING
- [🔬 m_Script = Just Gzip (No Prefix)](beat-saber-ps4-custom-songs/m_script-gzip-only.md) — **ROOT CAUSE FIXED!** m_Script is just gzip data, no decompressed_size prefix. This was the blocker for ALL previous experiments.
- [💾 Use save_typetree Instead of set_raw_data](beat-saber-ps4-custom-songs/save-typetree-over-set-raw-data.md) — save_typetree handles alignment correctly; set_raw_data causes serialization bugs.
- [🔤 Surrogateescape Encoding for Binary Data](beat-saber-ps4-custom-songs/surrogateescape-encoding.md) — Use .decode('utf-8', 'surrogateescape') not latin-1 for binary data in string fields.

### Initial Research
- [Research Findings](beat-saber-ps4-custom-songs/research_findings.md) — Feasibility research, existing projects, PS4 limitations
- [Community Findings](beat-saber-ps4-custom-songs/community_findings.md) — Web research, Backporter 2021 tool, community projects
- [Comprehensive Analysis](beat-saber-ps4-custom-songs/comprehensive_analysis.md) — Full analysis of all approaches

## 🌐 Community & Songs
- [Communities & Sources](beat-saber-ps4-custom-songs/communities_and_sources.md) — Custom song repositories, tools, communities
- [Songs Catalog](beat-saber-ps4-custom-songs/songs_catalog.md) — Top custom songs from BeatSaver

## 📐 Planning & Status
- [Implementation Plan](beat-saber-ps4-custom-songs/implementation_plan.md) — Original implementation plan
- [Pipeline Progress](beat-saber-ps4-custom-songs/pipeline_progress.md) — Pipeline build system progress
- [Status Report](beat-saber-ps4-custom-songs/status_report.md) — Previous status snapshot
- [User Preferences](beat-saber-ps4-custom-songs/user_preferences.md) — Difficulty requirements, UI preferences
- [Conversation History](beat-saber-ps4-custom-songs/conversation_history.md) — Full conversation history from initial pipeline phase
- [Session Persistence Fix](beat-saber-ps4-custom-songs/session-persistence-fix.md) — Fixed session discoverability: added cz-recent, cz-last, cz-resume commands to setup script

### Pack Bundle Patching — ALL BLOCKED by CRC Check
- [📌 Addressables Catalog CRC Validation](addressables-catalog-crc-validation.md) — **ROOT CAUSE FOUND!** Catalog stores per-bundle CRC32. Any modified bundle fails validation. All pack bundle modification approaches currently blocked.
- [Pack Bundle Patching](pack-bundle-patching.md) — Pack bundle patching reference (LZ4HC requirement, CAB format, current blocked state, UnityPy limitations)
- [PS4 UnityFS Compression Requirements](ps4-unityfs-compression-requirements.md) — PS4 requires LZ4HC (flag=3) for ALL UnityFS blocks. LZ4 (flag=2) crashes.
- [UnityPy Serialization Limitations](unitypy-serialization-limitations.md) — UnityPy save_typetree() ignores BeatmapLevelSO modifications in Unity 2022.3. cab.save() produces incompatible CAB.
- [v22+ CAB Header Format](v22plus-cab-header-format.md) — Unity 2022.3 SerializedFile header layout (big-endian fields, object table format)

## ⚙️ Operating Rules
- [Project Summary Update Rule](project-summary-update-rule.md) — **Enforcement:** Always update project_summary.md after every task completion or before reporting to user.
