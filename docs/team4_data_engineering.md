# Team 4 — Data Engineering
## PCB / Motherboard AI Inspection System | 1-Week Sprint

---

### Team Members
| Name | Suggested Focus |
|---|---|
| Kiruthiga (1) | Camera rig + Ubiquiti network stability |
| Shylaja | Camera rig + Ubiquiti network stability |
| Sudhir | Board sourcing + test set construction + labelling |
| Kiruthiga (2) | Dataset download + annotation + validation |

> **Internal split:** 2 people on physical setup & network, 2 people on data collection & labelling.

---

### Team 4 Role Summary

Team 4 is the **foundation of the entire project**. Every accuracy number the system reports depends on the quality of data Team 4 supplies. If the camera position drifts, if the reference board is photographed differently from test boards, or if the test labels are wrong — every downstream metric is invalid.

**Core responsibilities:**
1. Lock the physical camera setup (position, distance, lighting)
2. Set up and stabilise the Ubiquiti network link
3. Capture the golden reference board and all test boards
4. Build and maintain the structured 31-board test set with ground-truth labels
5. Download the Roboflow PCB dataset for Team 5's YOLO fine-tune track
6. Supply additional hard-case boards as needed throughout tuning
7. Support live demo logistics on Day 7

---

### Files Team 4 Owns

| File | Description |
|---|---|
| `docs/camera_setup_sop.md` | Standard Operating Procedure for camera placement (write and maintain) |
| `docs/api_contract.md` | Co-author with Team 5 — lock endpoint spec on Day 1 |
| `evaluation/test_labels.csv` | Ground-truth defect labels for all 31 test boards |
| `reference/golden_board.png` | Lossless golden reference image captured by Team 4 |
| `training/download_dataset.py` | Roboflow dataset download script |

---

### Day-by-Day Tasks

#### Day 1 — Physical Setup & Network
**Priority: CRITICAL. Nothing else can start without this.**

- [ ] Set up the Ubiquiti network between Laptop A and Laptop B with a **static IP** for Laptop B
- [ ] Verify connectivity: send a test image from Laptop A to `http://LAPTOP_B_IP:8000` using `curl` or Postman
- [ ] Lock Laptop A's camera position, distance, and lighting:
  - Tape all four corners of the laptop to the table
  - Tape the PCB placement zone and orientation on the table
  - Record in `docs/camera_setup_sop.md`:
    - Lens-to-board distance (measure in cm)
    - Ambient light source (window / ceiling light / lamp)
    - Camera exposure / brightness setting (lock it — do not use auto)
- [ ] Photograph a **white-balance reference card** under the same lighting — attach photo to SOP
- [ ] Share Laptop B's static IP with Team 5 and Team 6 (put it in `docs/api_contract.md`)

**Day 1 Exit Gate:** Team 6 can `curl -F "image=@test.jpg" http://LAPTOP_B_IP:8000/inspect` and get a response (even a dummy one). Ubiquiti link confirmed stable for 15+ minutes.

---

#### Day 2 — Golden Reference + Initial Test Boards
**Priority: CRITICAL. Teams 5 and 6 are blocked until the golden reference exists.**

- [ ] From the fixed camera position (Day 1 SOP), photograph the **golden reference board**:
  - Use lossless PNG format — no JPEG compression
  - Take 5 photos of the same board; Team 5 picks the sharpest one
  - Name it exactly: `reference/golden_board.png`
  - Record the shot in `docs/camera_setup_sop.md` (date, time, lighting conditions)
- [ ] Photograph **10 initial test boards** (mix of good and defective — see test set categories below)
- [ ] For each test board photographed, add a row to `evaluation/test_labels.csv`:

```
board_id, component_id, defect_type, physical_measurement, annotator_id, annotation_date
TB001,    U1,           missing,     N/A,                  Sudhir,       2026-DD-MM
TB002,    C3,           tombstone,   height_asymmetry=3mm, Kiruthiga2,   2026-DD-MM
```

- [ ] Download the Roboflow PCB detection dataset (Team 5 needs it for YOLO):
  - Go to https://universe.roboflow.com/ — search "PCB missing component"
  - Create a free account, get API key
  - Fill in `training/download_dataset.py` with the API key and project name
  - Run it — confirm `training/datasets/` folder is created with `train/`, `valid/`, `test/` subfolders

**Day 2 Exit Gate:** `reference/golden_board.png` exists and is shared with Team 5. At least 10 test boards photographed and rows in `test_labels.csv`.

---

#### Day 3 — Expand Test Set to 31 Boards

Build the complete structured test set according to this specification:

