# Release Validation Test Procedure — Full Functional Coverage

Complete procedure to validate a Beat Saber Deluxe release zip against a REAL
PS4. Covers **all release functionality**: static audit, read-only state
validation, build quality, end-to-end deploys (plugin included), feature-flag
round-trips, kill switch, surgical revert + restore, config sync/enforce,
plugin variant swaps, pack-mode scoping, metadata overrides, and final
state-integrity checks.

- **Manual doc (this file):** every step with full commands + expected results.
- **Automation companion:** `release-validation-test-procedure.sh` runs the
  entire sequence and prints a PASS/FAIL table. Destructive steps back up and
  restore live state automatically.

**Time required (manual):** ~45–60 min. Automated: ~25 min (dominated by two
song builds + deploys).

Validated against: `v0.8047-pipeline-0.5351-alpha01` (Exps 234–236).

## Prerequisites

- PS4 with GoldHEN + FTP (port 2121) reachable; Beat Saber CUSA12878
- Decrypted game dump at `/workspace/ps4_dump/` (v2.04 patch + your DLC loadout)
- Your working config: `/workspace/beat_saber_deluxe/ps4_config.json`
- Python deps: `UnityPy`, `soundfile`, `numpy` (or the zip's `requirements.txt`)
- `gh` CLI authenticated

> **Validating against a LIVE loadout:** the procedure is written for a PS4
> that already has deployments (the interesting case). Fresh-PS4 notes are
> inline where behavior differs. Every destructive step has a RESTORE step —
> do not skip restores.

---

## Part 1 — Setup

### 1.1 Download the release

```bash
mkdir -p /workspace/temp
cd /workspace/temp
gh release download v0.8047-pipeline-0.5351-alpha01 \
    --repo free5ty1e/BeatSaberPcCustomSongToPs4InstallConverter \
    --dir /workspace/temp --clobber
# → beat-saber-deluxe-v0.8047-pipeline-0.5351.zip (~861 KB)
```

### 1.2 Extract

```bash
rm -rf /workspace/temp/release-validation
mkdir -p /workspace/temp/release-validation
cd /workspace/temp/release-validation
unzip -q ../beat-saber-deluxe-v0.8047-pipeline-0.5351.zip
```

### 1.3 Static audit (no PS4 needed)

```bash
cat VERSION                      # EXPECT: 0.5351
ls docs/example-scripts/ | wc -l # EXPECT: 69
ls plugins/                      # EXPECT: beat_saber_deluxe.prx + beat_saber_deluxe_debug.prx
python3 - <<'EOF'
rel = open('plugins/beat_saber_deluxe.prx','rb').read()
dbg = open('plugins/beat_saber_deluxe_debug.prx','rb').read()
assert rel[:4] == bytes.fromhex('4f153d1d') and dbg[:4] == bytes.fromhex('4f153d1d'), "FSELF magic"
assert b'v0.8047' in rel and b'v0.8047' in dbg
print("binaries OK: FSELF + v0.8047, sizes", len(rel), len(dbg))
EOF
grep -c "no-prompt" docs/example-scripts/example_script_to_install_custom_songs_over_billie_eilish_music_pack.sh
# EXPECT: >0
grep -n "No Makefile (packaged release)" tools/full_custom_song_pipeline.py
# EXPECT: a hit (bundled-plugin fallback shipped)
grep -c "ensure_ascii=False" tools/full_custom_song_pipeline.py
# EXPECT: >0 (Unicode metadata fix shipped)
```

### 1.4 Symlink the game dump

The release ships NO game data (copyright — the release notes say so).
Symlink the existing dump:

```bash
cd /workspace/temp/release-validation
ln -s /workspace/ps4_dump ps4_dump
python3 -c "import os; assert os.path.isdir('ps4_dump/CUSA12878-patch'); print('dump OK')"
```

### 1.5 Copy + localize the PS4 config

```bash
cp /workspace/beat_saber_deluxe/ps4_config.json ps4_config.json
python3 - <<'EOF'
import json
ROOT = '/workspace/temp/release-validation'   # change to your extraction folder
cfg = json.load(open('ps4_config.json'))
cfg['paths']['game_dump_dir'] = f'{ROOT}/ps4_dump/CUSA12878-patch'
cfg['paths']['output_dir']    = f'{ROOT}/custom_songs'
cfg['pack_modes'] = {
    'packs': [],
    'build_dir': f'{ROOT}/pack_modes_bundles',
    'song_ids_path': f'{ROOT}/beat_saber_song_ids.json',
    'dump_dir': f'{ROOT}/ps4_dump/CUSA12878-patch',
    'catalog_key': 'aa/catalog.json',
    'patched_catalog': 'catalog_pack_modes.json',
    'patched_catalog_local': f'{ROOT}/catalog_pack_modes.json',
}
cfg['mass_deploy'] = {'bundle_dir': f'{ROOT}/mass_bundles', 'slots': []}
json.dump(cfg, open('ps4_config.json','w'), indent=2)
print("localized")
EOF
```

> **Why:** the pipeline's built-in defaults are devcontainer-absolute paths
> (release finding #1 — post-merge fix pending). Until then this step is REQUIRED.

### 1.6 Pull the live PS4 state (live-loadout validation)

```bash
rm redirects.json   # remove the empty template (lftp won't clobber)
timeout 60 lftp -u anonymous:anonymous \
    -e "get /data/GoldHEN/AFR/CUSA12878/redirects.json -o redirects.json; quit" \
    192.168.100.117:2121
python3 -c "import json; print('pulled', len(json.load(open('redirects.json'))['redirects']), 'redirects')"
# EXPECT: your live count (e.g. 53)
cp redirects.json redirects.pre-validation.bak   # safety net for Part 3
```

> Fresh PS4: skip the pull; the empty template is then correct.

### 1.7 Smoke-test the shipped pipeline

```bash
python3 tools/full_custom_song_pipeline.py --help 2>&1 | head -3
# EXPECT: "🎵 Beat Saber Deluxe Pipeline 0.5351" + Project: <extraction folder>
```

---

## Part 2 — Core validations

### 2.1 Read-only state verify

```bash
timeout 300 python3 tools/full_custom_song_pipeline.py --verify-ps4 2>&1 | tail -6
# EXPECT: 🎉 Post-deploy validation PASSED
#   PS4 reachable: N files in AFR dir
#   redirects.json on PS4 matches local (N redirects)
#   All N redirect targets exist on PS4
#   catalog dataIndexes valid / md5 matches local build
```

### 2.2 Build-only quality (no deploy)

```bash
timeout 550 python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song 4dea2 --target Oxytocin \
    --pcm16 --no-pad --convert-to-v3 --output /tmp/reltest.bundle 2>&1 | tail -4
# EXPECT: "Beatmaps replaced: 5/5", "Pipeline complete!", ~36.7 MB bundle

python3 - <<'EOF'   # chart quality: the shipped generators must be correct
import UnityPy, gzip, json
env = UnityPy.load('/tmp/reltest.bundle')
na = os_ = 0
for obj in env.objects:
    if obj.type.name != 'TextAsset': continue
    d = obj.read()
    if '.beatmap' not in d.m_Name: continue
    s = d.m_Script
    raw = s.encode('utf-8','surrogateescape') if isinstance(s, str) else (s.get_raw_data() if hasattr(s,'get_raw_data') else bytes(s))
    j = json.loads(gzip.decompress(raw).decode('utf-8','surrogateescape'))
    if 'NoArrows' in d.m_Name and {n.get('d',8) for n in j['colorNotes']} == {8}: na += 1
    if 'OneSaber' in d.m_Name:
        notes = j['colorNotes']
        if {n.get('d',8) for n in notes} == {8} and {n.get('c',0) for n in notes} == {1}: os_ += 1
print(f"EXPECT 5/5 + 5/5 → NoArrows {na}/5, OneSaber {os_}/5")
assert na == 5 and os_ == 5
EOF
rm -f /tmp/reltest.bundle
```

### 2.3 End-to-end `--deploy-full` — including the plugin

The packaged release has no Makefile, so the plugin step uses the **bundled
CI build** (Exp 235 behavior):

```bash
timeout 590 python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song 4dea2 --target Oxytocin \
    --pcm16 --no-pad --convert-to-v3 --deploy-full 2>&1 | grep -E "No Makefile|bundled|✅ Plugin|Preserving existing packs|PASSED|FAILED"
# EXPECT:
#   No Makefile (packaged release) — using bundled plugin: plugins/beat_saber_deluxe.prx
#   ✅ Plugin uploaded / plugins.ini updated
#   Preserving existing packs with custom songs: <your other packs>
#   🎉 Post-deploy validation PASSED
```

Idempotent on a song that is already live — state is preserved, not duplicated.

### 2.4 `--skip-plugin-deployment`

```bash
timeout 590 python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song 4dea2 --target Oxytocin \
    --pcm16 --no-pad --convert-to-v3 --deploy-full --skip-plugin-deployment \
    2>&1 | grep -cE "Building plugin|bundled plugin"
# EXPECT: 0 (no plugin activity at all) — and deploy still PASSED
```

### 2.5 `--debug-logging` plugin swap (canonical entry, both directions)

```bash
# Swap IN the verbose-logging build:
timeout 300 python3 tools/full_custom_song_pipeline.py --deploy-plugin --debug-logging 2>&1 \
    | grep -E "bundled plugin|Deploying .* as beat_saber_deluxe.prx"
# EXPECT: uses plugins/beat_saber_deluxe_debug.prx, deploys AS the canonical name

# Verify live + no forked plugins.ini entry:
timeout 60 lftp -u anonymous:anonymous -e "cat /data/GoldHEN/plugins.ini; quit" 192.168.100.117:2121 \
    | grep -c beat_saber_deluxe_debug
# EXPECT: 0 (single canonical entry)

# RESTORE the quiet build (do not skip):
timeout 300 python3 tools/full_custom_song_pipeline.py --deploy-plugin 2>&1 | grep "✅ Plugin uploaded"
```

> Byte-compare caveat: GoldHEN FTPD unpacks FSELF on download, so the
> downloaded .prx shows ELF magic and a different size than the local FSELF —
> compare version strings + size deltas (debug unpacks ~110,136 vs release
> ~110,040), not bytes.

---

## Part 3 — Feature flags & kill switch

### 3.1 Toggle a feature flag via `--features-only`

```bash
timeout 120 python3 tools/full_custom_song_pipeline.py \
    --features-only --set-feature enable_beatmap_mode_mapping=false 2>&1 | grep "✅ Features"
# verify on the PS4:
timeout 60 lftp -u anonymous:anonymous \
    -e "cat /data/GoldHEN/AFR/CUSA12878/features.json; quit" 192.168.100.117:2121
# EXPECT: "enable_beatmap_mode_mapping": false
```

In-game effect (optional, needs a boot): mode-selector buttons hidden; customs
still play Standard. Restore before continuing.

### 3.2 Kill-switch round-trip

```bash
timeout 120 python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_plugin=false
# verify PS4 features.json: enable_plugin false → boot shows (OFF) toast, official songs only
# RESTORE:
timeout 120 python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_plugin=true
# verify PS4 features.json: all true
```

### 3.3 Restore ALL flags (final state must be all-ON)

```bash
timeout 120 python3 tools/full_custom_song_pipeline.py --features-only \
    --set-feature enable_plugin=true \
    --set-feature enable_custom_song_replacements=true \
    --set-feature enable_song_metadata_modification=true \
    --set-feature enable_beatmap_mode_mapping=true
# verify PS4 features.json: every value true
```

---

## Part 4 — Surgical operations (each with a RESTORE)

### 4.1 `--metadata-only`

```bash
python3 -c "import json; print(len(json.load(open('redirects.json'))['redirects']), 'redirects before')"
timeout 120 python3 tools/full_custom_song_pipeline.py \
    --metadata-only --target Oxytocin --song-name "Kiss Me More" --artist "Doja Cat" --deploy 2>&1 \
    | grep -E "Song metadata|✅ Song metadata"
python3 -c "import json; print(len(json.load(open('redirects.json'))['redirects']), 'redirects after (UNCHANGED)')"
# EXPECT: same count before/after — metadata-only touches song_metadata.json only
```

### 4.2 `--clear-target-song` + restore

```bash
timeout 300 python3 tools/full_custom_song_pipeline.py --clear-target-song Oxytocin 2>&1 \
    | grep -E "Processing pack|reverted"
python3 -c "
import json
r = json.load(open('redirects.json'))['redirects']
se = [k for k in r if k.startswith('BeatmapLevelsData/')]
print('songs:', len(se), '| Oxytocin removed:', 'BeatmapLevelsData/Oxytocin' not in r)
packs = [k for k in r if '_pack_assets_' in k]
print('packs STILL:', len(packs))   # EXPECT: all packs intact (surgical)
"
timeout 120 python3 tools/full_custom_song_pipeline.py --verify-ps4 2>&1 | grep -E "PASSED|FAILED"
# RESTORE (re-deploy the song):
timeout 590 python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song 4dea2 --target Oxytocin \
    --pcm16 --no-pad --convert-to-v3 --deploy-full 2>&1 | grep -E "PASSED|FAILED"
# EXPECT: song count back to original; validation PASSED
```

### 4.3 `--sync-config` (pull PS4 → local)

```bash
timeout 120 python3 tools/full_custom_song_pipeline.py --verify-ps4 --sync-config 2>&1 \
    | grep -E "Syncing|Downloaded config|Saved|PASSED"
# EXPECT: "Downloaded config with N redirects" + Saved + PASSED
```

### 4.4 ⚠️ `--enforce-config` — DESTRUCTIVE (backup first!)

`--enforce-config` is **"push local state to the PS4, ignore PS4 data"** — its
contract. If your local redirects.json is stale/empty, you WIPE the PS4's
state. And `--verify-ps4` compares local-vs-PS4, so a wiped PS4 with an empty
local file still reports PASSED (release finding: verification blind spot).

```bash
cp redirects.json redirects.enforce.bak        # MANDATORY backup
# ... run your enforce scenario ...
# RESTORE if anything went wrong:
cp redirects.enforce.bak redirects.json
timeout 120 python3 tools/full_custom_song_pipeline.py --verify-ps4 --deploy-config 2>&1 | grep -E "Saved|PASSED"
# verify PS4: redirect count restored
```

> The automation script backs up automatically and enforces restore. Post-merge
> hardening (finding): `--verify-ps4` should flag catastrophic shrinkage
> (local pack redirects missing on PS4 that exist locally).

### 4.5 `--generate-config` / `--deploy-config` (no target)

```bash
timeout 120 python3 tools/full_custom_song_pipeline.py --verify-ps4 --generate-config --deploy-config 2>&1 \
    | grep -E "Saved|PASSED"
# EXPECT: "Saved redirects.json (N redirects)" — same N (no target → nothing added/removed)
```

---

## Part 5 — Pack-mode scoping & deploy-only modes

### 5.1 `--deploy-pack-modes --pack-modes-packs <one pack>`

```bash
timeout 300 python3 tools/full_custom_song_pipeline.py \
    --deploy-pack-modes --pack-modes-packs billieeilish 2>&1 | tail -8
# EXPECT: builds scoped to the requested pack, but the DEPLOY uploads ALL
# deployed packs' bundles + the merged catalog — by design (Exp 226/227):
# the catalog must describe every pack that is live on the PS4. This is NOT
# a scoping bug. Every upload line must end "✅ ... deployed".
```

### 5.2 `--deploy-mass-bundles` (validation config has no slots)

```bash
timeout 120 python3 tools/full_custom_song_pipeline.py --deploy-mass-bundles 2>&1 | tail -3
# EXPECT: "⚠️ No mass_deploy.slots configured — nothing to deploy" (no-op)
```

### 5.3 Build-parameter variants (no PS4 change)

```bash
# --song-name/--artist override: lands in the BeatmapLevelSO blob (UTF-16LE)
timeout 550 python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song 4dea2 --target Oxytocin --pcm16 --no-pad --convert-to-v3 \
    --song-name "Test Name Override" --artist "Test Artist" --output /tmp/reltest_named.bundle 2>&1 \
    | grep "Pipeline complete"
python3 -c "
data = open('_beatmap_level_so_Test Name Override.blob','rb').read()
assert 'Test Name Override'.encode('utf-16-le') in data, 'override missing from blob'
print('override in BeatmapLevelSO blob: OK')"
rm -f /tmp/reltest_named.bundle "_beatmap_level_so_Test Name Override.blob"
```

Other build-only flags (`--enable-modes`, `--skip-mode-generation`,
`--one-saber-min-gap`, `--rotation-cycle-beats`, `--fallback-mode-map`,
`--preserve-metadata`, `--ignore-non-standard-beatmaps`, `--hevag`,
`--vorbis`, `--no-convert-to-v3`, `--pad-fsb5`) alter chart/audio generation;
they are exercised implicitly by any build. Spot-check `--skip-mode-generation`
(a build with it must produce NO `*OneSaber*/*NoArrows*/*90Degree*` files)
if desired.

### 5.4 `--target-ip` override

```bash
timeout 120 python3 tools/full_custom_song_pipeline.py --verify-ps4 --target-ip 192.168.100.117 2>&1 | grep -E "PASSED|reachable"
# EXPECT: PASSED (same PS4 via explicit IP)
```

---

## Part 6 — Final state integrity (must be green before calling validation done)

```bash
timeout 120 python3 tools/full_custom_song_pipeline.py --verify-ps4 2>&1 | grep -E "PASSED|FAILED"
python3 -c "
import json
r = json.load(open('redirects.json'))['redirects']
packs = sorted(k.split('_')[0] for k in r if '_pack_assets_' in k)
songs = [k for k in r if k.startswith('BeatmapLevelsData/')]
print(f'{len(packs)} packs {packs}'); print(f'{len(songs)} songs'); print('catalog:', 'aa/catalog.json' in r)
"
# EXPECT: identical pack list + song count to Part 1.6's pull; validation PASSED
timeout 60 lftp -u anonymous:anonymous -e "cat /data/GoldHEN/AFR/CUSA12878/features.json; quit" 192.168.100.117:2121 \
    | python3 -c "import json,sys; raw=sys.stdin.read(); d=json.loads(raw[raw.find('{'):]); assert all(d.values()); print('all flags ON')"
```

## Expected-results summary

| # | Validation | Expected (alpha01 actual) |
|---|---|---|
| 1 | Static audit | VERSION 0.5351, 69 examples, FSELF binaries w/ v0.8047, fallback + Unicode fixes in shipped code — ✅ |
| 2 | `--verify-ps4` (live) | 🎉 PASSED, N redirects, catalog md5 match — ✅ |
| 3 | Build-only + quality | 5/5 beatmaps; NoArrows 5/5 all-dots; OneSaber 5/5 blue-dots — ✅ |
| 4 | `--deploy-full` (bundled plugin) | Plugin deployed from zip, packs preserved, PASSED — ✅ |
| 5 | `--skip-plugin-deployment` | Zero plugin activity, deploy PASSED — ✅ |
| 6 | `--debug-logging` swap + restore | Debug binary at canonical entry, no forked ini line, restore OK — ✅ |
| 7 | Feature-flag toggles | Each written+verified on PS4, restored all-ON — ✅ |
| 8 | Kill-switch round-trip | enable_plugin false→true verified both ways — ✅ |
| 9 | `--metadata-only` | Entry updated; redirect count unchanged — ✅ |
| 10 | `--clear-target-song` + restore | Surgical (1 song removed, packs intact), restore OK — ✅ |
| 11 | `--sync-config` | PS4 state pulled, Saved N, PASSED — ✅ |
| 12 | ⚠️ `--enforce-config` | Contract honored (local pushes to PS4) — **backup mandatory**; verify-blind-spot finding recorded — ✅ (with restore) |
| 13 | `--pack-modes-packs` scoping | Build scoped; deploy union covers all live packs by design — ✅ |
| 14 | `--song-name/--artist` override | In BeatmapLevelSO blob (UTF-16LE) — ✅ |
| 15 | `--target-ip` | Explicit-IP verify PASSED — ✅ |
| 16 | Final state | Packs/songs/flags identical to pre-validation — ✅ |

## Findings (record post-merge hardening items)

1. **Devcontainer-absolute default paths** (carried over from alpha00): consumers MUST localize config paths (step 1.5). Post-merge: PROJECT_ROOT-relative defaults.
2. **`--enforce-config` + verify blind spot**: enforce pushed a zeroed local file over live state during testing (restored from backup); `--verify-ps4` PASSED against the wiped PS4 because both sides were empty. Post-merge: verify should flag catastrophic shrinkage (pack redirects present locally but absent on PS4).
3. Cosmetic: zip `requirements.txt` includes test-only deps (pytest/ruff).
