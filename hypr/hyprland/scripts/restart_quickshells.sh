#!/usr/bin/env bash
set -euo pipefail

export QML2_IMPORT_PATH=/home/aashiqed/.local/share/caelestia-shell/build/qml
E4_CMD='qs -c ii'
CAELESTIA_CMD='qs -c /home/aashiqed/.local/share/caelestia-shell'

# Stop existing quickshell instances for a clean restart.
pkill -f "qs -c ii" || true
pkill -f "qs -c /home/aashiqed/.local/share/caelestia-shell" || true
pkill -f nwg-dock-hyprland || true
sleep 0.4

# Start e4 first, then Caelestia with a short delay to reduce startup races.
nohup $E4_CMD > /tmp/qs-ii.log 2>&1 &
sleep 0.7
nohup $CAELESTIA_CMD > /tmp/caelestia-shell.log 2>&1 &

# Launch custom nwg-dock with macOS styling and autohide
# if command -v nwg-dock-hyprland > /dev/null 2>&1; then
#   sleep 0.3
#   nohup nwg-dock-hyprland -d -o eDP-1 -l top -hl top -hd 0 > /tmp/nwg-dock.log 2>&1 &
# fi

# Keep clipboard history watchers alive after manual shell restarts.
~/.config/hypr/hyprland/scripts/start_clipboard_watchers.sh
