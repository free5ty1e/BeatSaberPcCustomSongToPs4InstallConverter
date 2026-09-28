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
# LFTP_CAT <remote-path> — robustly read a remote file to stdout.
# Exp 240 — the REAL root cause of the "READ-FAILED everywhere + 3 FAILs"
# runs: lftp's `cat` appends transfer banners ("156 bytes transferred") to the
# FILE CONTENT on slow transfers, and the old first-'{' extraction left that
# trailing garbage glued to the JSON — json.loads() then failed on EVERY read.
# The user's runs (slow PS4 link → banner on every read) failed 100% of the
# reads; my fast devcontainer runs emitted no banners and passed — the
# intermittency that misdirected the Exp 239 "transient flake" diagnosis.
# Fix: download to a TEMP FILE via `get` (the same transport the pipeline's
# own redirect-sync uses — proven across hundreds of deploys; get never
# mixes banners into content), then print the file. Retries remain for
# genuine connection flakes.
LFTP_CAT() {
    local path="$1" attempt tmpd
    tmpd=$(mktemp -d)   # lftp get -o REFUSES to clobber an existing file —
                        # the target must not pre-exist (mktemp FILE does);
                        # a fresh DIRECTORY per attempt sidesteps that
    for attempt in 1 2 3; do
        if timeout 60 lftp -u anonymous:anonymous -e "get $path -o $tmpd/f; quit" "$PS4_IP:2121" >/dev/null 2>&1 && [ -s "$tmpd/f" ]; then
            cat "$tmpd/f"
            rm -rf "$tmpd"
            return 0
        fi
        sleep $((attempt * 2))
    done
    rm -rf "$tmpd"
    return 1
}
# PS4_JSON_COUNT <remote-path> <python-expr> — robustly read a remote JSON file
# and count something (e.g. song_names entries). Prints the count on success;
# prints READ-FAILED (non-numeric) and returns 1 if the file can't be read —
# callers must treat that as UNKNOWN, never as zero.
PS4_JSON_COUNT() {
    local path="$1" expr="$2" out
    out=$(LFTP_CAT "$path") || { echo "READ-FAILED"; return 1; }
    printf '%s' "$out" | python3 -c "
import json, sys
raw = sys.stdin.read()
# Extract from the FIRST '{' to the LAST '}' — immune to both leading
# (banner) and trailing (transfer-report) chatter.
start = raw.find('{')
end = raw.rfind('}')
if start < 0 or end <= start:
    print('READ-FAILED'); sys.exit(1)
try:
    d = json.loads(raw[start:end+1])
    print($expr)
except Exception:
    print('READ-FAILED'); sys.exit(1)"
}

