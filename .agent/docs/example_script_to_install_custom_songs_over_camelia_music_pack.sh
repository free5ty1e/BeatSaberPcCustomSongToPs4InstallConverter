#!/bin/bash
# Full custom song installation over Camelia (Chromeo) music pack using pipeline automation
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
# 🔧 NEW: Clear Target Song (--clear-target-song)
# Revert a single custom song slot back to its stock state WITHOUT a full PS4 clean slate:
#   python3 tools/full_custom_song_pipeline.py --clear-target-song <SLOT_NAME>
# This removes: custom song bundle, redirect entry, song/artist metadata, deploys updated configs.
#
#
# This script deploys each of the 6 Camelia pack songs using the
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