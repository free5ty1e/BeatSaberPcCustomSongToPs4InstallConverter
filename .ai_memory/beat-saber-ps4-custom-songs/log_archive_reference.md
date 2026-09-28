# Archived Log Reference

> **Note (2026-08-01):** Raw PS4 logs are now archived directly in
> `.ai_memory/experiment_logs/` (version-specific filenames like
> `v0.8047_<desc>.txt`) — the download IS the archival copy, per workflow rules.
> Per-feature experiment documentation archives live in
> `experiment_log_archive/` in this directory.

| File | Version | Date | Key Content | Result |
|------|---------|------|-------------|--------|
| `v0.69_klass_not_found.txt` | v0.69 | 2026-07-17 | First memory injection test, mincore | "Class string not found" |
| `v0.69_klass_not_found_mincore_broken.txt` | v0.69 | 2026-07-17 | mincore test | mincore returns 0 for everything |
| `ps4_log_v0.69.txt` | v0.69 | 2026-07-17 | msync test | Same "Class string not found" |
| `v0.71_debug_verbose_log.txt` | v0.71 | 2026-07-19 | Signal handlers, VERBOSE_LOG, bounds check discovery | 🔍 **Found bounds reject bug** (4GB threshold) |
| `v0.72_bounds_fix_verbose_log.txt` | v0.72 | 2026-07-19 | Bounds check fixed to 16MB | ✅ try_read_mem works, but **"String not in module"** |
| `v0.79_strdebug_empty_log.txt` | v0.79 | 2026-07-19 | STRDEBUG diagnostic, 743 lines | ⏳ **Scan didn't fire** — user didn't press Play |
