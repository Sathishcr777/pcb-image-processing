# Team 6 — AI Model Deployment
## PCB / Motherboard AI Inspection System | 1-Week Sprint

---

### Team Members
| Name | Suggested Focus |
|---|---|
| Monish | Server integration + feed wiring + edge case handling |
| Sabarish | Server integration + audit logging wiring |
| Santhosh | Visualization overlay (OpenCV rendering) |
| Roshini | Visualization overlay + overlay clarity improvements |
| Poorani | Demo video production + demo runner script + rehearsal lead |

> **Internal split:** 2 people on server/feed integration, 2–3 people on overlay/visualization + demo production.

---

### Team 6 Role Summary

Team 6 is responsible for **everything the judges and users see**. The pipeline logic lives in Team 5's modules, but Team 6 wires it all together, makes it run reliably end-to-end from Laptop A to the final annotated image, and ensures the demo is polished, narrated, and backed up.

**Core responsibilities:**
1. Scaffold the FastAPI pipeline skeleton on Day 1 (using dummy data)
2. Wire the real Laptop A → Ubiquiti → Laptop B image feed (replacing dummy data)
3. Build the complete OpenCV visualization overlay (circles, triangles, diamonds, banner)
4. Implement the ISO 9001 audit logger
5. Handle all edge cases (board out of frame, network timeout, missing reference)
6. Improve overlay clarity and visual output quality
7. Record the backup demo video
8. Lead the Day 7 dry-run and demo logistics

---

### Files Team 6 Owns

| File | Description |
|---|---|
| `server/pipeline/visualizer.py` | OpenCV overlay renderer — all annotation types |
| `server/audit/logger.py` | ISO 9001-compliant append-only audit record writer |
| `client/capture_and_send.py` | Laptop A camera capture + POST to server |
| `client/requirements.txt` | Minimal Laptop A dependencies |
| `demo/run_demo.py` | Narrated demo runner script |
| `demo/backup_demo/` | Pre-recorded backup video (MP4) |
| `README.md` | Setup and run instructions |

---

### Day-by-Day Tasks

#### Day 1 — Pipeline Skeleton (Dummy Data)
**Goal: End-to-end plumbing works before real detection is ready.**

**Sub-team A (Monish + Sabarish) — Server Skeleton:**

- [ ] On Laptop B, create the FastAPI app skeleton (`server/main.py`) in coordination with Team 5:

```python
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import uvicorn, base64, numpy as np, cv2, io

app = FastAPI(title="PCB Inspection System v1.0")

@app.get("/health")
async def health():
    return {"status": "ok", "reference_loaded": False, "version": "1.0.0"}

@app.post("/set-reference")
async def set_reference(image: UploadFile = File(...)):
    # Day 1: just acknowledge receipt
    return {"status": "reference_received"}

@app.post("/inspect")
async def inspect(image: UploadFile = File(...)):
    # Day 1: return dummy result so Team 4 and 6 can test connectivity
    return {
        "health_index": 0.99,
        "verdict": "PASS",
        "missing_components": [],
        "height_tilt_flags": [],
        "overlay_image_b64": ""   # empty for now
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] Run the server: `python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload`
- [ ] Confirm Team 4 can POST to it from Laptop A

**Sub-team B (Santhosh + Roshini + Poorani) — Client Skeleton:**

- [ ] On Laptop A, create `client/capture_and_send.py`:

```python
import cv2, requests, base64, json, numpy as np

SERVER_URL = "http://LAPTOP_B_IP:8000"   # Update with real IP from Team 4

cap = cv2.VideoCapture(0)
print("Press SPACE to capture and send | Press Q to quit")

