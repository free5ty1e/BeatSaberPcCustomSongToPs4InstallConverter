#!/bin/bash
# Full custom song installation over Metallica music pack using pipeline automation
#
# This script deploys each of the 17 Metallica pack songs using the
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

echo "=== Deploying Metallica pack songs (full orchestration) ==="

# Song 1: Atlas, Rise!
echo "Deploying Atlas, Rise!..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target AtlasRise     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Atlas, Rise!"; exit 1; fi
echo "  Atlas, Rise! deployed successfully"


# Song 2: Battery
echo "Deploying Battery..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target Battery     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Battery"; exit 1; fi
echo "  Battery deployed successfully"


# Song 3: Blackened
echo "Deploying Blackened..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target Blackened     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Blackened"; exit 1; fi
echo "  Blackened deployed successfully"


# Song 4: Creeping Death
echo "Deploying Creeping Death..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target CreepingDeath     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Creeping Death"; exit 1; fi
echo "  Creeping Death deployed successfully"


# Song 5: Enter Sandman
echo "Deploying Enter Sandman..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target EnterSandman     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Enter Sandman"; exit 1; fi
echo "  Enter Sandman deployed successfully"


# Song 6: Fade to Black
echo "Deploying Fade to Black..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target FadeToBlack     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Fade to Black"; exit 1; fi
echo "  Fade to Black deployed successfully"


# Song 7: For Whom the Bell Tolls
echo "Deploying For Whom the Bell Tolls..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_7     --target ForWhomTheBellTolls     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed For Whom the Bell Tolls"; exit 1; fi
echo "  For Whom the Bell Tolls deployed successfully"


# Song 8: Fuel
echo "Deploying Fuel..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_8     --target Fuel     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Fuel"; exit 1; fi
echo "  Fuel deployed successfully"


# Song 9: Hit the Lights
echo "Deploying Hit the Lights..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_9     --target HitTheLights     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Hit the Lights"; exit 1; fi
echo "  Hit the Lights deployed successfully"


# Song 10: King Nothing
echo "Deploying King Nothing..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_10     --target KingNothing     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed King Nothing"; exit 1; fi
echo "  King Nothing deployed successfully"


# Song 11: Lux Æterna
echo "Deploying Lux Æterna..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_11     --target LuxAeterna     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Lux Æterna"; exit 1; fi
echo "  Lux Æterna deployed successfully"


# Song 12: Master of Puppets
echo "Deploying Master of Puppets..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_12     --target MasterOfPuppets     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Master of Puppets"; exit 1; fi
echo "  Master of Puppets deployed successfully"


# Song 13: Nothing Else Matters
echo "Deploying Nothing Else Matters..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_13     --target NothingElseMatters     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Nothing Else Matters"; exit 1; fi
echo "  Nothing Else Matters deployed successfully"


# Song 14: One
echo "Deploying One..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_14     --target One     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed One"; exit 1; fi
echo "  One deployed successfully"


# Song 15: Sad But True
echo "Deploying Sad But True..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_15     --target SadButTrue     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Sad But True"; exit 1; fi
echo "  Sad But True deployed successfully"


# Song 16: Seek & Destroy
echo "Deploying Seek & Destroy..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_16     --target SeekAndDestroy     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Seek & Destroy"; exit 1; fi
echo "  Seek & Destroy deployed successfully"


# Song 17: The Unforgiven
echo "Deploying The Unforgiven..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_17     --target TheUnforgiven     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed The Unforgiven"; exit 1; fi
echo "  The Unforgiven deployed successfully"


echo ""
echo "=== All 17 Metallica pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
