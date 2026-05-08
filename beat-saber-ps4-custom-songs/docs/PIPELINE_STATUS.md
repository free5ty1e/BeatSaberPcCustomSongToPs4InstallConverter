# Beat Saber PS4 Custom Songs - Complete Plan

## Current Status

### The Problem
- Unity 2022.3 requires a **PAID license** to build PS4 packages
- $450/year for Unity Pro (or $1500 one-time)
- This blocks our primary workflow

### Our Options Documented

| Option | Description | Feasibility | Status |
|--------|-------------|------------|--------|
| **Option 1** | Unity Windows build (test only) | Low - doesn't solve PS4 | Paused |
| **Option 2** | UABEA-only workflow (modify existing levels) | Medium | **Active** - Exploring |
| **Option 3** | Different Unity version with free PS4 | Low - PS4 always paid | Research |
| **Option 4** | Godot Engine (FREE!) | Low - see below | Exploring |

---

## Option 2: UABEA-Only Workflow

### What We Know
- Beat Saber levels are AssetBundles in `BeatmapLevelsData/`
- Each level contains `BeatSaberBeatmapLevelData` + `AudioClip` (FSB5 format)
- UABEA can **export** audio as OGG
- UABEA **cannot import** new audio directly (only works with FSB5 format it exports)

### Remaining Questions
1. Can we modify the **level metadata** (song name, BPM, etc.) and save?
2. Can we copy/replace levels with different names?
3. What's the minimal change needed to add a "new" song?

### UABEA Capabilities to Test

| Action | Works? | Evidence |
|--------|--------|---------|
| Open AssetBundle | ✅ Yes | Verified |
| Export audio as OGG | ✅ Yes | Verified |
| Export metadata JSON | ✅ Yes | Verified |
| Import JSON back | ❓ Not tried | Need test |
| Modify metadata | ❓ Not tried | Need test |
| Replace audio | ❓ Not tried | Need test |

### Plan for Option 2

**Step 1:** Test Metadata Modification
1. Open `beatsaber` level in UABEA
2. Modify song name in `BeatSaberBeatmapLevelData`
3. Save the AssetBundle
4. Verify it still works

**Step 2:** Test Audio Replacement
1. Export audio as OGG
2. Modify the OGG (if possible)
3. Try importing back (we know this is hard)
4. Alternative: Replace the .resource file directly

**Step 3:** Test Level Cloning
1. Copy `beatsaber` to `mysong`
2. Modify just the metadata
3. Build PKG
4. See if game loads both songs

### Key Files for Option 2

| File | Purpose |
|------|---------|
| `ps4_dump/.../BeatmapLevelsData/beatsaber` | Original level to copy |
| `docs/UABEA_opened_beatsaber_*.jpg` | UI screenshots |

---

## Option 4: Godot Engine

### Why Not Godot?
- Beat Saber is built in **Unity** - uses Unity-specific AssetBundle format
- Godot exports to its own format (.pck/.wasm)
- Even if Godot could create Unity AssetBundles (it can't), the game's C# code expects Unity classes
- Would require rewriting the entire game logic

### Conclusion: Not Viable
Godot cannot create Unity AssetBundles. Even if we could, Beat Saber's game code wouldn't understand them.

---

## Option 3: Alternative Unity Versions

### Research Results
From web search:
- **Unity PS4 support is a compile-time option**, not license-gated in older versions
- BUT: All modern Unity versions (2020+) require PS4 certification/SDK
- The **PS4 SDK** is what enables PS4 builds - it's separate from Unity

### PS4 Build Requirements
1. **Unity Editor** with PS4 module installed
2. **PS4 SDK** from Sony (requires developer account)
3. **Certificate** for signing PKGs

Even if Unity itself is free, you'd still need:
- Sony Developer Account ($10,000+ for full access)
- PS4 devkit or hacked retail console

### Conclusion: Not Viable Without Paid Unity

---

## Our Best Path Forward: Option 2

### Why Option 2?
- Uses existing tools (UABEA) - no license needed
- We already have the full game dump
- Beat Saber auto-loads ALL levels from `BeatmapLevelsData/`
- Even minimal changes could work

### What We Need to Test

#### Test 2A: Metadata Modification
1. Open `beatsaber` in UABEA
2. Change song name from "Beat Saber" to "My Custom Song"
3. Save
4. Verify with UABEA it saved

#### Test 2B: Level Cloning
1. Copy `beatsaber` to new file
2. Open in UABEA
3. Change song ID to something new
4. Save
5. Add to PKG project
6. Build and test

#### Test 2C: PKG with Multiple Levels
1. Take original dump
2. Add one modified level
3. Build PKG
4. Install and verify game loads it

---

## Next Steps (Action Items)

### Immediate Tests to Run

1. **Test 2A - Metadata Modify**
   - Open `beatsaber` in UABEA
   - Find `BeatSaberBeatmapLevelData` object
   - Edit the `_songName` or similar field
   - Save (File → Save or Ctrl+S)
   - Report: Did it save? Any errors?

2. **Test 2B - Level Clone**
   - Copy `beatsaber` file to a new name
   - Open new copy in UABEA
   - Change the level ID
   - Save
   - Report: Two different levels possible?

3. **Test 2C - Full PKG Test**
   - Use PkgToolBox on modified dump
   - Install on PS4
   - Report: Did game launch? New songs?

---

## Progress Tracking

| Test | Status | Result |
|------|--------|-------|
| Test 2A: Metadata Modify | ⏳ NOT STARTED | |
| Test 2B: Level Clone | ⏳ NOT STARTED | |
| Test 2C: PKG Test | ⏳ NOT STARTED | |

---

## Documentation

All findings should be recorded in:
- `docs/PIPELINE_STATUS.md` - Main tracking document
- `docs/UABEA_WORKFLOW.md` - UABEA-specific guidance

This document will be updated as we test each option.

---

## Questions Answered

| Question | Answer |
|----------|--------|
| Can Godot work? | **No** - incompatible format |
| Can old Unity work? | **No** - PS4 SDK always required |
| Can we work without paid Unity? | **Yes** - Option 2 (UABEA) |

---

## Final Recommendation

**Proceed with Option 2 (UABEA-only)** - test the metadata modification first, then level cloning.

The game auto-loads levels from `BeatmapLevelsData/`. If we can:
1. Modify existing level metadata → Easy win
2. Clone a level with new name → Adds more songs
3. Build PKG with modified levels → Full solution

Let's start testing! See `docs/COMPLETE_TEST_PROCEDURE.md` for detailed test steps.