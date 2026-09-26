#!/usr/bin/env bash
#
# exercise-bsd-backup.sh
#
# A shell script to fully exercise the backup-beat-saber-deluxe-files.py script.
# Runs all four exercise workflows using the actual PS4 connection.
#
# Prerequisites:
#   - backup-beat-saber-deluxe-files.py at /workspace/backup-beat-saber-deluxe-files.py
#   - PS4 at 192.168.100.117:2121 (set PS4_IP/PS4_PORT env vars if different)
#
# Usage:
#   chmod +x /workspace/exercise-bsd-backup.sh
#   /workspace/exercise-bsd-backup.sh
#

set -euo pipefail

SCRIPT="/workspace/backup-beat-saber-deluxe-files.py"
BACKUP_DIR="/workspace/ps4_backups"
ORIGINAL_BACKUP="/workspace/ps4_backup_20260904_120701"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    if [ ! -f "$SCRIPT" ]; then
        log_error "Script not found: $SCRIPT"
        exit 1
    fi

    if [ ! -d "$BACKUP_DIR" ]; then
        log_error "Backup directory not found: $BACKUP_DIR"
        exit 1
    fi

    log_info "Prerequisites check passed"
}

# Exercise 1: Restore from original backup
exercise1_restore() {
    log_info "Starting Exercise 1: Restore from original backup"
    log_info "Command: $SCRIPT restore $ORIGINAL_BACKUP"

    output=$("$SCRIPT" restore "$ORIGINAL_BACKUP" 2>&1) || true

    echo ""
    echo "=== EXERCISE 1 OUTPUT ==="
    echo "$output"
    echo ""

    # Check for expected validation markers
    if echo "$output" | grep -q "RESTORE COMPLETE"; then
        log_info "✓ Exercise 1: Restore completed successfully"
    else
        log_warn "⚠ Exercise 1: Restore completion marker not found"
    fi

    if echo "$output" | grep -q "afr.prx"; then
        log_info "✓ Exercise 1: afr.prx restore confirmed in output"
    else
        log_warn "⚠ Exercise 1: afr.prx restore not confirmed in output"
    fi

    if echo "$output" | grep -q "game_patch.prx"; then
        log_info "✓ Exercise 1: game_patch.prx restore confirmed in output"
    else
        log_warn "⚠ Exercise 1: game_patch.prx restore not confirmed in output"
    fi

    if echo "$output" | grep -q "plugins.ini"; then
        log_info "✓ Exercise 1: plugins.ini restore confirmed in output"
    else
        log_warn "⚠ Exercise 1: plugins.ini restore not confirmed in output"
    fi

    if echo "$output" | grep -q "AFR/CUSA12878"; then
        log_info "✓ Exercise 1: AFR/CUSA12878 restore confirmed"
    else
        log_warn "⚠ Exercise 1: AFR/CUSA12878 restore not confirmed in output"
    fi

    if echo "$output" | grep -q "Restoring from backup"; then
        log_info "✓ Exercise 1: Restore from backup initiated"
    else
        log_warn "⚠ Exercise 1: Restore from backup not initiated in output"
    fi

    echo ""
    log_info "Exercise 1 complete"
}

# Exercise 2: Backup without clear
exercise2_backup_no_clear() {
    log_info "Starting Exercise 2: Backup to new folder/zip without clear"
    log_info "Command: $SCRIPT backup"

    output=$("$SCRIPT" backup 2>&1) || true

    echo ""
    echo "=== EXERCISE 2 OUTPUT ==="
    echo "$output"
    echo ""

    # Check for expected markers
    if echo "$output" | grep -q "BACKUP COMPLETE"; then
        log_info "✓ Exercise 2: Backup completed successfully"
    else
        log_warn "⚠ Exercise 2: Backup completion marker not found"
    fi

    if echo "$output" | grep -q "bsd_backup_"; then
        log_info "✓ Exercise 2: Timestamped backup folder created"
    else
        log_warn "⚠ Exercise 2: Timestamped backup folder not detected"
    fi

    if echo "$output" | grep -q "\.zip"; then
        log_info "✓ Exercise 2: Zip archive created"
    else
        log_warn "⚠ Exercise 2: Zip archive not detected"
    fi

    # Check that backed up items are listed
    if echo "$output" | grep -q "afr.prx"; then
        log_info "✓ Exercise 2: afr.prx backed up detected"
    else
        log_warn "⚠ Exercise 2: afr.prx backup not detected"
    fi

    if echo "$output" | grep -q "game_patch.prx"; then
        log_info "✓ Exercise 2: game_patch.prx backed up detected"
    else
        log_warn "⚠ Exercise 2: game_patch.prx backup not detected"
    fi

    if echo "$output" | grep -q "plugins.ini"; then
        log_info "✓ Exercise 2: plugins.ini backed up detected"
    else
        log_warn "⚠ Exercise 2: plugins.ini backup not detected"
    fi

    if echo "$output" | grep -q "AFR/CUSA12878"; then
        log_info "✓ Exercise 2: AFR/CUSA12878 backup detected"
    else
        log_warn "⚠ Exercise 2: AFR/CUSA12878 backup not detected"
    fi

    if echo "$output" | grep -q "AFR/test"; then
        log_info "✓ Exercise 2: AFR/test backup detected"
    else
        log_warn "⚠ Exercise 2: AFR/test backup not detected"
    fi

    if echo "$output" | grep -q "AFR/bs_log"; then
        log_info "✓ Exercise 2: AFR/bs_log backup detected"
    else
        log_warn "⚠ Exercise 2: AFR/bs_log backup not detected"
    fi

    echo ""
    log_info "Exercise 2 complete"
}

