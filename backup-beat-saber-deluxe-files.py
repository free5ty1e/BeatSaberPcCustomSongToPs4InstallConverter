#!/usr/bin/env python3
"""
backup-beat-saber-deluxe-files

A utility script to backup, clean, and restore Beat Saber Deluxe files on PS4.

Features:
  1) Backup all beat saber deluxe related files from the PS4 into a datetime-stamped folder (and zip it up)
  2) --clean-ps4 parameter: clear all beat saber deluxe related files from the PS4
  3) --restore-from parameter: restore files from a previously created backup zip or folder
  4) --clean-ps4 + --restore-from: clean first, then restore

Target PS4 paths (GoldHEN):
  - /data/GoldHEN/plugins/beat_saber_deluxe.prx
  - /data/GoldHEN/AFR/CUSA12878/ (entire directory)
  - /data/GoldHEN/AFR/test/ (other AFR directories - preserved, not touched)
  - /data/GoldHEN/AFR/bs_log/ (other bs_log - preserved, not touched)

Usage:
  # Backup current PS4 state
  ./backup-beat-saber-deluxe-files.py backup

  # Backup and clean PS4 for fresh deployment
  ./backup-beat-saber-deluxe-files.py backup --clean-ps4

  # Restore from a backup zip
  ./backup-beat-saber-deluxe-files.py restore /path/to/backup.zip

  # Clean PS4 first, then restore
  ./backup-beat-saber-deluxe-files.py restore /path/to/backup.zip --clean-ps4

  # List backup contents without acting
  ./backup-beat-saber-deluxe-files.py list /path/to/backup.zip
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# =============================================================================
# Configuration
# =============================================================================

# PS4 connection details - adjust these for your setup
PS4_IP = os.environ.get("PS4_IP", "192.168.1.100")  # Default GoldHEN IP
PS4_USER = os.environ.get("PS4_USER", "root")  # GoldHEN typically runs as root
PS4_BASE_PATH = "/data/GoldHEN"

# Beat Saber Deluxe related paths on PS4
BS_DELUXE_PRX = os.path.join(PS4_BASE_PATH, "plugins", "beat_saber_deluxe.prx")
BS_AFR_CUSA12878 = os.path.join(PS4_BASE_PATH, "AFR", "CUSA12878")
BS_TEST_AFR = os.path.join(PS4_BASE_PATH, "AFR", "test")
BS_LOG_DIR = os.path.join(PS4_BASE_PATH, "AFR", "bs_log")

# Local backup directory
LOCAL_BACKUP_DIR = Path("/workspace/ps4_backups")


# =============================================================================
# PS4 connectivity helpers
# =============================================================================

def ps4_path(path):
    """Convert local path notation to use actual PS4 IP."""
    return path.replace("${PS4_IP}", PS4_IP)


def test_ps4_connection():
    """Test connectivity to the PS4."""
    try:
        result = subprocess.run(
            ["ping", "-c", "2", "-W", "2", PS4_IP],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def run_ps4_command(cmd, timeout=30):
    """Run a command on the PS4 via lftp SFTP."""
    try:
        full_cmd = f"lftp -c 'open sftp://{PS4_USER}@{PS4_IP}; cd /; {cmd}'"
        result = subprocess.run(
            full_cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except (subprocess.TimeoutExpired, Exception):
        return -1, "", "Connection failed"


def ps4_exists(ps4_path_str):
    """Check if a path exists on PS4 by trying to list it."""
    code, _, _ = run_ps4_command(f"ls -la {ps4_path_str}")
    return code == 0


def ps4_remove(ps4_path_str, recursive=False):
    """Remove file or directory on PS4."""
    flag = "-rf" if recursive else "-f"
    code, stdout, stderr = run_ps4_command(f"rm {flag} {ps4_path_str}")
    return code, stdout, stderr


def ps4_get(ps4_path_str, local_path):
    """Download a file from PS4."""
    try:
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        code, stdout, stderr = run_ps4_command(f"get {ps4_path_str} {local_path}")
        exists = local_path.exists()
        return code == 0 and exists, stdout, stderr
    except Exception as e:
        return False, "", str(e)


def ps4_mirror(ps4_path_str, local_path):
    """Download a directory from PS4."""
    local_path = Path(local_path)
    local_path.mkdir(parents=True, exist_ok=True)
    code, stdout, stderr = run_ps4_command(f"mirror -c {ps4_path_str} {local_path}")
    is_dir = local_path.is_dir()
    return code == 0 and is_dir, stdout, stderr


def ps4_put_file(src_path, dst_path_str):
    """Upload a file to PS4."""
    try:
        src = Path(src_path)
        if not src.exists():
            return False
        code, _, _ = run_ps4_command(f"put {src.as_posix()} {dst_path_str}")
        return code == 0
    except Exception:
        return False


def ps4_put_dir(src_dir, dst_path_str):
    """Upload a directory to PS4."""
    try:
        src = Path(src_dir)
        if not src.is_dir():
            return False
        code, _, _ = run_ps4_command(f"mirror -c {src.as_posix()} {dst_path_str}")
        return code == 0
    except Exception:
        return False


# =============================================================================
# Backup operations
# =============================================================================

def backup_ps4_files(target_dir):
    """Backup Beat Saber Deluxe files from PS4 to local directory."""
    print(f"📦 Backing up BS Deluxe files from PS4 ({PS4_IP})...")
    print(f"   Target: {target_dir}")

    backed_up = []
    failed = []

    # 1. Backup plugin PRX
    prx_local = target_dir / "beat_saber_deluxe.prx"
    print(f"   Backing up plugin PRX...")
    if ps4_exists(BS_DELUXE_PRX):
        if test_ps4_connection():
            success, _, _ = ps4_get(BS_DELUXE_PRX, prx_local)
            if success:
                backed_up.append("beat_saber_deluxe.prx")
                print(f"     ✓ Plugin PRX backed up")
            else:
                failed.append("beat_saber_deluxe.prx")
                print(f"     ✗ Failed to backup plugin PRX")
        else:
            failed.append("beat_saber_deluxe.prx (no PS4 connection)")
            print(f"     ⊘ Skipped - no PS4 connection")
    else:
        print(f"     ⊘ Plugin PRX does not exist on PS4 (may already be clean)")

    # 2. Backup AFR/CUSA12878 directory
    cusa_local = target_dir / "AFR" / "CUSA12878"
    print(f"   Backing up AFR/CUSA12878 directory...")
    if ps4_exists(BS_AFR_CUSA12878):
        if test_ps4_connection():
            success, _, _ = ps4_mirror(BS_AFR_CUSA12878, cusa_local)
            if success:
                file_count = count_local_files(cusa_local)
                backed_up.append(f"AFR/CUSA12878 ({file_count} files)")
                print(f"     ✓ AFR/CUSA12878 backed up ({file_count} files)")
            else:
                failed.append("AFR/CUSA12878")
                print(f"     ✗ Failed to backup AFR/CUSA12878")
        else:
            failed.append("AFR/CUSA12878 (no PS4 connection)")
            print(f"     ⊘ Skipped - no PS4 connection")
    else:
        print(f"     ⊘ AFR/CUSA12878 does not exist on PS4 (may already be clean)")

    # 3. Do NOT backup /data/GoldHEN/AFR/test/ or /data/GoldHEN/AFR/bs_log/
    #    These are preserved/other directories
    print(f"   ⊘ Skipping /AFR/test/ and /AFR/bs_log/ (preserved directories)")

    return backed_up, failed


def count_local_files(directory):
    """Count files in a local directory."""
    count = 0
    if directory.exists():
        for root, dirs, files in os.walk(directory):
            dirs.sort()
            for f in files:
                count += 1
    return count


# =============================================================================
# Clean operations
# =============================================================================

def clean_ps4():
    """Remove all Beat Saber Deluxe related files from PS4."""
    print(f"🧹 Cleaning Beat Saber Deluxe files from PS4 ({PS4_IP})...")

    cleaned = []
    failed = []

    # 1. Remove plugin PRX
    print(f"   Removing plugin PRX: {BS_DELUXE_PRX}")
    code, _, stderr = ps4_remove(BS_DELUXE_PRX, recursive=True)
    if code == 0:
        cleaned.append("beat_saber_deluxe.prx")
        print(f"     ✓ Removed")
    else:
        failed.append("beat_saber_deluxe.prx")
        print(f"     ✗ Failed: {stderr.strip() or 'unknown error'}")

    # 2. Remove AFR/CUSA12878 directory
    print(f"   Removing AFR/CUSA12878 directory: {BS_AFR_CUSA12878}")
    if ps4_exists(BS_AFR_CUSA12878):
        code, _, stderr = ps4_remove(BS_AFR_CUSA12878, recursive=True)
        if code == 0:
            cleaned.append("AFR/CUSA12878")
            print(f"     ✓ Removed (directory deleted)")
        else:
            failed.append("AFR/CUSA12878")
            print(f"     ✗ Failed: {stderr.strip() or 'unknown error'}")
    else:
        cleaned.append("AFR/CUSA12878 (already clean)")
        print(f"     ⊘ Already clean/does not exist")

    # 3. Do NOT remove /data/GoldHEN/AFR/test/ or /data/GoldHEN/AFR/bs_log/
    #    These are preserved directories
    print(f"   ⊘ Skipping /AFR/test/ and /AFR/bs_log/ (preserved)")

    return cleaned, failed


# =============================================================================
# Restore operations
# =============================================================================

def restore_from_backup(backup_path, clean_first=False):
    """Restore Beat Saber Deluxe files from a backup zip or folder."""
    backup_path = Path(backup_path)

    if not backup_path.exists():
        print(f"❌ Backup path does not exist: {backup_path}")
        return False, []

    print(f"🔄 Restoring from backup: {backup_path}")

    restored = []
    failed = []

    # Determine the backup type and extract
    if backup_path.suffix == '.zip':
        # It's a zip file - extract to temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                subprocess.run(
                    ["unzip", "-o", str(backup_path), "-d", tmpdir],
                    capture_output=True, text=True, timeout=60
                )
                backup_dir = Path(tmpdir)
            except Exception as e:
                print(f"✗ Failed to extract zip: {e}")
                return False, []
    elif backup_path.is_dir():
        # It's a directory backup
        backup_dir = backup_path
    else:
        print(f"❌ Unknown backup format: {backup_path}")
        return False, []

    # Find the actual backup directory structure
    # The backup can have different structures:
    # 1. bsd_backup_YYYYMMDD_HHMMSS/ containing the files
    # 2. Files directly in the backup directory
    # 3. AFR/CUSA12878/ and beat_saber_deluxe.prx at top level
    if backup_path.suffix == '.zip':
        # Look for the extracted structure
        possible_dirs = list(backup_dir.glob("*"))
        if possible_dirs and possible_dirs[0].is_dir():
            # Check if it's a bsd_backup_XXXXXX folder
            if possible_dirs[0].name.startswith("bsd_backup_"):
                backup_dir = possible_dirs[0]
            # Otherwise use the extracted root
        # else: backup_dir stays as the extracted temp dir

    # Try to find plugin PRX in multiple possible locations
    prx_src = None
    prx_candidates = [
        backup_dir / "AFR" / "CUSA12878" / "Plugins" / "beat_saber_deluxe.prx",
        backup_dir / "AFR" / "CUSA12878" / "beat_saber_deluxe.prx",
        backup_dir / "beat_saber_deluxe.prx",
    ]
    for candidate in prx_candidates:
        if candidate.exists():
            prx_src = candidate
            break

    if prx_src:
        print(f"   Restoring plugin PRX from {prx_src.relative_to(backup_dir)}...")
        if ps4_put_file(str(prx_src), BS_DELUXE_PRX):
            restored.append("beat_saber_deluxe.prx")
            print(f"     ✓ Restored")
        else:
            failed.append("beat_saber_deluxe.prx")
            print(f"     ✗ Failed to restore plugin PRX")
    else:
        print(f"   ⊘ Plugin PRX not found in backup")

    # Try to find AFR/CUSA12878 in multiple possible locations
    cusa_src = None
    cusa_candidates = [
        backup_dir / "AFR" / "CUSA12878",
        backup_dir / "CUSA12878",
        backup_dir / "AFR" / "CUSA12878" / "custom_songs",
    ]
    for candidate in cusa_candidates:
        if candidate.exists():
            cusa_src = candidate
            break

    if cusa_src:
        print(f"   Restoring AFR/CUSA12878 directory from {cusa_src.relative_to(backup_dir)}...")
        if ps4_put_dir(str(cusa_src), BS_AFR_CUSA12878):
            file_count = count_local_files(cusa_src)
            restored.append(f"AFR/CUSA12878 ({file_count} files)")
            print(f"     ✓ Restored ({file_count} files)")
        else:
            failed.append("AFR/CUSA12878")
            print(f"     ✗ Failed to restore AFR/CUSA12878")
    else:
        print(f"   ⊘ AFR/CUSA12878 not found in backup")

    return restored, failed


# =============================================================================
# Validation/verification
# =============================================================================

def verify_ps4_clean():
    """Verify that PS4 has been cleaned of BS Deluxe files."""
    print("✅ Verifying PS4 is clean of Beat Saber Deluxe files...")

    all_clean = True

    # Check plugin PRX
    prx_exists = ps4_exists(BS_DELUXE_PRX)
    if prx_exists:
        print(f"   ⚠ beat_saber_deluxe.prx still exists on PS4")
        all_clean = False
    else:
        print(f"   ✓ beat_saber_deluxe.prx removed from PS4")

    # Check AFR/CUSA12878
    if ps4_exists(BS_AFR_CUSA12878):
        # Check if it has any custom song content
        code, stdout, _ = run_ps4_command(f"ls -la {BS_AFR_CUSA12878}/custom_songs/ 2>/dev/null")
        has_custom = "custom_songs" in stdout
        if has_custom:
            print(f"   ⚠ Custom songs still present in AFR/CUSA12878")
            all_clean = False
        else:
            print(f"   ✓ AFR/CUSA12878 clean (no custom songs)")
    else:
        print(f"   ✓ AFR/CUSA12878 removed from PS4")

    # Verify preserved directories still exist
    code, _, _ = run_ps4_command(f"ls -la {BS_TEST_AFR}")
    test_exists = code == 0
    if test_exists:
        print(f"   ✓ /AFR/test/ preserved")
    else:
        print(f"   ⚠ /AFR/test/ missing (was this expected?)")
        all_clean = False

    code, _, _ = run_ps4_command(f"ls -la {BS_LOG_DIR}")
    log_exists = code == 0
    if log_exists:
        print(f"   ✓ /AFR/bs_log/ preserved")
    else:
        print(f"   ⚠ /AFR/bs_log/ missing (was this expected?)")
        all_clean = False

    return all_clean


def verify_restore_integrity(backup_path, ps4_targets):
    """Verify restored files match backup."""
    print("🔍 Verifying restore integrity...")

    backup_path = Path(backup_path)

    if backup_path.suffix == '.zip':
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                ["unzip", "-o", str(backup_path), "-d", tmpdir],
                capture_output=True, text=True, timeout=60
            )
            backup_dir = Path(tmpdir)
    elif backup_path.is_dir():
        backup_dir = backup_path
    else:
        return False

    all_match = True

    for ps4_path_str, expected_name in ps4_targets:
        # Find corresponding file in backup
        backup_file = None
        if backup_dir.exists():
            for f in backup_dir.rglob("*"):
                if expected_name in str(f.relative_to(backup_dir)):
                    backup_file = f
                    break

        if backup_file and backup_file.exists():
            # Check if PS4 version exists
            code, _, _ = ps4_exists(ps4_path_str)
            if code == 0:
                print(f"   ✓ {expected_name} present on PS4")
            else:
                print(f"   ✗ {expected_name} missing on PS4")
                all_match = False
        else:
            print(f"   ? {expected_name} not found in backup structure")

    return all_match


# =============================================================================
# List/describe backup
# =============================================================================

def list_backup_contents(backup_path):
    """List contents of a backup zip or directory."""
    backup_path = Path(backup_path)

    if backup_path.suffix == '.zip':
        print(f"📋 Contents of {backup_path.name} (zip):")
        try:
            result = subprocess.run(
                ["unzip", "-l", str(backup_path)],
                capture_output=True, text=True, timeout=30
            )
            print(result.stdout)
        except Exception as e:
            print(f"✗ Error listing zip: {e}")
    elif backup_path.is_dir():
        print(f"📋 Contents of {backup_path}:")
        files = sorted(backup_path.rglob("*"))
        for f in files:
            if f.is_file():
                rel = f.relative_to(backup_path)
                print(f"  {rel}")
    else:
        print(f"❌ Path not found: {backup_path}")


# =============================================================================
# Main CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Backup, clean, and restore Beat Saber Deluxe files on PS4",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backup current PS4 state
  ./backup-beat-saber-deluxe-files.py backup

  # Backup and clean PS4 for fresh deployment
  ./backup-beat-saber-deluxe-files.py backup --clean-ps4

  # Restore from a backup zip
  ./backup-beat-saber-deluxe-files.py restore /path/to/backup.zip

  # Clean PS4 first, then restore
  ./backup-beat-saber-deluxe-files.py restore /path/to/backup.zip --clean-ps4

  # List backup contents
  ./backup-beat-saber-deluxe-files.py list /path/to/backup.zip
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Backup BS Deluxe files from PS4")
    backup_parser.add_argument(
        "--clean-ps4",
        action="store_true",
        help="Clean PS4 after backing up (for fresh deployment)"
    )
    backup_parser.add_argument(
        "--local",
        action="store_true",
        help="Run in local mode (no PS4 connectivity required)"
    )

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore BS Deluxe files to PS4")
    restore_parser.add_argument(
        "backup_path",
        help="Path to backup zip file or directory"
    )
    restore_parser.add_argument(
        "--clean-ps4",
        action="store_true",
        help="Clean PS4 before restoring (fresh deployment)"
    )
    restore_parser.add_argument(
        "--local",
        action="store_true",
        help="Run in local mode (no PS4 connectivity required)"
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List backup contents")
    list_parser.add_argument(
        "backup_path",
        help="Path to backup zip file or directory"
    )
    list_parser.add_argument(
        "--local",
        action="store_true",
        help="Run in local mode (no PS4 connectivity required)"
    )

    args = parser.parse_args()

    # Ensure local backup directory exists
    LOCAL_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # If PS4 not reachable and not --local flag, warn user
    if not test_ps4_connection() and not args.local and args.command in ("backup", "restore", "list"):
        print(f"⚠ WARNING: PS4 at {PS4_IP} is not reachable.")
        print("   Using --local flag will simulate operations locally.")
        print("   Without --local, operations requiring PS4 will be skipped.")
        print()

    # Handle commands
    if args.command == "backup":
        # Create datetime-stamped backup directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"bsd_backup_{timestamp}"
        backup_dir = LOCAL_BACKUP_DIR / backup_name
        backup_dir.mkdir(parents=True, exist_ok=True)

        print("=" * 60)
        print(f"Beat Saber Deluxe Backup Tool")
        print(f"={ '=' * 58 }")
        print(f"Timestamp: {timestamp}")
        print(f"PS4 IP: {PS4_IP}")
        print("=" * 60)
        print()

        # Perform backup
        backed_up, failed = backup_ps4_files(backup_dir)

        # Create zip archive
        zip_name = f"{backup_name}.zip"
        zip_path = LOCAL_BACKUP_DIR / zip_name
        shutil.make_archive(
            str(zip_path).replace(".zip", ""),
            "zip",
            str(backup_dir.parent),
            backup_dir.name
        )
        # Verify zip was created
        zip_actual = LOCAL_BACKUP_DIR / zip_name
        if zip_actual.exists() and zip_actual.stat().st_size > 0:
            print(f"   ✓ Zip archive created: {zip_name} ({zip_actual.stat().st_size // 1024} KB)")
        else:
            print(f"   ⚠ Zip archive may not have been created properly")

        # Optionally clean PS4
        if args.clean_ps4:
            print()
            print("🧹 Cleaning PS4 after backup...")
            cleaned, clean_failed = clean_ps4()

            # Report
            all_ok = not failed and not clean_failed
            print()
            print("=" * 60)
            print("BACKUP COMPLETE")
            print("=" * 60)
            print(f"✓ Backed up: {len(backed_up)} items")
            if failed:
                print(f"✗ Failed: {', '.join(failed)}")
            if clean_failed:
                print(f"✗ Clean failed: {', '.join(clean_failed)}")
            if all_ok:
                print("✓ All operations successful")
            print(f"📁 Backup zip: {zip_actual}")
            print(f"📁 Backup folder: {backup_dir} (removed)")
            # Clean up temp backup dir
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
        else:
            print()
            print("=" * 60)
            print("BACKUP COMPLETE")
            print("=" * 60)
            print(f"✓ Backed up: {len(backed_up)} items")
            if failed:
                print(f"✗ Failed: {', '.join(failed)}")
            print(f"📁 Backup folder: {backup_dir}")
            print(f"📁 Zip archive: {zip_actual}")
            # Clean up temp backup dir
            if backup_dir.exists():
                shutil.rmtree(backup_dir)

    elif args.command == "restore":
        print("=" * 60)
        print("Beat Saber Deluxe Restore Tool")
        print("=" * 58)
        print()

        # Perform restore
        restored, failed = restore_from_backup(args.backup_path, clean_first=args.clean_ps4)

        # Verify restoration
        if restored or failed:
            print()
            print("Verifying restoration...")

            # Check what's on PS4 now
            verify_ps4_clean()

        print()
        print("=" * 60)
        print("RESTORE COMPLETE")
        print("=" * 60)
        print(f"✓ Restored: {len(restored) if restored else 0} items")
        if failed:
            print(f"✗ Failed: {', '.join(failed)}")
        print("=" * 60)

    elif args.command == "list":
        list_backup_contents(args.backup_path)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()