#!/bin/bash
# Full custom song installation over Lizzo music pack using pipeline automation

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
# This script deploys each of the 9 Lizzo pack songs using the
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
echo "Review the PS4 state above. If it is NOT what you expect (e.g. you"
echo "do not want to proceed from this state), press Ctrl+C to abort."
echo "Otherwise press Enter to continue with the deployment..."
read -r _
echo ""

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
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 25411     --target GoodAsHell     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Good As Hell"; exit 1; fi
echo "  Good As Hell → Do You Wanna Taste It deployed successfully"

# Song 6: Juice → One More (SG Lewis feat. Nile Rodgers)
echo "Deploying Juice → One More (SG Lewis feat. Nile Rodgers)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 27140     --target Juice     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Juice"; exit 1; fi
echo "  Juice → One More deployed successfully"

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