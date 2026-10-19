---
name: game-data-extractor
description: "M12's in-console game-data extractor: how the plugin copies the files the pipeline needs out of the game's own mounts (eliminating the PC-side dump requirement for users), the requests/status ownership split, idempotence + ERR-retry, measured footprints, the fresh-user bootstrap order, and the web-app integration lessons."
metadata:
  type: feature
---

# Game-Data Extractor (M12)

Shipped in plugin v0.8054 / pipeline v0.5364 / webapp 0.6.14 (Exp 280).
User-facing doc: `docs/features/game-data-extractor.md` (ships in the release zip).
Feature flag: `enable_game_data_extractor` (defaults false; console-maintenance
tooling — NOT gated by the kill switch, like [[in-game-plugin-toggle]]).

## The core discovery — the game's own mounts are readable in-process

The game reads its assets from **`/archive/mount/point/Media/...` (1,067 opens)
and `/app0/Media/...` (1,073 opens)** — both counted from the archived v0.8052
boot log, and both mounted decrypted inside the game process. The plugin can
`sceKernelOpen` those paths itself (bypassing its own open-hook — no
redirection interference) and stream-copy any of them to the AFR dir. **The
dump requirement existed only because it predated the plugin's capabilities** —
once the plugin could read game files, nobody revisited the question.

## What the pipeline actually needs (measured from the real 4.9GB dump)

| File | Per unit | Full 5-pack loadout |
|---|---|---|
| Per-slot templates (`Media/StreamingAssets/BeatmapLevelsData/<slot>`, single UnityFS files) | ~13.24 MB | 622 MB (47 slots) |
| Pack bundles (`aa/PS4/<pack>_pack_assets_all_<hash>.bundle`) | ~7 MB | 34.8 MB (5 packs) |
| Origin catalog (`aa/catalog.json`) | 0.79 MB | 0.79 MB |
| **Total** | **~140 MB per pack** | **658 MB** |

The manifest is computed from `beat_saber_song_ids.json` (ships in the repo —
**no dump needed to compute it**). A single-slot request automatically includes
its pack's bundle (pack-mode patching needs it) + the catalog.

## The ownership split (pull-before-push doctrine applied to plugin files)

- `game_data_requests.txt` — **pipeline/web-app OWNED** (one relative path per
  line, `#` comments). The plugin only READS it.
- `game_data_status.txt` — **PLUGIN OWNED** (one extracted path per line;
  `ERR <rel> <reason>` lines mark failures). The web app only READS it.
- No file is written by both sides → the stale-push class of bug
  ([[feature-flags]] Exp 248) is structurally impossible here.

## Idempotence + retry design

- **Line-exact done-matching** (`gamedata_line_present`): a rel that is a
  SUFFIX of another (`catalog.json` vs `aa/catalog.json`) can never false-match
  as done — substring matching would skip re-extraction incorrectly.
- **ERR lines retry for free**: a failed file's `ERR …` status line never
  matches a request line, so the next boot re-attempts it automatically.
- The run happens once per boot, lazily from the first `open_hook` call where
  the mounts resolve (open_hook only fires once the game opens files — the
  mounts are up by then; earlier attempts are cheap failed opens).
- **Case:** the PS4 FS is case-insensitive (the plugin's read resolves any
  casing), but the local PC cache is not — the manifest uses the ids-file
  casing so `--template` resolves the cached file verbatim.

## The fresh-user bootstrap order (the chicken-and-egg)

**The extractor lives in the plugin, but a fresh user has no song data to
deploy a plugin with** (song deploys deploy the plugin via `--deploy-full`).
The correct order (and the web-app flow that implements it):

1. **Deploy the plugin first** — the plugin-only surface
   (`POST /api/jobs/deploy-plugin` → `--deploy-plugin`; the Deploy tab card +
   the Get Started step-5 button). In a release extraction the pipeline falls
   back to the bundled `plugins/*.prx` binary (Exp 235) — no source needed.
2. Arm `enable_game_data_extractor` (Feature Flags tab).
3. Request the packs/songs (Dump Guide Option A).
4. Boot the game once (extraction happens during a normal boot).
5. Pull + "Use the extracted cache" (points `paths.game_dump_dir` at
   `./game_data` — the ONLY change a user makes; the cache mirrors the dump
   layout exactly, so the pipeline needs zero changes).
6. Deploy songs as usual — cache-only builds.

**Lesson from the gap:** the M12.4 checklist originally said "Deploy plugin
(tab)" — no such surface existed, because plugin deploys historically rode on
song deploys. The fresh-user flow made the gap visible; the fix (webapp 0.6.15)
added the explicit surface. **UX lesson: when a feature creates a new
bootstrap order, audit every step of that order for an existing UI action —
don't assume "the pipeline can do it" means "the user can click it."**

## Web-app integration notes

- Both operations are **pipeline subprocesses** (`--request-game-data`,
  `--pull-game-data`) — the thin-layer doctrine held; the webapp adds only
  state reads (`GET /api/game-data/state`) + the config switch
  (`POST /api/game-data/use-cache`, refuses an empty cache with a fix message).
- **The `__main__`-guard bug class:** FastAPI routes appended AFTER
  `if __name__ == "__main__": main()` NEVER REGISTER — `uvicorn.run` blocks
  forever, so the decorators below it never execute (symptom: 404 on new
  endpoints while `import server` looks fine). All route definitions must
  live before the guard.
- The DEBUG plugin option is deliberately exposed only on the Deploy tab (user
  directive) — Get Started's plugin button always deploys the release build.
- `--pull-game-data` uses lftp `mirror --parallel=4` (resumable; identical
  files skip — the same idempotence property as [[lftp-ftp-pitfalls]]' sound
  upload-skip rule).

## Legality principle

Per-user extraction from the user's own console = clean (a backup of their own
game). Nothing game-derived is ever committed: the repo ships only the
tooling. This is the same principle as the ps4_dump disclaimer, extended: the
dump is now a DEVELOPER-only artifact (research, parity checks); users never
hold one. The end-state alternative (zero stock bytes) is the custom-album
exploration (M14).

## Related
- [[feature-flags]] — the 6th runtime flag
- [[in-game-plugin-toggle]] — the other console-maintenance feature (the
  kill-switch-independence precedent)
- [[lftp-ftp-pitfalls]] — the banner-free read/mirror patterns used by the
  pull flow
- [[plugin-architecture]] — the lazy open-hook trigger pattern
