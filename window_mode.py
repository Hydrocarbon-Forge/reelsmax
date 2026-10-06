#!/usr/bin/env python3
"""
Reelsmax Window Mode Launcher
Calculates screen geometry via xrandr, divides the screen into an auto-computed
grid of borderless OS windows (9:16 Shorts aspect) with a few-px gap, and
launches independent browser instances per lane.
"""

import os
import sys
import re
import math
import subprocess
import time

def get_screen_geometry():
    """Reads actual mode from xrandr."""
    try:
        out = subprocess.check_output("DISPLAY=:0 xrandr", shell=True).decode()
        match = re.search(r"(\d+)x(\d+)\s+[\d\.]+\*\+", out)
        if match:
            return int(match.group(1)), int(match.group(2))
        match = re.search(r"current\s+(\d+)\s+x\s+(\d+)", out)
        if match:
            return int(match.group(1)), int(match.group(2))
    except Exception as e:
        print(f"Warning: Failed to query xrandr ({e}), defaulting to 1280x800")
    return 1280, 800

def compute_window_grid(num_lanes, screen_w, screen_h, gap=6):
    """Computes (x, y, w, h) for each lane window."""
    aspect = 9 / 16
    best_cols = 1
    best_w, best_h = 0, 0
    max_area = 0

    for c in range(1, num_lanes + 1):
        r = math.ceil(num_lanes / c)
        max_w = (screen_w - (c - 1) * gap) / c
        max_h = (screen_h - (r - 1) * gap) / r

        w = max_w
        h = w / aspect
        if h > max_h:
            h = max_h
            w = h * aspect

        area = w * h * num_lanes
        if area > max_area:
            max_area = area
            best_cols = c
            best_w = int(w)
            best_h = int(h)

    cols = best_cols
    rows = math.ceil(num_lanes / cols)
    total_grid_w = cols * best_w + (cols - 1) * gap
    total_grid_h = rows * best_h + (rows - 1) * gap
    offset_x = (screen_w - total_grid_w) // 2
    offset_y = (screen_h - total_grid_h) // 2

    windows = []
    for i in range(num_lanes):
        col = i % cols
        row = i // cols
        x = offset_x + col * (best_w + gap)
        y = offset_y + row * (best_h + gap)
        windows.append((x, y, best_w, best_h))
    return windows

def launch_window_mode(num_lanes=6, base_url="http://localhost:8905"):
    w, h = get_screen_geometry()
    print(f"[*] Detected screen geometry: {w}x{h}")
    grid = compute_window_grid(num_lanes, w, h)
    print(f"[*] Computed {len(grid)} window positions:")

    procs = []
    for idx, (win_x, win_y, win_w, win_h) in enumerate(grid):
        lane_id = idx + 1
        prof_dir = f"/home/bsmt-pc/snap/chromium/common/lane-win-{lane_id}"
        os.makedirs(prof_dir, exist_ok=True)
        print(f"  Lane {lane_id}: pos=({win_x},{win_y}) size={win_w}x{win_h}")

        cmd = [
            "chromium",
            f"--user-data-dir={prof_dir}",
            f"--window-position={win_x},{win_y}",
            f"--window-size={win_w},{win_h}",
            "--no-first-run",
            "--no-default-browser-check",
            "--autoplay-policy=no-user-gesture-required",
            f"--app={base_url}/#lane-{lane_id}"
        ]
        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs.append(p)
        time.sleep(0.3)

    print(f"[*] Launched {len(procs)} lane windows. Press Ctrl+C to close.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[*] Closing window mode...")
        for p in procs:
            p.terminate()

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    launch_window_mode(count)
