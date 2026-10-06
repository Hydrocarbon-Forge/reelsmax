# Forge Console — "Projects" tab brief (Product B of the reelsmax build)

Nathan requested (2026-10-05): a new **Projects** tab on the Hydrocarbon
Forge console. One page per project; each project page shows whether it
has a deployment, and if so a link to it. Backed by a central project
database.

## Console facts (verified — use as-is)

- Console = `~/HydrocarbonForge/Projects/forge-console/`, one python
  stdlib server `server.py` on port **8903** (bound 0.0.0.0), run as the
  systemd user service **`forge-console.service`** (pids ~171629 hold
  8901/8902/8903).
- Console frontend = `web/index.html` + `web/app.js` + `web/style.css`
  (served at `/`). Tab system is data-driven:
  - Nav buttons: `<button class="nav-tab" id="nav-<id>" data-tab="<id>">`
    inside `nav.nav-tabs` (existing: `insights`, `ideas`, `flow`).
  - Panes: `<section class="tab-pane" id="pane-<id>">`.
  - `web/app.js`: `.nav-tab` click → `switchTab(tab)` (line ~154);
    `switchTab(tabId, updateHash)` (line ~219) toggles `.active` on
    buttons + panes, sets `location.hash` (`#/insights` etc.); hash
    init at ~line 214. Keyboard: keys 1/2/3 mapped at ~line 265-269.
  - Existing panes for insights/ideas are iframes to engines; the Flow
    pane is inline canvas. `data/` dir already exists in the project.
- DO NOT restart `forge-console.service` (or any systemd service) —
  C6 restarts it. Leave your code changes in place; they activate on the
  next restart. Verify your work by running `server.py` standalone on a
  DIFFERENT port (e.g. `PORT=8910 python3 server.py`) and hitting it
  with curl/browser, then kill that test process.

## Build

1. **Central project database**: `data/projects.json` (new file) —
   schema:
   ```json
   {
     "projects": [
       {
         "id": "forge-console",
         "name": "Forge Console",
         "path": "~/HydrocarbonForge/Projects/forge-console",
         "description": "Central control panel (insights + ideas + flow)",
         "deployed": true,
         "deployment_url": "http://192.168.1.201:8903",
         "service": "forge-console.service",
         "tags": ["console"],
         "updated": "2026-10-05"
       }
     ]
   }
   ```
   `deployed: false` → no `deployment_url` (omit or null).
   Seed it with the real projects in `~/HydrocarbonForge/Projects/`
   (scan the dirs yourself: hello-world, hydrocarbon-forge-website,
   insights-board, monecraft-baking, road-to-100-grand, scheme-board,
   tabg-portal-passthrough, wonder-sprout, forge-console, forge-channel,
   forge-discord-design, gavin-presentation-video, test, test-site,
   plus `reelsmax` (this build) and `backups`). For each, infer
   `deployed` + `deployment_url` from evidence in the project (URLs in
   README/docs, service files, known LAN addresses): e.g. scheme-board
   serves at `http://192.168.1.201:8902` (evidence found in its docs),
   forge-console at `http://192.168.1.201:8903`, the website project if
   it has a deployed URL. No evidence → `deployed: false`.
2. **Server API** in `server.py` (stdlib only, no new deps):
   - `GET /api/projects` → the array.
   - `POST /api/projects` (create), `PATCH /api/projects/<id>` (update
     any field — this is how "deployment appeared" gets recorded),
     `DELETE /api/projects/<id>`.
   - Persist to `data/projects.json` (read-modify-write under a lock,
     atomic temp-file replace). 404 for unknown ids, 400 for bad
     shape. Validate: `id` = safe slug (lowercase, `-`/`_`/digits),
     `deployment_url` if present must be http(s) URL.
   - `GET /api/health` output: add a `projects: true/false` field if
     `data/projects.json` exists and parses (or just include the count) —
     minor, keep backwards compatible (existing fields unchanged).
3. **Frontend**:
   - New tab `PROJECTS` (`data-tab="projects"`, key `4`) after the
     existing three; pane `pane-projects` (inline section, NOT an
     iframe).
   - List view: project cards/table (name, description, service tag,
     deploy badge `DEPLOYED`/`not deployed`).
   - Project detail: clicking a project shows its page (hash route
     `#/projects/<id>`) — description, path, service, tags, updated
     date, and a prominent **Open deployment →** link when deployed
     (target=_blank); "no deployment yet" state when not. Back to list.
   - Add-project form (modal or inline): name → id auto-slug,
     description, service, deployment url, deployed checkbox.
   - Edit: from the detail view, edit fields incl. deployment url +
     deployed toggle (the "record a deployment" path). Delete with
     confirm.
   - Match the existing console aesthetic (dark, Oswald/Inter/
     JetBrains Mono, `.data-table` class exists for tables) — read
     `web/style.css` first. Responsive.
4. **Refresh**: poll `GET /api/projects` every 15-30s on the list view
   so external edits to the JSON show up; after any mutation, re-fetch
   immediately.

## Verification (show evidence)

- `PORT=8910 python3 server.py` (background) → curl:
  `GET /api/projects` returns seeded list; POST a test project → it
  persists to the file; PATCH its `deployed`/url → visible; DELETE →
  gone. Seed file unchanged by your test project afterwards (clean up).
- Browser: open `http://127.0.0.1:8910/` — tab visible, list renders,
  detail page for a deployed project shows the link, not-deployed shows
  the empty state, add→edit→delete round-trip works. Kill the test
  server when done.
- `python3 -m py_compile server.py` passes; frontend JS lint-clean
  (`node --check web/app.js` if node exists, else careful review).
- Final report: list every project you seeded and what deployment
  evidence you found for each, so C6 can sanity-check.
