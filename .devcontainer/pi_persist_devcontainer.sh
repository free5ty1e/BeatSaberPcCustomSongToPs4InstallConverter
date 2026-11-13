#!/usr/bin/env bash
# =============================================================================
# pi_persist_devcontainer.sh — Make Pi (pi-coding-agent) survive rebuilds
#
# A devcontainer rebuild wipes the home directory, losing Pi's sessions,
# settings, auth and extensions (all of $HOME/.pi). This script moves that
# state INTO the workspace — <workspace>/.pi_persist — which survives rebuilds,
# then symlinks $HOME/.pi -> <workspace>/.pi_persist so `pi` keeps launching
# with the normal command, no special parameters or env vars needed.
#
# Usage (from anywhere inside the container):
#   bash .devcontainer/pi_persist_devcontainer.sh
#
# Behavior (idempotent — safe to run any number of times):
#   1. $HOME/.pi is already a symlink to .pi_persist .... nothing to do.
#   2. $HOME/.pi missing/empty, .pi_persist has data .... RESTORE after a
#      rebuild: symlink only (fast path — nothing copied).
#   3. $HOME/.pi has data, .pi_persist missing/empty .... MIGRATE: copy
#      $HOME/.pi into .pi_persist, back the original aside, then symlink.
#   4. Both have data ................................... MERGE: $HOME/.pi is
#      copied OVER .pi_persist (home wins file conflicts; .pi_persist keeps
#      anything home lacks — e.g. pre-rebuild sessions survive while the
#      fresh managed install is refreshed), back the original aside, symlink.
#
# Nothing is ever deleted: the pre-symlink $HOME/.pi is renamed to
#   $HOME/.pi.pre-persist-<timestamp>
# Undo any time with:
#   rm $HOME/.pi && mv $HOME/.pi.pre-persist-<timestamp> $HOME/.pi
#
# LIVE-SESSION TAIL: a running pi keeps its open file handle on the OLD
# session file, so the current session keeps writing into the backup dir
# after the swap. Re-running this script folds any newer session files from
# those backups into .pi_persist — so RUN IT ONCE MORE BEFORE REBUILDING
# the container (the backup lives in $HOME, which the rebuild wipes).
#
# NOTE: .pi_persist contains auth.json (provider credentials) and your
# session history. The script adds .pi_persist/ to the workspace .gitignore —
# never commit it or share the folder.
# =============================================================================
set -euo pipefail

HOME_DIR="${HOME:-/home/vscode}"
PI_DIR="$HOME_DIR/.pi"

# Workspace root: devcontainer env vars -> git toplevel -> cwd.
WS="${CONTAINER_WORKSPACE_FOLDER:-${WORKSPACE_FOLDER:-}}"
if [ -z "$WS" ]; then
    WS="$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
fi
TARGET="$WS/.pi_persist"

has_data() { [ -d "$1" ] && [ -n "$(ls -A "$1" 2>/dev/null)" ]; }

count_sessions() {
    find "$1/agent/sessions" -name '*.jsonl' 2>/dev/null | wc -l | tr -d ' '
}

if pgrep -x pi >/dev/null 2>&1; then
    echo "⚠️  A 'pi' process appears to be running. Migrating under it is safe"
    echo "    (its live session file is copied as-is), but re-run afterwards"
    echo "    if you want the very latest session state in .pi_persist."
fi

# ── Case 1: already persisted ────────────────────────────────────────────────
if [ -L "$PI_DIR" ]; then
    CURRENT="$(readlink "$PI_DIR")"
    if [ "$CURRENT" = "$TARGET" ]; then
        echo "✅ Already persisted: $PI_DIR -> $TARGET ($(count_sessions "$PI_DIR") sessions)"
        # Fold the live-session tail: a pi process that was running during the
        # original swap keeps appending to the backup location. Newer session
        # files from the backups are merged in; the backups themselves are kept.
        for B in "$HOME_DIR"/.pi.pre-persist-*; do
            [ -d "$B" ] || continue
            if command -v rsync >/dev/null 2>&1; then
                rsync -a "$B/agent/sessions/" "$TARGET/agent/sessions/" 2>/dev/null || true
            else
                cp -a "$B/agent/sessions/." "$TARGET/agent/sessions/" 2>/dev/null || true
            fi
            echo "🔁 Folded newer session files from $B into $TARGET (backup kept — remove manually when happy)"
        done
        exit 0
    fi
    echo "❌ $PI_DIR is a symlink to '$CURRENT' (not '$TARGET') — refusing to touch it."
    exit 1
fi

# ── Cases 2-4 ────────────────────────────────────────────────────────────────
MODE=""
if ! has_data "$PI_DIR"; then
    if has_data "$TARGET"; then
        MODE="restore"
    else
        MODE="seed"
    fi
else
    if has_data "$TARGET"; then
        MODE="merge"
    else
        MODE="migrate"
    fi
fi

echo "Pi state : $PI_DIR ($(count_sessions "$PI_DIR") sessions, $(du -sh "$PI_DIR" 2>/dev/null | cut -f1))"
echo "Workspace: $WS"
echo "Target   : $TARGET"

mkdir -p "$TARGET"

if [ "$MODE" != "restore" ] && [ "$MODE" != "seed" ]; then
    echo "📦 Copying $MODE -> $TARGET ..."
    if command -v rsync >/dev/null 2>&1; then
        rsync -a "$PI_DIR/" "$TARGET/"
    else
        cp -a "$PI_DIR/." "$TARGET/"
    fi
fi

# Swap the home directory for the workspace symlink. Nothing is deleted:
# the original is renamed aside so it can always be restored.
BACKUP="$PI_DIR.pre-persist-$(date +%Y%m%d-%H%M%S)"
if [ -e "$PI_DIR" ]; then
    mv "$PI_DIR" "$BACKUP"
    echo "🗄️  Original moved aside: $BACKUP"
fi
ln -s "$TARGET" "$PI_DIR"

# Verify the link resolves to real Pi state.
if [ ! -e "$PI_DIR/agent" ]; then
    echo "❌ Symlink created but $PI_DIR/agent does not resolve — rolling back."
    rm "$PI_DIR"
    [ -e "$BACKUP" ] && mv "$BACKUP" "$PI_DIR"
    exit 1
fi

# Keep credentials + session history out of the repo (mandatory).
GITIGNORE="$WS/.gitignore"
if [ -f "$GITIGNORE" ] && ! grep -qx ".pi_persist/" "$GITIGNORE"; then
    printf '\n# Pi coding-agent state (sessions/auth) — lives in the container, never committed\n.pi_persist/\n' >> "$GITIGNORE"
    echo "🚫 Added .pi_persist/ to $GITIGNORE (contains auth.json — never commit)"
fi

cat <<EOF

✅ Pi state is now persisted at $TARGET ($MODE, $(count_sessions "$TARGET") sessions)
   $PI_DIR -> $TARGET

   - Launch pi as usual: no special command, flags or env vars needed.
   - Survives devcontainer rebuilds (the workspace volume keeps .pi_persist).
   - After a rebuild, re-run this script (or rely on postCreateCommand) to
     restore the symlink automatically.
   - Undo: rm $PI_DIR && mv $BACKUP $PI_DIR
EOF
