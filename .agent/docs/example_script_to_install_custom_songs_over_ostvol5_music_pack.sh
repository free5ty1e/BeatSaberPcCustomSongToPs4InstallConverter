#!/bin/bash
# Full custom song installation over Soundtrack Vol. 5 music pack using pipeline automation
#
# This script deploys each of the 6 Soundtrack Vol. 5 pack songs using the
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

echo "=== Deploying Soundtrack Vol. 5 pack songs (full orchestration) ==="

# Song 1: Curtains (All Night Long)
echo "Deploying Curtains (All Night Long)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target CurtainsAllNightLong     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Curtains (All Night Long)"; exit 1; fi
echo "  Curtains (All Night Long) deployed successfully"


# Song 2: $1.78
echo "Deploying $1.78..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target DollarSeventyEight     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed $1.78"; exit 1; fi
echo "  $1.78 deployed successfully"


# Song 3: Final-Boss-Chan
echo "Deploying Final-Boss-Chan..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target FinalBossChan     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Final-Boss-Chan"; exit 1; fi
echo "  Final-Boss-Chan deployed successfully"


# Song 4: Firestarter
echo "Deploying Firestarter..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target Firestarter     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Firestarter"; exit 1; fi
echo "  Firestarter deployed successfully"


# Song 5: I Wanna Be a Machine
echo "Deploying I Wanna Be a Machine..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target IWannaBeAMachine     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed I Wanna Be a Machine"; exit 1; fi
echo "  I Wanna Be a Machine deployed successfully"


# Song 6: Magic
echo "Deploying Magic..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target Magic     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Magic"; exit 1; fi
echo "  Magic deployed successfully"


echo ""
echo "=== All 6 Soundtrack Vol. 5 pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
