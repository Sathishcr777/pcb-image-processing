/* ==========================================================================
   SHARED INDUSTRIAL STATION CONTROLLER, NAVIGATION & GLOBAL BOARD SYNC
   Enterprise IPC-A-610H Class 2/3 & Industry 4.0 Platform
   ========================================================================== */

// --- 1. COMPREHENSIVE GROUND-TRUTH SCENARIO & DEFECT CATALOG (TB001 - TB032) ---
const SCENARIO_CATALOG = {
  "TB001": {
    id: "TB001",
    name: "Production Batch Golden Sample",
    defect_type: "none",
    defect_desc: "Production batch verification master (Zero defects)",
    component: "System All",
    default_verdict: "PASS",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_optimal"
  },
  "TB002": {
    id: "TB002",
    name: "C_R1 Tombstoned (45° Tilt Lift)",
    defect_type: "tombstone",
    defect_desc: "Non-wetted terminal lifted at 45° angle (2.8mm height asymmetry)",
    component: "C_R1 (0805 Capacitor)",
    default_verdict: "REWORK",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_tombstone"
  },
  "TB003": {
    id: "TB003",
    name: "Mid-Upper Controller (U2) Angular Tilt (18°)",
    defect_type: "tilt",
    defect_desc: "18.0° rotational skew exceeding footprint tolerance",
    component: "U2 (QFP Controller)",
    default_verdict: "REWORK",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_excess"
  },
  "TB004": {
    id: "TB004",
    name: "Top-Right MCU (U1) Placement Shift (1.5mm)",
    defect_type: "shift",
    defect_desc: "1.5mm sub-pixel offset exceeding 25% minimum pad width",
    component: "U1 (Main MCU)",
    default_verdict: "REWORK",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_excess"
  },
  "TB005": {
    id: "TB005",
    name: "100% Perfect Master Golden Board",
    defect_type: "none",
    defect_desc: "Certified Golden Master Reference (Zero defects, 100% Class 3 Target)",
    component: "All 12 Components",
    default_verdict: "PASS",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_optimal"
  },
  "TB006": {
    id: "TB006",
    name: "Golden Production Board 2",
    defect_type: "none",
    defect_desc: "Secondary production golden standard",
    component: "All Components",
    default_verdict: "PASS",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_optimal"
  },
  "TB007": {
    id: "TB007",
    name: "Golden Production Board 3",
    defect_type: "none",
    defect_desc: "Production run golden sample",
    component: "All Components",
    default_verdict: "PASS",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_optimal"
  },
  "TB008": {
    id: "TB008",
    name: "Golden Production Board 4",
    defect_type: "none",
    defect_desc: "Production run golden sample",
    component: "All Components",
    default_verdict: "PASS",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_optimal"
  },
  "TB009": {
    id: "TB009",
    name: "Golden Production Board 5",
    defect_type: "none",
    defect_desc: "Production run golden sample",
    component: "All Components",
    default_verdict: "PASS",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_optimal"
  },
  "TB010": {
    id: "TB010",
    name: "Top-Right MCU (U1) Missing",
    defect_type: "missing",
    defect_desc: "Unpopulated footprint pads with un-wetted solder",
    component: "U1 (Main MCU)",
    default_verdict: "FAIL",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_insufficient"
  },
  "TB011": {
    id: "TB011",
    name: "Center QFN Processor (U5) Missing",
    defect_type: "missing",
    defect_desc: "Missing center processor core on SMT footprint",
    component: "U5 (Core Processor)",
    default_verdict: "FAIL",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_insufficient"
  },
  "TB012": {
    id: "TB012",
    name: "Top-Right Controller (U1) Missing",
    defect_type: "missing",
    defect_desc: "Missing primary controller package",
    component: "U1 (Main MCU)",
    default_verdict: "FAIL",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_insufficient"
  },
  "TB013": {
    id: "TB013",
    name: "Mid-Upper Controller (U2) Missing",
    defect_type: "missing",
    defect_desc: "Missing controller IC body",
    component: "U2 (Controller)",
    default_verdict: "FAIL",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_insufficient"
  },
  "TB014": {
    id: "TB014",
    name: "Multi-Part Missing (U3 + C_R2 Capacitor)",
    defect_type: "missing",
    defect_desc: "Multiple unpopulated footprints (U3 Controller + C_R2 Passive)",
    component: "U3, C_R2",
    default_verdict: "FAIL",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_insufficient"
  },
  "TB015": {
    id: "TB015",
    name: "Top SMT Bus Header (J_TOP) Missing",
    defect_type: "missing",
    defect_desc: "Through-hole / SMT header connector missing",
    component: "J_TOP",
    default_verdict: "FAIL",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_insufficient"
  },
  "TB016": {
    id: "TB016",
    name: "Bottom SMT Header (J_BOT1) Missing",
    defect_type: "missing",
    defect_desc: "Bottom peripheral interface header missing",
    component: "J_BOT1",
    default_verdict: "FAIL",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_insufficient"
  },
  "TB017": {
    id: "TB017",
    name: "Left SMT Passives Matrix (BANK_L1) Missing",
    defect_type: "missing",
    defect_desc: "Decoupling passive matrix BANK_L1 missing",
    component: "BANK_L1",
    default_verdict: "FAIL",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_insufficient"
  },
  "TB018": {
    id: "TB018",
    name: "Bottom-Right MCU (U4) Missing",
    defect_type: "missing",
    defect_desc: "Secondary controller package missing",
    component: "U4 (MCU)",
    default_verdict: "FAIL",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_insufficient"
  },
  "TB019": {
    id: "TB019",
    name: "Left SMT Passives Matrix (BANK_L2) Missing",
    defect_type: "missing",
    defect_desc: "Decoupling passive matrix BANK_L2 missing",
    component: "BANK_L2",
    default_verdict: "FAIL",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_insufficient"
  },
  "TB020": {
    id: "TB020",
    name: "Dual Core Missing (U1 MCU + U5 Processor)",
    defect_type: "missing",
    defect_desc: "Catastrophic dual processor missing defect",
    component: "U1, U5",
    default_verdict: "FAIL",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_insufficient"
  },
  "TB021": {
    id: "TB021",
    name: "Dual Header & Matrix Missing (J_BOT2 + BANK_L2)",
    defect_type: "missing",
    defect_desc: "Multiple peripheral connectors and passive bank missing",
    component: "J_BOT2, BANK_L2",
    default_verdict: "FAIL",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_insufficient"
  },
  "TB022": {
    id: "TB022",
    name: "Triple Controller Missing (U2 + U3 + U4)",
    defect_type: "missing",
    defect_desc: "Triple IC package loss across board surface",
    component: "U2, U3, U4",
    default_verdict: "FAIL",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_insufficient"
  },
  "TB023": {
    id: "TB023",
    name: "C_R2 Capacitor Tombstone (2.9mm)",
    defect_type: "tombstone",
    defect_desc: "Single-pad lift off substrate (2.9mm asymmetry)",
    component: "C_R2 (Capacitor)",
    default_verdict: "REWORK",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_tombstone"
  },
  "TB024": {
    id: "TB024",
    name: "C_R1 Capacitor Tombstone (3.1mm)",
    defect_type: "tombstone",
    defect_desc: "Severe tombstone angle (3.1mm asymmetry)",
    component: "C_R1 (Capacitor)",
    default_verdict: "REWORK",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_tombstone"
  },
  "TB025": {
    id: "TB025",
    name: "U5 Processor Angular Tilt (22°)",
    defect_type: "tilt",
    defect_desc: "Rotational skew (22.0°) violating pad footprint limits",
    component: "U5 (Processor)",
    default_verdict: "REWORK",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_excess"
  },
  "TB026": {
    id: "TB026",
    name: "U3 Controller Angular Tilt (20°)",
    defect_type: "tilt",
    defect_desc: "Rotational skew (20.0°) violating IPC Class 3",
    component: "U3 (Controller)",
    default_verdict: "REWORK",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_excess"
  },
  "TB027": {
    id: "TB027",
    name: "U2 Controller Placement Shift (1.8mm)",
    defect_type: "shift",
    defect_desc: "Translational shift (1.8mm) violating lead alignment",
    component: "U2 (Controller)",
    default_verdict: "REWORK",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_excess"
  },
  "TB028": {
    id: "TB028",
    name: "U3 Controller Placement Shift (1.8mm)",
    defect_type: "shift",
    defect_desc: "Translational shift (1.8mm) exceeding solder pad margins",
    component: "U3 (Controller)",
    default_verdict: "REWORK",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_excess"
  },
  "TB029": {
    id: "TB029",
    name: "Framing Alignment Drift (+8px, +6px)",
    defect_type: "none",
    defect_desc: "Sub-pixel homography correction test sample",
    component: "None (Pass)",
    default_verdict: "PASS",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_optimal"
  },
  "TB030": {
    id: "TB030",
    name: "Framing Alignment Drift (-6px, +5px)",
    defect_type: "none",
    defect_desc: "Sub-pixel homography correction test sample",
    component: "None (Pass)",
    default_verdict: "PASS",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_optimal"
  },
  "TB031": {
    id: "TB031",
    name: "Multi-MCU Missing (U1 + U4 Missing)",
    defect_type: "missing",
    defect_desc: "Dual controller footprint unpopulated",
    component: "U1, U4",
    default_verdict: "FAIL",
    solder_applicable: true,
    xray_applicable: true,
    photometric_sample: "ps_sample_insufficient"
  },
  "TB032": {
    id: "TB032",
    name: "Substrate Thermal Burn Hole & Carbonized FR-4 Rupture",
    defect_type: "severe_thermal_burn",
    defect_desc: "Catastrophic dielectric burn-through, FR-4 pyrolysis and copper trace vaporization (IPC-A-610 Section 10.2 Scrap)",
    component: "Power Stage Substrate",
    default_verdict: "FAIL",
    solder_applicable: false, // Critical: Not a solder joint defect!
    xray_applicable: true,
    photometric_sample: "ps_sample_burn"
  }
};

