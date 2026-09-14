#!/bin/bash
# Full custom song installation over Daft Punk music pack using pipeline automation
#
# This script deploys each of the 10 Daft Punk pack songs using the
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

echo "=== Deploying Daft Punk pack songs (full orchestration) ==="

# Song 1: Around The World
echo "Deploying Around The World..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target AroundTheWorld     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Around The World"; exit 1; fi
echo "  Around The World deployed successfully"


# Song 2: Around The World / Harder Better Faster Stronger
echo "Deploying Around The World / Harder Better Faster Stronger..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target AroundTheWorldHarderBetterFasterStronger     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Around The World / Harder Better Faster Stronger"; exit 1; fi
echo "  Around The World / Harder Better Faster Stronger deployed successfully"


# Song 3: Da Funk / Daftendirekt
echo "Deploying Da Funk / Daftendirekt..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target DaFunkDaftendirekt     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Da Funk / Daftendirekt"; exit 1; fi
echo "  Da Funk / Daftendirekt deployed successfully"


# Song 4: Get Lucky
echo "Deploying Get Lucky..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target GetLucky     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Get Lucky"; exit 1; fi
echo "  Get Lucky deployed successfully"


# Song 5: Harder, Better, Faster, Stronger
echo "Deploying Harder, Better, Faster, Stronger..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target HarderBetterFasterStronger     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Harder, Better, Faster, Stronger"; exit 1; fi
echo "  Harder, Better, Faster, Stronger deployed successfully"


# Song 6: Lose Yourself To Dance
echo "Deploying Lose Yourself To Dance..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target LoseYourselfToDance     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Lose Yourself To Dance"; exit 1; fi
echo "  Lose Yourself To Dance deployed successfully"


# Song 7: One More Time
echo "Deploying One More Time..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_7     --target OneMoreTime     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed One More Time"; exit 1; fi
echo "  One More Time deployed successfully"


# Song 8: Prime Time of Your Life
echo "Deploying Prime Time of Your Life..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_8     --target PrimeTimeOfYourLifeBrainwasherRollinAliveLive2007     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Prime Time of Your Life"; exit 1; fi
echo "  Prime Time of Your Life deployed successfully"


# Song 9: Technologic
echo "Deploying Technologic..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_9     --target Technologic     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Technologic"; exit 1; fi
echo "  Technologic deployed successfully"


# Song 10: Veridis Quo
echo "Deploying Veridis Quo..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_10     --target VeridisQuo     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Veridis Quo"; exit 1; fi
echo "  Veridis Quo deployed successfully"


echo ""
echo "=== All 10 Daft Punk pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
