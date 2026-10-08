---
name: pipeline-single-song-deploy
description: "Self-contained single-song deploy via --deploy-full (v0.5331) + multi-pack incremental deploy fix (v0.5337): one pack's install no longer wipes other packs' custom songs."
metadata:
  type: reference
---

# Self-Contained Single-Song Deploy (`--deploy-full`)

**Introduced:** v0.5331 (Exp 211, 2026-09-08)

## The Problem

A `--download-beat-saver-song 4a901 --target AllTheGoodGirlsGoToHell --deploy-full`
command was **re-deploying all 4 configured packs** (therollingstones, billieeilish, lizzo,
camellia) plus 43 redirects — even though the user only wanted ONE song over one target slot.
On a clean PS4 this also failed validation ("Redirect targets missing") because the individual
`*_v3.bundle` song files for the other 38 slots were never uploaded.

## Root Cause

Two full-fleet behaviors fired unconditionally on every single-song deploy:

1. **Pack-mode deploy (Step 9a):** the song-processing path called
   `deploy_pack_bundle()` / `deploy_pack_modes()` with **no pack filter**, so
   `_get_pack_modes_entries()` iterated ALL `pack_modes.packs` and uploaded every pack's
   patched bundle + the merged catalog.
2. **Redirect generation (`_ensure_mass_song_redirects`):** regenerated the **entire 38-song**
   `mass_deploy.slots` redirect set, producing a 43-entry `redirects.json` that referenced
   bundles not present on a clean PS4.

Both are correct for a full-fleet deploy but wrong for a targeted single-song deploy. The
pipeline was full-fleet oriented with no single-song scoping.

## The Fix (v0.5331)

Added **single-song scoping** through the whole deployment stack:

- **`_resolve_target_pack(config, target)`** — maps a `--target` slot (e.g.
  `AllTheGoodGirlsGoToHell`) to its DLC pack (e.g. `billieeilish`) via
  `beat_saber_song_ids.json` albums.
- Threaded an optional `packs` filter through `_get_pack_modes_entries`,
  `_get_pack_modes_redirects`, `_get_pack_bundle_redirects`, `_ensure_pack_bundle_redirects`,
  `_regenerate_merged_catalog`, `_ensure_pack_mode_bundles`, `deploy_pack_modes`,
  `deploy_pack_bundle`, `_get_remote_pack_paths`; and a `slots` filter through
  `_ensure_mass_song_redirects`; and both through `manage_redirect_config`.
- In the song path, when a `--target` is present, the pipeline resolves the pack and scopes
  the pack-bundle deploy + catalog regen + redirect generation to **just that pack and that
  song slot**. Full-fleet behavior is preserved when no `--target` is given.
- `--deploy-full` now also implies `--deploy-plugin` (build + deploy plugin, ensure
  `plugins.ini` `[CUSA12878]` entry) and `--deploy-features` (deploy `features.json`).

## Result

A single `--deploy-full` for one song now:
1. resolves the target's pack,
2. deploys ONLY the song bundle,
3. deploys ONLY that pack's mode bundle + a matching **single-pack** merged catalog,
4. builds + deploys the plugin + ensures `plugins.ini`,
5. deploys `features.json`,
6. generates redirects scoped to just that song + pack pair,
7. validates.

It does **NOT** touch the other packs/songs — so you can rebuild custom songs one at a time
and test in-game after each (see `docs/example-scripts/example_commands_to_install_custom_songs_over_*_music_pack.md`).

## Keeping the Exp 180 Invariant

The single-pack catalog must cover exactly the redirected pack so CRC/size validation always
passes at boot. This is preserved: the merged catalog is regenerated for exactly the scoped
pack set(s). Related: [[pipeline-deploy-full-orchestration]], [[addressables-catalog-crc-validation]].

## Multi-Pack Incremental Deploys (v0.5337 fix)

