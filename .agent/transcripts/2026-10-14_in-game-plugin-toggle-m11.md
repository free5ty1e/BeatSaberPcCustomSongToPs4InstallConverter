# Session Transcript — M11: In-Game Global Plugin Toggle (L3+R3 Hotkey)

**Date:** 2026-10-14
**Session topic:** M11 — in-game enable/disable toggle for the global plugin via controller hotkey (no PC required)
**Feature flag:** `enable_in_game_plugin_toggle` (new, defaults false)
**Plan:** `.agent/plans/in-game-global-plugin-enable-toggle-exploration.md`
**Experiment numbers:** Exp 278 (M11 kickoff + research + implementation)
**Plugin:** v0.8048 → v0.8049 · **Pipeline:** 0.5362 → 0.5363 · **Webapp:** 0.6.6 → 0.6.7
**Prior transcript:** `.agent/transcripts/2026-10-09_song-previews-m10.md` (M10, shipped)

---

## Cycle 1 — Project takeover + M11 exploration request

**User (takeover):** Read `.agent/introduction.md` first; review CLAUDE.md, knowledge base, git history; summarize understanding before proceeding.

**Assistant:** Read introduction.md, project_summary.md, roadmap.md, context.yml, experiment_log.md (Exp 277 = M10 shipped, release v0.8048-pipeline-0.5362-webapp-0.6.6 live), KB index, song-previews plan; verified git state (branch `feature/next`, clean tree, 866-test suite green, pipeline VERSION 0.5362). Presented full project summary; next milestone candidates noted (M3 note colors standing; user picks).

**User (new feature):** Explore an in-game toggle to enable/disable the global plugin entirely — no PC connection required to access all stock songs vs all installed custom songs. Write the analysis with full details in `.agent/plans/in-game-global-plugin-enable-toggle-exploration.md` and add to the roadmap if feasible.

**Assistant:** Analyzed current architecture:
- Plugin reads features.json ONCE at module_start (`load_features()`); `enable_plugin` is the global kill switch (defaults TRUE when absent; explicit false = fully inert boot).
- Today toggling requires PC: `--features-only --set-feature enable_plugin=false|true` over FTP.
- Plugin runs in the game process → can read AND write the PS4 filesystem itself; hooks open()/fopen/MoveNext via GoldHEN Detour; notifications via sceKernelSendNotificationRequest.
- Wrote the exploration plan (Approach A recommended at the time: dedicated plugin_toggle.json + periodic reload + L1+R1+Touchpad button combo via a hypothetical Input.GetKey hook; flagged open questions: input hook target, time source, pad availability).
- Added M11 to the roadmap (exploration phase).

## Cycle 2 — User design directives + research

**User:** Approved the direction with refinements:
1. Hotkey must be behind a new feature flag (confirmed — will propose a name).
2. **L3 + R3 held for 2 seconds** on the normal PS4 controller (not L1+R1+Touchpad).
3. Notification showing the updated state after the toggle.
4. Proceed with research + an experiment deployable to the PS4 via the web UI (install a song + manage feature flags through it).
5. **Transcribe CLAUDE.md in full into the Pi rule file** (AGENTS.md) + add a rule to all 3 rule files (claude / opencode / pi) to keep all 3 synchronized on any change.
6. Documentation debt from the exploration cycle: new transcript (this file), new experiment log entry, KB + other docs — not just the roadmap.

**User (follow-ups):** (a) Beat Saber PS4 is played with Move controllers; a regular DS4 can be connected for the hotkey; **must not accidentally trigger during gameplay**. (b) **Requiring a full Beat Saber restart after the toggle is totally acceptable.**

