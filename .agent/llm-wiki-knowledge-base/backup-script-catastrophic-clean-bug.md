---
name: backup-script-catastrophic-clean-bug
description: "Critical bug in backup script clean operation that deleted base game files (app.pkg, app.json, etc.)"
metadata:
  type: reference
---

# CRITICAL BUG: Backup Script Clean Operation Deleted Base Game Files

## What Happened (Sep 2026)

The `clean_ps4()` function in `backup-beat-saber-deluxe-files.py` called `ps4_rmdir_recursive(PS4_USER_APP_CUSA12878)` which **deleted the ENTIRE `/user/app/CUSA12878/` directory**, including:

| File | Size | Description |
|------|------|-------------|
| `app.pkg` | ~254MB | v1.00 launcher shell (REQUIRED for game to launch) |
| `app.pbm` | ~774B | Content info manifest |
| `app.json` | ~258B | Package metadata |
| `app.xml` | ~279B | PlayGo status |

## Root Cause

The clean operation was designed to remove "AFR/CUSA12878 custom content" but used a **recursive directory delete** instead of surgical file removal. The comment said "Remove AFR/CUSA12878 from /user/app/CUSA12878/" but the implementation deleted the entire game installation directory.

## Impact

- **Game shows "Data is corrupted. Delete and reinstall."**
- **Base game launcher completely missing**
- **DLC (patch.pkg at /user/patch/CUSA12878/) is intact**
- **Save data is intact**

## The Fix (v0.5329+)

1. **Added protected file lists** that are NEVER deleted:
   - `PROTECTED_BASE_GAME_FILES`: `app.pkg`, `app.pbm`, `app.json`, `app.xml`
   - `PROTECTED_SYSTEM_MOUNTPOINTS`: 20+ 0-byte system files (normal PS4 behavior)
   - `BASE_GAME_DIRECTORIES`: `Plugins`, `custom_songs`, `pack_modes_bundles`, `sce_sys`

2. **Surgical clean operation** that only removes known custom content patterns:
   - `custom_songs/*.bundle`
   - `pack_modes_bundles/*.bundle`
   - `Plugins/*.prx`
   - Root level: `*_v3.bundle`, `*_custom_v3.bundle`, `catalog_pack_modes.json`, `redirects.json`, `song_metadata.json`, `features.json`, `bs_log.txt`

3. **Verification step** in `verify_ps4_clean()` that checks base game files are still present after clean

## Prevention

- **NEVER use recursive directory deletion** on `/user/app/CUSA12878/`
- **ALWAYS verify base game files exist** after any clean operation
- **Protected file lists are enforced** at the delete point with explicit continue

## Recovery

If this happens again:
1. Base game (`app.pkg`, `app.json`, `app.pbm`, `app.xml`) must be reinstalled
2. DLC (`patch.pkg` at `/user/patch/CUSA12878/`) is separate and unaffected
3. Save data (`/user/home/.../savedata/CUSA12878/`) is separate and unaffected
4. License files (`/user/license/`) are separate and unaffected

## Lesson Learned

**A "clean" operation for modding must be surgical, not destructive.** The line between "custom content" and "base game installation" must be explicitly defined and enforced.