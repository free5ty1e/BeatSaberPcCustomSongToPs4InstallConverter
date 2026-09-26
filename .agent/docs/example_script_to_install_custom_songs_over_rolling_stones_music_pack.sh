#!/bin/bash
# Full custom song installation over Rolling Stones music pack using pipeline automation

# 
# ⚠️ NEW: Partial Pack Deployment Safety (v0.5334+)
#
# Problem: When deploying custom songs one at a time, the pack bundle previously
# added extra mode buttons (OneSaber, NoArrows, 90Degree) for ALL songs in the
# pack — even unmodified stock songs. Selecting a stock song and trying to play
# a non-Standard mode would crash the game.
#
# Solution (automatic in --deploy-full):
# 1. Surgical pack bundle patching: The pipeline now builds the pack bundle with
#    extra modes ONLY for the custom song(s) being deployed. Stock songs in the
#    same pack keep only Standard mode.
# 2. Runtime feature flag enable_beatmap_mode_mapping (in features.json): Gates
#    visibility of extra mode sets in the mode selector UI.
#    - OFF (safe default for partial deploys): All songs show only Standard mode.
#    - ON (when pack is complete): Custom songs show all 4 modes; stock songs show
#      only Standard.
#
# Recommended workflow for partial pack deploys:
#   # Option A: Keep feature flag OFF until pack is complete (safest)
#   python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_beatmap_mode_mapping=false
#   # ... deploy songs one at a time ...
#   python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_beatmap_mode_mapping=true
#
#   # Option B: Let automatic surgical patching handle it (default in v0.5334+)
#   # Each --deploy-full only adds extra modes for THAT song in the pack bundle
#   python3 tools/full_custom_song_pipeline.py --download-beat-saver-song <MAP_ID> --target <SLOT> --pcm16 --no-pad --convert-to-v3 --deploy-full
#
#
# 🔌 Global Plugin Kill Switch (enable_plugin)
# Disable the ENTIRE plugin without editing plugins.ini or clearing the PS4 —
# the game plays 100% official songs on the next boot:
#   python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_plugin=false
# Re-enable your custom songs:
#   python3 tools/full_custom_song_pipeline.py --features-only --set-feature enable_plugin=true
# Takes effect on next game boot (features.json is read at plugin startup).
# Requires plugin v0.8043+. Boot shows ONE combined toast: "BS Deluxe v<ver> (ON) ... (N/3 features ON)" — or "(OFF) ... (official songs only)" when disabled (v0.8045+).
#
# 🔧 NEW: Clear Target Song (--clear-target-song)
# Revert a single custom song slot back to its stock state WITHOUT a full PS4 clean slate:
#   python3 tools/full_custom_song_pipeline.py --clear-target-song <SLOT_NAME>
# This removes: custom song bundle, redirect entry, song/artist metadata, deploys updated configs.


#
# This script deploys each of the 11 Rolling Stones pack songs using the
# per-song pipeline with --deploy-full flag. Each command is complete
# and self-contained - it downloads the custom song from BeatSaver,
# converts to V3.2.0, generates all 4 modes, deploys the song bundle,
# resolves the song's DLC pack and deploys ONLY that one pack + song,
# builds/deploys the plugin + plugins.ini entry + features.json,
# regenerates redirects.json scoped to that song, and runs post-deploy
# validation. All in ONE command.

# Optional: Clean PS4 for a fresh clean-slate state
# Uncomment the next line if you want to start from a completely clean PS4
# python3 /workspace/backup-beat-saber-deluxe-files.py backup --clean-ps4

cd /workspace/beat_saber_deluxe

echo ""
echo "=============================================================="
echo "PRE-DEPLOY CHECK — Current Beat Saber Deluxe state on PS4"
echo "=============================================================="
python3 /workspace/beat_saber_deluxe/development/scripts/ps4_state.py
echo ""
# --no-prompt: skip the interactive confirmation so chained pack scripts
# can run in series without babysitting (e.g. script1.sh --no-prompt &&
# script2.sh --no-prompt && ...). Default (no flag) keeps the prompt.
NO_PROMPT=0
for arg in "$@"; do
    if [ "$arg" = "--no-prompt" ]; then NO_PROMPT=1; fi
