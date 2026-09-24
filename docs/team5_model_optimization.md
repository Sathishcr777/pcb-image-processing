# Team 5 — Model Optimization & Backend Maintenance
## PCB / Motherboard AI Inspection System | 1-Week Sprint

---

### Team Members
| Name | Suggested Focus |
|---|---|
| Harini | 2D detection pipeline + Health Index formula |
| Anugraha | 2D detection pipeline + evaluation scripts |
| Rubachanderr | Depth Anything V2 inference pipeline + YOLO fine-tune |
| Mirra | Depth pipeline + GR&R study + SPC charts |

> **Internal split:** 2 people on 2D detection + Health Index + evaluation, 2 people on depth pipeline + YOLO fine-tune + statistical analysis.

---

### Team 5 Role Summary

Team 5 builds and owns the **core intelligence of the system** — the detection algorithms, the depth inference engine, the health index formula, the FastAPI backend, and all research-grade evaluation. The quality of the system's scientific claims rests entirely on Team 5's work.

**Core responsibilities:**
1. Set up the development environment and all Python dependencies
2. Implement the image alignment module
3. Implement the 2D missing-part detection module (SSIM + absdiff baseline)
4. Run Depth Anything V2 on the golden reference image → save `golden_depth.npy`
5. Implement the depth difference module for height/tilt anomaly detection
6. Build the Health Index formula and IPC-A-610 verdict mapping
7. Build the FastAPI `/inspect` and `/set-reference` endpoints
8. Run the complete evaluation suite (Precision/Recall/F1/FCR, ROC curves, ablation study, GR&R, SPC)
9. Fine-tune YOLOv8n on Roboflow dataset (optional upgrade track — only if baseline is solid)
10. **Freeze the backend on Day 6 at 18:00** — no changes after that except critical bugs

---

### Files Team 5 Owns