**Design decisions locked from these directives:**
- Persist-only semantics: hotkey flips `enable_plugin` in features.json for the NEXT boot; **no mid-session behavior change at all** (eliminates every mixed-state hazard: already-loaded pack bundles/mode buttons can't desync from per-song bundles mid-session; the potentially-crashy "mode button visible but stock chart underneath" state cannot occur). Session state is immutable; restart applies it.
- In-place surgical flip of the `enable_plugin` value inside features.json (preserves every other key/byte — supersedes the earlier plugin_toggle.json idea; single source of truth; the pipeline's Exp-248 pull-before-push reads live state, so in-game flips flow into webapp/ps4_state/pipeline deploys automatically).
- Clean-combo requirement: `buttons == L3|R3` EXACTLY (no other digital bit) + full 2-second hold + release-latch → accidental triggers essentially impossible (Moves physically cannot press stick buttons; jostling a DS4 mid-swing sets other bits and breaks the clean combo).
- New feature flag `enable_in_game_plugin_toggle` (defaults false) gates the pad hook install + body.
- **One-way-door prevention:** the hotkey must NOT be gated by `enable_plugin` itself — if the plugin is toggled OFF and restarted, L3+R3 must still re-enable it, or the feature would strand users without a PC. The kill switch disables game-behavior features (redirects/metadata/modes/previews), not the plugin's own control surface. Only `enable_in_game_plugin_toggle=false` disables the hotkey.

### Research performed (all open questions resolved)

**Toolchain/hardware facts (verified against two independent sources: OpenOrbis toolchain headers + shadPS4Plus SDK-accurate implementation):**
- `scePadRead(s32 handle, OrbisPadData* pData, s32 num)` → returns number of buffered samples written; **`buttons` is a u32 at offset 0 of OrbisPadData**; most-recent sample = `data[n-1]`.
- **L3 = 0x0002, R3 = 0x0004** → clean combo mask `0x0006` (OpenOrbis `orbis/_types/pad.h` enum OrbisPadButton; shadPS4Plus `OrbisPadButtonDataOffset` agrees).
- Time source: **`uint64_t sceKernelGetProcessTime(void)`** (µs, monotonic; declared in `orbis/libkernel.h` line 209 — the same lib the plugin already links). 2 s = 2,000,000 µs.
- OpenOrbis ships an input sample (`samples/input/input/controller.cpp`) showing the exact scePadInit/sceUserServiceGetInitialUser/scePadOpen/scePadReadState flow — only needed if we ever open our own pad handle; the hook approach needs none of it.

**Game-side verification (eboot.bin import analysis — the decisive research):**
- `readelf` cannot parse PS4 ELFs (e_shoff=0, e_shnum=0 — no section headers; type ET_SCE_DYNEXEC 0xfe10, OSABI FreeBSD). Wrote a new development script: `beat_saber_deluxe/development/scripts/ps4_elf_imports.py` — walks PT_DYNAMIC, handles the PS4-specific DT_SCE_* dynamic tags (0x61000025 HASH, 0x61000035 STRTAB, 0x61000039 SYMTAB, 0x6100003B SYMENT, 0x6100003F SYMTABSZ) whose values are **offsets relative to the PT_SCE_DYNLIBDATA program segment (p_type 0x61000000)**, not file offsets and not vaddrs (verified self-consistent: strtab 0x18 + strsz 0x3ca0 == symtab 0x3cb8; symtab + symtabsz 0x5268 == jmprel 0x8f20; dynlibdata at file offset 0x1bd5570).
- Game imports are **NID-obfuscated** (11-char base64-ish hashes + `#lib#mod` suffixes). Decoded all 849 imports by joining them against shadPS4Plus's aerolib NID database (`src/core/aerolib/aerolib.inl`, 94,276 STUB entries) — 846/849 decoded.
- **Beat Saber imports from libScePad:** `scePadInit`, `scePadOpen`, `scePadClose`, **`scePadRead`** (NID q1cHNfGycLI), `scePadGetControllerInformation`, `scePadResetLightBar`, `scePadSetLightBar`, `scePadSetVibration`, `scePadSetMotionSensorState`, `scePadSetAngularVelocityDeadbandState`, `scePadSetTiltCorrectionState`, `scePadResetOrientation`, `scePadDeviceClassGetExtendedInformation`, `scePadDeviceClassParseData`.
- **`scePadReadState` is NOT imported** — the game reads pads via `scePadRead`. The original plan's hypothetical Input.GetKey hook is unnecessary; the real target is the native `scePadRead` the engine already calls per frame.
- **Move controllers are read via the separate `libSceMove`** (`sceMoveInit/Open/ReadStateRecent/SetLightSphere/...`) — so `scePadRead` polls carry DS4-class controllers only; Moves can never set L3/R3 bits. The hotkey is Move-proof by construction.
- Hook mechanism: `dlsym(RTLD_DEFAULT, "scePadRead")` + GoldHEN Detour — the exact pattern already proven in this codebase for `il2cpp_string_new`; lazy install from `open_hook()` with retries (libScePad loads with the game before its first file open).
- To be verified on hardware (v1 build logs it): that the game polls a boot-connected DS4 every frame via scePadRead (expected — Unity's PS4 input backend polls all opened handles; v1 logs the first 8 calls + a periodic call counter to confirm; if a mid-session-connected DS4 isn't polled, v1.1 adds an own-handle fallback).

**Webapp/pipeline flag surfaces found (for the 5th flag):**
- `webapp/server.py` FLAG_DESCRIPTIONS dict (5 entries) — add description.
- `webapp/adapters/ps4.py` KNOWN_FLAGS tuple — add the flag name.
- `webapp/static/app.js` FEATURE_FLAG_KEYS (toast simulation, count/4 → count/5), FLAG_ORDER, TOAST_VERSION "v0.8048" → "v0.8049".
- `webapp/static/index.html` static placeholder "(4/4 features ON)" → "(5/5 features ON)".
- Pipeline DEFAULT_FEATURES — add `"enable_in_game_plugin_toggle": False`.
- Tests that pin counts: `tests/test_pack_mode_pipeline.py::test_toast_counts_four_flags` asserts `"(%d/4 features ON)"` (→ update to /5 + new flag in the sum); `test_song_previews.py::test_default_features_has_previews_flag` (pattern to mirror); `test_no_flag_is_decorative` gating audit (new flag needs real conditional uses); webapp `/api/jobs/flags` accepts any `enable_*` (no allowlist change).

### Rules synchronization (user directive #5)
- Confirmed `.opencode/rules.md` exists and mirrors CLAUDE.md §0.5+ (verified full read).
- Confirmed `AGENTS.md` does NOT exist (Pi's standard rules file name for this workspace).
- TODO this cycle: create `/workspace/AGENTS.md` as a full transcription of CLAUDE.md's rules, and update §0 (Rule Synchronization) in all three files to mandate 3-way sync: CLAUDE.md ↔ .opencode/rules.md ↔ AGENTS.md.

(Implementation + remaining docs continue below — appended at end of cycle.)

---

## Cycle 2 (continued) — Implementation (Exp 278)

**User (mid-cycle refinements):** (1) update + rename the plan doc (`-exploration.md` → `-plan.md`) — done: renamed (tracked file; filesystem mv + git add both paths) and REWRITTEN as the full implementation plan with all research + locked design + phases + history section. (2) The duplicated end-of-file Danger Guardrails block in CLAUDE.md was "an automated script [that] misfired" — NOT transcribed into AGENTS.md; the az/gh restrictions (which only live in that block) were consolidated into the single guardrails section so no real rule is lost.

### Files changed this cycle

| File | Change |
|---|---|
| `/workspace/AGENTS.md` | NEW — Pi rule file: full CLAUDE.md transcription + 3-way sync rule (§0); single guardrails section (no duplicate block) |
| `/workspace/CLAUDE.md` | §0 → 3-way sync rule (CLAUDE.md ↔ .opencode/rules.md ↔ AGENTS.md) |
| `/workspace/.opencode/rules.md` | §0 → same 3-way sync rule |
| `.agent/plans/in-game-global-plugin-enable-toggle-plan.md` | RENAMED from `-exploration.md` + full rewrite: locked design (L3+R3/persist-only/one-way-door), all research findings, component changes, phases, hardware test plan, rollback, safety analysis, history |
| `.agent/roadmap.md` | M11 section: research-complete checklist, locked design, phase checkboxes M11.1–M11.8 (implementation done, hardware pending) |
| `beat_saber_deluxe/src/main.cpp` | **Plugin v0.8049**: parses `enable_in_game_plugin_toggle`; new M11 section (pad constants L3=0x2/R3=0x4/combo 0x6/2s/µs, hold+latch globals, `in_game_toggle_plugin()` in-place flip, `pad_read_hook()` scePadRead hook w/ diagnostics, `try_install_pad_hook()` lazy dlsym install); open_hook calls try_install_pad_hook; toast N/5; boot log lines extended |
| `beat_saber_deluxe/tools/full_custom_song_pipeline.py` | DEFAULT_FEATURES + `enable_in_game_plugin_toggle: False` (pipeline v0.5363) |
| `beat_saber_deluxe/VERSION` | 0.5362 → 0.5363 |
| `beat_saber_deluxe/webapp/adapters/ps4.py` | KNOWN_FLAGS + new flag |
| `beat_saber_deluxe/webapp/server.py` | FLAG_DESCRIPTIONS + new flag (full description: hotkey, restart-to-apply, kill-switch independence) |
| `beat_saber_deluxe/webapp/static/app.js` | FEATURE_FLAG_KEYS + FLAG_ORDER + TOAST_VERSION v0.8049 |
| `beat_saber_deluxe/webapp/static/index.html` | toast placeholder 4/4 → 5/5 |
| `beat_saber_deluxe/webapp/VERSION` | 0.6.6 → 0.6.7 |
| `beat_saber_deluxe/tests/test_in_game_toggle.py` | NEW — 18 source-level pins: flag parse, not-decorative, one-way-door (no kill-switch gate in toggle path), persist-only (no runtime global write), scePadRead pin (NOT ReadState), L3/R3 bits, clean-combo exact match, 2s+sceKernelGetProcessTime, release latch, surgical flip, restart-hint notification, version/toast/DEFAULT_FEATURES, 4 webapp surfaces |
| `beat_saber_deluxe/tests/test_pack_mode_pipeline.py` | test_toast_counts_four_flags → test_toast_counts_five_flags (all 5 flags in the sum) |
| `beat_saber_deluxe/CHANGELOG-PLUGIN.md` | v0.8049 entry |
| `beat_saber_deluxe/CHANGELOG-PIPELINE.md` | v0.5363 entry |
| `beat_saber_deluxe/webapp/CHANGELOG-WEBAPP.md` | 0.6.7 entry |
| `beat_saber_deluxe/development/scripts/ps4_elf_imports.py` | NEW reusable tool (see research above); lint-fixed (7 undefined DT_SCE_* name constants added); NID-methodology docstring |
| `README.md` | banner versions; features table gains In-Game Plugin Toggle row (also fixes a pre-existing duplicated Song Previews row); flag table gains the 5th flag; NEW "In-Game Global Plugin Toggle" usage section |
| `beat_saber_deluxe/README.md` | v0.5363 highlights section |
| `.agent/llm-wiki-knowledge-base/feature-flags.md` | 5th flag row + features.json example |
| `.agent/llm-wiki-knowledge-base/ps4-controller-input-from-plugin.md` | NEW durable KB page (pad API, layouts, bits, hook pattern, NID/eboot methodology) |
| `.agent/llm-wiki-knowledge-base/in-game-plugin-toggle.md` | NEW feature KB page (the three design rules) |
| `.agent/llm-wiki-knowledge-base/index.md` | both new pages + feature-flags N/5 |
| `.ai_memory/.../experiment_log.md` | ROTATED per §3.0: M10 archived → `experiment_log_song-previews_exp268-277_2026-10-09_to_2026-10-14.md`; fresh M11 log with Exp 278 |
| `.agent/project_summary.md` | Status → M11 in progress; Exp 278 timeline row; M10 wrapped as Prior |
| `.agent/context.yml` | versions 0.8049/0.5363; current_feature → M11 (plan/transcript/flag/key facts/hardware test); rules_files note; experiment-log archive list; test_count 884 |

### Verification performed
- **Plugin build**: `make clean && make -B` — clean build, 89,008 B PRX; strings verified: v0.8049, enable_in_game_plugin_toggle, scePadRead, "Restart game to apply", "(%d/5 features ON)".
- **Full test suite**: **884/884 passed** (was 866; +18 new; ~8 min run).
- **Lint**: `ruff check tools/ tests/ webapp/ development/scripts/ps4_elf_imports.py` — All checks passed (pinned ruff 0.16.0).
- **New script proven live**: ps4_elf_imports.py decoded the game's 849 imports (846 named via aerolib) — the research above is its output.

### Status at end of cycle
✅ Research complete + implemented + all hermetic gates green. ⏳ Hardware deploy + test PENDING (PS4 off). Deploy path for next power-on: webapp Feature Flags tab → enable `enable_in_game_plugin_toggle` → Apply; deploy plugin v0.8049 (webapp Deploy tab, or any `--deploy-full`); user boots with DS4 connected and runs the M11.7 test sequence (roadmap/plan §5 Phase 4). Boot log will carry the first-8-calls pad diagnostics that answer the per-frame-DS4-poll question.

---

## Cycle 3 — Hardware deploy via the web app (Exp 278b, PS4 powered on)

**User:** "OK, PS4 is powered on and FTP is up."

**Deploy executed (web UI flow, as planned):**
1. Connectivity: PS4 reachable (64 AFR entries; features.json + bs_log.txt present).
2. Webapp started (`python3 server.py --no-browser --port 8765`); ping confirms **webapp 0.6.7 / pipeline 0.5363 / plugin v0.8049**.
3. `GET /api/flags` — live read: all 5 M10-era flags true; the new `enable_in_game_plugin_toggle` already rendered (KNOWN_FLAGS surface) as false.
4. `POST /api/jobs/flags {"flag": "enable_in_game_plugin_toggle", "value": true}` → job 1792034070 → **exit 0** (pipeline: pull-before-push → merged → deployed; log shows "Feature flag: enable_in_game_plugin_toggle = True", "✅ Features config deployed").
5. Live features.json read-back from the PS4: **all 6 keys present, hotkey flag true** — exactly the designed final state.
6. Plugin deploy (CLI `--deploy-plugin`; the webapp has no plugin-only surface — documented): built v0.8049 (89,008 B), uploaded to `/data/GoldHEN/plugins/beat_saber_deluxe.prx`, plugins.ini entry confirmed intact.
7. Deployed-PRX strings verification (download + strings; FSELF-unpack lesson): **v0.8049 + "[TOGGLE] in-game hotkey ARMED" + scePadRead + "Restart game to apply" + enable_in_game_plugin_toggle all present** in the DEPLOYED bytes; 11 TOGGLE strings.
8. Full validation via the webapp Verify endpoint (`POST /api/jobs/verify` → `--verify-ps4`): **🎉 PASSED** — 53 redirects, 6 pack/catalog pairs, catalog dataIndexes 0 bad + md5 match, all 5 packs' deployed bundle CRCs match the catalog. The 47-song loadout is untouched by the deploy.
9. Log hygiene per the rules: the pre-existing log (2,623 lines, 3 × v0.8048 boot sessions — M10 post-release gameplay) archived to `.ai_memory/experiment_logs/v0.8048_m10_post_release_boots.txt` and cleared on the PS4 → the hotkey test will produce a clean log.

**Status:** ✅ deployed + verified on-PS4. Awaiting the user's in-game test (checklist handed over); after their test: pull + analyze the clean boot log (first-8-calls padRead diagnostics answer the per-frame-DS4-poll question) + document (Exp 278b wrap).

---

## Cycle 4 — v0.8049 hardware test FAILED (Exp 278b): root cause from the boot log

**User:** tested on the PS4 — DS4 connected to the same profile as the VR headset + Moves: the 5/5 boot toast appeared (deploy + flag confirmed) but holding L3+R3 never fired a notification. User's read: the DS4 seems completely disabled in Beat Saber, so its inputs are ignored. Asked (a) whether I'd used the pipeline/webapp and redeployed a song (answers: webapp API for flag+verify + pipeline CLI --deploy-plugin for the plugin; NO song redeploy — the hotkey lives in the plugin + features.json only), and (b) to research the active controls and switch to a MOVE-controller button shortcut.

**Log analysis (archived `.ai_memory/experiment_logs/v0.8049_hotkey_test_failure_l3r3.txt`, 1,491 lines; cleared after):**
- `features: ... in_game_plugin_toggle=1` + "hotkey ARMED" ✓ — flag parsed, code deployed.
- **ROOT CAUSE: `[TOGGLE] scePadRead not found yet` × 100 attempts → "ERROR: scePadRead never found"** (then re-logged on EVERY subsequent open — the give-up-flag bug). The hook NEVER INSTALLED, so no pad data was ever observed.
- **The lesson (durable, now in KB):** `dlsym(RTLD_DEFAULT, "scePadRead")` resolves NOTHING because **Sony system libraries export functions under their NIDs, not readable names** — the game imports scePadRead as NID `q1cHNfGycLI`. Readable-name dlsym only ever worked here for eboot-exported symbols (`il2cpp_string_new`).

## Cycle 5 — v0.8050 redesign (Exp 278c): Move button + trigger; NID-resolved hooks; deployed

**User:** chose the combo: **Move button + trigger held together** — "used nowhere else in the beat saber game".

**Research (the game's own dump.cs):**
- `PSVRDeviceManager.PSMoveButton` enum: **Select=1, [2 = trigger — SKIPPED], Move=4, Start=8, Triangle=16, Circle=32, Cross=64, Square=128** — the enum skips 2 because the game reads the trigger via `GetPSMoveAnalog`; the trigger's DIGITAL bit is 0x2, the Move button is 0x4.
- Game surface: `GetPSMoveButtonDown(idx, button)` / `GetPSMoveAnalog(idx)` / PSMoveDevice carries sceMove handles.
- The per-frame Move read = **`sceMoveReadStateRecent`** (NID `f2bcpK6kJfg`) — the ONLY Move state read in the eboot's imports (sceMoveReadStateLatest NOT imported).
- SceMoveData layout per shadPS4Plus's SDK-derived OrbisMoveData: accelerometer[3]+gyro[3] then **button_data u16 @ +0x18, trigger u16 @ +0x1A**; shadPS4 documents the read as 4-arg (handle, timestamp, data, out_count) — arity handled SAFELY at runtime.

**Implemented (plugin v0.8050):** NID-first dlsym (`q1cHNfGycLI` scePadRead secondary DS4 path; `f2bcpK6kJfg` sceMoveReadStateRecent PRIMARY) with readable-name fallbacks; move_read_hook detects the call form at runtime via `is_mapped_rw_pointer()` (sceKernelQueryMemoryProtection — v0.8045-proven) and passes ALL FOUR registers through; combo = Move button + trigger (digital bit OR analog>0x80), clean (no other bit), 2 s via sceKernelGetProcessTime; shared `combo_feed()` detector with 250 ms poll-gap window (two Move handles interleave), release latch, 3 s global cooldown; diagnostics: first-10 moveRead calls raw + every data-word change (capped 40) — a button press lights up the boot log, confirming/correcting the +0x18/+0x1A offsets EMPIRICALLY; give-up flags fix the retry spam; entry-0 button check (a 2 s hold spans 100+ frames). Webapp 0.6.8 (description + TOAST_VERSION v0.8050). Pipeline unchanged (0.5363).

**Verification:** make clean build (105,536 B — matches the historical ~105 KB full-build baseline; the 89,008 B v0.8049 was a stale-link artifact though its deployed copy did carry all toggle code per strings-verification); tests rewritten for v2 (24 tests); suite **889/889**; ruff clean. **Deployed via `--deploy-plugin` + strings-verified on the PS4** (v0.8050 + both NIDs + Move-combo ARMED line in the downloaded bytes). Boot log was cleared at the Exp-278b archive, so the next boot produces a clean diagnostic log.

**Files changed (this cycle):** src/main.cpp (v0.8050 redesign), tests/test_in_game_toggle.py (rewritten), webapp/server.py + static/app.js + VERSION 0.6.8, CHANGELOG-PLUGIN v0.8050, webapp CHANGELOG 0.6.8, plan doc (§2.1 v2 + §3.5 hardware answers + Phase-4 test plan), roadmap M11 (278b/278c), experiment log (278b/278c entries), KB: ps4-controller-input-from-plugin (THE NID RULE + Move path section + signature-ambiguity technique), in-game-plugin-toggle (design history + new combo), feature-flags + index rows, both READMEs, project_summary + context.yml.

**Status:** ✅ v2 deployed. Awaiting the user's Move-combo test: boot → toast 5/5 → hold Move button+trigger 2 s → DISABLED notification → restart → stock → combo again from OFF (one-way-door proof) → restart → customs. The moveRead change-diagnostics will empirically confirm the bit layout (or pinpoint the true bits for a one-line v0.8051 fix).