| Category | Count | How to Create | Label in CSV |
|---|---|---|---|
| Known-good boards | 5 | All components present, correctly seated, consistent framing | `defect_type = "none"` |
| Missing critical component (IC / power reg) | 5 | Physically remove one critical component (IC, voltage regulator) | `defect_type = "missing"` |
| Missing passive (cap / resistor) | 5 | Remove one capacitor or resistor from a non-critical location | `defect_type = "missing"` |
| Multiple missing components | 5 | Remove 2–4 components of mixed types | One row per missing component |
| Tombstoned component | 3 | Stand one 0402/0603 capacitor or resistor vertically on one pad; measure height asymmetry with ruler | `defect_type = "tombstone"`, record `physical_measurement` |
| Tilted component | 3 | Tilt a visible component ~15°–30° off-axis; measure angle with protractor | `defect_type = "tilt"`, record angle in degrees |
| Shifted component | 3 | Slide a component ~50% off its pads; measure offset in mm | `defect_type = "shift"`, record offset |
| Partial out-of-frame | 2 | Move camera slightly (simulate framing drift) | `defect_type = "none"` — tests alignment gate |
| **Total** | **31** | | |

**Rules:**
- Every photo must be taken from the **exact fixed position** defined in the SOP
- Before photographing each defective board, verify the defect is real by visual check
- Use ruler / protractor to measure physical defects — record values in the CSV
- Two team members must sign off on each label (`annotator_id` column)

**Day 3 Exit Gate:** All 31 boards photographed. `evaluation/test_labels.csv` has 31+ rows. Shared with Team 5 for evaluation scripts.

---

#### Day 4 — Integration Checkpoint Support

- [ ] Confirm Ubiquiti link is stable during the Day 4 full-pipeline test
- [ ] If alignment is failing on any boards (Team 5 reports < 40% inlier ratio), re-photograph those boards from the correct position
- [ ] If lighting has changed since Day 2 (different time of day), re-photograph the golden reference under current conditions and notify Team 5 to recompute `golden_depth.npy`
- [ ] Watch the first full pipeline run — note any boards where the overlay looks wrong; document issues

**Day 4 Exit Gate:** All 31 boards pass through the pipeline without HTTP 422 alignment errors (>95% alignment success rate).

---

#### Day 5 — Hard Cases & Tuning Support

- [ ] Supply **5 additional hard-case boards** if Team 5 requests them for threshold tuning:
  - Very small missing component (0201 resistor)
  - Component with slight colour variation vs reference
  - Board with light scratches or silkscreen marks (not defects — should NOT trigger)
- [ ] Validate that the reference image is still clean and well-lit — if ambient light has drifted, re-shoot
- [ ] Re-run `docs/camera_setup_sop.md` checklist before the Day 5 test session

---

#### Day 6 — Final Full-Run & Demo Prep

- [ ] Conduct the final complete run of all 31 boards through the live pipeline — record results
- [ ] Prepare **5 boards for the live demo**:
  - 1 known-good board
  - 1 board with a missing critical IC (most visually dramatic)
  - 1 board with a tombstoned capacitor
  - 1 board with a tilted component
  - 1 board with multiple missing passives
- [ ] Mark each demo board with a label on the back (not visible to camera) so they can be picked up quickly during judging
- [ ] Practice handing boards to Team 6 during the demo rehearsal

---

#### Day 7 — Rehearsal & Live Demo Support

- [ ] Attend the full dry-run — physically hand boards in the correct order
- [ ] Know which board is which (label on back)
- [ ] Be ready to answer judge questions about how the test set was built and how defects were created/measured
- [ ] Have the camera SOP printed and visible during the demo as evidence of rigour

---

### Research-Grade Deliverables (Team 4)

| Deliverable | Format | Due |
|---|---|---|
| `docs/camera_setup_sop.md` | Markdown with photos | End of Day 1 |
| `reference/golden_board.png` | Lossless PNG | End of Day 2 |
| `evaluation/test_labels.csv` | CSV, 31+ rows, two annotators | End of Day 3 |
| Roboflow dataset in `training/datasets/` | YOLOv8 format | End of Day 2 |
| 5 demo boards (physical, labelled on back) | Physical hardware | End of Day 6 |

---

### Dependencies

**Team 4 needs from other teams:**

| Need | From | When |
|---|---|---|
| Laptop B static IP | Team 5 | Day 1 |
| Confirmation `/set-reference` endpoint is ready | Team 5 | Day 2 |
| Notification if alignment quality < 0.40 on any board | Team 5 | Ongoing |

**Other teams need from Team 4:**

| Deliverable | Needed By | When |
|---|---|---|
| Ubiquiti link confirmed | Team 6 | Day 1 |
| `reference/golden_board.png` | Team 5 | Day 2 morning |
| `evaluation/test_labels.csv` | Team 5 | Day 3 |
| Roboflow dataset | Team 5 | Day 2 |
| All 31 test board images | Teams 5 & 6 | Day 3 |

---

### Judge Questions — Team 4 Answers

**"How did you create the test set?"**
> We created a 31-board structured test set following a defined protocol. We physically removed components, measured tilt angles with a protractor, and recorded measurements in a labelled CSV with two annotators per entry. This gives ground-truth data for computing Precision, Recall, and F1.

**"How do you ensure the camera position is consistent?"**
> We follow a written Standard Operating Procedure — the laptop is taped down, the board placement zone is marked, the lighting source is fixed, and we verify alignment quality (≥ 0.70) before any session begins.

**"What if the lighting changes during the demo?"**
> The alignment quality gate in the pipeline catches it — if the board image is too different from the reference, the API returns a 422 error asking the operator to reposition rather than returning a false result.
