"""
Enterprise Solder Meniscus 3D Profiler & Coplanarity Metrology Engine.
Computes 2D cross-sectional slice curves Z(x), IPC-A-610 wetting angles (toe/heel/side),
3D solder paste volume integration, IC lead coplanarity, and 3D Wavefront OBJ mesh export.
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Any

class SolderProfilerEngine:
    def __init__(self, px_to_um: float = 2.5):
        self.px_to_um = px_to_um

    def extract_cross_section_profile(
        self,
        height_map_um: np.ndarray,
        slice_fraction: float = 0.5,
        axis: str = "horizontal"
    ) -> Dict[str, Any]:
        """
        Extracts 1D height curve Z(x) across a cross-section line.
        Returns: {x_coords_um, z_measured_um, z_ideal_um, z_upper_tol_um, z_lower_tol_um, wetting_angles}
        """
        h, w = height_map_um.shape[:2]

        if axis == "horizontal":
            row_idx = int(np.clip(slice_fraction * h, 0, h - 1))
            z_measured = height_map_um[row_idx, :].astype(float)
            length = w
        else:
            col_idx = int(np.clip(slice_fraction * w, 0, w - 1))
            z_measured = height_map_um[:, col_idx].astype(float)
            length = h

        x_coords_um = (np.arange(length) * self.px_to_um).tolist()
        z_measured_list = z_measured.tolist()

        # Generate theoretical IPC-A-610 Ideal Concave Meniscus Curve
        # Modeled as a smooth catenary / polynomial concave fillet
        norm_x = np.linspace(-1.0, 1.0, length)
        peak_z = float(np.max(z_measured)) if len(z_measured) > 0 else 120.0
        min_z = float(np.min(z_measured)) if len(z_measured) > 0 else 10.0

        # Ideal concave curve: low in center, smoothly rising to toe and heel
        z_ideal = min_z + (peak_z - min_z) * (norm_x**2)
        z_upper_tol = z_ideal + 15.0 # +15 um tolerance band
        z_lower_tol = np.maximum(0.0, z_ideal - 15.0) # -15 um tolerance band

        # Calculate local slope derivatives for wetting angles at boundaries (Toe & Heel)
        dz_dx = np.gradient(z_measured, self.px_to_um)
        toe_angle_deg = float(np.degrees(np.arctan(abs(dz_dx[int(length * 0.1)]))))
        heel_angle_deg = float(np.degrees(np.arctan(abs(dz_dx[int(length * 0.9)]))))
        mid_angle_deg = float(np.degrees(np.arctan(abs(dz_dx[int(length * 0.5)]))))

        # Conformance check
        in_tolerance = bool(np.all(z_measured <= z_upper_tol + 5.0) and np.all(z_measured >= z_lower_tol - 5.0))

        return {
            "x_coords_um": [round(x, 1) for x in x_coords_um],
            "z_measured_um": [round(z, 2) for z in z_measured_list],
            "z_ideal_um": [round(z, 2) for z in z_ideal.tolist()],
            "z_upper_tol_um": [round(z, 2) for z in z_upper_tol.tolist()],
            "z_lower_tol_um": [round(z, 2) for z in z_lower_tol.tolist()],
            "toe_wetting_angle_deg": round(toe_angle_deg, 1),
            "heel_wetting_angle_deg": round(heel_angle_deg, 1),
            "mid_wetting_angle_deg": round(mid_angle_deg, 1),
            "peak_height_um": round(peak_z, 1),
            "is_within_tolerance": in_tolerance
        }

    def compute_solder_volume(self, height_map_um: np.ndarray, pad_mask: np.ndarray = None) -> Dict[str, Any]:
        """
        Integrates height over pad area to compute exact solder paste volume:
        V = sum(Z(x,y) * dx * dy) in nanoliters (nL) and cubic micrometers.
        """
        if pad_mask is None:
            pad_mask = np.ones_like(height_map_um, dtype=bool)

        pixel_area_um2 = (self.px_to_um) ** 2
        masked_heights = height_map_um[pad_mask]

        # Volume in um^3
        volume_um3 = float(np.sum(masked_heights) * pixel_area_um2)
        # 1 nanoliter (nL) = 1,000,000 um^3 = 10^6 um^3 = 10^-3 mm^3
        volume_nl = volume_um3 / 1e6
        wetted_pixels = int(np.sum(masked_heights > 5.0))
        total_pad_pixels = int(np.sum(pad_mask))
        coverage_pct = float((wetted_pixels / max(1, total_pad_pixels)) * 100.0)

        return {
            "volume_um3": round(volume_um3, 0),
            "volume_nl": round(volume_nl, 3),
            "wetted_area_coverage_pct": round(coverage_pct, 1),
            "mean_solder_thickness_um": round(float(np.mean(masked_heights)), 2),
            "peak_solder_thickness_um": round(float(np.max(masked_heights)), 2)
        }

    def compute_lead_coplanarity(self, lead_heights_um: List[float]) -> Dict[str, Any]:
        """
        Computes multi-lead IC coplanarity: delta_Z = max(Z) - min(Z).
        IPC-A-610 Class 3 limit for QFP/SOIC is max coplanarity deviation <= 50 um.
        """
        if not lead_heights_um:
            return {"coplanarity_delta_um": 0.0, "is_coplanar": True, "ipc_status": "NO_LEADS"}

        arr = np.array(lead_heights_um)
        delta_z = float(np.max(arr) - np.min(arr))
        is_pass = delta_z <= 50.0

        return {
            "coplanarity_delta_um": round(delta_z, 1),
            "min_lead_height_um": round(float(np.min(arr)), 1),
            "max_lead_height_um": round(float(np.max(arr)), 1),
            "mean_lead_height_um": round(float(np.mean(arr)), 1),
            "lead_count": len(lead_heights_um),
            "is_coplanar": is_pass,
            "ipc_coplanarity_verdict": "CLASS 3 PASS" if is_pass else "VIOLATION (LIFTED PIN)"
        }

    def generate_wavefront_obj(self, height_map_um: np.ndarray, step: int = 2) -> str:
        """
        Generates standard 3D Wavefront .OBJ mesh string from 2D height elevation map.
        """
        h, w = height_map_um.shape[:2]
        obj_lines = ["# Photometric 3D Solder Metrology Studio Wavefront OBJ", "# Unit: Micrometers (um)"]

        # Vertices
        vertex_idx = {}
        v_count = 1
        for r in range(0, h, step):
            for c in range(0, w, step):
                x = c * self.px_to_um
                y = r * self.px_to_um
                z = float(height_map_um[r, c])
                obj_lines.append(f"v {x:.2f} {y:.2f} {z:.2f}")
                vertex_idx[(r, c)] = v_count
                v_count += 1

        # Faces (Triangulated Quad Grid)
        for r in range(0, h - step, step):
            for c in range(0, w - step, step):
                v1 = vertex_idx.get((r, c))
                v2 = vertex_idx.get((r, c + step))
                v3 = vertex_idx.get((r + step, c + step))
                v4 = vertex_idx.get((r + step, c))
                if v1 and v2 and v3 and v4:
                    obj_lines.append(f"f {v1} {v2} {v3}")
                    obj_lines.append(f"f {v1} {v3} {v4}")

        return "\n".join(obj_lines)
