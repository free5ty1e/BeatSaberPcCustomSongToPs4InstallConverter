#!/bin/bash
# Full custom song installation over EDM music pack using pipeline automation
#
# This script deploys each of the 10 EDM pack songs using the
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

echo "=== Deploying EDM pack songs (full orchestration) ==="

# Song 1: Alone
echo "Deploying Alone..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target Alone     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Alone"; exit 1; fi
echo "  Alone deployed successfully"


# Song 2: Animals
echo "Deploying Animals..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target Animals     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Animals"; exit 1; fi
echo "  Animals deployed successfully"


# Song 3: Freestyler
echo "Deploying Freestyler..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target Freestyler     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Freestyler"; exit 1; fi
echo "  Freestyler deployed successfully"


# Song 4: Ghosts 'n' Stuff
echo "Deploying Ghosts 'n' Stuff..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target GhostsNStuff     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Ghosts 'n' Stuff"; exit 1; fi
echo "  Ghosts 'n' Stuff deployed successfully"


# Song 5: Icarus
echo "Deploying Icarus..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target Icarus     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Icarus"; exit 1; fi
echo "  Icarus deployed successfully"


# Song 6: Sandstorm
echo "Deploying Sandstorm..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target Sandstorm     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Sandstorm"; exit 1; fi
echo "  Sandstorm deployed successfully"


# Song 7: Stay The Night
echo "Deploying Stay The Night..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_7     --target StayTheNight     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Stay The Night"; exit 1; fi
echo "  Stay The Night deployed successfully"


# Song 8: The Rockafeller Skank
echo "Deploying The Rockafeller Skank..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_8     --target TheRockafellerSkank     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed The Rockafeller Skank"; exit 1; fi
echo "  The Rockafeller Skank deployed successfully"


# Song 9: Waiting All Night
echo "Deploying Waiting All Night..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_9     --target WaitingAllNight     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Waiting All Night"; exit 1; fi
echo "  Waiting All Night deployed successfully"


# Song 10: Witchcraft
echo "Deploying Witchcraft..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_10     --target Witchcraft     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Witchcraft"; exit 1; fi
echo "  Witchcraft deployed successfully"


echo ""
echo "=== All 10 EDM pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
