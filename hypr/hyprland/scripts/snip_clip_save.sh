#!/usr/bin/env bash
set -euo pipefail

# Avoid nested region pickers.
if pgrep -x slurp >/dev/null; then
  exit 0
fi

out_dir="$HOME/Screenshots"
mkdir -p "$out_dir"

file="$out_dir/Screenshot_$(date '+%Y-%m-%d_%H.%M.%S').png"
region="$(slurp)"

[ -n "$region" ] || exit 0

grim -g "$region" "$file"
wl-copy < "$file"
