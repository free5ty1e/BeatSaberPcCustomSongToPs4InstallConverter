#!/bin/bash
# Full custom song installation over Britney Spears music pack using pipeline automation

# 
# ⚠️ NEW: Partial Pack Deployment Safety (v0.5334+)
#
# Problem: When deploying custom songs one at a time, the pack bundle previously
# added extra mode buttons (OneSaber, NoArrows, 90Degree) for ALL songs in the
# pack — even unmodified stock songs. Selecting a stock song and trying to play
# a non-Standard mode would crash the game.
#
# Solution (automatic in --deploy-full):
# 1. Surgical pack bundle patching: The pipeline now builds the pack bundle with
#    extra modes ONLY for the custom song(s) being deployed. Stock songs in the
#    same pack keep only Standard mode.
# 2. Runtime feature flag enable_beatmap_mode_mapping (in features.json): Gates
#    visibility of extra mode sets in the mode selector UI.
#    - OFF (safe default for partial deploys): All songs show only Standard mode.
#    - ON (when pack is complete): Custom songs show all 4 modes; stock songs show
#      only Standard.
#
# Recommended workflow for partial pack deploys:
#   # Option A: Keep feature flag OFF until pack is complete (safest)
#   python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_beatmap_mode_mapping=false
#   # ... deploy songs one at a time ...
#   python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_beatmap_mode_mapping=true
#
#   # Option B: Let automatic surgical patching handle it (default in v0.5334+)
#   # Each --deploy-full only adds extra modes for THAT song in the pack bundle
#   python3 tools/full_custom_song_pipeline.py --download-beat-saver-song <MAP_ID> --target <SLOT> --pcm16 --no-pad --convert-to-v3 --deploy-full
#
#
# 🔌 Global Plugin Kill Switch (enable_plugin)
# Disable the ENTIRE plugin without editing plugins.ini or clearing the PS4 —
# the game plays 100% official songs on the next boot:
#   python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_plugin=false
# Re-enable your custom songs:
#   python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_plugin=true
# Takes effect on next game boot (features.json is read at plugin startup).
# Requires plugin v0.8043+. Boot shows ONE combined toast: "BS Deluxe v<ver> (ON) ... (N/3 features ON)" — or "(OFF) ... (official songs only)" when disabled (v0.8045+).
#
# 🔧 NEW: Clear Target Song (--clear-target-song)
# Revert a single custom song slot back to its stock state WITHOUT a full PS4 clean slate:
#   python3 tools/full_custom_song_pipeline.py --clear-target-song <SLOT_NAME>
# This removes: custom song bundle, redirect entry, song/artist metadata, deploys updated configs.


#
# This script deploys each of the 11 Britney Spears pack songs using the
# per-song pipeline with --deploy-full flag. Each command is complete
# and self-contained - it downloads the custom song from BeatSaver,
# converts to V3.2.0, generates all 4 modes, deploys the song bundle,
# resolves the song's DLC pack and deploys ONLY that one pack + song,
# builds/deploys the plugin + plugins.ini entry + features.json,
# regenerates redirects.json scoped to that song, and runs post-deploy
# validation. All in ONE command.

# Optional: Clean PS4 for a fresh clean-slate state
# Uncomment the next line if you want to start from a completely clean PS4
# python3 /workspace/backup-beat-saber-deluxe-files.py backup --clean-ps4

cd /workspace/beat_saber_deluxe

echo ""
echo "=============================================================="
echo "PRE-DEPLOY CHECK — Current Beat Saber Deluxe state on PS4"
echo "=============================================================="
python3 /workspace/beat_saber_deluxe/development/scripts/ps4_state.py
echo ""
# --no-prompt: skip the interactive confirmation so chained pack scripts
# can run in series without babysitting (e.g. script1.sh --no-prompt &&
# script2.sh --no-prompt && ...). Default (no flag) keeps the prompt.
NO_PROMPT=0
for arg in "$@"; do
    if [ "$arg" = "--no-prompt" ]; then NO_PROMPT=1; fi
done
if [ "$NO_PROMPT" -eq 1 ]; then
    echo "--no-prompt: skipping confirmation, continuing in 3s..."
    sleep 3
