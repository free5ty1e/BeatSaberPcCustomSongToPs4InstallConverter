# Release Validation Test Procedure

Full step-by-step procedure to validate a Beat Saber Deluxe release zip against a
REAL PS4 (with an existing deployment) before publishing the release. This is the
exact procedure used to validate `v0.8047-pipeline-0.5350-alpha01`.

**Time required:** ~20 minutes (most of it is two song builds + an idempotent deploy).

## What this validates

1. The release zip is complete and internally consistent (binaries, configs, all 69 example files, docs)
2. The shipped pipeline tools work **from the extracted release alone** — no repo checkout
3. A song built by the release tools is correct (all-dot NoArrows, blue-dot OneSaber)
4. An idempotent deploy over a LIVE loadout preserves every other pack and song
5. Post-deploy validation passes from the release copy

## Prerequisites

- A PS4 with GoldHEN + FTP (port 2121) reachable from this machine
- A decrypted game dump at `/workspace/ps4_dump/` (base app + v2.04 patch with your DLC loadout)
- Your real PS4 connection info: `/workspace/beat_saber_deluxe/ps4_config.json`
- Python deps: `pip install UnityPy soundfile numpy` (or use the zip's `requirements.txt`)
- `gh` CLI authenticated (for downloading the release)

---

## 1. Download the release

```bash
mkdir -p /workspace/temp
gh release download v0.8047-pipeline-0.5350-alpha01 \
    --repo free5ty1e/BeatSaberPcCustomSongToPs4InstallConverter \
    --dir /workspace/temp
# → /workspace/temp/beat-saber-deluxe-v0.8047-pipeline-0.5350.zip (~859 KB)
```

## 2. Extract to a clean validation folder

```bash
rm -rf /workspace/temp/release-validation
mkdir -p /workspace/temp/release-validation
cd /workspace/temp/release-validation
unzip -q /workspace/temp/beat-saber-deluxe-v0.8047-pipeline-0.5350.zip
```

## 3. Content audit (static checks, no PS4 needed)

### 3a. Inventory

```bash
ls -la
# EXPECT: README.md, PIPELINE-README.md, CHANGELOG-PLUGIN.md, CHANGELOG-PIPELINE.md,
#         VERSION (0.5350), beat_saber_song_ids.json, requirements.txt,
#         features.json, redirects.json (empty template), plugins.ini,
#         ps4_config.example.json, plugins/, tools/, docs/, coverage-report/
ls docs/example-scripts/ | wc -l   # EXPECT: 69
ls docs/features/                  # EXPECT: beatmap-mode-mapping.md, custom-song-replacement.md, song-metadata-modification.md
ls plugins/                        # EXPECT: beat_saber_deluxe.prx, beat_saber_deluxe_debug.prx
cat VERSION                        # EXPECT: 0.5350
```

### 3b. Plugin binary checks

```bash
python3 - <<'EOF'
rel = open('plugins/beat_saber_deluxe.prx','rb').read()
dbg = open('plugins/beat_saber_deluxe_debug.prx','rb').read()
print(f"release prx: {len(rel)} bytes, magic={rel[:4].hex()}", "OK" if rel[:4]==bytes.fromhex('4f153d1d') else "BAD FSELF")
print(f"debug prx:   {len(dbg)} bytes, magic={dbg[:4].hex()}")
print("v0.8047 string in release prx:", b'v0.8047' in rel)
EOF
# EXPECT: both magics 4f153d1d (GoldHEN FSELF), v0.8047 present
```

### 3c. Config templates

```bash
cat redirects.json   # EXPECT: empty template {"titleId":"CUSA12878","afrBase":"/data/GoldHEN/AFR","redirects":{}}
cat features.json    # EXPECT: all four flags, enable_plugin true
grep -c "no-prompt" docs/example-scripts/example_script_to_install_custom_songs_over_billie_eilish_music_pack.sh
# EXPECT: >0 (the --no-prompt parameter is in the shipped scripts)
```

## 4. Configure the validation environment

### 4a. Symlink the game dump

The release zip does NOT include game data (see the release notes disclaimer).
Symlink the existing dump so the pipeline can read the stock pack bundles +
origin catalog without duplicating ~1 GB:

```bash
cd /workspace/temp/release-validation
ln -s /workspace/ps4_dump ps4_dump
python3 -c "import os; print('dump symlink OK:', os.path.isdir('ps4_dump/CUSA12878-patch'))"
# EXPECT: dump symlink OK: True
```

### 4b. Copy your PS4 config and LOCALIZE THE PATHS

```bash
cp /workspace/beat_saber_deluxe/ps4_config.json ps4_config.json
```

⚠️ **REQUIRED — localize the absolute paths.** The config (and the pipeline's
built-in defaults) reference the development workspace (`/workspace/beat_saber_deluxe/...`,
`/workspace/ps4_dump/...`). Point every path at the extraction folder:

```bash
python3 - <<'EOF'
import json
ROOT = '/workspace/temp/release-validation'
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
print("ps4_config.json localized to", ROOT)
EOF
```

(When validating a FUTURE release, replace `ROOT` with wherever you extracted.)

### 4c. Smoke-test the shipped pipeline

```bash
python3 tools/full_custom_song_pipeline.py --help 2>&1 | head -3
# EXPECT: "🎵 Beat Saber Deluxe Pipeline 0.5350" with Project: <your extraction folder>
```

## 5. Pull the live PS4 state (validating against an existing loadout)

The zip ships an EMPTY redirects.json template (correct for a fresh consumer).
To validate against your live PS4 WITHOUT disturbing it, pull the live state
(read-only on the PS4 side):

```bash
cd /workspace/temp/release-validation
rm redirects.json   # remove the empty template first (lftp won't clobber)
timeout 60 lftp -u anonymous:anonymous \
    -e "get /data/GoldHEN/AFR/CUSA12878/redirects.json -o redirects.json; quit" \
    192.168.100.117:2121
python3 -c "import json; print('pulled', len(json.load(open('redirects.json'))['redirects']), 'redirects')"
# EXPECT: pulled 53 redirects (or your current count)
```

> Fresh-PS4 validation: skip this step and validate from the empty template instead
> (the mismatch warnings are then expected).

## 6. Validation A — read-only PS4 verify

```bash
timeout 300 python3 tools/full_custom_song_pipeline.py --verify-ps4 2>&1 | tail -8
# EXPECT: 🎉 Post-deploy validation PASSED
#   - PS4 reachable: N files in AFR dir
#   - redirects.json on PS4 matches local (53 redirects)
#   - All 53 redirect targets exist on PS4
#   - catalog dataIndexes valid, md5 matches local build
```

## 7. Validation B — build-only (no deploy)

Proves the full conversion chain from the shipped tools: BeatSaver download →
audio → V4/V2→V3 conversion → mode generation → bundle build.

```bash
timeout 550 python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song 4dea2 --target Oxytocin \
    --pcm16 --no-pad --convert-to-v3 \
    --output Oxytocin_release_test.bundle 2>&1 | tail -5
# EXPECT: "Pipeline complete!", 5/5 beatmaps replaced, ~36.7 MB bundle
```

Then check the built bundle's chart quality (the Exp 231/218 generator fixes
must be in the shipped code):

