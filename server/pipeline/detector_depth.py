"""
3D Depth Defect Detector with Substrate Ground-Plane Leveling
Team 5 - Model Optimization & Sub-Team B

Features:
1. Substrate Ground-Plane Fitting to eliminate camera perspective slant
2. True vertical lift calculation relative to bare board substrate
3. Monocular Depth Estimation (Depth Anything V2 or High-Order Gradient Fallback)
4. Tombstoning, Billboarding, Component Tilt, and Seating Height Defect Detection
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from server.pipeline.substrate_leveler import SubstrateLeveler

class DetectorDepth:
    def __init__(
        self,
        theta_height: float = 0.14,
        theta_tilt: float = 0.040,
        theta_tomb: float = 0.012,
        use_model: bool = True,
        model_name_or_path: Optional[str] = None,
        hf_token: Optional[str] = None
    ):
        self.theta_height = theta_height
        self.theta_tilt = theta_tilt
        self.theta_tomb = theta_tomb
        self._pipe = None
        self.leveler = SubstrateLeveler(sample_grid_step=16)
        self.model_name = "Gradient-Depth-Engine (Fallback)"

        if use_model:
            try:
                from transformers import pipeline
                resolved_model = (model_name_or_path or "").strip() or "depth-anything/Depth-Anything-V2-Small-hf"
                local_model_path = Path(resolved_model)
                pipeline_kwargs = {"task": "depth-estimation", "model": str(local_model_path) if local_model_path.exists() else resolved_model}
                if hf_token:
                    pipeline_kwargs["token"] = hf_token
                self._pipe = pipeline(**pipeline_kwargs)
                if local_model_path.exists():
                    self.model_name = f"Local Depth Model ({local_model_path})"
                elif hf_token:
                    self.model_name = "Depth-Anything-V2-Small-hf (Authenticated)"
                else:
                    self.model_name = "Depth-Anything-V2-Small-hf (PyTorch)"
            except Exception:
                self._pipe = None
                self.model_name = "Gradient-Depth-Engine (Fallback)"

    def estimate_depth(self, img: np.ndarray) -> np.ndarray:
        """Estimates normalized depth map [0.0, 1.0] for input BGR image."""
        if self._pipe is not None:
            try:
                from PIL import Image
                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_img)
                res = self._pipe(pil_img)
                depth_map = np.array(res["depth"], dtype=np.float32)
                depth_norm = cv2.normalize(depth_map, None, alpha=0.0, beta=1.0, norm_type=cv2.NORM_MINMAX)
                return depth_norm.astype(np.float32)
            except Exception:
                pass

        # High-performance structural luminance + edge gradient depth fallback estimator
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        mag = cv2.magnitude(grad_x, grad_y)

        depth = (255.0 - gray.astype(np.float64)) * 0.6 + mag * 0.4
        depth_norm = cv2.normalize(depth, None, alpha=0.0, beta=1.0, norm_type=cv2.NORM_MINMAX)
        return depth_norm.astype(np.float32)

    def inspect(self, test_depth: np.ndarray, ref_depth: np.ndarray, components: list) -> Tuple[Dict, Dict]:
        """
        Levels both depth maps relative to the PCB substrate and calculates height/tilt/tombstone flags.
        Returns: (results_dict, substrate_leveling_stats)
        """
        if test_depth.shape != ref_depth.shape:
            test_depth = cv2.resize(test_depth, (ref_depth.shape[1], ref_depth.shape[0]))

        # 1. Level Depth Maps against Board Substrate
        test_leveled, _, test_stats = self.leveler.level_depth_map(test_depth, components)
        ref_leveled, _, ref_stats = self.leveler.level_depth_map(ref_depth, components)

        results = {}

        for comp in components:
            cid = comp["id"]
            x, y, w, h = comp["bbox_xywh"]
            check_depth = comp.get("depth_check", True)
            check_tilt = comp.get("tilt_check", True)
            check_tomb = comp.get("tombstone_check", True)

            img_h, img_w = test_leveled.shape
            x1, y1 = max(0, min(x, img_w - 1)), max(0, min(y, img_h - 1))
            x2, y2 = max(x1 + 1, min(img_w, x + w)), max(y1 + 1, min(img_h, y + h))

            roi_test_depth = test_leveled[y1:y2, x1:x2]
            roi_ref_depth = ref_leveled[y1:y2, x1:x2]

            if roi_test_depth.shape != roi_ref_depth.shape:
                roi_test_depth = cv2.resize(roi_test_depth, (roi_ref_depth.shape[1], roi_ref_depth.shape[0]))

            if roi_test_depth.shape[0] < 3 or roi_test_depth.shape[1] < 3 or roi_ref_depth.shape[0] < 3 or roi_ref_depth.shape[1] < 3:
                results[cid] = {
                    "height_penalty": 1.0,
                    "height_flag": True,
                    "tilt_flag": False,
                    "tombstone_flag": False,
                    "mean_dev": 1.0,
                    "tilt_diff": 0.0,
                    "asymmetry": 0.0
                }
                continue

            # 1. Height Anomaly Check (Component Lift / Depression vs Reference)
            abs_depth_diff = np.abs(roi_test_depth - roi_ref_depth)
            mean_dev = float(np.mean(abs_depth_diff))
            height_flag = bool(check_depth and mean_dev > self.theta_height)
            height_penalty = float(np.clip(mean_dev / (3.0 * self.theta_height + 1e-5), 0.0, 1.0))

            # 2. Tilt Check (Sobel Gradient Slope Difference across component body)
            try:
                sobel_test_x = cv2.Sobel(roi_test_depth, cv2.CV_32F, 1, 0, ksize=3)
                sobel_ref_x = cv2.Sobel(roi_ref_depth, cv2.CV_32F, 1, 0, ksize=3)
                tilt_diff = float(np.mean(np.abs(sobel_test_x - sobel_ref_x)))
            except Exception:
                tilt_diff = 0.0
            tilt_flag = bool(check_tilt and tilt_diff > self.theta_tilt)

            # 3. Tombstone Check (Left/Right Asymmetry difference relative to reference)
            mid_w = roi_test_depth.shape[1] // 2
            if mid_w > 0:
                test_asym = abs(float(np.mean(roi_test_depth[:, :mid_w])) - float(np.mean(roi_test_depth[:, mid_w:])))
                ref_asym = abs(float(np.mean(roi_ref_depth[:, :mid_w])) - float(np.mean(roi_ref_depth[:, mid_w:])))
                asymmetry = abs(test_asym - ref_asym)
            else:
                asymmetry = 0.0
            tombstone_flag = bool(check_tomb and asymmetry > self.theta_tomb)

            results[cid] = {
                "height_penalty": round(height_penalty, 4),
                "height_flag": height_flag,
                "tilt_flag": tilt_flag,
                "tombstone_flag": tombstone_flag,
                "mean_dev": round(mean_dev, 4),
                "tilt_diff": round(tilt_diff, 4),
                "asymmetry": round(asymmetry, 4)
            }

        leveling_summary = {
            "test_board_slant": test_stats,
            "ref_board_slant": ref_stats
        }

        return results, leveling_summary