| File | Description |
|---|---|
| `server/main.py` | FastAPI application — all endpoints |
| `server/pipeline/aligner.py` | ORB + Homography alignment module |
| `server/pipeline/detector_2d.py` | CLAHE + SSIM + absdiff per-ROI detection |
| `server/pipeline/detector_depth.py` | Depth Anything V2 inference + depth diff |
| `server/pipeline/health_index.py` | Health Index formula + IPC verdict mapping |
| `server/config/components.json` | ROI definitions + component weights |
| `server/reference/golden_depth.npy` | Precomputed reference depth map |
| `server/requirements.txt` | All Python dependencies |
| `training/train_yolo.py` | YOLOv8n fine-tune script |
| `training/evaluate_yolo.py` | YOLO evaluation (mAP, confusion matrix) |
| `evaluation/run_evaluation.py` | Full system evaluation (Precision/Recall/F1/FCR) |
| `evaluation/ablation_study.py` | 2D-only vs depth-only vs combined comparison |
| `evaluation/grr_study.py` | GR&R ANOVA study (%GR&R, Cohen's Kappa) |
| `evaluation/roc_pr_curves.py` | ROC curve + AUC + PR curve across thresholds |
| `evaluation/spearman_correlation.py` | Health Index vs manual severity correlation |
| `evaluation/spc_charts.py` | DPMO trend, p-chart, c-chart |
| `tests/` | All unit tests |
| `docs/research_report.md` | Final research report (methods, results, analysis) |

---

### Environment Setup (Do on Day 1)

#### Python Environment

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows

# Install dependencies
pip install fastapi uvicorn[standard] python-multipart
pip install opencv-python opencv-contrib-python
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install transformers pillow numpy scipy pandas
pip install scikit-image scikit-learn
pip install ultralytics roboflow
pip install pytest pytest-cov
```

#### Pre-download Model Weights (Do on Day 1 — needs internet)

```python
# Run this once to cache Depth Anything V2 weights locally
from transformers import pipeline
pipe = pipeline(task="depth-estimation",
                model="depth-anything/Depth-Anything-V2-Small-hf")
print("Model loaded successfully")
```

> **IMPORTANT:** Pre-download on Day 1. Do not rely on internet being available on demo day.

---

### Day-by-Day Tasks

#### Day 1 — Environment + First Depth Inference

- [ ] Set up Python virtual environment on Laptop B; install all dependencies from `server/requirements.txt`
- [ ] Run Depth Anything V2 on **any sample photo** (e.g., a phone photo of a desk) — confirm the model loads and produces a depth map:
  ```python
  from transformers import pipeline
  from PIL import Image
  import numpy as np
  pipe = pipeline(task="depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")
  img = Image.open("sample.jpg")
  result = pipe(img)
  depth = np.array(result["depth"])
  print(f"Depth map shape: {depth.shape}, range: [{depth.min():.3f}, {depth.max():.3f}]")
  ```
- [ ] Confirm inference time on Laptop B's CPU — record it (expected: 1–4 seconds per image for ViT-S)
- [ ] Scaffold `server/main.py` with a FastAPI skeleton:
  - `POST /inspect` — accepts image, returns hardcoded dummy JSON (200)
  - `POST /set-reference` — accepts image, returns `{"status": "ok"}`
  - `GET /health` — returns `{"status": "ok", "reference_loaded": false}`
- [ ] Start Uvicorn: `uvicorn server.main:app --host 0.0.0.0 --port 8000`
- [ ] Share Laptop B's IP with Team 4 and Team 6

**Day 1 Exit Gate:** `curl -F "image=@any.jpg" http://localhost:8000/inspect` returns `{"health_index": 0.99, "verdict": "PASS"}` (dummy). Depth map confirmed working.

---

#### Day 2 — Alignment + Reference Depth Map

- [ ] Implement `server/pipeline/aligner.py`:
  ```
  Input:  reference_bgr, test_bgr (numpy arrays)
  Output: (aligned_bgr, homography_3x3, alignment_quality_score)
  Logic:  ORB(5000 features) → BFMatcher(NORM_HAMMING) → Lowe ratio test(0.75)
          → findHomography(RANSAC, 5.0px) → warpPerspective
          → If inlier_ratio < 0.20: try ECC fallback
          → If both fail: raise AlignmentError (caller returns HTTP 422)
  ```
- [ ] Once Team 4 delivers `reference/golden_board.png`:
  - Call `POST /set-reference` with the image
  - Run Depth Anything V2 on it → save result as `reference/golden_depth.npy`
  - Log: reference SHA-256 hash, timestamp, depth map shape
- [ ] Manually annotate `server/config/components.json`:
  - Open `reference/golden_board.png` in any image viewer
  - For each visible component, record bounding box [x, y, w, h] in pixels
  - Assign component type, name, criticality weight (see weight table in master plan)
  - Aim for at least 8–12 component ROIs to start
- [ ] Test alignment: run `aligner.py` on 5 test board images from Team 4; verify alignment_quality ≥ 0.70 on all

**Day 2 Exit Gate:** `POST /set-reference` saves `golden_depth.npy`. `components.json` has ≥ 8 ROIs. Alignment quality ≥ 0.70 on test boards.

---

#### Day 3 — 2D Detection + Depth Diff + Health Index

**Sub-team A (Harini + Anugraha) — 2D Detection & Health Index:**

- [ ] Implement `server/pipeline/detector_2d.py`:
  ```
  Input:  reference_bgr, aligned_test_bgr, component_rois (from components.json)
  Per ROI:
    1. Convert both to grayscale
    2. Apply CLAHE (clipLimit=2.0, tileGridSize=(8,8))
    3. Gaussian blur 5×5
    4. skimage.ssim(ref_roi, test_roi) → ssim_score
    5. cv2.absdiff → diff_ratio (% pixels > threshold 40)
    6. is_missing = (ssim_score < 0.70) OR (diff_ratio > 0.30)
    7. presence_score = max(0, min(1, ssim_score))
  Output: list of per-component dicts
  ```
- [ ] Implement `server/pipeline/health_index.py`:
  ```
  HI = Σ(wᵢ × pᵢ × (1 − hᵢ)) / Σ(wᵢ)
  verdict: HI ≥ 0.95 → PASS | 0.80–0.94 → REWORK | < 0.80 → FAIL
  Also compute: DPMO estimate for the batch
  ```

**Sub-team B (Rubachanderr + Mirra) — Depth Pipeline:**

- [ ] Implement `server/pipeline/detector_depth.py`:
  ```
  Input:  aligned_test_bgr, reference_depth (golden_depth.npy), homography, component_rois
  Steps:
    1. Run Depth Anything V2 on aligned_test_bgr → test_depth (HxW float32)
    2. Load reference/golden_depth.npy → ref_depth
    3. Normalize both: d_norm = (d - d.min()) / (d.max() - d.min() + 1e-8)
    4. Apply homography warp to test_depth (same H used for RGB)
    5. Gaussian blur both (σ=2.0) to suppress noise
    Per ROI:
      height_dev = |mean(test_roi_depth) - mean(ref_roi_depth)|
      tilt_dev   = Sobel gradient magnitude difference
      asymmetry  = |mean(left_half) - mean(right_half)|
      height_flag    = height_dev > θ_height (default 0.12)
      tilt_flag       = tilt_dev > θ_tilt (default 0.08)
      tombstone_flag = asymmetry > θ_tomb (default 0.15)
      height_penalty = min(1.0, height_dev / (3 × θ_height))
  Output: list of per-component depth dicts
  ```

**Both sub-teams — Wire into main.py:**
- [ ] Replace dummy `/inspect` response with real pipeline: align → detect_2d → detect_depth → health_index
- [ ] Include both 2D results and depth results in the JSON response

**Day 3 Exit Gate:** POST a board with a deliberately removed IC → response shows `is_missing: true` for that component, `health_index < 0.5`, red circle in overlay (Team 6 builds overlay but Team 5 should verify the data feeding it).

---

#### Day 4 — Integration Checkpoint + Evaluation Baseline

- [ ] Participate in the full pipeline integration run with all teams
- [ ] Run `evaluation/run_evaluation.py` on the 31-board test set:
  - Load `test_labels.csv` from Team 4
  - For each board: POST to `/inspect` → compare predicted defects vs ground truth
  - Compute confusion matrix, Precision, Recall, F1, FCR, Escape Rate
  - Print results table — **record these as the Day 4 baseline numbers**
- [ ] Start YOLO fine-tune (background, separate Git branch — do NOT touch the working baseline):
  ```python
  from ultralytics import YOLO
  model = YOLO("yolov8n.pt")
  model.train(data="training/datasets/data.yaml", epochs=50, imgsz=640, batch=8)
  ```

**Day 4 Exit Gate:** Day 4 baseline Recall ≥ 80% on 31-board test set. If below 80%, focus tuning on alignment and SSIM thresholds before depth module.

---

#### Day 5 — Threshold Tuning + Ablation Study

- [ ] Run `evaluation/roc_pr_curves.py`:
  - Sweep `ssim_threshold` from 0.50 to 0.90 in steps of 0.05
  - Plot ROC curve; select operating point that maximises F1
  - Update `ssim_threshold` in `detector_2d.py` with chosen value
- [ ] Tune depth thresholds (`θ_height`, `θ_tilt`, `θ_tomb`):
  - Compare depth deviation on tilted/tombstoned boards vs good boards
  - Adjust thresholds so tilt boards are caught, good boards are not flagged
- [ ] Run `evaluation/ablation_study.py`:
  - Variant A: disable `detector_depth.py` → 2D-only metrics
  - Variant B: disable `detector_2d.py` → depth-only metrics
  - Variant C: full system → combined metrics
  - Tabulate results — quantifies the value of each module
- [ ] If YOLO training is complete, run `evaluation/evaluate_yolo.py`:
  - If YOLO mAP50 > SSIM F1: swap YOLO into `detector_2d.py` as primary detector
  - If YOLO underperforms: keep SSIM — document the comparison in `research_report.md`

**Day 5 Exit Gate:** Recall ≥ 88%, FCR ≤ 10%.

---

#### Day 6 — GR&R Study + SPC + Freeze

- [ ] Run `evaluation/grr_study.py`:
  - Select 10 boards (5 good, 5 defective)
  - Under 3 conditions (morning light / afternoon light / camera +5 mm height)
  - Inspect each board 3× per condition = 90 measurements
  - Compute %GR&R (ANOVA method), Cohen's Kappa κ, NDC
  - Record result in `docs/research_report.md`
- [ ] Run `evaluation/spc_charts.py`:
  - Compute DPMO across all 31 boards
  - Plot p-chart (fraction defective per batch) with UCL/LCL control limits
  - Plot c-chart (defect count per board)
  - Compute Sigma level from final DPMO
- [ ] Run `evaluation/spearman_correlation.py`:
  - Compare Health Index scores vs manually-assigned severity ratings (1–5 scale) for all boards
  - Report Spearman ρ
- [ ] **FREEZE at 18:00:** No more code or threshold changes after this point.
  - Tag the Git commit: `git tag v1.0-frozen`
  - Record frozen version in audit logger

**Day 6 Exit Gate:** All metrics computed and written to `docs/research_report.md`. %GR&R documented. Backend frozen.

---

#### Day 7 — Report + Rehearsal

- [ ] Finalise `docs/research_report.md` with all sections (see master plan §12 for outline)
- [ ] Prepare results table slide for demo presentation:
  - Precision / Recall / F1 / FCR / Escape Rate
  - Ablation study table
  - GR&R result
  - DPMO and Sigma level
- [ ] Participate in full dry-run demo
- [ ] Prep answers to judge questions (see §Judge Questions below)

---

### Health Index Formula Reference

$$\text{HI} = \frac{\sum_{i=1}^{N} w_i \cdot p_i \cdot (1 - h_i)}{\sum_{i=1}^{N} w_i}$$

| Symbol | Meaning |
|---|---|
| $w_i$ | Component criticality weight (from `components.json`) |
| $p_i$ | Presence score: SSIM confidence (or YOLO conf if upgraded) |
| $h_i$ | Height/tilt penalty: 0 = normal, 1 = maximum deviation |

**IPC-A-610H Verdict Mapping:**

| Health Index | Verdict | IPC Condition |
|---|---|---|
| ≥ 0.95 | ✅ PASS | Target / Acceptable |
| 0.80 – 0.94 | ⚠️ REWORK | Process Indicator |
| < 0.80 | ❌ FAIL | Defect |

---

### Evaluation Metrics Target

| Metric | Day 4 Baseline | Day 5 Target | Day 6 Final |
|---|---|---|---|
| Recall | ≥ 80% | ≥ 88% | ≥ 90% |
| Precision | ≥ 75% | ≥ 82% | ≥ 85% |
| F1 Score | ≥ 77% | ≥ 85% | ≥ 87% |
| False Call Rate | ≤ 15% | ≤ 10% | ≤ 8% |
| Escape Rate | ≤ 20% | ≤ 12% | ≤ 10% |
| %GR&R | — | — | ≤ 30% |
| Spearman ρ | — | — | ≥ 0.80 |

---

### Research-Grade Deliverables (Team 5)

| Deliverable | Format | Due |
|---|---|---|
| All 7 pipeline modules implemented | Python files | End of Day 3 |
| Day 4 evaluation baseline | Printed results table | End of Day 4 |
| ROC curves + threshold selection | PNG plots + chosen values | End of Day 5 |
| Ablation study table | CSV + printed table | End of Day 5 |
| GR&R study results | %GR&R, κ, NDC | End of Day 6 |
| SPC charts (DPMO, p-chart, c-chart) | PNG plots | End of Day 6 |
| Frozen backend (git tag v1.0-frozen) | Git tag | Day 6 at 18:00 |
| `docs/research_report.md` (complete) | Markdown | End of Day 7 |

---

### Dependencies

**Team 5 needs from other teams:**

| Need | From | When |
|---|---|---|
| `reference/golden_board.png` | Team 4 | Day 2 morning |
| All 31 test board images | Team 4 | Day 3 |
| `evaluation/test_labels.csv` | Team 4 | Day 3 |
| Overlay rendering in `/inspect` response | Team 6 | Day 3 |

**Other teams need from Team 5:**

| Deliverable | Needed By | When |
|---|---|---|
| Laptop B IP + server running on port 8000 | Team 4 & 6 | Day 1 |
| `/inspect` returning real detection results | Team 6 | Day 3 |
| Frozen model + thresholds | Team 6 (for backup demo) | Day 6 at 18:00 |
| Research report (results) | All (for judge Q&A) | Day 7 |

---

### Judge Questions — Team 5 Answers

**"Is this real 3D or estimated?"**
> We use Depth Anything V2 Small (Yang et al., 2024), a pretrained monocular depth model achieving AbsRel of 0.056 on NYU Depth V2. It produces relative — not metric — depth, which is sufficient for detecting height and tilt anomalies when differenced against a golden reference. We documented this honestly as a limitation in the research report.

**"What are your detection rates?"**
> [Quote the actual numbers from `evaluation/run_evaluation.py`]. These are computed against a 31-board test set with physically-measured ground-truth labels — not self-reported estimates.

**"Why not use a depth sensor?"**
> Structured-light AOI sensors (e.g., Koh Young moiré) cost $50k–$150k and require fixed industrial installation. Our research question is: can monocular depth from a consumer camera provide useful height/tilt signal? The ablation study shows [quote result] improvement in F1 when the depth module is added vs 2D-only — which answers the research question.

**"How reliable is your measurement system?"**
> We ran a formal GR&R study (90 measurements, 10 boards × 3 conditions × 3 trials). %GR&R = [actual value]. Per AIAG MSA guidelines, < 30% is acceptable for a research prototype, < 10% is production-grade.