done
if [ "$NO_PROMPT" -eq 1 ]; then
    echo "--no-prompt: skipping confirmation, continuing in 3s..."
    sleep 3
else
    echo "Review the PS4 state above. If it is NOT what you expect (e.g. you"
    echo "do not want to proceed from this state), press Ctrl+C to abort."
    echo "Otherwise press Enter to continue with the deployment..."
    read -r _
fi
echo ""

echo "=== Deploying Rolling Stones pack songs (full orchestration) ==="

# Song 1: Angry → Rhythm Is A Dancer (Pegboard Nerds)
echo "Deploying Angry → Rhythm Is A Dancer (Pegboard Nerds)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song c213     --target Angry     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Angry"; exit 1; fi
echo "  Angry → Rhythm Is A Dancer deployed successfully"

# Song 2: Bite My Head Off → Escaping the Ruins (Gareth Coker)
echo "Deploying Bite My Head Off → Escaping the Ruins (Gareth Coker)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1fccd     --target BiteMyHeadOff     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Bite My Head Off"; exit 1; fi
echo "  Bite My Head Off → Escaping the Ruins deployed successfully"

# Song 3: Can't You Hear Me Knocking → Spicy (aespa)
echo "Deploying Can't You Hear Me Knocking → Spicy (aespa)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 32c7a     --target CantYouHearMeKnocking     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Spicy"; exit 1; fi
echo "  Can't You Hear Me Knocking → Spicy deployed successfully"

# Song 4: Gimme Shelter → Yes I'm A Mess (AJR)
echo "Deploying Gimme Shelter → Yes I'm A Mess (AJR)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 35ca9     --target GimmeShelter     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Yes I'm A Mess"; exit 1; fi
echo "  Gimme Shelter → Yes I'm A Mess deployed successfully"

# Song 5: Satisfaction → Dreams Come True (aespa)
echo "Deploying Satisfaction → Dreams Come True (aespa)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 21a3f     --target ICantGetNoSatisfaction     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Dreams Come True"; exit 1; fi
echo "  Satisfaction → Dreams Come True deployed successfully"

# Song 6: Live by the Sword → Take Me to the Beach (Imagine Dragons feat. Ado)
echo "Deploying Live by the Sword → Take Me to the Beach (Imagine Dragons feat. Ado)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 42a0a     --target LiveByTheSword     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Take Me to the Beach"; exit 1; fi
echo "  Live by the Sword → Take Me to the Beach deployed successfully"

# Song 7: Mess it Up → Powersnake (Brothers of Metal)
echo "Deploying Mess it Up → Powersnake (Brothers of Metal)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 15db5     --target MessItUp     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Powersnake"; exit 1; fi
echo "  Mess it Up → Powersnake deployed successfully"

# Song 8: Paint It Black → Time Lapse (TheFatRat)
echo "Deploying Paint It Black → Time Lapse (TheFatRat)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song a909     --target PaintItBlack     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Time Lapse"; exit 1; fi
echo "  Paint It Black → Time Lapse deployed successfully"

# Song 9: Sympathy For The Devil → LIT (Polyphia)
echo "Deploying Sympathy For The Devil → LIT (Polyphia)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1b457     --target SympathyForTheDevil     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed LIT"; exit 1; fi
echo "  Sympathy For The Devil → LIT deployed successfully"

# Song 10: Whole Wide World → VOLUPTE (Tare)
echo "Deploying Whole Wide World → VOLUPTE (Tare)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song a692     --target WholeWideWorld     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Whole Wide World"; exit 1; fi
echo "  Whole Wide World → VOLUPTE deployed successfully"

echo ""
# Song 11: Start Me Up → Wake Me Up (Avicii)
echo "Deploying Start Me Up → Wake Me Up (Avicii)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 437d     --target StartMeUp     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Start Me Up"; exit 1; fi
echo "  Start Me Up → Wake Me Up deployed successfully"

echo ""
echo "=== All 11 Rolling Stones pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="