```bash
python3 - <<'EOF'
import UnityPy, gzip, json
env = UnityPy.load('Oxytocin_release_test.bundle')
na = os = 0
for obj in env.objects:
    if obj.type.name != 'TextAsset': continue
    d = obj.read()
    if '.beatmap' not in d.m_Name: continue
    s = d.m_Script
    raw = s.encode('utf-8','surrogateescape') if isinstance(s, str) else (s.get_raw_data() if hasattr(s,'get_raw_data') else bytes(s))
    j = json.loads(gzip.decompress(raw).decode('utf-8','surrogateescape'))
    if 'NoArrows' in d.m_Name:
        if {n.get('d',8) for n in j['colorNotes']} == {8}: na += 1
    if 'OneSaber' in d.m_Name:
        notes = j['colorNotes']
        if {n.get('d',8) for n in notes} == {8} and {n.get('c',0) for n in notes} == {1}: os += 1
print(f"NoArrows all-dots: {na}/5 (EXPECT 5/5), OneSaber blue-dots: {os}/5 (EXPECT 5/5)")
EOF
rm -f "Oxytocin_release_test.bundle" "_beatmap_level_so_Kiss Me More.blob"
```

## 8. Validation C — idempotent deploy over the live loadout

Re-deploys a song that is ALREADY live: no state change, but exercises FTP
uploads, incremental pack patching, catalog regeneration, and redirect
preservation from the release copy.