# Exercise 3: Backup with clear
exercise3_backup_with_clear() {
    log_info "Starting Exercise 3: Backup to new folder/zip with clear"
    log_info "Command: $SCRIPT backup --clean-ps4"

    output=$("$SCRIPT" backup --clean-ps4 2>&1) || true

    echo ""
    echo "=== EXERCISE 3 OUTPUT ==="
    echo "$output"
    echo ""

    # Check for expected markers
    if echo "$output" | grep -q "BACKUP COMPLETE"; then
        log_info "✓ Exercise 3: Backup completed successfully"
    else
        log_warn "⚠ Exercise 3: Backup completion marker not found"
    fi

    if echo "$output" | grep -q "bsd_backup_"; then
        log_info "✓ Exercise 3: Timestamped backup folder created"
    else
        log_warn "⚠ Exercise 3: Timestamped backup folder not detected"
    fi

    if echo "$output" | grep -q "\.zip"; then
        log_info "✓ Exercise 3: Zip archive created"
    else
        log_warn "⚠ Exercise 3: Zip archive not detected"
    fi

    # Check that cleanup items are listed
    if echo "$output" | grep -q "afr.prx"; then
        log_info "✓ Exercise 3: afr.prx cleanup detected in output"
    else
        log_warn "⚠ Exercise 3: afr.prx cleanup not detected"
    fi

    if echo "$output" | grep -q "game_patch.prx"; then
        log_info "✓ Exercise 3: game_patch.prx cleanup detected in output"
    else
        log_warn "⚠ Exercise 3: game_patch.prx cleanup not detected"
    fi

    if echo "$output" | grep -q "plugins.ini"; then
        log_info "✓ Exercise 3: plugins.ini cleanup (BSD entry removed) detected"
    else
        log_warn "⚠ Exercise 3: plugins.ini cleanup not detected"
    fi

    if echo "$output" | grep -q "AFR/CUSA12878"; then
        log_info "✓ Exercise 3: AFR/CUSA12878 cleanup detected"
    else
        log_warn "⚠ Exercise 3: AFR/CUSA12878 cleanup not detected"
    fi

    if echo "$output" | grep -q "AFR/test"; then
        log_info "✓ Exercise 3: AFR/test cleanup detected"
    else
        log_warn "⚠ Exercise 3: AFR/test cleanup not detected"
    fi

    if echo "$output" | grep -q "AFR/bs_log"; then
        log_info "✓ Exercise 3: AFR/bs_log cleanup detected"
    else
        log_warn "⚠ Exercise 3: AFR/bs_log cleanup not detected"
    fi

    echo ""
    log_info "Exercise 3 complete"
}

# Exercise 4: Restore from latest backup
exercise4_restore_latest() {
    log_info "Starting Exercise 4: Restore from latest backup"

    # Find the latest backup zip
    latest_zip=$(ls -t "$BACKUP_DIR"/bsd_backup_*.zip 2>/dev/null | head -1)

    if [ -z "$latest_zip" ]; then
        log_error "No backup zip files found in $BACKUP_DIR"
        log_info "Looking for any zip files..."
        latest_zip=$(ls -t "$BACKUP_DIR"/*.zip 2>/dev/null | head -1)
    fi

    if [ -z "$latest_zip" ]; then
        log_error "No zip files found at all. Cannot exercise restore."
        log_info "Available zips in $BACKUP_DIR:"
        ls -la "$BACKUP_DIR"/*.zip 2>/dev/null || echo "  No zip files found"
        return 1
    fi

    log_info "Using backup: $latest_zip"

    output=$("$SCRIPT" restore "$latest_zip" 2>&1) || true

    echo ""
    echo "=== EXERCISE 4 OUTPUT ==="
    echo "$output"
    echo ""

    # Check for expected markers
    if echo "$output" | grep -q "RESTORE COMPLETE"; then
        log_info "✓ Exercise 4: Restore completed successfully"
    else
        log_warn "⚠ Exercise 4: Restore completion marker not found"
    fi

    # Check that restored items are listed
    if echo "$output" | grep -q "afr.prx"; then
        log_info "✓ Exercise 4: afr.prx restore detected"
    else
        log_warn "⚠ Exercise 4: afr.prx restore not detected"
    fi

    if echo "$output" | grep -q "game_patch.prx"; then
        log_info "✓ Exercise 4: game_patch.prx restore detected"
    else
        log_warn "⚠ Exercise 4: game_patch.prx restore not detected"
    fi

    if echo "$output" | grep -q "plugins.ini"; then
        log_info "✓ Exercise 4: plugins.ini restore detected"
    else
        log_warn "⚠ Exercise 4: plugins.ini restore not detected"
    fi

    if echo "$output" | grep -q "AFR/CUSA12878"; then
        log_info "✓ Exercise 4: AFR/CUSA12878 restore detected"
    else
        log_warn "⚠ Exercise 4: AFR/CUSA12878 restore not detected"
    fi

    echo ""
    log_info "Exercise 4 complete"
}

# Main execution
main() {
    echo ""
    echo "========================================="
    echo "BS Deluxe Backup Script Exercise (with PS4)"
    echo "========================================="
    echo ""

    check_prerequisites

    echo ""
    exercise1_restore
    echo ""

    exercise2_backup_no_clear
    echo ""

    exercise3_backup_with_clear
    echo ""

    exercise4_restore_latest
    echo ""

    echo "========================================="
    echo "All exercises complete!"
    echo "========================================="
    echo ""
}

main "$@"