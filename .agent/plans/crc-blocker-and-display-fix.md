# Plan: Solve Addressables CRC Block & Display Name Problem

**Created:** 2026-07-16
**Status:** Active — Priority A in progress
**Related experiments:** 136, 142 (CRC discovery + GF(2) correction), 141 (mode selector dead end), 57–61 (song replacement breakthroughs), 94–95 (full song playback confirmed)

---

## Problem Statement

The Beat Saber PS4 game validates per-bundle integrity via the Addressables catalog (`aa/catalog.json`). The catalog stores `m_Crc` and `m_BundleSize` for every bundle in a UTF-16 encoded JSON string. When Unity loads a modified pack bundle, it checks CRC → mismatch → CE-34878-0 crash. This blocks:

1. **Display names/artists** — Custom songs appear under original Rolling Stones album names
2. **Mode selector** (OneSaber/90Degree) — `_previewDifficultyBeatmapSets` lives in pack bundle `BeatmapLevelSO`, not per-song bundles
3. **Any pack bundle modification** — UnityPy round-trip, manual rebuild, binary injection all crash

The catalog is loaded as plain JSON by `ContentCatalogProvider`, NOT via `AssetBundle.LoadFromFile`. GoldHEN's AFR plugin only hooks the latter → cannot redirect or patch the catalog.

---

## Current State (Working)

| Component | Status |
|-----------|--------|
| Plugin v0.65 | ✅ FSELF format, open() hook, dynamic redirects.json, 13-song table |
| Pipeline v0.52 | ✅ PCM16 audio, V2→V3 beatmaps, filename matching, plugin toggle |
| End-to-end song playback | ✅ Full custom songs play with correct sync on PS4 |
| Song metadata extraction | ✅ 305 songs cataloged from pack bundles |

## Current State (Blocked)

| Goal | Blocker | Last Attempt |
|------|---------|-------------|
| Custom display names in menu | Pack bundle CRC validation | Exp 142: CRC matched but size delta (+2,712B) crashed |
| Mode selector modes | Same CRC block + per-song bundles don't affect UI | Exp 141: Modes loaded but ignored by menu |
| IL2CPP hook for display strings | Inlined / never fires / calling convention mismatch | Exps 117–131: All dead |

---

## Priority A: Solve Display Name & Mode Selector (Three Approaches)

### Approach 1: Size + CRC Match via GF(2) Padding (Highest Feasibility)

**Concept:** Use the linearity of CRC-32 over GF(2) to find padding bytes that produce BOTH the original file size AND the original CRC simultaneously.

**What we know from Exp 142:**
- Original bundle: 7,902,803 bytes, CRC = `0xdc8b314f`
- Modified bundle (Exp 142): 7,905,515 bytes (+2,712B), CRC matched (`0xdc8b314f`) ✅
- Size mismatch triggers secondary validation beyond just CRC

**Implementation:**
1. Identify free padding/alignment bytes in the bundle (UnityFS blocks often have alignment padding)
2. The modified BeatmapLevelSO blob adds ~817 bytes to one CAB → shifts all subsequent offsets
3. Find padding that: (a) keeps file_size = 7,902,803 and (b) produces CRC = `0xdc8b314f`
4. This is a system of linear equations over GF(2): 32 bits for CRC + size constraint

**Success criteria:** Bundle loads without crash, display names show custom song info, modes appear in selector.

**Risk factors:**
- May not have enough free padding bytes to satisfy both constraints
- Size matching might require compressing differently (changing more than just padding)
- If `m_BundleSize` triggers additional validation beyond CRC, size match alone may not suffice

### Approach 2: Memory Injection Post-Initialization (Fallback)

**Concept:** After the game loads and Addressables are cached in memory, use GoldHEN's kernel write to patch BeatmapLevelSO objects directly in RAM. Bypasses catalog entirely since we're modifying live data.

**What we know:**
- GoldHEN SDK provides `sys_sdk_proc_rw()` for process memory writes (used for manual hooks)
- The plugin already loads successfully via FSELF format
- IL2CPP deserializes BeatmapLevelSO objects from the pack bundle into managed heap memory

**Implementation:**
1. Find the base address of `Il2CppUserAssemblies.prx` at runtime (`sceKernelGetModuleList`)
2. Scan for BeatmapLevelSO instances in memory (search for known field patterns: levelID string, songName string)
3. For each found instance matching a redirect target, patch `_songName`, `_songAuthorName`, and `_previewDifficultyBeatmapSets` fields
4. The plugin needs to know which songs are custom (from `redirects.json`)

**Success criteria:** Custom names appear in menu without any file modification.

