#!/bin/bash
# Full custom song installation over Fall Out Boy music pack using pipeline automation
#
# This script deploys each of the 8 Fall Out Boy pack songs using the
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

echo "=== Deploying Fall Out Boy pack songs (full orchestration) ==="

# Song 1: Centuries
echo "Deploying Centuries..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target Centuries     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Centuries"; exit 1; fi
echo "  Centuries deployed successfully"


# Song 2: Dance, Dance
echo "Deploying Dance, Dance..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target DanceDance     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Dance, Dance"; exit 1; fi
echo "  Dance, Dance deployed successfully"


# Song 3: I Don't Care
echo "Deploying I Don't Care..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target IDontCare     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed I Don't Care"; exit 1; fi
echo "  I Don't Care deployed successfully"


# Song 4: Immortals
echo "Deploying Immortals..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target Immortals     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Immortals"; exit 1; fi
echo "  Immortals deployed successfully"


# Song 5: Irresistible
echo "Deploying Irresistible..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target Irresistible     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Irresistible"; exit 1; fi
echo "  Irresistible deployed successfully"


# Song 6: My Songs Know What You Did In The Dark
echo "Deploying My Songs Know What You Did In The Dark..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target MySongsKnow     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed My Songs Know What You Did In The Dark"; exit 1; fi
echo "  My Songs Know What You Did In The Dark deployed successfully"


# Song 7: This Ain't A Scene, It's An Arms Race
echo "Deploying This Ain't A Scene, It's An Arms Race..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_7     --target ThisAintAScene     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed This Ain't A Scene, It's An Arms Race"; exit 1; fi
echo "  This Ain't A Scene, It's An Arms Race deployed successfully"


# Song 8: Thnks fr th Mmrs
echo "Deploying Thnks fr th Mmrs..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_8     --target ThnksFrThMmrs     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Thnks fr th Mmrs"; exit 1; fi
echo "  Thnks fr th Mmrs deployed successfully"


echo ""
echo "=== All 8 Fall Out Boy pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
