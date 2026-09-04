#!/bin/bash
# Full custom song installation over Lizzo music pack using pipeline automation
#
# This script deploys each of the 9 Lizzo pack songs using the
# per-song pipeline with --deploy-full flag. Each command is complete
# and self-contained - it downloads the custom song from BeatSaver,
# converts to V3.2.0, generates all 4 modes, deploys the song bundle,
# builds/deploys pack mode bundles + merged catalog, regenerates
# redirects.json, and runs post-deploy validation. All in ONE command.

cd /workspace/beat_saber_deluxe

echo "=== Deploying Lizzo pack songs (full orchestration) ==="

# Song 1: 2 Be Loved → Yes I'm A Mess (AJR)
echo "Deploying 2 Be Loved → Yes I'm A Mess (AJR)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 35ca9     --target 2BeLoved     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed 2 Be Loved"; exit 1; fi
echo "  2 Be Loved → Yes I'm A Mess deployed successfully"

# Song 2: About Damn Time → The Middle (Jimmy Eat World)
echo "Deploying About Damn Time → The Middle (Jimmy Eat World)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 27a13     --target AboutDamnTime     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed About Damn Time"; exit 1; fi
echo "  About Damn Time → The Middle deployed successfully"

# Song 3: Cuz I Love You → Bring It On (Giga-P)
echo "Deploying Cuz I Love You → Bring It On (Giga-P)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 2475     --target CuzILoveYou     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Cuz I Love You"; exit 1; fi
echo "  Cuz I Love You → Bring It On deployed successfully"

# Song 4: Everybody's Gay → Queencard ((G)I-DLE)
echo "Deploying Everybody's Gay → Queencard ((G)I-DLE)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 40a53     --target EverybodysGay     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Everybody's Gay"; exit 1; fi
echo "  Everybody's Gay → Queencard deployed successfully"

# Song 5: Good As Hell → Do You Wanna Taste It (Wig Wam)
echo "Deploying Good As Hell → Do You Wanna Taste It (Wig Wam)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 212c5     --target GoodAsHell     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Good As Hell"; exit 1; fi
echo "  Good As Hell → Do You Wanna Taste It deployed successfully"

# Song 6: Juice → Blame (Calvin Harris feat. John Newman)
echo "Deploying Juice → Blame (Calvin Harris feat. John Newman)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 5758     --target Juice     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Juice"; exit 1; fi
echo "  Juice → Blame deployed successfully"

# Song 7: Tempo → Bruises (Fox Stevenson)
echo "Deploying Tempo → Bruises (Fox Stevenson)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song ae3c     --target Tempo     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Tempo"; exit 1; fi
echo "  Tempo → Bruises deployed successfully"

# Song 8: Truth Hurts → Genie In A Bottle (DisasterTheory)
echo "Deploying Truth Hurts → Genie In A Bottle (DisasterTheory)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 50a08     --target TruthHurts     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Truth Hurts"; exit 1; fi
echo "  Truth Hurts → Genie In A Bottle deployed successfully"

# Song 9: Worship → Best Day Of My Life (American Authors)
echo "Deploying Worship → Best Day Of My Life (American Authors)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 86e9     --target Worship     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Worship"; exit 1; fi
echo "  Worship → Best Day Of My Life deployed successfully"

echo ""
echo "=== All 9 Lizzo pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="