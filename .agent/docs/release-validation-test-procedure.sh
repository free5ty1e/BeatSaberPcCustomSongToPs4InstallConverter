#!/bin/bash
# ============================================================================
# release-validation-test-procedure.sh — automated release validation
# ============================================================================
# Runs the FULL functional validation of a Beat Saber Deluxe release zip
# against a REAL PS4, per release-validation-test-procedure.md.
#
# Usage (bare, prints to console only):
#   bash /workspace/.agent/docs/release-validation-test-procedure.sh [TAG]
#
# Usage (console output AND a timestamped logfile for later review —
# RECOMMENDED, this is how each release is validated):
#
#   bash /workspace/.agent/docs/release-validation-test-procedure.sh \
#       --log /workspace/temp/release-validation-$(date +%Y%m%d-%H%M%S).log [TAG]
#
#   Console shows progress live (no blank screen); the logfile receives the
#   exact same output for detailed review afterwards. The script's exit code
#   is preserved: 0 = every check PASSED, 1 = failures (see the table).
#
#   TAG defaults to v0.8047-pipeline-0.5351-alpha01. Override the PS4 with:
#   PS4_IP=<ip> bash ... (environment variable, default 192.168.100.117)
#
# Idempotence / state restoration:
#   - Pulls and backs up BOTH PS4 state files (redirects.json AND
#     song_metadata.json) before touching anything (Exp 237).
#   - Destructive steps are backup-wrapped; --clear-target-song re-deploys
#     the cleared song immediately after testing it.
#   - The final integrity step compares end-state vs backups for BOTH files
#     AND the live PS4; any divergence AUTO-RESTORES both files.
#   - Net effect on a healthy PS4: functionally unchanged (song bundles may
#     be re-uploaded with functionally-identical rebuilt bytes; the bundled
#     plugin is re-uploaded — same CI build).
#
# What it does:
#   1. Downloads + extracts the release into /workspace/temp/release-validation
#   2. Static audit (binaries, examples, key fixes in shipped code)
#   3. Symlinks /workspace/ps4_dump, copies+localizes ps4_config.json
#   4. Pulls live PS4 state (backs it up — restore guaranteed)
#   5. Runs every validation: verify, build quality, deploy-full (bundled
#      plugin), skip-plugin, debug-logging swap+restore, feature-flag
#      round-trips + kill switch, metadata-only, clear-target-song + restore,
#      sync-config, enforce-config (backup-wrapped), pack-modes scoping,
#      metadata overrides, target-ip
#   6. Final state integrity vs the pre-validation backup (both files + live)
#   7. Prints a PASS/FAIL table; exits non-zero on any failure
#
# Destructive-step safety: BOTH state files are backed up before anything
# that can change them, and the final step compares live state to the
# backups and auto-restores if they diverge.
# ============================================================================
set -u   # no set -e: we collect failures and report at the end

