You are building two products in this project directory
(~/HydrocarbonForge/Projects/reelsmax/). Work autonomously, iterate,
and self-verify with real commands (curl, ps, screenshots, DOM checks) —
never claim something works without evidence.

READ FIRST (authoritative, in this directory):
- SPEC.md  — full spec + verified environment facts (RAM, X display,
  Firefox 157, no chromium, no xdotool, ports 8901-8903 taken).
- CONSOLE-PROJECTS.md — the Forge Console "Projects" tab brief.

DO BOTH, in this order:

PRODUCT A (reelsmax): the auto-fitting Shorts wall per SPEC.md §Product A.
Build it to RUN ON THIS MACHINE and verify it here. Prioritize a working
Wall mode over a fancy Window mode. You may install chromium and/or
pip/apt packages if needed (note what you installed). Remember: every
lane = its own cookie jar (own profile dir) so feeds diverge; autoplay
WITH audio with no user gesture needed; spacebar advances ALL lanes in
unison; add/remove reflows the whole grid with zero scrollbars; a RAM
governor + live RAM readout; global controls (space next, P/K pause,
M mute, +/- add/remove); a small JSON API (/api/state etc.) that C6
verifies through. Show real numbers: per-lane RAM, total with 12 lanes,
evidence that all lanes advanced on space.

PRODUCT B (console tab): implement CONSOLE-PROJECTS.md exactly — new
Projects tab on the existing console, data/projects.json central DB,
server endpoints, frontend list+detail+add/edit/delete, seeded with the
real projects and their deployment evidence. Do NOT restart the running
forge-console service (port 8903) — verify with a standalone
`PORT=8910 python3 server.py` instance instead, then kill it. Leave the
console code changes in place for C6 to restart.

CONSTRAINTS:
- No API keys/tokens/cookies in code, logs, or your report.
- Don't touch running services or their ports.
- End with a single clear FINAL REPORT: (1) what you built, (2) what you
  actually verified with real output (paste the key evidence), (3) what is
  stubbed or unverified and why, (4) exact commands to start both
  products, (5) the RAM numbers you measured.
