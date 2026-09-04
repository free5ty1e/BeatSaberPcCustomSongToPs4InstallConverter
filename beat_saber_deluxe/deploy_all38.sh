#!/bin/bash
# Deploy all 38 rebuilt custom song bundles + patched pack bundle + catalog to the PS4.
# Thin wrapper around the pipeline's self-validating mass deploy (v0.5317+):
#   - uploads every <slot>_v3.bundle from mass_deploy.bundle_dir
#   - deploys the patched pack bundle + catalog_startmeup_modes.json
#   - regenerates + deploys redirects.json (pack bundle + catalog pair enforced)
#   - runs post-deploy PS4 validation (PASS/FAIL per check)
# Requires the PS4 to be online at 192.168.100.117:2121.
set -eu

cd "$(dirname "$0")"
exec python3 tools/full_custom_song_pipeline.py \
  --deploy-mass-bundles --deploy-pack-bundle \
  --generate-config --deploy-config
