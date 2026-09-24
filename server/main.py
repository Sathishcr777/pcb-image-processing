"""
FastAPI Enterprise Production REST Server — Advanced PCB AI Inspection Engine
Teams 5 & 6 - AI Deployment, Metrology & Industry 4.0 Production Hardening

Host: 0.0.0.0 | Port: 8080 / 8000
Includes Web UI Dashboard mounting at http://localhost:8080
"""

import os
import sys
import time
import json
import logging
import re
import hmac
import base64
import io
import cv2
import numpy as np
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header, Depends, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool

# Add project root to Python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from server.pipeline.aligner import PCBAligner
from server.pipeline.detector_2d import Detector2D
from server.pipeline.detector_depth import DetectorDepth
from server.pipeline.health_index import HealthIndexCalculator
from server.pipeline.visualizer import PCBVisualizer
from server.pipeline.metrology_engine import MetrologyEngine
from server.pipeline.cad_parser import CADParser
from server.pipeline.cfx_dispatcher import CFXDispatcher
from server.pipeline.photometric_stereo import PhotometricStereoEngine
from server.pipeline.solder_profiler import SolderProfilerEngine
from server.pipeline.xray_engine import XRayEngine
from server.audit.logger import AuditLogger

# Configure Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s", "level":"%(levelname)s", "logger":"%(name)s", "message":%(message)s}'
)
logger = logging.getLogger("pcb_aoi_advanced")

