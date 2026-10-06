/**
 * Reelsmax Client Application
 * Zero-scrollbar auto-fitting grid, unison controls, and live RAM readout.
 */

let state = {
  lanes: [],
  total_lanes: 0,
  total_mem_mb: 0,
  avg_lane_mem_mb: 0,
  system_mem: { total_mb: 0, available_mb: 0 },
  ram_governor: { max_lanes: 12, limit_reached: false },
  global: { paused: false, muted: false }
};

const players = new Map(); // laneId -> YT.Player
let focusedLaneId = null;
let ytReady = false;

window.onYouTubeIframeAPIReady = () => {
  ytReady = true;
  console.log("[Reelsmax] YouTube IFrame API Ready");
};

// UI Elements
const gridContainer = document.getElementById("grid-container");
const viewport = document.getElementById("viewport");
const statLanes = document.getElementById("stat-lanes");
const statTotalRam = document.getElementById("stat-total-ram");
const statAvgRam = document.getElementById("stat-avg-ram");
const statAvailRam = document.getElementById("stat-avail-ram");
const govBadge = document.getElementById("gov-badge");
const govAlert = document.getElementById("governor-alert");
const btnNext = document.getElementById("btn-next");
const btnPause = document.getElementById("btn-pause");
const btnMute = document.getElementById("btn-mute");
const btnAdd = document.getElementById("btn-add");
const btnRem = document.getElementById("btn-rem");
const pauseIcon = document.getElementById("pause-icon");
const pauseText = document.getElementById("pause-text");
const muteIcon = document.getElementById("mute-icon");
const muteText = document.getElementById("mute-text");

// Auto-fitting 9:16 grid calculation
function reflowGrid() {
  const n = state.lanes.length;
  if (n === 0) {
    gridContainer.innerHTML = "";
    return;
  }

  const vw = viewport.clientWidth - 12;
  const vh = viewport.clientHeight - 12;
  const gap = 6;
  const aspect = 9 / 16; // width / height = 0.5625

  let bestCols = 1;
  let bestW = 0;
  let bestH = 0;
  let maxArea = 0;

  for (let c = 1; c <= n; c++) {
    const r = Math.ceil(n / c);
    const maxTileW = (vw - (c - 1) * gap) / c;
    const maxTileH = (vh - (r - 1) * gap) / r;

    if (maxTileW <= 0 || maxTileH <= 0) continue;

    let w = maxTileW;
    let h = w / aspect;

    if (h > maxTileH) {
      h = maxTileH;
      w = h * aspect;
    }

    const totalArea = w * h * n;
    if (totalArea > maxArea) {
      maxArea = totalArea;
      bestCols = c;
      bestW = Math.floor(w);
      bestH = Math.floor(h);
    }
  }

  // Apply layout styles
  gridContainer.style.gridTemplateColumns = `repeat(${bestCols}, ${bestW}px)`;
  gridContainer.style.gridAutoRows = `${bestH}px`;
  gridContainer.style.gap = `${gap}px`;

  // Update tile dimensions
  const tiles = gridContainer.querySelectorAll(".lane-tile");
  tiles.forEach(tile => {
    tile.style.width = `${bestW}px`;
    tile.style.height = `${bestH}px`;
  });
}