function getScenarioCatalogEntry(boardId) {
  if (!boardId) return SCENARIO_CATALOG["TB005"];
  const cleanId = String(boardId).trim().toUpperCase();
  if (SCENARIO_CATALOG[cleanId]) return SCENARIO_CATALOG[cleanId];

  // Try matching substring or custom upload
  for (const k of Object.keys(SCENARIO_CATALOG)) {
    if (cleanId.includes(k)) return SCENARIO_CATALOG[k];
  }

  return {
    id: boardId,
    name: `Custom Board (${boardId})`,
    defect_type: "custom",
    defect_desc: "Operator custom uploaded PCB image",
    component: "Custom",
    default_verdict: "REVIEW",
    solder_applicable: true,
    xray_applicable: false,
    photometric_sample: "ps_sample_optimal"
  };
}

// --- 2. GLOBAL ACTIVE BOARD SYNCHRONIZATION SYSTEM ---
const AOI_SYNC_CHANNEL_NAME = 'aoi_board_sync_channel';
let aoiSyncBroadcast = null;
try {
  aoiSyncBroadcast = new BroadcastChannel(AOI_SYNC_CHANNEL_NAME);
} catch (e) {
  console.warn("BroadcastChannel not supported", e);
}

// Function to update all navigation tabs on the current page to preserve active board parameter
function updateNavLinksWithActiveBoard(boardId) {
  if (!boardId) return;
  const bId = String(boardId).trim().toUpperCase();
  const navLinks = document.querySelectorAll('.ind-nav-menu a.nav-tab-btn');
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href && href.startsWith('/') && !href.startsWith('/api') && !href.startsWith('/download') && !href.startsWith('/static')) {
      const basePath = href.split('?')[0];
      link.setAttribute('href', `${basePath}?board=${encodeURIComponent(bId)}`);
    }
  });

  // Keep browser address bar query param in sync without reloading page
  if (typeof window !== 'undefined' && window.location && window.history && window.history.replaceState) {
    try {
      const currentParams = new URLSearchParams(window.location.search);
      if (currentParams.get('board') !== bId) {
        currentParams.set('board', bId);
        const newUrl = `${window.location.pathname}?${currentParams.toString()}`;
        window.history.replaceState({ board_id: bId }, '', newUrl);
      }
    } catch (e) {}
  }
}

