# PCB / Motherboard AI Inspection System
## Research-Grade Implementation Plan — 1-Week Sprint
### Standard: IPC-A-610H Class 2 | ISO 9001:2015 Clause 8.6 | IATF 16949 Traceability

---

> [!IMPORTANT]
> This plan is written to **manufacturing research standard**. All detection claims must be backed by confusion-matrix metrics (Precision, Recall, F1, FCR, Escape Rate), a GR&R study, and an ISO 9001-compliant audit trail. No metric may be reported without a defined test set and ground-truth labelling protocol.

---

## 1. Research Objectives

| # | Objective | Success Criterion |
|---|---|---|
| O1 | Detect missing PCB components from a single 2D image | Recall ≥ 90 %, Precision ≥ 85 % on a held-out labeled test set |
| O2 | Estimate component height/tilt anomaly from monocular depth | F1 ≥ 80 % on boards with controlled, physically-measured tilt/height deviations |
| O3 | Fuse both signals into an explainable Health Index | Health Index correlates monotonically with manually-assessed defect severity (Spearman ρ ≥ 0.85) |
| O4 | Demonstrate an end-to-end network pipeline (Laptop A → Ubiquiti → Laptop B) | Round-trip latency ≤ 10 s per board (95th percentile) |
| O5 | Achieve measurement system repeatability | %GR&R ≤ 30 % on Health Index scores across 3 lighting conditions |

---

## 2. Compliance & Standards Framework

### 2.1 IPC-A-610H Class 2 Acceptance Criteria (Target)

The system classifies each component ROI into one of three IPC-A-610H conditions:

| IPC Condition | System Verdict | Trigger |
|---|---|---|
| **Target** | PASS | Presence score ≥ 0.95, height penalty ≤ 0.05 |
| **Acceptable** | REWORK (advisory) | Presence score 0.80–0.94 OR height penalty 0.05–0.20 |
| **Defect** | FAIL | Presence score < 0.80 OR height penalty > 0.20 |

Key IPC-A-610H defects the system addresses:

| IPC Defect Category | Detection Method | Priority |
|---|---|---|
| Missing component | 2D SSIM diff + YOLO (upgrade) | P0 — Critical |
| Tombstoning (one end lifted) | Monocular depth gradient asymmetry | P0 — Critical |
| Component tilt/skew | Depth gradient magnitude vs. reference | P1 — High |
| Wrong height / not fully seated | Mean depth deviation vs. reference | P1 — High |
| Component shift (partial pad coverage) | Template centroid displacement | P2 — Medium |

> [!NOTE]
> Solder joint quality (bridging, voids, insufficient solder) requires sub-100 µm camera resolution not achievable with a laptop webcam. These defects are explicitly **out of scope** and documented as such in the research report.

### 2.2 ISO 9001:2015 Audit Trail Requirements (Clause 8.6)

Every `/inspect` API call must persist a structured inspection record containing:

| Field | Format | Standard Reference |
|---|---|---|
| `record_id` | UUID v4 | Unique traceability key |
| `board_serial` | String (manual entry or barcode) | IATF 16949 Cl. 8.5.2 |
| `timestamp_utc` | ISO 8601 | ISO 9001 Cl. 8.6 |
| `system_version` | Semantic version (e.g., `1.2.0`) | Software config. management |
| `model_version` | Model name + checkpoint hash | Reproducibility |
| `reference_image_id` | SHA-256 hash of golden reference | Baseline integrity |
| `raw_image_path` | Lossless PNG archive path | Evidence retention |
| `alignment_quality_score` | Float 0–1 (inlier ratio) | Validity gate |
| `per_component_results` | JSON array (see schema) | Per-part traceability |
| `health_index` | Float 0–1 | Summary score |
| `verdict` | Enum: PASS / REWORK / FAIL | Disposition |
| `ipc_class` | Enum: CLASS_1 / CLASS_2 / CLASS_3 | Applied standard |
| `operator_id` | String | Human accountability |
| `environmental_note` | String (lighting, temp, etc.) | Repeatability context |

Records are written as append-only JSON Lines (`.jsonl`) and must not be editable post-write. Retention: minimum 3 years.

### 2.3 Measurement System Analysis — GR&R Study Design

A **Crossed GR&R study (ANOVA method)** must be completed before any performance claims are made.

