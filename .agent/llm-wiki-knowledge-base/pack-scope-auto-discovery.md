---
name: pack-scope-auto-discovery
description: "Exps 224-225: zero hardcoded pack expectations — _resolve_active_packs() resolution order, the deploy-gate regression that crashed clean-slate boots, and the lftp quoting requirement"
metadata:
  type: reference
---

# Pack Scope Auto-Discovery (Zero Hardcoded Packs)

## The User Directive (Exp 224)

"There should be ZERO expectations on which music packs should be modified. It
is totally up to the user... we care about ONLY what the user deploys." The
Exp 188-era default `"packs": ["therollingstones","billieeilish","lizzo","camellia"]`
encoded one month's deployed state as a permanent expectation and is REMOVED.

## `_resolve_active_packs(config)` resolution order

1. **User-pinned list** — `pack_modes.packs` in ps4_config.json, if non-empty
   (explicit override for users who want a fixed scope);
2. **Deployed state** — otherwise, the packs whose `*_pack_modes_*` bundles are
   referenced in the LOCAL redirects.json (the deployment state file kept in
   sync with the PS4 on every deploy/sync/enforce). A state file that exists
   but references no patched packs = NO packs in scope — locally built bundles
   never count as deployed;
3. **Clean slate fallback** — no state file at all (fresh clone / clean PS4):
   packs with locally built bundles in `build_dir`, so build-time flows have a
   scope.

No FTP in the resolution path (fast + deterministic); `--verify-ps4` separately
proves local and PS4 redirect sets match.

## The Exp 225 Regression (the gate rule)

Two deploy gates (`deploy_pack_bundle`, `deploy_pack_modes`) still checked the
RAW PINNED LIST (`if pm.get('packs'):`). Under the new `[]` default both were
permanently False: on a clean-slate first-song deploy the patched PACK bundle
shipped **without** its merged catalog and **without** the `aa/catalog.json`
redirect → the game read the ORIGIN catalog → Unity CRC validation failed →
**CE-34878-0** (the [[addressables-catalog-crc-validation]] invariant).
Also: post-deploy validation now EXITS 1 on failure — a deploy that cannot
prove its consistency must fail the script, not print "Pipeline complete!".

**Rule: any gate deciding "does this flow apply?" must consult the same
resolution helper as the flow's inputs — never a raw config field that a
defaults change can silently empty.**

## lftp Path Quoting (same experiment)

lftp's `-e` script is parsed by lftp's own command language: an unquoted path
like `Scream&Shout_v3.bundle` splits at `&` and the transfer silently fails
while lftp exits 0. ALL pipeline FTP constructions quote paths via
`_ftp_quote()`, and `deploy_to_ps4` verifies uploads by remote listing size,
never by exit code. Same bug class in bash: `--target "Scream&Shout"` must be
quoted in scripts/docs.

## Related
- [[pack-bundle-patching]] — the bundle/CRC machinery whose scope this governs
- [[partial-pack-deployment-and-clear-target]] — per-song surgical patching
- [[pipeline-deploy-full-orchestration]] — where the gates live

## The Union Rule (Exp 226 — deployed state ADDS, never gates)

Deployed-state discovery reflects what is on the PS4 NOW — which by definition
lags the pack being deployed in the same invocation. Pure-filter scoping
(`[p for p in active if p in packs]`) therefore silently skipped every
not-yet-discovered requested pack: only the FIRST pack a user deployed ever
received its mode-button patch (britney/camellia/lizzo/RS all skipped with
"Requested pack(s) not in the active set"). All four helpers
(`_get_pack_modes_entries`, `_ensure_pack_mode_bundles`, `deploy_pack_bundle`,
`deploy_pack_modes`) now UNION the request onto the active set:
`configured = list(packs) + [p for p in configured if p not in packs]`.

**Rule: deployed-state discovery may ADD packs to a deploy's scope; it must
never GATE a pack the caller explicitly requested.**

## clear-target-song and the Empty-Scope Wipe (Exp 226)

`--clear-target-song` on the LAST custom song of a pack passed
`slots=rebuild_slots=[]` ("no slots need extra pack modes") into redirect
regeneration — which the scope filter read as "delete every song redirect".
44 redirects across all packs were destroyed live. Fixes (all three):
1. clear_target_song's regeneration scopes to the song redirects that still
   EXIST after its surgical removal;
2. `_ensure_mass_song_redirects` treats an empty scope as a NO-OP;
3. an unmatched non-empty scope preserves existing redirects (out-of-scope
   trimming only runs when the scope matched configured slots).

**Rule: scope parameters are for narrowing a caller's own deploy — an empty or
unmatched scope must NEVER become a deletion. Removing redirects is the job of
the dedicated removal paths (--clear-target-song's surgical step, clean slate).**

## Deploy Flows Use _resolve_deployed_packs (Exp 227 — no local-bundle fallback)

The Exp 226 union initially used `_resolve_active_packs` (which falls back to
locally-built bundles when no state file exists). On a clean-slate PS4 that
fallback resurrected SIX never-installed packs into a `--clear-target-song`
run — the stale `pack_modes_bundles/` contents became "deploy scope".

Rules (v0.5345):
1. **Deploy flows** (`deploy_pack_bundle`, `deploy_pack_modes`) union their
   requested packs against `_resolve_deployed_packs()` — the redirects.json
   state ONLY. No local-bundle fallback. Clean slate ⇒ [] ⇒ exactly the
   requested pack is touched.
2. **Caller-provided `packs=` is AUTHORITATIVE** in `_get_pack_modes_entries`
   and `_ensure_pack_mode_bundles` — they honor it verbatim (deploy flows do
   their own unioning). Build-time callers (no packs=) still get the fallback
   via `_resolve_active_packs`.
3. **A clean slate must wipe every local input a fallback can read.**
   `backup-beat-saber-deluxe-files.py --clean-ps4` now clears the 3 config
   files AND pack_modes_bundles/, custom_sundles/, mass_bundles/, and stray
   `_beatmap_level_so_*.blob` debug files — all regenerable from BeatSaver
   sources + the game dump.

**Lesson: a fallback built for one flow (build-time scope) must never be
consumed by a different flow (deploy-time preservation) — give the deploy side
its own strict resolver.**

## State-Authority vs Local-Existence (Exp 232 — the sweep rule)

A redirect-**deleting** sweep must validate against the DEPLOYED-STATE
authority (`_resolve_deployed_packs` — the redirects.json state file),
never against local cache existence (`os.path.isfile` on build artifacts).
The Exp 232 regression: `_ensure_pack_bundle_redirects`' stale-sweep asked
"which packs are still configured?" via the current pair — which filters by
local bundle presence — while the clean-slate wipe empties
`pack_modes_bundles/`. Each chained script's deploy then found only its OWN
bundle locally and deleted every other pack's redirect ("pack no longer
configured") even though those bundles were live on the PS4. The 5-script
chain ended with exactly one pack redirect: the last script's.

**Why prior QA passed:** stale local bundles from earlier sessions made the
file-existence filter accidentally permissive. The bug was latent since
Exp 226; the Exp 227 true-clean-slate exposed it.

**Rule:** local caches are BUILD inputs; the state file is the RECORD of
what is deployed. Deletion decisions read the record, not the cache. A
pack is removable only when it is in neither the current pair NOR the
deployed state.
