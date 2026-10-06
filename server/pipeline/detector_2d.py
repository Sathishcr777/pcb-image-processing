"""
2D Missing Component Detector & Multi-Metric Ensemble
Team 5 - Model Optimization & Computer Vision Engine

Upgraded Multi-Metric Architecture:
1. CIE-LAB Color Space Luminance Isolation
2. Specular Glare & Reflection Suppression for Shiny Solder Fillets
3. Tri-Metric Ensemble: 0.50*SSIM + 0.30*NCC + 0.20*(1 - EdgeDiffRatio)
"""

import cv2
import numpy as np
from typing import Dict, List

try:
    from skimage.metrics import structural_similarity as ssim
except ImportError:
    def ssim(img1, img2):
        C1 = (0.01 * 255)**2
        C2 = (0.03 * 255)**2
        img1 = img1.astype(np.float64)
        img2 = img2.astype(np.float64)
        kernel = cv2.getGaussianKernel(11, 1.5)
        window = np.outer(kernel, kernel.T)
        mu1 = cv2.filter2D(img1, -1, window)
        mu2 = cv2.filter2D(img2, -1, window)
        mu1_sq = mu1**2
        mu2_sq = mu2**2
        mu1_mu2 = mu1 * mu2
        sigma1_sq = cv2.filter2D(img1**2, -1, window) - mu1_sq
        sigma2_sq = cv2.filter2D(img2**2, -1, window) - mu2_sq
        sigma12 = cv2.filter2D(img1 * img2, -1, window) - mu1_mu2
        ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
        return float(ssim_map.mean())

class Detector2D:
    def __init__(self, ensemble_threshold: float = 0.78, diff_ratio_threshold: float = 0.25):
        self.ensemble_threshold = ensemble_threshold
        self.diff_ratio_threshold = diff_ratio_threshold
        self.clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))

    def preprocess_roi_lab(self, img_bgr: np.ndarray) -> np.ndarray:
        """
        Converts to CIE-LAB, suppresses extreme specular solder highlights (>240),
        and applies CLAHE to the L channel.
        """
        if len(img_bgr.shape) == 2:
            return self.clahe.apply(img_bgr)

        lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
        l_chan, a_chan, b_chan = cv2.split(lab)

        # Specular reflection clipping on shiny solder
        # Soft-clip values above 240 to prevent glare from dominating difference metrics
        glare_mask = l_chan > 240
        if np.any(glare_mask):
            l_chan[glare_mask] = 230

        l_norm = self.clahe.apply(l_chan)
        return l_norm

    def detect(self, aligned_img: np.ndarray, ref_img: np.ndarray, components: list) -> Dict:
        """
        Evaluates each component ROI using the Tri-Metric Ensemble:
        Ensemble Score = 0.50 * SSIM + 0.30 * NCC + 0.20 * (1.0 - EdgeDiffRatio)
        """
        if aligned_img.shape[:2] != ref_img.shape[:2]:
            aligned_img = cv2.resize(aligned_img, (ref_img.shape[1], ref_img.shape[0]))

        proc_aligned = self.preprocess_roi_lab(aligned_img)
        proc_ref = self.preprocess_roi_lab(ref_img)

        # Precompute Canny edge representations
        edges_aligned = cv2.Canny(proc_aligned, 50, 150)
        edges_ref = cv2.Canny(proc_ref, 50, 150)

        results = {}

        for comp in components:
            cid = comp["id"]
            x, y, w, h = comp["bbox_xywh"]

            img_h, img_w = proc_aligned.shape
            x1, y1 = max(0, min(x, img_w - 1)), max(0, min(y, img_h - 1))
            x2, y2 = max(x1 + 1, min(img_w, x + w)), max(y1 + 1, min(img_h, y + h))

            roi_test = proc_aligned[y1:y2, x1:x2]
            roi_ref = proc_ref[y1:y2, x1:x2]
            roi_edge_test = edges_aligned[y1:y2, x1:x2]
            roi_edge_ref = edges_ref[y1:y2, x1:x2]

            if roi_test.shape != roi_ref.shape:
                roi_test = cv2.resize(roi_test, (roi_ref.shape[1], roi_ref.shape[0]))
            if roi_edge_test.shape != roi_edge_ref.shape:
                roi_edge_test = cv2.resize(roi_edge_test, (roi_edge_ref.shape[1], roi_edge_ref.shape[0]))

            if roi_test.shape[0] < 7 or roi_test.shape[1] < 7 or roi_ref.shape[0] < 7 or roi_ref.shape[1] < 7:
                results[cid] = {
                    "presence_score": 0.0,
                    "is_missing": True,
                    "ssim_score": 0.0,
                    "ncc_score": 0.0,
                    "edge_score": 0.0,
                    "diff_ratio": 1.0,
                    "bbox_px": [x, y, w, h]
                }
                continue

            # 1. Structural Similarity (SSIM)
            try:
                score_ssim = float(ssim(roi_test, roi_ref))
            except Exception:
                score_ssim = 0.5
            score_ssim = float(np.clip(score_ssim, 0.0, 1.0))

            # 2. Normalized Cross-Correlation (NCC)
            try:
                res_ncc = cv2.matchTemplate(roi_test, roi_ref, cv2.TM_CCOEFF_NORMED)
                score_ncc = float(np.clip(res_ncc[0][0], 0.0, 1.0))
            except Exception:
                score_ncc = score_ssim

            # 3. Edge Structure Verification
            edge_diff = cv2.absdiff(roi_edge_test, roi_edge_ref)
            edge_diff_ratio = float(np.count_nonzero(edge_diff)) / float(max(1, edge_diff.size))
            score_edge = float(np.clip(1.0 - edge_diff_ratio, 0.0, 1.0))

            # Tri-Metric Ensemble Fusion
            ensemble_presence = (0.50 * score_ssim) + (0.30 * score_ncc) + (0.20 * score_edge)
            ensemble_presence = round(float(np.clip(ensemble_presence, 0.0, 1.0)), 4)

            # Absolute Diff Metric
            diff = cv2.absdiff(roi_test, roi_ref)
            _, thresh_diff = cv2.threshold(diff, 45, 255, cv2.THRESH_BINARY)
            diff_ratio = float(np.count_nonzero(thresh_diff)) / float(thresh_diff.size) if thresh_diff.size > 0 else 0.0

            is_missing = bool(ensemble_presence < self.ensemble_threshold or diff_ratio > self.diff_ratio_threshold)

            results[cid] = {
                "presence_score": ensemble_presence,
                "is_missing": is_missing,
                "ssim_score": round(score_ssim, 4),
                "ncc_score": round(score_ncc, 4),
                "edge_score": round(score_edge, 4),
                "diff_ratio": round(diff_ratio, 4),
                "bbox_px": [x, y, w, h]
            }

        return results