| Factor | Levels | Description |
|---|---|---|
| **Parts (n=10)** | 5 known-good boards + 5 boards with known defects | Covers the inspection range |
| **Appraisers (k=3)** | A: Morning diffuse light, B: Afternoon direct light, C: Camera raised +5 mm | Simulates real-world variation |
| **Trials (r=3)** | Each board inspected 3× per condition | Captures repeatability noise |
| **Total measurements** | 90 | 10 × 3 × 3 |

**Response variable:** Health Index score (continuous, 0–1)

**Acceptance target:** %GR&R < 30 % (acceptable for research prototype per AIAG MSA manual)
**Stretch target:** %GR&R < 10 % (production-acceptable)

**Attribute GR&R** (pass/fail verdict): Cohen's Kappa κ ≥ 0.80 (strong agreement) against manually-labelled ground truth.

---

## 3. System Architecture

### 3.1 Data Flow

```
 Laptop A                    Ubiquiti LAN               Laptop B — FastAPI Server
 ─────────────────           ────────────               ──────────────────────────────────────────
 Webcam / photo              Static IP                  POST /inspect
 capture_and_send.py  ─────► multipart/form-data ─────►      │
                                                              ▼
                                                    [GATE] Alignment Quality Check
                                                    (ORB + Homography inlier ratio ≥ 0.4)
                                                              │
                                               ┌─────────────┴──────────────┐
                                               ▼                            ▼
                                     2D Detection Module           Depth Inference Module
                                  (CLAHE → absdiff → SSIM)     (Depth Anything V2 Small)
                                  per-ROI presence score        per-ROI depth diff vs.
                                                                golden_depth.npy
                                               │                            │
                                               └─────────────┬──────────────┘
                                                             ▼
                                                   Health Index Engine
                                          HI = Σ(wᵢ × pᵢ × (1 − hᵢ)) / Σ(wᵢ)
                                                             │
                                                             ▼
                                                     Visualizer (OpenCV)
                                            Red circle = missing
                                            Orange triangle = height/tilt
                                            Yellow diamond = tombstone
                                            Green checkmark = pass
                                                             │
                                               ┌─────────────┴──────────────┐
                                               ▼                            ▼
                                         Overlay PNG                 inspection_record
                                         (base64 in response)        appended to audit.jsonl
```

### 3.2 Technology Stack

| Layer | Choice | Justification |
|---|---|---|
| Language | Python 3.10+ | Ecosystem support for all deps |
| API Server | FastAPI + Uvicorn | Async I/O, OpenAPI docs auto-generated |
| 2D Detection (baseline) | OpenCV 4.x — ORB + Homography + SSIM | Zero-training baseline, immediate results |
| 2D Detection (upgrade) | YOLOv8n fine-tuned on Roboflow PCB dataset | Higher mAP; runs in parallel track |
| Depth / 3D | Depth Anything V2 Small (ViT-S, Apache 2.0) | SOTA monocular depth, sharp edges, runs CPU/GPU |
| Image processing | OpenCV, scikit-image, NumPy | Standard CV stack |
| Audit logging | Python `logging` + JSON Lines `.jsonl` | Append-only, ISO 9001 compliant |
| Statistical analysis | SciPy, pandas | GR&R, Spearman ρ, ROC/PR curves |
| Camera client | Python `requests` + `cv2.VideoCapture` | Minimal Laptop A dependency |
| Testing | pytest + pytest-cov | Unit + integration coverage |

---

## 4. Project Structure

