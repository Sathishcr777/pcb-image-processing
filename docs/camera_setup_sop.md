# Standard Operating Procedure: PCB Camera Rig & Lighting Setup

**Document Owner:** Team 4 (Kiruthiga 1 & Shylaja)  
**Version:** 1.0  
**Last Updated:** 2026-07-30  

---

## 1. Hardware & Environment Rigging

### 1.1 Physical Camera Setup
- **Lens-to-Board Height:** 25.0 cm (measured perpendicular from lens center to table surface).
- **Perpendicular Angle:** 90° plumb line (zero angular tilt).
- **Rig Taping:** Laptop A base and camera mount secured with heavy-duty masking tape.
- **PCB Zone Marking:** Boundary rectangle marked with high-contrast tape on the table surface. Top-left corner aligned with Pin 1 indicator.

### 1.2 Lighting & White Balance Calibration
- **Lighting Source:** Overhead 45° diffuse LED ring light to eliminate hard shadows.
- **Exposure Mode:** HARD-LOCKED Manual Exposure (Auto-Exposure OFF, Auto-Focus OFF, Auto-WB OFF).
- **White Balance Card:** Photograph neutral gray reference card before each session (`docs/white_balance_reference.png`). Confirm RGB histogram balance within ±3%.

---

## 2. Golden Reference Log

| Shot # | Date & Time | Lighting | Exposure | Selection Notes | Approved By |
|---|---|---|---|---|---|
| 1 | 2026-07-30 09:00 | 5000K LED | ISO 100, 1/60s | Test capture 1 | Kiruthiga1 |
| 2 | 2026-07-30 09:02 | 5000K LED | ISO 100, 1/60s | Test capture 2 | Kiruthiga1 |
| 3 | 2026-07-30 09:04 | 5000K LED | ISO 100, 1/60s | **SELECTED as `golden_board.png`** | Kiruthiga1, Shylaja |
| 4 | 2026-07-30 09:06 | 5000K LED | ISO 100, 1/60s | Minor reflection | Shylaja |
| 5 | 2026-07-30 09:08 | 5000K LED | ISO 100, 1/60s | Alternative candidate | Kiruthiga1 |

---

## 3. Quality Gate Thresholds
- Minimum Alignment Quality Score: **$\ge 0.70$**
- Hard Alignment Failure (HTTP 422): **$< 0.40$**
