# M14 — Custom Song Environment Control (the four env modes)

**Status:** 🟡 Plan written (2026-11-07); research not yet started
**Branch:** to be cut from the post-M15-merge `main` (user creates the branch — git writes are agent-blocked)
**User directive:** deployed custom songs get a controllable in-game ENVIRONMENT with four modes — Default (today's behavior) · Force target-slot environment · Force blank · Force one of the 16 standard environments. Research-first (the roadmap's E1–E4 experiments), no asking-ahead.
**Companion docs:** roadmap M14 (the full goal + hypotheses + E1–E4) · KB: `pipeline-song-metadata-blob-injection` (the byte-verified BeatmapLevelSO blob + the UnityPy injection blocker + the Exp-129 raw-CAB patch), `song-metadata-storage` (where env could live), `song-metadata-addressables-structure` (the catalog → BeatmapLevel → SO chain), `pack-bundle-patching` (the pack-patch path M14 likely rides on) · M5's metadata work (the TMP text hook — UI strings only, CANNOT change environments: rendering property, not text)
**Doctrine:** research-first, measured-not-guessed (the observed per-song env behavior is the ground truth), every rule test-pinned, the web app stays a thin layer.

---

## 1. The problem (why this exists)

- The pipeline ships **zero environment handling** today. A custom song's `Info.dat _environmentName` never reaches the console (only beatmap TextAssets + audio deploy).
- **Observed (the user):** some customs DO show the target stock slot's environment ("and that's awesome"); MOST show a blank background. Explaining that split is the first research goal — it likely hands us "force blank" (and maybe "force target") for free.
- The user wants explicit control: Default · Target-slot · Blank · one of the 16 standard environments (the Beat Sage list — Default, Origins, Triangle, Nice, BigMirror, Dragons, KDA, Monstercat, CrabRave, Panic, Rocket, GreenDay, GreenDayGrenade, Timbaland, FitBeat, LinkinPark — all PS4-renderable, which is exactly why Beat Sage's list is these 16).

## 2. What we already have (the foundation)

| Asset | Role in M14 |
|---|---|
| `dump.cs` (line ~620880): `BeatmapLevelSO._environmentName` (string, offset 0x18, followed by `_colorScheme` @ 0x20) | The per-song layer: the env lives as a STRING on the SO |
| `dump.cs` (line ~625463): a pack-side record with `_environmentNameIdx` (int, 0x14) + `_beatmapColorSchemeIdx` (0x18) | The pack/Addressables layer: env bound by INDEX (into the game's env table). The pack-mode patch path rewrites this data region already (BeatmapLevelsData / CHAR_PATH_IDS / DIFF_BYTES=36) — **prime suspect for the blank-vs-working split (hypothesis b)** |
| `_build_beatmap_level_so_blob()` (pipeline, byte-verified vs `rollingstones_pack_full.bundle`) | Constructs the full SO blob (name/artist/BPM/preview arrays). Env fields come AFTER the preview arrays (roadmap E3) — the blob builder can carry a forced env |
| The Exp-129 **raw CAB binary patch** (verified offset 79924; Espresso/Duvet/TimeLapse CABs; size-delta handled by extending the CAB; deploy via AFR redirect or direct bundle patching — NOT UnityPy save_bundle, CE-34878-0 per Exp 116) | The PROVEN injection mechanism that bypasses the UnityPy 1.25.0 blocker (`create_object` absent; ObjectReader can't read independent blobs). Production still logs "⚠️ Blob not yet injected into CAB" — M14 is the forcing function to finish this (the roadmap says so explicitly) |
| The pack-mode patch machinery (`build_pack_mode_bundles.py`, `build_patched_pack_bundle.py`, inject/patch tools) | Where per-mode BeatmapLevelsData surgery already happens — the env-idx patch likely rides the same path (and must respect the catalog CRC invariant: bundle + merged catalog + redirects always ship together) |
| The webapp Beat Sage env list (`webapp/adapters/beatsage.py` ENVIRONMENTS + `static/app.js` envs) | The 16-name list already exists in the UI layer — the Deploy tab dropdown reuses it (+ Default/Target/Blank) |
| `song_metadata.json` / TMP_Text hook (M5) | NOT usable for env (renders text only) — but its pull-before-push + per-song keying patterns are the template for an `environments.json`-style state if needed |
| The PS4 log (`bs_log.txt`) + the in-VR playtest loop | The ground-truth oracle: E1–E4 need eyes on the console + log evidence |

## 3. Research plan (before any engine code)

### R1 — Explain today's behavior (the E1–E4 experiments; roadmap-ordered)

- **E1** — the same map deployed to two slots in two packs; compare envs (isolates slot vs map vs pack).
- **E2** — a custom's Standard vs its mode variants (OneSaber/90°) in-VR; compare envs (hypothesis d: mode-variant play correlates).
- **E3** — hexdump the stock BeatmapLevelSO's serialized fields AFTER the preview-array region in a stock pack bundle AND in a patched pack bundle: expect `_environmentName` + `_allDirectionsEnvironmentName` + color schemes. THEN compare the same region between a blank-env custom slot and a working-env custom slot (both patch paths, both layers — per-song bundle SO and pack-side record). This yields the **exact byte layout + the diff that makes one blank and one working**.
- **E4** — determine what today's BLANK customs actually resolve to: an unset/null binding may BE "force blank" for free.
- **The idx mapping:** find the game's environment table (the 16 envs → internal names → indices) — from the dump (EnvironmentNamesTable / BeatmapEnvironmentSO list in the catalog or sharedassets) — so `_environmentNameIdx` can be set deliberately. Cross-check the SO's string form vs the record's idx form (which layer WINS at runtime?).
- Output: a KB page `environment-binding-layers` with the measured tables + the E1–E4 verdicts.

### R2 — The injection mechanism (finish the standing blob-injection item)

- Re-validate the Exp-129 raw-CAB patch technique against the CURRENT bundle formats (it predates the pack-mode patch era): append/patch object bytes at a verified offset, extend the CAB for size delta, keep the catalog CRC triple intact.
- Decide the LAYER to patch (the plan's central design decision, resolved by R1's evidence):
  - **Per-song bundle SO** (string `_environmentName`) — surgical, per-song, matches --song-name/--artist granularity; but per-song bundles may not carry the SO (verify — the blob verification used a PACK bundle);
  - **Pack-side record idx** — rides the existing pack-mode patch path (one build covers all songs; needs the idx mapping and care with the catalog invariant);
  - **Both** (the SO string may be authoritative for Standard, the idx for the pack listing).
- Fall back to Options A/B/C from the KB if raw patching hits a wall (UnityPy type registry / separate Addressables entry).

### R3 — The user-facing semantics (the four modes, defined by evidence)

- `default` = touch nothing (today's behavior, byte-identical deploys — regression-pinned).
- `target` = whatever R1 finds makes "the awesome ones" work, applied deliberately.
- `blank` = the measured null/empty binding (E4) — if "blank" is NOT an unset binding, find the real blank env (the game's empty platform env) and force that.
- `<EnvName>` = force one of the 16 (the webapp dropdown = the Beat Sage list + the three symbolic modes).
- Validation loop: deploy each mode to a test slot → in-VR confirm (user) + `bs_log.txt` evidence → the mode persists across re-deploys of OTHER songs (no cross-slot bleed) and survives a full 5-pack re-deploy.

## 4. Implementation phases

- **M14.1 (R1+R2+R3+KB)** — the measured env behavior + the layer decision + the idx mapping; KB page; E1–E4 results in the experiment log.
- **M14.2 — pipeline `--environment <default|target|blank|EnvName>`** (+ config block `environments:`): the env rewrite at the chosen layer(s); default mode = provably no-op; feature-flag `enable_environment_control` gating the new behavior (DEFAULT_FEATURES + absent-file default per the fresh-install directive — propose ON, flag list IS the feature set); deploy log names the env resolution per song; regression tests (default = byte-identical bundle; each mode produces the expected bytes at the patched layer; catalog CRC invariant held).
- **M14.3 — webapp**: Deploy tab Environment dropdown (Beat Sage list + Default/Target-slot/Blank) → one more DeployOptions field → argv (thin layer); the Beat Sage form's env stays as-is (generate-time) — the deploy-time override wins and applies to ANY map.
- **M14.4 — docs + release**: feature doc `environment-control.md`; README rows; CI_RELEASE zip contents row; changelog + version bumps.
- **M14.5 — validation**: full release procedure + the in-VR four-mode playtest (the user's final judgment, as with M15).

## 5. Test strategy

- Hermetic first: blob/record construction unit tests (env string UTF-16LE, idx int, byte layouts vs real bundle hexdumps), default-mode byte-identity, catalog-CRC invariant tests (the triple), no-cross-slot-bleed property tests.
- Hardware-gated (HAS_BUILT/HAS_DUMP style): the E1–E4 live experiments and the four-mode deploy matrix skip cleanly without a PS4.
- The existing 1076-test suite stays green; new tests pin every measured layout from R1/R2.

## 6. Open questions (answered by research, not by asking)

- Q1: Which layer is authoritative at runtime — the per-song SO's string or the pack record's idx? (E3's byte diff decides.)
- Q2: What IS the blank env — an unset binding or a real empty environment? (E4.)
- Q3: Does mode-variant play change env resolution? (E2.)
- Q4: Does the per-song bundle carry a BeatmapLevelSO at all, or do pack bundles hold all SOs? (Byte audit of a deployed slot_v3.bundle vs the pack bundle.)
- Q5: Can one patch mechanism serve both env control AND finish the standing name/artist blob injection (retiring the TMP-hook dependency)? (R2's conclusion — but scope discipline: env control ships first; blob retirement is a follow-up unless trivial.)
