# Memory Index

## 📋 Master Index
- [Research Index](RESEARCH_INDEX.md) — **START HERE.** Comprehensive catalog of all project documents, status, and quick commands.

## 🎯 Project Context
- [Project Goal](../.agent/goal.md) — Mission, three-tier approach, success criteria
- [Project Summary](../.agent/project_summary.md) — Experiment timeline, build system, test procedures
- [Agent Rules](../.agent/rules.md) — Operating conventions for AI agents

## 🔬 Key Technical Findings

### Experiment Log
- [📋 Experiment Log](beat-saber-ps4-custom-songs/experiment_log.md) — **Complete chronological log of ALL 19+ experiments and tests with results. Updated every test cycle.**

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

## ⚙️ Operating Rules
- [Project Summary Update Rule](project-summary-update-rule.md) — **Enforcement:** Always update project_summary.md after every task completion or before reporting to user.
