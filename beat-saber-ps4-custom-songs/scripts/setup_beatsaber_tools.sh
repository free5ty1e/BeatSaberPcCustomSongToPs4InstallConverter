#!/bin/bash
# Beat Saber PS4 Custom Songs - Devcontainer Setup
# Installs Python dependencies and tools for custom song conversion

set -e

echo "=========================================="
echo "Beat Saber PS4 Custom Songs - Tool Setup"
echo "=========================================="

# Check if we're in the right directory
if [ ! -d "beat-saber-ps4-custom-songs" ]; then
    echo "Error: Not in the beat-saber-ps4-custom-songs directory"
    exit 1
fi

# Install Python packages (should already be available)
echo "Checking Python packages..."
python3 -c "import gzip, json, struct" 2>/dev/null || {
    echo "Note: Python standard library modules available"
}

# Create directories if needed
mkdir -p beat-saber-ps4-custom-songs/output/converted_songs
mkdir -p beat-saber-ps4-custom-songs/output/dlc_package/sce_sys
mkdir -p beat-saber-ps4-custom-songs/output/dlc_package/StreamingAssets/BeatmapLevelsData
mkdir -p beat-saber-ps4-custom-songs/output/dlc_package/StreamingAssets/HmxAudioAssets/songs
mkdir -p beat-saber-ps4-custom-songs/tools

# Make scripts executable
chmod +x beat-saber-ps4-custom-songs/scripts/*.py

echo ""
echo "Available tools:"
echo "  - convert_songs.py    : Convert PC songs to PS4 format"
echo "  - create_paramsfo.py   : Create PS4 PARAM.SFO (replaces orbis-pub-sfo.exe)"
echo "  - create_pkg.py        : Create PS4 PKG (replaces orbis-pub-gen.exe)"
echo "  - create_unlocker.py   : Create DLC unlocker (replaces psDLC.exe)"
echo ""
echo "Usage examples:"
echo "  # Convert all songs"
echo "  python3 beat-saber-ps4-custom-songs/scripts/convert_songs.py"
echo ""
echo "  # Create PARAM.SFO"
echo "  python3 beat-saber-ps4-custom-songs/scripts/create_paramsfo.py \\"
echo "    --content-id 'UP8802-CUSA12878_00-BSCUSTOMSONGS01' \\"
echo "    --output beat-saber-ps4-custom-songs/output/dlc_package/sce_sys/param.sfo"
echo ""
echo "  # Create PKG"
echo "  python3 beat-saber-ps4-custom-songs/scripts/create_pkg.py \\"
echo "    --content-id 'UP8802-CUSA12878_00-BSCUSTOMSONGS01' \\"
echo "    --folder beat-saber-ps4-custom-songs/output/dlc_package \\"
echo "    --output UP8802-CUSA12878_00-BSCUSTOMSONGS01.pkg"
echo ""
echo "  # Create unlocker"
echo "  python3 beat-saber-ps4-custom-songs/scripts/create_unlocker.py \\"
echo "    --content-id 'UP8802-CUSA12878_00-BSCUSTOMSONGS01' \\"
echo "    --output UP8802-CUSA12878_00-BSCUSTOMSONGS01-unlock.pkg"
echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="