else
    echo "Review the PS4 state above. If it is NOT what you expect (e.g. you"
    echo "do not want to proceed from this state), press Ctrl+C to abort."
    echo "Otherwise press Enter to continue with the deployment..."
    read -r _
fi
echo ""

echo "=== Deploying Britney Spears pack songs (full orchestration) ==="

# Song 1: Baby One More Time → Take on Me (a-ha)
echo "Deploying Baby One More Time → Take on Me (a-ha)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 6d63     --target BabyOneMoreTime     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Baby One More Time"; exit 1; fi
echo "  Baby One More Time → Take on Me deployed successfully"

# Song 2: Circus → Shape of You (Ed Sheeran)
echo "Deploying Circus → Shape of You (Ed Sheeran)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1672a     --target Circus     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Circus"; exit 1; fi
echo "  Circus → Shape of You deployed successfully"

# Song 3: Gimme More → That That (PSY ft. SUGA of BTS)
echo "Deploying Gimme More → That That (PSY ft. SUGA of BTS)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 250b5     --target GimmeMore     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Gimme More"; exit 1; fi
echo "  Gimme More → That That deployed successfully"

# Song 4: I'm a Slave 4 U → Believer (Imagine Dragons)
echo "Deploying I'm a Slave 4 U → Believer (Imagine Dragons)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1fef     --target ImASlave4U     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed I'm a Slave 4 U"; exit 1; fi
echo "  I'm a Slave 4 U → Believer deployed successfully"

# Song 5: Me Against The Music → Mr. Blue Sky (Electric Light Orchestra)
echo "Deploying Me Against The Music → Mr. Blue Sky (ELO)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 2fa04     --target MeAgainstTheMusic     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Me Against The Music"; exit 1; fi
echo "  Me Against The Music → Mr. Blue Sky deployed successfully"

# Song 6: Oops!...I Did It Again → Hollaback Girl (Gwen Stefani)
echo "Deploying Oops!...I Did It Again → Hollaback Girl (Gwen Stefani)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 53e4     --target OopsIDidItAgain     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Oops!...I Did It Again"; exit 1; fi
echo "  Oops!...I Did It Again → Hollaback Girl deployed successfully"

# Song 7: Overprotected → Shut Up And Dance (Walk The Moon)
echo "Deploying Overprotected → Shut Up And Dance (Walk The Moon)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 285e8     --target Overprotected     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Overprotected"; exit 1; fi
echo "  Overprotected → Shut Up And Dance deployed successfully"

# Song 8: Scream & Shout → Cold Heart (PNAU Remix) (Elton John & Dua Lipa)
echo "Deploying Scream & Shout → Cold Heart (PNAU Remix) (Elton John & Dua Lipa)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1d9fd     --target "Scream&Shout"     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Scream & Shout"; exit 1; fi
echo "  Scream & Shout → Cold Heart deployed successfully"

# Song 9: Till The World Ends → Dance Monkey (metal cover) (Leo Moracchioli)
echo "Deploying Till The World Ends → Dance Monkey (metal cover) (Leo Moracchioli)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 13f31     --target TillTheWorldEnds     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Till The World Ends"; exit 1; fi
echo "  Till The World Ends → Dance Monkey (metal cover) deployed successfully"

# Song 10: Toxic → Complicated (MELODICKA BROS — Avril Lavigne cover)
echo "Deploying Toxic → Complicated (MELODICKA BROS — Avril Lavigne cover)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 19849     --target Toxic     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Toxic"; exit 1; fi
echo "  Toxic → Complicated deployed successfully"

# Song 11: Womanizer → Teenagers (My Chemical Romance)
echo "Deploying Womanizer → Teenagers (My Chemical Romance)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 217f1     --target Womanizer     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Womanizer"; exit 1; fi
echo "  Womanizer → Teenagers deployed successfully"

echo ''
echo '=== All 11 Britney Spears pack songs deployed (full orchestration) ==='
echo 'Each command handled: song bundle + pack mode bundles + catalog + redirects + validation'
echo ''
echo '=== Deployment complete ==='