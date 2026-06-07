#!/bin/bash
set -e

INSTALL_DIR="/opt/openorbis"
REPO="OpenOrbis/OpenOrbis-PS4-Toolchain"

echo "--- Step 1: Installing System Dependencies (Clang/LLD) ---"
sudo apt update
sudo apt install -y clang lld

echo "--- Step 2: Installing OpenOrbis SDK ---"
RELEASE_JSON=$(curl -s "https://api.github.com/repos/$REPO/releases/latest")
TAG=$(echo "$RELEASE_JSON" | jq -r '.tag_name')
DOWNLOAD_URL=$(echo "$RELEASE_JSON" | jq -r '.assets[] | select(.name | contains("toolchain") and contains(".tar.gz")) | .browser_download_url' | head -n 1)

if [ -z "$DOWNLOAD_URL" ]; then
    echo "Error: Could not find a compatible Linux archive in the latest release."
    exit 1
fi

echo "Downloading SDK v$TAG from: $DOWNLOAD_URL"
curl -L "$DOWNLOAD_URL" -o /tmp/openorbis_sdk.archive

sudo mkdir -p "$INSTALL_DIR"
sudo chmod 777 "$INSTALL_DIR"

echo "Extracting SDK..."
tar -xzf /tmp/openorbis_sdk.archive -C "$INSTALL_DIR"
sudo chmod -R 755 "$INSTALL_DIR"

echo "--- Step 3: Setting Environment Variables ---"
# Add to .zshrc for persistence in the current user's shell
if ! grep -q "OO_PS4_TOOLCHAIN" ~/.zshrc; then
    echo "export OO_PS4_TOOLCHAIN=$INSTALL_DIR/OpenOrbis/PS4Toolchain" >> ~/.zshrc
    echo "export PATH=\$PATH:$INSTALL_DIR/OpenOrbis/PS4Toolchain/bin/linux" >> ~/.zshrc
fi

echo "Installation complete! PLEASE RESTART YOUR TERMINAL or run 'source ~/.zshrc'"
