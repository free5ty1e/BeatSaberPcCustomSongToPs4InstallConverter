#!/bin/bash
# Full custom song installation over Interscope music pack using pipeline automation
#
# This script deploys each of the 7 Interscope pack songs using the
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

echo "=== Deploying Interscope pack songs (full orchestration) ==="

# Song 1: Counting Stars
echo "Deploying Counting Stars..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target CountingStars     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Counting Stars"; exit 1; fi
echo "  Counting Stars deployed successfully"


# Song 2: DNA.
echo "Deploying DNA...."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target DnaLamar     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed DNA."; exit 1; fi
echo "  DNA. deployed successfully"


# Song 3: Don't Cha
echo "Deploying Don't Cha..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target DontCha     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Don't Cha"; exit 1; fi
echo "  Don't Cha deployed successfully"


# Song 4: Party Rock Anthem
echo "Deploying Party Rock Anthem..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target PartyRockAnthem     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Party Rock Anthem"; exit 1; fi
echo "  Party Rock Anthem deployed successfully"


# Song 5: Rollin' (Air Raid Vehicle)
echo "Deploying Rollin' (Air Raid Vehicle)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target Rollin     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Rollin' (Air Raid Vehicle)"; exit 1; fi
echo "  Rollin' (Air Raid Vehicle) deployed successfully"


# Song 6: Sugar
echo "Deploying Sugar..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target Sugar     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Sugar"; exit 1; fi
echo "  Sugar deployed successfully"


# Song 7: The Sweet Escape
echo "Deploying The Sweet Escape..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_7     --target TheSweetEscape     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed The Sweet Escape"; exit 1; fi
echo "  The Sweet Escape deployed successfully"


echo ""
echo "=== All 7 Interscope pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
