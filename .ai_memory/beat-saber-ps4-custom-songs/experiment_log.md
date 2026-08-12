---
name: experiment-log
description: "Active experiment log for the CURRENT feature only (Chromeo Source Recovery + Mass Redeploy). Per-feature rotation: when a feature concludes, archive this file into experiment_log_archive/ and open a fresh log. Prior features (Exp 1-183) archived in experiment_log_archive/."
metadata:
  node_type: memory
  type: reference
---

# Experiment Log: Beat Saber PS4 Custom Song Support — Chromeo Source Recovery + Mass Redeploy

**Feature:** Recover the 6 deleted Chromeo slot sources from deployed PS4 bundles (bundle → audio + V4 beatmaps → V3.2.0 → per-song pipeline), rebuild all 38 custom songs through the v0.5316 pipeline (mode mapping + generators, full audio, V2→V3), and mass-redeploy to the PS4.
**Started:** 2026-08-12 (Exp 184)
**System:** PS4 FW 9.00, GoldHEN 2.3 / 2.4b16.2
**Toolchain:** OpenOrbis PS4 Toolchain + GoldHEN Plugin SDK
**Plugin file:** `beat_saber_deluxe.prx` (plugin v0.8040 / pipeline v0.5316)
**Prior experiments (Exp 1-159, archived):** `experiment_log_archive/experiment_log_exp001-159_prior-features_2026-06-08_to_2026-07-31.md`
**Prior experiments (Exp 160-183, archived):** `experiment_log_archive/experiment_log_beatmap-mode-mapping_exp160-183_2026-07-28_to_2026-08-11.md`

**How to append:** Add the next `### Experiment <N+1>:` entry at the end of THIS file (only current-feature experiments). When this feature concludes, move the whole file into `experiment_log_archive/` with a feature+date name and open a fresh `experiment_log.md`.

---

### Experiment 184: Chromeo Source Recovery — Deleted Slots Reconstructed from PS4 Bundles (2026-08-12)
- **Date:** 2026-08-12
- **Context:** The 6 Chromeo slot source dirs (Crystallized, CycleHit, ExitThisEarthsAtomosphere, Ghost, LightItUp, WhatTheCat) were deleted from the local repo. The deployed PS4 bundles still carry the audio + beatmaps, so they can be reverse-recovered and fed through the per-song pipeline.
- **Extraction:**
  - Pulled all 6 bundles from the PS4 to `/tmp/opencode/chromeo_bundles/`.
  - TextAssets are real gzip; audio is the `.resource` subfile of the BundleFile (key `CAB-<hash>.resource`).
  - Fixed gzip decode: `m_Script` str must be decoded with `surrogateescape` (NOT `surrogatepass`) before `gzip.decompress`.
- **Beatmap formats:** 4 of 6 slots carry deployed V4 (v4.0.0, relative `colorNotes{b,i}` + `colorNotesData{x,y,c,d}`) beatmaps; `CycleHit`/`Ghost` carry a mix (some V3.2.0, some V4.0.0).
- **V4→V3.2.0 decoder** (`/tmp/opencode/reconstruct_chromeo_src.py`): merges data via `i` index with defaults (`x=0,y=0,c=0,d=0`), fills `bpmEvents` with per-slot BPM (Crystallized 140, CycleHit 129, ExitThisEarthsAtomosphere 117, Ghost 117, LightItUp 124, WhatTheCat 129).
- **Validation:** decoded max beat matches audio.gz `bpmData[0].eb` for Crystallized (791.0); others exceed stale eb (896/868/1136/1063/678) confirming those beatmaps were re-injected after audio, and pipeline regenerates bpmData anyway.
- **Reconstruction output:** `/workspace/beat-saber-ps4-custom-songs/songs/chromeo_backout/{slot}/` with `<Diff><Mode>.dat`, `Info.dat` (2.1.0, per-slot songName/songAuthorName from `song_metadata.json`, BPM), and `audio.fsb`. CycleHit/Ghost include original 3 OneSaber `.dat` files (ExpertOneSaber/ExpertPlusOneSaber/NormalOneSaber).
- **Pipeline rebuild verified:** all 6 Chromeo bundles rebuilt to `/tmp/opencode/chromeo_build/<slot>_v3.bundle` — sizes Crystallized 59,236,252 B; CycleHit 39,913,213 B; ExitThisEarthsAtomosphere 36,387,911 B; Ghost 39,284,023 B; LightItUp 33,574,856 B; WhatTheCat 37,796,839 B. Each verified: generated 90Degree/NoArrows/OneSaber beatmaps have notes, `bpmData[0].eb` corrected, sampleCount preserved (full audio, e.g. Crystallized 14,947,739 samples ≈ 339s).
- **Version:** Pipeline v0.5315
- **Status:** ✅ All 6 Chromeo slots recovered + rebuilt. AWAITING mass-rebuild completion + deploy.

