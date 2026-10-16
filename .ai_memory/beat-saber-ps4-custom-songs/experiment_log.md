---
name: experiment-log
description: "Active experiment log for the CURRENT feature only (M11: In-Game Global Plugin Enable/Disable Toggle — L3+R3 hotkey). Per-feature rotation: when a feature concludes, archive this file into experiment_log_archive/ and open a fresh log. Experiment numbers are globally sequential across the whole project."
metadata:
  node_type: memory
  type: reference
---

# Experiment Log: Beat Saber PS4 Custom Song Support — M11 In-Game Plugin Toggle

**Feature:** Toggle the global plugin ON/OFF from inside the game with only a
controller — hold **L3+R3 for 2 seconds** on a DualShock 4 → the plugin flips
`enable_plugin` inside `features.json` (persist-only; a notification shows the
new state; **restart Beat Saber to apply** — user-approved). No PC required to
switch between all-custom and 100% stock. Feature flag:
`enable_in_game_plugin_toggle` (new, defaults false). Plan:
`.agent/plans/in-game-global-plugin-enable-toggle-plan.md`.
**Started:** 2026-10-14 (Exp 278)
**System:** PS4 FW 9.00, GoldHEN 2.3 / 2.4b16.2
**Archive:** Exps 268-277 (M10 Song Previews) → `experiment_log_archive/experiment_log_song-previews_exp268-277_2026-10-09_to_2026-10-14.md`

---

### Experiment 278: M11 kickoff — research COMPLETE (every open question resolved against real bytes); design locked; implemented plugin v0.8049 + pipeline v0.5363 + webapp 0.6.7 (2026-10-14)
- **User:** approved the in-game toggle direction with refinements: new feature flag behind the hotkey; **L3+R3 held 2 seconds** (not the earlier L1+R1+Touchpad sketch); notification showing the updated state; accidental triggers during Move gameplay must be impossible; **restart-after-toggle totally acceptable**; deploy/test experiment via the web UI; transcribe CLAUDE.md into the Pi rule file (AGENTS.md) + a 3-way rule-sync rule (claude/opencode/pi); full documentation (transcript, experiment log, KB) — not just the roadmap. Also: the exploration doc was renamed/upgraded to `.agent/plans/in-game-global-plugin-enable-toggle-plan.md`.
- **Research — every open question RESOLVED, verified against real bytes + two independent SDK sources:**
  - **The game reads pads via native `scePadRead`** — NOT `scePadReadState`, NOT a managed Input.GetKey hook. Proven by decoding ALL 849 NID-obfuscated dynamic imports of the decrypted eboot (new reusable script `development/scripts/ps4_elf_imports.py`: PS4 ELFs have no section headers; DT_SCE_* dynamic-tag values are offsets relative to the PT_SCE_DYNLIBDATA segment — proven self-consistent: strtab 0x18+strsz 0x3ca0==symtab 0x3cb8; symtab+symtabsz==jmprel) joined against shadPS4Plus's aerolib NID DB (94,276 entries; 846/849 decoded). Beat Saber imports scePadInit/Open/Close/Read + 10 more libScePad functions.
  - **Move-proof by construction:** Moves are read via the separate `libSceMove` (`sceMoveReadStateRecent` etc. in the imports) — `scePadRead` polls carry DS4-class pads only; a Move physically cannot set L3/R3 bits.
  - **Button bits + layout dual-verified** (OpenOrbis `orbis/_types/pad.h` + shadPS4Plus `pad.h`): L3=0x0002, R3=0x0004; `buttons` u32 at offset 0 of `OrbisPadData`; most-recent sample = `data[n-1]` of `scePadRead(handle, data, num)`.
  - **Time source:** `sceKernelGetProcessTime()` (µs monotonic, `orbis/libkernel.h` — same lib the plugin links). 2 s = 2,000,000 µs.
  - **Hook mechanism:** `dlsym(RTLD_DEFAULT, "scePadRead")` + GoldHEN Detour (the proven il2cpp_string_new pattern), lazy install from `open_hook()` with retries (libScePad loads with the game).
