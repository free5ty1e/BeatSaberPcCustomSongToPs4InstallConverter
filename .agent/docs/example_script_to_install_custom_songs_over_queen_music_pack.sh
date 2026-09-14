#!/bin/bash
# Full custom song installation over Queen music pack using pipeline automation
#
# This script deploys each of the 11 Queen pack songs using the
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

echo "=== Deploying Queen pack songs (full orchestration) ==="

# Song 1: Another One Bites The Dust
echo "Deploying Another One Bites The Dust..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_1     --target AnotherOneBitesTheDust     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Another One Bites The Dust"; exit 1; fi
echo "  Another One Bites The Dust deployed successfully"


# Song 2: Bohemian Rhapsody
echo "Deploying Bohemian Rhapsody..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_2     --target BohemianRhapsody     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Bohemian Rhapsody"; exit 1; fi
echo "  Bohemian Rhapsody deployed successfully"


# Song 3: Crazy Little Thing Called Love
echo "Deploying Crazy Little Thing Called Love..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_3     --target CrazyLittleThingCalledLove     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Crazy Little Thing Called Love"; exit 1; fi
echo "  Crazy Little Thing Called Love deployed successfully"


# Song 4: Don't Stop Me Now
echo "Deploying Don't Stop Me Now..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_4     --target DontStopMeNow     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Don't Stop Me Now"; exit 1; fi
echo "  Don't Stop Me Now deployed successfully"


# Song 5: I Want It All
echo "Deploying I Want It All..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_5     --target IWantItAll     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed I Want It All"; exit 1; fi
echo "  I Want It All deployed successfully"


# Song 6: Killer Queen
echo "Deploying Killer Queen..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_6     --target KillerQueen     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Killer Queen"; exit 1; fi
echo "  Killer Queen deployed successfully"


# Song 7: One Vision
echo "Deploying One Vision..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_7     --target OneVision     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed One Vision"; exit 1; fi
echo "  One Vision deployed successfully"


# Song 8: Somebody To Love
echo "Deploying Somebody To Love..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_8     --target SomebodyToLove     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Somebody To Love"; exit 1; fi
echo "  Somebody To Love deployed successfully"


# Song 9: Stone Cold Crazy
echo "Deploying Stone Cold Crazy..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_9     --target StoneColdCrazy     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Stone Cold Crazy"; exit 1; fi
echo "  Stone Cold Crazy deployed successfully"


# Song 10: We Are The Champions
echo "Deploying We Are The Champions..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_10     --target WeAreTheChampions     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed We Are The Champions"; exit 1; fi
echo "  We Are The Champions deployed successfully"


# Song 11: We Will Rock You
echo "Deploying We Will Rock You..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song REPLACE_MAP_ID_11     --target WeWillRockYou     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed We Will Rock You"; exit 1; fi
echo "  We Will Rock You deployed successfully"


echo ""
echo "=== All 11 Queen pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="