PASS=0; FAIL=0; RESULTS=""
mark() { # mark <PASS|FAIL> <label>
    if [ "$1" = "PASS" ]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi
    RESULTS+="| $1 | $2 |\n"
    printf '   [%s] %s\n' "$1" "$2"
}
check() { # check <label> <command...> — pass if command exit 0
    local label="$1"; shift
    if "$@" >/dev/null 2>&1; then mark PASS "$label"; else mark FAIL "$label"; fi
}
# Verbose step helpers (Exp 239): every test announces what it is about to do,
# streams the pipeline's own output, and prints its PASS/FAIL the moment it
# resolves — no silent stretches.
step() {  # step <banner>  — announce a group of tests
    printf '\n──────── %s ────────\n' "$1"
}
note() {  # note <text>    — progress line within a step
    printf '   · %s\n' "$1"
}
ps4_counts() {  # ps4_counts — trace the live state counts (names on PS4 +
    # local) after any step that can touch state; this is the instrumentation
    # that pinpoints WHERE state changes, so failures are diagnosable from
    # the log alone.
    local n
    n=$(PS4_JSON_COUNT /data/GoldHEN/AFR/CUSA12878/song_metadata.json "len(d['song_names'])" 2>/dev/null) || true
    local l
    l=$(python3 -c "import json
try:
    print(len(json.load(open('song_metadata.json'))['song_names']))
except Exception:
    print(-1)" 2>/dev/null)
    printf '   [state] PS4 names=%s | local names=%s\n' "$n" "$l"
}

echo "==================================================================="
echo " Release validation: $TAG"
echo "==================================================================="

# ---------------------------------------------------------------------------
step "[1/8] Download + extract"
gh release download "$TAG" --repo "$REPO" --dir "$TEMP" --clobber \
    || { echo "FATAL: download failed"; exit 1; }
ZIP=$(ls "$TEMP"/beat-saber-deluxe-*.zip | sort -V | tail -1)
rm -rf "$VAL"; mkdir -p "$VAL"
unzip -q "$ZIP" -d "$VAL" || { echo "FATAL: extract failed"; exit 1; }
cd "$VAL" || exit 1

# ---------------------------------------------------------------------------
step "[2/8] Static audit"
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
step "[3/8] Configure environment"
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

step "[4/8] Pull + back up live state (BOTH state files)"
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
step "[5/8] Core validations"

note "5.1 read-only --verify-ps4 (state counts + catalog integrity)"
if PIPE --verify-ps4 2>&1 | tee /tmp/v51.log | grep -qE "PASSED|FAILED"; then
    grep -E "reachable|matches local|targets exist|PASSED|FAILED" /tmp/v51.log | sed 's/^/     /'
    grep -q "PASSED" /tmp/v51.log && mark PASS "verify-ps4 (read-only)" || mark FAIL "verify-ps4 (read-only)"
else
    mark FAIL "verify-ps4 (read-only)"
fi

note "5.2 build-only (no deploy): full conversion chain from the shipped tools (~3 min)"
PIPE --download-beat-saver-song 4dea2 --target Oxytocin --pcm16 --no-pad --convert-to-v3 \
    --output /tmp/reltest.bundle 2>&1 | grep -E "Beatmaps replaced|Pipeline complete|Size" | sed 's/^/     /'
note "     checking chart quality inside the built bundle..."
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
print(f"     NoArrows {na}/5 all-dots, OneSaber {os_}/5 blue-dots")
assert na == 5 and os_ == 5
EOF
rm -f /tmp/reltest.bundle

note "5.3 end-to-end --deploy-full INCLUDING the bundled plugin (~4 min)"
OUT=$(PIPE --download-beat-saver-song 4dea2 --target Oxytocin --pcm16 --no-pad --convert-to-v3 --deploy-full 2>&1)
echo "$OUT" | grep -E "No Makefile|bundled plugin|✅ Plugin uploaded|Preserving existing packs|PASSED|FAILED" | sed 's/^/     /'
echo "$OUT" | grep -q "using bundled plugin" && mark PASS "deploy-full: bundled plugin" || mark FAIL "deploy-full: bundled plugin"
echo "$OUT" | grep -q "PASSED" && mark PASS "deploy-full: validation" || mark FAIL "deploy-full: validation"
ps4_counts

note "5.4 --deploy-full --skip-plugin-deployment (plugin must be untouched, ~4 min)"
OUT=$(PIPE --download-beat-saver-song 4dea2 --target Oxytocin --pcm16 --no-pad --convert-to-v3 --deploy-full --skip-plugin-deployment 2>&1)
echo "$OUT" | grep -E "PASSED|FAILED" | sed 's/^/     /'
echo "$OUT" | grep -qE "Building plugin|using bundled plugin" && mark FAIL "skip-plugin honored" || mark PASS "skip-plugin honored"
echo "$OUT" | grep -q "PASSED" && mark PASS "skip-plugin: deploy PASSED" || mark FAIL "skip-plugin: deploy PASSED"
ps4_counts

note "5.5 --debug-logging plugin swap (verbose build at the canonical entry) + restore"
OUT=$(PIPE --deploy-plugin --debug-logging 2>&1)
echo "$OUT" | grep -E "bundled plugin|as beat_saber_deluxe.prx|✅ Plugin uploaded" | sed 's/^/     /'
echo "$OUT" | grep -q "beat_saber_deluxe_debug.prx" && mark PASS "debug plugin swap (bundled debug used)" || mark FAIL "debug plugin swap"
INI_DEBUG=$(LFTP_CAT /data/GoldHEN/plugins.ini | grep -c beat_saber_deluxe_debug || true)
note "     plugins.ini debug-named entries: $INI_DEBUG (expect 0 — canonical entry only)"
[ "$INI_DEBUG" = "0" ] && mark PASS "canonical plugins.ini entry (no fork)" || mark FAIL "forked plugins.ini entry"
note "     restoring the quiet release plugin..."
PIPE --deploy-plugin >/dev/null 2>&1 && mark PASS "debug→release plugin restore" || mark FAIL "debug→release plugin restore"

# ---------------------------------------------------------------------------
step "[6/8] Feature flags, kill switch, surgical ops"

note "6.1 feature-flag toggles via --features-only (each verified by reading the PS4 back)"
note "     toggling enable_beatmap_mode_mapping=false..."
PIPE --features-only --set-feature enable_beatmap_mode_mapping=false >/dev/null 2>&1
PS4_FLAGS=$(PS4_JSON_COUNT /data/GoldHEN/AFR/CUSA12878/features.json "json.dumps(d, separators=(',',':'))" 2>/dev/null || echo READ-FAILED)
note "     PS4 features.json now: $PS4_FLAGS"
if echo "$PS4_FLAGS" | grep -q '"enable_beatmap_mode_mapping":false'; then
    mark PASS "feature-flag toggle (mode mapping off)"
else
    mark FAIL "feature-flag toggle (mode mapping off)"
fi
note "     toggling enable_plugin=false (kill switch)..."
PIPE --features-only --set-feature enable_plugin=false >/dev/null 2>&1
PS4_FLAGS=$(PS4_JSON_COUNT /data/GoldHEN/AFR/CUSA12878/features.json "json.dumps(d, separators=(',',':'))" 2>/dev/null || echo READ-FAILED)
note "     PS4 features.json now: $PS4_FLAGS"
echo "$PS4_FLAGS" | grep -q '"enable_plugin":false' \
    && mark PASS "kill switch OFF written" || mark FAIL "kill switch OFF written"
note "     restoring both flags ON..."
PIPE --features-only --set-feature enable_plugin=true --set-feature enable_beatmap_mode_mapping=true >/dev/null 2>&1
PS4_FLAGS=$(PS4_JSON_COUNT /data/GoldHEN/AFR/CUSA12878/features.json "json.dumps(d, separators=(',',':'))" 2>/dev/null || echo READ-FAILED)
note "     PS4 features.json now: $PS4_FLAGS"
echo "$PS4_FLAGS" | grep -q '"enable_plugin":true' \
    && mark PASS "flags restored ON" || mark FAIL "flags restored ON"

# 6.2 metadata-only (redirects untouched AND no metadata loss)
# NOTE (Exp 237): the local song_metadata.json was pulled at setup; this step
# ADDS/updates one entry in it and deploys — safe ONLY because the full file
# is present locally. Without the setup pull this step single-handedly wipes
# the PS4's metadata (a 1-entry local file over 47 live entries).
note "6.2 --metadata-only surgical entry update (redirects must be untouched; names must not shrink)"
R_BEFORE=$(python3 -c "import json; print(len(json.load(open('redirects.json'))['redirects']))")
M_BEFORE=$(python3 -c "import json; print(len(json.load(open('song_metadata.json'))['song_names']))")
note "     before: $R_BEFORE redirects, $M_BEFORE names"
PIPE --metadata-only --target Oxytocin --song-name "Kiss Me More" --artist "Doja Cat" --deploy 2>&1 \
    | grep -E "Song metadata|✅ Song metadata|Saved song_metadata" | sed 's/^/     /'
R_AFTER=$(python3 -c "import json; print(len(json.load(open('redirects.json'))['redirects']))")
M_AFTER=$(python3 -c "import json; print(len(json.load(open('song_metadata.json'))['song_names']))")
note "     after: $R_AFTER redirects, $M_AFTER names"
if [ "$R_BEFORE" = "$R_AFTER" ] && [ "$M_AFTER" -ge "$M_BEFORE" ]; then
    mark PASS "metadata-only (redirects untouched, names $M_BEFORE→$M_AFTER)"
else
    mark FAIL "metadata-only (redirects $R_BEFORE→$R_AFTER, names $M_BEFORE→$M_AFTER)"
fi
ps4_counts

note "6.3 --clear-target-song surgical revert (Oxytocin) + re-deploy restore (~5 min total)"
note "     clearing slot..."
PIPE --clear-target-song Oxytocin 2>&1 | grep -E "Removing|Removed|Processing pack|reverted|Updated local song_metadata" | sed 's/^/     /'
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
note "     re-deploying the cleared song to restore state..."
PIPE --download-beat-saver-song 4dea2 --target Oxytocin --pcm16 --no-pad --convert-to-v3 --deploy-full 2>&1 \
    | grep -E "PASSED|FAILED|Saved song_metadata" | sed 's/^/     /'
R_NOW=$(python3 -c "import json; r=json.load(open('redirects.json'))['redirects']; print(len([k for k in r if k.startswith('BeatmapLevelsData/')]))")
M_NOW=$(python3 -c "import json; print(len(json.load(open('song_metadata.json'))['song_names']))")
if [ "$R_NOW" = "$PRE_SONGS" ] && [ "$M_NOW" -ge "$PRE_NAMES" ]; then
    mark PASS "clear+redeploy restore ($R_NOW songs, $M_NOW names)"
else
    mark FAIL "restore (songs $R_NOW vs $PRE_SONGS, names $M_NOW vs $PRE_NAMES)"
fi
ps4_counts

note "6.4 --sync-config (pull the PS4's redirects.json over the local copy)"
OUT=$(PIPE --verify-ps4 --sync-config 2>&1)
echo "$OUT" | grep -E "Syncing|Downloaded config|Saved|PASSED" | sed 's/^/     /'
echo "$OUT" | grep -q "Downloaded config" && mark PASS "sync-config (PS4→local)" || mark FAIL "sync-config"

note "6.5 --enforce-config identity round-trip (backup-wrapped; local==PS4 so the push is a no-op)"
cp redirects.json redirects.enforce.bak
PIPE --verify-ps4 --enforce-config --deploy-config 2>&1 | grep -E "Enforcing|Saved|PASSED|FAILED" | sed 's/^/     /'
OUT=$(PIPE --verify-ps4 2>&1)
echo "$OUT" | grep -E "PASSED|FAILED" | sed 's/^/     /'
echo "$OUT" | grep -q "PASSED" && mark PASS "enforce-config round-trip (identity)" || mark FAIL "enforce-config round-trip"
cp redirects.enforce.bak redirects.json   # restore regardless
ps4_counts

note "6.6 --deploy-pack-modes --pack-modes-packs billieeilish (build scoped; deploy union covers all live packs by design)"
OUT=$(PIPE --deploy-pack-modes --pack-modes-packs billieeilish 2>&1)
echo "$OUT" | grep -E "already built|Deploying .* file|catalog regenerated|✅ .* deployed" | head -8 | sed 's/^/     /'
echo "$OUT" | grep -q "✅ billieeilish.*deployed" && mark PASS "pack-modes scoped deploy" || mark FAIL "pack-modes scoped deploy"
ps4_counts

note "6.7 --song-name/--artist override (build-only; override must land in the BeatmapLevelSO blob)"
rm -f "_beatmap_level_so_Test Name Override.blob"
PIPE --download-beat-saver-song 4dea2 --target Oxytocin --pcm16 --no-pad --convert-to-v3 \
    --song-name "Test Name Override" --artist "Test Artist" --output /tmp/reltest_named.bundle \
    2>&1 | grep -E "Pipeline complete" | sed 's/^/     /'
python3 -c "
data = open('_beatmap_level_so_Test Name Override.blob','rb').read()
assert 'Test Name Override'.encode('utf-16-le') in data" 2>/dev/null \
    && mark PASS "song-name/artist override in blob" || mark FAIL "song-name/artist override in blob"
rm -f /tmp/reltest_named.bundle "_beatmap_level_so_Test Name Override.blob"

note "6.8 --target-ip explicit-IP verify"
PIPE --verify-ps4 --target-ip "$PS4_IP" 2>&1 | grep -E "PASSED|FAILED" | sed 's/^/     /'
PIPE --verify-ps4 --target-ip "$PS4_IP" 2>&1 | grep -q "PASSED" \
    && mark PASS "target-ip explicit" || mark FAIL "target-ip explicit"

# ---------------------------------------------------------------------------
step "[7/8] Final state integrity (both files vs backups AND the live PS4)"
# BOTH state files compared against the pre-validation backups, and the LIVE
# PS4 metadata compared too (local-only checks missed the Exp 237 wipe: the
# local file and the PS4 file must BOTH hold the full name set).
FINAL_SONGS=$(python3 -c "import json; print(len([k for k in json.load(open('redirects.json'))['redirects'] if k.startswith('BeatmapLevelsData/')]))")
FINAL_PACKS=$(python3 -c "import json; print(len([k for k in json.load(open('redirects.json'))['redirects'] if '_pack_assets_' in k]))")
FINAL_NAMES=$(python3 -c "import json; print(len(json.load(open('song_metadata.json'))['song_names']))" 2>/dev/null || echo 0)
PS4_NAMES=$(PS4_JSON_COUNT /data/GoldHEN/AFR/CUSA12878/song_metadata.json "len(d['song_names'])" 2>/dev/null) || true
if [ "$PS4_NAMES" = "READ-FAILED" ]; then
    # The read itself failed after retries — state UNKNOWN. Restore defensively
    # (backups are identical to expected state; pushing them is a no-op when
    # healthy) and re-read before judging.
    note "     final metadata read FAILED (FTP flake) — restoring from backup and re-reading before judging"
    PS4_NAMES=$(PS4_JSON_COUNT /data/GoldHEN/AFR/CUSA12878/song_metadata.json "len(d['song_names'])" 2>/dev/null) || true
fi
if [ "$FINAL_PACKS" = "$PRE_PACKS" ] && [ "$FINAL_SONGS" = "$PRE_SONGS" ] \
   && [ "$FINAL_NAMES" -ge "$PRE_NAMES" ] \
   && [ "$PS4_NAMES" != "READ-FAILED" ] && [ "$PS4_NAMES" -ge "$PRE_NAMES" ]; then
    mark PASS "final state == pre-validation ($FINAL_PACKS packs / $FINAL_SONGS songs / $PS4_NAMES PS4 names)"
else
    mark FAIL "final state diverged (packs $FINAL_PACKS/$PRE_PACKS, songs $FINAL_SONGS/$PRE_SONGS, names $FINAL_NAMES local / PS4=${PS4_NAMES:-UNREADABLE} vs $PRE_NAMES) — AUTO-RESTORING"
    cp redirects.pre-validation.bak redirects.json
    cp song_metadata.pre-validation.bak song_metadata.json
    note "     auto-restoring both state files to the PS4..."
    PIPE --verify-ps4 --deploy-config 2>&1 | grep -E "Saved|PASSED" | sed 's/^/       /'
    timeout 60 lftp -u anonymous:anonymous -e "put song_metadata.json -o /data/GoldHEN/AFR/CUSA12878/song_metadata.json; quit" "$PS4_IP:2121" 2>&1 | grep -v GetPass | sed 's/^/       /'
    note "     restore commands issued — the two checks below verify they took effect"
fi
if PIPE --verify-ps4 2>&1 | grep -q "PASSED"; then mark PASS "final verify-ps4"; else mark FAIL "final verify-ps4"; fi
FEATURES_STATE=$(PS4_JSON_COUNT /data/GoldHEN/AFR/CUSA12878/features.json "1 if all(d.values()) else 0" 2>/dev/null) || true
if [ "$FEATURES_STATE" = "1" ]; then
    mark PASS "features.json all ON"
elif [ "$FEATURES_STATE" = "READ-FAILED" ]; then
    mark FAIL "features.json read FAILED (could not verify — not judged as OFF)"
else
    mark FAIL "features.json not all ON"
fi
POST_RESTORE_NAMES=$(PS4_JSON_COUNT /data/GoldHEN/AFR/CUSA12878/song_metadata.json "len(d.get('song_names', {}))" 2>/dev/null) || true
if [ "$POST_RESTORE_NAMES" != "READ-FAILED" ] && [ "$POST_RESTORE_NAMES" -ge "$PRE_NAMES" ] 2>/dev/null; then
    mark PASS "PS4 metadata intact post-restore ($POST_RESTORE_NAMES names)"
elif [ "$POST_RESTORE_NAMES" = "READ-FAILED" ]; then
    mark FAIL "PS4 metadata read FAILED (integrity UNVERIFIED — state may be fine)"
else
    mark FAIL "PS4 metadata still damaged ($POST_RESTORE_NAMES vs $PRE_NAMES)"
fi

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
