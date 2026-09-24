
import os
import cv2
import numpy as np
import math

def draw_realistic_board():
    W, H = 1280, 720
    img = np.zeros((H, W, 3), dtype=np.uint8)
    depth = np.zeros((H, W), dtype=np.float32)

    # 1. Base Dark Industrial Green Solder Mask
    # Realistic gradient & fiberglass texture
    y_coords, x_coords = np.indices((H, W))
    base_g = 70 + (30 * (1.0 - y_coords / H)).astype(np.uint8)
    base_b = 30 + (15 * (x_coords / W)).astype(np.uint8)
    base_r = 18 + (10 * (y_coords / H)).astype(np.uint8)
    img[:, :, 0] = base_b
    img[:, :, 1] = base_g
    img[:, :, 2] = base_r

    # Add subtle weave noise
    weave = ((x_coords % 4 == 0) | (y_coords % 4 == 0)).astype(np.uint8) * 8
    img = np.clip(img.astype(np.int16) + weave[:, :, None] - 4, 0, 255).astype(np.uint8)

    # Depth of substrate baseline (0.0 mm)
    depth[:] = 0.0

    # 2. Copper Traces & Power Planes (Gold / Copper tint)
    trace_color = (45, 140, 110) # Darker green over copper under solder mask
    gold_pad = (60, 180, 215) # Gold/tin ENIG finish
    solder_tin = (210, 215, 220) # Shiny SAC305 solder

    # Trace routing
    traces = [
        # Bus to U1
        [(220, 280), (480, 280)],
        [(220, 310), (350, 310)],
        [(410, 310), (480, 310)],
        [(380, 340), (480, 340)],
        # U1 to VR1
        [(660, 340), (690, 340)],
        [(660, 370), (690, 370)],
        # U1 to J1
        [(660, 260), (820, 260)],
        [(660, 290), (820, 290)],
        [(660, 320), (820, 320)],
        [(660, 380), (820, 380)],
        [(660, 410), (820, 410)],
        # U1 to U3 & Passives
        [(510, 430), (510, 520)],
        [(550, 430), (550, 560)],
        [(450, 520), (480, 430)],
        [(335, 490), (335, 430), (480, 370)],
        [(370, 560), (370, 520), (405, 520)]
    ]
    for pts in traces:
        for i in range(len(pts) - 1):
            cv2.line(img, pts[i], pts[i+1], trace_color, 4, cv2.LINE_AA)
            cv2.line(img, pts[i], pts[i+1], (60, 160, 130), 2, cv2.LINE_AA)

    # Ground Vias (Test points & stitching)
    vias = [
        (160, 160), (160, 400), (160, 600), (450, 160), (750, 160),
        (750, 600), (1050, 160), (1050, 350), (1050, 600), (450, 600)
    ]
    for vx, vy in vias:
        cv2.circle(img, (vx, vy), 8, gold_pad, -1, cv2.LINE_AA)
        cv2.circle(img, (vx, vy), 4, (20, 25, 25), -1, cv2.LINE_AA)
        cv2.putText(img, "GND", (vx - 10, vy + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.28, (220, 220, 220), 1, cv2.LINE_AA)

    # 3. Component Rendering

    # --- U1: Main MCU QFP-64 / FPGA Package [480, 250, 180, 180] ---
    u1_x, u1_y, u1_w, u1_h = 480, 250, 180, 180
    depth[u1_y:u1_y+u1_h, u1_x:u1_x+u1_w] = 1.4

    # Outer gull-wing pins (Top, Bottom, Left, Right)
    for p in range(16):
        px = u1_x + 15 + p * 10
        # Top pins
        cv2.rectangle(img, (px, u1_y - 14), (px + 5, u1_y), solder_tin, -1)
        cv2.rectangle(img, (px, u1_y - 18), (px + 5, u1_y - 14), gold_pad, -1)
        # Bottom pins
        cv2.rectangle(img, (px, u1_y + u1_h), (px + 5, u1_y + u1_h + 14), solder_tin, -1)
        cv2.rectangle(img, (px, u1_y + u1_h + 14), (px + 5, u1_y + u1_h + 18), gold_pad, -1)
        # Left pins
        py = u1_y + 15 + p * 10
        cv2.rectangle(img, (u1_x - 14, py), (u1_x, py + 5), solder_tin, -1)
        cv2.rectangle(img, (u1_x - 18, py), (u1_x - 14, py + 5), gold_pad, -1)
        # Right pins
        cv2.rectangle(img, (u1_x + u1_w, py), (u1_x + u1_w + 14, py + 5), solder_tin, -1)
        cv2.rectangle(img, (u1_x + u1_w + 14, py), (u1_x + u1_w + 18, py + 5), gold_pad, -1)

    # Chip Black Molded Body
    cv2.rectangle(img, (u1_x, u1_y), (u1_x + u1_w, u1_y + u1_h), (25, 25, 28), -1)
    cv2.rectangle(img, (u1_x + 2, u1_y + 2), (u1_x + u1_w - 2, u1_y + u1_h - 2), (38, 38, 42), -1)
    # Beveled edge
    cv2.rectangle(img, (u1_x + 10, u1_y + 10), (u1_x + u1_w - 10, u1_y + u1_h - 10), (30, 30, 34), -1)
    # Pin 1 Index Dot
    cv2.circle(img, (u1_x + 22, u1_y + 22), 6, (18, 18, 20), -1)
    cv2.circle(img, (u1_x + 22, u1_y + 22), 4, (12, 12, 14), -1)
    # Laser Markings
    cv2.putText(img, "ARM CORTEX-M4", (u1_x + 28, u1_y + 70), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 165), 1, cv2.LINE_AA)
    cv2.putText(img, "STM32F407VGT6", (u1_x + 25, u1_y + 95), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (190, 190, 195), 1, cv2.LINE_AA)
    cv2.putText(img, "9928A V6 CHN", (u1_x + 40, u1_y + 120), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (130, 130, 135), 1, cv2.LINE_AA)

    # --- VR1: Voltage Regulator SOT-223 [690, 310, 70, 100] ---
    vr_x, vr_y, vr_w, vr_h = 690, 310, 70, 100
    depth[vr_y:vr_y+vr_h, vr_x:vr_x+vr_w] = 1.6
    # Large thermal tab on right
    cv2.rectangle(img, (vr_x + vr_w - 5, vr_y + 15), (vr_x + vr_w + 14, vr_y + vr_h - 15), solder_tin, -1)
    # 3 leads on left
    for i in range(3):
        ly = vr_y + 18 + i * 28
        cv2.rectangle(img, (vr_x - 14, ly), (vr_x, ly + 10), solder_tin, -1)
    # Black body
    cv2.rectangle(img, (vr_x, vr_y), (vr_x + vr_w, vr_y + vr_h), (28, 28, 30), -1)
    cv2.rectangle(img, (vr_x + 4, vr_y + 4), (vr_x + vr_w - 4, vr_y + vr_h - 4), (36, 36, 40), -1)
    cv2.putText(img, "AMS1117", (vr_x + 8, vr_y + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (180, 180, 180), 1, cv2.LINE_AA)
    cv2.putText(img, "3.3V", (vr_x + 20, vr_y + 65), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (200, 200, 200), 1, cv2.LINE_AA)

    # --- CONN1: USB Type Connector [200, 230, 140, 100] ---
    c1_x, c1_y, c1_w, c1_h = 200, 230, 140, 100
    depth[c1_y:c1_y+c1_h, c1_x:c1_x+c1_w] = 3.8
    # Metal shield
    cv2.rectangle(img, (c1_x, c1_y), (c1_x + c1_w, c1_y + c1_h), (170, 175, 185), -1)
    cv2.rectangle(img, (c1_x + 4, c1_y + 4), (c1_x + c1_w - 4, c1_y + c1_h - 4), (195, 200, 210), -1)
    # 4 corner through-hole solder tabs
    for sx, sy in [(c1_x - 8, c1_y + 8), (c1_x - 8, c1_y + c1_h - 24), (c1_x + c1_w - 8, c1_y + 8), (c1_x + c1_w - 8, c1_y + c1_h - 24)]:
        cv2.rectangle(img, (sx, sy), (sx + 16, sy + 16), solder_tin, -1)
    # Connector Port Slot
    cv2.rectangle(img, (c1_x + 20, c1_y + 30), (c1_x + c1_w - 20, c1_y + c1_h - 30), (40, 42, 48), -1)
    cv2.putText(img, "USB PWR", (c1_x + 35, c1_y + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (230, 230, 230), 1, cv2.LINE_AA)

    # --- CONN2: DC Terminal Block [230, 550, 140, 110] ---
    c2_x, c2_y, c2_w, c2_h = 230, 550, 140, 110
    depth[c2_y:c2_y+c2_h, c2_x:c2_x+c2_w] = 4.5
    # Green housing
    cv2.rectangle(img, (c2_x, c2_y), (c2_x + c2_w, c2_y + c2_h), (35, 110, 60), -1)
    cv2.rectangle(img, (c2_x + 4, c2_y + 4), (c2_x + c2_w - 4, c2_y + c2_h - 4), (45, 135, 75), -1)
    # 2 Brass screw heads
    for sp in [c2_x + 35, c2_x + 105]:
        cv2.circle(img, (sp, c2_y + 45), 18, (80, 160, 210), -1)
        cv2.circle(img, (sp, c2_y + 45), 14, (60, 130, 180), -1)
        cv2.line(img, (sp - 10, c2_y + 45), (sp + 10, c2_y + 45), (30, 70, 100), 3)
    cv2.putText(img, "+  VIN  -", (c2_x + 32, c2_y + 90), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (240, 240, 240), 1, cv2.LINE_AA)

    # --- J1: Right 40-Pin Header Strip [820, 180, 40, 420] ---
    j1_x, j1_y, j1_w, j1_h = 820, 180, 40, 420
    depth[j1_y:j1_y+j1_h, j1_x:j1_x+j1_w] = 3.2
    # Black insulator base
    cv2.rectangle(img, (j1_x, j1_y), (j1_x + j1_w, j1_y + j1_h), (20, 20, 22), -1)
    # Gold square pins (2 rows of 20 pins)
    for p in range(20):
        py = j1_y + 12 + p * 20
        # Left column pin
        cv2.rectangle(img, (j1_x + 6, py), (j1_x + 14, py + 8), (70, 190, 235), -1)
        cv2.rectangle(img, (j1_x + 8, py + 2), (j1_x + 12, py + 6), (90, 210, 255), -1)
        # Right column pin
        cv2.rectangle(img, (j1_x + 24, py), (j1_x + 32, py + 8), (70, 190, 235), -1)
        cv2.rectangle(img, (j1_x + 26, py + 2), (j1_x + 30, py + 6), (90, 210, 255), -1)

    # --- U2: SOIC-8 Flash IC [350, 280, 60, 60] ---
    u2_x, u2_y, u2_w, u2_h = 350, 280, 60, 60
    depth[u2_y:u2_y+u2_h, u2_x:u2_x+u2_w] = 1.1
    for p in range(4):
        py = u2_y + 8 + p * 13
        cv2.rectangle(img, (u2_x - 8, py), (u2_x, py + 4), solder_tin, -1)
        cv2.rectangle(img, (u2_x + u2_w, py), (u2_x + u2_w + 8, py + 4), solder_tin, -1)
    cv2.rectangle(img, (u2_x, u2_y), (u2_x + u2_w, u2_y + u2_h), (30, 30, 32), -1)
    cv2.circle(img, (u2_x + 8, u2_y + 8), 3, (15, 15, 15), -1)
    cv2.putText(img, "25Q128", (u2_x + 6, u2_y + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (170, 170, 170), 1, cv2.LINE_AA)

    # --- U3: SOIC-8 Logic IC [275, 490, 60, 60] ---
    u3_x, u3_y, u3_w, u3_h = 275, 490, 60, 60
    depth[u3_y:u3_y+u3_h, u3_x:u3_x+u3_w] = 1.1
    for p in range(4):
        py = u3_y + 8 + p * 13
        cv2.rectangle(img, (u3_x - 8, py), (u3_x, py + 4), solder_tin, -1)
        cv2.rectangle(img, (u3_x + u3_w, py), (u3_x + u3_w + 8, py + 4), solder_tin, -1)
    cv2.rectangle(img, (u3_x, u3_y), (u3_x + u3_w, u3_y + u3_h), (30, 30, 32), -1)
    cv2.circle(img, (u3_x + 8, u3_y + 8), 3, (15, 15, 15), -1)
    cv2.putText(img, "74HC595", (u3_x + 4, u3_y + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.30, (170, 170, 170), 1, cv2.LINE_AA)

    # --- C1 & C2: Electrolytic Capacitors [340, 560, 60, 70] & [410, 560, 60, 70] ---
    for cx, lbl in [(340, "100uF"), (410, "100uF")]:
        depth[560:630, cx:cx+60] = 3.5
        # Can shadow
        cv2.circle(img, (cx + 30, 595), 26, (140, 145, 150), -1)
        cv2.circle(img, (cx + 30, 595), 24, (190, 195, 205), -1)
        # Negative polarity black crescent
        cv2.ellipse(img, (cx + 30, 595), (24, 24), 0, -45, 45, (30, 30, 35), -1)
        cv2.putText(img, "-", (cx + 42, 598), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    # --- C3: SMD Filter Cap [320, 350, 90, 40] ---
    depth[350:390, 320:410] = 0.8
    cv2.rectangle(img, (320, 350), (336, 390), solder_tin, -1)
    cv2.rectangle(img, (394, 350), (410, 390), solder_tin, -1)
    cv2.rectangle(img, (336, 350), (394, 390), (60, 95, 140), -1) # Brown ceramic body
    cv2.putText(img, "10uF", (348, 375), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (220, 220, 220), 1, cv2.LINE_AA)

    # --- R12: SMD Resistor 0805 [400, 310, 30, 45] ---
    depth[310:355, 400:430] = 0.6
    cv2.rectangle(img, (400, 310), (430, 318), solder_tin, -1)
    cv2.rectangle(img, (400, 347), (430, 355), solder_tin, -1)
    cv2.rectangle(img, (400, 318), (430, 347), (25, 25, 28), -1) # Black body
    cv2.putText(img, "103", (404, 336), cv2.FONT_HERSHEY_SIMPLEX, 0.30, (230, 230, 230), 1, cv2.LINE_AA)

    # --- C5: Decoupling Cap 0603 [405, 520, 45, 30] ---
    depth[520:550, 405:450] = 0.5
    cv2.rectangle(img, (405, 520), (413, 550), solder_tin, -1)
    cv2.rectangle(img, (442, 520), (450, 550), solder_tin, -1)
    cv2.rectangle(img, (413, 520), (442, 550), (70, 110, 155), -1) # Ceramic body

    # 4. White Silkscreen Layer (Legends & Identifiers)
    silk_color = (235, 235, 240)
    cv2.putText(img, "U1", (480, 242), cv2.FONT_HERSHEY_SIMPLEX, 0.45, silk_color, 1, cv2.LINE_AA)
    cv2.putText(img, "VR1", (690, 302), cv2.FONT_HERSHEY_SIMPLEX, 0.45, silk_color, 1, cv2.LINE_AA)
    cv2.putText(img, "CONN1", (200, 222), cv2.FONT_HERSHEY_SIMPLEX, 0.45, silk_color, 1, cv2.LINE_AA)
    cv2.putText(img, "CONN2", (230, 542), cv2.FONT_HERSHEY_SIMPLEX, 0.45, silk_color, 1, cv2.LINE_AA)
    cv2.putText(img, "J1", (820, 172), cv2.FONT_HERSHEY_SIMPLEX, 0.45, silk_color, 1, cv2.LINE_AA)
    cv2.putText(img, "U2", (350, 272), cv2.FONT_HERSHEY_SIMPLEX, 0.42, silk_color, 1, cv2.LINE_AA)
    cv2.putText(img, "U3", (275, 482), cv2.FONT_HERSHEY_SIMPLEX, 0.42, silk_color, 1, cv2.LINE_AA)
    cv2.putText(img, "C1", (340, 552), cv2.FONT_HERSHEY_SIMPLEX, 0.42, silk_color, 1, cv2.LINE_AA)
    cv2.putText(img, "C2", (410, 552), cv2.FONT_HERSHEY_SIMPLEX, 0.42, silk_color, 1, cv2.LINE_AA)
    cv2.putText(img, "C3", (320, 344), cv2.FONT_HERSHEY_SIMPLEX, 0.42, silk_color, 1, cv2.LINE_AA)
    cv2.putText(img, "R12", (400, 304), cv2.FONT_HERSHEY_SIMPLEX, 0.40, silk_color, 1, cv2.LINE_AA)
    cv2.putText(img, "C5", (405, 514), cv2.FONT_HERSHEY_SIMPLEX, 0.40, silk_color, 1, cv2.LINE_AA)

    # Board Branding Silkscreen
    cv2.putText(img, "PCB AI INSPECTION MASTER — REV 4.2 [IPC-A-610H CLASS 3]", (80, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.55, silk_color, 1, cv2.LINE_AA)
    cv2.putText(img, "HIGH SPEED DIFFERENTIAL BUS & SMT TEST MATRIX", (80, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (180, 180, 185), 1, cv2.LINE_AA)
    cv2.putText(img, "CE  RoHS  FC", (1100, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.45, silk_color, 1, cv2.LINE_AA)

    # Fiducials (+)
    for fx, fy in [(70, 70), (1210, 70), (70, 650), (1210, 650)]:
        cv2.circle(img, (fx, fy), 10, gold_pad, 2, cv2.LINE_AA)
        cv2.circle(img, (fx, fy), 4, gold_pad, -1, cv2.LINE_AA)

    return img, depth

# Generate and save Golden Master
golden_img, golden_depth = draw_realistic_board()
cv2.imwrite("server/reference/golden_board.png", golden_img)
np.save("server/reference/golden_depth.npy", golden_depth)
print("Saved photorealistic server/reference/golden_board.png and golden_depth.npy")

# Generate all 31 evaluation test boards from this photorealistic master!
eval_dir = "evaluation/test_boards"
os.makedirs(eval_dir, exist_ok=True)

# Defect Injector function
def inject_defect(tb_idx):
    tb = golden_img.copy()
    
    # TB001: Pass
    if tb_idx == 1:
        return tb
    # TB002: Missing R12
    elif tb_idx == 2:
        cv2.rectangle(tb, (400, 310), (430, 355), (30, 80, 45), -1) # Green substrate with bare gold pads
        cv2.rectangle(tb, (400, 310), (430, 318), (60, 180, 215), -1)
        cv2.rectangle(tb, (400, 347), (430, 355), (60, 180, 215), -1)
    # TB003: Missing C5
    elif tb_idx == 3:
        cv2.rectangle(tb, (405, 520), (450, 550), (30, 80, 45), -1)
        cv2.rectangle(tb, (405, 520), (413, 550), (60, 180, 215), -1)
        cv2.rectangle(tb, (442, 520), (450, 550), (60, 180, 215), -1)
    # TB004: Shifted U2 IC
    elif tb_idx == 4:
        cv2.rectangle(tb, (342, 272), (418, 348), (30, 80, 45), -1)
        u2_crop = golden_img[280:340, 350:410].copy()
        tb[295:355, 365:425] = u2_crop # Shifted by 15px
    # TB005: Tombstone C3 (45 deg tilt)
    elif tb_idx == 5:
        cv2.rectangle(tb, (320, 350), (410, 390), (30, 80, 45), -1)
        # Left pad soldered, right side standing up casting shadow
        cv2.rectangle(tb, (320, 350), (336, 390), (210, 215, 220), -1)
        cv2.rectangle(tb, (336, 335), (370, 375), (50, 85, 125), -1)
        cv2.rectangle(tb, (370, 335), (380, 375), (180, 185, 190), -1)
        cv2.rectangle(tb, (340, 375), (395, 395), (15, 40, 20), -1) # Shadow
    # TB006: Solder bridge on U1
    elif tb_idx == 6:
        # Solder bridge between top pins 4 and 5
        cv2.rectangle(tb, (510, 236), (532, 252), (210, 215, 220), -1)
    # Other TBs: Realistic subtle optical/alignment variations
    else:
        # Subtle realistic lighting variation
        noise = np.random.normal(0, 1.5, tb.shape).astype(np.int16)
        tb = np.clip(tb.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    return tb

for i in range(1, 32):
    tb_img = inject_defect(i)
    tb_name = f"TB{i:03d}.png"
    cv2.imwrite(os.path.join(eval_dir, tb_name), tb_img)

print("Generated 31 photorealistic test boards in evaluation/test_boards/")