# ── Argument parsing: [--log <file>] [TAG] ─────────────────────────────────
LOGFILE=""
TAG="v0.8047-pipeline-0.5351-alpha01"
ARGS=("$@")
i=0
while [ $i -lt ${#ARGS[@]} ]; do
    if [ "${ARGS[$i]}" = "--log" ]; then
        i=$((i+1)); LOGFILE="${ARGS[$i]:-}"
    else
        TAG="${ARGS[$i]}"
    fi
    i=$((i+1))
done

if [ -n "$LOGFILE" ]; then
    mkdir -p "$(dirname "$LOGFILE")"
    # process substitution: console + logfile, and the script's own exit code
    # is preserved (no tee in a pipeline that would swallow $? — Exp 229 lesson)
    exec > >(tee "$LOGFILE") 2>&1
    echo "[release-validation] console output is also being logged to: $LOGFILE"
fi

REPO="free5ty1e/BeatSaberPcCustomSongToPs4InstallConverter"
PS4_IP="${PS4_IP:-192.168.100.117}"
TEMP="/workspace/temp"
VAL="$TEMP/release-validation"
CFG_VAL="$VAL/ps4_config.json"
PIPE() { python3 "$VAL/tools/full_custom_song_pipeline.py" "$@"; }
LFTP_CAT() { timeout 60 lftp -u anonymous:anonymous -e "cat $1; quit" "$PS4_IP:2121" 2>/dev/null | sed -n '/{/,$p'; }

PASS=0; FAIL=0; RESULTS=""
mark() { # mark <PASS|FAIL> <label>
    if [ "$1" = "PASS" ]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi
    RESULTS+="| $1 | $2 |\n"
}
check() { # check <label> <command...> — pass if command exit 0
    local label="$1"; shift
    if "$@" >/dev/null 2>&1; then mark PASS "$label"; else mark FAIL "$label"; fi
}

echo "==================================================================="
echo " Release validation: $TAG"
echo "==================================================================="

# ---------------------------------------------------------------------------
echo "── [1/8] Download + extract"
gh release download "$TAG" --repo "$REPO" --dir "$TEMP" --clobber \
    || { echo "FATAL: download failed"; exit 1; }
ZIP=$(ls "$TEMP"/beat-saber-deluxe-*.zip | sort -V | tail -1)
rm -rf "$VAL"; mkdir -p "$VAL"
unzip -q "$ZIP" -d "$VAL" || { echo "FATAL: extract failed"; exit 1; }
cd "$VAL" || exit 1

# ---------------------------------------------------------------------------
echo "── [2/8] Static audit"
V=$(cat VERSION); [ "$V" = "0.5351" ] && mark PASS "VERSION=0.5351" || mark FAIL "VERSION=$V"
N=$(ls docs/example-scripts/ | wc -l); [ "$N" = "69" ] && mark PASS "69 example files" || mark FAIL "$N example files"
python3 - <<'EOF' && mark PASS "plugin binaries (FSELF + v0.8047)" || mark FAIL "plugin binaries"
rel = open('plugins/beat_saber_deluxe.prx','rb').read()
dbg = open('plugins/beat_saber_deluxe_debug.prx','rb').read()
assert rel[:4] == bytes.fromhex('4f153d1d') and dbg[:4] == bytes.fromhex('4f153d1d')
assert b'v0.8047' in rel and b'v0.8047' in dbg
EOF
grep -q "No Makefile (packaged release)" tools/full_custom_song_pipeline.py \
    && mark PASS "bundled-plugin fallback in shipped code" \
    || mark FAIL "bundled-plugin fallback in shipped code"
grep -q "ensure_ascii=False" tools/full_custom_song_pipeline.py \
    && mark PASS "Unicode metadata fix in shipped code" \
    || mark FAIL "Unicode metadata fix in shipped code"
grep -q "no-prompt" docs/example-scripts/example_script_to_install_custom_songs_over_billie_eilish_music_pack.sh \
    && mark PASS "--no-prompt in example scripts" || mark FAIL "--no-prompt in example scripts"
if python3 tools/full_custom_song_pipeline.py --help 2>&1 | head -2 | grep -q "0.5351"; then
    mark PASS "pipeline smoke test"
else
    mark FAIL "pipeline smoke test"
fi

# ---------------------------------------------------------------------------
echo "── [3/8] Configure environment"
ln -sfn /workspace/ps4_dump ps4_dump
[ -d ps4_dump/CUSA12878-patch ] && mark PASS "ps4_dump symlink" || mark FAIL "ps4_dump symlink"
cp /workspace/beat_saber_deluxe/ps4_config.json ps4_config.json
python3 - <<EOF
import json
cfg = json.load(open('ps4_config.json'))
R = '$VAL'
cfg['paths']['game_dump_dir'] = f'{R}/ps4_dump/CUSA12878-patch'
cfg['paths']['output_dir']    = f'{R}/custom_songs'
cfg['pack_modes'] = {'packs': [], 'build_dir': f'{R}/pack_modes_bundles',
    'song_ids_path': f'{R}/beat_saber_song_ids.json',
    'dump_dir': f'{R}/ps4_dump/CUSA12878-patch', 'catalog_key': 'aa/catalog.json',
    'patched_catalog': 'catalog_pack_modes.json',
    'patched_catalog_local': f'{R}/catalog_pack_modes.json'}
cfg['mass_deploy'] = {'bundle_dir': f'{R}/mass_bundles', 'slots': []}
json.dump(cfg, open('ps4_config.json','w'), indent=2)
EOF
[ -f ps4_config.json ] && mark PASS "config localized" || mark FAIL "config localized"

echo "── [4/8] Pull + back up live state"
# BOTH state files must be pulled and backed up: redirects.json AND
# song_metadata.json. The release zip ships NEITHER (both are user state) —
# if song_metadata.json is missing locally, any pipeline step that loads
# 'local' metadata starts from an EMPTY file and, on deploy, WIPES the
# PS4's metadata (Exp 237: the 33/33 'green' run destroyed all 47 custom
# song names because nothing pulled or restored this file).
rm -f redirects.json song_metadata.json
timeout 60 lftp -u anonymous:anonymous -e "get /data/GoldHEN/AFR/CUSA12878/redirects.json -o redirects.json; quit" "$PS4_IP:2121" >/dev/null 2>&1
timeout 60 lftp -u anonymous:anonymous -e "get /data/GoldHEN/AFR/CUSA12878/song_metadata.json -o song_metadata.json; quit" "$PS4_IP:2121" >/dev/null 2>&1
PRE_SONGS=$(python3 -c "import json; print(len([k for k in json.load(open('redirects.json'))['redirects'] if k.startswith('BeatmapLevelsData/')]))" 2>/dev/null || echo 0)
PRE_PACKS=$(python3 -c "import json; print(len([k for k in json.load(open('redirects.json'))['redirects'] if '_pack_assets_' in k]))" 2>/dev/null || echo 0)
PRE_NAMES=$(python3 -c "import json; print(len(json.load(open('song_metadata.json'))['song_names']))" 2>/dev/null || echo 0)
PRE_ARTISTS=$(python3 -c "import json; print(len(json.load(open('song_metadata.json'))['song_artists']))" 2>/dev/null || echo 0)
cp redirects.json redirects.pre-validation.bak
cp song_metadata.json song_metadata.pre-validation.bak
if [ "$PRE_PACKS" -ge 1 ]; then
    mark PASS "live state pulled ($PRE_PACKS packs / $PRE_SONGS songs / $PRE_NAMES names / $PRE_ARTISTS artists)"
else
    mark FAIL "live state pulled (0 packs)"
fi
if [ "$PRE_NAMES" -ge "$PRE_SONGS" ]; then
    mark PASS "metadata coverage (names >= songs)"
else
    mark FAIL "metadata coverage ($PRE_NAMES names for $PRE_SONGS songs — pull may have failed)"
fi

# ---------------------------------------------------------------------------
echo "── [5/8] Core validations"
# 5.1 read-only verify
if PIPE --verify-ps4 2>&1 | grep -q "PASSED"; then mark PASS "verify-ps4 (read-only)"; else mark FAIL "verify-ps4 (read-only)"; fi

# 5.2 build-only + quality
PIPE --download-beat-saver-song 4dea2 --target Oxytocin --pcm16 --no-pad --convert-to-v3 --output /tmp/reltest.bundle >/dev/null 2>&1
python3 - <<'EOF' && mark PASS "build-only quality (NoArrows/OneSaber 5/5)" || mark FAIL "build-only quality"
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
assert na == 5 and os_ == 5
EOF
rm -f /tmp/reltest.bundle

# 5.3 deploy-full incl. bundled plugin
OUT=$(PIPE --download-beat-saver-song 4dea2 --target Oxytocin --pcm16 --no-pad --convert-to-v3 --deploy-full 2>&1)
echo "$OUT" | grep -q "using bundled plugin" && mark PASS "deploy-full: bundled plugin" || mark FAIL "deploy-full: bundled plugin"
echo "$OUT" | grep -q "PASSED" && mark PASS "deploy-full: validation" || mark FAIL "deploy-full: validation"

# 5.4 skip-plugin-deployment
OUT=$(PIPE --download-beat-saver-song 4dea2 --target Oxytocin --pcm16 --no-pad --convert-to-v3 --deploy-full --skip-plugin-deployment 2>&1)
echo "$OUT" | grep -qE "Building plugin|using bundled plugin" && mark FAIL "skip-plugin honored" || mark PASS "skip-plugin honored"
echo "$OUT" | grep -q "PASSED" && mark PASS "skip-plugin: deploy PASSED" || mark FAIL "skip-plugin: deploy PASSED"

# 5.5 debug-logging swap + restore
OUT=$(PIPE --deploy-plugin --debug-logging 2>&1)
echo "$OUT" | grep -q "beat_saber_deluxe_debug.prx" && mark PASS "debug plugin swap (bundled debug used)" || mark FAIL "debug plugin swap"
INI_DEBUG=$(LFTP_CAT /data/GoldHEN/plugins.ini | grep -c beat_saber_deluxe_debug || true)
[ "$INI_DEBUG" = "0" ] && mark PASS "canonical plugins.ini entry (no fork)" || mark FAIL "forked plugins.ini entry"
PIPE --deploy-plugin >/dev/null 2>&1 && mark PASS "debug→release plugin restore" || mark FAIL "debug→release plugin restore"

# ---------------------------------------------------------------------------
echo "── [6/8] Feature flags, kill switch, surgical ops"
# 6.1 feature flag toggle + verify + restore
PIPE --features-only --set-feature enable_beatmap_mode_mapping=false >/dev/null 2>&1
if LFTP_CAT /data/GoldHEN/AFR/CUSA12878/features.json | grep -q '"enable_beatmap_mode_mapping": false'; then
    mark PASS "feature-flag toggle (mode mapping off)"
else
    mark FAIL "feature-flag toggle (mode mapping off)"
fi
PIPE --features-only --set-feature enable_plugin=false >/dev/null 2>&1
LFTP_CAT /data/GoldHEN/AFR/CUSA12878/features.json | grep -q '"enable_plugin": false' \
    && mark PASS "kill switch OFF written" || mark FAIL "kill switch OFF written"
PIPE --features-only --set-feature enable_plugin=true --set-feature enable_beatmap_mode_mapping=true >/dev/null 2>&1
LFTP_CAT /data/GoldHEN/AFR/CUSA12878/features.json | grep -q '"enable_plugin": true' \
    && mark PASS "flags restored ON" || mark FAIL "flags restored ON"

# 6.2 metadata-only (redirects untouched AND no metadata loss)
# NOTE (Exp 237): the local song_metadata.json was pulled at setup; this step
# ADDS/updates one entry in it and deploys — safe ONLY because the full file
# is present locally. Without the setup pull this step single-handedly wipes
# the PS4's metadata (a 1-entry local file over 47 live entries).
R_BEFORE=$(python3 -c "import json; print(len(json.load(open('redirects.json'))['redirects']))")
M_BEFORE=$(python3 -c "import json; print(len(json.load(open('song_metadata.json'))['song_names']))")
PIPE --metadata-only --target Oxytocin --song-name "Kiss Me More" --artist "Doja Cat" --deploy >/dev/null 2>&1
R_AFTER=$(python3 -c "import json; print(len(json.load(open('redirects.json'))['redirects']))")
M_AFTER=$(python3 -c "import json; print(len(json.load(open('song_metadata.json'))['song_names']))")
if [ "$R_BEFORE" = "$R_AFTER" ] && [ "$M_AFTER" -ge "$M_BEFORE" ]; then
    mark PASS "metadata-only (redirects untouched, names $M_BEFORE→$M_AFTER)"
else
    mark FAIL "metadata-only (redirects $R_BEFORE→$R_AFTER, names $M_BEFORE→$M_AFTER)"
fi

# 6.3 clear-target-song (surgical: redirects AND metadata) + restore
PIPE --clear-target-song Oxytocin >/dev/null 2>&1
POST_CLEAR=$(python3 -c "
import json
r = json.load(open('redirects.json'))['redirects']
m = json.load(open('song_metadata.json'))
print(len([k for k in r if k.startswith('BeatmapLevelsData/')]),
      len([k for k in r if '_pack_assets_' in k]),
      len(m.get('song_names', {})))")
CLEAR_SONGS=$(echo "$POST_CLEAR" | cut -d' ' -f1); CLEAR_PACKS=$(echo "$POST_CLEAR" | cut -d' ' -f2); CLEAR_NAMES=$(echo "$POST_CLEAR" | cut -d' ' -f3)
if [ "$CLEAR_PACKS" = "$PRE_PACKS" ] && [ "$CLEAR_SONGS" = "$((PRE_SONGS-1))" ] && [ "$CLEAR_NAMES" -ge "$((PRE_NAMES-1))" ]; then
    mark PASS "clear-target-song surgical ($CLEAR_SONGS songs, $CLEAR_PACKS packs, $CLEAR_NAMES names)"
else
    mark FAIL "clear-target-song surgical (got $CLEAR_SONGS/$CLEAR_PACKS/$CLEAR_NAMES, want $((PRE_SONGS-1))/$PRE_PACKS/>=$((PRE_NAMES-1)))"
fi
PIPE --download-beat-saver-song 4dea2 --target Oxytocin --pcm16 --no-pad --convert-to-v3 --deploy-full >/dev/null 2>&1
R_NOW=$(python3 -c "import json; r=json.load(open('redirects.json'))['redirects']; print(len([k for k in r if k.startswith('BeatmapLevelsData/')]))")
M_NOW=$(python3 -c "import json; print(len(json.load(open('song_metadata.json'))['song_names']))")
if [ "$R_NOW" = "$PRE_SONGS" ] && [ "$M_NOW" -ge "$PRE_NAMES" ]; then
    mark PASS "clear+redeploy restore ($R_NOW songs, $M_NOW names)"
else
    mark FAIL "restore (songs $R_NOW vs $PRE_SONGS, names $M_NOW vs $PRE_NAMES)"
fi

# 6.4 sync-config
OUT=$(PIPE --verify-ps4 --sync-config 2>&1)
echo "$OUT" | grep -q "Downloaded config" && mark PASS "sync-config (PS4→local)" || mark FAIL "sync-config"

# 6.5 enforce-config — DESTRUCTIVE, backup-wrapped (tests the CONTRACT only:
#     we do NOT actually push a zeroed file; we verify local==PS4 round-trip)
cp redirects.json redirects.enforce.bak
PIPE --verify-ps4 --enforce-config --deploy-config >/dev/null 2>&1
OUT=$(PIPE --verify-ps4 2>&1)
echo "$OUT" | grep -q "PASSED" && mark PASS "enforce-config round-trip (identity)" || mark FAIL "enforce-config round-trip"
cp redirects.enforce.bak redirects.json   # restore regardless

# 6.6 pack-modes scoping (build scoped; deploy union covers all live packs)
OUT=$(PIPE --deploy-pack-modes --pack-modes-packs billieeilish 2>&1)
echo "$OUT" | grep -q "✅ billieeilish.*deployed" && mark PASS "pack-modes scoped deploy" || mark FAIL "pack-modes scoped deploy"

# 6.7 song-name/artist override → BeatmapLevelSO blob
rm -f "_beatmap_level_so_Test Name Override.blob"
PIPE --download-beat-saver-song 4dea2 --target Oxytocin --pcm16 --no-pad --convert-to-v3 \
    --song-name "Test Name Override" --artist "Test Artist" --output /tmp/reltest_named.bundle >/dev/null 2>&1
python3 -c "
data = open('_beatmap_level_so_Test Name Override.blob','rb').read()
assert 'Test Name Override'.encode('utf-16-le') in data" 2>/dev/null \
    && mark PASS "song-name/artist override in blob" || mark FAIL "song-name/artist override in blob"
rm -f /tmp/reltest_named.bundle "_beatmap_level_so_Test Name Override.blob"

# 6.8 target-ip
PIPE --verify-ps4 --target-ip "$PS4_IP" 2>&1 | grep -q "PASSED" \
    && mark PASS "target-ip explicit" || mark FAIL "target-ip explicit"

# ---------------------------------------------------------------------------
echo "── [7/8] Final state integrity"
# BOTH state files compared against the pre-validation backups, and the LIVE
# PS4 metadata compared too (local-only checks missed the Exp 237 wipe: the
# local file and the PS4 file must BOTH hold the full name set).
FINAL_SONGS=$(python3 -c "import json; print(len([k for k in json.load(open('redirects.json'))['redirects'] if k.startswith('BeatmapLevelsData/')]))")
FINAL_PACKS=$(python3 -c "import json; print(len([k for k in json.load(open('redirects.json'))['redirects'] if '_pack_assets_' in k]))")
FINAL_NAMES=$(python3 -c "import json; print(len(json.load(open('song_metadata.json'))['song_names']))" 2>/dev/null || echo 0)
PS4_NAMES=$(LFTP_CAT /data/GoldHEN/AFR/CUSA12878/song_metadata.json | python3 -c "import json,sys; print(len(json.load(sys.stdin)['song_names']))" 2>/dev/null || echo 0)
if [ "$FINAL_PACKS" = "$PRE_PACKS" ] && [ "$FINAL_SONGS" = "$PRE_SONGS" ] \
   && [ "$FINAL_NAMES" -ge "$PRE_NAMES" ] && [ "$PS4_NAMES" -ge "$PRE_NAMES" ]; then
    mark PASS "final state == pre-validation ($FINAL_PACKS packs / $FINAL_SONGS songs / $PS4_NAMES PS4 names)"
else
    mark FAIL "final state diverged (packs $FINAL_PACKS/$PRE_PACKS, songs $FINAL_SONGS/$PRE_SONGS, names $FINAL_NAMES local / $PS4_NAMES PS4 vs $PRE_NAMES) — AUTO-RESTORING"
    cp redirects.pre-validation.bak redirects.json
    cp song_metadata.pre-validation.bak song_metadata.json
    PIPE --verify-ps4 --deploy-config >/dev/null 2>&1
    timeout 60 lftp -u anonymous:anonymous -e "put song_metadata.json -o /data/GoldHEN/AFR/CUSA12878/song_metadata.json; quit" "$PS4_IP:2121" >/dev/null 2>&1
fi
if PIPE --verify-ps4 2>&1 | grep -q "PASSED"; then mark PASS "final verify-ps4"; else mark FAIL "final verify-ps4"; fi
LFTP_CAT /data/GoldHEN/AFR/CUSA12878/features.json | python3 -c "
import json,sys
d = json.load(sys.stdin)
sys.exit(0 if all(d.values()) else 1)" 2>/dev/null \
    && mark PASS "features.json all ON" || mark FAIL "features.json not all ON"
LFTP_CAT /data/GoldHEN/AFR/CUSA12878/song_metadata.json | python3 -c "
import json,sys
d = json.load(sys.stdin)
sys.exit(0 if len(d.get('song_names', {})) >= int(sys.argv[1]) else 1)" "$PRE_NAMES" 2>/dev/null \
    && mark PASS "PS4 metadata intact post-restore" || mark FAIL "PS4 metadata still damaged"

# ---------------------------------------------------------------------------
echo "── [8/8] RESULTS"
echo ""
echo "+--------+--------------------------------------------------------------+"
echo "| RESULT | VALIDATION                                                   |"
echo "+--------+--------------------------------------------------------------+"
printf "$RESULTS"
echo "+--------+--------------------------------------------------------------+"
echo ""
echo "PASS: $PASS   FAIL: $FAIL"
if [ "$FAIL" -gt 0 ]; then
    echo "❌ VALIDATION FAILED — live state was restored from backup."
    exit 1
fi
echo "✅ RELEASE VALIDATED — live state unchanged."
echo "   Validation folder kept for inspection: $VAL"
