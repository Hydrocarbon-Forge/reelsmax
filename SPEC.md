# Reelsmax — build spec

Requested by Nathan 2026-10-05. Build everything in this directory
(`~/HydrocarbonForge/Projects/reelsmax/`). Two products:

**A. Reelsmax** — an auto-fitting wall of YouTube Shorts instances that
play with audio, advance in unison on spacebar, and stay RAM-bounded.
**B. Forge Console "Projects" tab** — a new tab on the existing console
(see `CONSOLE-PROJECTS.md` in this dir).

This machine is the runtime host: build it to run HERE and verify it HERE.

────────────────────────────────────────────────────
## Verified environment facts (do not re-derive, just use)

- Host: Linux, 4 CPU cores, **7.3 GB RAM total** (~4.9 GB available).
  This is a hard constraint — the wall must work when many lanes are open.
- X display `:0` is running, active mode **1280x800** (check
  `xrandr | grep '\*'` at runtime; a different physical monitor may be
  connected — read the actual geometry, don't assume).
- **Firefox 157** at `/usr/bin/firefox` (only browser installed).
  **Chromium is NOT installed** — installing it (e.g. `sudo apt install
  chromium-browser` or downloading a chrome-headless-shell build) is
  allowed and probably worthwhile (per-tab-process memory is much better
  and its headless `--window-position/--window-size` flags are reliable),
  but if you stay on Firefox, everything below must still hold.
- NOT installed: `xdotool`, `wmctrl`, `python3-xlib`, `websocket-client`.
  `xprop` IS installed. You may `pip install` python libraries
  (pure-python `Xlib` is fine) or apt-install xdotool/wmctrl if you
  need them for window placement.
- Ports 8901/8902/8903 are taken by `forge-console.service` (do not
  touch it — C6 restarts it separately). Pick free ports for reelsmax
  (8905/8906 suggested) — verify free before binding, never kill
  anything to make room.
- `sudo` may need a password; if blocked, note it in your report and
  proceed with whatever worked without it.
- Servers bind `0.0.0.0` (LAN rule) on the chosen port.
- No build step required for the console tab (vanilla JS). Reelsmax
  itself: your choice — stdlib-only python (like the console) or node,
  but no npm build pipeline that needs network install steps at runtime.

────────────────────────────────────────────────────
## Product A — Reelsmax

### The lane model (architecture is up to you, these are the requirements)

A "lane" = one YouTube Shorts instance with its own cookie jar (so each
lane gets its own fresh feed), its own audio, playing with sound by
default, borderless (no browser chrome — tab content fills the tile).

How a lane is rendered is your design decision, but every one of these
must hold regardless of rendering choice:

1. **Autoplay with audio out of the box.** Lanes must not sit on a
   "tap to play" state. YouTube surfaces (iframe embed, mobile URL,
   etc.) that require a user gesture to start audio may be blocked by
   autoplay policy — you must solve this (e.g. headless browser flags
   like `--autoplay-policy=no-user-gesture-required`, or an initial
   synthetic user gesture, or starting lanes from a real user click on
   "add"). Whatever you do, verify: a freshly added lane is PLAYING with
   audible audio within seconds, no clicks required beyond the add.
2. **Borderless / edge-to-edge** — only video content in the tile.
3. **Spacebar advances every lane to its next short simultaneously**
   (unison). Optional per-lane offset index for variety is a bonus.
   Next-short must work reliably (e.g. the mobile Shorts UI's swipe/
   "next" semantics — find what actually works and use it).
4. **Global controls** (on-screen buttons + keyboard shortcuts, listed
   on the UI):
   - `Space` = next short on all lanes
   - `P` or `K` = pause/resume all
   - `M` = mute/unmute all (audio on/off globally, per-lane too if easy)
   - `+`/`Add` = add a lane, `-`/`Remove` = remove one
   - Bonus: click a tile to give it focus, arrows for per-lane next/prev.
   Show shortcut hints in the UI.
5. **Auto-fit grid, no scrollbars, no borders eating space.** When a lane
   is added, the whole grid recomputes so ALL tiles fit the screen at
   once (grid recalcs on resize too). Tiles are 9:16 (Shorts aspect).
   No page scroll on the wall itself. A small floating control bar is
   the only chrome allowed.
6. **RAM efficiency is a first-class requirement** (4-core/7.3 GB box):
   - Every rendered lane must have measured memory overhead well under
     ~150–250 MB. Measure with your own method (per-process RSS via
     `ps`/procfs, summed) and SHOW the numbers.
   - Include a **RAM governor**: a soft cap (configurable, default
     tuned so the wall works with ~4–6 GB of headroom for the OS) that
     refuses new lanes past the cap with a visible "RAM limit reached"
     notice rather than letting the box swap/burn.
   - Prefer one shared browser process with per-lane tabs/instances
     (separate user-data-dir per lane for cookies) over one browser
     process per lane if that's the cheaper design. Lazy-init lanes
     (only boot a lane's browser instance when it's added, not all at
     startup).
   - Show a live **RAM usage readout** (total lanes, total MB, per-lane
     average) in the control bar so the owner sees the budget.

### User-facing wall UI

- Dark, clean, "looks nice" — consistent with the console aesthetic
  (dark bg, subtle accents, monospace touches). Responsive to window
  size.
- **Two modes**:
  a) **Wall mode** (default): one page/grid — add N lanes, they all fit,
     no scrollbars. This is the headline mode.
  b) **Window mode**: lanes open as separate OS windows in an auto-computed
     grid (computed from actual screen geometry via `xrandr`; tiles sized
     to leave a few-px gap). If window placement proves unreliable with
     the available tooling (no xdotool/wmctrl initially — see above),
     deliver Wall mode fully and leave Window mode as a documented stub
     that explains what's missing. Don't let window-mode failures block
     the wall.