// Function to broadcast active board change to all pages and backend server
async function setGlobalActiveBoard(boardInfo) {
  if (!boardInfo) return;
  const bId = String(boardInfo.board_id || boardInfo.serial || 'TB005').trim().toUpperCase();
  const catalog = getScenarioCatalogEntry(bId);

  const enriched = {
    board_id: bId,
    serial: bId,
    scenario_id: bId,
    scenario_name: boardInfo.scenario_name || catalog.name,
    defect_type: boardInfo.defect_type || catalog.defect_type,
    defect_description: boardInfo.defect_description || catalog.defect_desc,
    solder_applicable: catalog.solder_applicable,
    verdict: boardInfo.verdict || catalog.default_verdict,
    health_index: boardInfo.health_index ?? (catalog.default_verdict === 'PASS' ? 1.0 : (catalog.id === 'TB032' ? 0.0 : 0.85)),
    defective_components: boardInfo.defective_components ?? (catalog.default_verdict === 'PASS' ? 0 : 1),
    image_url: boardInfo.image_url || `/evaluation/test_boards/${bId}.png`,
    components: boardInfo.components || [],
    metrology: boardInfo.metrology || [],
    measurements: boardInfo.measurements || {},
    golden_comparison: boardInfo.golden_comparison || null,
    timestamp: Date.now()
  };

  // Safe lightweight storage payload (stripping any large base64 strings to prevent QuotaExceededError)
  const storagePayload = {
    board_id: bId,
    serial: bId,
    scenario_id: bId,
    scenario_name: enriched.scenario_name,
    defect_type: enriched.defect_type,
    defect_description: enriched.defect_description,
    solder_applicable: enriched.solder_applicable,
    verdict: enriched.verdict,
    health_index: enriched.health_index,
    defective_components: enriched.defective_components,
    image_url: enriched.image_url,
    golden_comparison: enriched.golden_comparison || null,
    timestamp: enriched.timestamp
  };

  try {
    localStorage.removeItem('activeBoard3D'); // Purge legacy bloated key
    localStorage.setItem('aoi_active_board', JSON.stringify(storagePayload));
    sessionStorage.setItem('aoi_active_board', JSON.stringify(storagePayload));
  } catch (err) {
    console.warn("Storage write error", err);
  }

  // Update header badge and navigation links on current page immediately
  renderActiveBoardHeaderBadge(enriched);
  updateNavLinksWithActiveBoard(bId);

  if (aoiSyncBroadcast) {
    try {
      aoiSyncBroadcast.postMessage({ type: 'AOI_BOARD_CHANGED', data: enriched });
    } catch (err) {
      console.warn("BroadcastChannel post error", err);
    }
  }

  window.dispatchEvent(new CustomEvent('aoi_board_changed', { detail: enriched }));

  // Push to backend server as authoritative state
  try {
    await fetch('/api/active-board', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(enriched)
    });
  } catch (e) {
    console.warn("Failed to push active board to server:", e);
  }

  return enriched;
}