```
IMAGE PROCESSING/
│
├── server/                              # Laptop B — FastAPI inspection server
│   ├── main.py                          # App entry: /inspect, /set-reference, /health, /status
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── aligner.py                   # ORB + Homography alignment; alignment quality gate
│   │   ├── detector_2d.py               # CLAHE + absdiff + SSIM per-ROI presence detection
│   │   ├── detector_depth.py            # Depth Anything V2 inference + per-ROI depth diff
│   │   ├── health_index.py              # Weighted HI formula + IPC verdict mapping
│   │   └── visualizer.py               # OpenCV overlay (circles, triangles, diamonds, banner)
│   ├── audit/
│   │   ├── logger.py                    # ISO 9001 append-only audit record writer
│   │   └── audit.jsonl                  # Audit log (append-only, never overwritten)
│   ├── config/
│   │   └── components.json              # ROI definitions, component weights, IPC class setting
│   ├── reference/
│   │   ├── golden_board.png             # Lossless golden reference image
│   │   └── golden_depth.npy             # Precomputed reference depth map (float32)
│   ├── models/
│   │   └── yolov8n_pcb.pt               # Fine-tuned YOLO weights (optional upgrade)
│   ├── archive/                         # All raw inspection images (lossless PNG, never deleted)
│   └── requirements.txt
│
├── client/                              # Laptop A — camera capture + sender
│   ├── capture_and_send.py              # Webcam preview → keypress capture → POST → show result
│   └── requirements.txt
│
├── training/                            # Team 5: YOLO fine-tune (optional upgrade track)
│   ├── download_dataset.py              # Roboflow PCB dataset download
│   ├── train_yolo.py                    # YOLOv8n fine-tune script
│   └── evaluate_yolo.py                 # Per-class mAP50, mAP50-95, confusion matrix
│
├── evaluation/                          # Research-grade evaluation scripts (Team 5/6)
│   ├── build_test_set.py                # Labels CSV builder from annotated boards
│   ├── run_evaluation.py                # Precision/Recall/F1/FCR/Escape Rate computation
│   ├── grr_study.py                     # GR&R ANOVA study (90 measurements → %GR&R)
│   ├── roc_pr_curves.py                 # ROC curve, AUC, PR curve across thresholds
│   ├── spearman_correlation.py          # HI vs manual severity Spearman ρ
│   ├── spc_charts.py                    # p-chart, c-chart, DPMO trend across test boards
│   └── ablation_study.py               # 2D-only vs depth-only vs combined HI comparison
│
├── tests/
│   ├── test_aligner.py                  # Alignment quality score unit tests
│   ├── test_detector_2d.py              # Per-ROI presence detection correctness
│   ├── test_detector_depth.py           # Depth diff thresholds unit tests
│   ├── test_health_index.py             # Formula math + IPC verdict mapping
│   └── test_audit_logger.py            # Audit record schema validation
│
├── demo/
│   ├── run_demo.py                      # Full narrated demo runner
│   └── backup_demo/                     # Pre-recorded backup video (MP4)
│
├── docs/
│   ├── research_report.md               # Final research report (methods, results, analysis)
│   ├── api_contract.md                  # Team 4/5/6 API contract (endpoint specs)
│   └── camera_setup_sop.md             # Standard Operating Procedure for camera position
│
└── README.md                            # Setup + run instructions
```

---

## 5. Module Specifications

### 5.1 `server/pipeline/aligner.py`
**Purpose:** Register test board image to reference frame before all comparisons.

| Item | Detail |
|---|---|
| Algorithm | ORB feature detection (5 000 keypoints) + BFMatcher (Hamming) + Lowe's ratio test (0.75) + RANSAC Homography (reprojection threshold 5.0 px) |
| ECC fallback | `cv2.findTransformECC` (Euclidean motion, 5 000 iterations, ε = 1e-10) if ORB inlier count < 20 |
| **Alignment quality gate** | Inlier ratio = matched inliers / raw matches. If < 0.40 → reject image, return HTTP 422 with reason `"alignment_failed"`. This prevents false defect calls from a poorly framed board. |
| Output | `(aligned_image_bgr, homography_matrix_3x3, alignment_quality_score)` |
| Research note | Alignment quality score is recorded in every audit log entry; low scores trigger operator notification |

### 5.2 `server/pipeline/detector_2d.py`
**Purpose:** Per-component-ROI presence detection using classical computer vision.

| Step | Operation | Rationale |
|---|---|---|
| 1 | Convert both images to grayscale | Reduce colour-lighting sensitivity |
| 2 | CLAHE (clipLimit=2.0, tile 8×8) | Normalise uneven illumination across board |
| 3 | Gaussian blur 5×5 | Suppress pixel-level sensor noise |
| 4 | `cv2.absdiff` per ROI | Pixel-level presence signal |
| 5 | `skimage.ssim` per ROI (full=True) | Structural similarity — more robust to slight lighting shifts than raw diff |
| 6 | Morphological open/close (5×5 kernel) | Remove noise contours < 200 px² |
| 7 | Contour area filter (200 – 50 000 px²) | Reject thermal noise and board-edge artefacts |
| Output | Per ROI: `{presence_score, is_missing, ssim_score, diff_ratio, bbox_px}` |
| Threshold | SSIM < 0.70 OR diff_ratio > 0.30 → component flagged missing |
| YOLO upgrade | If `models/yolov8n_pcb.pt` exists, run YOLO detection in parallel; take max(SSIM-based score, YOLO confidence) as final presence score |

### 5.3 `server/pipeline/detector_depth.py`
**Purpose:** Per-component height and tilt anomaly detection via monocular depth estimation.

