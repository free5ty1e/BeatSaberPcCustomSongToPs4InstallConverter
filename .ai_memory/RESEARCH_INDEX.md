# Research Index — Beat Saber PS4 Custom Songs

**Last updated:** 2026-06-11  
**Purpose:** Central catalog of all research, memory, and planning documents for the Beat Saber PS4 custom song project. This file serves as an onboarding reference for new developers or AI agents.

---

## Project Status

| Milestone | Status | Doc |
|-----------|--------|-----|
| Feasibility research | ✅ Complete | [research_findings.md](beat-saber-ps4-custom-songs/research_findings.md) |
| PS4 file/topology analysis | ✅ Complete | [ps4_file_analysis.md](beat-saber-ps4-custom-songs/ps4_file_analysis.md), [ps4_topology.md](beat-saber-ps4-custom-songs/ps4_topology.md) |
| DLC package reverse engineering | ✅ Complete | [dlc_internal_format.md](beat-saber-ps4-custom-songs/dlc_internal_format.md) |
| Alternative tool/path analysis | ✅ Complete | [alternative_paths.md](beat-saber-ps4-custom-songs/alternative_paths.md) |
| Song community research | ✅ Complete | [communities_and_sources.md](beat-saber-ps4-custom-songs/communities_and_sources.md) |
| Song catalog | ✅ Complete | [songs_catalog.md](beat-saber-ps4-custom-songs/songs_catalog.md) |
| Implementation plan | ✅ Complete | [implementation_plan.md](beat-saber-ps4-custom-songs/implementation_plan.md) |
| Plugin development (PRX) | 🔄 In Progress | See `/workspace/beat_saber_deluxe/` and [crtlib-o-module-start-analysis.md](beat-saber-ps4-custom-songs/crtlib-o-module-start-analysis.md) |
| Plugin architecture reference (RB4DX) | ✅ Complete | [rb4dx-plugin-architecture-reference.md](beat-saber-ps4-custom-songs/rb4dx-plugin-architecture-reference.md) |
| Community/tool findings | ✅ Complete | [community_findings.md](beat-saber-ps4-custom-songs/community_findings.md) |
| Comprehensive analysis | ✅ Complete | [comprehensive_analysis.md](beat-saber-ps4-custom-songs/comprehensive_analysis.md) |

---

## Document Catalog

### 🎯 Goals & Strategy

