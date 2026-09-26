---
name: ps4-zero-byte-system-files
description: "0-byte files in /user/app/CUSA12878/ are normal PS4 system mount points, not corrupted game files"
metadata:
  type: reference
---

# PS4 0-Byte System Files in /user/app/CUSA12878/

## The Files

When listing `/user/app/CUSA12878/` via FTP on PS4, you'll see many 0-byte files:

system, usb, hostapp, SceSysAvControl.elf, eap_user, data, update,
system_data, host, preinst, eap_vsh, safemode.elf, user, mnt,
system_ex, mini-syscore.elf, app_tmp, preinst2, adm, hdd, dev, system_tmp

## These Are NOT Corrupted Game Files

**These are normal PS4 system mount points / special files.** They appear as 0 bytes because:
- They're not regular files — they're kernel mount points, device nodes, or sysfs entries
- The PS4's FTP server (GoldHEN) reports them as 0 bytes since they have no traditional file size
- They exist on EVERY PS4 for EVERY game/app — they're part of the PS4's sandbox filesystem structure

## What They Actually Are

| File | Type |
|------|------|
| system, data, update, system_data, system_ex, system_tmp | Mount points for system partitions |
| usb, host, hostapp | USB/host filesystem mounts |
| user, mnt | User/mount namespace |
| dev | Device nodes |
| preinst, preinst2 | Pre-installed content mounts |
| SceSysAvControl.elf, safemode.elf, mini-syscore.elf, app_tmp | System ELF modules (loaded from elsewhere, 0-byte stubs here) |
| eap_user, eap_vsh | EAP (Entitlement/App) mounts |
| adm, hdd | Admin/HDD mounts |

## The Backup Script Does NOT Create These

The backup script (backup-beat-saber-deluxe-files.py) only backs up/restores:
1. /data/GoldHEN/plugins/afr.prx and game_patch.prx
2. /data/GoldHEN/plugins.ini
3. /user/app/CUSA12878/ — whatever bundles/files exist there (custom songs, pack modes)
4. /data/GoldHEN/AFR/test/ and /data/GoldHEN/AFR/bs_log/ (preserved per GoldHEN topology)

It **faithfully copies whatever is at those paths**. If custom bundles are deployed there, it backs them up. If the directory is clean, it backs up an empty directory (just the 0-byte system files).

## Root Cause of "Data Corrupted" Error (Sep 2026)

The error was **NOT** caused by 0-byte system files. It was caused by:

1. **Custom song bundles** (60+ .bundle files) in /user/app/CUSA12878/ — deployed by the BSD pipeline during testing. The game's content verification detects these as unauthorized modifications.

2. **/data/GoldHEN/AFR/CUSA12878/ directory** — created by pipeline deployments. This directory doesn't exist on a stock PS4.

## Resolution

Remove all custom bundles from /user/app/CUSA12878/ and remove /data/GoldHEN/AFR/CUSA12878/. The stock game then launches normally.

## Prevention for Future

- Always clean /user/app/CUSA12878/ of custom bundles before testing stock game launch
- The backup script's --clean-ps4 flag removes /user/app/CUSA12878/ custom content
- The backup script's clean operation also removes the [CUSA12878] section from plugins.ini (the BSD plugin entry that can cause boot crashes)

## Key Takeaway

**0-byte files in /user/app/CUSA12878/ = normal PS4 behavior. Custom .bundle files there = "data corrupted" error.**