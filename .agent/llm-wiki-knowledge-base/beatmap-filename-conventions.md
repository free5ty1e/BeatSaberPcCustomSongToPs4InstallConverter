---
name: beatmap-filename-conventions
description: "BeatSaver beatmap file naming conventions and pipeline selection priority"
metadata:
  type: concept
---

# Beatmap Filename Conventions

## Overview

BeatSaver custom songs use a variety of filename conventions for difficulty beatmap
`.dat` files. The pipeline must handle all of them reliably when matching a community
song's files to the PS4 bundle's TextAsset difficulty slots.

## Observed Filename Patterns (from 96-song repo)

Sorted by priority (best → worst for PS4):

| Pattern | Example | Notes |
|---------|---------|-------|
| `<Diff>Standard.dat` | `ExpertPlusStandard.dat` | Standard mode — preferred |
| `<Diff>.dat` | `ExpertPlus.dat` | Bare name, no mode suffix — common |
| `<Diff>.beatmap.dat` | `ExpertPlus.beatmap.dat` | Alternate BeatSaver format |
| `<Diff>90Degree.dat` | `Expert90Degree.dat` | Limited angle — functional on PS4 |
| `<Diff>OneSaber.dat` | `ExpertOneSaber.dat` | One saber — functional on PS4 |
| `<Diff>NoArrows.dat` | `ExpertNoArrows.dat` | No-arrow (dot) notes — functional |
| `<Diff>Legacy.dat` | `ExpertLegacy.dat` | Legacy format — usually functional |
| `<Diff>Lawless.dat` | `ExpertPlusLawless.dat` | Lawless mode — functional |
| `<Diff>SingleSaber.dat` | `ExpertPlusSingleSaber.dat` | Alias for OneSaber |
| `<Diff>360Degree.dat` | `Expert360Degree.dat` | **Avoid** — notes behind player unplayable in PS4 VR |

All difficulty prefixes seen: `Easy`, `Normal`, `Hard`, `Expert`, `ExpertPlus`  
Also seen: `360DegreeExpert.dat` (mode prefix instead of suffix — these contain "360Degree" and are treated as tier 5)

## Pipeline Selection Priority (`_select_beatmap_file`)

The pipeline function `_select_beatmap_file(diff, beatmap_files, ignore_non_standard)` 
in `full_custom_song_pipeline.py` selects the best file using a 5-tier fallback:

```
Tier 1 — <Diff>Standard.dat         ← always preferred
Tier 2 — <Diff>.dat (bare)          ← no mode suffix, always included
Tier 3 — <Diff>.beatmap.dat         ← alternate BeatSaver format
Tier 4 — Other modes (90Degree, OneSaber, NoArrows, Legacy, etc.)
Tier 5 — 360Degree                  ← absolute last resort
```

The first non-empty tier wins.

### `--ignore-non-standard-beatmaps` Flag

When set:
- Tiers 1, 2, 3 are still considered (Standard, bare, .beatmap.dat)
- **Tiers 4 and 5 are suppressed** (no 90Degree, OneSaber, 360Degree fallback)
- Bare files (tier 2) are **not** filtered — they have no mode suffix and are
  valid Standard-equivalent candidates

> ⚠️ **Old behavior (pre-v0.51):** The flag incorrectly filtered bare `<Diff>.dat`
> files because the check was `if 'Standard' not in f: continue`, which also dropped
> bare-named files. Fixed in v0.51 with the tiered approach.

## ExpertPlus Guard

When matching `Expert`, the pipeline must skip any file containing `ExpertPlus`
(substring trap). The guard `if diff == 'Expert' and 'ExpertPlus' in base: continue`
is applied before tier assignment.

## 360Degree Notes (PS4 VR Limitation)

360Degree maps are designed for PC VR with full 360° tracking. On PS4 VR with
~90° field of view, notes that spawn behind the player are completely invisible and
unswingable. These maps technically load without crashing but are effectively
unplayable. Tier 5 means "we have nothing better" — the game won't crash, but the
player experience will be poor.

## Files Excluded from Selection

The following are always skipped regardless of tier:
- Files containing `Info` (e.g. `Info.dat`, `BPMInfo.dat`)
- Files containing `Lightshow` (lightshow data, not beatmap)
- Files containing `AudioData` (audio metadata, not beatmap)

## Implementation Reference

```python
# full_custom_song_pipeline.py
def _select_beatmap_file(diff: str, beatmap_files: list, ignore_non_standard: bool = False) -> str | None:
    tier1, tier2, tier3, tier4, tier5 = [], [], [], [], []
    for f in beatmap_files:
        # ... exclusion checks ...
        if f'{diff}Standard' in stem:    tier1.append(f)
        elif stem == f'{diff}.dat':       tier2.append(f)
        elif f'{diff}.beatmap' in stem:   tier3.append(f)
        elif '360Degree' in stem:         tier5.append(f)  # if not ignore_non_standard
        else:                             tier4.append(f)  # if not ignore_non_standard
    for tier in (tier1, tier2, tier3, tier4, tier5):
        if tier: return tier[0]
    return None
```

## See Also

- [[beatmap-conversion-pipeline]] — V2→V3 conversion, how .dat files are processed
- [[beatmap-format-v3]] — PS4 beatmap V3 format specification
- [[development-workflow]] — Pipeline usage and deployment cycle
