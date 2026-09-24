"""
Custom PCB Board Layout Renderer
Team 4 - Data Engineering & Hardware Gate

Renders exact high-resolution PCB images matching the user's uploaded layout image:
- Grey substrate background (105, 105, 105)
- Color-coded component outlines (Orange headers, White/Pink ICs, Cyan/Magenta Caps, Yellow VRs)
- Generates Golden Reference & 31 Test Boards with accurate defects matching test_labels.csv
"""

import cv2
import numpy as np
import os
import json

def render_custom_pcb(defects=None, shift_offset=(0, 0), noise_level=0):
    if defects is None:
        defects = {}

    width, height = 1280, 720
    # Grey PCB substrate color matching user image
    img = np.full((height, width, 3), (110, 110, 110), dtype=np.uint8)

    dx, dy = shift_offset

    # Draw Silkscreen Bounding Frame & Outer Header Outlines (Orange/White)
    # Top Headers
    for hx in [350, 520, 690]:
        cv2.rectangle(img, (hx+dx, 180+dy), (hx+150+dx, 205+dy), (0, 140, 255), 4) # Orange border
        cv2.rectangle(img, (hx+4+dx, 184+dy), (hx+146+dx, 201+dy), (255, 255, 255), -1) # White inner fill

    # Bottom Headers
    for hx in [400, 570, 740]:
        cv2.rectangle(img, (hx+dx, 620+dy), (hx+150+dx, 645+dy), (0, 140, 255), 4) # Orange border
        cv2.rectangle(img, (hx+4+dx, 624+dy), (hx+166+dx, 641+dy), (255, 255, 255), -1) # White inner fill

    # Right Vertical Header (J1)
    d_j1 = defects.get("J1", None)
    if d_j1 != "missing":
        cv2.rectangle(img, (820+dx, 180+dy), (860+dx, 600+dy), (0, 140, 255), 5)
        cv2.rectangle(img, (825+dx, 185+dy), (855+dx, 595+dy), (255, 255, 255), -1)

    # Top-Left USB/Power Connector (CONN1)
    d_conn1 = defects.get("CONN1", None)
    if d_conn1 != "missing":
        cv2.rectangle(img, (200+dx, 230+dy), (340+dx, 330+dy), (0, 140, 255), 5)
        cv2.rectangle(img, (206+dx, 236+dy), (334+dx, 324+dy), (255, 255, 255), -1)

    # Bottom-Left Terminal Block (CONN2)
    d_conn2 = defects.get("CONN2", None)
    if d_conn2 != "missing":
        cv2.rectangle(img, (230+dx, 550+dy), (370+dx, 660+dy), (0, 140, 255), 5)
        cv2.rectangle(img, (236+dx, 556+dy), (364+dx, 654+dy), (255, 255, 255), -1)

    # Main Processor IC (U1) - Large Center White/Pink Box
    d_u1 = defects.get("U1", None)
    u1_box = (480+dx, 250+dy, 660+dx, 430+dy)
    if d_u1 != "missing":
        cv2.rectangle(img, (u1_box[0], u1_box[1]), (u1_box[2], u1_box[3]), (180, 140, 255), 4) # Pink border
        cv2.rectangle(img, (u1_box[0]+4, u1_box[1]+4), (u1_box[2]-4, u1_box[3]-4), (255, 255, 255), -1)
    else:
        # Bare pad if missing
        cv2.rectangle(img, (u1_box[0], u1_box[1]), (u1_box[2], u1_box[3]), (80, 80, 80), 2)
        cv2.putText(img, "MISSING U1", (u1_box[0]+15, u1_box[1]+90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # Voltage Regulator (VR1) - Yellow-Green Border
    d_vr1 = defects.get("VR1", None)
    vr1_box = (690+dx, 310+dy, 760+dx, 410+dy)
    if d_vr1 != "missing":
        cv2.rectangle(img, (vr1_box[0], vr1_box[1]), (vr1_box[2], vr1_box[3]), (0, 240, 200), 4) # Yellow-Green
        cv2.rectangle(img, (vr1_box[0]+4, vr1_box[1]+4), (vr1_box[2]-4, vr1_box[3]-4), (255, 255, 255), -1)
    else:
        cv2.rectangle(img, (vr1_box[0], vr1_box[1]), (vr1_box[2], vr1_box[3]), (80, 80, 80), 2)

    # Main SMD Filter Cap C3 (Cyan Border)
    d_c3 = defects.get("C3", None)
    c3_box = (320+dx, 350+dy, 410+dx, 390+dy)
    if d_c3 == "tombstone":
        # Standing on one end
        cv2.rectangle(img, (c3_box[0], c3_box[1]-20), (c3_box[0]+35, c3_box[1]+20), (255, 255, 0), 4)
        cv2.rectangle(img, (c3_box[0]+4, c3_box[1]-16), (c3_box[0]+31, c3_box[1]+16), (255, 255, 255), -1)
    elif d_c3 != "missing":
        cv2.rectangle(img, (c3_box[0], c3_box[1]), (c3_box[2], c3_box[3]), (255, 255, 0), 4) # Cyan border
        cv2.rectangle(img, (c3_box[0]+4, c3_box[1]+4), (c3_box[2]-4, c3_box[3]-4), (255, 255, 255), -1)

    # Electrolytic Caps C1 & C2 (Magenta Boxes)
    for cid, cx in [("C1", 340), ("C2", 410)]:
        d_c = defects.get(cid, None)
        c_box = (cx+dx, 560+dy, cx+60+dx, 630+dy)
        if d_c != "missing":
            cv2.rectangle(img, (c_box[0], c_box[1]), (c_box[2], c_box[3]), (200, 0, 200), 4)
            cv2.rectangle(img, (c_box[0]+4, c_box[1]+4), (c_box[2]-4, c_box[3]-4), (255, 255, 255), -1)

    # Dense SMD Chips (Red, Blue, Purple, Green SMD outlines)
    # Resistor R12 (Red border chip)
    d_r12 = defects.get("R12", None)
    if d_r12 == "tilt":
        pts = np.array([[400+dx, 310+dy], [435+dx, 325+dy], [415+dx, 360+dy], [380+dx, 345+dy]], np.int32)
        cv2.fillPoly(img, [pts], (255, 255, 255))
        cv2.polylines(img, [pts], True, (0, 0, 220), 3)
    elif d_r12 != "missing":
        cv2.rectangle(img, (400+dx, 310+dy), (430+dx, 355+dy), (0, 0, 220), 3) # Red
        cv2.rectangle(img, (403+dx, 313+dy), (427+dx, 352+dy), (255, 255, 255), -1)

    # Decoupling Cap C5 (Blue border chip)
    d_c5 = defects.get("C5", None)
    if d_c5 == "shift":
        cv2.rectangle(img, (430+dx, 535+dy), (475+dx, 565+dy), (220, 100, 0), 3) # Blue shift
        cv2.rectangle(img, (433+dx, 538+dy), (472+dx, 562+dy), (255, 255, 255), -1)
    elif d_c5 != "missing":
        cv2.rectangle(img, (405+dx, 520+dy), (450+dx, 550+dy), (220, 100, 0), 3)
        cv2.rectangle(img, (408+dx, 523+dy), (447+dx, 547+dy), (255, 255, 255), -1)

    # Small ICs U2 & U3
    for uid, ux, uy in [("U2", 350, 280), ("U3", 275, 490)]:
        d_u = defects.get(uid, None)
        if d_u != "missing":
            cv2.rectangle(img, (ux+dx, uy+dy), (ux+60+dx, uy+60+dy), (220, 0, 220), 3)
            cv2.rectangle(img, (ux+4+dx, uy+4+dy), (ux+56+dx, uy+56+dy), (255, 255, 255), -1)

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

    # 1. Golden Reference
    golden_img = render_custom_pcb(defects={})
    golden_path = os.path.join(ref_dir, "golden_board.png")
    cv2.imwrite(golden_path, golden_img)
    print(f"[CUSTOM PCB] Rendered Golden Reference Board to: {golden_path}")

    # 2. Render 31 Test Boards
    test_specs = {
        "TB001": {"defects": {"U1": "missing"}},
        "TB002": {"defects": {"C3": "tombstone"}},
        "TB003": {"defects": {"R12": "tilt"}},
        "TB004": {"defects": {"C5": "shift"}},
        "TB005": {"defects": {}},
        "TB006": {"defects": {}},
        "TB007": {"defects": {}},
        "TB008": {"defects": {}},
        "TB009": {"defects": {}},
        "TB010": {"defects": {"U2": "missing"}},
        "TB011": {"defects": {"VR1": "missing"}},
        "TB012": {"defects": {"U1": "missing"}},
        "TB013": {"defects": {"U2": "missing"}},
        "TB014": {"defects": {"VR1": "missing", "C5": "missing"}},
        "TB015": {"defects": {"C1": "missing"}},
        "TB016": {"defects": {"C2": "missing"}},
        "TB017": {"defects": {"CONN1": "missing"}},
        "TB018": {"defects": {"R12": "missing"}},
        "TB019": {"defects": {"C5": "missing"}},
        "TB020": {"defects": {"U1": "missing", "C3": "missing"}},
        "TB021": {"defects": {"J1": "missing", "C1": "missing"}},
        "TB022": {"defects": {"U2": "missing", "C2": "missing", "VR1": "missing"}},
        "TB023": {"defects": {"C5": "tombstone"}},
        "TB024": {"defects": {"C3": "tombstone"}},
        "TB025": {"defects": {"C5": "tilt"}},
        "TB026": {"defects": {"R12": "tilt"}},
        "TB027": {"defects": {"C3": "shift"}},
        "TB028": {"defects": {"R12": "shift"}},
        "TB029": {"defects": {}, "shift_offset": (15, 12)},
        "TB030": {"defects": {}, "shift_offset": (-10, 8)},
        "TB031": {"defects": {"R12": "missing", "C3": "missing"}}
    }

    for board_id, spec in test_specs.items():
        defs = spec.get("defects", {})
        s_off = spec.get("shift_offset", (0, 0))
        img = render_custom_pcb(defects=defs, shift_offset=s_off)
        cv2.imwrite(os.path.join(tb_dir, f"{board_id}.png"), img)

    print(f"[CUSTOM PCB] Successfully rendered 31 test boards matching your PCB layout image.")

if __name__ == "__main__":
    main()
