---
name: environment-binding-layers
description: "M14 research: the THREE layers that bind an environment to a level on the PS4 build — the BeatmapLevelSO strings, the per-difficulty PreviewDifficultyBeatmap indices, and EnvironmentInfoSO — with measured blob layouts and offsets"
metadata:
  type: reference
---

# Environment Binding Layers (M14 research, Exp 297)

## The three layers (measured)

1. **BeatmapLevelSO string fields** (pack bundle, per-song SO object) — `_environmentName`
   (the pack's own env) + `_allDirectionsEnvironmentName`, stored as **length-prefixed ASCII
   strings** in the serialized blob, BEFORE the preview-sets region.
2. **`BeatmapLevelSO.PreviewDifficultyBeatmap._environmentNameIdx`** (int @ 0x14, next to
   `_beatmapColorSchemeIdx` @ 0x18) — **each per-difficulty preview entry binds its
   environment by INDEX** into the game's environment table. The mode patcher rewrites
   these preview structures — prime suspect for the blank-env mystery (audit pending:
   stock vs patched idx values per mode — Exp 297's next hardware-adjacent step).
3. **`EnvironmentInfoSO`** (the game's env registry: `_environmentName` @ 0x18,
   `_serializedName` @ 0x30, `_tags`, `_environmentType`) — the table the idx values
   resolve against; the 16-standard-env names + indices come from here.

## The measured blob layout (stock == patched env handling)

From real pack bundles (raw-CAB parse via `build_pack_mode_bundles.get_cab_raw` +
length-prefixed-ASCII scan), per-song slot SO objects:

```
billieeilish / AllTheGoodGirlsGoToHell (stock 484B → patched 1,072B):
  @ 28  len=35  'AllTheGoodGirlsGoToHellBeatmapLevel'   (levelID)
  @ 72  len=23  'AllTheGoodGirlsGoToHell'               (song name)
  @100  len=29  'all the good girls go to hell'         (subName)
  @140  len=13  'Billie Eilish'                          (author)
  @220  len=17  'BillieEnvironment'                      ← _environmentName (the PACK's own env)
  @244  len=22  'GlassDesertEnvironment'                 ← _allDirectionsEnvironmentName (SHARED)
  @280  …       preview sets (walk_blob's setsOff) … @480 contentRating
```

Cross-pack: lizzo → `LizzoEnvironment` / rollingstones → `TheRollingStonesEnvironment`,
BOTH with `_allDirectionsEnvironmentName` = `GlassDesertEnvironment` — every DLC pack has a
custom env, and 360° shares one standard env. (DLC envs are per-pack custom bundles:
`<pack>environment_assets_all_*.bundle` exist in the dump.)

## What this proves / eliminates

- **Hypothesis (b) ELIMINATED**: the pack-mode patch does NOT drop the SO's env strings —
  the patched slot SO preserves `BillieEnvironment` + `GlassDesertEnvironment` at the SAME
  offsets (484B → 1,072B growth is all preview-set data).
- The env strings are **directly patchable with the existing raw-CAB machinery** (the same
  `get_cab_raw`/blob-rewrite path the mode patches use) — no UnityPy blocker applies here.
- The blank-vs-working custom split must be explained by layer 2 (the per-difficulty
  `_environmentNameIdx` values — possibly rewritten to 0/default by `build_modes_blob` or
  the per-song deploy path) or by runtime resolution — hardware experiments E1/E2/E4
  (in-VR) plus an idx audit stock-vs-patched per mode remain.

## M14 implementation consequences

- "Force one of the 16" = write the standard env's exact serialized name into
  `_environmentName` (layer 1) AND/OR set the idx in layer 2 — which layer WINS at runtime
  is the next research question (E-series).
- "Force target" = the stock pack's env (already in the blob — likely a no-op at layer 1).
- "Force blank" = what the runtime does with an unset/idx-0 binding (E4).
- The patch point is the SAME blob+object the mode patcher already rewrites → the
  `--environment` flag rides `build_modes_blob`'s rewrite (one mechanism, no new injection).

Cross-references: [[pack-bundle-patching]] (the raw-CAB machinery),
[[song-metadata-addressables-structure]] (the SO chain),
[[beatsage-charting-behavior]] (the 16-env list the webapp already carries).

## Exp 298 addendum — the data layer is FULLY mapped; the blank-env cause is runtime-side

- **Layer-2 idx audit (stock vs patched, AllTheGoodGirlsGoToHell):** `envIdx=0` for EVERY
  difficulty in BOTH (stock 5 entries; patched 4 modes × 5 entries — all `envIdx=0,
  schemeIdx=0`, only NJS/njo vary). The mode patch preserves idx values exactly → the
  "mode patch zeroes the idx" hypothesis is ALSO eliminated. Idx 0 evidently means
  "the level's own env" (layer 1).
- **The per-song bundle layer exonerated:** `<slot>_v3.bundle` (AudioClip + 22 beatmap
  TextAssets + ONE MonoBehaviour) carries **`BeatmapLevelDataSO`** (DataModels asm) whose
  schema has NO env fields at all (`_version`, `_audioClip`, `_audioDataAsset`,
  `_difficultyBeatmapSets[]` = characteristic name + per-difficulty beatmap/lightshow
  TextAssets). Nothing we ship carries or breaks an env binding.
- **Conclusion:** every shipped byte is env-correct (layer 1 = the pack's env, preserved).
  The blank-vs-working custom split is therefore a RUNTIME resolution behavior — which code
  path the game takes for a custom slot's env (and why it differs per song) is what the
  in-VR E1/E2/E4 experiments + bs_log evidence must pin. The `--environment` implementation
  still rides layer 1 (the pack SO string, patchable with the existing raw-CAB machinery) —
  the open question is whether the runtime honors it for custom slots, which E4 answers.

## Exp 299 addendum — the E-series field data: every SHIPPED byte is exonerated; the cause is runtime-side

The user's in-VR census (2026-11-13): env SHOWS for billieeilish ATTITUDE(Bellyache)/
Baddie(BuryAFriend)/Cosmic(HappierThanEver), lizzo The Middle(AboutDamnTime), ALL 5 BTS
customs; BLANK for ALL 11 Rolling Stones customs and the other billie/lizzo customs.

Eliminated by byte-level comparison (showing vs blank slots, deployed previews-variant
bundles + PS4-pulled per-song bundles):
1. Pack SO env strings — `BillieEnvironment`+`GlassDesertEnvironment` present at identical
   offsets for BOTH camps (all slots, both bundle variants).
2. `_previewDifficultyBeatmapSets` idx — envIdx=0, schemeIdx=0 for every entry, both camps.
3. Preview AudioClip PPtr — resolves to a real AudioClip object for BOTH camps (no dangles).
4. Per-song `BeatmapLevelDataSO` — structurally identical (version=1, same 8-byte template
   hash, 4 mode sets, no env fields in the class schema).
5. Beatmap/lightshow JSON — same schemas; lightshow-count distribution identical (1-2 both).
6. The bs_log opens — the game loads the SAME file set per browse in both camps (slot
   redirect + env-scenes bundle + PlayerData), and loads each pack's env assets+scenes fine
   (RS env bundle loads too — yet RS renders blank!).

The map's own Info.dat `_environmentName` (BeatSaver API, deployed-map correlation) does NOT
predict the split either (SHOWS = {Nice, ABSENT, ABSENT}; blank = {Panic, Panic, BigMirror,
BigMirror, ABSENT, ABSENT, ABSENT}) — though deployed-version drift is unverified.

**Conclusion: the env decision happens INSIDE the game's runtime resolution, on data we
cannot see via file opens.** The next diagnostic (and likely the M14 implementation itself):
**hook `BeatmapLevelSO.get_environmentName` (RVA 0x962230, returns `EnvironmentName`) in the
plugin** (the M11 IL2CPP-hooking machinery) — log what the game asks/receives per song while
the user browses a showing vs a blank song. If it returns the pack env for both, the failure
is downstream (scene instantiation); if it differs, the SO lookup is the culprit — and the
same hook becomes the per-song env OVERRIDE (no bundle patching needed at all).