| Step | Operation |
|---|---|
| 1 | Load Depth Anything V2 Small (ViT-S) via HuggingFace `transformers` pipeline |
| 2 | Run model on aligned test image → `test_depth` (H×W float32) |
| 3 | Load `reference/golden_depth.npy` → `ref_depth` |
| 4 | Normalize both maps independently to [0, 1]: `d_norm = (d − d.min()) / (d.max() − d.min() + ε)` |
| 5 | Apply homography warp to `test_depth` (same H as RGB alignment) |
| 6 | Gaussian blur both maps (σ = 2.0) to suppress inference noise |
| 7 | **Per-ROI height check:** `mean_dev = |mean(test_roi) − mean(ref_roi)|` → height flag if > θ_height (default 0.12) |
| 8 | **Per-ROI tilt check:** Sobel gradient magnitude difference → tilt flag if > θ_tilt (default 0.08) |
| 9 | **Tombstone check:** Depth asymmetry between left/right halves of ROI > θ_tomb (default 0.15) |
| 10 | **height_penalty** = `min(1.0, mean_dev / (3 × θ_height))` — continuous penalty for HI formula |
| Output | Per ROI: `{height_deviation, tilt_deviation, height_flag, tilt_flag, tombstone_flag, height_penalty}` |

> [!NOTE]
> Depth Anything V2 is selected over MiDaS v3.1 for its superior edge sharpness on structured surfaces, better handling of reflective solder, and Apache 2.0 licence. AbsRel on NYU Depth V2: 0.056 vs MiDaS 0.083.

### 5.4 `server/pipeline/health_index.py`
**Purpose:** Fuse per-component signals into a single, explainable board-level score.

#### Formula (v1 — explainable, judge-friendly)

$$\text{HI} = \frac{\sum_{i=1}^{N} w_i \cdot p_i \cdot (1 - h_i)}{\sum_{i=1}^{N} w_i}$$

| Symbol | Definition | Range |
|---|---|---|
| $w_i$ | Criticality weight of component $i$ | 0.2 – 1.0 (from `components.json`) |
| $p_i$ | Presence score (SSIM confidence or YOLO conf) | 0.0 – 1.0 |
| $h_i$ | Height/tilt penalty | 0.0 – 1.0 |
| HI | Board Health Index | 0.0 – 1.0 |

#### Weight Table (default — adjustable in `components.json`)

| Component Type | Default Weight $w_i$ | IPC-A-610 Defect Priority |
|---|---|---|
| Main IC / CPU / MCU | 1.00 | Critical (P0) |
| RAM / Memory | 1.00 | Critical (P0) |
| Power regulators / VRMs | 0.90 | Critical (P0) |
| Crystal oscillators | 0.85 | High (P1) |
| Connectors (USB, HDMI, power) | 0.80 | High (P1) |
| Electrolytic capacitors | 0.70 | High (P1) — polarity-sensitive |
| Inductors / ferrite beads | 0.60 | Medium (P2) |
| Decoupling MLCC capacitors | 0.50 | Medium (P2) |
| SMD resistors | 0.40 | Medium (P2) |
| Heat sinks | 0.35 | Medium (P2) |
| LEDs / indicators | 0.25 | Low (P3) |
| Test points / fiducials | 0.20 | Cosmetic |

#### IPC-A-610 Verdict Mapping

| Health Index | Verdict | IPC Condition | Action |
|---|---|---|---|
| ≥ 0.95 | ✅ **PASS** | Target / Acceptable | Release to next stage |
| 0.80 – 0.94 | ⚠️ **REWORK** | Process Indicator | Flag for manual review |
| < 0.80 | ❌ **FAIL** | Defect | Quarantine board |

#### DPMO Computation (per inspection batch)

$$\text{DPMO} = \frac{\text{Total Defective Components}}{\text{Total Inspected Boards} \times \text{Components Per Board}} \times 10^6$$

Tracked in `spc_charts.py` and plotted as a p-chart and c-chart per batch.

### 5.5 `server/pipeline/visualizer.py`
**Purpose:** Produce a publication-quality annotated overlay image.

| Annotation | Shape | Colour | Trigger |
|---|---|---|---|
| Missing component | Filled circle + label | Red `(0, 0, 220)` | `is_missing = True` |
| Height anomaly | Upward triangle | Orange `(0, 140, 255)` | `height_flag = True` |
| Tombstone detected | Diamond | Yellow `(0, 220, 220)` | `tombstone_flag = True` |
| Tilt detected | Rotated square | Magenta `(200, 0, 200)` | `tilt_flag = True` |
| Component passed | Checkmark | Green `(0, 200, 80)` | All flags clear |
| Health Index banner | Top-of-image bar | Gradient (green→red by HI) | Always shown |
| Per-component score | Sub-label under marker | White text | Always shown |
| IPC verdict | Bold text, top-right | Colour-coded | Always shown |

