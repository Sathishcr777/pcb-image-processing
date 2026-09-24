"""
Single-Laptop Interactive Demo Runner
Team 6 — AI Deployment & Local Inspection Viewer

Runs full 2D/3D PCB inspection locally on this single laptop:
- No secondary laptop or Ubiquiti network required.
- Inspects test boards or local webcam feed in real-time.
- Renders publication-quality OpenCV inspection overlays directly on your screen.
"""

import os
import sys
import cv2
import numpy as np
import json

# Insert base directory into path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from server.pipeline.aligner import align_board
from server.pipeline.detector_2d import detect_2d_defects
from server.pipeline.detector_depth import detect_depth_anomalies
from server.pipeline.health_index import compute_health_index
from server.pipeline.visualizer import render_overlay

def run_single_laptop_demo():
    print("==========================================================")
    print("  PCB AI INSPECTION SYSTEM — SINGLE LAPTOP DEMO MODE")
    print("==========================================================")

    # 1. Load Golden Reference Board & Precompute Reference Depth
    ref_path = os.path.join(BASE_DIR, "server", "reference", "golden_board.png")
    if not os.path.exists(ref_path):
        print("[INFO] Golden reference not found. Generating sample PCB boards...")
        from scripts.generate_synthetic_boards import main as gen_boards
        gen_boards()

    ref_bgr = cv2.imread(ref_path)
    if ref_bgr is None:
        print(f"[ERROR] Failed to load reference image from {ref_path}")
        return

    # Load component ROI configuration
    config_path = os.path.join(BASE_DIR, "server", "config", "components.json")
    with open(config_path, "r", encoding="utf-8") as f:
        component_config = json.load(f)

    component_rois = component_config.get("components", [])

    print("\n--- INSTRUCTIONS ---")
    print("  Press '1' -> Inspect Board TB001 (Missing Main IC U1)")
    print("  Press '2' -> Inspect Board TB002 (Tombstoned Capacitor C3)")
    print("  Press '3' -> Inspect Board TB003 (Tilted Resistor R12)")
    print("  Press '4' -> Inspect Board TB004 (Shifted Capacitor C5)")
    print("  Press '5' -> Inspect Board TB005 (Known-Good Board - PASS)")
    print("  Press 'w' -> Open Local Webcam Live Feed & Inspect")
    print("  Press 'q' -> Quit Demo")
    print("---------------------\n")

    tb_dir = os.path.join(BASE_DIR, "evaluation", "test_boards")

    def inspect_and_show(test_bgr, board_name="Single-Laptop Test"):
        # Run Alignment
        aligned_bgr, homography, align_score = align_board(ref_bgr, test_bgr)
        if align_score < 0.40:
            print(f"[WARNING] Alignment score low ({align_score:.2f}). Board may be misaligned.")

        # Run 2D Presence Detection
        res_2d = detect_2d_defects(ref_bgr, aligned_bgr, component_rois)

        # Run 3D Depth Anomaly Detection
        res_depth = detect_depth_anomalies(aligned_bgr, None, homography, component_rois)

        # Compute Health Index & IPC-A-610 Verdict
        hi, verdict, merged_results = compute_health_index(res_2d, res_depth, component_rois)

        print(f"\n[INSPECTION RESULT] {board_name}")
        print(f"  Health Index: {hi:.4f} | Verdict: {verdict}")
        for comp in merged_results:
            flags = []
            if comp.get("is_missing"): flags.append("MISSING")
            if comp.get("height_flag"): flags.append("HEIGHT_DEV")
            if comp.get("tombstone_flag"): flags.append("TOMBSTONE")
            if comp.get("tilt_flag"): flags.append("TILT")
            flag_str = ", ".join(flags) if flags else "PASS"
            print(f"  - {comp['id']} ({comp['name']}): {flag_str}")

        # Render OpenCV Visual Overlay
        overlay_bytes = render_overlay(aligned_bgr, merged_results, hi, verdict, board_serial=board_name)
        overlay_arr = np.frombuffer(overlay_bytes, dtype=np.uint8)
        overlay_bgr = cv2.imdecode(overlay_arr, cv2.IMREAD_COLOR)

        cv2.imshow("Single Laptop PCB Inspection Overlay", overlay_bgr)
        cv2.waitKey(0)

    # Initial view on startup: Inspect TB001
    sample_img_path = os.path.join(tb_dir, "TB001.png")
    if os.path.exists(sample_img_path):
        sample_bgr = cv2.imread(sample_img_path)
        inspect_and_show(sample_bgr, board_name="TB001 (Missing IC U1)")

    while True:
        print("Enter key choice in terminal (1-5, w for webcam, q to exit): ", end="", flush=True)
        choice = input().strip().lower()

        if choice == '1':
            path = os.path.join(tb_dir, "TB001.png")
            if os.path.exists(path):
                inspect_and_show(cv2.imread(path), "TB001 (Missing IC U1)")
        elif choice == '2':
            path = os.path.join(tb_dir, "TB002.png")
            if os.path.exists(path):
                inspect_and_show(cv2.imread(path), "TB002 (Tombstone Cap C3)")
        elif choice == '3':
            path = os.path.join(tb_dir, "TB003.png")
            if os.path.exists(path):
                inspect_and_show(cv2.imread(path), "TB003 (Tilted Resistor R12)")
        elif choice == '4':
            path = os.path.join(tb_dir, "TB004.png")
            if os.path.exists(path):
                inspect_and_show(cv2.imread(path), "TB004 (Shifted Cap C5)")
        elif choice == '5':
            path = os.path.join(tb_dir, "TB005.png")
            if os.path.exists(path):
                inspect_and_show(cv2.imread(path), "TB005 (Known-Good Board)")
        elif choice == 'w':
            print("[WEBCAM] Opening webcam feed. Press SPACE to capture, Q to exit webcam.")
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("[ERROR] Cannot open webcam.")
                continue
            while True:
                ret, frame = cap.read()
                if not ret: break
                cv2.imshow("Webcam Live Feed - Press SPACE to Inspect", frame)
                k = cv2.waitKey(1) & 0xFF
                if k == 32: # SPACE
                    cv2.destroyWindow("Webcam Live Feed - Press SPACE to Inspect")
                    inspect_and_show(frame, "Webcam Live Board Capture")
                    break
                elif k == ord('q'):
                    cv2.destroyWindow("Webcam Live Feed - Press SPACE to Inspect")
                    break
            cap.release()
        elif choice == 'q':
            print("Exiting Single-Laptop Demo Mode.")
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_single_laptop_demo()
