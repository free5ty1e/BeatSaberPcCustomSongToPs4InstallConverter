#!/bin/bash
# Full custom song installation over Rolling Stones music pack using pipeline automation

cd /workspace/beat_saber_deluxe

echo "=== Deploying Rolling Stones pack songs ==="

# Song 1: Angry
echo "Deploying Angry (Pegboard Nerds)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song angry     --target Angry     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Angry"; exit 1; fi
echo "  Angry deployed successfully"

# Song 2: Bite My Head Off
echo "Deploying Bite My Head Off (Gareth Coker)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song bitemyheadoff     --target BiteMyHeadOff     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Bite My Head Off"; exit 1; fi
echo "  Bite My Head Off deployed successfully"

# Song 3: Spicy (aespa)
echo "Deploying Spicy (aespa)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song cantyouhearmeknocking     --target CantYouHearMeKnocking     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Spicy"; exit 1; fi
echo "  Spicy deployed successfully"

# Song 4: Yes I'm A Mess (AJR)
echo "Deploying Yes I'm A Mess (AJR)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song gimmeshelter     --target GimmeShelter     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Yes I'm A Mess"; exit 1; fi
echo "  Yes I'm A Mess deployed successfully"

# Song 5: Dreams Come True (aespa)
echo "Deploying Dreams Come True (aespa)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song satisfaction     --target Satisfaction     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Dreams Come True"; exit 1; fi
echo "  Dreams Come True deployed successfully"

# Song 6: Take Me to the Beach (Imagine Dragons)
echo "Deploying Take Me to the Beach (Imagine Dragons)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song lbythesword     --target LiveByTheSword     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Take Me to the Beach"; exit 1; fi
echo "  Take Me to the Beach deployed successfully"

# Song 7: Powersnake (Brothers of Metal)
echo "Deploying Powersnake (Brothers of Metal)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song messitup     --target MessItUp     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Powersnake"; exit 1; fi
echo "  Powersnake deployed successfully"

# Song 8: Time Lapse (TheFatRat)
echo "Deploying Time Lapse (TheFatRat)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song paintitblack     --target PaintItBlack     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Time Lapse"; exit 1; fi
echo "  Time Lapse deployed successfully"

# Song 9: Venom of Venus (Powerwolf)
echo "Deploying Venom of Venus (Powerwolf)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song sugarsoaker     --target SugarSoaker     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Venom of Venus"; exit 1; fi
echo "  Venom of Venus deployed successfully"

# Song 10: LIT (Polyphia)
echo "Deploying LIT (Polyphia)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song sympathyforthedevil     --target SympathyForTheDevil     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed LIT"; exit 1; fi
echo "  LIT deployed successfully"

# Song 11: Whole Wide World (REZZ/Tare)
echo "Deploying Whole Wide World (REZZ/Tare)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song wholewideworld     --target WholeWideWorld     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Whole Wide World"; exit 1; fi
echo "  Whole Wide World deployed successfully"

echo ""
echo "=== All 11 Rolling Stones pack songs deployed ==="
echo ""
echo "=== Running consolidated pack deploy ==="
python3 development/scripts/build_deploy_all38.py

echo ""
echo "=== Deployment complete ==="
