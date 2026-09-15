#!/bin/bash
# Full custom song installation over Rocket League music pack using pipeline automation

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
# 🔧 NEW: Clear Target Song (--clear-target-song)
# Revert a single custom song slot back to its stock state WITHOUT a full PS4 clean slate:
#   python3 tools/full_custom_song_pipeline.py --clear-target-song <SLOT_NAME>
# This removes: custom song bundle, redirect entry, song/artist metadata, deploys updated configs.


#
# This script deploys each of the 6 Rocket League pack songs using the
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
echo "Review the PS4 state above. If it is NOT what you expect (e.g. you"
echo "do not want to proceed from this state), press Ctrl+C to abort."
echo "Otherwise press Enter to continue with the deployment..."
read -r _
echo ""

echo "=== Deploying Rocket League pack songs (full orchestration) ==="

# Song 1: Glide
echo "Deploying Glide..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target Glide     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Glide"; exit 1; fi
echo "  Glide deployed successfully"


# Song 2: Luv U Need U
echo "Deploying Luv U Need U..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target LuvUNeedU     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Luv U Need U"; exit 1; fi
echo "  Luv U Need U deployed successfully"


# Song 3: Play
echo "Deploying Play..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target Play     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Play"; exit 1; fi
echo "  Play deployed successfully"


# Song 4: Rock It
echo "Deploying Rock It..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target RockIt     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Rock It"; exit 1; fi
echo "  Rock It deployed successfully"


# Song 5: Shiawase
echo "Deploying Shiawase..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target Shiawase     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Shiawase"; exit 1; fi
echo "  Shiawase deployed successfully"


# Song 6: Test Me
echo "Deploying Test Me..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target TestMe     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Test Me"; exit 1; fi
echo "  Test Me deployed successfully"


echo ""
echo "=== All 6 Rocket League pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
