#!/bin/bash
# Full custom song installation over Skrillex music pack using pipeline automation
#
# This script deploys each of the 8 Skrillex pack songs using the
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

echo "=== Deploying Skrillex pack songs (full orchestration) ==="

# Song 1: Bangarang
echo "Deploying Bangarang..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target Bangarang     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Bangarang"; exit 1; fi
echo "  Bangarang deployed successfully"


# Song 2: Butterflies
echo "Deploying Butterflies..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target Butterflies     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Butterflies"; exit 1; fi
echo "  Butterflies deployed successfully"


# Song 3: Don't Go
echo "Deploying Don't Go..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target DontGo     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Don't Go"; exit 1; fi
echo "  Don't Go deployed successfully"


# Song 4: First of the Year
echo "Deploying First of the Year..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target FirstOfTheYear     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed First of the Year"; exit 1; fi
echo "  First of the Year deployed successfully"


# Song 5: Ragga Bomb
echo "Deploying Ragga Bomb..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target RaggaBomb     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Ragga Bomb"; exit 1; fi
echo "  Ragga Bomb deployed successfully"


# Song 6: Rock 'n' Roll
echo "Deploying Rock 'n' Roll..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target RockNRoll     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Rock 'n' Roll"; exit 1; fi
echo "  Rock 'n' Roll deployed successfully"


# Song 7: Scary Monsters and Nice Sprites
echo "Deploying Scary Monsters and Nice Sprites..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_7     --target ScaryMonstersAndNiceSprites     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Scary Monsters and Nice Sprites"; exit 1; fi
echo "  Scary Monsters and Nice Sprites deployed successfully"


# Song 8: The Devil's Den
echo "Deploying The Devil's Den..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_8     --target TheDevilsDen     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed The Devil's Den"; exit 1; fi
echo "  The Devil's Den deployed successfully"


echo ""
echo "=== All 8 Skrillex pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
