#!/bin/bash
set -e

INSTALL_DIR="/opt/openorbis"
REPO="OpenOrbis/OpenOrbis-PS4-Toolchain"

echo "Searching for the latest OpenOrbis SDK release..."

# Use GitHub API to find the latest release and its assets
RELEASE_JSON=$(curl -s "https://api.github.com/repos/$REPO/releases/latest")
TAG=$(echo "$RELEASE_JSON" | jq -r '.tag_name')

if [ "$TAG" == "null" ]; then
    echo "Error: Could not find the latest release tag."
    exit 1
fi

echo "Latest release found: $TAG"

# Find the asset: Prioritize .tar.gz as it's the standard for Linux toolchains
# We look for 'toolchain' and '.tar.gz'
DOWNLOAD_URL=$(echo "$RELEASE_JSON" | jq -r '.assets[] | select(.name | contains("toolchain") and contains(".tar.gz")) | .browser_download_url' | head -n 1)

# Fallback: If no toolchain.tar.gz, try any .tar.gz
if [ -z "$DOWNLOAD_URL" ]; then
    echo "No 'toolchain' .tar.gz found, trying any .tar.gz asset..."
    DOWNLOAD_URL=$(echo "$RELEASE_JSON" | jq -r '.assets[] | select(.name | contains(".tar.gz")) | .browser_download_url' | head -n 1)
fi

if [ -z "$DOWNLOAD_URL" ]; then
    echo "Error: Could not find a compatible Linux archive (.tar.gz) in the latest release."
    exit 1
fi

echo "Downloading asset from: $DOWNLOAD_URL"
curl -L "$DOWNLOAD_URL" -o /tmp/openorbis_sdk.archive

echo "Preparing installation directory..."
sudo mkdir -p "$INSTALL_DIR"
sudo chmod 777 "$INSTALL_DIR"

echo "Extracting SDK..."
if [[ "$DOWNLOAD_URL" == *".zip" ]]; then
    unzip -q /tmp/openorbis_sdk.archive -d "$INSTALL_DIR"
elif [[ "$DOWNLOAD_URL" == *".tar.gz" ]]; then
    tar -xzf /tmp/openorbis_sdk.archive -C "$INSTALL_DIR"
else
    echo "Error: Unsupported archive format."
    exit 1
fi

echo "Setting permissions..."
sudo chmod -R 755 "$INSTALL_DIR"

echo "Installation complete! SDK is located at $INSTALL_DIR"
