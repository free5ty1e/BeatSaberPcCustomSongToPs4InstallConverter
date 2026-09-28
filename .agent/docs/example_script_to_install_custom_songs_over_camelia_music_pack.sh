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
#
# This script deploys each of the 6 Camelia pack songs using the
# per-song pipeline with --deploy-full flag (pipeline v0.5338+).
# Song selection rule: every song ships native Easy, Normal AND Hard
# difficulties from its mapper (Expert-only maps lock out lower-skilled
# players and do not qualify). Expert/Expert+ gaps are auto-filled by the
# pipeline from the map's own closest difficulty.
# Each command is complete
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

echo "=== Deploying Camelia (Chromeo) pack songs (full orchestration) ==="

# Song 1: Crystallized → Le Freak (Chic)
echo "Deploying Crystallized → Le Freak (Chic)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1760d     --target Crystallized     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Crystallized"; exit 1; fi
echo "  Crystallized → Le Freak (Chic) deployed successfully"

# Song 2: CycleHit → 24K Magic (Bruno Mars)
echo "Deploying CycleHit → 24K Magic (Bruno Mars)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 16726     --target CycleHit     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed CycleHit"; exit 1; fi
echo "  CycleHit → 24K Magic (Bruno Mars) deployed successfully"

# Song 3: ExitThisEarthsAtomosphere → Fireball (Pitbull feat. John Ryan)
echo "Deploying ExitThisEarthsAtomosphere → Fireball (Pitbull feat. John Ryan)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 9c05     --target ExitThisEarthsAtomosphere     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed ExitThisEarthsAtomosphere"; exit 1; fi
echo "  ExitThisEarthsAtomosphere → Fireball (Pitbull feat. John Ryan) deployed successfully"

# Song 4: Ghost → Around The World (Niklas Dee)
echo "Deploying Ghost → Around The World (Niklas Dee)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 40201     --target Ghost     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed Ghost"; exit 1; fi
echo "  Ghost → Around The World (Niklas Dee) deployed successfully"

# Song 5: LightItUp → Daft Punk Megamix 1 (Daft Punk)
echo "Deploying LightItUp → Daft Punk Megamix 1 (Daft Punk)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 242e9     --target LightItUp     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed LightItUp"; exit 1; fi
echo "  LightItUp → Daft Punk Megamix 1 (Daft Punk) deployed successfully"

# Song 6: WhatTheCat → Stayin' Alive (Bee Gees)
echo "Deploying WhatTheCat → Stayin' Alive (Bee Gees)..."
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 3cfe9     --target WhatTheCat     --pcm16     --no-pad     --convert-to-v3     --deploy-full
if [ $? -ne 0 ]; then echo "ERROR: Failed WhatTheCat"; exit 1; fi
echo "  WhatTheCat → Stayin' Alive (Bee Gees) deployed successfully"

echo ""
echo "=== All 6 Camelia pack songs deployed (full orchestration) ==="
echo "Each command handled: song bundle + pack mode bundles + catalog + redirects + validation"
echo ""
echo "=== Deployment complete ==="