#!/bin/bash
# Full custom song installation over Hip Hop music pack using pipeline automation
#
# This script deploys each of the 9 Hip Hop pack songs using the
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

echo "=== Deploying Hip Hop pack songs (full orchestration) ==="

# Song 1: All Eyez On Me
echo "Deploying All Eyez On Me..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target AllEyezOnMe     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed All Eyez On Me"; exit 1; fi
echo "  All Eyez On Me deployed successfully"


# Song 2: Anaconda
echo "Deploying Anaconda..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target Anaconda     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Anaconda"; exit 1; fi
echo "  Anaconda deployed successfully"


# Song 3: Gin and Juice
echo "Deploying Gin and Juice..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target GinAndJuice     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Gin and Juice"; exit 1; fi
echo "  Gin and Juice deployed successfully"


# Song 4: Godzilla
echo "Deploying Godzilla..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target Godzilla     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Godzilla"; exit 1; fi
echo "  Godzilla deployed successfully"


# Song 5: Hey Ya!
echo "Deploying Hey Ya!..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target HeyYA     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Hey Ya!"; exit 1; fi
echo "  Hey Ya! deployed successfully"


# Song 6: Hypnotize
echo "Deploying Hypnotize..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target Hypnotize     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Hypnotize"; exit 1; fi
echo "  Hypnotize deployed successfully"


# Song 7: Nuthin' But A "G" Thang
echo "Deploying Nuthin' But A "G" Thang..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_7     --target NuthinButAGThang     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Nuthin' But A "G" Thang"; exit 1; fi
echo "  Nuthin' But A "G" Thang deployed successfully"


# Song 8: The Message
echo "Deploying The Message..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_8     --target TheMessage     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed The Message"; exit 1; fi
echo "  The Message deployed successfully"


# Song 9: The Woo
echo "Deploying The Woo..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_9     --target TheWoo     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed The Woo"; exit 1; fi
echo "  The Woo deployed successfully"


echo ""
echo "=== All 9 Hip Hop pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
