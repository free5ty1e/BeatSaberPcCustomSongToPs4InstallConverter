#!/bin/bash
# Full custom song installation over Monstercat Vol. 2 music pack using pipeline automation
#
# This script deploys each of the 12 Monstercat Vol. 2 pack songs using the
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

echo "=== Deploying Monstercat Vol. 2 pack songs (full orchestration) ==="

# Song 1: Accelerate
echo "Deploying Accelerate..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target Accelerate     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Accelerate"; exit 1; fi
echo "  Accelerate deployed successfully"


# Song 2: DABADABADABADABA
echo "Deploying DABADABADABADABA..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target Dabadabadabadaba     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed DABADABADABADABA"; exit 1; fi
echo "  DABADABADABADABA deployed successfully"


# Song 3: Dead Man Walking
echo "Deploying Dead Man Walking..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target DeadManWalking     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Dead Man Walking"; exit 1; fi
echo "  Dead Man Walking deployed successfully"


# Song 4: Endgame
echo "Deploying Endgame..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target Endgame     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Endgame"; exit 1; fi
echo "  Endgame deployed successfully"


# Song 5: Final Boss
echo "Deploying Final Boss..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target FinalBoss     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Final Boss"; exit 1; fi
echo "  Final Boss deployed successfully"


# Song 6: Memory Bank
echo "Deploying Memory Bank..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target MemoryBank     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Memory Bank"; exit 1; fi
echo "  Memory Bank deployed successfully"


# Song 7: Mercenary
echo "Deploying Mercenary..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_7     --target Mercenary     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Mercenary"; exit 1; fi
echo "  Mercenary deployed successfully"


# Song 8: Pump
echo "Deploying Pump..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_8     --target Pump     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Pump"; exit 1; fi
echo "  Pump deployed successfully"


# Song 9: RAD
echo "Deploying RAD..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_9     --target Rad     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed RAD"; exit 1; fi
echo "  RAD deployed successfully"


# Song 10: RIOT
echo "Deploying RIOT..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_10     --target RIOT     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed RIOT"; exit 1; fi
echo "  RIOT deployed successfully"


# Song 11: Thrones of Blood
echo "Deploying Thrones of Blood..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_11     --target ThronesOfBlood     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Thrones of Blood"; exit 1; fi
echo "  Thrones of Blood deployed successfully"


# Song 12: Wake Up
echo "Deploying Wake Up..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_12     --target WakeUp     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Wake Up"; exit 1; fi
echo "  Wake Up deployed successfully"


echo ""
echo "=== All 12 Monstercat Vol. 2 pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
