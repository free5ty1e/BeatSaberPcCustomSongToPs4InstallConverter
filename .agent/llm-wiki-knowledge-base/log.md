---
name: log
description: "Chronological record of knowledge base creation and updates"
metadata:
  type: log
---

# Knowledge Base Log

## [2026-07-01] creation | Beat Saber Deluxe LLM Wiki
- Created initial knowledge base from conversation history, experiment log, memory files, and source code
- Categories covered: plugin architecture, AssetBundle structure, beatmap formats, conversion pipeline, PS4 specifics, tooling
- Key root causes documented: m_Script gzip-only, save_typetree vs set_raw_data, surrogateescape encoding
- 10 wiki pages created covering all durable project knowledge

## [2026-07-01] update | Bomb notes conversion
- Updated [[beatmap-conversion-pipeline]] with bomb notes conversion section
- New content: V2→V3 bomb notes algorithm, bombNotes format, V3 bombNotesData (position only)
- Marked `Bomb notes conversion` as completed in roadmap
- Experiment 72 deployed with MUSIC STAR test song (14-40 bombs per difficulty)

## [2026-07-01] update | Bomb notes conversion SUCCESS
- Experiment 72 confirmed: bomb notes visible in-game alongside custom notes
- Knowledge base beatmap-conversion-pipeline.md already updated with bomb notes section
- Log analysis: 751 lines, 2 redirects, 0 errors, clean PlayerData save

## [2026-07-01] update | Slider/burstSlider conversion added
- Implemented V2 sliders → V3 arcs and V2 burstSliders → V3 chains conversion
- Updated [[beatmap-format-v3]] with arcs, chains, bombNotes sections
- Updated [[beatmap-conversion-pipeline]] with arc/chain conversion algorithms
- Verified: all 3 test songs (notes, bombs, sliders) pass UnityPy verification
- Roadmap: arcs and chains marked as done

## [2026-07-01] update | All features combined test
- Experiment 74: combined MUSIC STAR + Take Me to the Beach into one bundle
- Notes, bombs, obstacles, arcs (sliders), and chains (burstSliders) all present
- Knowledge base already updated with arcs and chains conversion in previous updates

## [2026-07-01] update | Floating walls + obstacles y field documented
- Experiment 74b confirmed: V3 obstaclesData supports `y` (row offset) field
- Updated [[beatmap-format-v3.md]] obstacles section with `x`, `y`, and floating wall info
- Updated [[beatmap-conversion-pipeline.md]] obstacle conversion with `y` handling and V2 type→V3 y mapping

## [2026-07-01] create | PS4 Environment System documented
- Environment is NOT stored in individual song AssetBundles
- Environment is tied to song's album/pack via Addressable system
- Full environment control requires resources.assets patching (Milestone 4)
- Created [[ps4-environment-system.md]] knowledge page

## [2026-07-01] update | Audio replacement pipeline + HEVAG encoder
- Experiment 75: Implemented full audio replacement pipeline
- HEVAG (PS4 ADPCM) encoder in Python — 3.5:1 compression
- FSB5 container creation with proper PS4 format
- Bundle size reduced from 12MB to 216KB
- Script: quick_test_gen.py now generates everything (beatmaps + audio)

## [2026-07-01] update | Audio pipeline: HEVAG encoder extracted + FSB5 fix
- Extracted `tools/hevag_encoder.py` — standalone CLI tool + importable module
- Created [[ps4-hevag-fsb5-audio.md]] documenting the full audio pipeline
- Fixed: wrong FSB5 header template was causing game freeze (was using different song's DSP coefficients)
- Corrected template now uses Start Me Up's own FSB5 header (bytes 16-915)
- Optimized encoder: silence fast path (211K frames/s), early termination, batch PCM reading
- Updated quick_test_gen.py to import from standalone module
