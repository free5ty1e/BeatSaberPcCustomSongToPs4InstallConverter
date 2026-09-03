#!/bin/bash
# Full custom song installation over Camelia (Chromeo) music pack using pipeline automation

cd /workspace/beat_saber_deluxe

echo "=== Deploying Camelia (Chromeo) pack songs ==="

# Song 1: Crystallized → Sexy Socialite (Chromeo)
echo "Deploying Crystallized → Sexy Socialite (Chromeo)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 6f1f     --target Crystallized     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Crystallized"; exit 1; fi
echo "  Crystallized → Sexy Socialite deployed successfully"

# Song 2: Cyclehit → Jealous (I Ain't With It) (Chromeo)
echo "Deploying Cyclehit → Jealous (I Ain't With It) (Chromeo)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 111fd     --target Cyclehit     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Cyclehit"; exit 1; fi
echo "  Cyclehit → Jealous deployed successfully"

# Song 3: Exit Earth → 'Roni Got Me Stressed Out (Chromeo)
echo "Deploying Exit Earth → 'Roni Got Me Stressed Out (Chromeo)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 115ba     --target ExitEarth     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Exit Earth"; exit 1; fi
echo "  Exit Earth → 'Roni Got Me Stressed Out deployed successfully"

# Song 4: Ghost → Green Light (Chromeo Remix) (Lorde, Chromeo)
echo "Deploying Ghost → Green Light (Chromeo Remix) (Lorde, Chromeo)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 37d5     --target Ghost     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Ghost"; exit 1; fi
echo "  Ghost → Green Light (Chromeo Remix) deployed successfully"

# Song 5: Lightsetup → 1999 (Charli XCX & Troye Sivan)
echo "Deploying Lightsetup → 1999 (Charli XCX & Troye Sivan)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 5352     --target Lightsetup     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Lightsetup"; exit 1; fi
echo "  Lightsetup → 1999 deployed successfully"

# Song 6: Whatcat → FANCY (TWICE)
echo "Deploying Whatcat → FANCY (TWICE)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 47f3     --target Whatcat     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Whatcat"; exit 1; fi
echo "  Whatcat → FANCY deployed successfully"

echo ""
echo "=== All 6 Camelia pack songs deployed ==="
echo ""
echo "=== Running consolidated pack deploy ==="
python3 development/scripts/build_deploy_all38.py

echo ""
echo "=== Deployment complete ==="