---
name: pipeline-deploy-full-download-guard-ordering
description: "Root cause: --deploy-full --download-beat-saver-song skipped song conversion because the BeatSaver download ran AFTER main()'s plugin-only early-exit guard."
metadata:
  type: reference
---

# `--deploy-full --download-beat-saver-song` Silently Skipped Song Conversion

**Introduced:** v0.5332 (Exp 214, 2026-09-08)

## The Problem

The user's very first single-song install failed silently. The command was:

```bash
python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song 4a901 \
    --target AllTheGoodGirlsGoToHell \
    --pcm16 --no-pad --convert-to-v3 --deploy-full
```

Observed behavior (only 3 log lines before the prompt returned):

```
[INFO] Deploying plugin to PS4: /data/GoldHEN/plugins/beat_saber_deluxe.prx
[WARNING]   ⚠️ Plugin deploy failed (PS4 offline?): put: /wat_saber_deluxe.prx: No such file or directory
[INFO] Plugin deployment complete (no song processed)
[INFO]   Saved redirects.json (43 redirects)
[INFO]   ✅ Redirect config deployed
```

No song was downloaded, no plugin was built, and a **43-entry unscoped `redirects.json`**
was deployed to a single-song request. PS4 state afterward showed only `redirects.json`
present — zero custom songs, zero modified packs.

## Root Cause

In `tools/full_custom_song_pipeline.py` `main()`, the **BeatSaver auto-download** that
populates `args.song_dir` was positioned *after* the `plugin-only` early-exit guard:

```python
# (old order — BROKEN)
if args.deploy_plugin and not args.song_dir:   # <-- plugin-only guard fires here
    deploy_plugin(os.path.join(PROJECT_ROOT, 'beat_saber_deluxe.prx'), ...)
    manage_redirect_config(..., target_name=None, ...)   # 43 unscoped redirects
    sys.exit(0)
# ...
# (300 lines later) the download that *would* have set args.song_dir:
if args.download_beat_saver_song and not args.song_dir:
    args.song_dir = download_beat_saver_song(...)
```

Because `--deploy-full` sets `args.deploy_plugin = True`, the guard
`if args.deploy_plugin and not args.song_dir:` evaluated to `if True and True:`
— since `--download-beat-saver-song` had not yet been translated into `args.song_dir`.
The run was shunted into **"plugin-only mode"**, which:

1. Tried to `upload` a `.prx` that was never built (the song path's Step 8
   `build_plugin()` — the only place the plugin gets compiled — was never reached),
   producing the truncated-path `put: /wat_saber_deluxe.prx` error (the local path
   `/workspace/.../beat_saber_deluxe.prx` was mangled in lftp's `<file` feedback).
2. Regenerated **43 unscoped redirects** with `target_name=None` (full mass_deploy slot
   list), deploying a config that had nothing to do with the single target song.
3. Called `sys.exit(0)` before the song was ever downloaded or converted.

## The Fix

Move the `--download-beat-saver-song` → `args.song_dir` resolution to the **top of
`main()`**, immediately after `load_config()`, *before* the `features-only` /
`plugin-only` / deploy-only / plugin-toggle early-exit guards:

```python
config = load_config(args.config)
cfg_ps4 = config.get('ps4', {})
cfg_title = config.get('title', {})
cfg_paths = config.get('paths', {})

# Auto-download from BeatSaver if requested (BEFORE all early-exit guards)
if args.download_beat_saver_song and not args.song_dir:
    args.song_dir = download_beat_saver_song(args.download_beat_saver_song,
                                              api_base=args.beatsaver_api_base)
elif args.download_beat_saver_song and args.song_dir:
    log.info(f"Using local song directory: {args.song_dir} ...")

# ... now the plugin-only / deploy-only / toggle guards safely evaluate song_dir
```

Now `song_dir` is non-`None` by the time any guard runs, so a single-song `--deploy-full`
correctly reaches the full song-processing path: download → audio convert → beatmap mode
generation → BeatmapLevelSO metadata injection → bundle → **build+deploy plugin** →
scoped single-pack deploy + scoped redirects + validation.

## Lesson

`main()` in this pipeline uses a flat sequence of mutually-exclusive "mode" early-exit
guards (plugin-only, deploy-only, plugin-toggle, then the song path), each keyed on
combinations of `args.*` booleans. **Any argument that *resolves into* another argument
must be resolved BEFORE those guards** — otherwise a flag like `--download-beat-saver-song`
(which populates `args.song_dir`) is treated as "absent" by the guards and the wrong mode
is selected.

Guarding invariant: resolution-of-inputs → mode-selection guards → work.
Never: mode-selection guards → resolution-of-inputs.

See also `[[pipeline-single-song-deploy|pipeline-single-song-deploy]]` (the
scoping fix this builds on) and `[[pipeline-deploy-full-orchestration|pipeline-deploy-full-orchestration]]`.