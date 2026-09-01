#!/bin/bash
# Full custom song installation over Camelia (Chromeo) music pack using pipeline automation

cd /workspace/beat_saber_deluxe

echo "=== Deploying Camelia (Chromeo) pack songs ==="

# Song 1: Crystallized
echo "Deploying Crystallized (Chromeo)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song crystallized     --target Crystallized     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Crystallized"; exit 1; fi
echo "  Crystallized deployed successfully"

# Song 2: Cycle Hit
echo "Deploying Cycle Hit (Chromeo)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song cyclehit     --target CycleHit     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Cycle Hit"; exit 1; fi
echo "  Cycle Hit deployed successfully"

# Song 3: EXiT This Earth's Atomosphere
echo "Deploying EXiT This Earth's Atomosphere (Chromeo)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song exitearth     --target ExitThisEarthsAtomosphere     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed EXiT This Earth's Atomosphere"; exit 1; fi
echo "  EXiT This Earth's Atomosphere deployed successfully"

# Song 4: Ghost
echo "Deploying Ghost (Chromeo)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song ghost     --target Ghost     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Ghost"; exit 1; fi
echo "  Ghost deployed successfully"

# Song 5: Light It Up
echo "Deploying Light It Up (Charli XCX & Troye Sivan)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song lightsetup     --target LightItUp     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Light It Up"; exit 1; fi
echo "  Light It Up deployed successfully"

# Song 6: WHAT THE CAT!?
echo "Deploying WHAT THE CAT!? (TWICE)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song whatcat     --target WhatTheCat     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed WHAT THE CAT!?"; exit 1; fi
echo "  WHAT THE CAT!? deployed successfully"

echo ""
echo "=== All 6 Camelia pack songs deployed ==="
echo ""
echo "=== Running consolidated pack deploy ==="
python3 development/scripts/build_deploy_all38.py

echo ""
echo "=== Deployment complete ==="
