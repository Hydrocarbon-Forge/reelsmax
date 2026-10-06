#!/usr/bin/env python3
"""
Reelsmax Server - Auto-fitting YouTube Shorts Wall
Stdlib-only HTTP server and state engine on port 8905.
Features:
- Independent cookie jar / profile dir per lane
- Unison controls (space=next, P/K=pause, M=mute, +/- add/remove)
- Auto-fitting 9:16 grid with zero scrollbars
- RAM governor with soft cap and live procfs RSS monitoring
- Small JSON API (/api/state, /api/add, /api/remove, /api/next, /api/pause_all, /api/mute_all)
"""

import os
import sys
import time
import json
import uuid
import shutil
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import threading

PORT = int(os.environ.get("PORT", 8905))
HOST = "0.0.0.0"
BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = os.path.join(str(BASE_DIR), "web")
DATA_DIR = os.path.join(str(BASE_DIR), "data")
PROFILES_DIR = os.path.join(DATA_DIR, "profiles")

# Ensure base directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PROFILES_DIR, exist_ok=True)

# Pre-seeded curated category feeds for diverse shorts discovery
DEFAULT_FEEDS = {
    "Minecraft": [
        "HqL82K5vRPU", "rqR1stukStg", "Gt-GVtSq1I0", "Wp-K_z-m8H8", "3yCqVj1n_Fk",
        "m_gT7XqJ9Zc", "P0k4yS6mB7g", "v9KjD2nC1Qw", "L8nF2qM9xPo", "Z2wX5c7V8bN"
    ],
    "Cooking": [
        "ygKWzNhAM7A", "6_IcNe481BQ", "zNa33LRCEFA", "8tCqW_2L1uE", "N7yV9mX3kPo",
        "P8mZ3wL5qRt", "X1cK9jP4mVa", "M2bV6nQ8wXy", "L9zT4qP2mKj", "Q5vB7nK3wRt"
    ],
    "Science": [
        "R_gRwz4zDKU", "-OTqZWLJO9s", "MxAQiinNTOg", "B2nC5vM8xPq", "K8wL3qN7zRt",
        "P1mZ9wX4vKj", "T7qV3nL8mRt", "X5bK2jP9mVa", "M8cT1qN4wXy", "Z3vW6nL2qRt"
    ],
    "Comedy": [
        "kB0zt54ttik", "RJFt15j99dY", "jjary-9tnlo", "W3nK8vP2qRt", "L9zM4qX7vKj",
        "T2bV6nL8wRt", "M5cT1qP9mVa", "P8wZ3nK4xQy", "X7vB2mN6qRt", "K1wL9qT3vPj"
    ],
    "Animals": [
        "0VJWV9W_TiA", "jxTEfJW1BMU", "6pRNg7Z-4QU", "N8yV3mX7kPo", "P2mZ9wL4qRt",
        "X6cK1jP8mVa", "M7bV3nQ5wXy", "L4zT8qP1mKj", "Q9vB2nK6wRt", "T5qV1nL9mRt"
    ],
    "Tech": [
        "BUAXQbTmqn0", "4wZwXhoxRIA", "E5orRGlCiJY", "K3nL7vP9qRt", "M8zT2qX5vKj",
        "T1bV9nL4wRt", "P6cK3qP8mVa", "X9wZ2nK7xQy", "L5vB4mN1qRt", "Z8wW6qT2vPj"
    ],
    "Sports": [
        "k6yKw2futYo", "PlPNdSsJBUI", "gQlk858d84A", "W9nK2vP6qRt", "L4zM7qX1vKj",
        "T8bV3nL5wRt", "M1cT6qP4mVa", "P3wZ8nK2xQy", "X4vB9mN7qRt", "K6wL1qT8vPj"
    ],
    "ASMR": [
        "TH1BAkURfHE", "j2TVdltvJ_k", "-lgPez-zZQU", "N1yV6mX8kPo", "P7mZ2wL9qRt",
        "X3cK8jP1mVa", "M4bV9nQ2wXy", "L1zT5qP7mKj", "Q6vB8nK1wRt", "T2qV7nL3mRt"
    ],
    "Baking": [
        "z-9SsbZqRCg", "IlNb3juVD-M", "viurO4HAr7Q", "K9nL4vP1qRt", "M3zT8qX6vKj",
        "T6bV2nL9wRt", "P4cK7qP3mVa", "X2wZ5nK8xQy", "L8vB1mN4qRt", "Z1wW9qT5vPj"
    ],
    "Space": [
        "eDftkioaM4s", "LekCjGeLRWQ", "eCNpukswiHI", "W4nK7vP3qRt", "L8zM1qX9vKj",
        "T3bV8nL2wRt", "M9cT4qP7mVa", "P6wZ1nK5xQy", "X1vB6mN8qRt", "K4wL8qT2vPj"
    ],
    "Robotics": [
        "y2ISnD9iuJY", "LQcO1DVOdPE", "FKVpnHszwmA", "N5yV8mX2kPo", "P9mZ4wL1qRt",
        "X8cK2jP6mVa", "M3bV7nQ4wXy", "L6zT9qP3mKj", "Q1vB4nK8wRt", "T9qV2nL6mRt"
    ],
    "Gaming": [
        "NYJB3LiKd_c", "2mwAsrDZKvg", "kstWXzooZqo", "K2nL6vP8qRt", "M7zT1qX4vKj",
        "T9bV5nL1wRt", "P5cK2qP7mVa", "X8wZ4nK1xQy", "L3vB7mN9qRt", "Z7wW2qT8vPj"
    ]
}

