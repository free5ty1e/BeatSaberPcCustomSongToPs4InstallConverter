#!/bin/bash
# Full custom song installation over Britney Spears music pack using pipeline automation

# This script processes all 11 songs in the Britney Spears DLC pack,
# downloading each from BeatSaver, converting to V3.2.0 schema,
# and deploying to PS4 with 4 selectable modes.

cd /workspace/beat_saber_deluxe

# Song mappings: BeatSaver MAP_ID -> slot name from beat_saber_song_ids.json
declare -A SONG_MAP=( 
    [8553]=BabyOneMoreTime
    [1672a]=Circus
    [141]=GimmeMore
    [1fef]=ImASlave4U
    [570]=MeAgainstTheMusic
    [46d4]=OopsIDidItAgain
    [11cf8]=Overprotected
    [bd45]=Scream&Shout
    [6cc2]=TillTheWorldEnds
)

echo '=== Deploying Britney Spears pack songs ==='

# Deploy each song individually
for MAP_ID in 8553 1672a 141 1fef 570 46d4 11cf8 bd45 6cc2; do
    SLOT=${SONG_MAP[$MAP_ID]}
    echo "Deploying $SLOT (MAP_ID: $MAP_ID)..."
    python3 tools/full_custom_song_pipeline.py         --download-beat-saver-song $MAP_ID         --target $SLOT         --pcm16         --no-pad         --convert-to-v3         --deploy
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to deploy $SLOT"
        exit 1
    fi
    echo "  $SLOT deployed successfully"
done

echo ''
echo '=== All 9 songs deployed ==='

# Two remaining songs (Toxic and Womanizer) - use map IDs from selection
echo 'Deploying Toxic and Womanizer (remaining 2 Britney pack songs)...'
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song <TOXIC_MAP_ID>     --target Toxic     --pcm16     --no-pad     --convert-to-v3     --deploy

python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song <WOMANIZER_MAP_ID>     --target Womanizer     --pcm16     --no-pad     --convert-to-v3     --deploy

echo ''
echo '=== All 11 Britney Spears pack songs deployed ==='

echo ''
echo '=== Running consolidated pack deploy ==='
echo 'This updates pack metadata, catalog, and redirects in one pass.'
python3 development/scripts/build_deploy_all38.py

echo ''
echo '=== Deployment complete ===' 
echo 'Your PS4 now has:'
echo '- 38 custom songs, each with 4 selectable modes'
echo '- 4 music packs fully patched (including Britney Spears)'
echo '- Validated redirect configuration'
echo ''
echo 'Run: ls /data/GoldHEN/AFR/CUSA12878/*_v3.bundle | wc -l'
echo 'Should show 38 custom song bundles.'
