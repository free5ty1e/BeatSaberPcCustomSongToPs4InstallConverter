#!/bin/bash
# Full custom song installation over Lady Gaga music pack using pipeline automation
#
# This script deploys each of the 10 Lady Gaga pack songs using the
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

echo "=== Deploying Lady Gaga pack songs (full orchestration) ==="

# Song 1: Alejandro
echo "Deploying Alejandro..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target Alejandro     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Alejandro"; exit 1; fi
echo "  Alejandro deployed successfully"


# Song 2: Bad Romance
echo "Deploying Bad Romance..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target BadRomance     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Bad Romance"; exit 1; fi
echo "  Bad Romance deployed successfully"


# Song 3: Born This Way
echo "Deploying Born This Way..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target BornThisWay     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Born This Way"; exit 1; fi
echo "  Born This Way deployed successfully"


# Song 4: Just Dance
echo "Deploying Just Dance..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target JustDance     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Just Dance"; exit 1; fi
echo "  Just Dance deployed successfully"


# Song 5: Paparazzi
echo "Deploying Paparazzi..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target Paparazzi     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Paparazzi"; exit 1; fi
echo "  Paparazzi deployed successfully"


# Song 6: Poker Face
echo "Deploying Poker Face..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target PokerFace     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Poker Face"; exit 1; fi
echo "  Poker Face deployed successfully"


# Song 7: Rain On Me
echo "Deploying Rain On Me..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_7     --target RainOnMe     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Rain On Me"; exit 1; fi
echo "  Rain On Me deployed successfully"


# Song 8: Stupid Love
echo "Deploying Stupid Love..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_8     --target StupidLove     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Stupid Love"; exit 1; fi
echo "  Stupid Love deployed successfully"


# Song 9: Telephone
echo "Deploying Telephone..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_9     --target Telephone     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Telephone"; exit 1; fi
echo "  Telephone deployed successfully"


# Song 10: The Edge Of Glory
echo "Deploying The Edge Of Glory..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_10     --target TheEdgeOfGlory     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed The Edge Of Glory"; exit 1; fi
echo "  The Edge Of Glory deployed successfully"


echo ""
echo "=== All 10 Lady Gaga pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
