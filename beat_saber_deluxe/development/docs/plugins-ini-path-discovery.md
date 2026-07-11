---
name: plugins-ini-path-discovery
description: "Critical finding: GoldHEN reads /data/GoldHEN/plugins.ini (root level), NOT /data/GoldHEN/plugins/plugins.ini (subdirectory)"
metadata:
  type: reference
---

## plugins.ini Path Discovery

**Date:** 2026-06-11
**Severity:** 🔴 Critical — ALL prior experiments invalidated by this

**The problem:** GoldHEN reads its plugin configuration from `/data/GoldHEN/plugins.ini` (root level), but we were deploying our config to `/data/GoldHEN/plugins/plugins.ini` (subdirectory). The root file contained RB4DX entries but no reference to `beat_saber_deluxe.prx`.

**Evidence:** FTP listing showed two plugins.ini files:
- `/data/GoldHEN/plugins.ini` (477 bytes, Apr 1) — original, has RB4DX entries, NO Beat Saber entry
- `/data/GoldHEN/plugins/plugins.ini` (351 bytes, Jun 11) — our deploy, has Beat Saber entry, but GoldHEN never reads this

**Impact:** All experiments 4b through 4f had correct code but were never registered with GoldHEN. The four root causes in order of discovery:
1. Wrong container format (fself vs .oelf signed ELF)
2. TLS segment from musl libc
3. Duplicate LOAD program header
4. Wrong plugins.ini deployment path ← THIS was the critical one

**Fix:** Updated `/workspace/plugins.ini` to preserve existing RB4DX entries and add Beat Saber, then deployed to `/data/GoldHEN/plugins.ini`.

**See also:** [[experiment-4f-init-entry-point]]