**Risk factors:**
- Finding BeatmapLevelSO instances via memory scan is fragile (GC moves objects, multiple copies)
- IL2CPP managed heap layout differs from native memory — PPtr references may break
- GC may reclaim patched objects before they're displayed
- Requires deep understanding of PS4 FMOD/IL2CPP memory model

### Approach 3: Per-Song Bundle with BeatmapLevelSO Injection (Exploratory)

**Concept:** Each per-song bundle already contains a `BeatmapLevel` object. Investigate whether the game's menu code path reads display info from this object instead of the pack bundle's `BeatmapLevelSO`. If so, injecting modified metadata into the per-song bundle would work without touching the pack bundle.

**What we know:**
- Per-song bundles contain `BeatmapLevel` (MonoBehaviour) with audio/beatmap references
- Pack bundles contain `BeatmapLevelSO` (ScriptableObject) with display metadata
- Exp 141 proved mode selector reads from pack bundle's `_previewDifficultyBeatmapSets`, not per-song bundles
- But the **display name** path might differ — menu may read songName from BeatmapLevel, not BeatmapLevelSO

**Implementation:**
1. Inspect the game's `StandardLevelDetailView` or `AnnotatedBeatmapLevelCollectionController` code (from Il2CppDumper) for where display names are resolved
2. If per-song bundle has a path to display metadata, inject it there
3. If not, this approach is dead

**Success criteria:** Custom names appear in menu via per-song bundles only.

**Risk factors:**
- Exp 141 suggests menu reads from pack bundle for modes — likely same for names
- BeatmapLevelSO is a ScriptableObject shared across songs; modifying one instance may not affect the UI if the menu caches by reference

---

## Priority B: Pipeline Hardening (After A Solved)

| Task | Details |
|------|---------|
| Remove hardcoded `ORIGINAL_RESOURCE_SIZE` | Auto-detect from template bundle's `.resource` file |
| Remove hardcoded `DIFFICULTIES` list | Detect from song directory contents |
| Remove hardcoded `SAMPLE_RATE` | Detect from audio file metadata (`soundfile` library) |
| Add `--no-beatmap-bpm` flag | Fall back to Info.dat BPM if beatmap scanning fails |
| Support more audio formats | WAV is already supported; OGG via oggenc works for Vorbis FSB5 path |

---

## Priority C: Community Release Prep (After A Solved)

- Document full pipeline walkthrough in README
- Publish song catalog (`beat_saber_song_ids.json`) with 305 songs
- Document known limitations (display names, mode selector)
- Create deployment guide for community users
- Consider GitHub releases automation (CI workflow exists but needs auth)

---

## Execution Order

```
1. Approach 1: Size + CRC match via GF(2) padding  [~2-4 hours]
   ├─ Identify free bytes in bundle structure
   ├─ Build system of equations over GF(2)
   ├─ Solve for padding that satisfies both constraints
   └─ Test on PS4 if successful

2. If Approach 1 fails: Approach 2: Memory injection [~4-8 hours]
   ├─ Implement BeatmapLevelSO scanner in plugin
   ├─ Patch display fields at runtime
   ├─ Test with Espresso custom song
   └─ Iterate on scan reliability

3. If Approach 2 fails: Approach 3: Per-song path exploration [~2-4 hours]
   ├─ Il2CppDumper analysis of menu code paths
   ├─ Determine if BeatmapLevel (not SO) feeds display
   └─ Inject metadata into per-song bundle if possible

4. Priority B and C once A is solved
```

---

## Key Files Referenced

| File | Purpose |
|------|---------|
| `beat_saber_deluxe/build_patched_pack_bundle.py` | Exp 132/135 bundle builder (LZ4HC, text patching) |
| `beat_saber_deluxe/src/main.cpp` | Plugin source — open hook, redirects.json loading |
| `beat_saber_deluxe/tools/full_custom_song_pipeline.py` | Main pipeline — PCM16 → FSB5 → bundle → deploy |
| `beat_saber_deluxe/redirects.json` | Dynamic redirect config (deployed to AFR path) |
| `.agent/llm-wiki-knowledge-base/song-metadata-addressables-structure.md` | Full catalog CRC discovery documentation |
| `.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md` | All 190+ experiments with results |

---

## Success Criteria for Priority A

- [ ] Custom song names appear in Beat Saber PS4 menu (not "Start Me Up", "Paint It Black", etc.)
- [ ] Custom artist names display correctly
- [ ] Song selection loads the custom bundle (not original)
- [ ] Song plays with correct audio and sync
- [ ] Score saves for custom songs
- [ ] No CE-34878-0 crashes during normal gameplay

---

*This plan supersedes any prior planning documents. All approaches are ranked by feasibility based on 190+ experiments of empirical testing.*