APP_ENV = os.getenv("PCB_AOI_ENV", "development").strip().lower()
API_KEY_ENV = os.getenv("PCB_AOI_API_KEY", "").strip()
API_KEY_FILE = os.getenv("PCB_AOI_API_KEY_FILE", "").strip()
AUTH_REQUIRED = os.getenv("PCB_AOI_REQUIRE_API_KEY", "1" if APP_ENV == "production" else "0").strip().lower() in {"1", "true", "yes", "on"}
MAX_UPLOAD_MB = int(os.getenv("PCB_AOI_MAX_UPLOAD_MB", "10"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
USE_DEPTH_MODEL = os.getenv("PCB_AOI_USE_DEPTH_MODEL", "0").strip().lower() in {"1", "true", "yes", "on"}
DEPTH_MODEL_NAME_OR_PATH = os.getenv("PCB_AOI_DEPTH_MODEL_NAME_OR_PATH", "").strip() or None
DEPTH_MODEL_TOKEN = os.getenv("PCB_AOI_DEPTH_MODEL_TOKEN", "").strip() or None
DEFAULT_ALLOWED_ORIGINS = ["*"]
AUDIT_DIR = os.getenv("PCB_AOI_AUDIT_DIR", os.path.join(os.path.dirname(__file__), "audit"))

app = FastAPI(
    title="Advanced PCB AI Inspection & Metrology System",
    version="v2.0-advanced",
    description="High-Reliability Enterprise IPC-A-610H AI Inspection, Sub-pixel Metrology & Industry 4.0 CFX Server"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Pipeline Module Instances
aligner = PCBAligner()
detector_2d = Detector2D()
detector_depth = DetectorDepth(
    use_model=USE_DEPTH_MODEL,
    model_name_or_path=DEPTH_MODEL_NAME_OR_PATH,
    hf_token=DEPTH_MODEL_TOKEN,
)
hi_calculator = HealthIndexCalculator()
visualizer = PCBVisualizer()
metrology_engine = MetrologyEngine(px_to_mm_scale=0.05)
cad_parser = CADParser(pcb_width_mm=100.0, pcb_height_mm=80.0)
cfx_dispatcher = CFXDispatcher(line_id="SMT-LINE-01", station_id="AOI-POST-REFLOW-01")
audit_logger = AuditLogger(log_dir=AUDIT_DIR)
photometric_engine = PhotometricStereoEngine()
solder_profiler = SolderProfilerEngine(px_to_um=2.5)
xray_engine = XRayEngine()

# Paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
REF_DIR = os.path.join(BASE_DIR, "reference")
CONFIG_PATH = os.path.join(BASE_DIR, "config", "components.json")
STATIC_DIR = os.path.join(BASE_DIR, "static")
EVAL_BOARDS_DIR = os.path.join(ROOT_DIR, "evaluation", "test_boards")
EVAL_DIR = EVAL_BOARDS_DIR
STATIC_BOARDS_DIR = os.path.join(STATIC_DIR, "boards")
os.makedirs(STATIC_BOARDS_DIR, exist_ok=True)

GOLDEN_IMG_PATH = os.path.join(REF_DIR, "golden_board.png")
GOLDEN_DEPTH_PATH = os.path.join(REF_DIR, "golden_depth.npy")

# Mount Static Files
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(REF_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/server/reference", StaticFiles(directory=REF_DIR), name="ref_dir")

CONFIG_DIR = os.path.join(BASE_DIR, "config")
if os.path.exists(CONFIG_DIR):
    app.mount("/server/config", StaticFiles(directory=CONFIG_DIR), name="config_dir")

if os.path.exists(EVAL_BOARDS_DIR):
    app.mount("/evaluation/test_boards", StaticFiles(directory=EVAL_BOARDS_DIR), name="eval_boards")

EVAL_REPORTS_DIR = os.path.join(ROOT_DIR, "evaluation", "reports")
os.makedirs(EVAL_REPORTS_DIR, exist_ok=True)
app.mount("/evaluation/reports", StaticFiles(directory=EVAL_REPORTS_DIR), name="eval_reports")

@app.get("/api/components")
def get_components():
    return load_components_config()

def load_components_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logger.exception("Failed to load components config")
    return []

def validate_board_serial(board_serial: str) -> str:
    serial = (board_serial or "").strip()
    if not serial:
        serial = "AUTO-SERIAL-001"
    serial = re.sub(r'[^A-Za-z0-9._\-]', '-', serial)
    serial = serial.strip('-') or "AUTO-SERIAL-001"
    return serial[:64].upper()

async def read_image_upload(file: UploadFile) -> bytes:
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="empty_image_payload")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="file_too_large")
    return contents

# Global Memory Cache
_REF_CACHE = {
    "ref_img": None,
    "ref_depth": None,
    "components": None
}

def get_reference_data():
    if _REF_CACHE["ref_img"] is None and os.path.exists(GOLDEN_IMG_PATH):
        _REF_CACHE["ref_img"] = cv2.imread(GOLDEN_IMG_PATH)

    if _REF_CACHE["ref_depth"] is None:
        if os.path.exists(GOLDEN_DEPTH_PATH):
            _REF_CACHE["ref_depth"] = np.load(GOLDEN_DEPTH_PATH)
        elif _REF_CACHE["ref_img"] is not None:
            _REF_CACHE["ref_depth"] = detector_depth.estimate_depth(_REF_CACHE["ref_img"])
            np.save(GOLDEN_DEPTH_PATH, _REF_CACHE["ref_depth"])

    if _REF_CACHE["components"] is None:
        _REF_CACHE["components"] = load_components_config()

    return _REF_CACHE["ref_img"], _REF_CACHE["ref_depth"], _REF_CACHE["components"]

def clear_reference_cache():
    _REF_CACHE["ref_img"] = None
    _REF_CACHE["ref_depth"] = None
    _REF_CACHE["components"] = None

_ACTIVE_INSPECTION_STATE = {
    "board_id": "TB005",
    "serial": "TB005",
    "verdict": "PASS",
    "defective_components": 0,
    "image_url": "/evaluation/test_boards/TB005.png",
    "overlay_image_b64": None,
    "depth_heatmap_b64": None,
    "components": [],
    "metrology": [],
    "updated_at": datetime.now(timezone.utc).isoformat()
}

@app.get("/api/active-board")
async def get_active_board():
    """
    Returns the currently active inspected board across all suite views.
    """
    return _ACTIVE_INSPECTION_STATE

@app.post("/api/active-board")
async def set_active_board(request: Request):
    """
    Allows setting the current active board across the suite.
    """
    try:
        data = await request.json()
        if isinstance(data, dict):
            for k, v in data.items():
                if k in _ACTIVE_INSPECTION_STATE:
                    _ACTIVE_INSPECTION_STATE[k] = v
            _ACTIVE_INSPECTION_STATE["updated_at"] = datetime.now(timezone.utc).isoformat()
        return {"status": "ok", "active_board": _ACTIVE_INSPECTION_STATE}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/")
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Advanced PCB AI Inspection Server Running."}

@app.get("/download-zip")
@app.get("/api/download-suite")
async def download_complete_suite():
    """
    Direct HTTP file download of the entire complete suite ZIP package.
    """
    import zipfile
    zip_path = os.path.join(ROOT_DIR, "PCB-Photometric-AOI-Suite-v4.0-Complete.zip")
    external_zip = os.path.abspath(os.path.join(ROOT_DIR, "..", "PCB-Photometric-AOI-Suite-v4.0-Complete.zip"))
    
    target_zip = external_zip if os.path.exists(external_zip) else zip_path

    if not os.path.exists(target_zip):
        exclude_dirs = {'__pycache__', '.pytest_cache', '.git', '.vscode', '.idea'}
        exclude_extensions = {'.pyc', '.pyo', '.pyd'}
        with zipfile.ZipFile(target_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            for root, dirs, files in os.walk(ROOT_DIR):
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                for file in files:
                    if file.endswith('.zip'):
                        continue
                    ext = os.path.splitext(file)[1].lower()
                    if ext in exclude_extensions:
                        continue
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, ROOT_DIR)
                    zipf.write(full_path, arcname=os.path.join("PCB-Photometric-AOI-Suite-v4.0", rel_path))

    return FileResponse(
        target_zip,
        media_type="application/zip",
        filename="PCB-Photometric-AOI-Suite-v4.0-Complete.zip",
        headers={"Content-Disposition": "attachment; filename=PCB-Photometric-AOI-Suite-v4.0-Complete.zip"}
    )

@app.get("/presentation")
async def serve_presentation():
    pres_path = os.path.join(STATIC_DIR, "presentation.html")
    if os.path.exists(pres_path):
        return FileResponse(pres_path)
    raise HTTPException(status_code=404, detail="Presentation deck not found")

@app.get("/photometric")
async def serve_photometric():
    ps_path = os.path.join(STATIC_DIR, "photometric.html")
    if os.path.exists(ps_path):
        return FileResponse(ps_path)
    raise HTTPException(status_code=404, detail="Photometric dashboard not found")

@app.get("/api/photometric/reconstruct")
async def api_photometric_reconstruct(sample_id: str = "ps_sample_optimal"):
    sample_path = os.path.join(STATIC_DIR, "photometric_samples", f"{sample_id}.png")
    if not os.path.exists(sample_path):
        sample_path = GOLDEN_IMG_PATH

    img = cv2.imread(sample_path)
    if img is None:
        raise HTTPException(status_code=404, detail="Sample image not found")

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    normals_vis, albedo_map, slope_map, height_map = await run_in_threadpool(photometric_engine.reconstruct_surface_normals, rgb)
    solder_eval = photometric_engine.classify_solder_joint(img)

    slope_colored = cv2.applyColorMap(((slope_map / 90.0) * 255.0).astype(np.uint8), cv2.COLORMAP_INFERNO)

    return {
        "sample_id": sample_id,
        "solder_evaluation": solder_eval,
        "mean_slope_deg": round(float(np.mean(slope_map)), 2),
        "peak_height_um": round(float(np.max(height_map)), 1),
        "rgb_base64": visualizer.to_base64(img),
        "normals_base64": visualizer.to_base64(normals_vis),
        "slope_heatmap_base64": visualizer.to_base64(slope_colored)
    }

@app.get("/xray-studio")
async def serve_xray_studio():
    xray_path = os.path.join(STATIC_DIR, "xray_studio.html")
    if os.path.exists(xray_path):
        return FileResponse(xray_path)
    raise HTTPException(status_code=404, detail="3D X-Ray Studio dashboard not found")

@app.get("/api/xray/full-board")
async def api_xray_full_board(colormap: str = "bone"):
    return await run_in_threadpool(xray_engine.get_full_board_radiograph, colormap=colormap)

@app.get("/api/xray/slice")
async def api_xray_slice(depth_um: float = 0.0, colormap: str = "bone"):
    return await run_in_threadpool(xray_engine.get_z_slice, depth_um=depth_um, colormap=colormap)

@app.get("/api/xray/bga-matrix")
async def api_xray_bga_matrix():
    return await run_in_threadpool(xray_engine.analyze_bga_voids)

@app.get("/api/xray/qfn")
async def api_xray_qfn():
    return await run_in_threadpool(xray_engine.analyze_qfn_thermal_pad)

@app.get("/api/xray/tht")
async def api_xray_tht():
    return await run_in_threadpool(xray_engine.analyze_tht_barrel_fill)

@app.post("/api/xray/upload")
async def api_xray_upload(file: UploadFile = File(...), colormap: str = Form("bone")):
    contents = await read_image_upload(file)
    nparr = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise HTTPException(status_code=400, detail="invalid_image_format")
    return await run_in_threadpool(xray_engine.process_custom_image, img_bgr=img_bgr, colormap=colormap)

@app.get("/photometric-studio")
async def serve_photometric_studio():
    studio_path = os.path.join(STATIC_DIR, "photometric_studio.html")
    if os.path.exists(studio_path):
        return FileResponse(studio_path)
    raise HTTPException(status_code=404, detail="Photometric studio dashboard not found")

@app.get("/api/studio/profile")
async def api_studio_profile(comp_id: str = "U1_PIN1", slice_pct: float = 50.0):
    sample_map = {
        "U1_PIN1": "ps_sample_optimal",
        "U2_PIN4": "ps_sample_excess",
        "C1_PAD_L": "ps_sample_tombstone",
        "R1_PAD_R": "ps_sample_insufficient",
        "D1_ANODE": "ps_sample_optimal"
    }
    sample_id = sample_map.get(comp_id, "ps_sample_optimal")
    sample_path = os.path.join(STATIC_DIR, "photometric_samples", f"{sample_id}.png")
    if not os.path.exists(sample_path):
        sample_path = GOLDEN_IMG_PATH

    img = cv2.imread(sample_path)
    if img is None:
        raise HTTPException(status_code=404, detail="Component image not found")

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    _, _, _, height_map = await run_in_threadpool(photometric_engine.reconstruct_surface_normals, rgb)

    slice_frac = float(slice_pct) / 100.0
    profile_data = solder_profiler.extract_cross_section_profile(height_map, slice_frac, "horizontal")
    volume_data = solder_profiler.compute_solder_volume(height_map)

    # Lead coplanarity simulated across 4 corners
    if comp_id.startswith("U"):
        coplanar = solder_profiler.compute_lead_coplanarity([138.0, 142.5, 136.0, 139.5] if comp_id == "U1_PIN1" else [140.0, 210.0, 135.0, 138.0])
    else:
        coplanar = solder_profiler.compute_lead_coplanarity([130.0, 135.0])

    return {
        "component_id": comp_id,
        "slice_pct": slice_pct,
        **profile_data,
        "volume_nl": volume_data["volume_nl"],
        "wetted_coverage_pct": volume_data["wetted_area_coverage_pct"],
        "coplanarity_delta_um": coplanar["coplanarity_delta_um"],
        "ipc_coplanarity_verdict": coplanar["ipc_coplanarity_verdict"]
    }

@app.get("/api/studio/export-obj")
async def api_studio_export_obj(comp_id: str = "U1_PIN1"):
    sample_map = {
        "U1_PIN1": "ps_sample_optimal",
        "U2_PIN4": "ps_sample_excess",
        "C1_PAD_L": "ps_sample_tombstone",
        "R1_PAD_R": "ps_sample_insufficient",
        "D1_ANODE": "ps_sample_optimal"
    }
    sample_id = sample_map.get(comp_id, "ps_sample_optimal")
    sample_path = os.path.join(STATIC_DIR, "photometric_samples", f"{sample_id}.png")
    if not os.path.exists(sample_path):
        sample_path = GOLDEN_IMG_PATH

    img = cv2.imread(sample_path)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    _, _, _, height_map = await run_in_threadpool(photometric_engine.reconstruct_surface_normals, rgb)

    obj_content = solder_profiler.generate_wavefront_obj(height_map, step=4)
    out_path = os.path.join(STATIC_DIR, f"{comp_id}_mesh.obj")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(obj_content)

    return FileResponse(out_path, media_type="text/plain", filename=f"{comp_id}_3d_mesh.obj")

@app.get("/health")
def get_health():
    ref_exists = os.path.exists(GOLDEN_IMG_PATH) and os.path.exists(GOLDEN_DEPTH_PATH)
    return {
        "status": "healthy",
        "system_version": "v2.0-advanced",
        "reference_loaded": ref_exists,
        "depth_engine_type": getattr(detector_depth, "model_name", "Gradient-Depth-Engine (Fallback)"),
        "features": [
            "IPC-A-610-Metrology",
            "3D-Substrate-Leveling",
            "CAD-Centroid-AutoIngestion",
            "Industry4.0-CFX-Dispatcher",
            "TriMetric-2D-Ensemble"
        ],
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }

@app.post("/set-reference")
async def set_reference(file: UploadFile = File(...)):
    contents = await read_image_upload(file)
    np_arr = np.frombuffer(contents, np.uint8)
    golden_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if golden_img is None:
        raise HTTPException(status_code=400, detail="invalid_image_payload")

    os.makedirs(REF_DIR, exist_ok=True)
    cv2.imwrite(GOLDEN_IMG_PATH, golden_img)

    ref_depth = await run_in_threadpool(detector_depth.estimate_depth, golden_img)
    np.save(GOLDEN_DEPTH_PATH, ref_depth)

    _REF_CACHE["ref_img"] = golden_img
    _REF_CACHE["ref_depth"] = ref_depth
    _REF_CACHE["components"] = load_components_config()

    return {
        "status": "success",
        "message": "Golden reference set and substrate-leveled depth map generated.",
        "golden_shape": list(golden_img.shape)
    }

@app.post("/cad/import")
async def import_cad_centroid(file: UploadFile = File(...), pcb_width_mm: float = Form(100.0), pcb_height_mm: float = Form(80.0)):
    """
    Auto-generates component inspection ROIs from standard SMT Pick-and-Place Centroid CSV.
    """
    contents = await file.read()
    csv_text = contents.decode("utf-8", errors="ignore")
    
    ref_img, _, _ = get_reference_data()
    img_shape = ref_img.shape if ref_img is not None else (720, 1080, 3)

    cad_parser.pcb_width_mm = pcb_width_mm
    cad_parser.pcb_height_mm = pcb_height_mm
    components = cad_parser.parse_centroid_csv(csv_text, img_shape)

    if not components:
        raise HTTPException(status_code=400, detail="Unable to parse CAD centroid file format")

    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(components, f, indent=2)

    _REF_CACHE["components"] = components

    return {
        "status": "success",
        "message": f"Successfully parsed {len(components)} component footprints from SMT CAD file.",
        "component_count": len(components),
        "components": components
    }

@app.post("/inspect")
async def inspect_board(
    file: UploadFile = File(...),
    board_serial: str = Form("AUTO-SERIAL-001")
):
    start_time = time.time()
    board_serial = validate_board_serial(board_serial)

    ref_img, ref_depth, components = get_reference_data()

    if ref_img is None or ref_depth is None:
        raise HTTPException(status_code=503, detail="reference_not_set")

    contents = await read_image_upload(file)
    np_arr = np.frombuffer(contents, np.uint8)
    test_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if test_img is None:
        raise HTTPException(status_code=400, detail="invalid_image_payload")

    # 1. Optical Quality & Alignment Stage
    aligned_img, align_quality, _, align_stats = await run_in_threadpool(aligner.align, test_img, ref_img)

    if align_quality < 0.35:
        raise HTTPException(
            status_code=422,
            detail={"error": "alignment_failed", "alignment_quality": round(align_quality, 4), "stats": align_stats}
        )

    # 2. 2D Tri-Metric Ensemble Detection Stage
    results_2d = await run_in_threadpool(detector_2d.detect, aligned_img, ref_img, components)

    # 3. 3D Substrate-Leveled Depth Stage
    test_depth = await run_in_threadpool(detector_depth.estimate_depth, aligned_img)
    results_depth, leveling_stats = await run_in_threadpool(detector_depth.inspect, test_depth, ref_depth, components)

    # 4. IPC-A-610 Sub-Pixel Metrology Stage
    metrology_list = []
    for comp in components:
        x, y, w, h = comp["bbox_xywh"]
        r_test = aligned_img[y:y+h, x:x+w]
        r_ref = ref_img[y:y+h, x:x+w]
        metro_res = metrology_engine.inspect_component_metrology(r_test, r_ref, comp)
        metrology_list.append(metro_res)

    # 5. Health Index & Verdict Mapping
    hi_results = hi_calculator.compute(components, results_2d, results_depth)

    processing_ms = (time.time() - start_time) * 1000.0

    # 6. Industry 4.0 CFX Event Generation
    cfx_event = cfx_dispatcher.generate_inspection_event(board_serial, hi_results, metrology_list, processing_ms)

    # 7. Visualization Overlays
    overlay_img = await run_in_threadpool(visualizer.draw_overlay, aligned_img, hi_results, metrology_list, processing_ms)
    overlay_b64 = visualizer.to_base64(overlay_img)

    depth_heatmap_img = await run_in_threadpool(visualizer.draw_depth_heatmap, aligned_img, test_depth)
    depth_heatmap_b64 = visualizer.to_base64(depth_heatmap_img)

    golden_b64 = visualizer.to_base64(ref_img)

    # 8. ISO 9001 Audit Logging
    record = await run_in_threadpool(
        audit_logger.write_record,
        contents,
        hi_results,
        align_quality,
        processing_ms,
        board_serial
    )

    response_payload = {
        "record_id": record["record_id"],
        "alignment_quality": round(float(align_quality), 4),
        "optical_stats": align_stats,
        "health_index": hi_results["health_index"],
        "verdict": hi_results["verdict"],
        "total_components": hi_results["total_components"],
        "defective_components": hi_results["defective_components"],
        "processing_time_ms": round(processing_ms, 2),
        "per_component_results": hi_results["components"],
        "metrology": metrology_list,
        "substrate_leveling": leveling_stats,
        "cfx_telemetry": cfx_event,
        "golden_image_b64": golden_b64,
        "overlay_image_b64": overlay_b64,
        "depth_heatmap_b64": depth_heatmap_b64
    }

    _ACTIVE_INSPECTION_STATE["board_id"] = board_serial
    _ACTIVE_INSPECTION_STATE["serial"] = board_serial
    _ACTIVE_INSPECTION_STATE["verdict"] = hi_results["verdict"]
    _ACTIVE_INSPECTION_STATE["defective_components"] = hi_results["defective_components"]
    _ACTIVE_INSPECTION_STATE["overlay_image_b64"] = overlay_b64
    _ACTIVE_INSPECTION_STATE["depth_heatmap_b64"] = depth_heatmap_b64
    _ACTIVE_INSPECTION_STATE["components"] = hi_results["components"]
    _ACTIVE_INSPECTION_STATE["metrology"] = metrology_list
    _ACTIVE_INSPECTION_STATE["updated_at"] = datetime.now(timezone.utc).isoformat()

    if os.path.exists(os.path.join(EVAL_DIR, f"{board_serial}.png")):
        _ACTIVE_INSPECTION_STATE["image_url"] = f"/evaluation/test_boards/{board_serial}.png"
    else:
        custom_active_path = os.path.join(STATIC_BOARDS_DIR, "active_custom_board.png")
        cv2.imwrite(custom_active_path, test_img)
        _ACTIVE_INSPECTION_STATE["image_url"] = f"/static/boards/active_custom_board.png?t={int(time.time()*1000)}"

    return JSONResponse(content=response_payload, status_code=200)

@app.post("/api/xray/process-custom")
async def api_xray_process_custom(image: UploadFile = File(...)):
    try:
        contents = await read_image_upload(image)
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image encoding")
        
        # Dual-scale edge-preserving radiographic processing
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        inv = 255 - gray
        filtered = cv2.bilateralFilter(inv, 7, 50, 50)
        clahe_fine = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        clahe_broad = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(16, 16))
        c_fine = clahe_fine.apply(filtered)
        c_broad = clahe_broad.apply(filtered)
        combined_clahe = cv2.addWeighted(c_fine, 0.65, c_broad, 0.35, 0)
        blur = cv2.GaussianBlur(combined_clahe, (0, 0), 1.2)
        sharp = cv2.addWeighted(combined_clahe, 1.5, blur, -0.5, 0)
        norm_radiograph = cv2.normalize(np.clip(sharp, 0, 255).astype(np.uint8), None, 0, 255, cv2.NORM_MINMAX)

        bone_img = cv2.cvtColor(norm_radiograph, cv2.COLOR_GRAY2BGR)
        inferno_img = cv2.applyColorMap(norm_radiograph, cv2.COLORMAP_INFERNO)
        gray_img = cv2.cvtColor(norm_radiograph, cv2.COLOR_GRAY2BGR)

        # Total Blue Spectrum LUT (Deep Cobalt -> Electric Cyan -> White Glow)
        blue_lut = np.zeros((256, 1, 3), dtype=np.uint8)
        for i in range(256):
            t = i / 255.0
            if t < 0.35:
                s = t / 0.35
                b = int(10 + s * 170)
                g = int(5 + s * 45)
                r = int(2 + s * 8)
            elif t < 0.75:
                s = (t - 0.35) / 0.40
                b = int(180 + s * 75)
                g = int(50 + s * 150)
                r = int(10 + s * 30)
            else:
                s = (t - 0.75) / 0.25
                b = 255
                g = int(200 + s * 55)
                r = int(40 + s * 190)
            blue_lut[i, 0] = [b, g, r]
        jet_img = cv2.LUT(bone_img, blue_lut)

        def to_b64(im):
            _, buf = cv2.imencode('.png', im)
            return "data:image/png;base64," + base64.b64encode(buf).decode('utf-8')

        return JSONResponse({
            "status": "success",
            "modes": {
                "bone": to_b64(bone_img),
                "inferno": to_b64(inferno_img),
                "gray": to_b64(gray_img),
                "jet": to_b64(jet_img)
            }
        })
    except Exception as e:
        logger.exception("Error processing custom xray upload")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cfx/telemetry")
def get_cfx_telemetry():
    return cfx_dispatcher.get_recent_events(limit=20)

@app.get("/metrics")
def get_metrics():
    return audit_logger.get_summary_stats()

@app.get("/audit/logs")
def get_audit_logs():
    audit_file = os.path.join(BASE_DIR, "audit", "audit.jsonl")
    logs = []
    if os.path.exists(audit_file):
        with open(audit_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        logs.append(json.loads(line))
                    except Exception:
                        pass
    logs.reverse()
    return logs

# Multi-Page Route Handlers
@app.get("/", response_class=FileResponse)
def page_inspection():
    return os.path.join(STATIC_DIR, "index.html")

@app.get("/metrology", response_class=FileResponse)
def page_metrology():
    return os.path.join(STATIC_DIR, "metrology.html")

@app.get("/analytics", response_class=FileResponse)
def page_analytics():
    return os.path.join(STATIC_DIR, "analytics.html")

@app.get("/spc", response_class=FileResponse)
def page_spc():
    return os.path.join(STATIC_DIR, "spc.html")

@app.get("/msa", response_class=FileResponse)
def page_msa():
    return os.path.join(STATIC_DIR, "msa.html")

@app.get("/cfx", response_class=FileResponse)
def page_cfx():
    return os.path.join(STATIC_DIR, "cfx.html")

@app.get("/audit", response_class=FileResponse)
def page_audit():
    return os.path.join(STATIC_DIR, "audit.html")

@app.get("/3d-view")
def page_3d_view():
    return FileResponse(os.path.join(STATIC_DIR, "3d_view.html"), headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/xray-studio")
def page_xray_studio():
    return FileResponse(os.path.join(STATIC_DIR, "xray_studio.html"), headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/photometric-studio")
def page_photometric_studio():
    return FileResponse(os.path.join(STATIC_DIR, "photometric_studio.html"), headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/photometric")
def page_photometric():
    return FileResponse(os.path.join(STATIC_DIR, "photometric.html"), headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
