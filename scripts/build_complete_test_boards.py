"""
Complete PCB Test Suite & Radiograph Generator
Team 4 - Ground Truth & Synthetic Data Engineering

Generates all 31 test boards (TB001-TB031) in evaluation/test_boards/
matching evaluation/test_labels.csv with exact physical component footprints.
Also generates all 4-mode X-Ray radiographs in server/static/boards/.
"""

import os
import sys
import json
import math
import shutil
import cv2
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
EVAL_DIR = os.path.join(ROOT, "evaluation", "test_boards")
STATIC_BOARDS_DIR = os.path.join(ROOT, "server", "static", "boards")
REF_DIR = os.path.join(ROOT, "server", "reference")
CONFIG_PATH = os.path.join(ROOT, "server", "config", "components.json")
LABELS_PATH = os.path.join(ROOT, "evaluation", "test_labels.csv")

os.makedirs(EVAL_DIR, exist_ok=True)
os.makedirs(STATIC_BOARDS_DIR, exist_ok=True)
os.makedirs(REF_DIR, exist_ok=True)

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    components = json.load(f)

comp_map = {c["id"]: c for c in components}

# Load the pristine golden board (TB005)
golden_img = cv2.imread(os.path.join(EVAL_DIR, "TB005.png"))
if golden_img is None:
    raise RuntimeError("Could not load TB005.png")

H, W, _ = golden_img.shape

# Substrate background sample for bare pads
sub_bg = golden_img[200:400, 200:400].copy()

