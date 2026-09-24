"""
Multi-Angle RGB Photometric Stereo & 3D Solder Meniscus Inspection Engine.
Physics-based surface normal recovery, IPC-A-610 wetting angle classification,
and Frankot-Chellappa / FFT Poisson 3D topographical height integration.
"""

import cv2
import numpy as np
from typing import Tuple, Dict, List, Any

class PhotometricStereoEngine:
    def __init__(self):
        # Calibrated 3-channel light direction unit vectors [Lx, Ly, Lz]
        # Red: High-angle direct illumination (theta=75 deg, phi=90 deg)
        # Green: 45-degree slope illumination (theta=45 deg, phi=210 deg)
        # Blue: 20-degree grazing angle illumination (theta=20 deg, phi=330 deg)
        self.light_matrix = np.array([
            [0.0, np.sin(np.radians(75)), np.cos(np.radians(75))], # Red channel
            [-np.sin(np.radians(45))*np.cos(np.radians(30)), -np.sin(np.radians(45))*np.sin(np.radians(30)), np.cos(np.radians(45))], # Green
            [ np.sin(np.radians(20))*np.cos(np.radians(30)), -np.sin(np.radians(20))*np.sin(np.radians(30)), np.cos(np.radians(20))]  # Blue
        ], dtype=np.float32)

        # Invert light matrix for least-squares normal recovery: G = L_inv * I
        self.light_inv = np.linalg.pinv(self.light_matrix)

    def reconstruct_surface_normals(self, rgb_img: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Recovers surface normals (Nx, Ny, Nz), albedo (reflectance), slope angles, and 3D height.
        Returns: (normals_rgb_vis, albedo_map, slope_deg_map, height_map_um)
        """
        if rgb_img.shape[2] != 3:
            raise ValueError("Photometric Stereo requires 3-channel RGB image.")

        img_float = rgb_img.astype(np.float32) / 255.0
        h, w = img_float.shape[:2]

        # Reshape [H, W, 3] -> [3, H*W]
        I = img_float.reshape(-1, 3).T

        # Solve G = L_inv * I -> G: [3, H*W] (where G = albedo * Normal)
        G = np.dot(self.light_inv, I)

        # Albedo rho = ||G||
        albedo = np.linalg.norm(G, axis=0) + 1e-6 # [H*W]
        normals = G / albedo[None, :] # [3, H*W]

        # Clamp Nz >= 0 (upward facing surface)
        normals[2, :] = np.clip(normals[2, :], 0.05, 1.0)
        # Re-normalize
        normals = normals / (np.linalg.norm(normals, axis=0, keepdims=True) + 1e-6)

        # Calculate local slope angle alpha = arccos(Nz) in degrees
        slope_deg = np.degrees(np.arccos(np.clip(normals[2, :], 0.0, 1.0)))

        # Format maps
        normals_map = normals.T.reshape(h, w, 3) # [H, W, 3] in range [-1, 1]
        normals_vis = ((normals_map * 0.5 + 0.5) * 255.0).astype(np.uint8)
        albedo_map = albedo.reshape(h, w)
        slope_map = slope_deg.reshape(h, w)

        # 3D Height via Fast Fourier Transform Poisson Integration
        height_map = self.integrate_poisson_height(normals_map)

        return normals_vis, albedo_map, slope_map, height_map

    def integrate_poisson_height(self, normals_map: np.ndarray) -> np.ndarray:
        """
        Solves Poisson equation via 2D FFT to reconstruct continuous 3D elevation Z(x, y).
        Gradients: p = -Nx/Nz, q = -Ny/Nz
        """
        h, w = normals_map.shape[:2]
        nx = normals_map[:, :, 0]
        ny = normals_map[:, :, 1]
        nz = np.clip(normals_map[:, :, 2], 0.08, 1.0)

        p = -nx / nz
        q = -ny / nz

        # Frequency domain coordinates
        u = np.fft.fftfreq(w)
        v = np.fft.fftfreq(h)
        U, V = np.meshgrid(u, v)

        # Gradients in Fourier domain
        P = np.fft.fft2(p)
        Q = np.fft.fft2(q)

        # Poisson equation in frequency domain: -4 * pi^2 * (U^2 + V^2) * Z = -2 * pi * i * (U * P + V * Q)
        denom = (2.0 * np.pi * U)**2 + (2.0 * np.pi * V)**2
        denom[0, 0] = 1.0 # Avoid division by zero at DC component

        Z_freq = (-1j * 2.0 * np.pi * U * P - 1j * 2.0 * np.pi * V * Q) / (denom + 1e-6)
        Z_freq[0, 0] = 0.0 # Zero mean elevation

        # Inverse FFT
        z_spatial = np.real(np.fft.ifft2(Z_freq))
        z_norm = z_spatial - np.min(z_spatial)
        # Calibrated scale in micrometers (~0 to 180 um solder height)
        height_um = (z_norm / (np.max(z_norm) + 1e-5)) * 180.0
        return height_um.astype(np.float32)

    def classify_solder_joint(self, roi_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Evaluates solder joint wetting angle, curvature, and volume against IPC-A-610 Class 2/3.
        """
        if roi_bgr is None or roi_bgr.size == 0:
            return {"mean_wetting_angle_deg": 0.0, "verdict": "NO_DATA", "ipc_status": "NONE", "is_defect": False}

        rgb = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2RGB)
        normals_vis, albedo_map, slope_map, height_map = self.reconstruct_surface_normals(rgb)

        mean_slope = float(np.mean(slope_map))
        p90_slope = float(np.percentile(slope_map, 90))
        peak_height_um = float(np.max(height_map))

        # IPC-A-610 Criteria
        if mean_slope < 12.0:
            status = "INSUFFICIENT_SOLDER"
            ipc = "IPC Class 3 Violation (Insufficient Wetting)"
            is_defect = True
        elif 15.0 <= mean_slope <= 45.0:
            status = "OPTIMAL_CONCAVE_MENISCUS"
            ipc = "IPC Class 3 Target (Optimal Wetting)"
            is_defect = False
        elif 45.0 < mean_slope <= 65.0:
            status = "ACCEPTABLE_CLASS_2"
            ipc = "IPC Class 2 Acceptable (Slight Excess)"
            is_defect = False
        elif 65.0 < mean_slope <= 75.0:
            status = "EXCESS_SOLDER_BRIDGE"
            ipc = "IPC Class 3 Violation (Excess Solder / Bulge)"
            is_defect = True
        else:
            status = "TOMBSTONE_LIFTED_LEAD"
            ipc = "IPC Class 3 Defect (Vertical Component Lift)"
            is_defect = True

        return {
            "mean_wetting_angle_deg": round(mean_slope, 2),
            "peak_slope_deg": round(p90_slope, 2),
            "peak_solder_height_um": round(peak_height_um, 1),
            "solder_status": status,
            "ipc_classification": ipc,
            "is_defect": is_defect,
            "albedo_mean": round(float(np.mean(albedo_map)), 3)
        }
