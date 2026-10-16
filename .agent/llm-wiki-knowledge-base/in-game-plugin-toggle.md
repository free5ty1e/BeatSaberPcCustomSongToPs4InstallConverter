---
name: in-game-plugin-toggle
description: "M11: the L3+R3 2-second DS4 hotkey that flips the global plugin state from inside the game — no PC required. Persist-only design (restart to apply), one-way-door prevention, clean-combo anti-accidental-trigger, in-place features.json flip."
metadata:
  type: feature
---

# In-Game Global Plugin Toggle (M11)

Shipped in plugin v0.8049 / pipeline v0.5363 / webapp 0.6.7 (Exp 278). Plan:
`.agent/plans/in-game-global-plugin-enable-toggle-plan.md`.

## What it does

Hold **L3 + R3 together for 2 full seconds** on a DualShock 4 → the plugin flips
its own global state (`enable_plugin` inside `features.json`) → a PS4
notification shows the new state → **restart Beat Saber to apply**. Switches the
game between all-custom (redirects, metadata swaps, mode buttons, previews) and
100% stock with zero PC involvement. Gated behind `enable_in_game_plugin_toggle`
(defaults false; enable via the webapp Feature Flags tab or
`--features-only --set-feature enable_in_game_plugin_toggle=true`).

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

- **Clean combo:** `buttons == L3|R3` EXACTLY (0x0006). Any other digital bit
  (face/shoulder/dpad/touchpad-click) resets the hold. Resting on analog L2/R2
  is harmless — analog values live outside the bitmask.
- **2-second hold** via `sceKernelGetProcessTime()` µs.
- **Release latch:** after a toggle fires, the combo must be fully released
  before the next can arm.
- **Move-proof:** Moves are read via `libSceMove`, not `scePadRead` — see
  [[ps4-controller-input-from-plugin]].

## Hook architecture

`scePadRead` (the function Beat Saber actually imports) hooked via
`dlsym(RTLD_DEFAULT, ...)` + GoldHEN Detour, lazily installed from `open_hook()`
with retries. The hook calls the original first, then reads
`((uint32_t*)data)[n-1]` (most recent sample's button mask). No threads, no
signal handlers, no memory probing — the safest hook class in this codebase.

## Rollback / disable

`--features-only --set-feature enable_in_game_plugin_toggle=false` (webapp
Feature Flags tab) — hotkey gone next boot; everything else untouched. The
toggle only ever writes the `enable_plugin` key, so the
[[pack-bundle-patching]] catalog-CRC invariant family is structurally unaffected.

## Related
- [[ps4-controller-input-from-plugin]] — the underlying pad research
- [[feature-flags]] — the full flag table
- [[plugin-architecture]] — hook/Detour patterns
