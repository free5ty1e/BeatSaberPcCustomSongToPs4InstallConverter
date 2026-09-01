# Installing Custom Songs Over the Britney Spears Music Pack

This document provides step-by-step, self-contained pipeline commands to replace all 11 songs
in the official Britney Spears DLC music pack with custom community songs from BeatSaver.

Pipeline: v0.5328 -- fully automated, no manual song_metadata.json editing required.
All custom songs deploy with 4 selectable modes (Standard, OneSaber, NoArrows, 90Degree).

## Target: Britney Spears Official DLC Pack

- Pack key: britneyspears
- Pack bundle: britneyspears_pack_assets_all_18d2741e11e15c97493346b2797ea847.bundle
- 11 songs (each with 5 difficulties: Easy, Normal, Hard, Expert, ExpertPlus):
  1. Baby One More Time -- MAP_ID: 8553 (Blinding Lights)
  2. Circus -- MAP_ID: 1672a (Shape of You)
  3. Gimme More -- MAP_ID: 141 (Gangnam Style)
  4. I'm a Slave 4 U -- MAP_ID: 1fef (Believer)
  5. Me Against The Music -- MAP_ID: 570 (Mr. Blue Sky)
  6. Oops!...I Did It Again -- MAP_ID: 46d4 (Rap God)
  7. Overprotected -- MAP_ID: 11cf8 (Up & Down)
  8. Scream & Shout -- MAP_ID: bd45 (Never Gonna Give You Up)
  9. Till The World Ends -- MAP_ID: 6cc2 (Dance Monkey)
  10. Toxic -- (selected BeatSaver map)
  11. Womanizer -- (selected BeatSaver map)

## Where Target Metadata Lives

The song slot IDs and difficulty modes for the Britney Spears pack are defined in:
  /workspace/beat_saber_deluxe/beat_saber_song_ids.json

Key structure (read from the JSON):
{
  pack: britneyspears,
  songs: [
    songName: ...Baby One More Time, songID: BabyOneMoreTime, ...,
    ...
  ]
}

Each song has a songID that maps to the pipeline --target parameter (slot name).

## Where Local Song Metadata JSON is Stored

The local installed-song metadata file is at:
  /workspace/beat_saber_deluxe/song_metadata.json

This file maps display names to source hash IDs and is NOT included in the repository.
It is automatically managed by the pipeline (build_deploy_all38.py). 
To exclude it from git tracking, add the following line to .gitignore:
song_metadata.json

(If not already present -- it is currently NOT gitignored, so adding it prevents accidental commits.)

## Per-Song Pipeline Command Pattern

Each custom song is downloaded from BeatSaver, converted to V3.2.0 schema, and deployed to PS4
using a single pipeline command:

python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song MAP_ID     --target SLOT_ID     --pcm16     --no-pad     --convert-to-v3     --deploy

Where:
- MAP_ID = the BeatSaver map key (e.g., 8553, 1672a, 141, 1fef, 570, 46d4, 11cf8, bd45, 6cc2)
- SLOT_ID = the slot name from beat_saber_song_ids.json (e.g., BabyOneMoreTime, Circus, GimmeMore, ImASlave4U, MeAgainstTheMusic, OopsIDidItAgain, Overprotected, Scream&Shout, TillTheWorldEnds, Toxic, Womanizer)
- --pcm16 = 16-bit PCM audio (full audio, no downsampling)
- --no-pad = no audio padding (full-length playback)
- --convert-to-v3 = reconstruct V4 beatmap data to V3.2.0 schema
- --deploy = upload bundle + redirect entry to PS4

## 11 Per-Song Commands (Complete Sequence)

Replace all 11 Britney Spears pack songs, one command per song:

# 1. Baby One More Time (MAP_ID: 8553, target: BabyOneMoreTime)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 8553     --target BabyOneMoreTime     --pcm16     --no-pad     --convert-to-v3     --deploy

# 2. Circus (MAP_ID: 1672a, target: Circus)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1672a     --target Circus     --pcm16     --no-pad     --convert-to-v3     --deploy