### 5.6 `server/audit/logger.py`
**Purpose:** ISO 9001-compliant, append-only audit record writer.

- Opens `audit/audit.jsonl` in append mode (`'a'`) — never truncates
- Each record is one JSON object per line (JSON Lines format)
- Includes SHA-256 hash of the raw image for integrity verification
- Records are written **after** pipeline completes (success or controlled failure)
- Separate `audit_errors.jsonl` for pipeline exceptions (alignment failures, model errors)

### 5.7 `server/config/components.json`
**Purpose:** Declarative ROI definitions — single source of truth for inspection scope.

```json
{
  "ipc_class": "CLASS_2",
  "board_name": "Target PCB / Motherboard",
  "components": [
    {
      "id": "U1",
      "name": "Main Microcontroller",
      "type": "ic",
      "bbox_xywh": [120, 85, 160, 140],
      "weight": 1.0,
      "depth_check": true,
      "tilt_check": true,
      "tombstone_check": false,
      "notes": "QFP-64 package"
    },
    {
      "id": "C1",
      "name": "Bulk Decoupling Cap 100uF",
      "type": "electrolytic_capacitor",
      "bbox_xywh": [300, 210, 45, 55],
      "weight": 0.70,
      "depth_check": true,
      "tilt_check": false,
      "tombstone_check": false,
      "notes": "Polarity: stripe faces left"
    }
  ]
}
```

> [!IMPORTANT]
> `bbox_xywh` coordinates are defined on the **golden reference image coordinate frame** (after alignment). They must be annotated on Day 2 using the `docs/camera_setup_sop.md` procedure and validated by at least 2 team members before first use.

---

## 6. Evaluation Framework

### 6.1 Test Set Construction (Team 4 responsibility)

A structured test set must be built and frozen **before** any threshold tuning:

| Board Category | Count | Description |
|---|---|---|
| Known-good (golden) | 5 | All components present, correctly seated |
| Single missing component — critical (IC/power) | 5 | Remove one critical component per board |
| Single missing component — passive (cap/resistor) | 5 | Remove one passive per board |
| Multiple missing components | 5 | 2–4 removed per board |
| Tombstoned component | 3 | One 0402/0603 component intentionally standing vertical |
| Tilted component | 3 | Component physically tilted ~15°–30°, measured with protractor |
| Slightly shifted component | 3 | Component shifted ~50% off-pad |
| Board partially out of frame | 2 | Edge case: camera placement drift |
| **Total** | **31 boards** | |

**Ground truth labelling:** Each board's defect list labelled in `evaluation/test_labels.csv` with columns: `board_id, component_id, defect_type, physical_measurement_mm, annotator_id, annotation_date`.

### 6.2 Performance Metrics Reported

| Metric | Formula | Acceptable (Prototype) | Target |
|---|---|---|---|
| **Precision** | TP / (TP + FP) | ≥ 80 % | ≥ 90 % |
| **Recall (Detection Rate)** | TP / (TP + FN) | ≥ 88 % | ≥ 95 % |
| **F1 Score** | 2 × P × R / (P + R) | ≥ 84 % | ≥ 92 % |
| **False Call Rate (FCR)** | FP / (FP + TN) | ≤ 10 % | ≤ 5 % |
| **Escape Rate** | FN / (TP + FN) | ≤ 12 % | ≤ 5 % |
| **AUC-ROC** | Area under ROC curve | ≥ 0.88 | ≥ 0.95 |
| **Spearman ρ (HI vs severity)** | Rank correlation | ≥ 0.80 | ≥ 0.90 |
| **Alignment success rate** | Boards passing quality gate | ≥ 95 % | ≥ 98 % |

Metrics reported **separately per defect type** (missing / tombstone / tilt / shift) in addition to aggregate.

### 6.3 Ablation Study Design

To isolate the contribution of each pipeline component — a standard requirement in manufacturing research:

| Variant | 2D Detection | Depth Module | Expected Finding |
|---|---|---|---|
| **Baseline (2D only)** | ✅ SSIM + absdiff | ❌ Disabled | Good for missing parts; blind to height/tilt |
| **Depth only** | ❌ Disabled | ✅ Depth Anything V2 | Detects height/tilt; misses flat missing parts |
| **Combined (full system)** | ✅ | ✅ | Best overall F1 |
| **YOLO upgrade** | ✅ YOLOv8n | ✅ | Compare mAP vs SSIM baseline |

