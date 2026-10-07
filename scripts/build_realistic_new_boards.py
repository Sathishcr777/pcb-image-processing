"""
Realistic New PCB Test Board Generator (TB033 - TB040)
Generates additive realistic inspection samples for evaluation/test_boards/
and corresponding 4-mode X-Ray radiographs in server/static/boards/.
"""

import os
import sys
import json
import math
import cv2
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

EVAL_DIR = os.path.join(ROOT, "evaluation", "test_boards")
STATIC_BOARDS_DIR = os.path.join(ROOT, "server", "static", "boards")
REF_DIR = os.path.join(ROOT, "server", "reference")
CONFIG_PATH = os.path.join(ROOT, "server", "config", "components.json")

os.makedirs(EVAL_DIR, exist_ok=True)
os.makedirs(STATIC_BOARDS_DIR, exist_ok=True)

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    components = json.load(f)

comp_map = {c["id"]: c for c in components}

golden_img = cv2.imread(os.path.join(EVAL_DIR, "TB005.png"))
if golden_img is None:
    golden_img = cv2.imread(os.path.join(REF_DIR, "golden_board.png"))
if golden_img is None:
    raise RuntimeError("Could not load golden reference board")

H, W, _ = golden_img.shape
sub_bg = golden_img[200:400, 200:400].copy()