while True:
    ret, frame = cap.read()
    cv2.imshow("Laptop A — PCB Camera", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord(' '):                      # SPACE = capture + send
        _, img_bytes = cv2.imencode('.png', frame)
        response = requests.post(
            f"{SERVER_URL}/inspect",
            files={"image": ("board.png", img_bytes.tobytes(), "image/png")},
            timeout=30
        )
        result = response.json()
        print(f"Health Index: {result['health_index']:.3f} | Verdict: {result['verdict']}")

        if result.get("overlay_image_b64"):
            overlay_bytes = base64.b64decode(result["overlay_image_b64"])
            overlay_arr = np.frombuffer(overlay_bytes, dtype=np.uint8)
            overlay_img = cv2.imdecode(overlay_arr, cv2.IMREAD_COLOR)
            cv2.imshow("Inspection Result", overlay_img)

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

**Day 1 Exit Gate:** `capture_and_send.py` on Laptop A sends a frame and prints `Health Index: 0.990 | Verdict: PASS` (dummy). Network confirmed working.

---

#### Day 2 — Audit Logger + Real Feed Wiring

**Sub-team A (Monish + Sabarish):**

- [ ] Implement `server/audit/logger.py` (ISO 9001 Clause 8.6 compliance):

```python
import json, hashlib, uuid
from datetime import datetime, timezone
from pathlib import Path

AUDIT_FILE = Path("server/audit/audit.jsonl")
AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

def write_audit_record(
    board_serial: str,
    raw_image_bytes: bytes,
    per_component_results: list,
    health_index: float,
    verdict: str,
    alignment_quality: float,
    operator_id: str = "system",
    ipc_class: str = "CLASS_2",
    system_version: str = "1.0.0"
):
    image_hash = hashlib.sha256(raw_image_bytes).hexdigest()
    record = {
        "record_id": str(uuid.uuid4()),
        "board_serial": board_serial,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "system_version": system_version,
        "reference_image_hash": _get_reference_hash(),
        "image_sha256": image_hash,
        "alignment_quality_score": round(alignment_quality, 4),
        "ipc_class": ipc_class,
        "operator_id": operator_id,
        "health_index": round(health_index, 4),
        "verdict": verdict,
        "per_component_results": per_component_results,
    }
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")   # Append-only — never overwrites
    return record["record_id"]

def _get_reference_hash() -> str:
    ref_path = Path("server/reference/golden_board.png")
    if not ref_path.exists():
        return "NO_REFERENCE"
    return hashlib.sha256(ref_path.read_bytes()).hexdigest()[:16]
```

- [ ] Wire the audit logger into the `/inspect` endpoint in `main.py` — call `write_audit_record(...)` after every inspection (success or error)
- [ ] Add `GET /audit/recent` endpoint — returns last 10 records from `audit.jsonl` (for monitoring)

**Sub-team B (Santhosh + Roshini):**

- [ ] Build a basic version of `server/pipeline/visualizer.py` early — Team 5 needs to know the interface:

```python
def render_overlay(image_bgr, per_component_results, health_index, verdict) -> bytes:
    """
    Returns PNG bytes of the annotated overlay image.
    Called by main.py after detection; result is base64-encoded in JSON response.
    """
    ...
```

- [ ] Implement the Health Index banner at the top of every overlay image

**Day 2 Exit Gate:** Every `/inspect` call writes a record to `audit.jsonl`. Audit file can be opened and each line is valid JSON.

---

#### Day 3 — Full Visualization Overlay

**Sub-team B (Santhosh + Roshini + Poorani) — Build the complete visualizer:**

Implement all 5 annotation types in `server/pipeline/visualizer.py`:

| Annotation | Shape | Colour (BGR) | Trigger |
|---|---|---|---|
| Missing component | Filled circle (r=20) + label text | Red: `(0, 0, 220)` | `is_missing == True` |
| Height anomaly | Upward-pointing triangle | Orange: `(0, 140, 255)` | `height_flag == True` |
| Tombstone detected | Diamond (rotated square) | Yellow: `(0, 220, 220)` | `tombstone_flag == True` |
| Tilt detected | Rotated square (45°) | Magenta: `(200, 0, 200)` | `tilt_flag == True` |
| Component passed | Checkmark glyph | Green: `(0, 200, 80)` | All flags clear |

**Additional overlay elements:**

- [ ] **Health Index banner** — coloured bar at top of image (green → red gradient based on HI value):
  ```
  | ██████████████░░░░░░ HI: 0.87  ⚠️ REWORK  Board: TB-024 |
  ```
- [ ] **Per-component mini-label** — small text below each marker showing component ID and score
- [ ] **Legend** — small legend box in bottom-right corner showing what each shape/colour means
- [ ] **IPC-A-610 verdict** — bold text in top-right corner, colour-coded:
  - PASS: dark green background
  - REWORK: amber background
  - FAIL: red background
- [ ] **Processing time** — small text in bottom-left corner: `Inference: 3.2s`

**Overlay function signature:**
```python
def render_overlay(
    image_bgr: np.ndarray,
    per_component_results: list,   # from detector_2d + detector_depth (merged)
    health_index: float,
    verdict: str,
    board_serial: str = "",
    processing_time_ms: int = 0
) -> bytes:  # Returns PNG bytes
```

**Sub-team A (Monish + Sabarish):**

- [ ] Wire the real `detector_2d`, `detector_depth`, `health_index`, and `visualizer` from Team 5 into `main.py`:
  - Replace dummy response with real pipeline call
  - Base64-encode the overlay PNG and include in JSON response
  - Measure end-to-end latency; log it

**Day 3 Exit Gate:** POST a board with a missing IC → overlay image shows a red circle at the IC location. JSON response contains `is_missing: true` for that component.

---

#### Day 4 — Integration + Edge Cases

- [ ] Participate in the Day 4 full integration checkpoint — full Laptop A → Ubiquiti → server pipeline run
- [ ] Implement edge case handling in `main.py`:

| Edge Case | Response |
|---|---|
| `/inspect` called before `/set-reference` | HTTP 503: `{"error": "reference_not_set", "action": "POST /set-reference first"}` |
| Alignment quality < 0.40 | HTTP 422: `{"error": "alignment_failed", "alignment_quality": 0.21, "action": "reposition board and retry"}` |
| Image file > 10 MB | HTTP 413: `{"error": "file_too_large"}` |
| Invalid file type (not PNG/JPEG) | HTTP 400: `{"error": "invalid_image_type"}` |
| Network timeout (Laptop A side) | `requests.Timeout` exception caught, retry once after 5s |
| Board partially out of frame | Caught by alignment gate (422) or flagged in overlay with "LOW ALIGNMENT" warning banner |

- [ ] Test each edge case manually — confirm correct HTTP status and error message
- [ ] Add `GET /metrics` endpoint returning session statistics:
  ```json
  {
    "boards_inspected": 42,
    "pass_count": 35,
    "rework_count": 5,
    "fail_count": 2,
    "session_fpy": 0.833,
    "avg_processing_ms": 3100
  }
  ```

**Day 4 Exit Gate:** All 5 edge cases return correct HTTP status codes. Full pipeline runs without unhandled exceptions on all 31 test boards.

---

#### Day 5 — Overlay Clarity + UX Polish

- [ ] Improve overlay readability based on Day 4 review feedback:
  - Ensure text labels do not overlap each other or run off image edges
  - Scale marker size relative to component bounding box size
  - Add semi-transparent background behind text labels for readability
  - If multiple defect types overlap on one component, show stacked markers
- [ ] Add a **summary panel** to the overlay — right-side panel listing:
  - Total components inspected
  - Missing: N components (listed by name)
  - Height/tilt flags: N components
  - Health Index: 0.XX (PASS / REWORK / FAIL)
- [ ] Test overlay on boards with many missing components (worst case visual)
- [ ] Test overlay on known-good boards (should show all green checkmarks, clean look)
- [ ] Verify overlay is readable when printed in black and white (for report figures)

**Day 5 Exit Gate:** Overlay is clean, readable, and unambiguous on all board types. All labels visible.

---

#### Day 6 — Backup Demo Video + Final Freeze

**Poorani leads backup demo video production:**

Record the backup video in one take on Day 6 (after the full test run). It must be narrated, professional, and cover the complete pipeline.

**Backup video script:**

```
[0:00 - 0:20] Introduction
  "This is the PCB Motherboard Inspection System — an AI-powered visual
   inspection tool built for manufacturing quality control..."

[0:20 - 1:00] Setup shot
  Show Laptop A camera aimed at the board, Laptop B running the server,
  Ubiquiti router in frame if possible.

[1:00 - 2:00] Healthy board demo
  Place the known-good board → run inspection → show overlay (all green) →
  narrate: "Health Index 0.97, all 12 components detected, verdict: PASS"

[2:00 - 3:00] Missing component demo
  Place board with missing IC → run inspection → show overlay (red circle) →
  narrate: "Component U1 missing, Health Index drops to 0.41, verdict: FAIL"

[3:00 - 3:45] Height/tilt anomaly demo
  Place board with tombstoned capacitor → show orange triangle in overlay →
  narrate: "Tombstone defect detected on C3, height asymmetry flagged by
   Depth Anything V2 monocular depth estimation"

[3:45 - 4:30] Multi-defect board
  Place worst-case board → show multiple markers → narrate HI breakdown

[4:30 - 5:00] Results & metrics
  Show the results table (Precision/Recall/F1) and GR&R result on screen.
  End with: "31 boards tested, F1 = [actual], %GR&R = [actual]"
```

- [ ] Record video at ≥ 1080p — save to `demo/backup_demo/pcb_inspection_demo.mp4`
- [ ] Verify video plays correctly on both laptops before Day 7
- [ ] **Watch the frozen backend** — do not request any changes from Team 5 after 18:00 Day 6

**Day 6 Exit Gate:** Backup video saved and plays correctly. Duration: 4–6 minutes.

---

#### Day 7 — Rehearsal + Live Demo Lead

- [ ] Lead the full dry-run demo in front of the whole group — run it exactly as you will for the judges
- [ ] Demo order (recommended):
  1. Show server health check: `GET /health` in browser
  2. Load the golden reference via `POST /set-reference`
  3. Show the camera SOP (Team 4 marks the position)
  4. Board 1: Known-good → PASS result with all green checkmarks
  5. Board 2: Missing critical IC → FAIL result with red circle
  6. Board 3: Tombstoned capacitor → REWORK with orange triangle
  7. Board 4: Multiple missing passives → FAIL with multiple markers
  8. Board 5 (if time): Tilted component → magenta rotated-square marker
  9. Show the `GET /metrics` endpoint → session DPMO and FPY
  10. Show 1 page from `audit.jsonl` — demonstrate traceability
- [ ] Time each step during the dry-run — total demo should fit in 5–7 minutes
- [ ] Have the backup video ready to play on a third device immediately if anything fails

---

### Overlay Annotation Reference

```
Board Image with Overlay
┌─────────────────────────────────────────────────────────────┐
│  HI: 0.62 ██████████░░░░░░░░░░░░░░░░  ❌ FAIL  TB-017     │  ← HI Banner
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    [●] U1 — MISSING (0.08)         ← Red circle            │
│        ↑ Main Microcontroller                              │
│                                                             │
│    [▲] C3 — HEIGHT FLAG (pen=0.34) ← Orange triangle       │
│                                                             │
│    [◆] C5 — TOMBSTONE              ← Yellow diamond        │
│                                                             │
│    [✓] R7 — PASS (0.96)           ← Green checkmark        │
│                                             ┌───────────┐  │
│                                             │ ● Missing  │  │
│                                             │ ▲ Height   │  │ ← Legend
│                                             │ ◆ Tombstn  │  │
│  Inference: 3.2s                            │ ✓ Pass     │  │
└─────────────────────────────────────────────────────────────┘
```

---

### Research-Grade Deliverables (Team 6)

| Deliverable | Format | Due |
|---|---|---|
| FastAPI skeleton running on Laptop B | Python server | End of Day 1 |
| `client/capture_and_send.py` functional | Python script | End of Day 1 |
| `server/audit/logger.py` writing records | Python + JSONL output | End of Day 2 |
| Complete `visualizer.py` (all 5 annotation types) | Python + tested | End of Day 3 |
| All 5 edge cases handled with correct HTTP codes | Python | End of Day 4 |
| Polished overlay (labels, legend, summary panel) | Python | End of Day 5 |
| Backup demo video (narrated, 4–6 min, 1080p) | MP4 file | End of Day 6 |
| `README.md` (setup + run instructions) | Markdown | End of Day 6 |
| Live demo run successfully in dry-run | Demonstration | Day 7 |

---

### API Contract Summary (Team 6 must follow exactly)

Team 6 must use these exact endpoints as defined by Team 5:

| Endpoint | Method | Purpose | Key Response Fields |
|---|---|---|---|
| `/health` | GET | Server liveness check | `status`, `reference_loaded` |
| `/set-reference` | POST | Upload golden board | `reference_id`, `component_rois_loaded` |
| `/inspect` | POST | Main inspection call | `health_index`, `verdict`, `missing_components`, `height_tilt_flags`, `overlay_image_b64` |
| `/metrics` | GET | Session statistics | `boards_inspected`, `session_fpy`, `avg_processing_ms` |

**Field `overlay_image_b64`:** Base64-encoded PNG bytes. Decode with:
```python
import base64, numpy as np, cv2
img_bytes = base64.b64decode(result["overlay_image_b64"])
img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
```

---

### Dependencies

**Team 6 needs from other teams:**

| Need | From | When |
|---|---|---|
| Laptop B static IP | Team 5 | Day 1 |
| Dummy `/inspect` returning 200 | Team 5 | Day 1 |
| Real detection results in `/inspect` response | Team 5 | Day 3 |
| Frozen backend + thresholds | Team 5 | Day 6 at 18:00 |
| 5 demo boards (physical, labelled) | Team 4 | Day 6 |

**Other teams need from Team 6:**

| Deliverable | Needed By | When |
|---|---|---|
| Server running on port 8000 (skeleton) | Team 4 (connectivity test) | Day 1 |
| Overlay PNG returning in response | Team 5 (to verify visualizer wiring) | Day 3 |
| Backup demo video | All (fallback during judging) | Day 6 |

---

### Judge Questions — Team 6 Answers

**"What happens if the network drops during the demo?"**
> The client script has a 30-second timeout and retries once. If the network is still down, we play the pre-recorded backup video — a complete narrated run of the pipeline recorded on Day 6.

**"How is this production-ready?"**
> The API contract is identical to what any production camera system would use — a REST POST with an image and a structured JSON response. The audit log is ISO 9001-compliant: every inspection is recorded with a UUID, timestamp, board serial, image hash, and per-component results in an append-only file.

**"What does the Health Index number mean?"**
> It's a weighted average of per-component quality scores, where critical parts like ICs and power regulators have higher weights than passive components. A score of 1.0 means every component matches the golden reference in both 2D presence and 3D depth profile. The IPC-A-610H standard mapping gives: ≥ 0.95 = PASS, 0.80–0.94 = REWORK, < 0.80 = FAIL.

**"What's in your audit log?"**
> Every inspection record includes: a UUID, board serial number, UTC timestamp, software version, SHA-256 hash of the reference image, SHA-256 hash of the inspected image, alignment quality score, per-component results with scores, Health Index, IPC verdict, and operator ID. Records are append-only — they cannot be modified after writing.
