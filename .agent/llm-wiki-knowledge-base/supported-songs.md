---
name: supported-songs
description: "Track record of all custom song deployments and sync status"
metadata:
  type: project
---

# Supported Custom Songs

This document tracks every custom song we've deployed and tested. Songs are listed by their Beat Saber slot (Rolling Stones pack), the custom song they've been replaced with, and their sync/playability status.

## Legend

- ✅ **Perfect sync** — notes match audio accurately throughout
- ⚠️ **Minor issue** — sync is correct but song has a long intro (>5s before first note)
- ❌ **Broken** — sync is wrong or song doesn't load

## Deployed Songs

| Slot | Custom Song | Artist | BPM | First Note | Beatmaps | Status | Notes |
|------|------------|--------|-----|------------|----------|--------|-------|
| startmeup | Espresso | Sabrina Carpenter | 104 | 2.3s (b=4) | 5/5 | ✅ Perfect | Reference implementation, V3.3.0 native |
| angry | Rhythm Is A Dancer | Pegboard Nerds | 128 | 1.9s (b=4) | 5/5 | ✅ Perfect | Replaced "We All Lift Together" |
| gimmeshelter | Yes I'm A Mess | AJR | 184 | 2.6s (b=8) | 5/5 | ✅ Perfect | Replaced "How You Like That" |
| cantyouhearmeknocking | Spicy | aespa | 115 | 3.7s (b=7) | 5/5 | ✅ Perfect | Replaced "Spectre" |
| livebythesword | Take Me to the Beach | Imagine Dragons | 105 | 2.3s (b=4) | 5/5 | ✅ Perfect | Has arcs + chains, replaced MUSIC STAR |
| bitemyheadoff | Escaping the Ruins | | 160 | 5.5s (b=14.7) | 5/5 | ✅ Good | |
| deadmanwalking | Finesse (Remix) | | 105 | 2.3s (b=4) | 5/5 | ✅ Good | |
| icantgetnosatisfaction | Dreams Come True | | 99 | 2.9s (b=4.75) | 5/5 | ✅ Good | |
| messitup | Powersnake | | 175 | 2.7s (b=8) | 5/5 | ✅ Good | |
| paintitblack | Time Lapse | | 127 | 1.9s (b=4) | 5/5 | ✅ Good | |
| sugarsoaker | Venom of Venus | | 164 | 2.9s (b=8) | 5/5 | ✅ Good | |
| sympathyforthedevil | LIT | | 99 | 2.4s (b=4) | 5/5 | ✅ Good | |
| wholewideworld | VOLUPTE | | 128 | 2.8s (b=6) | 5/5 | ✅ Good | |


## Sync Knowledge

All sync and color fix details are documented in the knowledge base:
- **[beatmap-audio-sync.md](../llm-wiki-knowledge-base/beatmap-audio-sync.md)** — bpmData eb fix, bpmEvents fix, V3 empty bpmEvents fix, c field color fix
- **[note-color-field-version-differences.md](../llm-wiki-knowledge-base/note-color-field-version-differences.md)** — c vs a field deep dive with V4 reference

## Song Selection Criteria

When selecting a new song for deployment:

1. **At least 3 beatmaps** — Easy, Normal, AND Hard (or 90-degree/OneSaber variants)
2. **Not country music** — any other genre is fine
3. **Decent BeatSaver rating** — proven playability
4. **Short first note** — ideally < 5s before first note (otherwise user perceives it as "very very late")
5. **Has audio file** — `.egg` or `.wav` in the song directory
