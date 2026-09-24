
import os

html_code = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Optical (OG) vs 3D X-Ray Multi-Modal Comparator | PCB AI Suite</title>

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&family=Outfit:wght@500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

  <link rel="stylesheet" href="/static/styles.css">
  <style>
    .comparator-layout {
      display: grid;
      grid-template-columns: 1.25fr 0.75fr;
      gap: 16px;
      margin-top: 14px;
    }
    .compare-viewport-card {
      background: #060913;
      border: 1px solid #1e293b;
      border-radius: 12px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      height: 600px;
      position: relative;
    }
    .compare-viewport-header {
      background: rgba(15, 23, 42, 0.92);
      padding: 10px 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #1e293b;
      z-index: 10;
    }
    .split-image-container {
      flex: 1;
      position: relative;
      background: #000;
      overflow: hidden;
      user-select: none;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .base-layer-img {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      object-fit: contain;
      pointer-events: none;
    }
    .overlay-clip-container {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
      pointer-events: none;
    }
    .overlay-layer-img {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      object-fit: contain;
      pointer-events: none;
    }
    .split-curtain-divider {
      position: absolute;
      top: 0;
      bottom: 0;
      width: 3px;
      background: #38bdf8;
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.9);
      cursor: ew-resize;
      z-index: 20;
    }
    .split-handle-knob {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 34px;
      height: 34px;
      background: #0284c7;
      border: 2px solid #ffffff;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
      font-size: 12px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.6);
    }
    .layer-badge {
      position: absolute;
      top: 14px;
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 700;
      font-family: var(--font-mono);
      z-index: 15;
      backdrop-filter: blur(8px);
    }
    .layer-badge-og {
      left: 14px;
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid #10b981;
      color: #10b981;
    }
    .layer-badge-xray {
      right: 14px;
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid #38bdf8;
      color: #38bdf8;
    }
    .studio-card {
      background: rgba(15, 23, 42, 0.75);
      border: 1px solid #334155;
      border-radius: 10px;
      padding: 14px 16px;
    }
    .studio-card-title {
      font-size: 12px;
      font-weight: 700;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .defect-card-row {
      background: rgba(30, 41, 59, 0.5);
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 10px 12px;
      margin-bottom: 10px;
      transition: all 0.2s ease;
      cursor: pointer;
    }
    .defect-card-row:hover {
      border-color: #0284c7;
      background: rgba(30, 41, 59, 0.8);
    }
    .defect-card-row.active {
      border-color: #38bdf8;
      box-shadow: 0 0 0 1px #38bdf8;
    }
    .mode-pill-btn {
      background: #1e293b;
      border: 1px solid #334155;
      color: #94a3b8;
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 11px;
      cursor: pointer;
      font-family: var(--font-mono, monospace);
      transition: all 0.2s;
    }
    .mode-pill-btn.active, .mode-pill-btn:hover {
      background: #0284c7;
      color: #fff;
      border-color: #38bdf8;
    }
  </style>
</head>
<body>

  <!-- Top Enterprise Industrial Header Bar -->
  <header class="ind-header">
    <div class="header-left">
      <div class="company-brand">
        <div class="brand-logo"><i class="fa-solid fa-microchip"></i></div>
        <div class="brand-meta">
          <div class="brand-name">PCB AI Metrology & AOI Station</div>
          <div class="brand-sub">Optical (OG) vs 3D X-Ray Multi-Modal Fusion Comparator</div>
        </div>
      </div>
      <div class="standards-pills">
        <span class="pill pill-standard"><i class="fa-solid fa-camera"></i> Optical AOI</span>
        <span class="pill pill-version"><i class="fa-solid fa-radiation"></i> 3D X-Ray AXI</span>
        <span class="pill pill-standard"><i class="fa-solid fa-code-compare"></i> Sub-Pixel Fusion</span>
      </div>
    </div>
    <div class="telemetry-panel">
      <div class="telem-item">
        <div class="telem-dot active"></div>
        <div class="telem-info">
          <span class="telem-label">MULTI-MODAL COMPARATOR</span>
          <span class="telem-val text-pass">SYNCHRONIZED VIEWPORTS</span>
        </div>
      </div>
    </div>
  </header>

  <!-- Multi-Page Industrial Navigation Menu -->
  <nav class="ind-nav-menu">
    <a href="/" class="nav-tab-btn"><i class="fa-solid fa-camera-retro"></i> Live Inspection</a>
    <a href="/3d-view" class="nav-tab-btn"><i class="fa-solid fa-cube"></i> 360° 3D Digital Twin</a>
    <a href="/photometric-studio" class="nav-tab-btn"><i class="fa-solid fa-wand-magic-sparkles"></i> 3D Photometric Studio</a>
    <a href="/xray-studio" class="nav-tab-btn"><i class="fa-solid fa-radiation"></i> 3D X-Ray Studio</a>
    <a href="/xray-comparator" class="nav-tab-btn active"><i class="fa-solid fa-code-compare"></i> Optical vs X-Ray Comparator</a>
    <a href="/photometric" class="nav-tab-btn"><i class="fa-solid fa-layer-group"></i> Photometric Stereo</a>
    <a href="/metrology" class="nav-tab-btn"><i class="fa-solid fa-ruler-combined"></i> IPC-A-610 Metrology</a>
    <a href="/analytics" class="nav-tab-btn"><i class="fa-solid fa-chart-pie"></i> Statistical Analytics</a>
    <a href="/spc" class="nav-tab-btn"><i class="fa-solid fa-chart-line"></i> SPC Control Charts</a>
    <a href="/msa" class="nav-tab-btn"><i class="fa-solid fa-flask"></i> Gage R&R (MSA)</a>
    <a href="/cfx" class="nav-tab-btn"><i class="fa-solid fa-satellite-dish"></i> Industry 4.0 CFX</a>
    <a href="/audit" class="nav-tab-btn"><i class="fa-solid fa-file-shield"></i> ISO 9001 Audit</a>
  </nav>

  <main style="padding: 16px 24px; max-width: 1720px; margin: 0 auto;">

    <!-- Top Explainer / Scenario Selector Bar -->
    <div style="background: rgba(15, 23, 42, 0.75); border: 1px solid #334155; padding: 12px 18px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 12px;">
      <div style="display: flex; align-items: center; gap: 12px;">
        <label style="font-size: 13px; font-weight: 700; color: #f8fafc;">
          <i class="fa-solid fa-sliders text-cyan"></i> Target Board Scenario:
        </label>
        <select id="boardSelect" class="ind-select" style="padding: 6px 14px; background: #0f172a; color: #38bdf8; border: 1px solid #0284c7; border-radius: 6px; font-weight: 600;" onchange="loadBoardScenario(this.value)">
          <option value="master" selected>Master Industrial FPGA & Power PCB (1280x720 High-Res)</option>
          <option value="dense">Dense Multi-Chip SMT Assembly (BGA + QFN + SOIC)</option>
          <option value="controller">Microcontroller Signal Processing Board (PTH Header)</option>
          <option value="standard">Standard IPC-A-610 Test Matrix Board</option>
        </select>
        <label class="mode-pill-btn" style="padding: 6px 12px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px;">
          <i class="fa-solid fa-upload"></i> Upload Custom Board
          <input type="file" id="customUpload" accept="image/*" style="display: none;" onchange="handleCustomBoardUpload(event)">
        </label>
      </div>

      <div style="display: flex; gap: 8px;">
        <button class="mode-pill-btn active" id="btnModeWipe" onclick="setComparisonMode('wipe')"><i class="fa-solid fa-arrows-left-right"></i> Wipe Curtain</button>
        <button class="mode-pill-btn" id="btnModeFusion" onclick="setComparisonMode('fusion')"><i class="fa-solid fa-layer-group"></i> Multi-Modal Alpha Fusion</button>
        <button class="mode-pill-btn" id="btnModeSide" onclick="setComparisonMode('side')"><i class="fa-solid fa-table-columns"></i> Side-by-Side Dual View</button>
        <button class="btn btn-secondary" style="font-size: 12px; padding: 4px 10px;" onclick="exportComparisonReport()"><i class="fa-solid fa-file-arrow-down"></i> Export Audit JSON</button>
      </div>
    </div>

    <!-- Main Comparator Layout -->
    <div class="comparator-layout">
      
      <!-- LEFT: Interactive Split / Fusion Comparison Viewport -->
      <div class="compare-viewport-card">
        <div class="compare-viewport-header">
          <div style="display: flex; align-items: center; gap: 8px;">
            <i class="fa-solid fa-code-compare text-cyan"></i>
            <span style="font-size: 12px; font-weight: 700; color: #f8fafc;" id="viewportTitle">
              Original (OG) Optical Surface vs 3D X-Ray Sub-Surface Radiograph
            </span>
          </div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 11px; color: #94a3b8;">X-Ray Colormap:</span>
            <select id="colormapSelect" class="ind-select" style="padding: 3px 8px; font-size: 11px; background: #1e293b; color: #38bdf8; border: 1px solid #334155; border-radius: 4px;" onchange="changeXrayColormap(this.value)">
              <option value="bone" selected>Medical Bone</option>
              <option value="inferno">Inferno Density</option>
            </select>
          </div>
        </div>

        <div class="split-image-container" id="splitContainer">
          
          <!-- Badges -->
          <div class="layer-badge layer-badge-og" id="badgeOg">OPTICAL CAMERA (SURFACE)</div>
          <div class="layer-badge layer-badge-xray" id="badgeXray">3D X-RAY (SUBSURFACE)</div>

          <!-- Base Image (OG Optical Board) -->
          <img id="imgOgBase" class="base-layer-img" src="/static/boards/board_master_og.png" alt="Original PCB Optical View" />

          <!-- Overlay Image Container (X-Ray Radiograph) -->
          <div class="overlay-clip-container" id="overlayContainer" style="width: 50%;">
            <img id="imgXrayOverlay" class="overlay-layer-img" src="/static/boards/board_master_xray_bone.png" alt="3D X-Ray Radiograph" />
          </div>

          <!-- Vertical Split Curtain Divider Line -->
          <div class="split-curtain-divider" id="splitDivider" style="left: 50%;">
            <div class="split-handle-knob">
              <i class="fa-solid fa-arrows-left-right"></i>
            </div>
          </div>

        </div>

        <!-- Bottom Controls Bar inside Viewport -->
        <div style="background: rgba(15, 23, 42, 0.9); border-top: 1px solid #1e293b; padding: 10px 16px; display: flex; justify-content: space-between; align-items: center;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 11px; font-weight: 700; color: #94a3b8;"><i class="fa-solid fa-sliders"></i> Multi-Modal Alpha Blend:</span>
            <input type="range" id="alphaSlider" min="0" max="100" value="50" style="width: 140px; cursor: pointer; accent-color: #38bdf8;" oninput="onAlphaSliderChange(this.value)">
            <span id="alphaLabel" style="font-size: 11px; font-family: var(--font-mono); color: #38bdf8; font-weight: 700;">50% Split</span>
          </div>

          <div style="display: flex; gap: 8px; font-size: 11px; color: #94a3b8;">
            <span><i class="fa-solid fa-circle" style="color: #10b981; font-size: 8px;"></i> Optical 2D Surface</span>
            <span>&bull;</span>
            <span><i class="fa-solid fa-circle" style="color: #38bdf8; font-size: 8px;"></i> 3D X-Ray Attenuation</span>
          </div>
        </div>
      </div>

      <!-- RIGHT: Sub-surface Defect Discovery & Discrepancy Inspector -->
      <div style="display: flex; flex-direction: column; gap: 14px;">
        
        <div class="studio-card">
          <div class="studio-card-title">
            <span><i class="fa-solid fa-shield-halved text-cyan"></i> Subsurface Defect Discovery</span>
            <span style="font-size: 10px; font-family: var(--font-mono); color: #ef4444;">2 Hidden Defects Detected</span>
          </div>
          <p style="font-size: 11px; color: #94a3b8; margin-top: -4px; margin-bottom: 12px;">
            Features that appear <strong>PASS</strong> on standard Optical AOI cameras, but fail <strong>IPC-A-610 Class 3</strong> under 3D X-Ray penetration:
          </p>

          <!-- Component Comparison Row 1: BGA -->
          <div class="defect-card-row active" onclick="focusComponent('bga', this)">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
              <span style="font-weight: 800; font-size: 12px; color: #f8fafc;">U1 FPGA Core BGA-64 (Solder Spheres)</span>
              <span class="badge" style="background: rgba(239,68,68,0.2); color: #ef4444; border: 1px solid #dc2626; font-size: 9px; padding: 1px 6px; border-radius: 3px;">X-RAY DEFECT</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 11px; margin-top: 6px;">
              <div style="background: rgba(15,23,42,0.6); padding: 6px 8px; border-radius: 4px; border-left: 2px solid #10b981;">
                <span style="color: #10b981; font-weight: 700; display: block;">Optical Camera View:</span>
                <span style="color: #cbd5e1;">Package aligned, pins occluded under epoxy (PASS)</span>
              </div>
              <div style="background: rgba(15,23,42,0.6); padding: 6px 8px; border-radius: 4px; border-left: 2px solid #ef4444;">
                <span style="color: #ef4444; font-weight: 700; display: block;">3D X-Ray Discovery:</span>
                <span style="color: #cbd5e1;">Ball C4 Voiding 31.4% (&gt;25% IPC Limit — FAIL)</span>
              </div>
            </div>
          </div>

          <!-- Component Comparison Row 2: QFN -->
          <div class="defect-card-row" onclick="focusComponent('qfn', this)">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
              <span style="font-weight: 800; font-size: 12px; color: #f8fafc;">U2 Power Management QFN-32 (Thermal Pad)</span>
              <span class="badge" style="background: rgba(16,185,129,0.2); color: #10b981; border: 1px solid #059669; font-size: 9px; padding: 1px 6px; border-radius: 3px;">X-RAY PASS</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 11px; margin-top: 6px;">
              <div style="background: rgba(15,23,42,0.6); padding: 6px 8px; border-radius: 4px; border-left: 2px solid #10b981;">
                <span style="color: #10b981; font-weight: 700; display: block;">Optical Camera View:</span>
                <span style="color: #cbd5e1;">Leadframe perimeter soldered (PASS)</span>
              </div>
              <div style="background: rgba(15,23,42,0.6); padding: 6px 8px; border-radius: 4px; border-left: 2px solid #10b981;">
                <span style="color: #10b981; font-weight: 700; display: block;">3D X-Ray Discovery:</span>
                <span style="color: #cbd5e1;">Thermal Ground Void Ratio 18.5% (&le;25% PASS)</span>
              </div>
            </div>
          </div>

          <!-- Component Comparison Row 3: PTH Header -->
          <div class="defect-card-row" onclick="focusComponent('pth', this)">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
              <span style="font-weight: 800; font-size: 12px; color: #f8fafc;">J1 Through-Hole Header (PTH Barrel Fill)</span>
              <span class="badge" style="background: rgba(239,68,68,0.2); color: #ef4444; border: 1px solid #dc2626; font-size: 9px; padding: 1px 6px; border-radius: 3px;">X-RAY DEFECT</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 11px; margin-top: 6px;">
              <div style="background: rgba(15,23,42,0.6); padding: 6px 8px; border-radius: 4px; border-left: 2px solid #10b981;">
                <span style="color: #10b981; font-weight: 700; display: block;">Optical Camera View:</span>
                <span style="color: #cbd5e1;">Top solder meniscus fully wetted (PASS)</span>
              </div>
              <div style="background: rgba(15,23,42,0.6); padding: 6px 8px; border-radius: 4px; border-left: 2px solid #ef4444;">
                <span style="color: #ef4444; font-weight: 700; display: block;">3D X-Ray Discovery:</span>
                <span style="color: #cbd5e1;">Pin 3 Barrel Fill 62% (&lt;75% IPC Min — FAIL)</span>
              </div>
            </div>
          </div>

        </div>

        <!-- Multi-Modal Synthesis Summary KPI Card -->
        <div class="studio-card" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; text-align: center;">
          <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid #334155; padding: 8px 10px; border-radius: 6px;">
            <div style="font-size: 10px; color: #94a3b8; font-weight: 600;">OPTICAL AOI SCORE</div>
            <div style="font-size: 15px; font-weight: 800; font-family: var(--font-mono); color: #10b981; margin-top: 2px;">98.4% (PASS)</div>
          </div>
          <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid #334155; padding: 8px 10px; border-radius: 6px;">
            <div style="font-size: 10px; color: #94a3b8; font-weight: 600;">3D X-RAY AXI SCORE</div>
            <div style="font-size: 15px; font-weight: 800; font-family: var(--font-mono); color: #ef4444; margin-top: 2px;">82.1% (REJECT)</div>
          </div>
          <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid #334155; padding: 8px 10px; border-radius: 6px;">
            <div style="font-size: 10px; color: #94a3b8; font-weight: 600;">FUSION VERDICT</div>
            <div style="font-size: 15px; font-weight: 800; font-family: var(--font-mono); color: #ef4444; margin-top: 2px;">REWORK REQ</div>
          </div>
        </div>

      </div>

    </div>

  </main>

  <script>
    let isDragging = false;
    let currentMode = "wipe";
    let activeColormap = "bone";
    let currentScenario = "master";

    const splitContainer = document.getElementById("splitContainer");
    const overlayContainer = document.getElementById("overlayContainer");
    const splitDivider = document.getElementById("splitDivider");
    const imgOgBase = document.getElementById("imgOgBase");
    const imgXrayOverlay = document.getElementById("imgXrayOverlay");

    function init() {
      setupSplitSlider();
      loadBoardScenario("master");
    }

    function setupSplitSlider() {
      splitContainer.addEventListener("mousedown", (e) => {
        isDragging = true;
        updateCurtainPosition(e);
      });

      window.addEventListener("mousemove", (e) => {
        if (!isDragging) return;
        updateCurtainPosition(e);
      });

      window.addEventListener("mouseup", () => {
        isDragging = false;
      });

      // Touch events for mobile/tablet
      splitContainer.addEventListener("touchstart", (e) => {
        isDragging = true;
        updateCurtainPosition(e.touches[0]);
      });
      window.addEventListener("touchmove", (e) => {
        if (!isDragging) return;
        updateCurtainPosition(e.touches[0]);
      });
      window.addEventListener("touchend", () => {
        isDragging = false;
      });
    }

    function updateCurtainPosition(e) {
      if (currentMode !== "wipe") return;
      const rect = splitContainer.getBoundingClientRect();
      const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
      const pct = (x / rect.width) * 100;

      overlayContainer.style.width = `${pct}%`;
      splitDivider.style.left = `${pct}%`;
      document.getElementById("alphaSlider").value = Math.round(pct);
      document.getElementById("alphaLabel").innerText = `${Math.round(pct)}% Split`;
    }

    function onAlphaSliderChange(val) {
      const pct = parseInt(val);
      if (currentMode === "wipe") {
        overlayContainer.style.width = `${pct}%`;
        splitDivider.style.left = `${pct}%`;
        document.getElementById("alphaLabel").innerText = `${pct}% Split`;
      } else if (currentMode === "fusion") {
        const opacity = pct / 100.0;
        imgXrayOverlay.style.opacity = opacity;
        document.getElementById("alphaLabel").innerText = `${pct}% X-Ray Blend`;
      }
    }

    function setComparisonMode(mode) {
      currentMode = mode;
      document.querySelectorAll(".mode-pill-btn").forEach(b => {
        if (b.id.startsWith("btnMode")) b.classList.remove("active");
      });

      if (mode === "wipe") {
        document.getElementById("btnModeWipe").classList.add("active");
        overlayContainer.style.width = "50%";
        overlayContainer.style.opacity = "1";
        imgXrayOverlay.style.opacity = "1";
        splitDivider.style.display = "block";
        document.getElementById("splitDivider").style.left = "50%";
        document.getElementById("badgeOg").style.display = "block";
        document.getElementById("badgeXray").style.display = "block";
      } else if (mode === "fusion") {
        document.getElementById("btnModeFusion").classList.add("active");
        overlayContainer.style.width = "100%";
        splitDivider.style.display = "none";
        imgXrayOverlay.style.opacity = "0.5";
        document.getElementById("alphaSlider").value = 50;
        document.getElementById("alphaLabel").innerText = "50% X-Ray Blend";
      } else if (mode === "side") {
        document.getElementById("btnModeSide").classList.add("active");
        overlayContainer.style.width = "50%";
        splitDivider.style.display = "block";
        document.getElementById("splitDivider").style.left = "50%";
      }
    }

    function loadBoardScenario(scenario) {
      currentScenario = scenario;
      const baseMap = {
        "master": "/static/boards/board_master_og.png",
        "dense": "/static/boards/board_dense_smt_og.png",
        "controller": "/static/boards/board_controller_og.png",
        "standard": "/static/boards/board_power_og.png"
      };

      const xrayMap = {
        "master": `/static/boards/board_master_xray_${activeColormap}.png`,
        "dense": `/static/boards/board_dense_smt_xray_${activeColormap}.png`,
        "controller": `/static/boards/board_controller_xray_${activeColormap}.png`,
        "standard": `/static/boards/board_power_xray_${activeColormap}.png`
      };

      imgOgBase.src = baseMap[scenario] || baseMap["master"];
      imgXrayOverlay.src = xrayMap[scenario] || xrayMap["master"];
    }

    function changeXrayColormap(cmap) {
      activeColormap = cmap;
      loadBoardScenario(currentScenario);
    }

    async function handleCustomBoardUpload(e) {
      const file = e.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append("file", file);
      formData.append("colormap", activeColormap);

      const reader = new FileReader();
      reader.onload = function(evt) {
        imgOgBase.src = evt.target.result;
      };
      reader.readAsDataURL(file);

      try {
        const res = await fetch("/api/xray/upload", { method: "POST", body: formData });
        const data = await res.json();
        imgXrayOverlay.src = data.image_base64;
      } catch (err) {
        console.error("Custom board upload error:", err);
      }
    }

    function focusComponent(compId, cardEl) {
      document.querySelectorAll(".defect-card-row").forEach(r => r.classList.remove("active"));
      if (cardEl) cardEl.classList.add("active");
    }

    function exportComparisonReport() {
      const report = {
        timestamp: new Date().toISOString(),
        board_scenario: currentScenario,
        standard: "IPC-A-610 Class 3 Multi-Modal Standard",
        optical_status: "PASS (Surface Meniscus Normal)",
        xray_status: "REJECT (Subsurface Voids in U1 BGA and J1 PTH)",
        comparator_mode: currentMode
      };
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
      const dl = document.createElement("a");
      dl.setAttribute("href", dataStr);
      dl.setAttribute("download", `COMPARISON_REPORT_${Date.now()}.json`);
      document.body.appendChild(dl);
      dl.click();
      dl.remove();
    }

    window.onload = init;
  </script>
</body>
</html>
"""

with open("server/static/xray_comparator.html", "w", encoding="utf-8") as f:
    f.write(html_code)
print("Created server/static/xray_comparator.html successfully!")
