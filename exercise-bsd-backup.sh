#!/usr/bin/env bash
#
# exercise-bsd-backup.sh
#
# A shell script to fully exercise the backup-beat-saber-deluxe-files.py script.
# Runs all four exercise workflows from a state where the PS4 is a blank slate
# and a backup folder exists.
#
# Prerequisites:
#   - backup-beat-saber-deluxe-files.py at /workspace/backup-beat-saber-deluxe-files.py
#   - PS4 at 192.168.1.100 (or set PS4_IP env var)
#   - --local flag for testing without PS4 connectivity
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
RED='\033[0;31m'
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

    if [ ! -d "$ORIGINAL_BACKUP" ]; then
        log_error "Original backup directory not found: $ORIGINAL_BACKUP"
        log_info "Creating a minimal backup structure for exercise..."
        mkdir -p "$BACKUP_DIR/test_backup"
        touch "$BACKUP_DIR/test_backup/placeholder.txt"
    fi

    log_info "Prerequisites check passed"
}

# Exercise 1: Restore from original backup
exercise1_restore() {
    log_info "Starting Exercise 1: Restore from original backup"
    log_info "Command: $SCRIPT restore $ORIGINAL_BACKUP --local"

    output=$("$SCRIPT" restore "$ORIGINAL_BACKUP" --local 2>&1) || true

    echo ""
    echo "=== EXERCISE 1 OUTPUT ==="
    echo "$output"
    echo ""

    # Check for expected validation markers
    if echo "$output" | grep -q "✅ Verifying PS4 is clean"; then
        log_info "✓ Exercise 1: PS4 clean verification found in output"
    else
        log_warn "⚠ Exercise 1: PS4 clean verification not found in output"
    fi

    if echo "$output" | grep -q "✓ beat_saber_deluxe.prx removed from PS4"; then
        log_info "✓ Exercise 1: Plugin PRX removal confirmed"
    else
        log_warn "⚠ Exercise 1: Plugin PRX removal not confirmed in output"
    fi

    echo ""
    log_info "Exercise 1 complete"
}

# Exercise 2: Backup without clear
exercise2_backup_no_clear() {
    log_info "Starting Exercise 2: Backup to new folder/zip without clear"
    log_info "Command: $SCRIPT backup --local"

    output=$("$SCRIPT" backup --local 2>&1) || true

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

    echo ""
    log_info "Exercise 2 complete"
}

# Exercise 3: Backup with clear
exercise3_backup_with_clear() {
    log_info "Starting Exercise 3: Backup to new folder/zip with clear"
    log_info "Command: $SCRIPT backup --clean-ps4 --local"

    output=$("$SCRIPT" backup --clean-ps4 --local 2>&1) || true

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

    if echo "$output" | grep -q "Cleaning PS4 after backup"; then
        log_info "✓ Exercise 3: PS4 clean step attempted"
    else
        log_warn "⚠ Exercise 3: PS4 clean step not found in output"
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
        log_error "No zip files found at all. Creating exercise backup first..."
        "$SCRIPT" backup --local > /dev/null 2>&1 || true
        latest_zip=$(ls -t "$BACKUP_DIR"/bsd_backup_*.zip 2>/dev/null | head -1)
    fi

    log_info "Using backup: $latest_zip"

    output=$("$SCRIPT" restore "$latest_zip" --local 2>&1) || true

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

    echo ""
    log_info "Exercise 4 complete"
}

# Main execution
main() {
    echo ""
    echo "========================================="
    echo "BS Deluxe Backup Script Exercise"
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