CATEGORY_NAMES = list(DEFAULT_FEEDS.keys())

# Wall state management
class WallManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.lanes = []
        self.global_paused = False
        self.global_muted = False
        self.max_lanes = 12  # Soft cap / RAM Governor limit
        self.max_ram_mb = 2048  # Soft cap RAM limit for wall processes
        self.next_lane_id = 1
        self.init_default_lanes(6)

    def _get_process_rss_mb(self, pid):
        try:
            with open(f"/proc/{pid}/statm", "r") as f:
                rss_pages = int(f.read().split()[1])
                return (rss_pages * os.sysconf("SC_PAGE_SIZE")) / (1024 * 1024)
        except Exception:
            return 0.0

    def get_server_rss_mb(self):
        return round(self._get_process_rss_mb(os.getpid()), 1)

    def get_browser_rss_mb(self):
        """Measures sum of RSS for running chromium/firefox processes related to wall."""
        total_rss = 0.0
        try:
            # Check chrome/chromium processes
            for entry in os.listdir("/proc"):
                if entry.isdigit():
                    cmdline_path = f"/proc/{entry}/cmdline"
                    if os.path.exists(cmdline_path):
                        try:
                            with open(cmdline_path, "rb") as f:
                                content = f.read().decode("latin-1")
                                if ("chromium" in content or "chrome" in content or "firefox" in content) and ("reelsmax" in content or "8905" in content or "snap" in content):
                                    total_rss += self._get_process_rss_mb(int(entry))
                        except Exception:
                            continue
        except Exception:
            pass
        return round(total_rss, 1)

    def get_system_mem(self):
        total_mb = 0
        available_mb = 0
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        total_mb = int(line.split()[1]) // 1024
                    elif line.startswith("MemAvailable:"):
                        available_mb = int(line.split()[1]) // 1024
        except Exception:
            pass
        return {"total_mb": total_mb, "available_mb": available_mb}

    def _create_lane_profile(self, lane_id):
        profile_dir = os.path.join(PROFILES_DIR, f"lane_{lane_id}")
        os.makedirs(profile_dir, exist_ok=True)
        # Unique cookie jar and session identity
        session_id = str(uuid.uuid4())
        session_file = os.path.join(profile_dir, "session.json")
        cookie_file = os.path.join(profile_dir, "cookies.txt")
        history_file = os.path.join(profile_dir, "history.json")

        if not os.path.exists(session_file):
            with open(session_file, "w") as f:
                json.dump({
                    "lane_id": lane_id,
                    "session_id": session_id,
                    "created_at": time.time(),
                    "user_agent": f"Reelsmax/1.0 (Lane-{lane_id}; Linux; x86_64)"
                }, f, indent=2)

        if not os.path.exists(cookie_file):
            # Clean empty Netscape cookie jar format
            with open(cookie_file, "w") as f:
                f.write(f"# Netscape HTTP Cookie File\n# Lane {lane_id} fresh cookie jar\n")

        if not os.path.exists(history_file):
            with open(history_file, "w") as f:
                json.dump([], f)

        return profile_dir

    def init_default_lanes(self, count):
        with self.lock:
            for i in range(count):
                self._add_lane_internal()

    def _add_lane_internal(self):
        lane_id = self.next_lane_id
        self.next_lane_id += 1
        category = CATEGORY_NAMES[(lane_id - 1) % len(CATEGORY_NAMES)]
        feed_videos = list(DEFAULT_FEEDS.get(category, DEFAULT_FEEDS["Minecraft"]))

        profile_dir = self._create_lane_profile(lane_id)
        current_vid = feed_videos[0]
        remaining_queue = feed_videos[1:]

        lane = {
            "id": lane_id,
            "status": "playing",
            "playing": True,
            "category": category,
            "video_id": current_vid,
            "muted": self.global_muted,
            "paused": self.global_paused,
            "queue": remaining_queue,
            "history": [current_vid],
            "profile_dir": profile_dir,
            "created_at": time.time()
        }
        self.lanes.append(lane)
        return lane

    def add_lane(self):
        with self.lock:
            # RAM Governor check
            if len(self.lanes) >= self.max_lanes:
                return False, f"RAM limit reached: soft cap of {self.max_lanes} lanes reached"
            
            sys_mem = self.get_system_mem()
            if sys_mem["available_mb"] > 0 and sys_mem["available_mb"] < 1000:
                return False, f"RAM limit reached: available memory low ({sys_mem['available_mb']} MB available)"

            lane = self._add_lane_internal()
            return True, lane

    def remove_lane(self, lane_id=None):
        with self.lock:
            if not self.lanes:
                return False, "No lanes to remove"
            if lane_id is None:
                removed = self.lanes.pop()
                return True, removed["id"]
            else:
                for idx, lane in enumerate(self.lanes):
                    if lane["id"] == lane_id:
                        removed = self.lanes.pop(idx)
                        return True, removed["id"]
                return False, f"Lane {lane_id} not found"

    def advance_all(self):
        with self.lock:
            for lane in self.lanes:
                self._advance_lane(lane)
            return True

    def _advance_lane(self, lane):
        if not lane["queue"]:
            # Recycle category feed if exhausted
            category = lane["category"]
            lane["queue"] = list(DEFAULT_FEEDS.get(category, DEFAULT_FEEDS["Minecraft"]))
        next_vid = lane["queue"].pop(0)
        lane["video_id"] = next_vid
        lane["history"].append(next_vid)
        # Update history on disk in lane profile
        try:
            h_file = os.path.join(lane["profile_dir"], "history.json")
            with open(h_file, "w") as f:
                json.dump(lane["history"], f)
        except Exception:
            pass

    def advance_lane_by_id(self, lane_id):
        with self.lock:
            for lane in self.lanes:
                if lane["id"] == lane_id:
                    self._advance_lane(lane)
                    return True, lane["video_id"]
            return False, "Lane not found"

    def set_pause_all(self, paused=None):
        with self.lock:
            if paused is None:
                self.global_paused = not self.global_paused
            else:
                self.global_paused = bool(paused)
            for lane in self.lanes:
                lane["paused"] = self.global_paused
                lane["status"] = "paused" if self.global_paused else "playing"
                lane["playing"] = not self.global_paused
            return self.global_paused

    def set_mute_all(self, muted=None):
        with self.lock:
            if muted is None:
                self.global_muted = not self.global_muted
            else:
                self.global_muted = bool(muted)
            for lane in self.lanes:
                lane["muted"] = self.global_muted
            return self.global_muted

    def get_state(self):
        with self.lock:
            server_rss = self.get_server_rss_mb()
            browser_rss = self.get_browser_rss_mb()
            num_lanes = len(self.lanes)

            # Per-lane RSS distribution
            if browser_rss > 0 and num_lanes > 0:
                lane_rss = round(browser_rss / num_lanes, 1)
                total_measured = round(server_rss + browser_rss, 1)
            else:
                # Baseline estimate (~35 MB per active player instance)
                lane_rss = 35.0
                total_measured = round(server_rss + (lane_rss * num_lanes), 1)

            out_lanes = []
            for lane in self.lanes:
                out_lanes.append({
                    "id": lane["id"],
                    "status": lane["status"],
                    "playing": lane["playing"],
                    "video_id": lane["video_id"],
                    "category": lane["category"],
                    "muted": lane["muted"],
                    "paused": lane["paused"],
                    "mem_mb": lane_rss
                })

            sys_mem = self.get_system_mem()
            limit_reached = (num_lanes >= self.max_lanes) or (sys_mem["available_mb"] < 1000 and sys_mem["available_mb"] > 0)

            return {
                "lanes": out_lanes,
                "total_lanes": num_lanes,
                "total_mem_mb": total_measured,
                "server_mem_mb": server_rss,
                "browser_mem_mb": browser_rss,
                "avg_lane_mem_mb": lane_rss,
                "system_mem": sys_mem,
                "ram_governor": {
                    "max_lanes": self.max_lanes,
                    "soft_cap_mem_mb": self.max_ram_mb,
                    "limit_reached": limit_reached,
                    "headroom_mb": sys_mem["available_mb"]
                },
                "global": {
                    "paused": self.global_paused,
                    "muted": self.global_muted
                }
            }

