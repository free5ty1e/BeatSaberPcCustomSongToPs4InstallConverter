#!/bin/bash
# Complete deploy script: Plugin + All 12 Rolling Stones + Live By The Sword bundles
# Usage: ./deploy_all.sh [--release|--debug]
# Default: deploys release plugin (no verbose per-file logging)
# --debug: deploys debug plugin with verbose logging to bs_log.txt

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT="$SCRIPT_DIR/custom_songs"

# Read PS4 config
CFG="$SCRIPT_DIR/ps4_config.json"
PS4_IP=$(python3 -c "import json; print(json.load(open('$CFG'))['ps4']['ip'])" 2>/dev/null || echo "192.168.100.117")
PS4_PORT=$(python3 -c "import json; print(json.load(open('$CFG'))['ps4']['ftp_port'])" 2>/dev/null || echo "2121")

TARGETS=(
    "angry"
    "bitemyheadoff"
    "cantyouhearmeknocking"
    "deadmanwalking"
    "gimmeshelter"
    "icantgetnosatisfaction"
    "livebythesword"
    "messitup"
    "paintitblack"
    "startmeup"
    "sugarsoaker"
    "sympathyforthedevil"
    "wholewideworld"
)

# ── Step 1: Deploy the plugin ──────────────────────────────────────────────
PLUGIN_MODE="$1"
if [ "$PLUGIN_MODE" = "--debug" ]; then
    PLUGIN_FILE="$SCRIPT_DIR/beat_saber_deluxe_debug.prx"
    echo "🔧 Deploying DEBUG plugin (verbose logging)..."
else
    PLUGIN_FILE="$SCRIPT_DIR/beat_saber_deluxe.prx"
    echo "🚀 Deploying RELEASE plugin..."
fi

if [ ! -f "$PLUGIN_FILE" ]; then
    echo "❌ Plugin not found: $PLUGIN_FILE"
    echo "   Run 'make' or 'make DEBUG=1' first."
    exit 1
fi

echo "📤 Uploading plugin..."
lftp -u anonymous, -p "$PS4_PORT" "$PS4_IP" \
    -e "put '$PLUGIN_FILE' -o '/data/GoldHEN/plugins/beat_saber_deluxe.prx'; quit" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "  ✅ Plugin deployed"
else
    echo "  ❌ Plugin deployment failed"
    exit 1
fi

# ── Step 2: Deploy all bundles ─────────────────────────────────────────────
echo ""
echo "📦 Deploying $((${#TARGETS[@]})) bundles..."
for TARGET in "${TARGETS[@]}"; do
    BUNDLE="$OUTPUT/${TARGET}_custom_v3.bundle"
    if [ ! -f "$BUNDLE" ]; then
        BUNDLE="$OUTPUT/${TARGET}_custom.bundle"
    fi
    if [ ! -f "$BUNDLE" ]; then
        echo "  ⚠️  Bundle not found: $BUNDLE (skipping)"
        continue
    fi

    REMOTE_PATH="/data/GoldHEN/AFR/CUSA12878/${TARGET}_v3"
    SIZE_MB=$(stat --format=%s "$BUNDLE" 2>/dev/null | awk '{printf "%.1f", $1/1024/1024}')

    echo "  📤 $TARGET ($SIZE_MB MB)..."
    lftp -u anonymous, -p "$PS4_PORT" "$PS4_IP" \
        -e "put '$BUNDLE' -o '$REMOTE_PATH'; quit" 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "    ✅ $TARGET deployed"
    else
        echo "    ❌ $TARGET failed"
    fi
done

echo ""
echo "========================================"
echo "✅ Deploy complete!"
echo ""
echo "🔄 Restart Beat Saber on PS4"
echo ""
echo "What to test:"
echo "1. Play each Rolling Stones song"
echo "2. Start Me Up should play Espresso (verified working)"
echo "3. All other 11 should play their custom songs"
echo "4. Check ps_log.txt for redirect counts: grep '->' bs_log.txt | grep AFR"
echo ""
echo "If plugin still shows old version, restart PS4 fully"
echo "(Some GoldHEN installs cache the plugin until reboot)"