def get_bare_footprint(comp):
    cid = comp["id"]
    x, y, w, h = comp["bbox_xywh"]
    
    h_tiles = (h // 200) + 1
    w_tiles = (w // 200) + 1
    tiled = np.tile(sub_bg, (h_tiles, w_tiles, 1))[:h, :w].copy()
    
    # Substrate color
    tiled = (tiled.astype(np.float32) * 0.95).astype(np.uint8)
    
    # Add silkscreen outline & solder pads according to type
    pad_col = (195, 205, 215) # Silver SAC305 solder
    
    if "U" in cid: # IC package bare pad
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
            
    elif "J_" in cid: # Header bare pad
        step_x = max(10, w // 18)
        for px in range(6, w - 6, step_x):
            cv2.rectangle(tiled, (px, 4), (px + step_x - 4, h // 2 - 4), pad_col, -1)
            cv2.rectangle(tiled, (px, h // 2 + 4), (px + step_x - 4, h - 4), pad_col, -1)
            
    elif "BANK" in cid: # Passives bank
        step_y = max(14, h // 8)
        for py in range(8, h - 8, step_y):
            cv2.rectangle(tiled, (6, py), (w // 2 - 8, py + step_y - 4), pad_col, -1)
            cv2.rectangle(tiled, (w // 2 + 8, py), (w - 6, py + step_y - 4), pad_col, -1)
            
    elif "C_" in cid: # Cap bank
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

def render_board(board_id, defect_specs):
    img = golden_img.copy()
    
    for spec in defect_specs:
        cid = spec["cid"]
        dtype = spec["type"]
        meas = spec.get("meas", "")
        
        if cid == "NONE" or dtype == "none":
            if "framing_drift" in meas:
                # e.g. dx8_dy6 or dx-6_dy5
                dx, dy = 0, 0
                if "dx8_dy6" in meas: dx, dy = 8, 6
                elif "dx-6_dy5" in meas: dx, dy = -6, 5
                
                M = np.float32([[1, 0, dx], [0, 1, dy]])
                img = cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        if dtype == "severe_thermal_burn":
            burn_src = os.path.join(STATIC_BOARDS_DIR, "burned_defect_board.png")
            if os.path.exists(burn_src):
                burn = cv2.imread(burn_src)
                if burn is not None:
                    bh, bw = burn.shape[:2]
                    cy, cx = int(bh * 0.42), int(bw * 0.52)
                    crop_size = 360
                    y1 = max(0, cy - crop_size // 2)
                    y2 = min(bh, cy + crop_size // 2)
                    x1 = max(0, cx - crop_size // 2)
                    x2 = min(bw, cx + crop_size // 2)
                    burn_roi = cv2.resize(burn[y1:y2, x1:x2], (crop_size, crop_size))

                    mask = np.zeros((crop_size, crop_size), dtype=np.float32)
                    cv2.circle(mask, (crop_size//2, crop_size//2), crop_size//2 - 15, 1.0, -1)
                    mask = cv2.GaussianBlur(mask, (31, 31), 11)

                    target_y = H // 2 - crop_size // 2
                    target_x = W // 2 - crop_size // 2

                    bg_roi = img[target_y:target_y+crop_size, target_x:target_x+crop_size].astype(np.float32)
                    fg_roi = burn_roi.astype(np.float32)

                    mask_3c = np.dstack([mask]*3)
                    img[target_y:target_y+crop_size, target_x:target_x+crop_size] = (fg_roi * mask_3c + bg_roi * (1.0 - mask_3c)).astype(np.uint8)
                    continue
            cv2.circle(img, (W//2, H//2), 140, (18, 18, 18), -1)
            cv2.circle(img, (W//2, H//2), 70, (5, 5, 5), -1)
            continue

        if cid not in comp_map:
            continue
            
        comp = comp_map[cid]
        x, y, w, h = comp["bbox_xywh"]
        roi_original = golden_img[y:y+h, x:x+w].copy()
        bare_pad = get_bare_footprint(comp)
        
        if dtype == "missing":
            img[y:y+h, x:x+w] = bare_pad
            
        elif dtype == "tilt":
            # Extract tilt angle
            angle = 18.0
            if "angle=" in meas:
                try: angle = float(meas.split("angle=")[1].replace("deg", "").strip())
                except Exception: angle = 18.0
                
            img[y:y+h, x:x+w] = bare_pad
            center = (w // 2, h // 2)
            rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated_roi = cv2.warpAffine(roi_original, rot_mat, (w, h), borderMode=cv2.BORDER_REFLECT)
            
            # Mask component from bare pad
            mask = np.zeros((h, w), dtype=np.uint8)
            cv2.rectangle(mask, (6, 6), (w - 6, h - 6), 255, -1)
            rot_mask = cv2.warpAffine(mask, rot_mat, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            
            fg = cv2.bitwise_and(rotated_roi, rotated_roi, mask=rot_mask)
            bg = cv2.bitwise_and(bare_pad, bare_pad, mask=cv2.bitwise_not(rot_mask))
            img[y:y+h, x:x+w] = cv2.add(fg, bg)
            
        elif dtype == "shift":
            shift_px = 24
            img[y:y+h, x:x+w] = bare_pad
            
            shift_mat = np.float32([[1, 0, shift_px], [0, 1, shift_px // 2]])
            shifted_roi = cv2.warpAffine(roi_original, shift_mat, (w, h), borderMode=cv2.BORDER_REFLECT)
            
            mask = np.zeros((h, w), dtype=np.uint8)
            cv2.rectangle(mask, (6, 6), (w - 6, h - 6), 255, -1)
            shifted_mask = cv2.warpAffine(mask, shift_mat, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            
            fg = cv2.bitwise_and(shifted_roi, shifted_roi, mask=shifted_mask)
            bg = cv2.bitwise_and(bare_pad, bare_pad, mask=cv2.bitwise_not(shifted_mask))
            img[y:y+h, x:x+w] = cv2.add(fg, bg)
            
        elif dtype == "tombstone":
            # Tombstone: half bare pad, half lifted component with bright yellow-white edge
            img[y:y+h, x:x+w] = bare_pad
            half_w = w // 2
            tomb_roi = roi_original[:, :half_w].copy()
            # brighten the lifted edge
            tomb_roi = np.clip(tomb_roi.astype(np.float32) * 1.35 + 30, 0, 255).astype(np.uint8)
            img[y:y+h, x:x+half_w] = tomb_roi

    # Add subtle sensor noise for realism
    noise = np.random.normal(0, 0.4, (H, W, 3)).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return img

def main():
    print(f"[BUILD] Generating all 31 test boards from ground truth {LABELS_PATH}...")
    df = pd.read_csv(LABELS_PATH)
    
    # Save golden master to server/reference/
    cv2.imwrite(os.path.join(REF_DIR, "golden_board.png"), golden_img)
    from server.pipeline.detector_depth import DetectorDepth
    ddepth = DetectorDepth(use_model=False)
    golden_depth = ddepth.estimate_depth(golden_img)
    np.save(os.path.join(REF_DIR, "golden_depth.npy"), golden_depth)
    print(f"[SUCCESS] Saved golden_board.png and golden_depth.npy in {REF_DIR}")
    
    for b_id, grp in df.groupby("board_id"):
        def_specs = []
        for _, row in grp.iterrows():
            def_specs.append({
                "cid": str(row["component_id"]).strip(),
                "type": str(row["defect_type"]).strip().lower(),
                "meas": str(row.get("physical_measurement", "")).strip()
            })
            
        board_img = render_board(b_id, def_specs)
        out_path = os.path.join(EVAL_DIR, f"{b_id}.png")
        cv2.imwrite(out_path, board_img)
        generate_radiographs(board_img, b_id)
        
    # Also generate radiographs for ai_hd_xray if exists
    hd_path = os.path.join(EVAL_DIR, "ai_hd_xray.png")
    if os.path.exists(hd_path):
        hd_img = cv2.imread(hd_path)
        generate_radiographs(hd_img, "ai_hd_xray")
        
    print(f"[SUCCESS] All 31 test boards generated in {EVAL_DIR}")
    print(f"[SUCCESS] All radiographs generated in {STATIC_BOARDS_DIR}")

if __name__ == "__main__":
    main()