// Function for any page to get the authoritative current active board
async function getGlobalActiveBoard() {
  const urlParams = new URLSearchParams(window.location.search);
  const urlBoard = urlParams.get('board') || urlParams.get('scenario');

  // 1. If URL has explicit board param, sync with server using that param
  if (urlBoard) {
    const cleanId = String(urlBoard).trim().toUpperCase();
    try {
      const res = await fetch(`/api/active-board?board=${encodeURIComponent(cleanId)}`);
      if (res.ok) {
        const data = await res.json();
        const enriched = enrichBoardInfo(data);
        renderActiveBoardHeaderBadge(enriched);
        updateNavLinksWithActiveBoard(enriched.board_id);
        return enriched;
      }
    } catch (e) {}
  }

  // 2. Fetch authoritative state from backend API
  try {
    const res = await fetch('/api/active-board');
    if (res.ok) {
      const data = await res.json();
      if (data && (data.board_id || data.serial)) {
        const enriched = enrichBoardInfo(data);
        renderActiveBoardHeaderBadge(enriched);
        updateNavLinksWithActiveBoard(enriched.board_id);
        return enriched;
      }
    }
  } catch (e) {}

  // 3. Fallback to sessionStorage / localStorage if server unreachable
  try {
    const stored = sessionStorage.getItem('aoi_active_board') || localStorage.getItem('aoi_active_board');
    if (stored) {
      const parsed = JSON.parse(stored);
      if (parsed && (parsed.board_id || parsed.serial)) {
        const enriched = enrichBoardInfo(parsed);
        renderActiveBoardHeaderBadge(enriched);
        updateNavLinksWithActiveBoard(enriched.board_id);
        return enriched;
      }
    }
  } catch (e) {}

  // 4. Clean standard default to TB005 master
  const def = enrichBoardInfo({ board_id: 'TB005', serial: 'TB005', verdict: 'PASS' });
  renderActiveBoardHeaderBadge(def);
  updateNavLinksWithActiveBoard(def.board_id);
  return def;
}

