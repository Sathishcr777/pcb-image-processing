
import os

html_code = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>3D X-Ray (AXI) Volumetric Board Tomography — Enterprise</title>

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&family=Outfit:wght@500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

  <!-- Three.js & OrbitControls -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>

  <link rel="stylesheet" href="/static/styles.css">
  <style>
    .viewport-3d-container {
      position: relative;
      width: 100%;
      height: calc(100vh - 200px);
      min-height: 600px;
      background: radial-gradient(circle at center, #0f172a 0%, #060913 100%);
      border-radius: 12px;
      border: 1px solid #1E293B;
      overflow: hidden;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
    }
    #webglCanvas {
      width: 100%;
      height: 100%;
      display: block;
    }
    .hud-overlay-top-left {
      position: absolute;
      top: 16px;
      left: 16px;
      background: rgba(15, 23, 42, 0.92);
      backdrop-filter: blur(10px);
      border: 1px solid #334155;
      padding: 12px 18px;
      border-radius: 8px;
      color: #FFFFFF;
      z-index: 10;
    }
    .hud-overlay-top-right {
      position: absolute;
      top: 16px;
      right: 16px;
      background: rgba(15, 23, 42, 0.92);
      backdrop-filter: blur(10px);
      border: 1px solid #0284c7;
      padding: 14px 18px;
      border-radius: 8px;
      color: #FFFFFF;
      min-width: 280px;
      z-index: 10;
      box-shadow: 0 8px 24px rgba(0,0,0,0.6);
    }
    .hud-controls-bottom {
      position: absolute;
      bottom: 16px;
      left: 16px;
      right: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(15, 23, 42, 0.94);
      backdrop-filter: blur(10px);
      border: 1px solid #334155;
      padding: 12px 20px;
      border-radius: 8px;
      z-index: 10;
      flex-wrap: wrap;
      gap: 12px;
    }
    .mode-pill-btn {
      background: #1e293b;
      border: 1px solid #334155;
      color: #94a3b8;
      padding: 6px 12px;
      border-radius: 6px;
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
    .hud-slider {
      cursor: pointer;
      accent-color: #38bdf8;
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
          <div class="brand-sub">Enterprise 3D X-Ray (AXI) Volumetric Board Tomography</div>
        </div>
      </div>
      <div class="standards-pills">
        <span class="pill pill-standard"><i class="fa-solid fa-radiation"></i> 16-Layer CT Volume</span>
        <span class="pill pill-version"><i class="fa-solid fa-certificate"></i> IPC-A-610 Class 3</span>
        <span class="pill pill-standard"><i class="fa-solid fa-layer-group"></i> Multi-Layer Laminography</span>
      </div>
    </div>
    <div class="telemetry-panel">
      <div class="telem-item">
        <div class="telem-dot active"></div>
        <div class="telem-info">
          <span class="telem-label">3D X-RAY CORE</span>
          <span class="telem-val text-pass">VOLUMETRIC RAYTRACER ACTIVE</span>
        </div>
      </div>
    </div>
  </header>

  <!-- Multi-Page Industrial Navigation Menu -->
  <nav class="ind-nav-menu">
    <a href="/" class="nav-tab-btn"><i class="fa-solid fa-camera-retro"></i> Live Inspection</a>
    <a href="/photometric-studio" class="nav-tab-btn"><i class="fa-solid fa-wand-magic-sparkles"></i> 3D Photometric Studio</a>
    <a href="/xray-studio" class="nav-tab-btn active"><i class="fa-solid fa-radiation"></i> 3D X-Ray Studio</a>
    <a href="/photometric" class="nav-tab-btn"><i class="fa-solid fa-layer-group"></i> Photometric Stereo</a>
    <a href="/metrology" class="nav-tab-btn"><i class="fa-solid fa-ruler-combined"></i> IPC-A-610 Metrology</a>
    <a href="/analytics" class="nav-tab-btn"><i class="fa-solid fa-chart-pie"></i> Statistical Analytics</a>
    <a href="/spc" class="nav-tab-btn"><i class="fa-solid fa-chart-line"></i> SPC Control Charts</a>
    <a href="/msa" class="nav-tab-btn"><i class="fa-solid fa-flask"></i> Gage R&R (MSA)</a>
    <a href="/cfx" class="nav-tab-btn"><i class="fa-solid fa-satellite-dish"></i> Industry 4.0 CFX</a>
    <a href="/audit" class="nav-tab-btn"><i class="fa-solid fa-file-shield"></i> ISO 9001 Audit</a>
  </nav>

  <main style="padding: 16px 24px; max-width: 1720px; margin: 0 auto;">

    <!-- 3D X-Ray Viewport Container -->
    <div class="viewport-3d-container">
      <canvas id="webglCanvas"></canvas>

      <!-- Top-Left HUD: Board Status & Scenario Selector -->
      <div class="hud-overlay-top-left">
        <div style="font-size: 11px; color: #38BDF8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
          <i class="fa-solid fa-radiation"></i> 3D X-Ray Board Scenario
        </div>
        <div id="hudScenarioTitle" style="font-size: 15px; font-weight: 800; color: #FFFFFF; font-family: var(--font-outfit);">
          Full Multi-Layer PCB X-Ray Radiograph
        </div>
        <div style="margin-top: 6px; display: flex; align-items: center; gap: 8px;">
          <select id="boardScenarioSelect" class="ind-select" style="padding: 4px 10px; font-size: 11px; background: #0f172a; color: #38bdf8; border: 1px solid #0284c7; border-radius: 4px;" onchange="loadPresetScenario(this.value)">
            <option value="golden" selected>Master Board — 4-Layer Power & Signal Bus (IPC Class 3)</option>
            <option value="bga_defect">BGA Inspection — Solder Ball C4 Voiding (31.4% Defect)</option>
            <option value="qfn_pth">Power Subsystem — QFN Thermal Pad & PTH Vias</option>
          </select>
          <label class="mode-pill-btn" style="padding: 4px 10px; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;">
            <i class="fa-solid fa-upload"></i> Upload Image
            <input type="file" id="imageUploadInput" accept="image/*" style="display: none;" onchange="handleImageUpload(event)">
          </label>
        </div>
      </div>

      <!-- Top-Right HUD: Telemetry & Selected Feature Inspector -->
      <div class="hud-overlay-top-right">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 6px; margin-bottom: 8px;">
          <span style="font-size: 11px; font-weight: 800; color: #38bdf8; text-transform: uppercase;">
            <i class="fa-solid fa-crosshairs"></i> 3D X-Ray Feature Probe
          </span>
          <span id="ipcBadge" class="badge" style="background: rgba(16,185,129,0.2); color: #10b981; border: 1px solid #059669; font-size: 9px; padding: 1px 6px; border-radius: 3px;">IPC CLASS 3</span>
        </div>
        <div style="font-size: 12px; display: flex; flex-direction: column; gap: 4px;">
          <div style="display: flex; justify-content: space-between;">
            <span style="color: #94a3b8;">Target:</span>
            <span id="probeTarget" style="font-weight: 700; color: #f8fafc; font-family: var(--font-mono);">U1 FPGA BGA-64 (Solder Spheres)</span>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span style="color: #94a3b8;">X-Ray Attenuation:</span>
            <span id="probeAttenuation" style="font-weight: 700; color: #38bdf8; font-family: var(--font-mono);">High (&mu; = 14.8 cm⁻¹)</span>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span style="color: #94a3b8;">Solder Void Ratio:</span>
            <span id="probeVoid" style="font-weight: 700; color: #ef4444; font-family: var(--font-mono);">31.4% (Ball C4 Exceeds 25%)</span>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span style="color: #94a3b8;">Subsurface Depth:</span>
            <span id="probeDepth" style="font-weight: 700; color: #c084fc; font-family: var(--font-mono);">Z = 350 µm (Equatorial Plane)</span>
          </div>
        </div>
      </div>

      <!-- Bottom HUD: Interactive 3D X-Ray Controls -->
      <div class="hud-controls-bottom">
        
        <!-- Left: X-Ray View Modes & Colormaps -->
        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
          <span style="font-size: 11px; font-weight: 700; color: #94a3b8;">Colormap:</span>
          <button class="mode-pill-btn active" onclick="setColormap('bone', this)"><i class="fa-solid fa-bone"></i> Medical Bone</button>
          <button class="mode-pill-btn" onclick="setColormap('inferno', this)"><i class="fa-solid fa-fire"></i> Inferno Density</button>
          <button class="mode-pill-btn" onclick="setColormap('gray', this)"><i class="fa-solid fa-circle-half-stroke"></i> Monochrome</button>
          <button class="mode-pill-btn" onclick="setColormap('jet', this)"><i class="fa-solid fa-rainbow"></i> Jet</button>
        </div>

        <!-- Center: Camera Angles & Exploded View -->
        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
          <button class="mode-pill-btn" onclick="setCameraView('isometric')"><i class="fa-solid fa-cube"></i> Isometric 3D</button>
          <button class="mode-pill-btn" onclick="setCameraView('top')"><i class="fa-solid fa-camera"></i> Top AOI</button>
          <button class="mode-pill-btn" onclick="setCameraView('side')"><i class="fa-solid fa-arrows-up-down"></i> Side (Z-Stack)</button>
          <button id="btnAutoRotate" class="mode-pill-btn" onclick="toggleAutoRotate()"><i class="fa-solid fa-rotate"></i> Auto-Rotate</button>
        </div>

        <!-- Right: Interactive Sliders -->
        <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
          
          <!-- Substrate Opacity Slider -->
          <div style="display: flex; align-items: center; gap: 8px;">
            <label style="font-size: 11px; color: #cbd5e1; font-weight: 600;"><i class="fa-solid fa-eye-low-vision"></i> X-Ray Opacity:</label>
            <input type="range" id="xrayOpacitySlider" min="0.05" max="0.95" value="0.45" step="0.05" class="hud-slider" style="width: 80px;" oninput="updateSubstrateOpacity(this.value)">
          </div>

          <!-- Multi-Layer Exploded Stack Slider -->
          <div style="display: flex; align-items: center; gap: 8px;">
            <label style="font-size: 11px; color: #cbd5e1; font-weight: 600;"><i class="fa-solid fa-bars"></i> Exploded Stack:</label>
            <input type="range" id="explodedSlider" min="0" max="30" value="0" step="1" class="hud-slider" style="width: 80px;" oninput="updateExplodedStack(this.value)">
          </div>

          <!-- Z-Clipping Slicer Slider -->
          <div style="display: flex; align-items: center; gap: 8px;">
            <label style="font-size: 11px; color: #cbd5e1; font-weight: 600;"><i class="fa-solid fa-scissors"></i> Z-Clip:</label>
            <input type="range" id="zClipSlider" min="0" max="1600" value="1600" step="50" class="hud-slider" style="width: 80px;" oninput="updateZClip(this.value)">
          </div>

        </div>

      </div>

    </div>

  </main>

  <script>
    let scene, camera, renderer, controls;
    let pcbBodyMesh = null, topLayerMesh = null, innerCopperMesh = null, solderLayerMesh = null, bottomLayerMesh = null;
    let bgaBallsGroup = new THREE.Group();
    let thtPinsGroup = new THREE.Group();
    let qfnLeadframeGroup = new THREE.Group();
    let isAutoRotating = true;
    let currentColorMap = "bone";
    let textureLoader = new THREE.TextureLoader();

    const boardW = 110, boardL = 75, boardT = 2.4;

    function init() {
      const canvas = document.getElementById("webglCanvas");
      const container = canvas.parentElement;

      scene = new THREE.Scene();
      scene.background = new THREE.Color(0x060913);

      camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
      camera.position.set(0, 75, 95);

      renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
      renderer.setSize(container.clientWidth, container.clientHeight);
      renderer.setPixelRatio(window.devicePixelRatio);
      renderer.localClippingEnabled = true;

      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.05;
      controls.autoRotate = isAutoRotating;
      controls.autoRotateSpeed = 1.2;

      const ambLight = new THREE.AmbientLight(0xffffff, 0.85);
      scene.add(ambLight);

      const dirLight = new THREE.DirectionalLight(0x38bdf8, 1.3);
      dirLight.position.set(60, 90, 60);
      scene.add(dirLight);

      const backLight = new THREE.DirectionalLight(0xf97316, 0.9);
      backLight.position.set(-60, -40, -60);
      scene.add(backLight);

      const grid = new THREE.GridHelper(220, 44, 0x1e293b, 0x0f172a);
      grid.position.y = -12;
      scene.add(grid);

      scene.add(bgaBallsGroup);
      scene.add(thtPinsGroup);
      scene.add(qfnLeadframeGroup);

      buildFull3DXRayBoard();

      window.addEventListener("resize", onWindowResize);
      animate();
    }

    async function buildFull3DXRayBoard(customData = null) {
      if (pcbBodyMesh) scene.remove(pcbBodyMesh);
      if (topLayerMesh) scene.remove(topLayerMesh);
      if (innerCopperMesh) scene.remove(innerCopperMesh);
      if (solderLayerMesh) scene.remove(solderLayerMesh);
      if (bottomLayerMesh) scene.remove(bottomLayerMesh);

      while(bgaBallsGroup.children.length > 0) bgaBallsGroup.remove(bgaBallsGroup.children[0]);
      while(thtPinsGroup.children.length > 0) thtPinsGroup.remove(thtPinsGroup.children[0]);
      while(qfnLeadframeGroup.children.length > 0) qfnLeadframeGroup.remove(qfnLeadframeGroup.children[0]);

      let data = customData;
      if (!data) {
        const res = await fetch(`/api/xray/full-board?colormap=${currentColorMap}`);
        data = await res.json();
      }

      const topTex = textureLoader.load(data.layers_base64?.top || data.image_base64);
      const innerTex = textureLoader.load(data.layers_base64?.inner || data.image_base64);
      const solderTex = textureLoader.load(data.layers_base64?.solder || data.image_base64);
      const bottomTex = textureLoader.load(data.layers_base64?.bottom || data.image_base64);

      const substrateGeo = new THREE.BoxGeometry(boardW, boardT, boardL);
      const substrateMat = new THREE.MeshPhysicalMaterial({
        color: 0x0c2738,
        metalness: 0.1,
        roughness: 0.2,
        transmission: 0.85,
        transparent: true,
        opacity: 0.45,
        reflectivity: 0.6
      });
      pcbBodyMesh = new THREE.Mesh(substrateGeo, substrateMat);
      scene.add(pcbBodyMesh);

      const planeGeo = new THREE.PlaneGeometry(boardW, boardL);
      const topMat = new THREE.MeshStandardMaterial({
        map: topTex,
        transparent: true,
        opacity: 0.85,
        roughness: 0.4
      });
      topLayerMesh = new THREE.Mesh(planeGeo, topMat);
      topLayerMesh.rotation.x = -Math.PI / 2;
      topLayerMesh.position.y = boardT / 2 + 0.05;
      scene.add(topLayerMesh);

      const innerMat = new THREE.MeshStandardMaterial({
        map: innerTex,
        transparent: true,
        opacity: 0.90,
        metalness: 0.8,
        roughness: 0.2
      });
      innerCopperMesh = new THREE.Mesh(planeGeo, innerMat);
      innerCopperMesh.rotation.x = -Math.PI / 2;
      innerCopperMesh.position.y = 0;
      scene.add(innerCopperMesh);

      const bottomMat = new THREE.MeshStandardMaterial({
        map: bottomTex,
        transparent: true,
        opacity: 0.80,
        roughness: 0.4
      });
      bottomLayerMesh = new THREE.Mesh(planeGeo, bottomMat);
      bottomLayerMesh.rotation.x = Math.PI / 2;
      bottomLayerMesh.position.y = -boardT / 2 - 0.05;
      scene.add(bottomLayerMesh);

      build3DBgaMatrix();
      build3DPthVias();
      build3DQfnLeadframe();
    }

    function build3DBgaMatrix() {
      const rows = 8, cols = 8, pitch = 3.2, ballRad = 1.1;
      const startX = -10, startZ = 2;

      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const px = startX + (c - cols / 2) * pitch;
          const pz = startZ + (r - rows / 2) * pitch;
          const py = boardT / 2 + 0.6;

          const isDefect = (r === 2 && c === 3);
          const isWarn = (r === 5 && c === 6);

          const ballGeo = new THREE.SphereGeometry(ballRad, 20, 20);
          const ballMat = new THREE.MeshPhysicalMaterial({
            color: isDefect ? 0xef4444 : (isWarn ? 0xf59e0b : 0x94a3b8),
            metalness: 0.85,
            roughness: 0.2,
            transmission: 0.6,
            transparent: true,
            opacity: 0.8
          });
          const ballMesh = new THREE.Mesh(ballGeo, ballMat);
          ballMesh.position.set(px, py, pz);
          bgaBallsGroup.add(ballMesh);

          if (isDefect || isWarn) {
            const voidGeo = new THREE.SphereGeometry(ballRad * (isDefect ? 0.65 : 0.45), 14, 14);
            const voidMat = new THREE.MeshStandardMaterial({
              color: 0xff1111,
              emissive: 0xaa0000,
              emissiveIntensity: 0.8
            });
            const voidMesh = new THREE.Mesh(voidGeo, voidMat);
            voidMesh.position.set(px + 0.2, py, pz - 0.2);
            bgaBallsGroup.add(voidMesh);
          }
        }
      }
    }

    function build3DPthVias() {
      const viaCoords = [
        { x: -35, z: -15, fill: 0.94 },
        { x: -35, z: -5, fill: 0.88 },
        { x: -35, z: 5, fill: 0.62 },
        { x: -35, z: 15, fill: 0.91 }
      ];

      viaCoords.forEach(v => {
        const barrelGeo = new THREE.CylinderGeometry(2.4, 2.4, boardT + 1.2, 24, 1, true);
        const barrelMat = new THREE.MeshStandardMaterial({ color: 0xd97706, side: THREE.DoubleSide, metalness: 0.8 });
        const barrelMesh = new THREE.Mesh(barrelGeo, barrelMat);
        barrelMesh.position.set(v.x, 0, v.z);
        thtPinsGroup.add(barrelMesh);

        const pinGeo = new THREE.CylinderGeometry(1.1, 1.1, boardT + 3.0, 16);
        const pinMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.9 });
        const pinMesh = new THREE.Mesh(pinGeo, pinMat);
        pinMesh.position.set(v.x, 0, v.z);
        thtPinsGroup.add(pinMesh);
      });
    }

    function build3DQfnLeadframe() {
      const qfnGeo = new THREE.BoxGeometry(16, 1.2, 16);
      const qfnMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.5, transparent: true, opacity: 0.7 });
      const qfnMesh = new THREE.Mesh(qfnGeo, qfnMat);
      qfnMesh.position.set(26, boardT / 2 + 0.7, -10);
      qfnLeadframeGroup.add(qfnMesh);

      const padGeo = new THREE.BoxGeometry(10, 0.4, 10);
      const padMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8, metalness: 0.9 });
      const padMesh = new THREE.Mesh(padGeo, padMat);
      padMesh.position.set(26, boardT / 2 + 0.2, -10);
      qfnLeadframeGroup.add(padMesh);
    }

    function updateSubstrateOpacity(val) {
      if (pcbBodyMesh) {
        pcbBodyMesh.material.opacity = parseFloat(val);
      }
    }

    function updateExplodedStack(val) {
      const sep = parseFloat(val) * 0.4;
      if (topLayerMesh) topLayerMesh.position.y = (boardT / 2 + 0.05) + sep * 1.5;
      if (bgaBallsGroup) bgaBallsGroup.position.y = sep * 1.2;
      if (innerCopperMesh) innerCopperMesh.position.y = 0;
      if (bottomLayerMesh) bottomLayerMesh.position.y = (-boardT / 2 - 0.05) - sep * 1.5;
    }

    function updateZClip(val) {
      const depthRatio = parseFloat(val) / 1600.0;
      const clipY = (depthRatio - 0.5) * boardT * 2.5;
      const clipPlane = new THREE.Plane(new THREE.Vector3(0, -1, 0), clipY + 2.0);
      renderer.clippingPlanes = [clipPlane];
    }

    function setColormap(cm, btnEl) {
      currentColorMap = cm;
      document.querySelectorAll(".hud-controls-bottom .mode-pill-btn").forEach(b => {
        if (b.innerText.includes("Medical") || b.innerText.includes("Inferno") || b.innerText.includes("Monochrome") || b.innerText.includes("Jet")) {
          b.classList.remove("active");
        }
      });
      if (btnEl) btnEl.classList.add("active");
      buildFull3DXRayBoard();
    }

    function setCameraView(mode) {
      if (mode === "isometric") {
        camera.position.set(0, 75, 95);
      } else if (mode === "top") {
        camera.position.set(0, 110, 0);
      } else if (mode === "side") {
        camera.position.set(0, 2, 110);
      }
      controls.target.set(0, 0, 0);
      controls.update();
    }

    function toggleAutoRotate() {
      isAutoRotating = !isAutoRotating;
      controls.autoRotate = isAutoRotating;
      const btn = document.getElementById("btnAutoRotate");
      if (btn) btn.classList.toggle("active", isAutoRotating);
    }

    async function handleImageUpload(e) {
      const file = e.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append("file", file);
      formData.append("colormap", currentColorMap);

      document.getElementById("hudScenarioTitle").innerText = `Uploaded: ${file.name}`;
      try {
        const res = await fetch("/api/xray/upload", { method: "POST", body: formData });
        const data = await res.json();
        buildFull3DXRayBoard(data);
      } catch (err) {
        console.error("Upload tomography error:", err);
      }
    }

    function loadPresetScenario(scenario) {
      if (scenario === "golden") {
        document.getElementById("hudScenarioTitle").innerText = "Full Multi-Layer PCB X-Ray Radiograph";
        document.getElementById("ipcBadge").innerText = "IPC CLASS 3";
        document.getElementById("probeTarget").innerText = "Master Multi-Layer PCB Core";
        document.getElementById("probeVoid").innerText = "0.0% (Zero Critical Voids)";
        document.getElementById("probeVoid").style.color = "#10b981";
      } else if (scenario === "bga_defect") {
        document.getElementById("hudScenarioTitle").innerText = "BGA Solder Sphere Voiding & HiP Inspection";
        document.getElementById("ipcBadge").innerText = "REJECT DEFECT";
        document.getElementById("probeTarget").innerText = "U1 BGA Ball C4";
        document.getElementById("probeVoid").innerText = "31.4% (Exceeds 25% IPC Limit)";
        document.getElementById("probeVoid").style.color = "#ef4444";
      } else {
        document.getElementById("hudScenarioTitle").innerText = "QFN Thermal Pad & PTH Barrel Fill Subsystem";
        document.getElementById("ipcBadge").innerText = "REWORK WARNING";
        document.getElementById("probeTarget").innerText = "J1 Pin 3 (62% Barrel Fill)";
        document.getElementById("probeVoid").innerText = "Pin 3 < 75% Vertical Fill Standard";
        document.getElementById("probeVoid").style.color = "#f59e0b";
      }
      buildFull3DXRayBoard();
    }

    function onWindowResize() {
      const container = document.getElementById("webglCanvas").parentElement;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    }

    function animate() {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }

    window.onload = init;
  </script>
</body>
</html>
"""

with open("server/static/xray_studio.html", "w", encoding="utf-8") as f:
    f.write(html_code)
print("Complete 3D X-Ray Volumetric Board Studio written successfully!")