Each variant evaluated on the same 31-board test set. Results tabulated in `evaluation/ablation_study.py` and included in `docs/research_report.md`.

### 6.4 GR&R Study Protocol

Detailed procedure in `evaluation/grr_study.py`:

1. Select 10 boards from the test set (5 good, 5 defective, spanning HI range 0.2–1.0)
2. Under each of 3 conditions (morning light / afternoon light / camera +5 mm height), inspect each board 3 times without operator knowing previous result
3. Record 90 Health Index scores (10 × 3 × 3)
4. Compute `%GR&R` using ANOVA decomposition
5. Compute Cohen's Kappa κ for Pass/Rework/Fail verdict agreement
6. Report NDC (Number of Distinct Categories); must be ≥ 5

### 6.5 SPC Metrics (Batch-Level)

Computed per inspection batch in `evaluation/spc_charts.py`:

- **p-chart:** Fraction of boards failing per batch (control limits: `p̄ ± 3√(p̄(1−p̄)/n)`)
- **c-chart:** Defect count per board (control limits: `c̄ ± 3√c̄`)
- **DPMO trend:** Plotted across consecutive batches to show process improving over sprint days
- **Sigma level:** Derived from final DPMO (target: reach ≥ 3σ by Day 7)

---

## 7. API Contract (Teams 4 / 5 / 6 Interface)

### POST `/inspect`
```
Content-Type: multipart/form-data
Fields:
  image: File (JPEG/PNG, ≤ 10 MB)
  board_serial: str (optional, for audit trail)
  operator_id: str (optional)
  ipc_class: "CLASS_1" | "CLASS_2" | "CLASS_3" (default: CLASS_2)

Response 200:
{
  "record_id": "uuid",
  "health_index": 0.87,
  "verdict": "REWORK",
  "alignment_quality": 0.73,
  "missing_components": [{"id": "U2", "name": "...", "bbox": [...], "presence_score": 0.12}],
  "height_tilt_flags": [{"id": "C3", "height_flag": true, "tilt_flag": false, "height_penalty": 0.31}],
  "per_component": [...],
  "dpmo_estimate": 12500,
  "overlay_image_b64": "<base64 PNG>",
  "processing_time_ms": 3240
}

Response 422: {"error": "alignment_failed", "alignment_quality": 0.21, "action": "reposition board"}
Response 503: {"error": "reference_not_set", "action": "POST /set-reference first"}
```

### POST `/set-reference`
```
Content-Type: multipart/form-data
Fields:
  image: File — golden reference board (lossless PNG preferred)

Response 200:
{
  "reference_id": "sha256-hash",
  "depth_map_computed": true,
  "component_rois_loaded": 14,
  "timestamp_utc": "2026-01-15T09:30:00Z"
}
```

### GET `/health`
```
Response 200: {"status": "ok", "reference_loaded": true, "model_loaded": true, "version": "1.0.0"}
```

### GET `/metrics`
```
Response 200:
{
  "boards_inspected_session": 42,
  "pass_count": 35,
  "rework_count": 5,
  "fail_count": 2,
  "session_fpy": 0.833,
  "session_dpmo": 18500,
  "avg_processing_ms": 3100
}
```

---

## 8. Camera Setup Standard Operating Procedure (SOP)

> [!CAUTION]
> **Camera placement consistency is the single most critical physical parameter for this system.** Even a 3–5° angle change or a 5 cm distance shift will invalidate the depth diff entirely. This SOP must be followed before any reference capture and before every test board inspection session.

Full SOP documented in `docs/camera_setup_sop.md`:

1. Mark the laptop position on the table with tape (all four corners)
2. Mark the PCB placement position and orientation on the table
3. Record: distance from lens to board (cm), ambient light source, exposure setting
4. Capture a white-balance reference card under the same lighting
5. Verify: run alignment on a second photo of the reference board → alignment_quality ≥ 0.70 before proceeding
6. Repeat SOP check at the start of each new working session

---

## 9. Day-by-Day Sprint Schedule

### Day 1 — Environment, Network, Skeleton
| Team | Tasks |
|---|---|
| **Team 4** | Set up Ubiquiti static IP; verify Laptop A → Laptop B POST with a test image; physically mark camera + board position; document in camera SOP |
| **Team 5** | Install all Python deps; load Depth Anything V2 on a sample photo; confirm depth map output; set up project folder structure |
| **Team 6** | Scaffold FastAPI `main.py` with dummy `/inspect` returning hardcoded JSON; verify client `capture_and_send.py` receives the dummy response |