- The add-lane action generates a **fresh cookie identity per lane**
  (lane's own profile dir, no pre-seeded cookies) so feeds diverge.
  Never write cookie values into files in the repo.
- Persistence: lane count survives a server restart is a bonus, not
  required.

### Verification (do ALL, show evidence)

1. Boot the reelsmax server; open the wall with 6 and with 12 lanes:
   all tiles fit with zero scrollbars (screenshot or DOM proof:
   `document.body.scrollHeight <= clientHeight`).
2. 12 lanes playing with audio (verify via audio output or
   `mediastream`/process evidence; if the host has no audio device,
   prove playback state programmatically — e.g. each lane reports
   `playing: true` in its control channel — and say which you used).
3. Press space: ALL lanes advance (capture before/after URL or video id
   per lane as evidence).
4. RAM: with 12 lanes, report total RSS of the lane processes +
   reelsmax server; show the per-lane average; show the governor
   refusing lane #N+1 at the cap.
5. Mute all / pause all verified via the API the wall exposes.
6. Expose a small JSON API (e.g. `GET /api/state` -> lanes[] with
   id, status, video_id, muted, paused, mem_mb; `POST /api/add`,
   `POST /api/remove`, `POST /api/next`, `POST /api/pause_all`,
   `POST /api/mute_all`) — the console tab and C6 both verify through it.

────────────────────────────────────────────────────
## Product B — Forge Console Projects tab

Read `CONSOLE-PROJECTS.md` next to this file — it contains the full
brief, the `data/projects.json` schema, seed-data instructions, and the
console integration constraints (service name, files, "do not restart
the service" rule).

────────────────────────────────────────────────────
## Standing rules

- No API keys/tokens/cookies in code, logs, or your report.
- Don't touch `forge-console.service`, `insights-board`, or
  `scheme-board` processes. Do not restart any systemd service — C6
  handles restarts; leave the console code changes in place and note
  "restart required".
- Keep a `reelsmax/README.md`: what it is, how to start/stop (systemd
  unit file is a bonus, but do not install a unit without C6's say-so),
  ports, controls, RAM notes.
- When done: print a final report — what's verified with real evidence,
  what's stubbed, what you could not verify and why, plus the exact
  commands to start everything.
