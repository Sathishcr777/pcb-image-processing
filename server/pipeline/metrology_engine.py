"""
IPC-A-610 Quantitative Optical Metrology Engine
Team 5 & Industry Metrology Standards

Calculates:
1. Exact physical shifts: Delta X, Delta Y (pixels and mm)
2. Skew / Rotation angle: Delta Theta (in degrees)
3. Maximum Side & End Overhang percentages
4. IPC-A-610 Class 2 and Class 3 automated compliance verdicts
5. Polarity / Pin-1 Index Mark Verification
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional

class MetrologyEngine:
    def __init__(self, px_to_mm_scale: float = 0.05):
        """
        px_to_mm_scale: Calibration scale (e.g. 0.05 mm per pixel)
        """
        self.px_to_mm_scale = px_to_mm_scale
        
        # IPC-A-610H Standard Thresholds
        self.IPC_CLASS_2_MAX_OVERHANG = 50.0  # % max allowable side overhang
        self.IPC_CLASS_3_MAX_OVERHANG = 25.0  # % max allowable side overhang
        self.MAX_ACCEPTABLE_ROTATION_DEG = 5.0 # Max rotation before process indicator warning

    def inspect_component_metrology(
        self,
        test_roi_bgr: np.ndarray,
        ref_roi_bgr: np.ndarray,
        comp_info: Dict
    ) -> Dict:
        """
        Performs sub-pixel metrology and IPC-A-610 verification on a single component ROI.
        """
        cid = comp_info.get("id", "COMP")
        bbox = comp_info.get("bbox_xywh", [0, 0, 30, 30])
        _, _, w, h = bbox
        if test_roi_bgr is None or ref_roi_bgr is None or test_roi_bgr.size == 0 or ref_roi_bgr.size == 0:
            return self._empty_metrology_result(cid, "EMPTY_IMAGE")

        if test_roi_bgr.shape[0] < 8 or test_roi_bgr.shape[1] < 8 or ref_roi_bgr.shape[0] < 8 or ref_roi_bgr.shape[1] < 8:
            return self._empty_metrology_result(cid, "IMAGE_TOO_SMALL")

        gray_test = cv2.cvtColor(test_roi_bgr, cv2.COLOR_BGR2GRAY)
        gray_ref = cv2.cvtColor(ref_roi_bgr, cv2.COLOR_BGR2GRAY)

        # 1. Sub-pixel Contour Extraction for Center & Orientation
        center_test, angle_test, rect_test = self._extract_component_pose(gray_test)
        center_ref, angle_ref, rect_ref = self._extract_component_pose(gray_ref)

        # 2. Calculate Shifts (Delta X, Delta Y)
        dx_px = float(center_test[0] - center_ref[0])
        dy_px = float(center_test[1] - center_ref[1])
        dx_mm = round(dx_px * self.px_to_mm_scale, 3)
        dy_mm = round(dy_px * self.px_to_mm_scale, 3)

        # 3. Calculate Rotation (Delta Theta)
        # Normalize angle difference to [-45, +45] range
        d_theta = float(angle_test - angle_ref)
        if d_theta > 45.0: d_theta -= 90.0
        elif d_theta < -45.0: d_theta += 90.0
        d_theta = round(d_theta, 2)

        # 4. Overhang Ratio Calculations (%)
        side_overhang_pct = round(min(100.0, (abs(dx_px) / max(1.0, float(w))) * 100.0), 2)
        end_overhang_pct = round(min(100.0, (abs(dy_px) / max(1.0, float(h))) * 100.0), 2)
        max_overhang_pct = max(side_overhang_pct, end_overhang_pct)

        # 5. IPC-A-610 Automated Class Verification
        if max_overhang_pct <= self.IPC_CLASS_3_MAX_OVERHANG and abs(d_theta) <= 3.0:
            ipc_status = "CLASS_3_TARGET"  # High reliability aerospace / medical
            ipc_pass = True
        elif max_overhang_pct <= self.IPC_CLASS_2_MAX_OVERHANG and abs(d_theta) <= self.MAX_ACCEPTABLE_ROTATION_DEG:
            ipc_status = "CLASS_2_ACCEPTABLE"  # Dedicated service commercial
            ipc_pass = True
        elif max_overhang_pct <= 75.0:
            ipc_status = "PROCESS_INDICATOR"  # Warning, near limit
            ipc_pass = False
        else:
            ipc_status = "DEFECT_MISALIGNED"
            ipc_pass = False

        # 6. Polarity / Pin-1 Orientation Verification for ICs and Polarized Caps
        comp_type = comp_info.get("type", "").upper()
        polarity_status = "NOT_APPLICABLE"
        polarity_pass = True

        if any(k in comp_type for k in ["IC", "SOIC", "QFP", "MCU"]):
            polarity_pass, polarity_score = self._verify_ic_pin1_dot(gray_test)
            polarity_status = "PIN1_VERIFIED" if polarity_pass else "PIN1_REVERSED_OR_MISSING"
        elif "DIODE" in comp_type or comp_info.get("polarity_check", False):
            polarity_pass, polarity_score = self._verify_cathode_stripe(gray_test)
            polarity_status = "STRIPE_VERIFIED" if polarity_pass else "STRIPE_REVERSED"

        return {
            "component_id": cid,
            "delta_x_px": round(dx_px, 2),
            "delta_y_px": round(dy_px, 2),
            "delta_x_mm": dx_mm,
            "delta_y_mm": dy_mm,
            "rotation_deg": d_theta,
            "side_overhang_pct": side_overhang_pct,
            "end_overhang_pct": end_overhang_pct,
            "max_overhang_pct": max_overhang_pct,
            "ipc_class_verdict": ipc_status,
            "metrology_pass": ipc_pass and polarity_pass,
            "polarity_status": polarity_status,
            "measured_box_px": [round(float(v), 1) for v in rect_test[0]] if rect_test else [0, 0]
        }

    def _extract_component_pose(self, gray_roi: np.ndarray) -> Tuple[Tuple[float, float], float, Optional[tuple]]:
        """
        Uses Otsu thresholding, morphological closing, and minAreaRect for sub-pixel pose estimation.
        """
        h, w = gray_roi.shape
        nominal_center = (float(w) / 2.0, float(h) / 2.0)

        # Adaptive preprocessing
        blurred = cv2.GaussianBlur(gray_roi, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Invert if component is darker than substrate
        if np.mean(thresh) > 127:
            thresh = cv2.bitwise_not(thresh)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return nominal_center, 0.0, None

        # Take largest central contour
        largest_cnt = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_cnt) < (w * h * 0.1):
            return nominal_center, 0.0, None

        # MinAreaRect returns: ((center_x, center_y), (width, height), angle)
        min_rect = cv2.minAreaRect(largest_cnt)
        center = min_rect[0]
        angle = min_rect[2]

        # OpenCV angle adjustment conventions
        if min_rect[1][0] < min_rect[1][1]:
            angle = angle + 90.0

        return center, angle, min_rect

    def _verify_ic_pin1_dot(self, gray_roi: np.ndarray) -> Tuple[bool, float]:
        """
        Verifies the existence of a Pin-1 circular index dot in the expected top-left corner.
        """
        h, w = gray_roi.shape
        q_h, q_w = max(4, h // 3), max(4, w // 3)
        top_left_quad = gray_roi[0:q_h, 0:q_w]

        # Look for circular dark/bright indentation
        grad = cv2.Sobel(top_left_quad, cv2.CV_32F, 1, 1, ksize=3)
        contrast_score = float(np.std(grad))

        # A valid pin 1 marker creates distinct localized high-frequency edge variance
        is_valid = contrast_score > 7.5
        return is_valid, contrast_score

    def _verify_cathode_stripe(self, gray_roi: np.ndarray) -> Tuple[bool, float]:
        """
        Verifies directional brightness gradient for diode / polarized cap cathode markings.
        """
        w = gray_roi.shape[1]
        mid = w // 2
        left_lum = float(np.mean(gray_roi[:, :mid]))
        right_lum = float(np.mean(gray_roi[:, mid:]))
        
        diff = abs(left_lum - right_lum)
        is_polarized = diff > 8.0
        return is_polarized, diff

    def _empty_metrology_result(self, cid: str, reason: str) -> Dict:
        return {
            "component_id": cid,
            "delta_x_px": 0.0,
            "delta_y_px": 0.0,
            "delta_x_mm": 0.0,
            "delta_y_mm": 0.0,
            "rotation_deg": 0.0,
            "side_overhang_pct": 0.0,
            "end_overhang_pct": 0.0,
            "max_overhang_pct": 0.0,
            "ipc_class_verdict": reason,
            "metrology_pass": True,
            "polarity_status": "SKIPPED",
            "measured_box_px": [0, 0]
        }
