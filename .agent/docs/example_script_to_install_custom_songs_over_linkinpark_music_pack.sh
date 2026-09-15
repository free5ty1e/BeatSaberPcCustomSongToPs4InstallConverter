#!/bin/bash
# Full custom song installation over Linkin Park music pack using pipeline automation

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
# This script deploys each of the 11 Linkin Park pack songs using the
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

echo "=== Deploying Linkin Park pack songs (full orchestration) ==="

# Song 1: Bleed It Out
echo "Deploying Bleed It Out..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target BleedItOut     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Bleed It Out"; exit 1; fi
echo "  Bleed It Out deployed successfully"


# Song 2: Breaking the Habit
echo "Deploying Breaking the Habit..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target BreakingTheHabit     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Breaking the Habit"; exit 1; fi
echo "  Breaking the Habit deployed successfully"


# Song 3: Faint
echo "Deploying Faint..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target Faint     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Faint"; exit 1; fi
echo "  Faint deployed successfully"


# Song 4: Given Up
echo "Deploying Given Up..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target GivenUp     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Given Up"; exit 1; fi
echo "  Given Up deployed successfully"


# Song 5: In the End
echo "Deploying In the End..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target InTheEnd     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed In the End"; exit 1; fi
echo "  In the End deployed successfully"


# Song 6: New Divide
echo "Deploying New Divide..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target NewDivide     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed New Divide"; exit 1; fi
echo "  New Divide deployed successfully"


# Song 7: Numb
echo "Deploying Numb..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_7     --target Numb     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Numb"; exit 1; fi
echo "  Numb deployed successfully"


# Song 8: One Step Closer
echo "Deploying One Step Closer..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_8     --target OneStepCloser     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed One Step Closer"; exit 1; fi
echo "  One Step Closer deployed successfully"


# Song 9: Papercut
echo "Deploying Papercut..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_9     --target Papercut     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Papercut"; exit 1; fi
echo "  Papercut deployed successfully"


# Song 10: Somewhere I Belong
echo "Deploying Somewhere I Belong..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_10     --target SomewhereIBelong     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Somewhere I Belong"; exit 1; fi
echo "  Somewhere I Belong deployed successfully"


# Song 11: What I've Done
echo "Deploying What I've Done..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_11     --target WhatIveDone     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed What I've Done"; exit 1; fi
echo "  What I've Done deployed successfully"


echo ""
echo "=== All 11 Linkin Park pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