# 3. Gimme More (MAP_ID: 141, target: GimmeMore)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 141     --target GimmeMore     --pcm16     --no-pad     --convert-to-v3     --deploy

# 4. I'm a Slave 4 U (MAP_ID: 1fef, target: ImASlave4U)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 1fef     --target ImASlave4U     --pcm16     --no-pad     --convert-to-v3     --deploy

# 5. Me Against The Music (MAP_ID: 570, target: MeAgainstTheMusic)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 570     --target MeAgainstTheMusic     --pcm16     --no-pad     --convert-to-v3     --deploy

# 6. Oops!...I Did It Again (MAP_ID: 46d4, target: OopsIDidItAgain)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 46d4     --target OopsIDidItAgain     --pcm16     --no-pad     --convert-to-v3     --deploy

# 7. Overprotected (MAP_ID: 11cf8, target: Overprotected)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 11cf8     --target Overprotected     --pcm16     --no-pad     --convert-to-v3     --deploy

# 8. Scream & Shout (MAP_ID: bd45, target: Scream&Shout)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song bd45     --target Scream&Shout     --pcm16     --no-pad     --convert-to-v3     --deploy

# 9. Till The World Ends (MAP_ID: 6cc2, target: TillTheWorldEnds)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 6cc2     --target TillTheWorldEnds     --pcm16     --no-pad     --convert-to-v3     --deploy

# 10. Toxic (MAP_ID: TOXIC_MAP_ID, target: Toxic)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song TOXIC_MAP_ID     --target Toxic     --pcm16     --no-pad     --convert-to-v3     --deploy

# 11. Womanizer (MAP_ID: WOMANIZER_MAP_ID, target: Womanizer)
python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song WOMANIZER_MAP_ID     --target Womanizer     --pcm16     --no-pad     --convert-to-v3     --deploy

## Interim: Single Custom Song Test (One-Song Only)

Test a single song before deploying the full pack:

python3 tools/full_custom_song_pipeline.py     --download-beat-saver-song 8553     --target BabyOneMoreTime     --pcm16     --no-pad     --convert-to-v3     --deploy

Verify the song appears in-game with all 4 modes selectable (Standard, OneSaber, NoArrows, 90Degree).

## Full Pack Deploy (After All 11 Songs Are Individualy Deployed)

Once all 11 songs are individually deployed, run the consolidated deploy to update
the pack metadata, catalog, and redirects in one pass:

cd /workspace/beat_saber_deluxe
python3 development/scripts/build_deploy_all38.py

This single command:
- Auto-detects all songs in songs_repo/ and songs/chromeo_backout/
- Resolves song metadata automatically (no manual song_metadata.json editing)
- Builds all bundles into mass_bundles/
- Deploys all 38 custom song bundles + 4 pack bundles + merged catalog + redirects.json to PS4
- Runs post-deploy validation (verifies all files, hashes, CRC/size)

## Verify Installation

After deployment, verify the Britney pack has 4 modes available:

# Check song bundles on PS4
ls /data/GoldHEN/AFR/CUSA12878/*_v3.bundle | wc -l
# Should show 38 (38 custom songs deployed)

# Verify mode coverage for Britney songs
python3 - << 'PYEOF'
from UnityPy import Environment
env = Environment('/workspace/beat_saber_deluxe/mass_bundles/BabyOneMoreTime_v3.bundle')
modes = set()
for obj in env.objects:
    if obj.type.name == 'TextAsset':
        nm = getattr(obj.read(), 'm_Name', '')
        for mode in ['OneSaber', 'NoArrows', '90Degree']:
            if mode in nm:
                modes.add(mode)
print(f BabyOneMoreTime modes: {modes} (should include 4 modes)')
PYEOF

# Verify music pack mode sets
python3 << 'PYEOF'
import os
from UnityPy import Environment

packs = [britneyspears]  Among the 4 configured packs
for pack in packs:
    pack_dir = /workspace/beat_saber_deluxe/pack_modes_bundles
    bundle_files = [f for f in os.listdir(pack_dir) if f.endswith(_v3.bundle)]
    print(f {pack}: {len(bundle_files)} bundles deployed)
PYEOF
