"""
3D Substrate Ground-Plane Leveler
Team 5 - Advanced Depth Normalization

Solves camera perspective slant & board tilt by fitting a 3D plane
Z_base = A*x + B*y + C to the bare PCB substrate and subtracting it,
yielding pure relative component vertical lift.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple

class SubstrateLeveler:
    def __init__(self, sample_grid_step: int = 16):
        self.sample_grid_step = sample_grid_step

    def level_depth_map(self, raw_depth: np.ndarray, components: List[Dict]) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """
        Fits a 3D plane to non-component substrate pixels and subtracts it.
        Returns:
            leveled_depth: Depth map normalized relative to flat board substrate [0.0, 1.0]
            plane_depth: The calculated substrate slope plane
            plane_stats: Estimated board tilt angles in X and Y (degrees)
        """
        img_h, img_w = raw_depth.shape[:2]
        
        # 1. Create a binary mask of bare substrate (exclude all component ROIs)
        substrate_mask = np.ones((img_h, img_w), dtype=np.uint8) * 255
        for comp in components:
            x, y, w, h = comp.get("bbox_xywh", [0, 0, 0, 0])
            # Add a slight padding margin (+10%) around components
            pad_x, pad_y = max(4, int(w * 0.1)), max(4, int(h * 0.1))
            x1, y1 = max(0, x - pad_x), max(0, y - pad_y)
            x2, y2 = min(img_w, x + w + pad_x), min(img_h, y + h + pad_y)
            substrate_mask[y1:y2, x1:x2] = 0

        # Avoid image borders (often have shadows or fixtures)
        border = 12
        substrate_mask[:border, :] = 0
        substrate_mask[-border:, :] = 0
        substrate_mask[:, :border] = 0
        substrate_mask[:, -border:] = 0

        # 2. Sample substrate (X, Y, Z) coordinates on a regular grid
        sample_y, sample_x = np.where(substrate_mask[::self.sample_grid_step, ::self.sample_grid_step] > 0)
        sample_y = sample_y * self.sample_grid_step
        sample_x = sample_x * self.sample_grid_step

        if len(sample_x) < 20:
            # Fallback if too few substrate pixels found
            return raw_depth.copy(), np.zeros_like(raw_depth), {"tilt_x_deg": 0.0, "tilt_y_deg": 0.0}

        sample_z = raw_depth[sample_y, sample_x]

        # 3. Fit 3D Plane Equation: Z = A*X + B*Y + C via Least Squares
        # Formulation: M * [A, B, C]^T = Z, where M = [X, Y, 1]
        M = np.column_stack([sample_x, sample_y, np.ones_like(sample_x)])
        
        try:
            plane_coeffs, _, _, _ = np.linalg.lstsq(M, sample_z, rcond=None)
            A, B, C = float(plane_coeffs[0]), float(plane_coeffs[1]), float(plane_coeffs[2])
        except Exception:
            A, B, C = 0.0, 0.0, float(np.median(sample_z))

        # 4. Generate the Substrate Plane Map over the entire image grid
        grid_x, grid_y = np.meshgrid(np.arange(img_w), np.arange(img_h))
        plane_depth = A * grid_x + B * grid_y + C

        # 5. Subtract Base Plane: Pure Component Height Above Substrate
        relative_depth = raw_depth - plane_depth
        
        # Substrate should be at 0.0; elevate positive component heights
        # Clip negative noise (slight depressions/vias)
        leveled = np.clip(relative_depth, 0.0, None)
        
        # Normalize to [0.0, 1.0] for stable threshold comparison
        max_val = np.percentile(leveled, 99.0)
        if max_val > 1e-4:
            leveled = np.clip(leveled / max_val, 0.0, 1.0)

        # Estimate substrate tilt angles
        tilt_x_deg = round(float(np.degrees(np.arctan(A))), 2)
        tilt_y_deg = round(float(np.degrees(np.arctan(B))), 2)

        plane_stats = {
            "plane_equation": f"Z = {A:.5f}X + {B:.5f}Y + {C:.3f}",
            "board_pitch_deg": tilt_y_deg,
            "board_roll_deg": tilt_x_deg,
            "substrate_sample_count": len(sample_x)
        }

        return leveled.astype(np.float32), plane_depth.astype(np.float32), plane_stats
