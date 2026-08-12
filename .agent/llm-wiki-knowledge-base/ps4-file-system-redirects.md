---
name: ps4-file-system-redirects
description: "How the PS4 file system redirect works via AFR partition and open() hook"
metadata:
  type: concept
---

# PS4 File System & Redirects

## Redirect Source of Truth (v0.5318+)

Redirects are **dynamic**, loaded by the plugin at runtime from `redirects.json` on the PS4
(`/data/GoldHEN/AFR/CUSA12878/redirects.json`), NOT hardcoded in `main.cpp`. `load_redirects()`
parses the JSON pairs; for each value without a `/`, the plugin prepends
`AFR_BASE "/" TITLE_ID "/"` (see `src/main.cpp` `load_redirects`, e.g. line 187).

### ⚠️ CRITICAL — Redirect VALUE naming rule (Exp 187)

- The plugin opens the redirect **VALUE verbatim** (`AFR_BASE/TITLE_ID/` + value), and `open()`
  is **case-sensitive** → the value MUST byte-match the exact deployed bundle filename.
- A value like `Crystallized_v3` silently keeps serving the STALE build while the freshly
  deployed `crystallized_v3.bundle` sits unused — the game never errors (stale file exists).
- Deployed bundle name = **canonical slot casing** (from `mass_deploy.slots`, matched
  case-insensitively) + `paths.afr_target_suffix` (default `_v3.bundle`).
- Pipeline enforcement: `_deployed_bundle_name()` (single source of truth) +
  `_ensure_mass_song_redirects()` (runs on EVERY `manage_redirect_config` save, like the
  pack/catalog pair): keeps known-good redirect KEYS, fixes VALUES to exact deployed names,
  drops stale pre-`.bundle` entries, adds missing slots.
- Keys are matched **case-insensitively** via lowered `strstr`, so key casing doesn't matter;
  only the VALUE must be exact.

### ⚠️ CRITICAL: AFR vs Plugin Deploy Paths

**Two separate mechanisms exist on GoldHEN, with different directories:**

### 1. AFR (Application File Redirect) — Asset Bundles Only

**Path:** `/data/GoldHEN/AFR/<TITLE_ID>/`
**Purpose:** Stores redirected AssetBundle files (song bundles, resources)
**Config:** Redirect table in `redirects.json` loaded by the plugin at runtime
**Deploy command:**
```bash
lftp -u anonymous, -p 2121 192.168.100.117 \
  -e "put custom_song.bundle -o /data/GoldHEN/AFR/CUSA12878/startmeup_v3.bundle; quit"
```

### 2. GoldHEN Plugins — PRX Plugin Files

**Path:** `/data/GoldHEN/plugins/`
**Purpose:** Stores `.prx` plugin files loaded by GoldHEN's plugin loader
**Config:** `/data/GoldHEN/plugins.ini` maps plugin files to game title IDs
**Deploy command:**
```bash
lftp -u anonymous, -p 2121 192.168.100.117 \
  -e "put beat_saber_deluxe.prx -o /data/GoldHEN/plugins/beat_saber_deluxe.prx; quit"
```

**plugins.ini content:**
```
[default]
/data/GoldHEN/plugins/game_patch.prx

[CUSA12878]
/data/GoldHEN/plugins/beat_saber_deluxe.prx
```

**IMPORTANT:** Uploading the plugin PRX to the AFR directory has NO EFFECT — GoldHEN's plugin loader reads from `plugins/` as configured in `plugins.ini`. The AFR directory is for **asset redirects only**, not plugin loading. This mistake cost several test cycles (v0.71 deployed to AFR instead of plugins/).

| Plugin matches | Redirects to | Deploy absolute path |
|---|---|---|
| `BeatmapLevelsData/startmeup` | `startmeup_v3.bundle` | `/data/GoldHEN/AFR/CUSA12878/startmeup_v3.bundle` |

**Deploying to `startmeup` instead of `startmeup_v3.bundle` will have NO EFFECT.**
The bundle will sit on the PS4 but never be loaded by the game.

### Current Active Redirects (v0.5318)

40 redirects in `redirects.json`: 38 song slots (`BeatmapLevelsData/<slot>` →
`<slot>_v3.bundle`) + the pack pair (`aa/catalog.json` → `catalog_startmeup_modes.json` and
`therollingstones_pack_assets_all_*.bundle` → `startmeup_pack_modes.bundle`, see
[[pack-bundle-patching]]). To add more, use the pipeline (`--generate-config`) — it merges
into the existing `redirects.json` and enforces naming + the pack pair on every save.

## AFR (Application File Redirect)

GoldHEN's AFR mechanism allows intercepting file reads from the game's archive partition and redirecting them to files on the console's internal storage. This is the foundation of the custom song system — without AFR, we couldn't modify any game files (the game directory is read-only via FTP).

### Directory Structure
```
/data/GoldHEN/AFR/<TITLE_ID>/<filename>
```
Where:
- `<TITLE_ID>` is the game's ID (e.g., `CUSA12878`)
- `<filename>` is the name the game will look up when redirected

For Beat Saber:
```
/data/GoldHEN/AFR/CUSA12878/startmeup_v3.bundle   ← the custom AssetBundle
```

### Redirect Mechanism
The plugin hooks `open()` and checks if the path contains a target string (from the dynamic
redirects.json, matched case-insensitively):
```cpp
if (strstr(lowercased_path, "beatmaplevelsdata/startmeup"))
    np = AFR_BASE "/" TITLE_ID "/startmeup_v3.bundle";
```
When matched, it replaces the original path with the AFR path and calls `open()` on the
redirected path (the VALUE is opened verbatim — case-sensitive, byte-exact).

### Permission Fix
AFR directories need proper permissions via `sceKernelMkdir` and `sceKernelFchmod`:
```cpp
sceKernelMkdir(AFR_BASE, 0777);
sceKernelMkdir(AFR_BASE "/" TITLE_ID, 0777);
// File permissions set during log_write
sceKernelFchmod(fd, 0644);
```

## FTP Access
- FTP server on port 2121 (not the default 21)
- User: `anonymous` with blank password
- Upload to: `/data/GoldHEN/AFR/CUSA12878/<filename>`
- `lftp` is used for batch operations:
```bash
lftp -u anonymous, -p 2121 192.168.100.117 -e "put <local> -o <remote>; quit"
```

## File Open Lifecycle
When the game opens a BeatmapLevelData file:
1. Game calls `open("...BeatmapLevelsData/startmeup")`
2. Hook intercepts, logs the call, replaces path
3. Game receives handle to our custom bundle file
4. Unity loads the AssetBundle from the handle
5. Game uses assets from the bundle as if they were the original

## PS4 Stale-File Hygiene (Exp 187)
- The Aug-13 mass redeploy left BOTH old `<slot>_v3` files (no `.bundle`) AND fresh
  `<slot>_v3.bundle` files on the PS4. The `--verify-ps4` size check could NOT catch stale
  redirects because the stale file also exists. Cleanup: `development/scripts/cleanup_ps4_stale.sh`
  (dry-run default). **Order matters: deploy the corrected `redirects.json` FIRST, then delete
  stale files** — old redirect values still point at `_v3` files; deleting those first crashes boot.

## Important Notes
- The redirect only intercepts the specific song file — other songs load normally
- The environment/scene bundles also load normally (no redirect needed)
- If the redirect target file doesn't exist, the original open() call returns -1 (file not found), causing the game to fail gracefully (return to menu)

See also: [[plugin-architecture]], [[pack-bundle-patching]], [[toolchain-and-build]], [[development-workflow]]
