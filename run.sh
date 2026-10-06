#!/usr/bin/env bash
set -e

PORT=${PORT:-8905}
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "[*] Starting Reelsmax Server on port $PORT..."
python3 server.py &
SERVER_PID=$!

echo "[*] Server PID: $SERVER_PID"
sleep 1

if [ "$1" == "--browser" ] || [ "$1" == "-b" ]; then
    echo "[*] Launching Chromium in Wall mode on DISPLAY=:0..."
    DISPLAY=:0 chromium \
        --app="http://127.0.0.1:$PORT/" \
        --window-size=1280,800 \
        --window-position=0,0 \
        --no-first-run \
        --no-default-browser-check \
        --autoplay-policy=no-user-gesture-required \
        --user-data-dir="/home/bsmt-pc/snap/chromium/common/reelsmax-wall-profile" &
fi

wait $SERVER_PID
