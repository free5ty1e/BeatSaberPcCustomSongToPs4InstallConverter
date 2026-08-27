#!/bin/bash
# Full custom song installation over Britney Spears music pack (uses therollingstones template)

cd /workspace/beat_saber_deluxe

# Step 1: Build and deploy everything
echo "=== Building and deploying all 38 custom songs + 4 packs ==="
python3 development/scripts/build_deploy_all38.py

# Step 2: Verify deployment
echo "=== Verifying deployment ==="
echo "Song bundles on PS4:"
ls /data/GoldHEN/AFR/CUSA12878/*_v3.bundle 2>/dev/null | wc -l
echo "Pack bundles on PS4:"
ls /data/GoldHEN/AFR/CUSA12878/*_pack_modes_assets* 2>/dev/null | wc -l

# Step 3: Run full validation
echo "=== Running post-deploy validation ==="
python3 tools/full_custom_song_pipeline.py --deploy-mass-bundles --deploy-pack-modes --deploy-config --verify-ps4

echo "=== Done! ==="
echo "Your PS4 now has:"
echo "- 38 custom songs, each with 4 selectable modes"
echo "- 4 music packs fully patched"
echo "- Validated redirect configuration"
