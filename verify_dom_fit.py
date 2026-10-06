#!/usr/bin/env python3
"""
DOM Proof Script:
Tests BOTH 6 lanes and 12 lanes.
Connects to headless Chromium via CDP and evaluates:
document.body.scrollHeight <= document.documentElement.clientHeight
window.innerHeight
for both 6 and 12 lanes on 1280x800 viewport.
"""

import os
import sys
import time
import json
import urllib.request
import subprocess
import websockets
import asyncio

async def evaluate_js(ws_url, expr):
    async with websockets.connect(ws_url) as ws:
        msg = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expr,
                "returnByValue": True
            }
        }
        await ws.send(json.dumps(msg))
        res = await ws.recv()
        data = json.loads(res)
        return data.get("result", {}).get("result", {}).get("value")

async def test_viewport_fit_both():
    print("[*] Launching Chromium headless at 1280x800 with CDP...")
    prof = "/home/bsmt-pc/snap/chromium/common/test-cdp-dom"
    os.makedirs(prof, exist_ok=True)
    proc = subprocess.Popen([
        "chromium",
        "--headless=new",
        "--remote-debugging-port=9223",
        "--window-size=1280,800",
        f"--user-data-dir={prof}",
        "http://127.0.0.1:8905/"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        await asyncio.sleep(3)
        # Find page target
        targets_req = urllib.request.urlopen("http://127.0.0.1:9223/json")
        targets = json.loads(targets_req.read().decode())
        page_target = None
        for t in targets:
            if t.get("type") == "page":
                page_target = t
                break

        ws_url = page_target["webSocketDebuggerUrl"]
        print(f"[*] Connected to CDP websocket: {ws_url}")

        # Part 1: Test 6 lanes
        print("\n--- TEST A: 6 LANES DOM FIT ---")
        sh6 = await evaluate_js(ws_url, "document.body.scrollHeight")
        ch6 = await evaluate_js(ws_url, "document.documentElement.clientHeight")
        ih6 = await evaluate_js(ws_url, "window.innerHeight")
        tiles6 = await evaluate_js(ws_url, "document.querySelectorAll('.lane-tile').length")
        has_scroll6 = await evaluate_js(ws_url, "document.body.scrollHeight > document.documentElement.clientHeight")

        print(f"  Tile Count: {tiles6}")
        print(f"  document.body.scrollHeight: {sh6}px")
        print(f"  document.documentElement.clientHeight: {ch6}px")
        print(f"  window.innerHeight: {ih6}px")
        print(f"  Has Vertical Scrollbar: {has_scroll6}")
        assert sh6 <= ch6, f"6-lane DOM Proof Failed: scrollHeight ({sh6}) > clientHeight ({ch6})"
        assert not has_scroll6, "6-lane page has vertical scrollbar!"
        print(f"  -> PROOF VERIFIED FOR 6 LANES: scrollHeight ({sh6}) <= clientHeight ({ch6}) with 0 scrollbars!")

        # Part 2: Scale up to 12 lanes via API
        print("\n--- TEST B: 12 LANES DOM FIT ---")
        for _ in range(6):
            req = urllib.request.Request("http://127.0.0.1:8905/api/add", data=b"{}", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as resp:
                pass
        # Trigger reflow in client
        await evaluate_js(ws_url, "fetchState()")
        await asyncio.sleep(2)

        sh12 = await evaluate_js(ws_url, "document.body.scrollHeight")
        ch12 = await evaluate_js(ws_url, "document.documentElement.clientHeight")
        ih12 = await evaluate_js(ws_url, "window.innerHeight")
        tiles12 = await evaluate_js(ws_url, "document.querySelectorAll('.lane-tile').length")
        has_scroll12 = await evaluate_js(ws_url, "document.body.scrollHeight > document.documentElement.clientHeight")

        print(f"  Tile Count: {tiles12}")
        print(f"  document.body.scrollHeight: {sh12}px")
        print(f"  document.documentElement.clientHeight: {ch12}px")
        print(f"  window.innerHeight: {ih12}px")
        print(f"  Has Vertical Scrollbar: {has_scroll12}")
        assert sh12 <= ch12, f"12-lane DOM Proof Failed: scrollHeight ({sh12}) > clientHeight ({ch12})"
        assert not has_scroll12, "12-lane page has vertical scrollbar!"
        print(f"  -> PROOF VERIFIED FOR 12 LANES: scrollHeight ({sh12}) <= clientHeight ({ch12}) with 0 scrollbars!")

    finally:
        proc.terminate()
        proc.wait()
        subprocess.run(f"rm -rf {prof}", shell=True)

if __name__ == "__main__":
    asyncio.run(test_viewport_fit_both())
