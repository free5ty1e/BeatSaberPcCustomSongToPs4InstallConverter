#!/bin/bash
# Full custom song installation over The Weeknd music pack using pipeline automation

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
# Requires plugin v0.8043+.
#
# 🔧 NEW: Clear Target Song (--clear-target-song)
# Revert a single custom song slot back to its stock state WITHOUT a full PS4 clean slate:
#   python3 tools/full_custom_song_pipeline.py --clear-target-song <SLOT_NAME>
# This removes: custom song bundle, redirect entry, song/artist metadata, deploys updated configs.


#
# This script deploys each of the 12 The Weeknd pack songs using the
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

echo "=== Deploying The Weeknd pack songs (full orchestration) ==="

# Song 1: Blinding Lights
echo "Deploying Blinding Lights..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target BlindingLights     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Blinding Lights"; exit 1; fi
echo "  Blinding Lights deployed successfully"


# Song 2: Can't Feel My Face
echo "Deploying Can't Feel My Face..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target CantFeelMyFace     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Can't Feel My Face"; exit 1; fi
echo "  Can't Feel My Face deployed successfully"


# Song 3: Die For You (Remix)
echo "Deploying Die For You (Remix)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target DieForYou     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Die For You (Remix)"; exit 1; fi
echo "  Die For You (Remix) deployed successfully"


# Song 4: How Do I Make You Love Me?
echo "Deploying How Do I Make You Love Me?..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target HowDoIMakeYouLoveMe     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed How Do I Make You Love Me?"; exit 1; fi
echo "  How Do I Make You Love Me? deployed successfully"


# Song 5: I Feel It Coming
echo "Deploying I Feel It Coming..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target IFeelItComing     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed I Feel It Coming"; exit 1; fi
echo "  I Feel It Coming deployed successfully"


# Song 6: Less Than Zero
echo "Deploying Less Than Zero..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target LessThanZero     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Less Than Zero"; exit 1; fi
echo "  Less Than Zero deployed successfully"


# Song 7: Pray For Me
echo "Deploying Pray For Me..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_7     --target PrayForMe     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Pray For Me"; exit 1; fi
echo "  Pray For Me deployed successfully"


# Song 8: Sacrifice
echo "Deploying Sacrifice..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_8     --target Sacrifice     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Sacrifice"; exit 1; fi
echo "  Sacrifice deployed successfully"


# Song 9: Save Your Tears
echo "Deploying Save Your Tears..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_9     --target SaveYourTears     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Save Your Tears"; exit 1; fi
echo "  Save Your Tears deployed successfully"


# Song 10: Starboy
echo "Deploying Starboy..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_10     --target Starboy     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Starboy"; exit 1; fi
echo "  Starboy deployed successfully"


# Song 11: Take My Breath
echo "Deploying Take My Breath..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_11     --target TakeMyBreath     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Take My Breath"; exit 1; fi
echo "  Take My Breath deployed successfully"


# Song 12: The Hills
echo "Deploying The Hills..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_12     --target TheHills     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed The Hills"; exit 1; fi
echo "  The Hills deployed successfully"


echo ""
echo "=== All 12 The Weeknd pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