function enrichBoardInfo(raw) {
  const bId = String(raw.board_id || raw.serial || 'TB005').trim().toUpperCase();
  const catalog = getScenarioCatalogEntry(bId);
  return {
    ...raw,
    board_id: bId,
    serial: bId,
    scenario_id: bId,
    scenario_name: raw.scenario_name || catalog.name,
    defect_type: raw.defect_type || catalog.defect_type,
    defect_description: raw.defect_description || catalog.defect_desc,
    solder_applicable: catalog.solder_applicable,
    verdict: raw.verdict || catalog.default_verdict,
    health_index: raw.health_index ?? (catalog.default_verdict === 'PASS' ? 1.0 : (bId === 'TB032' ? 0.0 : 0.85)),
    defective_components: raw.defective_components ?? (catalog.default_verdict === 'PASS' ? 0 : 1),
    image_url: raw.image_url || `/evaluation/test_boards/${bId}.png`
  };
}

// Function for any page to subscribe to live board changes
function onGlobalActiveBoardChange(callback) {
  if (typeof callback !== 'function') return;

  if (aoiSyncBroadcast) {
    aoiSyncBroadcast.addEventListener('message', (event) => {
      if (event.data && event.data.type === 'AOI_BOARD_CHANGED') {
        const enriched = enrichBoardInfo(event.data.data);
        renderActiveBoardHeaderBadge(enriched);
        updateNavLinksWithActiveBoard(enriched.board_id);
        callback(enriched);
      }
    });
  }

  window.addEventListener('storage', (event) => {
    if (event.key === 'aoi_active_board' && event.newValue) {
      try {
        const enriched = enrichBoardInfo(JSON.parse(event.newValue));
        renderActiveBoardHeaderBadge(enriched);
        updateNavLinksWithActiveBoard(enriched.board_id);
        callback(enriched);
      } catch (e) {}
    }
  });

  window.addEventListener('aoi_board_changed', (event) => {
    if (event.detail) {
      const enriched = enrichBoardInfo(event.detail);
      renderActiveBoardHeaderBadge(enriched);
      updateNavLinksWithActiveBoard(enriched.board_id);
      callback(enriched);
    }
  });
}

