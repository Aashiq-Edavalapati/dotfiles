#!/usr/bin/env bash
set -euo pipefail

# Start text watcher once
if ! pgrep -af "wl-paste --type text --watch" >/dev/null; then
  nohup wl-paste --type text --watch bash -lc 'cliphist store && qs ipc --any-display -c ii call cliphistService update' >/tmp/wl-paste-text.log 2>&1 &
fi

# Start image watcher once
if ! pgrep -af "wl-paste --type image --watch" >/dev/null; then
  nohup wl-paste --type image --watch bash -lc 'cliphist store && qs ipc --any-display -c ii call cliphistService update' >/tmp/wl-paste-image.log 2>&1 &
fi