### Experiment 185: Mass Re-Run All 38 Songs + Generator Bug Fix (2026-08-12)
- **Date:** 2026-08-12
- **Context:** Mass re-run all 38 custom songs (13 Rolling Stones + 10 Billie + 9 Lizzo + 6 Chromeo) through the v0.5315 default pipeline (PCM16 + no-pad full audio + beatmap mode mapping/generators + V2→V3) into `/tmp/opencode/mass_build/`, then verify + deploy.
- **Slot→source mapping completed:** all 32 non-Chromeo slots mapped to `songs_repo/` dirs (96 dirs, same content as `songs/`). Rolling Stones 13 + Billie 8 mapped earlier; this session finished Billie (NDA=`fb14e8…`, ThereforeIAm=`559113…`) and all 9 Lizzo. Chromeo 6 use `chromeo_backout/` with `--audio <src>/audio.fsb`.
- **Bug found + fixed (pipeline v0.5315→0.5316):** V3 beatmaps may OMIT `x`/`y` (and even `b`) — valid per V3 spec (defaults 0). Some BeatSaver sources (e.g. "Take Me to the Beach" → `livebythesword` + `IDidntChangeMyNumber`; Billie "Oxytocin" source) crashed the OneSaber generator with `KeyError: 'y'` (direct `n["y"]`/`n["x"]` indexing). The 90Degree generator also direct-indexed `n["b"]`/`obs["b"]`/`ev["b"]`. **Fix:** all generator field reads use `.get(..., 0)` defaults for V3, matching the V2 branch. Regression tests added: `test_v3_omitted_position_fields_default_to_zero` (OneSaber + NoArrows), `test_v3_omitted_fields_in_90_degree`. Full suite: 407/407 pass.
- **Mass build results:** 38/38 bundles built + verified. Every slot: Standard 5/5 + 90Degree 5/5 + NoArrows 5/5 + OneSaber 5/5. startmeup_v3.bundle 30,889,589 B (byte-identical to deployed Espresso). Side effect: `songs_repo/` source dirs now contain generated mode `.dat` files — fine (gitignored, idempotent on re-run).
- **Deploy prep:** regenerated `redirects.json` (39 redirects: 38 slots + rollingstones pack); wrote `deploy_all38.sh` (lftp upload of all 38 + config). `deploy_all.sh` (old 13-slot, no mode mapping) confirmed outdated — superseded.
- **Deploy status:** 🔴 **BLOCKED** — PS4 FTP (192.168.100.117:2121) unreachable (connection timeout; likely powered off). All 38 bundles ready in `/tmp/opencode/mass_build/`.
- **Version:** Pipeline v0.5316
- **Status:** ✅ Code fix + all 38 bundles built/verified. 🔴 PS4 deploy pending. After deploy: user test — all modes selectable, full audio, Chromeo slots playable.
- **Next steps:** PS4 online → run `deploy_all38.sh` → clear `bs_log.txt` → user test all 38 (spot-check Chromeo slots + new Billie songs + 90Degree on all).

### Experiment 186: Mass Deploy of All 38 Songs — DEPLOYED (2026-08-12)
- **Date:** 2026-08-12
- **Context:** PS4 came back online. Deploy the 38 rebuilt bundles (Exp 185) + regenerated config.
- **Deploy:** Ran `beat_saber_deluxe/deploy_all38.sh` — all 38 bundles uploaded to `/data/GoldHEN/AFR/CUSA12878/` in ~10 min. Sizes on PS4 match local builds exactly (spot-checked all via `ls`). Deployed `redirects.json` (39 redirects: 38 slots + rollingstones pack bundle) — verified on-device content via `cat` + JSON parse. `song_metadata.json` (2382 B, all 38 songs incl. Chromeo) verified byte-identical to local.
- **Plugin:** v0.8040 (`beat_saber_deluxe.prx`, 88,752 B, Aug 6) confirmed present in `/data/GoldHEN/plugins/`.
- **bs_log.txt:** absent (fresh after reboot — expected).
- **Status:** ✅ **DEPLOYED — AWAITING USER TEST.** No `bs_log.txt` pull needed yet (nothing to analyze until a game session runs).
- **Next steps:** user boots Beat Saber → test: all 6 Chromeo slots (Crystallized/CycleHit/ExitThisEarthsAtomosphere/Ghost/LightItUp/WhatTheCat), new Billie songs (Oxytocin/NDA/ThereforeIAm), 90Degree mode across several songs, full audio lengths (no truncation). Pull + archive `bs_log.txt` afterward and record results in song_testing_log.md.

