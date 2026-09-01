#!/bin/bash
# Full custom song installation over Billie Eilish music pack using pipeline automation

cd /workspace/beat_saber_deluxe

echo "=== Deploying Billie Eilish pack songs ==="

# Song 1: all the good girls go to hell - Ado
echo "Deploying all the good girls go to hell (Ado)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song allthegoodgirlsgothell     --target AllTheGoodGirlsGoToHell     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed all the good girls go to hell"; exit 1; fi
echo "  all the good girls go to hell deployed successfully"

# Song 2: bad guy - Ado
echo "Deploying bad guy (Ado)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song badguy     --target BadGuy     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed bad guy"; exit 1; fi
echo "  bad guy deployed successfully"

# Song 3: bellyache - IVE
echo "Deploying bellyache (IVE)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song bellyache     --target Bellyache     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed bellyache"; exit 1; fi
echo "  bellyache deployed successfully"

# Song 4: bury a friend - IVE
echo "Deploying bury a friend (IVE)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song buryafriend     --target BuryAFriend     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed bury a friend"; exit 1; fi
echo "  bury a friend deployed successfully"

# Song 5: happier than ever - Red Velvet
echo "Deploying happier than ever (Red Velvet)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song happierthanever     --target HappierThanEver     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed happier than ever"; exit 1; fi
echo "  happier than ever deployed successfully"

# Song 6: nda - Bôa
echo "Deploying nda (Bôa)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song nda     --target NDA     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed nda"; exit 1; fi
echo "  nda deployed successfully"

# Song 7: therefore i am - Ava Max
echo "Deploying therefore i am (Ava Max)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song thereforeiam     --target ThereforeIAm     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed therefore i am"; exit 1; fi
echo "  therefore i am deployed successfully"

# Song 8: 2 be loved (am i ready) - AJR
echo "Deploying 2 be loved (am i ready) (AJR)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 2beloved     --target 2BeLoved     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed 2 be loved (am i ready)"; exit 1; fi
echo "  2 be loved (am i ready) deployed successfully"

# Song 9: about damn time - Jimmy Eat World
echo "Deploying about damn time (Jimmy Eat World)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song aboutdamntime     --target AboutDamnTime     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed about damn time"; exit 1; fi
echo "  about damn time deployed successfully"

# Song 10: cuz i love you - Giga-P
echo "Deploying cuz i love you (Giga-P)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song cuziloveyou     --target CuzILoveYou     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed cuz i love you"; exit 1; fi
echo "  cuz i love you deployed successfully"

echo ""
echo "=== All 10 Billie Eilish pack songs deployed ==="
echo ""
echo "=== Running consolidated pack deploy ==="
python3 development/scripts/build_deploy_all38.py

echo ""
echo "=== Deployment complete ==="
