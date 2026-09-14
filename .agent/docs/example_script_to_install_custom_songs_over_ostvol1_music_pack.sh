#!/bin/bash
# Full custom song installation over Soundtrack Vol. 1 music pack using pipeline automation
#
# This script deploys each of the 10 Soundtrack Vol. 1 pack songs using the
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

echo "=== Deploying Soundtrack Vol. 1 pack songs (full orchestration) ==="

# Song 1: $100 Bills
echo "Deploying $100 Bills..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target 100Bills     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed $100 Bills"; exit 1; fi
echo "  $100 Bills deployed successfully"


# Song 2: Balearic Pumping
echo "Deploying Balearic Pumping..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target BalearicPumping     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Balearic Pumping"; exit 1; fi
echo "  Balearic Pumping deployed successfully"


# Song 3: Beat Saber
echo "Deploying Beat Saber..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target BeatSaber     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Beat Saber"; exit 1; fi
echo "  Beat Saber deployed successfully"


# Song 4: Breezer
echo "Deploying Breezer..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target Breezer     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Breezer"; exit 1; fi
echo "  Breezer deployed successfully"


# Song 5: Commercial Pumping
echo "Deploying Commercial Pumping..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target CommercialPumping     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Commercial Pumping"; exit 1; fi
echo "  Commercial Pumping deployed successfully"


# Song 6: Country Rounds
echo "Deploying Country Rounds..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target CountryRounds     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Country Rounds"; exit 1; fi
echo "  Country Rounds deployed successfully"


# Song 7: Escape
echo "Deploying Escape..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_7     --target Escape     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Escape"; exit 1; fi
echo "  Escape deployed successfully"


# Song 8: Legend
echo "Deploying Legend..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_8     --target Legend     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Legend"; exit 1; fi
echo "  Legend deployed successfully"


# Song 9: Lvl Insane
echo "Deploying Lvl Insane..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_9     --target LvlInsane     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Lvl Insane"; exit 1; fi
echo "  Lvl Insane deployed successfully"


# Song 10: Turn Me On
echo "Deploying Turn Me On..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_10     --target TurnMeOn     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Turn Me On"; exit 1; fi
echo "  Turn Me On deployed successfully"


echo ""
echo "=== All 10 Soundtrack Vol. 1 pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