### Experiment 187: Redirect Naming Bug — VALUES pointed at stale `_v3`, not the deployed `.bundle` (2026-08-13)
- **Date:** 2026-08-13
- **Context:** The Aug-13 redeploy uploaded all 38 fresh builds as `<slot>_v3.bundle` (lowercase slot casing, `.bundle` suffix), but the generated `redirects.json` still carried values like `Crystallized_v3` / `startmeup_v3` — no `.bundle`, titlecase. The plugin (`load_redirects` in `src/main.cpp`) opens the redirect VALUE verbatim (prefixed with `AFR_BASE/TITLE_ID/` only), and `open()` is case-sensitive → the game would silently keep serving the stale Jul/Aug builds while the new bundles sat unused on the PS4. Confirmed on-device: both `startmeup_v3` (30,889,577 B) and `startmeup_v3.bundle` (30,889,589 B) existed per slot; the size-check in `verify_ps4_deployment` could not catch it because the stale file also exists.
- **Fix (pipeline v0.5317→0.5318):**
  - `_deployed_bundle_name(slot, config)` — single source of truth: canonical slot casing (case-insensitive match against `mass_deploy.slots`) + `paths.afr_target_suffix` (default now `_v3.bundle`, was `_v3`).
  - `_ensure_mass_song_redirects(redirect_data, config)` — runs on every `manage_redirect_config` save (like the pack/catalog pair): preserves existing redirect KEYS (case-insensitive basename match, e.g. keeps `BeatmapLevelsData/Crystallized`), fixes VALUES to `_deployed_bundle_name`, removes stale pre-`.bundle` entries, adds missing slots.
  - `deploy_mass_bundles` no longer hardcodes a second `.bundle` append — uploads `os.path.basename(local_path)`; `deploy_to_ps4` uses `_deployed_bundle_name`; `manage_redirect_config` dropped its unused `bundle_suffix` param.
- **Verification:** local `redirects.json` regenerated → 40 redirects, every value an exact deployed filename (`BeatmapLevelsData/startmeup -> startmeup_v3.bundle`, `BeatmapLevelsData/Crystallized -> crystallized_v3.bundle`); no non-`.bundle`/`.json` values remain. New `TestDeployedBundleNaming` (6 tests): full suite 419/419 pass.
- **Deploy attempt:** `--deploy-config --verify-ps4` loaded `ps4_config.json`, regenerated + saved correct `redirects.json`, then lftp timed out (PS4 went offline mid-deploy). 🔴 PS4's on-device `redirects.json` is STILL the old `_v3`-valued one.
- **PS4 cleanup planned:** `development/scripts/cleanup_ps4_stale.sh` (dry-run default) removes 58 stale items (old `_v3` builds, titlecase Camellia, old `_v3` dirs, `catalog_test.json`, `ftp_test.txt`, `100bills*`, `startmeup_*`, `resources_patched_v3.assets`, stale pack variants) while keeping all 38 `_v3.bundle` builds + config + plugin. **Ordering is critical: deploy corrected `redirects.json` FIRST, then clean up** (old redirects still point at `_v3` files; deleting those first would crash boot).
- **Version:** Pipeline v0.5318
- **Status:** ✅ **DEPLOYED + PS4 CLEANED (2026-08-13).** Corrected `redirects.json` (40 redirects, all `.bundle` values) live on PS4, verified byte-match on-device. Post-deploy validation PASSED.
- **PS4 cleanup executed:** `cleanup_ps4_stale.sh --yes` removed all 58 stale items — AFR dir went 98 → 44 files. Kept: 38 `_v3.bundle` builds + pack pair + `redirects.json`/`features.json`/`song_metadata.json` + `Media/` + `Plugins/`. (Note: `therollingstones_pack_assets_all_*.bundle` original pack file was removed — it's only the redirect KEY's source path inside the game's own data, never a redirect target on the AFR side; the patched `startmeup_pack_modes.bundle` is the value the game loads.)
- **Pre-existing `bs_log.txt` (Aug 12, 2 boot sessions) pulled + archived:** `.ai_memory/experiment_logs/v0.5316_preexisting_bs_log_2026-08-12.txt` — showed 2 stable boots with the OLD `_v3` config, pack bundle REDIRECTED at OPEN #310/#528/#593/#753 (catalog pair held), no crashes. Log cleared on PS4 for a clean boot test.
- **Next steps:** user boots Beat Saber → test: all 6 Chromeo slots (Crystallized/CycleHit/ExitThisEarthsAtomosphere/Ghost/LightItUp/WhatTheCat), new Billie songs (Oxytocin/NDA/ThereforeIAm), 90Degree mode across several songs, full audio lengths (no truncation). Pull + archive `bs_log.txt` afterward and record results in song_testing_log.md. Confirm the game loads the NEW `.bundle` builds (log should show `startmeup -> .../startmeup_v3.bundle` REDIRECTED, no `_v3` non-bundle opens).
