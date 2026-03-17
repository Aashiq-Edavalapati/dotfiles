#!/bin/bash

THRESHOLD=40
WIDTH=1920   # <-- set your screen width
EDGE_DELAY_MS=100   # delay in milliseconds (0.35s)

COOLDOWN=0
EDGE_START=0
EDGE_SIDE=""

while true; do
    POS=$(hyprctl cursorpos)
    X=$(echo $POS | awk '{print int($1)}')

    # detect dragging (floating OR moving)
    DRAGGING=$(hyprctl activewindow -j | jq '.floating')

    if [ "$DRAGGING" != "true" ]; then
        COOLDOWN=0
        EDGE_START=0
        EDGE_SIDE=""
        sleep 0.05
        continue
    fi

    CURRENT_TIME=$(date +%s%3N)

    # LEFT EDGE
    if [ "$X" -le "$THRESHOLD" ]; then
        if [ "$EDGE_SIDE" != "left" ]; then
            EDGE_SIDE="left"
            EDGE_START=$CURRENT_TIME
        fi

        if [ $((CURRENT_TIME - EDGE_START)) -ge $EDGE_DELAY_MS ] && [ "$COOLDOWN" -eq 0 ]; then
            hyprctl dispatch workspace -1
            COOLDOWN=1
            EDGE_START=$CURRENT_TIME
        fi

    # RIGHT EDGE
    elif [ "$X" -ge $((WIDTH - THRESHOLD)) ]; then
        if [ "$EDGE_SIDE" != "right" ]; then
            EDGE_SIDE="right"
            EDGE_START=$CURRENT_TIME
        fi

        if [ $((CURRENT_TIME - EDGE_START)) -ge $EDGE_DELAY_MS ] && [ "$COOLDOWN" -eq 0 ]; then
            hyprctl dispatch workspace +1
            COOLDOWN=1
            EDGE_START=$CURRENT_TIME
        fi

    else
        EDGE_SIDE=""
        EDGE_START=0
        COOLDOWN=0
    fi

    sleep 0.03
done