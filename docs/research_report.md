# High-Reliability PCB AI Inspection System: A Multi-Modal 2D/3D Hybrid Computer Vision Architecture

**Authors:** Team 4 (Data Engineering & Hardware), Team 5 (Model Optimization), Team 6 (AI Deployment)  
**Date:** 2026-07-30  
**Version:** v1.0-frozen  

---

## Abstract
Manual visual inspection of Printed Circuit Board Assemblies (PCBAs) under the IPC-A-610H standard is subject to human inspector fatigue, inconsistent lighting, and low throughput. In this paper, we present a real-time multi-modal computer vision inspection framework combining 2D Structural Similarity (SSIM) difference analysis and 3D Monocular Depth Estimation (Depth Anything V2). Our architecture automatically aligns candidate board captures using an ORB feature matcher and RANSAC homography, computes per-component 2D presence scores and 3D structural anomaly metrics (height deviation, tilt gradient, and tombstone depth asymmetry), and derives a continuous **Health Index (HI)** mapped directly to IPC-A-610H quality verdicts (`PASS`, `REWORK`, `FAIL`). Evaluated on a 31-board dataset across 8 defect categories, our system achieves **92.3% Recall**, **95.2% Precision**, a **3.8% False Call Rate (FCR)**, and an acceptable Measurement System Analysis score of **%GR&R = 18.4%** (ANOVA).

---

## 1. System Architecture & Methodology

```mermaid
graph TD
    A["📸 Webcam Frame Capture (Laptop A)"] --> B["🌐 Ubiquiti Network Transfer (192.168.1.100:8000)"]
    B --> C["🔍 ORB + RANSAC Homography Alignment Engine"]
    C --> D["🎯 2D CLAHE + AbsDiff + SSIM Detector"]
    C --> E["📐 3D Monocular Depth Estimator"]
    D --> F["📊 Weighted Continuous Health Index Engine"]
    E --> F
    F --> G["🎨 Multi-Shape Visual Overlay Renderer"]
    F --> H["📝 ISO 9001 Append-Only Audit Logger (audit.jsonl)"]
```

---

## 2. Experimental Results & Performance Summary

### 2.1 Baseline Evaluation Metrics (31-Board Ground Truth Set)

| Metric | Value | Target Standard | Status |
|---|---|---|---|
| **Precision** | **95.2%** | $\ge 90.0\%$ | ✅ PASSED |
| **Recall (Sensitivity)** | **92.3%** | $\ge 88.0\%$ | ✅ PASSED |
| **F1 Score** | **0.937** | $\ge 0.900$ | ✅ PASSED |
| **False Call Rate (FCR)** | **3.8%** | $\le 10.0\%$ | ✅ PASSED |
| **Escape Rate (Missed Defect)** | **7.7%** | $\le 10.0\%$ | ✅ PASSED |
| **Average End-to-End Latency** | **342 ms** | $< 1000\text{ ms}$ | ✅ PASSED |

---

### 2.2 Ablation Study Results

To evaluate the contribution of each module, we conducted an ablation study comparing three system variants:

| System Variant | Precision | Recall | F1 Score | False Call Rate | Key Finding |
|---|---|---|---|---|---|
| **Variant A (2D-Only)** | 91.3% | 76.9% | 0.835 | 5.2% | Misses tombstone & 3D tilt anomalies |
| **Variant B (Depth-Only)** | 84.6% | 69.2% | 0.762 | 9.4% | Sensitive to height, but lower 2D boundary resolution |
| **Variant C (Full Hybrid Pipeline)** | **95.2%** | **92.3%** | **0.937** | **3.8%** | **Optimal performance across all defect classes** |

---

### 2.3 Measurement System Analysis (Gage R&R Study)
Conducted across 90 total inspection trials (10 representative boards $\times$ 3 lighting/camera conditions $\times$ 3 trials):
- **%GR&R (ANOVA):** **18.4%** (Acceptable for research prototype $< 30\%$)
- **Number of Distinct Categories (NDC):** **7** (Target $\ge 5$)
- **Cohen's Kappa ($\kappa$):** **0.912** (Demonstrates high inter-trial classification consistency)

---

### 2.4 Statistical Process Control (SPC) & Quality Metrics
- **Session Defect Rate (DPMO):** 83,870.97 DPMO
- **Process Sigma Level:** **3.22 $\sigma$** (Exceeds minimum $3.0\sigma$ threshold)
- **Spearman Rank Correlation ($\rho$):** **$-0.941$** ($p < 0.001$, showing strong monotonic inverse relationship between continuous Health Index and physical defect severity).

---

## 3. ISO 9001 Compliance & Traceability
Every inspection request automatically appends an immutable JSON record to `server/audit/audit.jsonl` recording:
- Unique Record ID & SHA-256 image hash
- Hardware alignment score
- Continuous Health Index & IPC-A-610H verdict
- Per-component detection breakdown & system version (`v1.0-frozen`)

---

## 4. Conclusion
The proposed hybrid 2D/3D PCB AI Inspection System provides a research-grade, ISO 9001 compliant solution capable of real-time component verification with sub-second latency, robust physical alignment, and high measurement repeatability.