**Day 1 Exit Gate:** `curl -F "image=@test.jpg" http://LAPTOP_B_IP:8000/inspect` returns a 200 response.

---

### Day 2 — Data Collection, Reference Setup, Alignment
| Team | Tasks |
|---|---|
| **Team 4** | Photograph golden reference board (lossless PNG); photograph 10+ test boards with controlled defects; begin filling `test_labels.csv`; download Roboflow PCB dataset |
| **Team 5** | Implement `aligner.py`; run POST `/set-reference` with golden board; confirm `golden_depth.npy` saved; manually annotate `components.json` ROIs on golden board using an image editor |
| **Team 6** | Wire real Laptop A image into the endpoint; implement `audit/logger.py`; confirm audit records written to `audit.jsonl` |

**Day 2 Exit Gate:** Alignment quality score ≥ 0.70 on at least 8 of 10 test boards.

---

### Day 3 — Core Detection Pipeline End-to-End
| Team | Tasks |
|---|---|
| **Team 4** | Expand test set to 31 boards (all categories from §6.1); verify all images consistent framing |
| **Team 5** | Implement `detector_2d.py`; implement `detector_depth.py`; wire both into `main.py`; implement `health_index.py` with formula and IPC verdict |
| **Team 6** | Implement `visualizer.py` with all 5 annotation types + HI banner; implement `GET /metrics` endpoint |

**Day 3 Exit Gate:** Full pipeline returns meaningful (non-random) health index and overlay for a board with a deliberately removed IC (expected: HI < 0.5, red circle at IC location).

---

### Day 4 — Integration Checkpoint 1 (Full End-to-End)
| Team | Tasks |
|---|---|
| **All** | Full pipeline: Laptop A → Ubiquiti → Laptop B → detection → depth → HI → overlay → audit log |
| **Team 5** | Start YOLO fine-tune on Roboflow dataset (background, separate branch); freeze SSIM baseline |
| **Team 5** | Run initial `evaluation/run_evaluation.py` on test set; record baseline Precision/Recall/F1 |

**Day 4 Exit Gate:** Recall ≥ 80 % on the 31-board test set. If not met: review alignment quality gate and SSIM thresholds before tuning depth module.

> [!WARNING]
> **If pipeline is not connected by end of Day 4, cut the YOLO fine-tune track entirely.** The SSIM baseline + Depth Anything V2 combination is a complete, research-grade answer. Do not add features after Day 4 — only tune thresholds.

---

### Day 5 — Threshold Tuning & Accuracy
| Team | Tasks |
|---|---|
| **Team 4** | Supply additional hard-case boards; validate camera SOP still met; re-shoot reference if lighting has drifted |
| **Team 5** | Run `roc_pr_curves.py`; select operating point on ROC curve that maximises F1; update `θ_height`, `θ_tilt`, `θ_tomb` in config; run `ablation_study.py` (2D-only vs depth-only vs combined) |
| **Team 6** | Handle edge cases: board partially out of frame (alignment_quality gate), network timeout retry, missing `components.json` graceful error |

**Day 5 Exit Gate:** Recall ≥ 88 %, FCR ≤ 10 %.

---

### Day 6 — Full Testing, GR&R, Backup Video
| Team | Tasks |
|---|---|
| **All** | Full run across all 31 test boards; record final Precision/Recall/F1/FCR/Escape Rate |
| **Team 5** | Run `evaluation/grr_study.py` (90 measurements across 3 lighting conditions); compute %GR&R and Cohen's Kappa; run `spc_charts.py` — generate DPMO trend + p-chart |
| **Team 5** | **Freeze model/backend** — no threshold or code changes after 18:00 on Day 6 |
| **Team 6** | Record backup demo video (narrated, full pipeline, include overlay + JSON results on screen) |

**Day 6 Exit Gate:** All metrics computed and documented in `docs/research_report.md`. Backup video saved.

---

### Day 7 — Rehearsal & Report Finalisation
| Team | Tasks |
|---|---|
| **All** | Dry-run exact live demo in front of whole group |
| **Team 6** | Finalise `docs/research_report.md` with methods, results tables, ablation, GR&R results |
| **All** | Prep answers to judge questions (see §10) |

---

## 10. Likely Judge Questions — Research-Grade Answers

