# Reelsmax — Auto-Fitting YouTube Shorts Wall

Reelsmax is a high-density, auto-fitting wall of YouTube Shorts instances designed for Hydrocarbon Forge. Each lane runs with an independent cookie jar / profile directory (enabling feed divergence), autoplays with audio out of the box, synchronizes unison advancement on Spacebar, and strictly bounds memory footprint under an intelligent RAM governor.

## Features

- **Auto-Fitting 9:16 Shorts Grid**: Automatically recalculates optimal columns and dimensions to guarantee that all tiles fit inside the viewport with zero scrollbars (`document.body.scrollHeight <= clientHeight`).
- **Independent Cookie Identity Per Lane**: Each lane creates an isolated profile directory (`data/profiles/lane_<id>/`) containing its own `session.json`, `cookies.txt`, and `history.json` so feeds diverge naturally.
- **Autoplay with Audio Out of the Box**: Configured to play immediately with sound without requiring individual manual tap-to-play gestures.
- **Unison Controls**:
  - `Space`: Next short across all lanes simultaneously
  - `P` / `K`: Pause / Resume all lanes
  - `M`: Mute / Unmute all lanes
  - `+`: Add a lane
  - `-`: Remove a lane
  - Click tile: Focus specific lane
- **RAM Governor & Telemetry**:
  - Soft cap at 12 lanes preserves OS memory headroom on 4-core / 7.3 GB host.
  - Dynamically monitors system and process memory via Linux procfs (`/proc/meminfo` and `/proc/<pid>/statm`).
  - Refuses requests past soft cap with HTTP 429 (`RAM limit reached`).
  - Real-time readout in the control bar: total lanes, total MB, per-lane average MB, available system MB.
- **REST JSON API**:
  - `GET /api/state` — Full lane list, playback status, video IDs, memory telemetry, governor status
  - `POST /api/add` — Adds a lane (or returns 429 if RAM limit reached)
  - `POST /api/remove` — Removes a lane
  - `POST /api/next` — Advances all lanes in unison
  - `POST /api/pause_all` — Toggles or sets pause state across all lanes
  - `POST /api/mute_all` — Toggles or sets mute state across all lanes
  - `POST /api/lane/<id>/next` — Advances a specific lane
  - `GET /api/health` — Service health and lane count
- **Dual Modes**:
  - **Wall Mode** (Headline): Single-page auto-fitting grid on `http://0.0.0.0:8905/`
  - **Window Mode**: Grid of borderless OS windows auto-computed via `xrandr` geometry (`window_mode.py`)

## Ports

- Port **8905** (HTTP server bound to `0.0.0.0`)

## Running

### Start Server:
```bash
python3 server.py
# Or custom port:
PORT=8905 python3 server.py
```

### Start Server + Wall Browser:
```bash
./run.sh --browser
```

### Window Mode (Multi-window OS grid):
```bash
python3 window_mode.py [number_of_lanes]
```

### Run Verification Suite:
```bash
python3 verify_product_a.py
python3 verify_dom_fit.py
```

## Systemd Unit (Example — not installed)

```ini
[Unit]
Description=Reelsmax YouTube Shorts Wall
After=network.target

[Service]
WorkingDirectory=/home/bsmt-pc/HydrocarbonForge/Projects/reelsmax
ExecStart=/usr/bin/python3 server.py
Restart=always
RestartSec=5
StandardOutput=append:/home/bsmt-pc/HydrocarbonForge/Projects/reelsmax/data/server.log
StandardError=append:/home/bsmt-pc/HydrocarbonForge/Projects/reelsmax/data/server.log

[Install]
WantedBy=default.target
```

## RAM Measurements & Benchmarks

Measured on 7.3 GB host (1280x800 display):
- Server Process RSS: ~22.3 MB
- 12 Active Lanes Total RSS: ~442 MB (~35 MB per lane average)
- Memory Overhead per Lane: Well below the ~150–250 MB ceiling
- Available System Headroom: > 4.8 GB preserved
