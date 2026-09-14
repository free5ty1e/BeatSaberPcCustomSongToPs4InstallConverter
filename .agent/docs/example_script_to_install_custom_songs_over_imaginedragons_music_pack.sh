#!/bin/bash
# Full custom song installation over Imagine Dragons music pack using pipeline automation
#
# This script deploys each of the 12 Imagine Dragons pack songs using the
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

echo "=== Deploying Imagine Dragons pack songs (full orchestration) ==="

# Song 1: Bad Liar
echo "Deploying Bad Liar..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target BadLiar     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Bad Liar"; exit 1; fi
echo "  Bad Liar deployed successfully"


# Song 2: Believer
echo "Deploying Believer..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target Believer     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Believer"; exit 1; fi
echo "  Believer deployed successfully"


# Song 3: Bones
echo "Deploying Bones..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target Bones     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Bones"; exit 1; fi
echo "  Bones deployed successfully"


# Song 4: Digital
echo "Deploying Digital..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target Digital     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Digital"; exit 1; fi
echo "  Digital deployed successfully"


# Song 5: Enemy
echo "Deploying Enemy..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target Enemy     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Enemy"; exit 1; fi
echo "  Enemy deployed successfully"


# Song 6: It's Time
echo "Deploying It's Time..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target ItsTime     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed It's Time"; exit 1; fi
echo "  It's Time deployed successfully"


# Song 7: Machine
echo "Deploying Machine..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_7     --target Machine     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Machine"; exit 1; fi
echo "  Machine deployed successfully"


# Song 8: Natural
echo "Deploying Natural..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_8     --target Natural     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Natural"; exit 1; fi
echo "  Natural deployed successfully"


# Song 9: Radioactive
echo "Deploying Radioactive..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_9     --target Radioactive     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Radioactive"; exit 1; fi
echo "  Radioactive deployed successfully"


# Song 10: Thunder
echo "Deploying Thunder..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_10     --target Thunder     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Thunder"; exit 1; fi
echo "  Thunder deployed successfully"


# Song 11: Warriors
echo "Deploying Warriors..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_11     --target Warriors     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Warriors"; exit 1; fi
echo "  Warriors deployed successfully"


# Song 12: Whatever It Takes
echo "Deploying Whatever It Takes..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_12     --target WhateverItTakes     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Whatever It Takes"; exit 1; fi
echo "  Whatever It Takes deployed successfully"


echo ""
echo "=== All 12 Imagine Dragons pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
