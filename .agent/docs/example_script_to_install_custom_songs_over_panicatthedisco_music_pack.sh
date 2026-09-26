#!/bin/bash
# Full custom song installation over Panic! At The Disco music pack using pipeline automation

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
# This script deploys each of the 10 Panic! At The Disco pack songs using the
# per-song pipeline with --deploy-full flag. Each command is complete
# and self-contained - it downloads the custom song from BeatSaver,
# converts to V3.2.0, generates all 4 modes, deploys the song bundle,
# resolves the song's DLC pack and deploys ONLY that one pack + song,
# builds/deploys the plugin + plugins.ini entry + features.json,
# regenerates redirects.json scoped to that song, and runs post-deploy
# validation. All in ONE command.
#
# IMPORTANT: Replace all REPLACE_MAP_ID placeholders with actual BeatSaver MAP IDs
# before running this script!

cd /workspace/beat_saber_deluxe

# Optional: Clean PS4 for a fresh clean-slate state
# Uncomment the next line if you want to start from a completely clean PS4
# python3 /workspace/backup-beat-saber-deluxe-files.py backup --clean-ps4

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

echo "=== Deploying Panic! At The Disco pack songs (full orchestration) ==="

# Song 1: Crazy = Genius
echo "Deploying Crazy = Genius..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target CrazyGenius     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Crazy = Genius"; exit 1; fi
echo "  Crazy = Genius deployed successfully"


# Song 2: Dancing's Not A Crime
echo "Deploying Dancing's Not A Crime..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target DancingsNotACrime     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Dancing's Not A Crime"; exit 1; fi
echo "  Dancing's Not A Crime deployed successfully"


# Song 3: Emperor's New Clothes
echo "Deploying Emperor's New Clothes..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target EmperorsNewClothes     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Emperor's New Clothes"; exit 1; fi
echo "  Emperor's New Clothes deployed successfully"


# Song 4: Hey Look Ma, I Made It
echo "Deploying Hey Look Ma, I Made It..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target HeyLookMaIMadeIt     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Hey Look Ma, I Made It"; exit 1; fi
echo "  Hey Look Ma, I Made It deployed successfully"


# Song 5: High Hopes
echo "Deploying High Hopes..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target HighHopes     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed High Hopes"; exit 1; fi
echo "  High Hopes deployed successfully"


# Song 6: Say Amen (Saturday Night)
echo "Deploying Say Amen (Saturday Night)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target SayAmen     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Say Amen (Saturday Night)"; exit 1; fi
echo "  Say Amen (Saturday Night) deployed successfully"


# Song 7: Sugar Soaker
echo "Deploying Sugar Soaker..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_7     --target SugarSoaker     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Sugar Soaker"; exit 1; fi
echo "  Sugar Soaker deployed successfully"


# Song 8: The Greatest Show
echo "Deploying The Greatest Show..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_8     --target TheGreatestShow     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed The Greatest Show"; exit 1; fi
echo "  The Greatest Show deployed successfully"


# Song 9: Victorious
echo "Deploying Victorious..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_9     --target Victorious     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Victorious"; exit 1; fi
echo "  Victorious deployed successfully"


# Song 10: Viva Las Vengeance
echo "Deploying Viva Las Vengeance..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_10     --target VivaLasVengeance     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Viva Las Vengeance"; exit 1; fi
echo "  Viva Las Vengeance deployed successfully"


echo ""
echo "=== All 10 Panic! At The Disco pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
