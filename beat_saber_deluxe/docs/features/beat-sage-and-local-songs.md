# Beat Sage + Local Song Folders

**Status:** ✅ Tier 1 verified against the live beatsage.com service (2026-10-22, M13) · web app **0.6.20+** · no plugin/pipeline version requirement (the flow ends at the pipeline's existing `--song-dir`)

## What it does

The web app's **Pick a Song** tab gains two ways to convert songs that are not
on BeatSaver:

1. **Generate a map with Beat Sage** — pick any audio file you have the rights
   to process, and the free AI service [beatsage.com](https://beatsage.com)
   generates a Beat Saber map from it. *Powered by beatsage.com* — their
   service, their terms, their branding; we drive it politely.
2. **Use a map you already have** — a local folder or a map zip (any
   BeatSaver-format map: V2, V3, or V4).

Both end at the same place: a **validated, staged song folder** that deploys
with the existing Deploy tab unchanged (`--song-dir <folder> --target <slot>`).
**Zero plugin or pipeline changes** — the pipeline has always accepted local
folders; this feature stages and validates them for you.

## Beat Sage: the automation ladder

| Tier | What the web app does | When you get it |
|---|---|---|
| **1 — generate for me** | Uploads your audio to beatsage.com, polls their job at *their own UI's cadence* (3 s), downloads the finished map zip, validates it, and stages it — one click, one live console | Local web app + internet (the default) |
| **2 — guided flow** | Shows the exact options to pick on their site + a drop zone for the downloaded zip (extract → validate → stage, automated) | Always — the fallback if Tier 1 fails, and the only path in command-builder (Pages) mode |
| **3 — manual** | The same guidance without the drop zone (point section 3 at your extracted folder) | If even zip intake is impossible |

Any Tier-1 failure (their service busy, moved, changed) **automatically opens
the guided card** — the feature never dead-ends.

### The respect rules (why this is safe to ship)

- **One job at a time**, polled at their own cadence with their own failure
  budget (3 misses) — never a hammer on their free queue.
- **Their branding is explicit** in the UI; using Beat Sage means accepting
  *their* terms; the map is theirs, generated for you.
- **You assert the rights to the audio** (checkbox required before generate):
  use your own music or music you're licensed to process. The generated map
  stays on your machine — don't redistribute it.
- The API surface is **live-captured, not scraped**: the three routes, the
  multipart field names, and every status value were read from their own
  client bundle once (Oct 2026) and are pinned by tests; the gated
  `BEATSAGE_LIVE=1` test verifies the contract against the real service.
- **CI never contacts beatsage.com** — every test is mocked; the one live
  check is opt-in per run.

## Local folders: the validator

Type a folder path (or drop a zip) and the web app validates it live against
the pipeline's own contract — per-problem messages, each with a **To fix:**
suggestion:

- `Info.dat` (or `info.dat`) must exist and parse — V2/V3/V4 all fine
  (the pipeline converts V2→V3 and auto-fills Expert/Expert+ during deploy)
- at least one audio file (`.wav .ogg .flac .mp3 .aiff .egg`)
- at least one beatmap `.dat`

Warnings are informational: missing Easy (Beat Sage can't generate one),
missing Expert/Expert+ (auto-filled), V2 schema (converted), no BPM
(estimated). Zip intake is **zip-slip guarded** (traversal and absolute-path
entries are refused), and BeatSaver-style single-wrapper zips are descended
into automatically.

## Staged songs

Every validated song lands in the **staged songs** list (persists across web
app restarts; entries whose folder vanished are pruned automatically):

- **Deploy →** hands the folder to the Deploy tab (the button turns into the
  normal deploy flow; the command preview shows `--song-dir …`)
- **✕** removes the entry — zip-extracted folders are deleted from
  `webapp/staged_songs/`; folders you pointed at stay where they are (they
  were never ours)

## Command-line equivalents

Everything the sections do is one pipeline command:

```
# deploy any staged/local folder:
python3 beat_saber_deluxe/tools/full_custom_song_pipeline.py \
    --song-dir /path/to/your/map_folder --target TruthHurts \
    --pcm16 --no-pad --convert-to-v3 --deploy-full
```

Beat Sage itself is web-app-only (it's a service interaction, not a pipeline
operation) — but its output is just a folder: the staged song's path is shown
in the staged list and usable with `--song-dir` directly.