// Render lanes into grid
function renderGrid() {
  const currentTileIds = new Set(Array.from(gridContainer.children).map(el => parseInt(el.dataset.id)));
  const newLanesMap = new Map(state.lanes.map(l => [l.id, l]));

  // Remove stale tiles
  for (const id of currentTileIds) {
    if (!newLanesMap.has(id)) {
      const el = gridContainer.querySelector(`[data-id="${id}"]`);
      if (el) el.remove();
      if (players.has(id)) players.delete(id);
    }
  }

  // Add or update tiles
  state.lanes.forEach(lane => {
    let tile = gridContainer.querySelector(`[data-id="${lane.id}"]`);
    if (!tile) {
      tile = document.createElement("div");
      tile.className = "lane-tile";
      tile.dataset.id = lane.id;
      if (focusedLaneId === lane.id) tile.classList.add("focused");

      tile.addEventListener("click", () => {
        setFocusLane(lane.id);
      });

      const badge = document.createElement("div");
      badge.className = "lane-badge";
      badge.textContent = `LANE ${lane.id} · ${lane.category.toUpperCase()}`;
      tile.appendChild(badge);

      const wrapper = document.createElement("div");
      wrapper.className = "lane-iframe-wrapper";
      const playerId = `yt-player-${lane.id}`;
      wrapper.id = playerId;
      tile.appendChild(wrapper);

      gridContainer.appendChild(tile);

      // Create YouTube player or iframe
      createPlayerForLane(lane.id, playerId, lane.video_id);
    } else {
      // Check if video changed
      const currentVid = tile.dataset.videoId;
      if (currentVid !== lane.video_id) {
        tile.dataset.videoId = lane.video_id;
        updatePlayerVideo(lane.id, lane.video_id);
      }
    }
  });

  reflowGrid();
}

function createPlayerForLane(laneId, containerId, videoId) {
  const tile = gridContainer.querySelector(`[data-id="${laneId}"]`);
  if (tile) tile.dataset.videoId = videoId;

  const origin = window.location.origin;
  const embedUrl = `https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1&mute=${state.global.muted ? 1 : 0}&controls=0&loop=1&playsinline=1&enablejsapi=1&origin=${encodeURIComponent(origin)}`;

  if (ytReady && window.YT && window.YT.Player) {
    try {
      const player = new YT.Player(containerId, {
        videoId: videoId,
        playerVars: {
          autoplay: 1,
          mute: state.global.muted ? 1 : 0,
          controls: 0,
          loop: 1,
          playsinline: 1,
          rel: 0,
          origin: origin
        },
        events: {
          onReady: (event) => {
            if (!state.global.muted) event.target.unMute();
            if (!state.global.paused) event.target.playVideo();
          }
        }
      });
      players.set(laneId, player);
      return;
    } catch (e) {
      console.warn("Falling back to iframe embed", e);
    }
  }

  // Fallback: direct iframe
  const wrapper = document.getElementById(containerId);
  if (wrapper) {
    wrapper.innerHTML = `<iframe src="${embedUrl}" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
  }
}

function updatePlayerVideo(laneId, videoId) {
  const player = players.get(laneId);
  if (player && typeof player.loadVideoById === "function") {
    player.loadVideoById(videoId);
    if (!state.global.muted && typeof player.unMute === "function") player.unMute();
    if (!state.global.paused && typeof player.playVideo === "function") player.playVideo();
  } else {
    const tile = gridContainer.querySelector(`[data-id="${laneId}"]`);
    if (tile) {
      const wrapper = tile.querySelector(".lane-iframe-wrapper");
      if (wrapper) {
        const origin = window.location.origin;
        const embedUrl = `https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1&mute=${state.global.muted ? 1 : 0}&controls=0&loop=1&playsinline=1&enablejsapi=1&origin=${encodeURIComponent(origin)}`;
        wrapper.innerHTML = `<iframe src="${embedUrl}" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
      }
    }
  }
}

function setFocusLane(id) {
  focusedLaneId = (focusedLaneId === id) ? null : id;
  const tiles = gridContainer.querySelectorAll(".lane-tile");
  tiles.forEach(tile => {
    if (parseInt(tile.dataset.id) === focusedLaneId) {
      tile.classList.add("focused");
    } else {
      tile.classList.remove("focused");
    }
  });
}

// Synchronous Control API Calls
async function advanceAll() {
  try {
    const res = await fetch("/api/next", { method: "POST" });
    const data = await res.json();
    if (data.state) {
      applyState(data.state);
    }
  } catch (e) {
    console.error("Next failed", e);
  }
}

async function togglePauseAll() {
  const nextPaused = !state.global.paused;
  try {
    const res = await fetch("/api/pause_all", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ paused: nextPaused })
    });
    const data = await res.json();
    if (data.state) applyState(data.state);
  } catch (e) {
    console.error("Pause failed", e);
  }
}

