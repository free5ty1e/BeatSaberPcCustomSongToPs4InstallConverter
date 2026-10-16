# M11 — In-Game Global Plugin Enable/Disable Toggle (L3+R3 Hotkey) — Implementation Plan

**Status:** 🟢 Research COMPLETE — all open questions resolved (Exp 278); implementation in progress
**Created:** 2026-10-14 (exploration) → 2026-10-14 (plan, research-locked)
**Supersedes:** the exploration document of the same feature (renamed; alternatives considered are preserved in §8)
**Feature flag:** `enable_in_game_plugin_toggle` (new, defaults false when absent)
**Plugin:** v0.8049 · **Pipeline:** 0.5363 · **Webapp:** 0.6.7
**Transcript:** `.agent/transcripts/2026-10-14_in-game-plugin-toggle-m11.md`

---

## 1. Problem Statement

Toggling the global plugin state (`enable_plugin` in `features.json`) currently requires
a PC on the same network running the pipeline (`--features-only --set-feature
enable_plugin=false|true` over FTP). **Goal:** let the user switch between all-stock and
all-custom Beat Saber entirely from the couch, with only a PS4 controller.

**Approved hotkey:** hold **L3 + R3 simultaneously for 2 seconds** on a DualShock 4 →
notification shows the new state → restart Beat Saber to apply (restart explicitly
acceptable — see §2.2).

Beat Saber is played with Move controllers; the DS4 is connected alongside them for
the hotkey. **Accidental triggers during gameplay must be impossible** — see §2.3.

## 2. Locked Design Decisions (user-approved, Exp 278)

### 2.1 Hotkey = L3 + R3, 2-second hold, clean combo, release latch
- **L3 = bit 0x0002, R3 = bit 0x0004** in the pad `buttons` u32 (dual-verified: OpenOrbis
  `orbis/_types/pad.h` `enum OrbisPadButton` + shadPS4Plus `OrbisPadButtonDataOffset`).
- **Clean combo:** trigger requires `buttons == 0x0006` EXACTLY — no other digital bit
  may be set in any poll during the hold. Gripping/jostling a DS4 mid-swing sets face/
  shoulder/dpad bits and breaks the combo; resting thumbs on analog L2/R2 does NOT
  (analog values live outside the bitmask). The 2-second hold adds a second layer.
- **Release latch:** after a toggle fires, both buttons must be RELEASED (any poll with
  `buttons != 0x6`) before the next hold can begin — no rapid re-toggling from a held combo.
