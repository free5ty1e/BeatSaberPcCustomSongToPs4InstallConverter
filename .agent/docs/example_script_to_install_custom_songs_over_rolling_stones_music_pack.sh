#!/bin/bash
# Full custom song installation over Rolling Stones music pack using pipeline automation

cd /workspace/beat_saber_deluxe

echo "=== Deploying Rolling Stones pack songs ==="

# Song 1: Angry → Rhythm Is A Dancer (Pegboard Nerds)
echo "Deploying Angry → Rhythm Is A Dancer (Pegboard Nerds)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song c213     --target Angry     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Angry"; exit 1; fi
echo "  Angry → Rhythm Is A Dancer deployed successfully"

# Song 2: Bite My Head Off → Escaping the Ruins (MDK / Gareth Coker)
echo "Deploying Bite My Head Off → Escaping the Ruins (MDK / Gareth Coker)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 8c2a     --target BiteMyHeadOff     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Bite My Head Off"; exit 1; fi
echo "  Bite My Head Off → Escaping the Ruins deployed successfully"

# Song 3: Can't You Hear Me Knocking → Spicy (aespa)
echo "Deploying Can't You Hear Me Knocking → Spicy (aespa)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 32c7a     --target CantYouHearMeKnocking     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Spicy"; exit 1; fi
echo "  Can't You Hear Me Knocking → Spicy deployed successfully"

# Song 4: Gimme Shelter → Yes I'm A Mess (AJR)
echo "Deploying Gimme Shelter → Yes I'm A Mess (AJR)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 35ca9     --target GimmeShelter     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Yes I'm A Mess"; exit 1; fi
echo "  Gimme Shelter → Yes I'm A Mess deployed successfully"

# Song 5: Satisfaction → Dreams Come True (aespa)
echo "Deploying Satisfaction → Dreams Come True (aespa)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 21a3f     --target Satisfaction     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Dreams Come True"; exit 1; fi
echo "  Satisfaction → Dreams Come True deployed successfully"

# Song 6: Live by the Sword → Take Me to the Beach (Imagine Dragons feat. Ado)
echo "Deploying Live by the Sword → Take Me to the Beach (Imagine Dragons feat. Ado)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 42a0a     --target LiveByTheSword     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Take Me to the Beach"; exit 1; fi
echo "  Live by the Sword → Take Me to the Beach deployed successfully"

# Song 7: Mess it Up → Powersnake (Brothers of Metal)
echo "Deploying Mess it Up → Powersnake (Brothers of Metal)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 15db5     --target MessItUp     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Powersnake"; exit 1; fi
echo "  Mess it Up → Powersnake deployed successfully"

# Song 8: Paint It Black → Time Lapse (TheFatRat)
echo "Deploying Paint It Black → Time Lapse (TheFatRat)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song a909     --target PaintItBlack     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Time Lapse"; exit 1; fi
echo "  Paint It Black → Time Lapse deployed successfully"

# Song 9: Sugar Soaker → Venom of Venus (Powerwolf)
echo "Deploying Sugar Soaker → Venom of Venus (Powerwolf)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song b7aa     --target SugarSoaker     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Venom of Venus"; exit 1; fi
echo "  Sugar Soaker → Venom of Venus deployed successfully"

# Song 10: Sympathy For The Devil → LIT (Polyphia)
echo "Deploying Sympathy For The Devil → LIT (Polyphia)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1b457     --target SympathyForTheDevil     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed LIT"; exit 1; fi
echo "  Sympathy For The Devil → LIT deployed successfully"

# Song 11: Whole Wide World → VOLUPTE (Tare)
echo "Deploying Whole Wide World → VOLUPTE (Tare)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song a692     --target WholeWideWorld     --pcm16     --no-pad     --convert-to-v3     --deploy
if [ $? -ne 0 ]; then echo "ERROR: Failed Whole Wide World"; exit 1; fi
echo "  Whole Wide World → VOLUPTE deployed successfully"

echo ""
echo "=== All 11 Rolling Stones pack songs deployed ==="
echo ""
echo "=== Running consolidated pack deploy ==="
python3 development/scripts/build_deploy_all38.py

echo ""
echo "=== Deployment complete ==="