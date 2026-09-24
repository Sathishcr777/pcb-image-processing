"""
Synthetic PCB Board Generator
Team 4 - Data Engineering & Hardware Gate

Generates high-resolution 1080p synthetic PCB images for 31 test boards
and golden reference candidates with realistic components, traces, solder pads,
and exact physical defects matching evaluation/test_labels.csv.
"""

import cv2
import numpy as np
import os
import json

def get_base_components():
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server", "config", "components.json"))
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise RuntimeError(f"Could not locate components configuration at {config_path}")

def render_pcb(defects=None, shift_offset=(0, 0), noise_level=0):
    """
    Renders a 1280x720 PCB image.
    defects: dict mapping component_id -> defect_type ('missing', 'tombstone', 'tilt', 'shift')
    """
    if defects is None:
        defects = {}

    width, height = 1280, 720
    img = np.full((height, width, 3), (34, 120, 34), dtype=np.uint8) # Dark Green PCB Board

    # Apply global framing shift if specified (e.g. edge case)
    dx, dy = shift_offset

    # Draw Copper Traces (Gold/Copper lines)
    cv2.line(img, (100+dx, 200+dy), (400+dx, 200+dy), (0, 215, 255), 3)
    cv2.line(img, (400+dx, 200+dy), (400+dx, 500+dy), (0, 215, 255), 3)
    cv2.line(img, (200+dx, 300+dy), (600+dx, 300+dy), (0, 215, 255), 2)
    cv2.line(img, (700+dx, 150+dy), (1100+dx, 150+dy), (0, 215, 255), 3)
    cv2.line(img, (350+dx, 520+dy), (800+dx, 500+dy), (0, 215, 255), 2)

    # Draw Silkscreen Grid & Outer Border
    cv2.rectangle(img, (50+dx, 50+dy), (1230+dx, 670+dy), (240, 240, 240), 2)
    cv2.putText(img, "PCB-INSPECTION-BOARD v1.0 [IPC-A-610H]", (70+dx, 90+dy),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (240, 240, 240), 2)

    components = get_base_components()

    for comp in components:
        cid = comp["id"]
        x, y, w, h = comp["bbox_xywh"]
        x += dx
        y += dy

        d_type = defects.get(cid, None)

        # Draw Solder Pads first
        cv2.rectangle(img, (x-4, y-4), (x+w+4, y+h+4), (180, 180, 180), 2)
        cv2.putText(img, cid, (x, y-8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1)

        if d_type == "missing":
            # Missing component: render bare copper pad with cross mark
            cv2.rectangle(img, (x, y), (x+w, y+h), (30, 70, 30), -1)
            cv2.line(img, (x, y), (x+w, y+h), (40, 40, 200), 2)
            cv2.line(img, (x+w, y), (x, y+h), (40, 40, 200), 2)
            cv2.putText(img, "MISSING", (x+5, y+h//2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        elif d_type == "tombstone":
            # Tombstoned component: standing vertically on left pad edge (Bright Yellow/Amber body)
            cv2.rectangle(img, (x, y), (x+w//2, y+h), (0, 215, 255), -1)
            cv2.rectangle(img, (x+w//2, y), (x+w, y+h), (30, 70, 30), -1) # Bare pad
            cv2.putText(img, "TOMB", (x, y-18), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 215, 255), 1)

        elif d_type == "tilt":
            # Tilted component: rotated angle (~25 deg) (Bright Purple body)
            center = (x + w // 2, y + h // 2)
            rect = (center, (w, h), 25)
            box = cv2.boxPoints(rect)
            box = np.intp(box)
            cv2.drawContours(img, [box], 0, (247, 85, 168), -1)
            cv2.drawContours(img, [box], 0, (255, 255, 255), 1)

        elif d_type == "shift":
            # Shifted component: offset by 50% off-pad (Bright Cyan body)
            sx, sy = x + w // 2, y + h // 4
            cv2.rectangle(img, (sx, sy), (sx+w, sy+h), (212, 182, 6), -1)

        else:
            # Normal present component
            if "U" in cid or "VR" in cid:
                # Black IC package with pins
                cv2.rectangle(img, (x, y), (x+w, y+h), (25, 25, 25), -1)
                cv2.rectangle(img, (x+5, y+5), (x+w-5, y+h-5), (45, 45, 45), -1)
                # Pin indicators
                for px in range(x+10, x+w-10, 20):
                    cv2.rectangle(img, (px, y-5), (px+8, y), (200, 200, 200), -1)
                    cv2.rectangle(img, (px, y+h), (px+8, y+h+5), (200, 200, 200), -1)
            elif "C" in cid:
                # Blue surface-mount capacitor
                cv2.rectangle(img, (x, y), (x+w, y+h), (180, 60, 50), -1)
                cv2.rectangle(img, (x+2, y+2), (x+8, y+h-2), (210, 210, 210), -1)
                cv2.rectangle(img, (x+w-8, y+2), (x+w-2, y+h-2), (210, 210, 210), -1)
            else:
                # Resistor / Passive
                cv2.rectangle(img, (x, y), (x+w, y+h), (50, 50, 150), -1)
                cv2.rectangle(img, (x+2, y+2), (x+6, y+h-2), (190, 190, 190), -1)
                cv2.rectangle(img, (x+w-6, y+2), (x+w-2, y+h-2), (190, 190, 190), -1)

    if noise_level > 0:
        noise = np.random.normal(0, noise_level, img.shape).astype(np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    return img

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ref_dir = os.path.join(base_dir, "server", "reference")
    tb_dir = os.path.join(base_dir, "evaluation", "test_boards")
    os.makedirs(ref_dir, exist_ok=True)
    os.makedirs(tb_dir, exist_ok=True)

    # 1. Golden Reference Image
    golden_img = render_pcb(defects={})
    cv2.imwrite(os.path.join(ref_dir, "golden_board.png"), golden_img)
    print(f"[SUCCESS] Golden reference saved to {os.path.join(ref_dir, 'golden_board.png')}")

    # 2. Golden Candidates
    for i in range(1, 6):
        cand_img = render_pcb(defects={}, noise_level=i*0.5)
        cv2.imwrite(os.path.join(ref_dir, f"golden_candidate_{i}.png"), cand_img)

    # 3. 31 Test Boards Mapping
    test_specs = {
        "TB001": {"defects": {"U1": "missing"}},
        "TB002": {"defects": {"C3": "tombstone"}},
        "TB003": {"defects": {"R12": "tilt"}},
        "TB004": {"defects": {"C5": "shift"}},
        "TB005": {"defects": {}}, # Known good
        "TB006": {"defects": {}}, # Known good
        "TB007": {"defects": {}}, # Known good
        "TB008": {"defects": {}}, # Known good
        "TB009": {"defects": {}}, # Known good
        "TB010": {"defects": {"U2": "missing"}},
        "TB011": {"defects": {"VR1": "missing"}},
        "TB012": {"defects": {"U1": "missing"}},
        "TB013": {"defects": {"U2": "missing"}},
        "TB014": {"defects": {"VR1": "missing", "C5": "missing"}},
        "TB015": {"defects": {"C1": "missing"}},
        "TB016": {"defects": {"C2": "missing"}},
        "TB017": {"defects": {"R1": "missing"}},
        "TB018": {"defects": {"R12": "missing"}},
        "TB019": {"defects": {"C5": "missing"}},
        "TB020": {"defects": {"U1": "missing", "C3": "missing"}},
        "TB021": {"defects": {"R1": "missing", "C1": "missing"}},
        "TB022": {"defects": {"U2": "missing", "C2": "missing", "R14": "missing"}},
        "TB023": {"defects": {"C5": "tombstone"}},
        "TB024": {"defects": {"R14": "tombstone"}},
        "TB025": {"defects": {"C5": "tilt"}},
        "TB026": {"defects": {"R1": "tilt"}},
        "TB027": {"defects": {"C3": "shift"}},
        "TB028": {"defects": {"R12": "shift"}},
        "TB029": {"defects": {}, "shift_offset": (15, 12)}, # Framing drift
        "TB030": {"defects": {}, "shift_offset": (-10, 8)}, # Framing drift
        "TB031": {"defects": {"R12": "missing", "C3": "missing"}}
    }

    for board_id, spec in test_specs.items():
        defs = spec.get("defects", {})
        s_off = spec.get("shift_offset", (0, 0))
        img = render_pcb(defects=defs, shift_offset=s_off)
        file_path = os.path.join(tb_dir, f"{board_id}.png")
        cv2.imwrite(file_path, img)

    print(f"[SUCCESS] Rendered all 31 test boards in {tb_dir}")

if __name__ == "__main__":
    main()
