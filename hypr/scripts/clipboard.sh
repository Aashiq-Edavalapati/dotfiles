#!/usr/bin/env bash
# Caelestia Clipboard Manager launcher
# Toggles the GUI: opens if not running, closes if already open.
# Uses a PID file so the check is instant and unambiguous.

SCRIPT="$HOME/.config/hypr/scripts/clipboard_manager.py"
PIDFILE="/tmp/caelestia_clipboard.pid"

# If PID file exists and the process is still alive → kill and exit
if [[ -f "$PIDFILE" ]]; then
    pid=$(< "$PIDFILE")
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        rm -f "$PIDFILE"
        exit 0
    else
        # Stale PID file — process already dead, clean up and fall through
        rm -f "$PIDFILE"
    fi
fi

# Launch, write PID, and disown so the shell exits immediately
python3 "$SCRIPT" &
echo $! > "$PIDFILE"
disown