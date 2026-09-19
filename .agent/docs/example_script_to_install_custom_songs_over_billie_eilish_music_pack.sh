#!/bin/bash
# Full custom song installation over Billie Eilish music pack using pipeline automation

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
# Requires plugin v0.8043+. Boot shows "BSD Plugin enabled N/3 feature flags ON" (v0.8044+).
#
# 🔧 NEW: Clear Target Song (--clear-target-song)
# Revert a single custom song slot back to its stock state WITHOUT a full PS4 clean slate:
#   python3 tools/full_custom_song_pipeline.py --clear-target-song <SLOT_NAME>
# This removes: custom song bundle, redirect entry, song/artist metadata, deploys updated configs.


#
# This script deploys each of the 10 Billie Eilish pack songs using the
# per-song pipeline with --deploy-full flag. Each command is complete
# and self-contained - it downloads the custom song from BeatSaver,
# converts to V3.2.0, generates all 4 modes, deploys the song bundle,
# resolves the song's DLC pack and deploys ONLY that one pack + song,
# builds/deploys the plugin + plugins.ini entry + features.json,
# regenerates redirects.json scoped to that song, and runs post-deploy
# validation. All in ONE command.

cd /workspace/beat_saber_deluxe

# Optional: Clean PS4 for a fresh clean-slate state
# Uncomment the next line if you want to start from a completely clean PS4
# python3 /workspace/backup-beat-saber-deluxe-files.py backup --clean-ps4

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

echo "=== Deploying Billie Eilish pack songs (full orchestration) ==="

# Song 1: all the good girls go to hell → Mirror (Ado)
echo "Deploying all the good girls go to hell → Mirror (Ado)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 4a901     --target AllTheGoodGirlsGoToHell     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed all the good girls go to hell"; exit 1; fi
echo "  all the good girls go to hell → Mirror deployed successfully"

# Song 2: bad guy → Odo (Ado)
echo "Deploying bad guy → Odo (Ado)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1dbb9     --target BadGuy     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed bad guy"; exit 1; fi
echo "  bad guy → Odo deployed successfully"

# Song 3: bellyache → ATTITUDE (IVE)
echo "Deploying bellyache → ATTITUDE (IVE)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 44218     --target Bellyache     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed bellyache"; exit 1; fi
echo "  bellyache → ATTITUDE deployed successfully"

# Song 4: bury a friend → Baddie (IVE)
echo "Deploying bury a friend → Baddie (IVE)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 36ab4     --target BuryAFriend     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed bury a friend"; exit 1; fi
echo "  bury a friend → Baddie deployed successfully"

# Song 5: happier than ever → Cosmic (Red Velvet)
echo "Deploying happier than ever → Cosmic (Red Velvet)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 3e192     --target HappierThanEver     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed happier than ever"; exit 1; fi
echo "  happier than ever → Cosmic deployed successfully"

# Song 6: nda → Duvet (Bôa — Shiki Miyoshino cover)
echo "Deploying nda → Duvet (Bôa — Shiki Miyoshino cover)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 22c4e     --target NDA     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed nda"; exit 1; fi
echo "  nda → Duvet deployed successfully"

# Song 7: therefore i am → Who's Laughing Now (Ava Max)
echo "Deploying therefore i am → Who's Laughing Now (Ava Max)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song f91e     --target ThereforeIAm     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed therefore i am"; exit 1; fi
echo "  therefore i am → Who's Laughing Now deployed successfully"

# Song 8: 2 be loved (am i ready) → Yes I'm A Mess (AJR)
echo "Deploying 2 be loved (am i ready) → Yes I'm A Mess (AJR)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 35ca9     --target 2BeLoved     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed 2 be loved"; exit 1; fi
echo "  2 be loved → Yes I'm A Mess deployed successfully"

# Song 9: about damn time → The Middle (Jimmy Eat World)
echo "Deploying about damn time → The Middle (Jimmy Eat World)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 27a13     --target AboutDamnTime     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed about damn time"; exit 1; fi
echo "  about damn time → The Middle deployed successfully"

# Song 10: cuz i love you → Bring It On (Giga-P)
echo "Deploying cuz i love you → Bring It On (Giga-P)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 2475     --target CuzILoveYou     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed cuz i love you"; exit 1; fi
echo "  cuz i love you → Bring It On deployed successfully"

echo ""
echo "=== All 10 Billie Eilish pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="