def get_bare_footprint(comp):
    cid = comp["id"]
    x, y, w, h = comp["bbox_xywh"]
    
    h_tiles = (h // 200) + 1
    w_tiles = (w // 200) + 1
    tiled = np.tile(sub_bg, (h_tiles, w_tiles, 1))[:h, :w].copy()
    tiled = (tiled.astype(np.float32) * 0.95).astype(np.uint8)
    
    pad_col = (195, 205, 215)
    
    if "U" in cid:
        pad_margin_x = int(w * 0.25)
        pad_margin_y = int(h * 0.25)
        cv2.rectangle(tiled, (pad_margin_x, pad_margin_y), (w - pad_margin_x, h - pad_margin_y), (140, 160, 175), -1)
        cv2.rectangle(tiled, (pad_margin_x, pad_margin_y), (w - pad_margin_x, h - pad_margin_y), (180, 190, 200), 2)
        
        step_x = max(8, w // 12)
        for px in range(8, w - 8, step_x):
            cv2.rectangle(tiled, (px, 2), (px + step_x - 3, 16), pad_col, -1)
            cv2.rectangle(tiled, (px, h - 16), (px + step_x - 3, h - 2), pad_col, -1)
        step_y = max(8, h // 10)
        for py in range(8, h - 8, step_y):
            cv2.rectangle(tiled, (2, py), (16, py + step_y - 3), pad_col, -1)
            cv2.rectangle(tiled, (w - 16, py), (w - 2, py + step_y - 3), pad_col, -1)
            
    elif "J_" in cid:
        step_x = max(10, w // 18)
        for px in range(6, w - 6, step_x):
            cv2.rectangle(tiled, (px, 4), (px + step_x - 4, h // 2 - 4), pad_col, -1)
            cv2.rectangle(tiled, (px, h // 2 + 4), (px + step_x - 4, h - 4), pad_col, -1)
            
    elif "BANK" in cid:
        step_y = max(14, h // 8)
        for py in range(8, h - 8, step_y):
            cv2.rectangle(tiled, (6, py), (w // 2 - 8, py + step_y - 4), pad_col, -1)
            cv2.rectangle(tiled, (w // 2 + 8, py), (w - 6, py + step_y - 4), pad_col, -1)
            
    elif "C_" in cid:
        step_y = max(18, h // 6)
        for py in range(8, h - 8, step_y):
            cv2.rectangle(tiled, (6, py), (w // 2 - 6, py + step_y - 6), pad_col, -1)
            cv2.rectangle(tiled, (w // 2 + 6, py), (w - 6, py + step_y - 6), pad_col, -1)
            
    return tiled

def generate_radiographs(board_img, board_id):
    gray = cv2.cvtColor(board_img, cv2.COLOR_BGR2GRAY)
    inv = 255 - gray
    filtered = cv2.bilateralFilter(inv, 7, 50, 50)
    clahe_fine = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    clahe_broad = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(16, 16))
    c_fine = clahe_fine.apply(filtered)
    c_broad = clahe_broad.apply(filtered)
    combined_clahe = cv2.addWeighted(c_fine, 0.65, c_broad, 0.35, 0)
    blur = cv2.GaussianBlur(combined_clahe, (0, 0), 1.2)
    sharp = cv2.addWeighted(combined_clahe, 1.5, blur, -0.5, 0)
    norm_radiograph = cv2.normalize(np.clip(sharp, 0, 255).astype(np.uint8), None, 0, 255, cv2.NORM_MINMAX)

    bone_img = cv2.cvtColor(norm_radiograph, cv2.COLOR_GRAY2BGR)
    inferno_img = cv2.applyColorMap(norm_radiograph, cv2.COLORMAP_INFERNO)
    gray_img = cv2.cvtColor(norm_radiograph, cv2.COLOR_GRAY2BGR)

    blue_lut = np.zeros((256, 1, 3), dtype=np.uint8)
    for i in range(256):
        t = i / 255.0
        if t < 0.35:
            s = t / 0.35
            b = int(10 + s * 170)
            g = int(5 + s * 45)
            r = int(2 + s * 8)
        elif t < 0.75:
            s = (t - 0.35) / 0.40
            b = int(180 + s * 75)
            g = int(50 + s * 150)
            r = int(10 + s * 30)
        else:
            s = (t - 0.75) / 0.25
            b = 255
            g = int(200 + s * 55)
            r = int(40 + s * 190)
        blue_lut[i, 0] = [b, g, r]
    jet_img = cv2.LUT(bone_img, blue_lut)

    cv2.imwrite(os.path.join(STATIC_BOARDS_DIR, f"{board_id}_xray_bone.png"), bone_img)
    cv2.imwrite(os.path.join(STATIC_BOARDS_DIR, f"{board_id}_xray_gray.png"), gray_img)
    cv2.imwrite(os.path.join(STATIC_BOARDS_DIR, f"{board_id}_xray_inferno.png"), inferno_img)
    cv2.imwrite(os.path.join(STATIC_BOARDS_DIR, f"{board_id}_xray_jet.png"), jet_img)

def build_new_boards():
    boards = {}

    # 1. TB033: Good / Conforming Production Board (PASS)
    # Pristine conforming production board with minute sensor noise
    img33 = golden_img.copy()
    noise = np.random.normal(0, 0.25, (H, W, 3)).astype(np.int16)
    img33 = np.clip(img33.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    boards["TB033"] = img33

    # 2. TB034: Component Rotational Misalignment / Skew (REWORK)
    # U4 (Bottom-Right QFP MCU) tilted 16.5 degrees
    img34 = golden_img.copy()
    comp_u4 = comp_map["U4"]
    x, y, w, h = comp_u4["bbox_xywh"]
    roi_u4 = golden_img[y:y+h, x:x+w].copy()
    bare_u4 = get_bare_footprint(comp_u4)
    img34[y:y+h, x:x+w] = bare_u4
    center = (w // 2, h // 2)
    rot_mat = cv2.getRotationMatrix2D(center, 16.5, 1.0)
    rotated_u4 = cv2.warpAffine(roi_u4, rot_mat, (w, h), borderMode=cv2.BORDER_REFLECT)
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.rectangle(mask, (6, 6), (w - 6, h - 6), 255, -1)
    rot_mask = cv2.warpAffine(mask, rot_mat, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    fg = cv2.bitwise_and(rotated_u4, rotated_u4, mask=rot_mask)
    bg = cv2.bitwise_and(bare_u4, bare_u4, mask=cv2.bitwise_not(rot_mask))
    img34[y:y+h, x:x+w] = cv2.add(fg, bg)
    boards["TB034"] = img34

    # 3. TB035: Missing Component (FAIL / REWORK)
    # U3 (Mid-Lower QFP Controller) unpopulated / missing
    img35 = golden_img.copy()
    comp_u3 = comp_map["U3"]
    x, y, w, h = comp_u3["bbox_xywh"]
    img35[y:y+h, x:x+w] = get_bare_footprint(comp_u3)
    boards["TB035"] = img35

    # 4. TB036: Solder Bridge / Lead Short (FAIL / REWORK)
    # U2 (Mid-Upper QFP Controller) has major tin bridging shorting pins and leads
    img36 = golden_img.copy()
    comp_u2 = comp_map["U2"]
    x, y, w, h = comp_u2["bbox_xywh"]
    roi_u2 = golden_img[y:y+h, x:x+w].copy()
    bare_u2 = get_bare_footprint(comp_u2)
    # Shift slightly by 8px and add wide solder bridge pools
    shift_mat = np.float32([[1, 0, -8], [0, 1, 4]])
    shifted_u2 = cv2.warpAffine(roi_u2, shift_mat, (w, h), borderMode=cv2.BORDER_REFLECT)
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.rectangle(mask, (4, 4), (w - 4, h - 4), 255, -1)
    shifted_mask = cv2.warpAffine(mask, shift_mat, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    fg = cv2.bitwise_and(shifted_u2, shifted_u2, mask=shifted_mask)
    bg = cv2.bitwise_and(bare_u2, bare_u2, mask=cv2.bitwise_not(shifted_mask))
    img36[y:y+h, x:x+w] = cv2.add(fg, bg)
    # Draw conspicuous solder bridge pool
    cv2.rectangle(img36, (x - 6, y + 20), (x + 35, y + 80), (210, 220, 230), -1)
    cv2.rectangle(img36, (x - 4, y + 22), (x + 33, y + 78), (240, 245, 250), -1)
    cv2.rectangle(img36, (x - 6, y + 20), (x + 35, y + 80), (140, 150, 160), 2)
    boards["TB036"] = img36

    # 5. TB037: Open Circuit / Broken Trace (FAIL / REWORK)
    # J_TOP header has open contact / unpopulated pins on right half
    img37 = golden_img.copy()
    comp_jtop = comp_map["J_TOP"]
    x, y, w, h = comp_jtop["bbox_xywh"]
    bare_jtop = get_bare_footprint(comp_jtop)
    # Replace right half with bare pad and severed circuit traces
    half_x = w // 2
    img37[y:y+h, x+half_x:x+w] = bare_jtop[:, half_x:]
    # Draw scratch / open trace cut
    cv2.line(img37, (x + half_x - 5, y), (x + half_x - 5, y + h), (15, 25, 20), 4)
    boards["TB037"] = img37

    # 6. TB038: Complex Multi-Defect Assembly (FAIL)
    # U5 (Center QFN) shifted + C_R1 (Right Edge Upper Cap) tombstoned
    img38 = golden_img.copy()
    # U5 shift
    comp_u5 = comp_map["U5"]
    x, y, w, h = comp_u5["bbox_xywh"]
    roi_u5 = golden_img[y:y+h, x:x+w].copy()
    bare_u5 = get_bare_footprint(comp_u5)
    img38[y:y+h, x:x+w] = bare_u5
    shift_mat = np.float32([[1, 0, 22], [0, 1, 10]])
    shifted_u5 = cv2.warpAffine(roi_u5, shift_mat, (w, h), borderMode=cv2.BORDER_REFLECT)
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.rectangle(mask, (4, 4), (w - 4, h - 4), 255, -1)
    shifted_mask = cv2.warpAffine(mask, shift_mat, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    fg = cv2.bitwise_and(shifted_u5, shifted_u5, mask=shifted_mask)
    bg = cv2.bitwise_and(bare_u5, bare_u5, mask=cv2.bitwise_not(shifted_mask))
    img38[y:y+h, x:x+w] = cv2.add(fg, bg)
    
    # C_R1 tombstone
    comp_cr1 = comp_map["C_R1"]
    x2, y2, w2, h2 = comp_cr1["bbox_xywh"]
    bare_cr1 = get_bare_footprint(comp_cr1)
    roi_cr1 = golden_img[y2:y2+h2, x2:x2+w2].copy()
    img38[y2:y2+h2, x2:x2+w2] = bare_cr1
    half_w = w2 // 2
    tomb_roi = roi_cr1[:, :half_w].copy()
    tomb_roi = np.clip(tomb_roi.astype(np.float32) * 1.4 + 35, 0, 255).astype(np.uint8)
    img38[y2:y2+h2, x2:x2+half_w] = tomb_roi
    boards["TB038"] = img38

    # 7. TB039: PCB Substrate Scratch & Trace Gouge (REVIEW / FAIL)
    # Severe mechanical gouge scraping off lower section of BANK_L1 passives
    img39 = golden_img.copy()
    comp_bank1 = comp_map["BANK_L1"]
    x, y, w, h = comp_bank1["bbox_xywh"]
    bare_bank1 = get_bare_footprint(comp_bank1)
    # Bare pad on lower third of passive matrix
    img39[y+h*2//3:y+h, x:x+w] = bare_bank1[h*2//3:, :]
    # Jagged gouge mark across BANK_L1
    pts = np.array([
        [x + 10, y + 25],
        [x + 60, y + 100],
        [x + 110, y + 180],
        [x + 150, y + 250],
        [x + 180, y + 310]
    ], np.int32)
    cv2.polylines(img39, [pts], False, (15, 25, 20), 9, cv2.LINE_AA)
    cv2.polylines(img39, [pts], False, (40, 145, 225), 5, cv2.LINE_AA)
    cv2.polylines(img39, [pts], False, (220, 230, 240), 2, cv2.LINE_AA)
    boards["TB039"] = img39

    # 8. TB040: Localized Thermal Power Stage Burn (FAIL / SCRAP)
    # Carbonized FR-4 charring crater consuming J_BOT2
    img40 = golden_img.copy()
    comp_jbot2 = comp_map["J_BOT2"]
    x, y, w, h = comp_jbot2["bbox_xywh"]
    bare_jbot2 = get_bare_footprint(comp_jbot2)
    img40[y:y+h, x:x+w] = bare_jbot2
    cx, cy = x + w // 2, y + h // 2
    cv2.circle(img40, (cx, cy), 110, (20, 30, 25), -1)
    cv2.circle(img40, (cx, cy), 85, (10, 15, 12), -1)
    cv2.circle(img40, (cx, cy), 55, (5, 5, 5), -1)
    cv2.circle(img40, (cx, cy), 125, (30, 60, 50), 4, cv2.LINE_AA)
    boards["TB040"] = img40

    # Save images and generate radiographs
    for b_id, b_img in boards.items():
        out_path = os.path.join(EVAL_DIR, f"{b_id}.png")
        cv2.imwrite(out_path, b_img)
        generate_radiographs(b_img, b_id)
        print(f"[OK] Saved {b_id}.png and radiographs")

if __name__ == "__main__":
    build_new_boards()
