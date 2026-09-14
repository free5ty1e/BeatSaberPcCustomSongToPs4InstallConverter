#!/bin/bash
# Full custom song installation over Monstercat music pack using pipeline automation
#
# This script deploys each of the 10 Monstercat pack songs using the
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

echo "=== Deploying Monstercat pack songs (full orchestration) ==="

# Song 1: Boundless
echo "Deploying Boundless..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target Boundless     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Boundless"; exit 1; fi
echo "  Boundless deployed successfully"


# Song 2: Emoji VIP
echo "Deploying Emoji VIP..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target EmojiVIP     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Emoji VIP"; exit 1; fi
echo "  Emoji VIP deployed successfully"


# Song 3: EPIC
echo "Deploying EPIC..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target Epic     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed EPIC"; exit 1; fi
echo "  EPIC deployed successfully"


# Song 4: Feeling Stronger
echo "Deploying Feeling Stronger..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target FeelingStronger     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Feeling Stronger"; exit 1; fi
echo "  Feeling Stronger deployed successfully"


# Song 5: Overkill
echo "Deploying Overkill..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target Overkill     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Overkill"; exit 1; fi
echo "  Overkill deployed successfully"


# Song 6: Rattlesnake
echo "Deploying Rattlesnake..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target Rattlesnake     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Rattlesnake"; exit 1; fi
echo "  Rattlesnake deployed successfully"


# Song 7: Stronger
echo "Deploying Stronger..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_7     --target Stronger     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Stronger"; exit 1; fi
echo "  Stronger deployed successfully"


# Song 8: This Time
echo "Deploying This Time..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_8     --target ThisTime     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed This Time"; exit 1; fi
echo "  This Time deployed successfully"


# Song 9: Till It's Over
echo "Deploying Till It's Over..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_9     --target TillItsOver     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Till It's Over"; exit 1; fi
echo "  Till It's Over deployed successfully"


# Song 10: We Won't Be Alone
echo "Deploying We Won't Be Alone..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_10     --target WeWontBeAlone     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed We Won't Be Alone"; exit 1; fi
echo "  We Won't Be Alone deployed successfully"


echo ""
echo "=== All 10 Monstercat pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
