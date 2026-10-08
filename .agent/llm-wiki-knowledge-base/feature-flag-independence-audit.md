---
name: feature-flag-independence-audit
description: "Complete audit of every BSD feature flag: every usage site, every gating combination, crash-safety per combination, and the one real hazard (metadata flag OFF mid-list-views leaves stale replaced strings until re-entry). Plugin v0.8047 wiring."
metadata:
  type: reference
---

# Feature-Flag Independence Audit (Exp 249, 2026-10-03)

**Scope:** every runtime flag's every usage site in the plugin (v0.8047
`src/main.cpp`), every ON/OFF combination (16), crash-safety, and independent
behavioral outcomes. User requirement: each flag must be entirely independent
of the others (except the global kill switch) — disabling one must never
crash or corrupt.

**Wiring (unchanged since v0.8043):**
- `enable_plugin` — global kill switch, defaults TRUE when the KEY IS ABSENT
  (only flag that does); missing features.json → all four OFF *except*
  plugin stays TRUE (static init), then `features: plugin=1 …` in the boot log.
- `enable_custom_song_replacements` — gates the entire redirects table match
  (open_hook L367).
- `enable_song_metadata_modification` — gates metadata table load (L910),
  the TMP_Text hooks' replacement logic (L703/L759), and the deferred hook
  INSTALLER (L858).
- `enable_beatmap_mode_mapping` — gates pack-bundle + catalog redirects
  (Exp 222 gate, L384) — per-song redirects continue.

## The 16-combination matrix (verified against source)

| plugin | replacements | metadata | mode-mapping | Result |
|---|---|---|---|---|
| OFF | * | * | * | Fully stock game. No redirects match (L367 requires plugin),
  no metadata hooks install (L703/L759/L858 all require plugin), hooks exist
  but inert. **SAFE.** |
| ON | OFF | OFF | OFF | Stock songs everywhere; no redirects, no swaps.
  **SAFE.** |
| ON | ON | OFF | OFF | Customs play (Standard beatmaps only); stock
  pack bundles + stock catalog serve; no name swaps. **SAFE** — this is the
  documented "partial deploy" posture. |
| ON | ON | ON | OFF | Customs play; names swapped; modes hidden.
  **SAFE.** |
| ON | ON | OFF | ON | **⚠ THE ONE HAZARD** — see below. |
| ON | ON | ON | ON | Full experience. **SAFE** (the shipping posture). |
| ON | OFF | ON | * | Names swapped over STOCK audio — intentional and
  safe (labels ≠ content; the user's known "label only" state renders
  exactly this). **SAFE.** |
| ON | OFF | * | ON | Modes visible on STOCK pack data? NO — the Exp 222
  gate sits INSIDE the replacements check (L367): with replacements OFF the
  loop never runs, so pack/catalog redirects never fire regardless of
  mode-mapping. Modes cannot appear without customs. **SAFE.** |

## The one hazard: metadata flag OFF leaves stale swapped strings in live list views

**Mechanism:** `move_next_hook` writes replacement strings INTO the
`BeatmapLevel` objects (`songName`/`songAuthorName` field pointers, L759-800)
— in-place data mutation, not render-time interception. The flag is only
checked at hook entry. Turning the flag OFF mid-session (via the webapp's
Flags tab → next boot is fine; the flags are read ONCE at `module_start`)
stops NEW mutations — but any `BeatmapLevel` already populated in the game's
level list KEEPS the replaced strings until that object is re-created
(re-entering the song list screen re-runs MoveNext → re-reads stock data).
Worst case is therefore cosmetic and self-healing: stale custom names on
already-built list cells; no crash path exists (the hook chain null-checks
every pointer and both string-creation helpers fall back to the original
object on failure, L707-714).

**Trigger surface:** the webapp Flags tab + `--features-only` at runtime
between boots. **Not a crash vector; not state corruption** — the PS4's
song_metadata.json and the pipeline's local copy are untouched by the flag;
only in-memory UI strings lag.

**Verdict:** independence HOLDS for crash-safety across all 16 combinations.
The hazard is a cosmetic staleness with a self-heal, inherent to the
in-place-mutation design (the design that made metadata work at all — the
render-time-only approach was the pre-v0.8034 failure). Options if it
matters to the user: (a) accept (recommended — re-entering the list
refreshes), (b) re-entry note in the Flags tab UI, (c) plugin-level: swap
move_next to also RESTORE stock strings when the flag is OFF (requires
keeping originals — more state, more risk; not recommended).

## Independence proof points

1. **replacements ⊥ metadata:** the redirect table match (L367) never reads
   any metadata state; the metadata hooks (L703+) never read redirect state.
   "Label only" and "custom without label" both render correctly.
2. **replacements → mode-mapping is one-way:** mode-mapping's gate lives
   INSIDE the replacements loop — ON with replacements OFF is impossible to
   observe (modes can't appear over stock packs; that's also the Exp 180
   crash-fix invariant: patched catalog + stock bundles never co-serve).
   This is BY DESIGN: mode-mapping is a modifier of the redirect stream,
   not an independent stream. Documented, not a defect.
3. **metadata ⊥ mode-mapping:** zero shared sites.
4. **plugin ⊃ everything:** the only intended dependency (the global gate;
   each subsystem checks it first — L367, L703, L759, L858).
5. **Missing files are safe:** absent features.json → flags OFF (plugin ON
   by default-init); absent song_metadata.json → "no metadata replacements
   active" (L475); absent redirects.json → "no redirects" (L229). No path
   dereferences a null table (all reads count-guarded).
6. **The toast is diagnostic, not gating:** the (N/3) count reflects the
   three feature flags; plugin OFF shows "(official songs only)" regardless
   of the others (L918-925).

See also: [[feature-flags]] (the flag reference page),
[[ps4-file-system-redirects]] (redirect serving),
[[lftp-ftp-pitfalls]] (the flags FILE's transport, post-Exp 248).
