# Industrial PCB / Motherboard AI Inspection & Metrology Suite
## IPC-A-610H Class 2/3 | Industry 4.0 IPC-CFX-2591 | ISO 9001:2015 Traceability

[![FastAPI](https://img.shields.io/badge/FastAPI-v0.100+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-v2.0+-EE4C2C.svg?logo=pytorch)](https://pytorch.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-v4.8+-5C3EE8.svg?logo=opencv)](https://opencv.org)
[![IPC Standard](https://img.shields.io/badge/Standard-IPC--A--610H-blue.svg)](https://www.ipc.org)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](https://opensource.org/licenses/Apache-2.0)

---

## 📌 Executive Summary

An enterprise AI-powered visual inspection and quantitative metrology platform for electronics manufacturing lines (SMT / PCBA). The system transforms standard 2D industrial/edge camera feeds into a **3D-aware metrology station** with zero hardware depth sensors.

### 🌟 Key Capabilities
- **2D Tri-Metric Defect Detection**: Fuses CIE-LAB CLAHE, SSIM, Normalized Cross-Correlation (NCC), and Canny Edge Density.
- **3D Substrate-Leveled Depth Engine**: Employs Monocular Depth AI (Depth Anything V2) with automated 3D ground-plane regression to isolate true vertical lift (tombstoning, billboarding, unseated ICs).
- **IPC-A-610H Quantitative Metrology**: Sub-pixel measurement of component shift ($\Delta X, \Delta Y$ in mm), rotation ($\Delta \theta$ in degrees), side overhang percentage, and Pin-1 polarity verification.
- **Automated SMT CAD Centroid Ingestion**: Auto-converts Pick-and-Place `.csv` / `.xy` placement files into pixel inspection ROIs.
- **Industry 4.0 IPC-CFX Telemetry**: Dispatches standard JSON events for automated upstream feeder nozzle recalibration.
- **ISO 9001:2015 Audit Trail**: Tamper-proof, append-only JSONL audit logs with SHA-256 image hashing.

---

## 🗂️ Clean Project Directory Structure

```
IMAGE PROCESSING/
├── server/                          # FastAPI Enterprise Inspection Server (Laptop B)
│   ├── main.py                      # REST API endpoints, routing & threadpool management
│   ├── pipeline/                    # Core Computer Vision & Metrology Pipeline
│   │   ├── aligner.py               # Optical gating, bilateral filter & ORB/RANSAC homography
│   │   ├── detector_2d.py           # LAB-space CLAHE & Tri-Metric Ensemble (SSIM+NCC+Edge)
│   │   ├── detector_depth.py        # 3D Depth inference & vertical defect detector
│   │   ├── substrate_leveler.py     # 3D PCB substrate plane fitting & leveling
│   │   ├── metrology_engine.py      # IPC-A-610 sub-pixel offsets, rotation & overhang %
│   │   ├── cad_parser.py            # SMT Pick-and-Place centroid CSV/XY auto-ROI parser
│   │   ├── health_index.py          # Continuous Health Index & IPC verdict calculator
│   │   ├── visualizer.py            # Multi-shape overlay renderer & metrology vector callouts
│   │   └── cfx_dispatcher.py        # IPC-CFX-2591 Industry 4.0 MES telemetry dispatcher
│   ├── audit/                       # ISO 9001 Compliance Logging
│   │   ├── logger.py                # Thread-safe append-only audit writer & statistics engine
│   │   └── audit.jsonl              # Immutable inspection audit logs
│   ├── config/                      # System Configurations
│   │   └── components.json          # Active component footprint definitions & tolerances
│   ├── reference/                   # Golden Reference Standards
│   │   ├── golden_board.png         # Golden reference board image
│   │   └── golden_depth.npy         # Precomputed reference depth matrix
│   └── static/                      # Web Dashboard Frontend (Single Page App)
│       ├── index.html               # Industrial dark-theme UI dashboard
│       ├── styles.css               # Responsive design & component styling
│       └── app.js                   # Client controller, Chart.js analytics & API hooks
│
├── client/                          # Camera Capture Node (Laptop A)
│   ├── capture_and_send.py          # Local/webcam frame capture & static IP REST client
│   └── requirements.txt             # Minimal client dependencies
│
├── evaluation/                      # Research Benchmarking & MSA Suite
│   ├── test_boards/                 # 31 standard physical test boards (TB001 - TB031)
│   ├── reports/                     # Statistical analysis outputs & dashboards
│   │   ├── grr_report.xlsx          # Full Gage R&R ANOVA Excel report
│   │   ├── grr_dashboard.png        # 4-panel MSA visual chart
│   │   └── preprocessing_steps/     # Step-by-step diagnostic image outputs
│   ├── test_labels.csv              # Ground-truth labelled defect catalog
│   ├── grr_study.py                 # Crossed Gage R&R ANOVA study (%GR&R = 7.14%, NDC = 19)
│   ├── ablation_study.py            # 2D-only vs Depth-only vs Combined evaluation
│   ├── roc_pr_curves.py             # ROC curves, AUC, and precision-recall sweeps
│   ├── spearman_correlation.py      # Health Index monotonic rank correlation (ρ = 0.967)
│   └── spc_charts.py                # Live p-chart, c-chart & Six Sigma DPMO trend
│
├── scripts/                         # Production & Developer Utilities
│   ├── diagnose_preprocessing.py    # Step-by-step diagnostic on raw PCB images
│   ├── generate_synthetic_boards.py # Generates calibrated test boards with known defects
│   ├── capture_golden_from_webcam.py# Interactive CLI tool for capturing reference boards
│   ├── verify_two_laptop_setup.py   # Ubiquiti network latency & connectivity validator
│   ├── start_server_laptop_b.bat    # Windows 1-click server launch script
│   └── start_client_laptop_a.bat    # Windows 1-click client launch script
│
├── docs/                            # Engineering Documentation & SOPs
│   ├── presentation/                # Pitch decks & competition slide decks
│   ├── camera_setup_sop.md          # Standard Operating Procedure for optical rig setup
│   ├── api_contract.md              # REST API endpoint specifications
│   ├── research_report.md           # Formal research paper draft & benchmarking results
│   ├── step_by_step_procedure.md    # Complete physical sprint procedure
│   ├── project_study_guide.md       # Team briefing guide & conceptual analogies
│   ├── team4_data_engineering.md    # Team 4 work allocation
│   ├── team5_model_optimization.md  # Team 5 work allocation
│   └── team6_ai_deployment.md       # Team 6 work allocation
│
├── tests/                           # Automated Verification Suite
│   ├── test_advanced_features.py    # Tests CAD parser, metrology, substrate leveler, CFX
│   └── test_pipeline.py             # End-to-end alignment, 2D/3D diff, and audit tests
│
├── .env.example                     # Environment configuration template
├── .gitignore                       # Clean repository exclusion rules
├── Dockerfile                       # Production container definition
├── docker-compose.yml               # Multi-container service orchestrator
└── requirements.txt                 # Unified project dependencies
```

---

## ⚡ Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/Monishp-eng/IMAGE-PROCESSING.git
cd "IMAGE PROCESSING"

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

# Install dependencies
pip install -r requirements.txt
```

### 2. Launching the Server (Laptop B)

```bash
python -m uvicorn server.main:app --host 0.0.0.0 --port 8080 --reload
```
Open **`http://localhost:8080`** in your browser to access the live dashboard.

### 3. Launching the Camera Client (Laptop A)

```bash
# Edit SERVER_URL in client/capture_and_send.py with Laptop B's static IP
python client/capture_and_send.py
```

---

## 📡 REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | `GET` | System liveness, loaded depth engine & active feature list |
| `/set-reference` | `POST` | Sets golden reference image and precomputes 3D depth baseline |
| `/cad/import` | `POST` | Ingests SMT Pick-and-Place centroid CSV to auto-generate component ROIs |
| `/inspect` | `POST` | Runs full 2D/3D inspection, sub-pixel metrology & returns annotated overlay |
| `/cfx/telemetry` | `GET` | Streams recent IPC-CFX-2591 machine-to-machine event messages |
| `/metrics` | `GET` | Live batch statistics (First Pass Yield, DPMO, Mean Latency) |
| `/audit/logs` | `GET` | Returns immutable ISO 9001:2015 inspection audit history |

---

## 🔬 Benchmark Results

| Metric | Target (Class 2/3) | Measured Platform Value |
| :--- | :--- | :--- |
| **Gage R&R (%GR&R)** | $< 10.0\%$ (Excellent) | **$7.14\%$** |
| **Number of Distinct Categories (NDC)** | $\ge 5$ | **$19$** |
| **Cohen's Kappa ($\kappa$)** | $> 0.90$ (High Agreement)| **$0.9778$** |
| **Spearman Rank Correlation ($\rho$)** | $\ge 0.85$ | **$0.967$** |
| **Mean End-to-End Latency** | $< 500\text{ ms}$ | **$170\text{--}220\text{ ms}$** |
| **First Pass Yield (Golden Set)** | $100.0\%$ | **$100.0\%$** |

---

## 🧪 Running Automated Tests

```bash
# Run all automated tests
python -m pytest tests/ -v
```

---

## 📜 Standards Compliance
- **IPC-A-610H Class 2/3**: Component misalignment, skew, and side overhang criteria.
- **IPC-CFX-2591**: Connected Factory Exchange standard for automated Industry 4.0 telemetry.
- **ISO 9001:2015 Clause 8.6**: Complete traceability audit trail with immutable SHA-256 records.
- **AIAG MSA Manual**: Gage Repeatability & Reproducibility (ANOVA method).

---

## 👥 Engineering Team & Roles

| Team | Focus Area | Key Deliverables |
| :--- | :--- | :--- |
| **Team 4: Data Engineering** | Optical rig calibration & dataset curation | Camera SOP, 31-board dataset, ground-truth labels |
| **Team 5: Model Optimization** | Computer vision & depth algorithms | Metrology engine, substrate leveler, tri-metric 2D, MSA |
| **Team 6: AI Deployment** | Production backend & UI engineering | FastAPI server, Industry 4.0 CFX, audit logging, dashboard |

---
*Developed for Industrial SMT Quality Assurance & Smart Factory Metrology.*
