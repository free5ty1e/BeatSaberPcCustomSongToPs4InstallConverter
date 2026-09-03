#!/bin/bash
# Full custom song installation over Billie Eilish music pack using pipeline automation

cd /workspace/beat_saber_deluxe

echo "=== Deploying Billie Eilish pack songs ==="

# Song 1: all the good girls go to hell → Mirror (Ado)
echo "Deploying all the good girls go to hell → Mirror (Ado)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 4a901     --target AllTheGoodGirlsGoToHell     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed all the good girls go to hell"; exit 1; fi
echo "  all the good girls go to hell → Mirror deployed successfully"

# Song 2: bad guy → Odo (Ado)
echo "Deploying bad guy → Odo (Ado)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1dbb9     --target BadGuy     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed bad guy"; exit 1; fi
echo "  bad guy → Odo deployed successfully"

# Song 3: bellyache → ATTITUDE (IVE)
echo "Deploying bellyache → ATTITUDE (IVE)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 44218     --target Bellyache     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed bellyache"; exit 1; fi
echo "  bellyache → ATTITUDE deployed successfully"

# Song 4: bury a friend → Baddie (IVE)
echo "Deploying bury a friend → Baddie (IVE)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 36ab4     --target BuryAFriend     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed bury a friend"; exit 1; fi
echo "  bury a friend → Baddie deployed successfully"

# Song 5: happier than ever → Cosmic (Red Velvet)
echo "Deploying happier than ever → Cosmic (Red Velvet)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 3e192     --target HappierThanEver     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed happier than ever"; exit 1; fi
echo "  happier than ever → Cosmic deployed successfully"

# Song 6: nda → Duvet (Bôa)
echo "Deploying nda → Duvet (Bôa)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 4b107     --target NDA     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed nda"; exit 1; fi
echo "  nda → Duvet deployed successfully"

# Song 7: therefore i am → Who's Laughing Now (Ava Max)
echo "Deploying therefore i am → Who's Laughing Now (Ava Max)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song f91e     --target ThereforeIAm     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed therefore i am"; exit 1; fi
echo "  therefore i am → Who's Laughing Now deployed successfully"

# Song 8: 2 be loved (am i ready) → Yes I'm A Mess (AJR)
echo "Deploying 2 be loved (am i ready) → Yes I'm A Mess (AJR)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 35ca9     --target 2BeLoved     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed 2 be loved"; exit 1; fi
echo "  2 be loved → Yes I'm A Mess deployed successfully"

# Song 9: about damn time → The Middle (Jimmy Eat World)
echo "Deploying about damn time → The Middle (Jimmy Eat World)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 27a13     --target AboutDamnTime     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed about damn time"; exit 1; fi
echo "  about damn time → The Middle deployed successfully"

# Song 10: cuz i love you → Bring It On (Giga-P)
echo "Deploying cuz i love you → Bring It On (Giga-P)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 2475     --target CuzILoveYou     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed cuz i love you"; exit 1; fi
echo "  cuz i love you → Bring It On deployed successfully"

echo ""
echo "=== All 10 Billie Eilish pack songs deployed ==="
echo ""
echo "=== Running consolidated pack deploy ==="
python3 development/scripts/build_deploy_all38.py

echo ""
echo "=== Deployment complete ==="