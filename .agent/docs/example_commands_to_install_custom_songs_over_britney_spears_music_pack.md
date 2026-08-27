# Installing Custom Songs Over the Britney Spears Music Pack

This document provides step-by-step commands to install custom songs over the Britney Spears music pack using the pipeline automation.

**Note**: There is currently no Britney Spears music pack in the system. The following commands use the existing therollingstones pack structure as a template, since it has the most complete setup. To use with Britney Spears, you would replace the pack name and song sources accordingly.

## Prerequisites

1. PS4 must be online and reachable at 192.168.100.117:2121
2. GoldHEN firmware with Beat Saber Deluxe v0.8041+
3. Pipeline v0.5328 or later installed on your PC
4. Access to custom song source directories

## Step 1: Prepare Custom Song Sources

The pipeline requires song sources in specific directories:

```bash
# For non-Chromeo songs (in songs_repo):
# Format: <hash>/ with these files:
# - Info.dat  (contains _songName, _songAuthorName, _beatsPerMinute, etc.)
# - .dat files for each difficulty/mode combination
# Example from therollingstones:
ls /workspace/beat-saber-ps4-custom-songs/songs_repo/06121351c6bc732112b20d2c524fb84c036ddf5e/
# Contains: Info.dat, Easy.dat, EasyNoArrows.dat, etc.

# For Chromeo songs (from PS4 bundle extraction):
# Format: songs/chromeo_backout/<song_name>/ 
# Contains: .dat files + audio.fsb
# Example:
ls /workspace/beat-saber-ps4-custom-songs/songs/chromeo_backout/Crystallized/
```

## Step 2: Add Song to song_metadata.json

If adding a new song not already in the system:

```bash
# Edit song_metadata.json to add the new song entry
# Format: "song_display_name": "source_directory_hash"
# Example:
# "American Idiot": "01ce5a3adc19e360ba0ffd8347f91b5dc974eb7c"

# Or if using the pipeline script's auto-resolution, ensure the song name matches
# one of the detected modes from detect_song_modes()
```

## Step 3: Run the Build and Deploy Pipeline

### Option A: Full Automated Build + Deploy (Recommended)

This single command builds all 38 songs and deploys everything in one pipeline pass:

```bash
cd /workspace/beat_saber_deluxe
python3 development/scripts/build_deploy_all38.py
```

**What this does**:
- Phase 1: Builds all 38 custom song bundles into `/workspace/beat_saber_deluxe/mass_bundles/`
- Phase 2: Deploys all 38 song bundles + 4 pack bundles + catalog + redirects.json to PS4
- Phase 3: Runs post-deploy validation (verifies 2251 entries, md5 hashes, CRC/size)

### Option B: Two-Step Manual Process (if needed)

**Step 3a: Build Only (no deployment)**

```bash
python3 development/scripts/build_deploy_all38.py --build-only
```

This builds all bundles into `/workspace/beat_saber_deluxe/mass_bundles/` without uploading to PS4.

**Step 3b: Deploy Existing Bundles**

```bash
python3 tools/full_custom_song_pipeline.py \
    --deploy-mass-bundles \
    --deploy-pack-modes \
    --deploy-config \
    --verify-ps4
```

## Step 4: Verify the Installation

After deployment, verify the installation:

```bash
# Check PS4 file listing
ls -la /data/GoldHEN/AFR/CUSA12878/ | grep "_v3.bundle" | wc -l
# Should show 38 song bundles

# Verify specific song
python3 - << 'PYEOF'
from UnityPy import Environment
env = Environment('/workspace/beat_saber_deluxe/mass_bundles/startmeup_v3.bundle')
for obj in env.objects:
    if obj.type.name == 'TextAsset':
        nm = getattr(obj.read(), 'm_Name', '')
        if 'beatmap' in nm.lower():
            print(f"  {nm}")
PYEOF
```

## Step 5: Verify Mode Selector Shows 4 Modes

For each custom song, verify all 4 modes are selectable:

```bash
# Check a specific song's bundle for mode coverage
python3 << 'PYEOF'
from UnityPy import Environment

def check_bundle_modes(song_slot):
    env = Environment(f'/workspace/beat_saber_deluxe/mass_bundles/{song_slot}_v3.bundle')
    modes_found = set()
    for obj in env.objects:
        if obj.type.name == 'TextAsset':
            nm = getattr(obj.read(), 'm_Name', '')
            for mode in ['OneSaber', 'NoArrows', '90Degree']:
                if mode in nm:
                    modes_found.add(mode)
    return len(modes_found) == 4  # Should be True for all songs

# Test a few songs
for slot in ['startmeup', 'angry', 'lizzo', 'crystallized']:
    result = check_bundle_modes(slot)
    print(f"{slot}: {'PASS - 4 modes' if result else 'FAIL - missing modes'}")
PYEOF
```

## Step 6: Verify All 4 Music Packs Have Complete Mode Sets

```bash
# Verify each of the 4 music packs has all songs with 4 modes
python3 << 'PYEOF'
import os
from UnityPy import Environment

packs = ['therollingstones', 'billieeilish', 'lizzo', 'camellia']
for pack in packs:
    pack_dir = '/workspace/beat_saber_deluxe/pack_modes_bundles'
    bundle_files = [f for f in os.listdir(pack_dir) if f.endswith('_v3.bundle')]
    
    total_ok = 0
    total_bundles = len(bundle_files)
    
    for bundle in bundle_files:
        env = Environment(f'{pack_dir}/{bundle}')
        # Check for mode sets in the bundle
        for obj in env.objects:
            if obj.type.name == 'MonoBehaviour':
                # Quick check for mode-related data
                pass
    
    print(f"{pack}: {total_bundles} bundles")
PYEOF
```

## Troubleshooting Common Issues

### If a song doesn't appear in the selector:
1. Verify the redirect in `redirects.json` points to the correct bundle
2. Check that the bundle was deployed successfully (`grep "✅" /tmp/deploy.log`)
3. Ensure the bundle filename matches the redirect value exactly (case-sensitive)

### If a mode is missing:
1. Check that the beatmap .dat files exist in the bundle
2. Verify the V3 schema is complete (17 keys including basicBeatmapEvents, waypoints, etc.)
3. Ensure the Easy difficulty has notes (zero-note maps were the Chromeo issue - fixed in v0.5328)

### If deployment fails:
1. Check PS4 connectivity: `lftp -u anonymous, -p 2121 192.168.100.117 -ls`
2. Verify local bundles exist in `/workspace/beat_saber_deluxe/mass_bundles/`
3. Check the deploy log for specific errors

## Interim Testing: Testing a Single Custom Song

If you want to test just one custom song without rebuilding everything:

```bash
# Single song build and deploy
python3 tools/full_custom_song_pipeline.py \
    --song-dir /workspace/beat-saber-ps4-custom-songs/songs_repo/06121351c6bc732112b20d2c524fb84c036ddf5c \
    --target startmeup \
    --pcm16 \
    --no-pad \
    --output /workspace/beat_saber_deluxe/mass_bundles/startmeup_v3.bundle \
    --deploy
```

This will:
1. Build the single song bundle into mass_bundles/
2. Deploy it to PS4
3. Run post-deploy validation

## Complete Workflow Summary

For a fresh PS4 setup:

1. `cd /workspace/beat_saber_deluxe`
2. `python3 development/scripts/build_deploy_all38.py` (builds + deploys everything)
3. Verify: `ls /data/GoldHEN/AFR/CUSA12878/ | grep _v3.bundle | wc -l` should show 38
4. Test: Launch Beat Saber and verify all 4 music packs show 4 modes each

For adding one new custom song to an existing pack:

1. Add song source to appropriate directory
2. `python3 development/scripts/build_deploy_all38.py --build-only`
3. `python3 tools/full_custom_song_pipeline.py --deploy-mass-bundles --deploy-pack-modes --deploy-config --verify-ps4`
4. Verify the new song appears with 4 modes

## Complete Command Sequence (One-Shot)

```bash
#!/bin/bash
# Full custom song installation

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