⚠️ **Use `--skip-plugin-deployment`.** The release zip ships tools only — no
`src/`, no Makefile — so `--deploy-full`'s plugin build step fails from the
extracted copy (see Findings #2). The shipped `plugins/beat_saber_deluxe.prx`
is the same v0.8047 build already on the PS4.

```bash
timeout 590 python3 tools/full_custom_song_pipeline.py \
    --download-beat-saver-song 4dea2 --target Oxytocin \
    --pcm16 --no-pad --convert-to-v3 --deploy-full \
    --skip-plugin-deployment 2>&1 | grep -E "Preserving|Processing pack|PASSED|FAILED" | head -12
# EXPECT:
#   Preserving existing packs with custom songs: <all your other packs>
#   Preserving existing custom songs: <all your other slots>
#   📦 Processing pack: <one line per deployed pack — ALL of them>
#   ... validation PASSED
```

## 9. Validation D — post-deploy state integrity

```bash
timeout 120 python3 tools/full_custom_song_pipeline.py --verify-ps4 2>&1 | grep -E "PASSED|FAILED"
python3 -c "
import json
r = json.load(open('redirects.json'))['redirects']
pe = sorted(k.split('_')[0] for k in r if '_pack_assets_' in k)
se = [k for k in r if k.startswith('BeatmapLevelsData/')]
print(f'{len(pe)} pack redirects {pe}')
print(f'{len(se)} song redirects; ghosts:', any('deadmanwalking' in k or 'sugarsoaker' in k for k in se))
print('catalog redirect:', 'aa/catalog.json' in r)
"
# EXPECT: 5 packs, all your songs, no ghosts, catalog present, validation PASSED
```

Confirm the PS4 plugin was untouched:

```bash
timeout 60 lftp -u anonymous:anonymous \
    -e "cat /data/GoldHEN/plugins/beat_saber_deluxe.prx > /tmp/ps4_prx_check.bin; quit" \
    192.168.100.117:2121
python3 -c "print('v0.8047 still on PS4:', b'v0.8047' in open('/tmp/ps4_prx_check.bin','rb').read())"
# EXPECT: True
```

## 10. Cleanup (optional)

```bash
# The validation folder is disposable: everything in it (except the ps4_dump
# symlink target) was created by the release. Keep it for the release record or:
cd /workspace
rm -rf /workspace/temp/release-validation /workspace/temp/beat-saber-deluxe-*.zip
```

---

## Expected-results summary

| Check | Expected (alpha01 actual) |
|---|---|
| Zip contents | README ×2, changelogs ×2, VERSION 0.5350, song_ids, requirements, features/redirects templates, 2 plugin binaries, tools/, coverage, docs (3 features + 2 examples + **69 example scripts**) — ✅ all present |
| Plugin binaries | FSELF magic `4f153d1d`, v0.8047 strings — ✅ both |
| Pipeline smoke | Runs standalone, correct PROJECT_ROOT — ✅ |
| Read-only verify (live PS4) | 🎉 PASSED (53 redirects, catalog valid) — ✅ |
| Build-only | 5/5 beatmaps, NoArrows 5/5 all-dots, OneSaber 5/5 blue-dots — ✅ |
| Idempotent deploy | All other packs + songs preserved, validation PASSED — ✅ |
| Post-deploy state | 5 packs, all songs, no ghosts, plugin untouched — ✅ |

## Findings from the alpha01 audit (fix before / at the real release)

1. **Pipeline defaults are devcontainer-absolute** (`/workspace/beat_saber_deluxe/...`,
   `/workspace/ps4_dump/...` in `full_custom_song_pipeline.py` DEFAULT_CONFIG and
   `ps4_config.example.json`). A consumer extracting anywhere else MUST localize
   ~7 path values (step 4b) or every pack-mode operation fails with missing-file
   errors. **Recommended fix (pipeline change → v0.5351+): make defaults relative
   to PROJECT_ROOT** so an extracted release works with only the symlink +
   ps4 IP entered. Until then, step 4b of this procedure is REQUIRED.
2. **`--deploy-full` tries to build the plugin from source, but the release
   ships no `src/` or Makefile** → the documented quick-start command fails
   from the zip alone (`RuntimeError: Plugin build failed`). Workaround today:
   always pass `--skip-plugin-deployment` from an extracted release (the shipped
   .prx is the same build CI deployed). **Recommended fix: `build_plugin` falls
   back to the bundled `plugins/beat_saber_deluxe.prx` when no Makefile exists**
   (or bundle src/ + Makefile in the zip).
3. Cosmetic: `requirements.txt` in the zip is the repo's `requirements-test.txt`
   (includes pytest/ruff). Fine for a dev-oriented release; a consumer-only
   variant would list just UnityPy/soundfile/numpy.

Neither finding blocks the alpha; both are one-line-adjacent fixes to fold in
before the final release tag.