- **Move-proof by construction:** Move controllers are read through the separate
  `libSceMove` (`sceMoveReadStateRecent` — verified in the game's imports), and Moves
  have no stick buttons. `scePadRead` polls carry DS4-class pads only, so a Move can
  never set L3/R3 bits.

### 2.2 Persist-only semantics — restart to apply (no mid-session behavior change)
The hotkey flips the `enable_plugin` value **inside `features.json` on the PS4** for the
NEXT boot and sends a notification ("BS Deluxe: Plugin ENABLED/DISABLED — restart game
to apply"). **The current session's behavior never changes.**
- This eliminates every mixed-state hazard at once: pack bundles, the catalog, mode
  buttons and preview clips are loaded at boot; flipping runtime state mid-session
  could leave mode buttons pointing at stock per-song data (potential crash) or
  preview sets without their clips.
- Session state is immutable; the boot-time `load_features()` governs everything, as
  today.

### 2.3 In-place surgical flip (supersedes the exploration doc's toggle-file idea)
- The plugin reads `features.json` (small, ~200–400 B), flips the `enable_plugin`
  value in the text buffer in place (`true`↔`false` via memmove for the 1-byte size
  delta), and writes it back — **preserving every other key and byte**.
- **Why, vs a separate `plugin_toggle.json`:** single source of truth. The pipeline's
  Exp-248 pull-before-push reads the LIVE `features.json` before any flag deploy, so
  in-game flips automatically survive and flow into webapp/`ps4_state.py`/pipeline
  deploys. No second file to keep in sync, no precedence rules, no `--verify-ps4`
  changes.
- Edge case — key absent (hand-edited file): absent `enable_plugin` defaults ON, so
  "flip to ON" is a no-op; "flip to OFF" rewrites the file with all known keys from
  the boot-time parse (pipeline re-materializes keys per Exp 221 on next deploy anyway).

### 2.4 One-way-door prevention: the hotkey is NOT gated by the kill switch
- The hotkey is gated ONLY by `enable_in_game_plugin_toggle`. It must keep working when
  `enable_plugin=false` — otherwise toggling OFF strands the user without a PC.
- Kill-switch semantics unchanged for game behavior: OFF = no redirects, no metadata
  swaps, no mode buttons, no previews — "official songs only". The plugin's own
  control surface (pad hook + toggle) stays alive by design; the ONLY way to disable
  the hotkey is `enable_in_game_plugin_toggle=false` (via webapp/CLI).

### 2.5 Feature flag
`enable_in_game_plugin_toggle` (defaults false, per CLAUDE.md §2 flag enforcement):
- plugin: gates the pad-hook install AND the hook body
- pipeline: added to `DEFAULT_FEATURES` (False)
- webapp: KNOWN_FLAGS + FLAG_DESCRIPTIONS + toast-simulation list
- boot toast becomes **N/5 features ON** (the toggle is the 5th feature flag)

## 3. Research Findings (all open questions RESOLVED — Exp 278)

### 3.1 The game reads pads via `scePadRead` — NOT `scePadReadState` (decisive)
Decoded all **849 dynamic imports** of the decrypted eboot (`ps4_dump/CUSA12878-patch/eboot.bin`)
against shadPS4Plus's aerolib NID database (94,276 entries; 846/849 decoded). Beat Saber
imports from **libScePad**: `scePadInit`, `scePadOpen`, `scePadClose`, **`scePadRead`**
(NID `q1cHNfGycLI`), `scePadGetControllerInformation`, `scePadResetLightBar`,
`scePadSetLightBar`, `scePadSetVibration`, `scePadSetMotionSensorState`,
`scePadSetAngularVelocityDeadbandState`, `scePadSetTiltCorrectionState`,
`scePadResetOrientation`, `scePadDeviceClassGetExtendedInformation`,
`scePadDeviceClassParseData`.
- **`scePadReadState` is NOT imported** — the exploration doc's hypothetical
  `UnityEngine.Input.GetKey` managed hook is unnecessary; the real target is the native
  `scePadRead` the engine already calls every frame (Unity's PS4 input backend polls all
  opened handles per frame).
- Signature (shadPS4Plus, SDK-accurate): `int scePadRead(s32 handle, OrbisPadData* pData, s32 num)`
  → returns the count of buffered samples; the most recent state is `pData[n-1]`.

### 3.2 `OrbisPadData` layout + button bits (dual-verified)
OpenOrbis `orbis/_types/pad.h` and shadPS4Plus `pad.h` agree:
```c
struct OrbisPadData {
    uint32_t buttons;   // offset 0 — L3=0x2, R3=0x4, OPTIONS=0x8, dpad=0x10..0x80,
                        // L2=0x100 R2=0x200 L1=0x400 R1=0x800, face=0x1000..0x8000,
                        // TOUCH_PAD click=0x100000
    stick  leftStick;  // offset 4
    ...
};
```
Only offset 0 is read by our hook → `((uint32_t*)data)[n-1]`.

### 3.3 Time source
`uint64_t sceKernelGetProcessTime(void)` — µs, monotonic per-process; declared in the
toolchain's `orbis/libkernel.h` (the same lib the plugin already links for
sceKernelOpen/Write/…). 2 s = 2,000,000 µs. No clock_gettime needed.

### 3.4 Hook mechanism (proven pattern, zero new dependencies)
`dlsym(RTLD_DEFAULT, "scePadRead")` → GoldHEN `Detour_DetourFunction` at the resolved
address — the exact pattern already proven in this codebase for `il2cpp_string_new`.
- **Lazy install from `open_hook()`** with retries (the `try_install_tmp_hook` pattern):
  at plugin `module_start` only 3 modules are visible (project invariant), but libScePad
  (imported by the eboot) is loaded before the game's first file open — the first
  attempts succeed quickly.
- Hook body: call original via `HOOK_CONTINUE`, then inspect the returned samples.
- Reads/writes for the toggle use `sceKernelOpen/Read/Write` directly (same as
  `log_write` — avoids our own libc `open` hook entirely).
- Diagnostics in v1 (hardware validation of the poll assumption): log the first 8
  calls (handle, num, return, buttons) + install event + a periodic call counter, so
  the boot log answers "does the game poll a boot-connected DS4 every frame?".

### 3.5 To verify on hardware (only remaining unknown)
- That the game polls a boot-connected DS4 every frame via `scePadRead` (expected:
  Unity PS4 input polls all opened handles; the v1 diagnostic logging confirms or
  refutes from the boot log).
- Whether a DS4 connected MID-session gets polled (edge case; if not, v1.1 adds an
  own-handle fallback — `scePadOpen` + poll our handle inside the hook tick. The
  OpenOrbis input sample documents the scePadInit/sceUserServiceGetInitialUser/scePadOpen
  flow; not needed for v1).
- **v1 guidance: connect the DS4 before booting Beat Saber.**

### 3.6 New reusable tool (development script)
`beat_saber_deluxe/development/scripts/ps4_elf_imports.py` — dumps dynamic symbols of
PS4 ELFs (`ET_SCE_DYNEXEC`/`ET_SCE_DYNAMIC`), which `readelf` cannot parse (no section
headers). Handles the PS4-specific `DT_SCE_*` dynamic tags (values are offsets
**relative to the `PT_SCE_DYNLIBDATA` program segment**, p_type `0x61000000` — verified
self-consistent on this eboot: strtab 0x18 + strsz 0x3ca0 == symtab 0x3cb8; symtab +
symtabsz == jmprel). Import NIDs (11-char base64-ish + `#lib#mod` suffixes) decode
against a NID database (we used shadPS4Plus's `aerolib.inl`).

## 4. Architecture — Component Changes

### 4.1 Plugin v0.8049 (`src/main.cpp`)
1. Parse `enable_in_game_plugin_toggle` in `load_features()` → `g_feature_in_game_plugin_toggle`.
2. Boot toast: enabled-count sums 5 flags → `(%d/5 features ON)`.
3. `try_install_pad_hook()` — lazy `dlsym(RTLD_DEFAULT, "scePadRead")` + Detour install,
   gated ONLY by the new flag (NOT by the kill switch — §2.4); called from `open_hook()`.
4. `pad_read_hook(handle, data, num)`:
   - `HOOK_CONTINUE` the original first; gate body on the feature flag.
   - Log first 8 calls + periodic counter (diagnostics, §3.4).
   - Hold detection: `buttons == 0x00000006` on the most recent sample →
     `sceKernelGetProcessTime()` delta ≥ 2,000,000 µs and not latched → fire toggle,
     set release latch; any non-matching poll clears the hold + latch.
5. `in_game_toggle_plugin()`:
   - Read `features.json` via `sceKernelOpen/Read` (4096 buffer).
   - Surgical in-place flip of the `enable_plugin` value (§2.3); key-absent fallback
     (§2.3); write back via `sceKernelOpen(O_WRONLY|O_CREAT|O_TRUNC)`.
   - Log the flip; send notification: `BS Deluxe: Plugin ENABLED/DISABLED\nRestart game to apply`.
   - **Does NOT touch `g_feature_plugin_enabled`** (persist-only, §2.2).

### 4.2 Pipeline 0.5363 (`tools/full_custom_song_pipeline.py`)
- `DEFAULT_FEATURES` gains `"enable_in_game_plugin_toggle": False`.
- Nothing else: `apply_feature_flags` pull-before-push (Exp 248) already bases every
  flag deploy on the LIVE features.json — in-game flips are picked up automatically.

### 4.3 Webapp 0.6.7
- `adapters/ps4.py`: add to `KNOWN_FLAGS`.
- `server.py`: `FLAG_DESCRIPTIONS` entry (documents restart-to-apply + DS4 + L3/R3).
- `static/app.js`: `FEATURE_FLAG_KEYS` + `FLAG_ORDER` + `TOAST_VERSION = "v0.8049"`
  (toast simulation count becomes N/5 automatically).
- `static/index.html`: static placeholder 4/4 → 5/5.

### 4.4 Tests (hermetic, source-level pins mirroring the song-previews pattern)
New `tests/test_in_game_toggle.py`:
- flag parsed in main.cpp (`strcmp(key, "enable_in_game_plugin_toggle")` + global)
- flag NOT decorative (real conditional outside `load_features`)
- hotkey NOT gated by the kill switch (one-way-door prevention — §2.4)
- hook target is `scePadRead` (pin the researched fact; NOT scePadReadState)
- L3|R3 clean-combo constant `0x0000006` + 2s constant `2000000`
- `sceKernelGetProcessTime` used for hold timing
- notification carries "Restart" (persist-only UX)
- surgical in-place flip pattern present (memmove in the toggle path)
- `DEFAULT_FEATURES['enable_in_game_plugin_toggle'] is False`
- `PLUGIN_VERSION` == v0.8049
Updated: `tests/test_pack_mode_pipeline.py::test_toast_counts_four_flags` → counts five.

## 5. Phases

- [x] **Phase 0 — Exploration** (cycle 1): architecture analysis, feasibility, approaches
      (preserved §8), roadmap M11 entry added.
- [x] **Phase 1 — Research** (Exp 278): every open question resolved against real bytes
      (eboot imports, toolchain headers, shadPS4Plus cross-verification). Design locked
      with the user (L3+R3, persist-only, feature flag, one-way-door prevention).
- [x] **Phase 2 — Implementation** (Exp 278): plugin v0.8049 + pipeline 0.5363 +
      webapp 0.6.7 + tests (§4).
- [ ] **Phase 3 — Deploy via web UI** (hardware): webapp Feature Flags tab →
      `enable_in_game_plugin_toggle=true`; deploy plugin v0.8049 (or a `--deploy-full`
      song install to exercise the full flow); reboot Beat Saber.
- [ ] **Phase 4 — Hardware test** (user, DS4 connected at boot):
      1. Boot → toast shows `(5/5 features ON)` (with all flags on) + log shows
         `[TOGGLE] scePadRead hooked` + first-call diagnostics.
      2. Hold L3+R3 2 s → notification "Plugin DISABLED — restart game to apply".
      3. Restart → toast `(OFF)`/official songs only; song menu shows stock names;
         previews stock; mode buttons gone.
      4. Hold L3+R3 2 s → notification "Plugin ENABLED — restart game to apply"
         (**kill-switch survival — the one-way-door test**).
      5. Restart → customs fully back (toast 5/5).
      6. Anti-accidental check: grip the DS4 during a Move session with combos of other
         buttons + L3/R3 — no toggle unless buttons == L3|R3 exactly for the full 2 s.
      7. Pull + archive the PS4 log; confirm the pad-poll diagnostics (§3.5).
- [ ] **Phase 5 — Docs polish**: README hotkey section + flag table row, KB
      `feature-flags` 5th row, release notes at next tag.

## 6. Rollback
- `--features-only --set-feature enable_in_game_plugin_toggle=false` (webapp Feature
  Flags tab) → hotkey gone on next boot; everything else unchanged.
- The toggle only ever writes `enable_plugin` inside features.json — the pipeline's
  `--set-feature` restores any state; no redirect/bundle/catalog files are touched,
  so the CE-34878-0 invariant family is structurally unaffected.

## 7. Safety Analysis
- **No new crash surface**: no threads (Exp 133/165 lesson), no signal handlers
  (Exp 165/166 lesson — the existing extract handler stays untouched), no memory
  probing, no new hook contexts beyond one native function whose original is always
  called first via the proven Detour trampoline.
- **The one file we write** is `features.json` — parsed by our own boot loader and
  the pipeline's banner-proof reader; the surgical flip preserves JSON validity
  (pipeline writes `"enable_plugin": true` with indent=2; we flip exactly that byte
  range).
- **Gameplay interference**: the hook adds a few instructions to a per-frame call —
  negligible; the toggle writes a <1 KB file once per hotkey activation.
- **What the toggle can never do**: crash the session (persist-only — no runtime state
  change), affect deployed files, or leave the user stranded (§2.4).

## 8. History — Approaches Considered (from the exploration phase)
- ~~`plugin_toggle.json` dedicated toggle file + periodic reload in `open_hook`~~ —
  rejected: two sources of truth; superseded by the in-place features.json flip (§2.3)
  which the pipeline's live-pull already understands.
- ~~`UnityEngine.Input.GetKey` managed-IL2CPP hook~~ — rejected: unnecessary (native
  `scePadRead` is the real per-frame poll) and riskier (managed hooking pitfalls).
- ~~Button combo L1+R1+Touchpad~~ — superseded by user-approved L3+R3 (cleaner, both
  thumbs, unused in gameplay).
- ~~Immediate mid-session effect + runtime reload machinery~~ — superseded by
  persist-only + restart-to-apply (user-approved; eliminates all mixed-state risk).
- Own pad handle (`scePadOpen` + poll inside hook tick) — held in reserve for v1.1
  IF hardware shows mid-session-connected DS4s aren't polled (§3.5).

## 9. Documentation Map
- Plan (this file) — updated every phase.
- Experiment log: `.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md` (M11
  header, Exp 278+; M10 archived per the §3.0 rotation rule).
- KB: new `ps4-controller-input-from-plugin.md` (durable: pad API, button bits,
  NID/eboot-import methodology) + `feature-flags.md` 5th row + index.
- Roadmap: M11 section (updated phases + research results).
- Transcript: `.agent/transcripts/2026-10-14_in-game-plugin-toggle-m11.md`.
- Changelogs: CHANGELOG-PLUGIN v0.8049, CHANGELOG-PIPELINE v0.5363, webapp 0.6.7.
