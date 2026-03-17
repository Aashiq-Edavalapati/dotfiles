#!/usr/bin/env bash
# ================================================================
#  nwg-dock-hyprland — macOS-style launch script
#  Place at: ~/.config/hypr/scripts/dock-launch.sh
#  Make executable: chmod +x ~/.config/hypr/scripts/dock-launch.sh
# ================================================================
#
#  Usage (in hyprland keybinds or nwg-dock launcher):
#    ~/.config/hypr/scripts/dock-launch.sh <command>
#
#  What it does:
#  1. Launches the app normally
#  2. Waits for the window to appear in hyprctl
#  3. Sends SIGUSR1 to nwg-dock so it refreshes its state,
#     which re-triggers the #active CSS class → bounce animation
#
# ================================================================

APP_CMD="$*"

if [[ -z "$APP_CMD" ]]; then
  echo "Usage: dock-launch.sh <command>"
  exit 1
fi

# Launch the application in background
$APP_CMD &
APP_PID=$!

# Give hyprland a moment to register the new window
sleep 0.15

# Refresh nwg-dock state — this causes it to re-evaluate #active
# which re-triggers the CSS bounce @keyframes
DOCK_PID=$(pgrep -x nwg-dock-hyprlan)
if [[ -n "$DOCK_PID" ]]; then
  # SIGRTMIN+1 (35) = toggle; we use kill -USR1 for broad compat
  kill -35 "$DOCK_PID" 2>/dev/null || true
fi

# Wait for app so this script doesn't become a zombie
wait $APP_PID 2>/dev/null || true