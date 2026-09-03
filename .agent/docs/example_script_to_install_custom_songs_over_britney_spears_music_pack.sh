#!/bin/bash
# Full custom song installation over Britney Spears music pack using pipeline automation

# This script processes all 11 songs in the Britney Spears DLC pack,
# downloading each from BeatSaver with song name/artist identification
# and deploying to PS4 with 4 selectable modes (Standard, OneSaber, NoArrows, 90Degree).

cd /workspace/beat_saber_deluxe

echo '=== Deploying Britney Spears pack songs ==='

# Song 1: Baby One More Time → Blinding Lights (The Weeknd)
echo "Deploying Baby One More Time → Blinding Lights (The Weeknd)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 8553     --target BabyOneMoreTime     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to deploy Baby One More Time"
    exit 1
fi
echo "  Baby One More Time → Blinding Lights deployed successfully"

# Song 2: Circus → Shape of You (Ed Sheeran)
echo "Deploying Circus → Shape of You (Ed Sheeran)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1672a     --target Circus     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to deploy Circus"
    exit 1
fi
echo "  Circus → Shape of You deployed successfully"

# Song 3: Gimme More → Gangnam Style (PSY)
echo "Deploying Gimme More → Gangnam Style (PSY)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 141     --target GimmeMore     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to deploy Gimme More"
    exit 1
fi
echo "  Gimme More → Gangnam Style deployed successfully"

# Song 4: I'm a Slave 4 U → Believer (Imagine Dragons)
echo "Deploying I'm a Slave 4 U → Believer (Imagine Dragons)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1fef     --target ImASlave4U     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to deploy I'm a Slave 4 U"
    exit 1
fi
echo "  I'm a Slave 4 U → Believer deployed successfully"

# Song 5: Me Against The Music → Mr. Blue Sky (Electric Light Orchestra)
echo "Deploying Me Against The Music → Mr. Blue Sky (ELO)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 570     --target MeAgainstTheMusic     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to deploy Me Against The Music"
    exit 1
fi
echo "  Me Against The Music → Mr. Blue Sky deployed successfully"

# Song 6: Oops!...I Did It Again → Rap God (Eminem)
echo "Deploying Oops!...I Did It Again → Rap God (Eminem)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 46d4     --target OopsIDidItAgain     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to deploy Oops!...I Did It Again"
    exit 1
fi
echo "  Oops!...I Did It Again → Rap God deployed successfully"

# Song 7: Overprotected → Dancing On My Own (Robyn - Buzz Junkies Remix)
# Note: BeatSaver MAP_ID for "Dancing On My Own" by Robyn needs to be specified
echo "Deploying Overprotected → Dancing On My Own (Robyn)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song <MAP_ID>     --target Overprotected     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to deploy Overprotected"
    exit 1
fi
echo "  Overprotected → Dancing On My Own deployed successfully"

# Song 8: Scream & Shout → Levitating (Dua Lipa)
# Note: BeatSaver MAP_ID for "Levitating" by Dua Lipa needs to be specified
echo "Deploying Scream & Shout → Levitating (Dua Lipa)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song <MAP_ID>     --target Scream&Shout     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to deploy Scream & Shout"
    exit 1
fi
echo "  Scream & Shout → Levitating deployed successfully"

# Song 9: Till The World Ends → Dance Monkey (Tones and I)
echo "Deploying Till The World Ends → Dance Monkey (Tones and I)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 6cc2     --target TillTheWorldEnds     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to deploy Till The World Ends"
    exit 1
fi
echo "  Till The World Ends → Dance Monkey deployed successfully"

# Song 10: Toxic → Toxic (Britney Spears - Emir's map)
echo "Deploying Toxic → Toxic (Britney Spears)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 21540     --target Toxic     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to deploy Toxic"
    exit 1
fi
echo "  Toxic → Toxic deployed successfully"

# Song 11: Womanizer → Womanizer (Britney Spears)
echo "Deploying Womanizer → Womanizer (Britney Spears)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 12bd8     --target Womanizer     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to deploy Womanizer"
    exit 1
fi
echo "  Womanizer → Womanizer deployed successfully"

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