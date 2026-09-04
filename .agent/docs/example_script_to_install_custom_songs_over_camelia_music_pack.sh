#!/bin/bash
# Full custom song installation over Camelia (Chromeo) music pack using pipeline automation
#
# This script deploys each of the 6 Camelia pack songs using the
# per-song pipeline with --deploy-full flag. Each command is complete
# and self-contained - it downloads the custom song from BeatSaver,
# converts to V3.2.0, generates all 4 modes, deploys the song bundle,
# builds/deploys pack mode bundles + merged catalog, regenerates
# redirects.json, and runs post-deploy validation. All in ONE command.

cd /workspace/beat_saber_deluxe

echo "=== Deploying Camelia (Chromeo) pack songs (full orchestration) ==="

# Song 1: Crystallized → Sexy Socialite (Chromeo)
echo "Deploying Crystallized → Sexy Socialite (Chromeo)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 6f1f     --target Crystallized     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Crystallized"; exit 1; fi
echo "  Crystallized → Sexy Socialite deployed successfully"

# Song 2: CycleHit → Jealous (I Ain't With It) (Chromeo)
echo "Deploying CycleHit → Jealous (I Ain't With It) (Chromeo)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 111fd     --target CycleHit     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed CycleHit"; exit 1; fi
echo "  CycleHit → Jealous deployed successfully"

# Song 3: ExitThisEarthsAtomosphere → 'Roni Got Me Stressed Out (Chromeo)
echo "Deploying ExitThisEarthsAtomosphere → 'Roni Got Me Stressed Out (Chromeo)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 115ba     --target ExitThisEarthsAtomosphere     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed ExitThisEarthsAtomosphere"; exit 1; fi
echo "  ExitThisEarthsAtomosphere → 'Roni Got Me Stressed Out deployed successfully"

# Song 4: Ghost → Green Light (Chromeo Remix) (Lorde, Chromeo)
echo "Deploying Ghost → Green Light (Chromeo Remix) (Lorde, Chromeo)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 37d5     --target Ghost     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Ghost"; exit 1; fi
echo "  Ghost → Green Light (Chromeo Remix) deployed successfully"

# Song 5: LightItUp → 1999 (Charli XCX & Troye Sivan)
echo "Deploying LightItUp → 1999 (Charli XCX & Troye Sivan)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 5352     --target LightItUp     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed LightItUp"; exit 1; fi
echo "  LightItUp → 1999 deployed successfully"

# Song 6: WhatTheCat → FANCY (TWICE)
echo "Deploying WhatTheCat → FANCY (TWICE)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 47f3     --target WhatTheCat     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed WhatTheCat"; exit 1; fi
echo "  WhatTheCat → FANCY deployed successfully"

echo ""
echo "=== All 6 Camelia pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="