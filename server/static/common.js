/* ==========================================================================
   SHARED INDUSTRIAL STATION CONTROLLER, NAVIGATION & GLOBAL BOARD SYNC
   ========================================================================== */

// Auto-highlight active multi-page navigation button based on current URL path
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;
  const navLinks = document.querySelectorAll('.ind-nav-menu a.nav-tab-btn');

  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href === path || (path === '/' && href === '/') || (path === '' && href === '/')) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });

  // Global Server Health Polling
  checkGlobalServerHealth();
  setInterval(checkGlobalServerHealth, 10000);
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

/* ==========================================================================
   GLOBAL AOI BOARD SYNCHRONIZATION SYSTEM
   Synchronizes the active inspected board simultaneously across all views:
   Live Inspection, 360 3D Twin, 3D Photometrics, 3D X-Ray, Metrology, etc.
   ========================================================================== */

const AOI_SYNC_CHANNEL_NAME = 'aoi_board_sync_channel';
let aoiSyncBroadcast = null;
try {
  aoiSyncBroadcast = new BroadcastChannel(AOI_SYNC_CHANNEL_NAME);
} catch (e) {
  console.warn("BroadcastChannel not supported", e);
}

// Function to broadcast active board change to all pages
function setGlobalActiveBoard(boardInfo) {
  if (!boardInfo) return;
  
  try {
    localStorage.setItem('aoi_active_board', JSON.stringify(boardInfo));
    localStorage.setItem('activeBoard3D', JSON.stringify({
      serial: boardInfo.serial || boardInfo.board_id,
      verdict: boardInfo.verdict || 'PASS',
      components: boardInfo.components || [],
      metrology: boardInfo.metrology || [],
      image_b64: boardInfo.image_b64 || boardInfo.overlay_b64
    }));
  } catch (err) {
    console.warn("localStorage write error", err);
  }

  if (aoiSyncBroadcast) {
    try {
      aoiSyncBroadcast.postMessage({ type: 'AOI_BOARD_CHANGED', data: boardInfo });
    } catch (err) {
      console.warn("BroadcastChannel post error", err);
    }
  }

  window.dispatchEvent(new CustomEvent('aoi_board_changed', { detail: boardInfo }));

  // Also push to backend if available
  fetch('/api/active-board', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(boardInfo)
  }).catch(() => {});
}

// Function for any page to get the current active board
async function getGlobalActiveBoard() {
  // Try localStorage first
  try {
    const local = localStorage.getItem('aoi_active_board');
    if (local) {
      const parsed = JSON.parse(local);
      if (parsed && (parsed.board_id || parsed.serial)) {
        return parsed;
      }
    }
  } catch (e) {}

  // Fallback to backend API
  try {
    const res = await fetch('/api/active-board');
    if (res.ok) {
      const data = await res.json();
      return data;
    }
  } catch (e) {}

  return null;
}

// Function for any page to subscribe to live board changes
function onGlobalActiveBoardChange(callback) {
  if (typeof callback !== 'function') return;

  if (aoiSyncBroadcast) {
    aoiSyncBroadcast.addEventListener('message', (event) => {
      if (event.data && event.data.type === 'AOI_BOARD_CHANGED') {
        callback(event.data.data);
      }
    });
  }

  window.addEventListener('storage', (event) => {
    if (event.key === 'aoi_active_board' && event.newValue) {
      try {
        callback(JSON.parse(event.newValue));
      } catch (e) {}
    }
  });

  window.addEventListener('aoi_board_changed', (event) => {
    if (event.detail) callback(event.detail);
  });
}