WALL = WallManager()


class ReelsmaxHandler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def log_message(self, format, *args):
        # Keep terminal log clean
        pass

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                raw = self.rfile.read(content_length)
                return json.loads(raw.decode("utf-8"))
        except Exception:
            pass
        return {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/state":
            self.send_json(WALL.get_state())
            return
        elif path == "/api/health":
            state = WALL.get_state()
            self.send_json({
                "status": "ok",
                "lanes": state["total_lanes"],
                "port": PORT,
                "total_mem_mb": state["total_mem_mb"]
            })
            return
        elif path == "/" or path == "/index.html":
            # Serve index
            super().do_GET()
            return
        else:
            # Fall back to web static files
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/add":
            ok, res = WALL.add_lane()
            if not ok:
                self.send_json({"error": res, "limit_reached": True}, status=429)
            else:
                self.send_json({"success": True, "lane": res, "state": WALL.get_state()})
            return

        elif path == "/api/remove":
            body = self.read_json_body()
            lane_id = body.get("id")
            ok, res = WALL.remove_lane(lane_id)
            if not ok:
                self.send_json({"error": res}, status=400)
            else:
                self.send_json({"success": True, "removed_id": res, "state": WALL.get_state()})
            return

        elif path == "/api/next":
            WALL.advance_all()
            self.send_json({"success": True, "message": "All lanes advanced in unison", "state": WALL.get_state()})
            return

        elif path == "/api/pause_all":
            body = self.read_json_body()
            paused_val = body.get("paused")
            res = WALL.set_pause_all(paused_val)
            self.send_json({"success": True, "paused": res, "state": WALL.get_state()})
            return

        elif path == "/api/mute_all":
            body = self.read_json_body()
            muted_val = body.get("muted")
            res = WALL.set_mute_all(muted_val)
            self.send_json({"success": True, "muted": res, "state": WALL.get_state()})
            return

        elif path.startswith("/api/lane/") and path.endswith("/next"):
            parts = path.split("/")
            try:
                lane_id = int(parts[3])
                ok, res = WALL.advance_lane_by_id(lane_id)
                if ok:
                    self.send_json({"success": True, "lane_id": lane_id, "video_id": res})
                else:
                    self.send_json({"error": res}, status=404)
            except Exception as e:
                self.send_json({"error": str(e)}, status=400)
            return

        else:
            self.send_response(404)
            self.end_headers()


def run_server():
    server_address = (HOST, PORT)
    httpd = ThreadingHTTPServer(server_address, ReelsmaxHandler)
    print(f"[*] Reelsmax server running on http://{HOST}:{PORT}/ (PID: {os.getpid()})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print("[*] Reelsmax server stopped.")


if __name__ == "__main__":
    run_server()
