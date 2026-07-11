---
name: ps4-file-system-redirects
description: "How the PS4 file system redirect works via AFR partition and open() hook"
metadata:
  type: concept
---

# PS4 File System & Redirects

## Plugin Redirect Table (beat_saber_deluxe.prx v0.44)

The redirect table is defined in `src/main.cpp` line 64-65:

```cpp
if (strstr(path, "BeatmapLevelsData/startmeup"))
    np = AFR_BASE "/" TITLE_ID "/startmeup_v3";
```

### ⚠️ CRITICAL: Deploy Path Must Match Plugin Redirect

| Plugin matches | Redirects to | Deploy absolute path |
|---|---|---|
| `BeatmapLevelsData/startmeup` | `startmeup_v3` | `/data/GoldHEN/AFR/CUSA12878/startmeup_v3` |

**Deploying to `startmeup` instead of `startmeup_v3` will have NO EFFECT.**
The bundle will sit on the PS4 but never be loaded by the game.

### Current Active Redirects (v0.44)

Only **one** redirect is active:
- `BeatmapLevelsData/startmeup` → `startmeup_v3`

To add more, modify `main.cpp` and add new `if (strstr(...))` clauses before the fallthrough.

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
/data/GoldHEN/AFR/CUSA12878/startmeup_v3   ← the custom AssetBundle
```

### Redirect Mechanism
The plugin hooks `open()` and checks if the path contains a target string:
```cpp
if (strstr(path, "BeatmapLevelsData/startmeup"))
    np = AFR_BASE "/" TITLE_ID "/startmeup_v3";
```
When matched, it replaces the original path with the AFR path and calls `open()` on the redirected path.

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

## Important Notes
- The redirect only intercepts the specific song file — other songs load normally
- The environment/scene bundles also load normally (no redirect needed)
- If the redirect target file doesn't exist, the original open() call returns -1 (file not found), causing the game to fail gracefully (return to menu)

See also: [[plugin-architecture]], [[toolchain-and-build]], [[development-workflow]]
