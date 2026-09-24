"""
Deep Preprocessing Diagnostics & Stage-by-Stage Visual Breakdown
Demonstrates how raw camera image data is cleaned, normalized, and transformed.
"""

import os
import sys
import json
import cv2
import numpy as np

# Add project root to sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from server.pipeline.aligner import PCBAligner
from server.pipeline.detector_2d import Detector2D
from server.pipeline.substrate_leveler import SubstrateLeveler
from server.pipeline.detector_depth import DetectorDepth

def run_preprocessing_pipeline_diagnostic(image_path: str, ref_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Load Raw Image
    raw_img = cv2.imread(image_path)
    ref_img = cv2.imread(ref_path)
    
    if raw_img is None or ref_img is None:
        raise ValueError(f"Could not load images: {image_path}, {ref_path}")

    h, w = raw_img.shape[:2]
    cv2.imwrite(os.path.join(output_dir, "step1_raw_input.png"), raw_img)
    
    # 2. Stage 1: Optical Quality Gate & Exposure Analysis
    gray_raw = cv2.cvtColor(raw_img, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray_raw, cv2.CV_64F)
    blur_variance = float(laplacian.var())
    mean_brightness = float(np.mean(gray_raw))
    std_contrast = float(np.std(gray_raw))

    # Save visual Laplacian edge energy map
    laplacian_vis = cv2.normalize(np.abs(laplacian), None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    cv2.imwrite(os.path.join(output_dir, "step2_laplacian_sharpness_map.png"), laplacian_vis)

    # 3. Stage 2: Specular Reflection Detection & Clipping in CIE-LAB Color Space
    lab = cv2.cvtColor(raw_img, cv2.COLOR_BGR2LAB)
    l_chan, a_chan, b_chan = cv2.split(lab)
    
    # Identify shiny specular reflections on solder joints / metallic packages (> 240 in L)
    glare_mask = (l_chan > 240).astype(np.uint8) * 255
    glare_pixel_count = int(np.count_nonzero(glare_mask))
    
    # Generate highlighted glare visualization (red marks over glare points)
    glare_vis = raw_img.copy()
    glare_vis[glare_mask > 0] = [0, 0, 255] # Mark glare in Red
    cv2.imwrite(os.path.join(output_dir, "step3_specular_glare_mask.png"), glare_vis)

    # Suppress specular glare
    l_suppressed = l_chan.copy()
    l_suppressed[l_chan > 240] = 230

    # 4. Stage 3: CLAHE (Contrast-Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l_clahe = clahe.apply(l_suppressed)
    
    # Recombine to normalized BGR
    lab_normalized = cv2.merge([l_clahe, a_chan, b_chan])
    bgr_clahe = cv2.cvtColor(lab_normalized, cv2.COLOR_LAB2BGR)
    cv2.imwrite(os.path.join(output_dir, "step4_lab_clahe_normalized.png"), bgr_clahe)
    cv2.imwrite(os.path.join(output_dir, "step4_luminance_equalized.png"), l_clahe)

    # 5. Stage 4: Edge-Preserving Bilateral Denoising
    bilateral_denoised = cv2.bilateralFilter(l_clahe, d=5, sigmaColor=35, sigmaSpace=35)
    cv2.imwrite(os.path.join(output_dir, "step5_bilateral_denoised.png"), bilateral_denoised)

    # 6. Stage 5: Dual-Stage ORB Feature Extraction & RANSAC Homography Alignment
    aligner = PCBAligner(nfeatures=5000)
    aligned_img, align_q, H, align_stats = aligner.align(raw_img, ref_img)
    cv2.imwrite(os.path.join(output_dir, "step6_homography_aligned.png"), aligned_img)

    # Feature match visualization
    kp1, des1 = aligner.orb.detectAndCompute(bilateral_denoised, None)
    kp_vis = cv2.drawKeypoints(raw_img, kp1[:300], None, color=(0, 255, 0), flags=0)
    cv2.imwrite(os.path.join(output_dir, "step6_orb_features_detected.png"), kp_vis)

    # 7. Stage 6: Multi-Scale Structural Canny Edge Density Map
    canny_edges = cv2.Canny(bilateral_denoised, 50, 150)
    cv2.imwrite(os.path.join(output_dir, "step7_canny_edge_structure.png"), canny_edges)

    # 8. Stage 7: 3D Depth Ground-Plane Fitting & Substrate Leveling
    depth_engine = DetectorDepth(use_model=False)
    raw_depth = depth_engine.estimate_depth(aligned_img)
    cv2.imwrite(os.path.join(output_dir, "step8_raw_depth_map.png"), (raw_depth * 255).astype(np.uint8))

    config_path = os.path.join(ROOT_DIR, "server", "config", "components.json")
    with open(config_path, "r") as f:
        components = json.load(f)

    leveler = SubstrateLeveler()
    leveled_depth, substrate_plane, plane_stats = leveler.level_depth_map(raw_depth, components)
    
    cv2.imwrite(os.path.join(output_dir, "step9_substrate_plane.png"), cv2.normalize(substrate_plane, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U))
    cv2.imwrite(os.path.join(output_dir, "step9_leveled_pure_lift_depth.png"), (leveled_depth * 255).astype(np.uint8))

    # Colorize leveled depth heatmap
    depth_color = cv2.applyColorMap((leveled_depth * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
    cv2.imwrite(os.path.join(output_dir, "step9_depth_inferno_heatmap.png"), depth_color)

    # Build Diagnostic Report Summary
    report = {
        "input_dimensions": f"{w}x{h}",
        "stage_1_optical_quality": {
            "blur_variance": round(blur_variance, 2),
            "status": "SHARP (PASS)" if blur_variance >= 65 else "BLURRY (FAIL)",
            "mean_brightness": round(mean_brightness, 2),
            "dynamic_range_contrast": round(std_contrast, 2)
        },
        "stage_2_specular_suppression": {
            "shiny_solder_glare_pixels_detected": glare_pixel_count,
            "glare_percentage_of_board": f"{round((glare_pixel_count / (w * h)) * 100, 3)}%",
            "action": "Soft-clipped in CIE-LAB L-channel to 230 to prevent false-alarm triggers"
        },
        "stage_3_clahe_normalization": {
            "algorithm": "Contrast-Limited Adaptive Histogram Equalization",
            "tile_grid": "8x8 tiles",
            "clip_limit": 2.5,
            "purpose": "Eliminates uneven factory lighting gradients across the board surface"
        },
        "stage_4_bilateral_denoising": {
            "diameter": 5,
            "sigma_color": 35,
            "sigma_space": 35,
            "edge_preservation": "Maintains razor-sharp 0402 / IC pad boundaries while removing camera CMOS sensor noise"
        },
        "stage_5_alignment_homography": {
            "inlier_matches": align_stats.get("inlier_count", 0),
            "total_matches": align_stats.get("total_matches", 0),
            "alignment_quality_score": f"{round(align_q * 100, 1)}%",
            "homography_matrix_det": round(float(np.linalg.det(H)), 4)
        },
        "stage_6_substrate_depth_leveling": {
            "fitted_plane_equation": plane_stats.get("plane_equation", ""),
            "estimated_board_pitch_deg": plane_stats.get("board_pitch_deg", 0.0),
            "estimated_board_roll_deg": plane_stats.get("board_roll_deg", 0.0),
            "substrate_sampling_points": plane_stats.get("substrate_sample_count", 0),
            "result": "Substrate zeroed out to 0.0; isolated true physical component vertical lift"
        }
    }

    report_path = os.path.join(output_dir, "preprocessing_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report

if __name__ == "__main__":
    report = run_preprocessing_pipeline_diagnostic(
        image_path=os.path.join(ROOT_DIR, "evaluation", "test_boards", "TB001.png"),
        ref_path=os.path.join(ROOT_DIR, "server", "reference", "golden_board.png"),
        output_dir=os.path.join(ROOT_DIR, "evaluation", "reports", "preprocessing_steps")
    )
    print("PREPROCESSING DIAGNOSTIC COMPLETE:")
    print(json.dumps(report, indent=2))