// --- 3. GLOBAL HEADER ACTIVE BOARD CONTEXT BADGE ---
function renderActiveBoardHeaderBadge(boardInfo) {
  if (!boardInfo) return;
  const header = document.querySelector('header.ind-header');
  if (!header) return;

  let badge = document.getElementById('activeBoardGlobalBadge');
  if (!badge) {
    badge = document.createElement('div');
    badge.className = 'active-board-badge';
    badge.id = 'activeBoardGlobalBadge';
    badge.setAttribute('title', 'Active Inspection Context synchronized across all suite views');

    const telemPanel = header.querySelector('.telemetry-panel');
    if (telemPanel) {
      header.insertBefore(badge, telemPanel);
    } else {
      header.appendChild(badge);
    }
  }

  const bId = String(boardInfo.board_id || boardInfo.serial || 'TB005').trim().toUpperCase();
  const name = boardInfo.scenario_name || getScenarioCatalogEntry(bId).name;
  const v = (boardInfo.verdict || 'PASS').toUpperCase();
  const vClass = v === 'PASS' ? 'pass' : (v === 'REWORK' ? 'rework' : 'fail');

  badge.innerHTML = `
    <div class="active-board-tag">
      <i class="fa-solid fa-microchip"></i>
      <span>ACTIVE: <strong>${bId}</strong></span>
      <span class="active-board-verdict-pill ${vClass}">${v}</span>
    </div>
    <div class="active-board-name" title="${name}">${name}</div>
  `;
}

// --- 4. SHARED DROPDOWN SYNCHRONIZER HELPER ---
function syncDropdownToActiveBoard(selectElement, activeBoardId) {
  if (!selectElement || !activeBoardId) return;
  const targetId = String(activeBoardId).trim().toUpperCase();

  let found = false;
  for (const opt of selectElement.options) {
    if (opt.value && opt.value.toUpperCase() === targetId) {
      selectElement.value = opt.value;
      found = true;
      break;
    }
  }

  if (!found) {
    const catalog = getScenarioCatalogEntry(targetId);
    let opt = selectElement.querySelector('option[data-dynamic-active="true"]');
    if (!opt) {
      opt = document.createElement('option');
      opt.setAttribute('data-dynamic-active', 'true');
      selectElement.insertBefore(opt, selectElement.firstChild);
    }
    opt.value = targetId;
    opt.textContent = `⚡ Live Active: ${targetId} - ${catalog.name}`;
    selectElement.value = targetId;
  }
}

// --- 5. INITIALIZATION ON DOM READY ---
document.addEventListener('DOMContentLoaded', () => {
  // Auto-highlight active multi-page navigation button based on current URL path
  const path = window.location.pathname;
  const navLinks = document.querySelectorAll('.ind-nav-menu a.nav-tab-btn');

  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href) {
      const cleanHref = href.split('?')[0];
      if (cleanHref === path || (path === '/' && cleanHref === '/') || (path === '' && cleanHref === '/')) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    }
  });

  // Global Server Health Polling
  checkGlobalServerHealth();
  setInterval(checkGlobalServerHealth, 10000);

  // Initialize and render global active board badge immediately
  getGlobalActiveBoard().then(active => {
    renderActiveBoardHeaderBadge(active);
    updateNavLinksWithActiveBoard(active.board_id);
  });
});

async function checkGlobalServerHealth() {
  const telemServer = document.getElementById('telemServer');
  if (!telemServer) return;
  try {
    const resp = await fetch('/health');
    if (resp.ok) {
      const data = await resp.json();
      telemServer.textContent = `SMT LINE 01 ONLINE • ${data.depth_engine_type || '3D Leveled'}`;
      telemServer.className = 'telem-val text-pass';
    }
  } catch (e) {
    telemServer.textContent = 'LINE OFFLINE (Reconnecting...)';
    telemServer.className = 'telem-val text-fail';
  }
}