- **Design locked (user-approved):** clean combo (`buttons == 0x0006` EXACTLY — any other digital bit resets the hold; analog L2/R2 rest is harmless), 2 s hold, release latch, **persist-only** (flip features.json for the NEXT boot; the current session NEVER changes mid-game — eliminates every mixed-state hazard), **in-place surgical flip** of the `enable_plugin` value via memmove preserving every other key/byte (single source of truth — the pipeline's Exp-248 pull-before-push reads the LIVE file, so in-game flips flow into webapp/ps4_state/pipeline deploys automatically), **one-way-door prevention** (hotkey gated ONLY by `enable_in_game_plugin_toggle`, NOT the kill switch — a toggled-OFF user must always be able to re-enable from the couch).
- **Implemented:**
  - **Plugin v0.8049:** parses the 5th flag; lazy scePadRead hook; hold detection with sceKernelGetProcessTime; `in_game_toggle_plugin()` (read → surgical flip → write-back O_TRUNC → log → notification "BS Deluxe: Plugin ENABLED/DISABLED — restart game to apply"); key-absent fallback; diagnostics (first 8 padRead calls logged with handle/num/ret/buttons, liveness counter every 10k calls, install/retry logs, boot-time "hotkey ARMED" line); boot toast **N/5**; built clean (89,008 B; all new strings verified in the PRX).
  - **Pipeline v0.5363:** `DEFAULT_FEATURES` gains `enable_in_game_plugin_toggle: False` — deliberately the ONLY pipeline change (pull-before-push already handles everything else).
  - **Webapp 0.6.7:** KNOWN_FLAGS + FLAG_DESCRIPTIONS + toast-sim FEATURE_FLAG_KEYS/FLAG_ORDER (N/5) + TOAST_VERSION v0.8049 + index.html 5/5 placeholder.
  - **Tests:** new `tests/test_in_game_toggle.py` (18 tests: flag parse, not-decorative gating audit, one-way-door [no kill-switch gate in any toggle-path function], persist-only [no runtime global write], scePadRead-pin [NOT ReadState], L3/R3 bits, clean-combo exact match, 2 s + kernel time, release latch, surgical flip, notification restart hint, version/toast/DEFAULT_FEATURES, all 4 webapp surfaces); `test_toast_counts_four_flags` → `test_toast_counts_five_flags`. Suite **884/884** (was 866); ruff clean (7 findings in the new ELF script fixed).
  - **Rules files (user directive):** created `/workspace/AGENTS.md` (full CLAUDE.md transcription; per user: the duplicated end-of-file guardrails block was a misfired script artifact — NOT transcribed, az/gh rules consolidated into the single guardrails section); §0 Rule Synchronization updated in ALL THREE files (CLAUDE.md, .opencode/rules.md, AGENTS.md) to mandate 3-way sync on every rule change.
  - **KB:** new [[ps4-controller-input-from-plugin]] (durable pad-API/NID/methodology reference) + new [[in-game-plugin-toggle]] (feature page: the three design rules) + [[feature-flags]] 5th flag row + [[index]] updated.
- **Status:** ✅ research + implementation complete, all hermetic gates green. **PENDING: hardware deploy + test** (PS4 was off): webapp Feature Flags tab → `enable_in_game_plugin_toggle=true` + deploy plugin v0.8049 (a `--deploy-full` song install also works); then the user's test sequence: boot with DS4 connected → toast 5/5 + "[TOGGLE] hotkey ARMED" + first-8-calls diagnostics → hold L3+R3 2 s → "DISABLED, restart to apply" → restart → stock → hold L3+R3 2 s **from the OFF state** (one-way-door proof) → restart → customs back → anti-accidental check during Move gameplay. Boot log will answer the one remaining unknown (per-frame DS4 polling — expected yes; if a mid-session-connected DS4 isn't polled, v1.1 adds an own-handle fallback).

### Experiment 278b: M11 hardware deploy via the web app — flag live, plugin v0.8049 on-PS4, validation PASSED (2026-10-14)
- **User:** PS4 powered on, FTP up — proceed with the deploy.
- **Deployed (web UI flow):** webapp `/api/flags` live-read showed the 5 M10 flags ON + the new flag rendering as false; `POST /api/jobs/flags` flipped `enable_in_game_plugin_toggle=true` (job exit 0 — pipeline pull-before-push → merge → deploy); **live features.json read-back on the PS4 shows all 6 keys, hotkey armed**. Plugin v0.8049 (89,008 B) deployed via `--deploy-plugin` (CLI — the webapp has no plugin-only surface, documented) + plugins.ini entry confirmed; **deployed-PRX strings verified** (v0.8049, "[TOGGLE] in-game hotkey ARMED", scePadRead, restart hint — 11 TOGGLE strings). Full `--verify-ps4` via the webapp Verify endpoint: **🎉 PASSED** (53 redirects, catalog dataIndexes 0 bad + md5 match, all 5 packs' deployed CRCs match) — the 47-song loadout untouched.
- **Log hygiene:** pre-existing 2,623-line log (3 × v0.8048 M10 post-release boot sessions) archived to `.ai_memory/experiment_logs/v0.8048_m10_post_release_boots.txt` + cleared on the PS4 — the hotkey test will produce a clean boot log for analysis.
- **Status:** ✅ deployed + verified. Awaiting the user's in-game test (L3+R3 2s → DISABLED notification → restart → stock → L3+R3 from OFF state [one-way-door proof] → restart → customs back; anti-accidental check during Move gameplay). Next: pull + analyze the boot log's first-8-calls padRead diagnostics (the per-frame-DS4-poll question) + wrap documentation.