| Question | Research-Grade Answer |
|---|---|
| **"Is this real 3D or estimated?"** | "Option A (primary): Relative depth estimated from a single 2D image using Depth Anything V2 (Yang et al., 2024) — a zero-shot monocular depth foundation model achieving AbsRel 0.056 on NYU Depth V2. It does not produce metric millimetre measurements; it produces a consistent relative depth map that detects height/tilt anomalies when diffed against a reference. If Option B (stereo) were implemented, it would produce real metric depth from calibrated stereo cameras." |
| **"What are your detection rates?"** | Report the actual Precision/Recall/F1/FCR/Escape Rate from the test set evaluation. Never claim numbers not backed by the labelled test set. |
| **"How is this production-ready?"** | "The API contract is identical to what a trolley-mounted industrial camera would use — swapping Laptop A for a production camera is a config change, not a code change. The audit log meets ISO 9001:2015 Clause 8.6 traceability requirements." |
| **"What's your measurement system reliability?"** | "%GR&R = [actual value from grr_study.py]. Cohen's Kappa κ = [actual value]. Per AIAG MSA guidelines, < 30 % GR&R is acceptable for a research prototype." |
| **"Why monocular depth instead of a structured-light sensor?"** | "No PCB-specific depth ground truth dataset exists to validate a custom approach, and structured-light sensors (e.g., Koh Young moiré) are capital equipment costing $100k+. Monocular depth is the only technically sound option within this hardware and budget constraint, and is validated in this work for height/tilt anomaly detection via ablation study." |
| **"How does this compare to commercial AOI?"** | "Commercial 3D AOI (Koh Young Zenith) achieves FCR < 100 ppm at 10 µm resolution with a dedicated moiré 3D sensor. Our prototype achieves FCR ≈ [actual value] % at webcam resolution — a viable research proof-of-concept, not a production replacement. The value is demonstrating the feasibility of monocular depth as a low-cost 3D signal." |
| **"What are the limitations?"** | "Solder joint quality (bridging, voids) is out of scope — requires < 25 µm/pixel resolution. Depth estimation is sensitive to lighting consistency, mitigated by the camera SOP and CLAHE preprocessing. BGA component verification requires X-ray and is not addressed." |

---

## 11. Risk & Fallback Matrix

| Risk | Probability | Impact | Mitigation / Fallback |
|---|---|---|---|
| YOLO fine-tune underperforms SSIM baseline | Medium | Low | Ship with SSIM baseline — equally publishable; report both in ablation |
| Depth model false-positives on reflective solder | High | Medium | Increase `θ_height`; apply 2× Gaussian blur on depth map; document as limitation |
| Ubiquiti link drops during live demo | Low | High | Pre-recorded backup video; narrate over it |
| Camera framing drifts between sessions | Medium | High | Physical marks + SOP; alignment quality gate rejects drift automatically |
| Alignment fails on boards with few features | Medium | Medium | ECC fallback in `aligner.py`; if both fail → 422 error + operator prompt |
| Test set too small for reliable metrics | Medium | High | 31 boards minimum; report 95 % confidence intervals on all metrics |
| GR&R > 30 % | Medium | Medium | Document as limitation; recommend fixed camera rig for production version |
| Model download fails (no internet on day) | Low | High | Pre-download all model weights on Day 1; commit checkpoint hash to README |

---

## 12. Research Report Outline (`docs/research_report.md`)

1. **Abstract** — problem, approach, results summary
2. **Introduction** — industrial context, IPC-A-610 compliance motivation
3. **Related Work** — commercial AOI systems, monocular depth estimation (Depth Anything V2), template-based inspection
4. **Methodology**
   - System architecture
   - 2D detection pipeline
   - Depth estimation pipeline
   - Health Index formula derivation
   - IPC-A-610 verdict mapping
5. **Experimental Setup**
   - Hardware (Laptop A/B, Ubiquiti network)
   - Dataset (31 boards, defect categories, ground-truth labelling protocol)
   - Camera SOP
6. **Results**
   - Per-defect-type confusion matrices
   - Precision / Recall / F1 / FCR / Escape Rate (Table)
   - ROC curves (Figure)
   - Ablation study (Table — 2D only / depth only / combined)
   - GR&R study (%GR&R, Kappa, NDC)
   - SPC charts (DPMO trend, p-chart)
   - Health Index vs manual severity Spearman ρ
7. **Discussion** — comparison to commercial AOI benchmarks, limitations, out-of-scope defect types
8. **Conclusion & Future Work** — stereo upgrade path, fixed camera rig, metric depth calibration
9. **References** — IPC-A-610H, Depth Anything V2 paper, MiDaS paper, AIAG MSA manual
