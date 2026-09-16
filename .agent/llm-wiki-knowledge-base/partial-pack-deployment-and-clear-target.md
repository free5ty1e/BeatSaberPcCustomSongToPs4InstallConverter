---
name: partial-pack-deployment-and-clear-target
description: Partial pack deployment fix and --clear-target-song parameter for reverting custom songs.
metadata:
  type: architecture
---

# Partial Pack Deployment & Clear Target Song

## Problem: Partial Pack Crashes

When deploying custom songs one at a time (single-song `--deploy-full`), the pipeline builds pack mode bundles that add 4 preview mode sets (Standard, OneSaber, NoArrows, 90Degree) for **every song in the pack**. If you only replaced 2 of 10 songs in the Billie Eilish pack, the other 8 stock songs would also have their preview arrays patched to show the extra modes. Selecting a stock song and trying to play OneSaber/NoArrows/90Degree would crash because those songs don't have the corresponding beatmap assets — they only have Standard beatmaps.

## Solution: Surgical Pack Bundle Patching + Runtime Feature Flag

### 1. Runtime Feature Flag: `enable_beatmap_mode_mapping`

**Plugin v0.8041+** reads `enable_beatmap_mode_mapping` from `features.json` at startup. This flag gates whether the extra mode sets in pack bundles are visible in the mode selector UI.

- **OFF (default when missing):** Extra mode sets in pack bundles are hidden. ALL songs (custom and stock) show only Standard mode. Safe for partial deployments.
- **ON:** Custom songs with their own patched mode sets show all 4 modes. Stock songs (whose BeatmapLevelSOs still only have Standard in their preview arrays) also only show Standard.

This is the primary safety mechanism — you can deploy custom songs one at a time with the feature flag OFF, and enable it only when the full pack is replaced.

### 2. Surgical Pack Bundle Patching: `target_slots` Parameter

Since v0.5334, `build_pack_mode_bundles.py` accepts a `target_slots` parameter that limits which song slots get their BeatmapLevelSO preview arrays patched:

```python
build_pack_mode_bundles(
    song_ids_path=...,
    dump_dir=...,
    out_dir=...,
    packs=["billieeilish"],
    enable_modes=["OneSaber", "NoArrows", "90Degree"],
    target_slots=["AllTheGoodGirlsGoToHell", "BadGuy"]  # only these two get patched
)
```

When `target_slots` is provided:
- Only the specified song IDs have their BeatmapLevelSO preview arrays extended with extra modes
- All other songs in the pack remain untouched (only Standard in their preview arrays)
- The pack bundle is still valid and the merged catalog CRC/size is updated correctly

### 3. Pipeline Integration

The main pipeline (`full_custom_song_pipeline.py`) now automatically:
1. Detects which modes the custom song has (auto-detect + generation)
2. Resolves the target song's pack via `_resolve_target_pack()`
3. Scopes the pack bundle build to **only that pack** and **only that song slot**
4. Passes `enable_modes` (non-Standard modes) and `target_slots=[target_slot]` to the pack bundle builder

This means `--deploy-full` for a single song only patches that song's preview array in the pack bundle. The other 9 songs remain with only Standard — safe even if the feature flag is ON.

### 4. Default Behavior for `--deploy-full`

```bash
python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song 4a901 \
    --target AllTheGoodGirlsGoToHell \
    --pcm16 --no-pad --convert-to-v3 \
    --deploy-full
```

This now:
- Builds the custom song bundle with all 4 modes
- Builds the pack bundle (`billieeilish`) with extra modes ONLY for `AllTheGoodGirlsGoToHell`
- Deploys song bundle + pack bundle + merged catalog + redirects + features.json + plugin
- The pack bundle has 4 preview sets for the custom song, 1 preview set (Standard) for the other 9 songs
- With `enable_beatmap_mode_mapping=true` in features.json, only the custom song shows 4 mode buttons

---

## New Parameter: `--clear-target-song <SLOT>`

Reverts a custom song slot back to its stock state without a full PS4 clean slate.

### What it does:

```bash
python3 tools/full_custom_song_pipeline.py --clear-target-song AllTheGoodGirlsGoToHell
```

1. **Removes the custom song bundle** from PS4 AFR directory (`/data/GoldHEN/AFR/CUSA12878/AllTheGoodGirlsGoToHell_v3.bundle`)
2. **Removes the redirect entry** from `redirects.json` (both local and PS4)
3. **Removes song metadata** from `song_metadata.json`:
   - `song_names["all the good girls go to hell"]` → deleted
   - `song_artists["Billie Eilish"]` → deleted
4. **Deploys updated configs** (redirects.json, song_metadata.json) to PS4

### What it does NOT do:

- Does NOT rebuild the pack bundle (the pack bundle will still have the extra mode sets for that slot, but since the redirect is gone, the game loads the original stock bundle which only has Standard)
- Does NOT remove the plugin or features.json
- Does NOT affect other custom songs in the same pack

### Use Cases:

- **Test a different custom song** in the same slot: clear first, then deploy new song
- **Debug a problematic custom song**: clear it to verify the stock song plays correctly
- **Partial pack rollback**: remove just one song without rebuilding the whole pack

---

## Workflow: Safe Partial Pack Deployment

### Option A: Feature Flag OFF (Safest, No Extra Modes)
```bash
# 1. Disable mode mapping UI
python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_beatmap_mode_mapping=false

# 2. Deploy custom songs one at a time
python3 tools/full_custom_song_pipeline.py --download-beat-saver-song 4a901 --target AllTheGoodGirlsGoToHell --pcm16 --no-pad --convert-to-v3 --deploy-full
python3 tools/full_custom_song_pipeline.py --download-beat-saver-song 1dbb9 --target BadGuy --pcm16 --no-pad --convert-to-v3 --deploy-full
# ... more songs ...

# 3. When pack is complete, enable mode mapping
python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_beatmap_mode_mapping=true
```

### Option B: Feature Flag ON (Surgical Patching, Default in v0.5334+)
```bash
# Deploy custom songs one at a time — pack bundle only patched for deployed songs
python3 tools/full_custom_song_pipeline.py --download-beat-saver-song 4a901 --target AllTheGoodGirlsGoToHell --pcm16 --no-pad --convert-to-v3 --deploy-full
python3 tools/full_custom_song_pipeline.py --download-beat-saver-song 1dbb9 --target BadGuy --pcm16 --no-pad --convert-to-v3 --deploy-full
# ... more songs ...
# Each deploy only adds extra modes for THAT song in the pack bundle
# Stock songs remain Standard-only — no crashes possible
```

---

## Related Files

- `beat_saber_deluxe/tools/build_pack_mode_bundles.py` — `patch_pack_bundle()` with `target_slots` parameter
- `beat_saber_deluxe/tools/full_custom_song_pipeline.py` — `--clear-target-song` parameter, single-song deploy scoping
- `beat_saber_deluxe/src/main.cpp` — `g_feature_beatmap_mode_mapping` feature flag gate
- `beat_saber_deluxe/CHANGELOG-PIPELINE.md` — v0.5334 entry

---

## See Also
- [[feature-flags]] — feature flag architecture and defaults
- [[pipeline-afr-base-fix-clean-slate]] — clean slate workflow
- [[procedural-mode-generators]] — build-time mode generators