| File | Description | Key Content |
|------|-------------|-------------|
| [goal.md](../.agent/goal.md) | Project mission & high-level approach | Three-tier approach: insert songs into existing albums (#3), add custom album (#2), add new album per PKG (#1) |
| [rules.md](../.agent/rules.md) | AI agent operating rules | Memory storage conventions, git behavior, PS4/fileshare read-only policy |
| [project_summary.md](../.agent/project_summary.md) | **Main project status document** | Full experiment timeline, build system, test procedures, RB4DX reference, CRT analysis |

### 🔬 Research & Analysis

| File | Date | Description |
|------|------|-------------|
| [research_findings.md](beat-saber-ps4-custom-songs/research_findings.md) | 2026-04 | Initial feasibility research — existing projects, tools (BMBF, SongCore), PS4 limitations. Found no fully working automated pipeline. |
| [comprehensive_analysis.md](beat-saber-ps4-custom-songs/comprehensive_analysis.md) | 2026-05 | Full analysis of all approaches — PKG building, FTP direct-write, UABEA patching, runtime hooking via GoldHEN plugin. |
| [alternative_paths.md](beat-saber-ps4-custom-songs/alternative_paths.md) | 2026-04 | Analysis of alternative tools and approaches — PkgToolBox, LibForge, UABEA, AssetRipper, Labakis. |
| [community_findings.md](beat-saber-ps4-custom-songs/community_findings.md) | 2026-04 | Web research findings — Backporter 2021 tool (unmaintained), existing PS4 mod projects, community tools. |
| [user_preferences.md](beat-saber-ps4-custom-songs/user_preferences.md) | 2026-04 | User's difficulty requirements (Expert+), song selection preferences, UI expectations. |

### 💻 Technical Analysis

| File | Date | Description |
|------|------|-------------|
| [ps4_file_analysis.md](beat-saber-ps4-custom-songs/ps4_file_analysis.md) | 2026-04-24 | CUSA ID mapping, installed file structure, `ps4-update.tar` contents, `resources.assets` analysis. Game engine: Unity 2022.3, LZ4HAM compression. |
| [ps4_topology.md](beat-saber-ps4-custom-songs/ps4_topology.md) | 2026-04 | PS4 FTP topology — directory structure, permissions, GoldHEN plugin paths, custom assets paths. **PS4 IP:** 192.168.100.117:2121. |
| [dlc_internal_format.md](beat-saber-ps4-custom-songs/dlc_internal_format.md) | 2026-04-24 | Reverse-engineering of DLC PKG files (Darude-Sandstorm, Imagine Dragons-Believer). Identified param.sfo, embedded AssetBundles, FSB5 audio. |
| [songs_catalog.md](beat-saber-ps4-custom-songs/songs_catalog.md) | 2026-04 | Auto-generated catalog of top Beat Saber custom songs from BeatSaver — artist, mapper, BPM, download links. |

### 🏗️ Implementation

| File | Date | Description |
|------|------|-------------|
| [implementation_plan.md](beat-saber-ps4-custom-songs/implementation_plan.md) | 2026-04 | Original implementation plan — runtime memory patching approach similar to RB4DX. Predates the actual plugin experiments. |
| [pipeline_progress.md](beat-saber-ps4-custom-songs/pipeline_progress.md) | 2026-04 | Previous pipeline build system progress — LibForge, PkgToolBox, asset extraction pipeline. |
| [status_report.md](beat-saber-ps4-custom-songs/status_report.md) | 2026-05-01 | Status report — what was working at that point in time. |
| [conversation_history.md](beat-saber-ps4-custom-songs/conversation_history.md) | 2026-04-27 | Full conversation history from the initial pipeline-building phase. |
| [crtlib-o-module-start-analysis.md](beat-saber-ps4-custom-songs/crtlib-o-module-start-analysis.md) | 2026-06-11 | **Critical finding:** `crtlib.o`'s `module_start` does NOT call `plugin_main()`. This explains why heartbeat tests 4a-4c failed. |
| [rb4dx-plugin-architecture-reference.md](beat-saber-ps4-custom-songs/rb4dx-plugin-architecture-reference.md) | 2026-06-11 | Reference architecture from working GoldHEN plugin RB4DX — correct CRT, entry point, hook system, Makefile flags. |

### 🌐 Community & Tools

| File | Description |
|------|-------------|
| [communities_and_sources.md](beat-saber-ps4-custom-songs/communities_and_sources.md) | Catalog of custom song communities, repositories, and tools (BeastSaber, BeatSaver, BMBF, etc.) |

---

## Key Directories

| Path | Contents |
|------|----------|
| `/workspace/.ai_memory/` | Memory & research index files |
| `/workspace/.ai_memory/beat-saber-ps4-custom-songs/` | All research and planning documents |
| `/workspace/.agent/` | Agent context files (goal, rules, project_summary, openorbis_sdk_guide, context_beat_saber_fileshare) |
| `/workspace/beat_saber_deluxe/` | Plugin source code (PRX) |
| `/workspace/beat-saber-ps4-custom-songs/` | Original project repo (docs, converted assets, LibForge, PkgToolBox, RB4DX source reference) |
| `/workspace/rb4dx_repo/` | RB4DX full repo (reference GoldHEN plugin) |
| `/opt/openorbis/OpenOrbis/PS4Toolchain/` | OpenOrbis PS4 cross-compilation toolchain |

## Quick Cheat Sheet

```bash
# Build the plugin
export OO_PS4_TOOLCHAIN=/opt/openorbis/OpenOrbis/PS4Toolchain
cd /workspace/beat_saber_deluxe && make clean && rm -rf obj && make -B

# Verify entry point
readelf -h obj/beat_saber_deluxe.elf | grep Entry

# Deploy to PS4
lftp -u anonymous, -p 2121 192.168.100.117 <<< "put beat_saber_deluxe.prx -o /data/GoldHEN/plugins/beat_saber_deluxe.prx"

# Check for heartbeat on PS4
lftp -u anonymous, -p 2121 192.168.100.117 <<< "ls /data/custom/bs_deluxe/"
```
