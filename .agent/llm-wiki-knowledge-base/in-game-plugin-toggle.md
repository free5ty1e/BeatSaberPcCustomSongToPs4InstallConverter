---
name: in-game-plugin-toggle
description: "M11: the L3+R3 2-second DS4 hotkey that flips the global plugin state from inside the game — no PC required. Persist-only design (restart to apply), one-way-door prevention, clean-combo anti-accidental-trigger, in-place features.json flip."
metadata:
  type: feature
---

# In-Game Global Plugin Toggle (M11)

Shipped in plugin v0.8049/v0.8050 / pipeline v0.5363 / webapp 0.6.7–0.6.8
(Exps 278–278c). Plan:
`.agent/plans/in-game-global-plugin-enable-toggle-plan.md`.

## What it does

Hold **the Move BUTTON + TRIGGER together for 2 full seconds** on a Move
controller → the plugin flips its own global state (`enable_plugin` inside
`features.json`) → a PS4 notification shows the new state → **restart Beat
Saber to apply**. Switches the game between all-custom (redirects, metadata
swaps, mode buttons, previews) and 100% stock with zero PC involvement.
Gated behind `enable_in_game_plugin_toggle` (defaults false; enable via the
webapp Feature Flags tab or `--features-only --set-feature
enable_in_game_plugin_toggle=true`).

### Design history (two hardware iterations — both instructive)
- **v0.8049 (Exp 278):** L3+R3 on a DS4. Hardware test (Exp 278b): NEVER
  fired. Two findings: (1) **root cause — dlsym by readable name failed**
  because Sony system libraries export NIDs
  ([[ps4-controller-input-from-plugin]] — the critical lesson); (2) the
  **DS4 is ignored by Beat Saber in VR mode** (user-verified — a DS4 on the
  same profile as the headset + Moves never produced pad input).
- **v0.8050 (Exp 278c):** user-chosen combo **Move button + trigger** (used
  nowhere else in the game); primary hook `sceMoveReadStateRecent` (NID
  `f2bcpK6kJfg` — the only Move read in the eboot's imports, called every
  frame for both Moves); Move bits reconstructed from the game's own
  `PSVRDeviceManager.PSMoveButton` enum (trigger=0x2, Move=0x4);
  runtime-safe signature detection via sceKernelQueryMemoryProtection; raw
  word diagnostics so the first boot log confirms the offsets empirically.
  Hardware result: STILL never fired — **NID dlsym also resolves nothing**
  (dlsym cannot see kernel-loaded SPRX exports at all).
- **v0.8051 (Exp 278d):** GOT resolution WORKED (eboot.bin base found;
  scePadRead slot bound at open #1) — but Detouring the real library code
  built a trampoline over a non-relocatable prologue → **the game HUNG at a
  black screen on the first scePadRead call**. Also revealed: JUMP_SLOTs
  bind LAZILY (the move slot held a sentinel until the game's first call).
- **v0.8052 (Exp 278e):** **GOT HIJACKING** — overwrite the slot value with
  the hook address after mprotect RW (atomic write, no trampoline, no code
  patching; the hook calls the saved original pointer directly) and WAIT for
  lazy slots to bind. Per-call diagnostics moved behind VERBOSE_LOG (debug
  builds only) per the release-performance directive; release logs one-time
  events only. Form detection cached (no hot-path syscalls).
- **v0.8051 (Exp 278d):** the definitive resolution — **the EBOOT'S GOT
  slots** (r_offset from the eboot's JMPREL relocations, precomputed from
  the decrypted dump: sceMoveReadStateRecent → RVA 0x1c634e8, scePadRead →
  0x1c63500) hold the loader-bound final addresses; the plugin finds
  eboot.bin by name via the module list, reads the slot, validates with
  sceKernelQueryMemoryProtection, Detours the resolved address. See
  [[ps4-controller-input-from-plugin]].

## The three deliberate design rules

1. **Persist-only (restart to apply).** The hotkey writes `features.json` for
   the NEXT boot; the current session's behavior NEVER changes. This eliminates
   every mixed-state hazard at once — pack bundles/catalog/mode buttons load at
   boot, so a mid-session flip could leave mode buttons pointing at stock
   per-song data (crash risk) or previews without their clips. Boot-time
   `load_features()` governs runtime, exactly as before.
2. **In-place surgical flip.** `"enable_plugin": true↔false` is flipped inside
   the file buffer via memmove (±1 byte for the true/false length delta),
   preserving every other key/byte. Single source of truth: the pipeline's
   Exp-248 pull-before-push reads the LIVE features.json, so in-game flips
   flow into webapp/`ps4_state.py`/pipeline deploys automatically — a separate
   toggle file would have created two sources of truth.
3. **One-way-door prevention.** The hotkey is gated ONLY by
   `enable_in_game_plugin_toggle` — deliberately NOT by the `enable_plugin`
   kill switch. Otherwise a user toggled OFF could never re-enable without a
   PC. The kill switch disables game-behavior features, not the plugin's own
   control surface.

## Anti-accidental-trigger (user requirement: Move gameplay safety)

- **Clean combo:** Move button + trigger together (bits 0x4|0x2 = 0x6) with
  NO other button bit set — any other bit breaks the hold. A combination
  used nowhere else in the game (user-verified).
- **2-second hold** via `sceKernelGetProcessTime()` µs, continuous within a
  250 ms poll-gap window (the two Move handles interleave per-frame polls —
  the non-holding handle's polls must not reset a hold the other sustains).
- **Release latch + 3 s cooldown:** after a toggle fires, the combo must be
  fully released before the next can arm, and a global cooldown prevents
  double-fires from the two hook paths.

## Hook architecture

`sceMoveReadStateRecent` (primary — NID-resolved) + `scePadRead` (secondary
DS4 path) hooked via `dlsym(RTLD_DEFAULT, <NID>)` + GoldHEN Detour, lazily
installed from `open_hook()` with retries. The hook calls the original first,
then reads entry 0's button bits (a 2-second hold spans 100+ frames — every
entry shows the same held-state bits). **All hooks resolve BY NID** — see
[[ps4-controller-input-from-plugin]] for the Exp 278b lesson.

## Rollback / disable

`--features-only --set-feature enable_in_game_plugin_toggle=false` (webapp
Feature Flags tab) — hotkey gone next boot; everything else untouched. The
toggle only ever writes the `enable_plugin` key, so the
[[pack-bundle-patching]] catalog-CRC invariant family is structurally unaffected.

## Related
- [[ps4-controller-input-from-plugin]] — the underlying pad research
- [[feature-flags]] — the full flag table
- [[plugin-architecture]] — hook/Detour patterns
