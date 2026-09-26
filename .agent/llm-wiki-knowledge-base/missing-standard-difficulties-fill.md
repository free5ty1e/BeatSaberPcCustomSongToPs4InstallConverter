---
name: missing-standard-difficulties-fill
description: "Exp 218: why maps with fewer than 5 difficulties shipped STOCK beatmaps in unreplaced slots, and how fill_missing_standard_difficulties() fixes it"
metadata:
  type: reference
---

# Missing Standard Difficulties Fill (Exp 218)

## The Bug

The pipeline's `replace_beatmaps()` only replaces a difficulty TextAsset when the
source map provides a matching chart. A BeatSaver map with only ExpertPlus (e.g.
Sexy Socialite) left the bundle's Easy/Normal/Hard/Expert slots containing the
**STOCK** target song's beatmaps — timed for the stock song's BPM grid, played
over the **custom** audio. Symptom: "BPM wayyy too slow, note blocks coming
wayyy too late and slow" on any difficulty the map didn't provide. Mode sets
had the same hole: OneSaber/NoArrows/90Degree diffs without a source chart
fell back to Standard-ref clones (stock data).

## The Fix — `fill_missing_standard_difficulties()` (v0.5338)

Runs in Step 5a-0, BEFORE mode detection/generation/replacement:

1. For each canonical difficulty (Easy, Normal, Hard, Expert, ExpertPlus)
   with no Standard source file, pick the donor:
   **closest HARDER difficulty** (playing up is safer than down), else
   **closest EASIER** one;
2. Clone the donor's chart verbatim into `<Diff>.dat`;
3. Never overwrites files the map provides; **mode files (OneSaber/NoArrows/
   90Degree) are NEVER donors** (an OneSaber chart cloned to a Standard slot
   would be all-blue dots);
4. After filling, mode generation covers all 5 diffs automatically.

The refill list refreshes when the donor itself was just written this run
(ExpertPlus-only map → Easy/Normal/Hard/Expert all clone from ExpertPlusStandard).

## Worst Case (why the song-selection rule exists)

An ExpertPlus-only map becomes ExpertPlus content at ALL five difficulties —
playable, but useless for lower-skilled players. Per `user_preferences.md`,
example-doc songs MUST ship native Easy/Normal/Hard charts from their mapper;
Expert/Expert+ gaps are acceptable (auto-filled from the map's own content).
See [[beatmap-audio-sync]] for the companion BPM-grid fix from the same
experiment, and [[procedural-mode-generators]] for the mode-side handling.

## Related
- [[beatmap-audio-sync]] — Info.dat BPM is the authoritative grid
- [[pipeline-single-song-deploy]] — the deploy flow this runs inside
