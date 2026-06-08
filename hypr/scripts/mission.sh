#!/bin/bash

# Prevent spam triggering
LOCKFILE="/tmp/hymission.lock"

if [ -f "$LOCKFILE" ]; then
    exit 0
fi

touch "$LOCKFILE"

# Small delay → lets Hyprland + Caelestia settle
sleep 0.08

hyprctl dispatch hymission:toggle onlycurrentworkspace

# Cooldown (prevents flicker spam)
sleep 0.2
rm -f "$LOCKFILE"