async function toggleMuteAll() {
  const nextMuted = !state.global.muted;
  try {
    const res = await fetch("/api/mute_all", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ muted: nextMuted })
    });
    const data = await res.json();
    if (data.state) applyState(data.state);
  } catch (e) {
    console.error("Mute failed", e);
  }
}

async function addLane() {
  try {
    const res = await fetch("/api/add", { method: "POST" });
    const data = await res.json();
    if (res.status === 429 || data.limit_reached) {
      showGovernorAlert(data.error || "RAM limit reached");
    } else if (data.state) {
      hideGovernorAlert();
      applyState(data.state);
    }
  } catch (e) {
    console.error("Add failed", e);
  }
}

async function removeLane() {
  try {
    const res = await fetch("/api/remove", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(focusedLaneId ? { id: focusedLaneId } : {})
    });
    const data = await res.json();
    if (data.state) {
      hideGovernorAlert();
      applyState(data.state);
    }
  } catch (e) {
    console.error("Remove failed", e);
  }
}

function showGovernorAlert(msg) {
  govAlert.textContent = `⚠️ ${msg}`;
  govAlert.classList.remove("hidden");
  govBadge.className = "governor-badge warn";
  govBadge.textContent = "RAM LIMIT REACHED";
}

function hideGovernorAlert() {
  govAlert.classList.add("hidden");
  govBadge.className = "governor-badge ok";
  govBadge.textContent = "GOVERNOR OK";
}

// Update UI Telemetry
function applyState(newState) {
  state = newState;

  statLanes.textContent = state.total_lanes;
  statTotalRam.textContent = state.total_mem_mb;
  statAvgRam.textContent = state.avg_lane_mem_mb;
  statAvailRam.textContent = state.system_mem.available_mb;

  if (state.ram_governor.limit_reached) {
    showGovernorAlert(`RAM LIMIT REACHED: Soft cap of ${state.ram_governor.max_lanes} lanes reached.`);
  } else {
    hideGovernorAlert();
  }

  // Update control button text/icons
  if (state.global.paused) {
    pauseIcon.textContent = "▶";
    pauseText.textContent = "PLAY (P)";
  } else {
    pauseIcon.textContent = "⏸";
    pauseText.textContent = "PAUSE (P)";
  }

  if (state.global.muted) {
    muteIcon.textContent = "🔇";
    muteText.textContent = "UNMUTE (M)";
  } else {
    muteIcon.textContent = "🔊";
    muteText.textContent = "MUTE (M)";
  }

  // Propagate pause/mute to active player instances
  players.forEach((player) => {
    try {
      if (state.global.paused) {
        if (typeof player.pauseVideo === "function") player.pauseVideo();
      } else {
        if (typeof player.playVideo === "function") player.playVideo();
      }
      if (state.global.muted) {
        if (typeof player.mute === "function") player.mute();
      } else {
        if (typeof player.unMute === "function") player.unMute();
      }
    } catch (e) {}
  });

  renderGrid();
}

// Polling loop for state sync
async function fetchState() {
  try {
    const res = await fetch("/api/state");
    if (res.ok) {
      const data = await res.json();
      applyState(data);
    }
  } catch (e) {}
}

// Event Listeners
btnNext.addEventListener("click", advanceAll);
btnPause.addEventListener("click", togglePauseAll);
btnMute.addEventListener("click", toggleMuteAll);
btnAdd.addEventListener("click", addLane);
btnRem.addEventListener("click", removeLane);

window.addEventListener("resize", reflowGrid);

// Global Keyboard Navigation
window.addEventListener("keydown", (e) => {
  // Ignore inside text inputs
  if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

  if (e.code === "Space") {
    e.preventDefault();
    advanceAll();
  } else if (e.code === "KeyP" || e.code === "KeyK") {
    e.preventDefault();
    togglePauseAll();
  } else if (e.code === "KeyM") {
    e.preventDefault();
    toggleMuteAll();
  } else if (e.key === "+" || e.key === "=") {
    e.preventDefault();
    addLane();
  } else if (e.key === "-" || e.key === "_") {
    e.preventDefault();
    removeLane();
  }
});

// Initial boot
fetchState();
setInterval(fetchState, 3000);
