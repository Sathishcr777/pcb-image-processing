"""
Multi-Angle RGB Photometric Stereo Calibrated Dataset Generator.
Generates test boards illuminated under simulated 3-tier RGB ring lights.
"""

import os
import cv2
import numpy as np

def generate_photometric_boards():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    out_dir = os.path.join(base_dir, "server", "static", "photometric_samples")
    os.makedirs(out_dir, exist_ok=True)

    scenarios = [
        ("ps_sample_optimal", "OPTIMAL_WETTING", 28.0),
        ("ps_sample_insufficient", "INSUFFICIENT", 8.0),
        ("ps_sample_excess", "EXCESS_BRIDGE", 68.0),
        ("ps_sample_tombstone", "TOMBSTONE", 78.0)
    ]

    for name, stype, slope in scenarios:
        # Generate 400x400 multi-angle illuminated solder fillet
        img = np.zeros((400, 400, 3), dtype=np.uint8)

        # Base PCB Substrate (Red High Angle illumination dominates flat area)
        img[:, :] = (30, 80, 20)

        # Solder Pad (Copper / Silver)
        cv2.rectangle(img, (80, 100), (320, 300), (180, 190, 200), -1)

        # Solder Meniscus Slope Simulation (RGB color coding based on angle)
        # Red: Flat top, Green: 45 deg slope, Blue: 20 deg vertical
        if stype == "OPTIMAL_WETTING":
            # Perfect concave curve: Green highlight on slope, Red in center
            for r in range(120, 20, -5):
                cv2.ellipse(img, (200, 200), (int(r*1.2), r), 0, 0, 360, (50, 220, 120), -1)
            cv2.ellipse(img, (200, 200), (50, 30), 0, 0, 360, (230, 60, 40), -1)
        elif stype == "INSUFFICIENT":
            # Flat pad: Pure red reflection, no green slope
            cv2.ellipse(img, (200, 200), (90, 60), 0, 0, 360, (240, 50, 30), -1)
        elif stype == "EXCESS_BRIDGE":
            # Bulging bulb: Intense green and blue reflections
            cv2.ellipse(img, (200, 200), (140, 110), 0, 0, 360, (70, 240, 240), -1)
            cv2.line(img, (50, 200), (350, 200), (220, 230, 240), 16)
        elif stype == "TOMBSTONE":
            # Vertical face: Intense blue grazing reflection
            cv2.rectangle(img, (140, 80), (260, 280), (240, 120, 40), -1)
            cv2.rectangle(img, (140, 80), (180, 280), (255, 220, 60), -1)

        cv2.imwrite(os.path.join(out_dir, f"{name}.png"), img)

    print(f"Photometric stereo sample images generated in {out_dir}")

if __name__ == "__main__":
    generate_photometric_boards()
