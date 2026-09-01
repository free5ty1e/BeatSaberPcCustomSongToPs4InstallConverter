#!/bin/bash
# Full custom song installation over Lizzo music pack using pipeline automation

cd /workspace/beat_saber_deluxe

echo "=== Deploying Lizzo pack songs ==="

# Song 1: 2 Be Loved (Am I Ready) - AJR
echo "Deploying 2 Be Loved (Am I Ready) (AJR)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 2beloved     --target 2BeLoved     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed 2 Be Loved"; exit 1; fi
echo "  2 Be Loved deployed successfully"

# Song 2: About Damn Time - Jimmy Eat World
echo "Deploying About Damn Time (Jimmy Eat World)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song aboutdamntime     --target AboutDamnTime     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed About Damn Time"; exit 1; fi
echo "  About Damn Time deployed successfully"

# Song 3: Cuz I Love You - Giga-P
echo "Deploying Cuz I Love You (Giga-P)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song cuziloveyou     --target CuzILoveYou     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Cuz I Love You"; exit 1; fi
echo "  Cuz I Love You deployed successfully"

# Song 4: Everybody's Gay - (G)I-DLE
echo "Deploying Everybody's Gay ((G)I-DLE)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song everybodysgay     --target EverybodysGay     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Everybody's Gay"; exit 1; fi
echo "  Everybody's Gay deployed successfully"

# Song 5: Good As Hell - Wig Wam
echo "Deploying Good As Hell (Wig Wam)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song goodashell     --target GoodAsHell     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Good As Hell"; exit 1; fi
echo "  Good As Hell deployed successfully"

# Song 6: Juice - Calvin Harris
echo "Deploying Juice (Calvin Harris)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song juice     --target Juice     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Juice"; exit 1; fi
echo "  Juice deployed successfully"

# Song 7: Tempo - Fox Stevenson
echo "Deploying Tempo (Fox Stevenson)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song tempo     --target Tempo     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Tempo"; exit 1; fi
echo "  Tempo deployed successfully"

# Song 8: Truth Hurts - DisasterTheory
echo "Deploying Truth Hurts (DisasterTheory)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song truthhurts     --target TruthHurts     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Truth Hurts"; exit 1; fi
echo "  Truth Hurts deployed successfully"

# Song 9: Worship - American Authors
echo "Deploying Worship (American Authors)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song worship     --target Worship     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Worship"; exit 1; fi
echo "  Worship deployed successfully"

echo ""
echo "=== All 9 Lizzo pack songs deployed ==="
echo ""
echo "=== Running consolidated pack deploy ==="
python3 development/scripts/build_deploy_all38.py

echo ""
echo "=== Deployment complete ==="
