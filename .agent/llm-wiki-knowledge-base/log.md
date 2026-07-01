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