**Bug (Exp 217):** running one pack's install script (e.g. the Camelia script) removed all
custom songs previously deployed into OTHER packs (e.g. Billie Eilish). The user's custom BE
songs reverted to stock; only the song-list metadata survived (it lives in a separate
`song_metadata.json` that isn't scoped).

Two root causes:

1. **Cross-pack slot scoping.** `deploy_slots` only collected custom songs from the *target*
   pack. `_ensure_mass_song_redirects` then treated every other pack's song redirect as "out
   of scope" and deleted it. Worse, when the casing mismatch below made the target-pack lookup
   fail too, the function hit its "empty slot scope" branch and deleted ALL song redirects —
   exactly what the console log showed: `Removed song redirect (no slots in scope)` for every
   song, ending with a 2-entry `redirects.json` (catalog + one pack).
2. **Case-sensitive slot matching.** Slots discovered from the PS4 `redirects.json` use the
   game's canonical casing (`BeatmapLevelsData/Crystallized`), while `mass_deploy.slots` in
   the default config uses lowercase (`crystallized`) and the DLC song IDs use mixed casing
   (`Crystallized`). The `s in slots` / `song['songID'] in target_slots` membership tests are
   case-sensitive, so no slot ever matched.

**Fix (v0.5337):**
- `deploy_slots` now collects ALL `BeatmapLevelsData/` slots present in the PS4
  `redirects.json` (any pack), and `deploy_packs` is extended with every pack that owns one
  of those slots. A billieeilish deploy therefore also re-deploys camellia's patched pack
  bundle so both stay in the merged catalog.
- Slot membership comparisons are now case-insensitive in `_ensure_mass_song_redirects`
  (pipeline) and `patch_pack_bundle` (builder).

**Deploy-time ordering note:** `deploy_pack_bundle()` downloads each in-scope pack's existing
PS4 bundle and copies it into `pack_modes_bundles/` as the incremental base BEFORE
`deploy_pack_modes()` builds — so preserved packs keep their already-patched slots and the new
target slot is added on top.

**Verification sequence (all on hardware, v0.5337):** clean slate → Crystallized (3 redirects)
→ CycleHit (4, "Preserving existing custom songs: Crystallized") → AllTheGoodGirlsGoToHell
across packs (6, "Preserving existing packs with custom songs: camellia") →
ExitThisEarthsAtomosphere (7). Catalog CRC/size verified matching for BOTH packs; pack-bundle
inspection confirmed 4 mode sets on exactly the custom slots and stock slots untouched.
## Song-Quality Invariants (v0.5338, Exp 218)

Every `--deploy-full` now guarantees three content invariants on the deployed
per-song bundle:

1. **All 5 Standard slots carry custom content.** Maps providing fewer than 5
   difficulties previously left the STOCK beatmap in unreplaced TextAssets —
   stock timing over custom audio ("BPM wayyy too slow, notes wayyy too late"
   on the user's played difficulty). `fill_missing_standard_difficulties()`
   (Step 5a-0, before mode detection/generation/replacement) clones the map's
   own closest harder difficulty (else closest easier) into `<Diff>.dat` for
   each missing difficulty. Never overwrites provided files; never uses mode
   files (OneSaber/NoArrows/90Degree) as donors (a OneSaber chart cloned into
   a Standard slot would be all-blue dots).
2. **bpmData uses Info.dat `_beatsPerMinute` as the beat grid.**
   `eb = duration × bpm / 60`, extended only if a note lands beyond that grid.
   The old `max_beat × 60 / audio_duration` heuristic undershot BPM by the
   trailing-tail fraction of every map with an outro (see
   [[beatmap-audio-sync]]).
3. **OneSaber TextAssets are blue dots.** Generated AND mapper-authored charts
   are normalized through `_generate_one_saber()` at injection (see
   [[saber-colors-and-one-saber]]); bombs pass through.

## Post-Deploy Size Checks: Scope Them to Session Uploads (v0.5356, Exp 264)

The post-deploy validation's "sizes match local files" check exists to catch
FAILED/INCOMPLETE uploads of what a deploy just pushed. It must NOT hard-fail
over out-of-scope redirect targets whose stale LOCAL artifact differs from the
live PS4 copy — that comparison says nothing about the deploy's health, and
in practice it will eventually be true (local rebuilds by different pipeline
versions legitimately differ by a few bytes; charts stay identical). The
user's first 22-song multi-pack batch died at song 1/22 on exactly this:
`Size mismatches: ['Oxytocin_v3.bundle (local 36,706,086 vs PS4 36,706,075)']`
for a song the batch never touched.

**Rule:** the pipeline keeps a session upload ledger
(`_SESSION_UPLOADED_BUNDLES`) that `deploy_to_ps4` and `_deploy_file_to_ps4`
record into on every VERIFIED upload. The size check:

- hard-fails only for files in the ledger (did MY upload land intact?);
- reports out-of-scope mismatches as an informational `ℹ️` note;
- with an EMPTY ledger (standalone `--verify-ps4` — the deep-audit mode),
  checks everything and fails on any mismatch.

**Related trap (same batch, found while proving):** parsers of the example
scripts must strip SHELL quoting from tokens. The scripts write
`--target "Scream&Shout"` because `&` must be quoted for the shell; a `\S+`
regex captures the quotes into the slot name and the deploy targets a
garbage slot. Quotes are shell syntax, never part of the value. See
[[lftp-ftp-pitfalls]] (pitfall 4 — the same `&` from the transport side) and
[[ps4-file-system-redirects]] (case-sensitivity of redirect VALUES).
