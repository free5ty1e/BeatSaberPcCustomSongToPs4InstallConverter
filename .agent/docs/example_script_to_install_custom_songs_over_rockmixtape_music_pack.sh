#!/bin/bash
# Full custom song installation over Rock Mixtape music pack using pipeline automation
#
# This script deploys each of the 8 Rock Mixtape pack songs using the
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

echo "=== Deploying Rock Mixtape pack songs (full orchestration) ==="

# Song 1: Born To Be Wild
echo "Deploying Born To Be Wild..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target BornToBeWild     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Born To Be Wild"; exit 1; fi
echo "  Born To Be Wild deployed successfully"


# Song 2: Eye of the Tiger
echo "Deploying Eye of the Tiger..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target EyeOfTheTiger     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Eye of the Tiger"; exit 1; fi
echo "  Eye of the Tiger deployed successfully"


# Song 3: Free Bird
echo "Deploying Free Bird..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target FreeBird     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Free Bird"; exit 1; fi
echo "  Free Bird deployed successfully"


# Song 4: I Was Made For Lovin' You
echo "Deploying I Was Made For Lovin' You..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target IWasMadeLovingYou     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed I Was Made For Lovin' You"; exit 1; fi
echo "  I Was Made For Lovin' You deployed successfully"


# Song 5: Seven Nation Army
echo "Deploying Seven Nation Army..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target SevenNationArmy     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Seven Nation Army"; exit 1; fi
echo "  Seven Nation Army deployed successfully"


# Song 6: Smells Like Teen Spirit
echo "Deploying Smells Like Teen Spirit..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target SmellsLikeTeenSpirit     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Smells Like Teen Spirit"; exit 1; fi
echo "  Smells Like Teen Spirit deployed successfully"


# Song 7: Sweet Child O' Mine
echo "Deploying Sweet Child O' Mine..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_7     --target SweetChildOMine     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Sweet Child O' Mine"; exit 1; fi
echo "  Sweet Child O' Mine deployed successfully"


# Song 8: The Pretender
echo "Deploying The Pretender..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_8     --target ThePretender     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed The Pretender"; exit 1; fi
echo "  The Pretender deployed successfully"


echo ""
echo "=== All 8 Rock Mixtape pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
