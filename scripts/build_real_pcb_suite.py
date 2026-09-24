import os
import cv2
import numpy as np

def create_real_pcb_master():
    W, H = 1280, 720
    
    # Base photographic board substrate from real circuit13_raw
    c13 = cv2.imread('server/reference/circuit13_raw.jpg')
    rpi = cv2.imread('server/reference/rpi4_raw.jpg')
    ssd = cv2.imread('server/reference/ssd_raw.jpg')
    
    ch, cw, _ = c13.shape
    target_ratio = 16.0 / 9.0
    cw_crop = int(ch * target_ratio)
    cx_start = (cw - cw_crop) // 2
    board_base = c13[:, cx_start:cx_start+cw_crop]
    board_master = cv2.resize(board_base, (W, H), interpolation=cv2.INTER_LANCZOS4)
    
    depth = np.zeros((H, W), dtype=np.float32)
    
    # 1. Main MCU IC (U1): Broadcom SoC from RPi [480, 250, 180, 180]
    u1_crop = cv2.resize(rpi[1050:1750, 1300:2000], (180, 180), interpolation=cv2.INTER_LANCZOS4)
    board_master[250:430, 480:660] = u1_crop
    depth[250:430, 480:660] = 1.45
    
    # 2. Voltage Regulator (VR1) [690, 310, 70, 100]
    vr_crop = cv2.resize(c13[400:600, 700:850], (70, 100), interpolation=cv2.INTER_LANCZOS4)
    board_master[310:410, 690:760] = vr_crop
    depth[310:410, 690:760] = 1.60
    
    # 3. USB Connector (CONN1) [200, 230, 140, 100]
    conn1_crop = cv2.resize(rpi[2000:2600, 600:1300], (140, 100), interpolation=cv2.INTER_LANCZOS4)
    board_master[230:330, 200:340] = conn1_crop
    depth[230:330, 200:340] = 3.50
    
    # 4. DC Terminal / Power Connector (CONN2) [230, 550, 140, 110]
    conn2_crop = cv2.resize(c13[1800:2300, 200:800], (140, 110), interpolation=cv2.INTER_LANCZOS4)
    board_master[550:660, 230:370] = conn2_crop
    depth[550:660, 230:370] = 4.20
    
    # 5. Right 40-Pin Header Strip (J1) [820, 180, 40, 420]
    j1_crop = cv2.resize(rpi[100:600, 900:3100], (420, 40), interpolation=cv2.INTER_LANCZOS4)
    j1_crop_v = cv2.rotate(j1_crop, cv2.ROTATE_90_CLOCKWISE)
    board_master[180:600, 820:860] = j1_crop_v
    depth[180:600, 820:860] = 3.20
    
    # 6. Flash IC (U2) [350, 280, 60, 60] & Logic IC (U3) [275, 490, 60, 60]
    soic_crop = cv2.resize(ssd[1200:1500, 1800:2100], (60, 60), interpolation=cv2.INTER_LANCZOS4)
    board_master[280:340, 350:410] = soic_crop
    depth[280:340, 350:410] = 1.10
    
    logic_crop = cv2.resize(c13[1200:1500, 2800:3100], (60, 60), interpolation=cv2.INTER_LANCZOS4)
    board_master[490:550, 275:335] = logic_crop
    depth[490:550, 275:335] = 1.10
    
    # 7. Electrolytic Capacitors (C1, C2) [340, 560, 60, 70] & [410, 560, 60, 70]
    cap_crop = cv2.resize(c13[100:350, 200:450], (60, 70), interpolation=cv2.INTER_LANCZOS4)
    board_master[560:630, 340:400] = cap_crop
    depth[560:630, 340:400] = 3.80
    
    cap2_crop = cv2.resize(c13[100:350, 450:700], (60, 70), interpolation=cv2.INTER_LANCZOS4)
    board_master[560:630, 410:470] = cap2_crop
    depth[560:630, 410:470] = 3.80
    
    # 8. Ceramic SMD Capacitor (C3) [320, 350, 90, 40]
    c3_crop = cv2.resize(rpi[1700:1820, 2400:2700], (90, 40), interpolation=cv2.INTER_LANCZOS4)
    board_master[350:390, 320:410] = c3_crop
    depth[350:390, 320:410] = 0.85
    
    # 9. SMD Resistor (R12) [400, 310, 30, 45]
    r12_crop = cv2.resize(rpi[1900:2050, 2200:2300], (30, 45), interpolation=cv2.INTER_LANCZOS4)
    board_master[310:355, 400:430] = r12_crop
    depth[310:355, 400:430] = 0.65
    
    # 10. Decoupling Cap (C5) [405, 520, 45, 30]
    c5_crop = cv2.resize(rpi[1800:1900, 2100:2250], (45, 30), interpolation=cv2.INTER_LANCZOS4)
    board_master[520:550, 405:450] = c5_crop
    depth[520:550, 405:450] = 0.55
    
    silk_color = (220, 225, 230)
    cv2.putText(board_master, 'U1', (480, 242), cv2.FONT_HERSHEY_SIMPLEX, 0.45, silk_color, 1, cv2.LINE_AA)
    cv2.putText(board_master, 'VR1', (690, 302), cv2.FONT_HERSHEY_SIMPLEX, 0.45, silk_color, 1, cv2.LINE_AA)
    cv2.putText(board_master, 'CONN1', (200, 222), cv2.FONT_HERSHEY_SIMPLEX, 0.45, silk_color, 1, cv2.LINE_AA)
    cv2.putText(board_master, 'CONN2', (230, 542), cv2.FONT_HERSHEY_SIMPLEX, 0.45, silk_color, 1, cv2.LINE_AA)
    cv2.putText(board_master, 'J1', (820, 172), cv2.FONT_HERSHEY_SIMPLEX, 0.45, silk_color, 1, cv2.LINE_AA)
    cv2.putText(board_master, 'U2', (350, 272), cv2.FONT_HERSHEY_SIMPLEX, 0.42, silk_color, 1, cv2.LINE_AA)
    cv2.putText(board_master, 'U3', (275, 482), cv2.FONT_HERSHEY_SIMPLEX, 0.42, silk_color, 1, cv2.LINE_AA)
    cv2.putText(board_master, 'C1', (340, 552), cv2.FONT_HERSHEY_SIMPLEX, 0.42, silk_color, 1, cv2.LINE_AA)
    cv2.putText(board_master, 'C2', (410, 552), cv2.FONT_HERSHEY_SIMPLEX, 0.42, silk_color, 1, cv2.LINE_AA)
    cv2.putText(board_master, 'C3', (320, 344), cv2.FONT_HERSHEY_SIMPLEX, 0.42, silk_color, 1, cv2.LINE_AA)
    cv2.putText(board_master, 'R12', (400, 304), cv2.FONT_HERSHEY_SIMPLEX, 0.40, silk_color, 1, cv2.LINE_AA)
    cv2.putText(board_master, 'C5', (405, 514), cv2.FONT_HERSHEY_SIMPLEX, 0.40, silk_color, 1, cv2.LINE_AA)
    
    cv2.putText(board_master, 'SMT INDUSTRIAL PRODUCTION MASTER — IPC-A-610H CLASS 3', (60, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, silk_color, 1, cv2.LINE_AA)
    cv2.putText(board_master, 'CE  RoHS  FC', (1120, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.48, silk_color, 1, cv2.LINE_AA)
    
    gold = (70, 190, 230)
    for fx, fy in [(60, 80), (1220, 80), (60, 660), (1220, 660)]:
        cv2.circle(board_master, (fx, fy), 9, gold, 2, cv2.LINE_AA)
        cv2.circle(board_master, (fx, fy), 3, gold, -1, cv2.LINE_AA)
        
    depth_smooth = cv2.bilateralFilter(depth, 7, 50, 50)
    return board_master, depth_smooth

def inject_board_defects(golden_master, golden_depth):
    eval_dir = 'evaluation/test_boards'
    os.makedirs(eval_dir, exist_ok=True)
    W, H = 1280, 720
    
    def patch_empty(img, x, y, w, h):
        sub = img[y:y+h, x:x+w].copy()
        sub[:] = (35, 75, 45)
        cv2.rectangle(sub, (2, 2), (w-2, 6), (70, 180, 210), -1)
        cv2.rectangle(sub, (2, h-6), (w-2, h-2), (70, 180, 210), -1)
        img[y:y+h, x:x+w] = sub

    for i in range(1, 32):
        tb = golden_master.copy()
        if i == 1 or i == 12 or i == 20:
            patch_empty(tb, 480, 250, 180, 180)
        if i == 2 or i == 24 or i == 20 or i == 31:
            patch_empty(tb, 320, 350, 90, 40)
            if i == 2 or i == 24:
                cv2.rectangle(tb, (320, 345), (345, 385), (60, 95, 140), -1)
                cv2.rectangle(tb, (320, 345), (345, 355), (200, 205, 210), -1)
        if i == 3 or i == 18 or i == 26 or i == 31:
            patch_empty(tb, 400, 310, 30, 45)
            if i == 3 or i == 26:
                r_crop = golden_master[310:355, 400:430]
                center = (15, 22)
                M = cv2.getRotationMatrix2D(center, 25, 1.0)
                rotated = cv2.warpAffine(r_crop, M, (30, 45), borderMode=cv2.BORDER_REFLECT)
                tb[310:355, 400:430] = rotated
        if i == 4 or i == 14 or i == 19 or i == 23 or i == 25:
            patch_empty(tb, 405, 520, 45, 30)
            if i == 4:
                tb[520:550, 417:462] = golden_master[520:550, 405:450]
            elif i == 23:
                cv2.rectangle(tb, (405, 515), (425, 545), (70, 110, 155), -1)
            elif i == 25:
                c_crop = golden_master[520:550, 405:450]
                center = (22, 15)
                M = cv2.getRotationMatrix2D(center, 20, 1.0)
                rotated = cv2.warpAffine(c_crop, M, (45, 30), borderMode=cv2.BORDER_REFLECT)
                tb[520:550, 405:450] = rotated
        if i == 10 or i == 13 or i == 22:
            patch_empty(tb, 350, 280, 60, 60)
        if i == 11 or i == 14 or i == 22:
            patch_empty(tb, 690, 310, 70, 100)
        if i == 15 or i == 21:
            patch_empty(tb, 340, 560, 60, 70)
        if i == 16 or i == 22:
            patch_empty(tb, 410, 560, 60, 70)
        if i == 17:
            patch_empty(tb, 200, 230, 140, 100)
        if i == 21:
            patch_empty(tb, 820, 180, 40, 420)
        if i == 27:
            patch_empty(tb, 320, 350, 90, 40)
            tb[350:390, 332:422] = golden_master[350:390, 320:410]
        if i == 28:
            patch_empty(tb, 400, 310, 30, 45)
            tb[310:355, 415:445] = golden_master[310:355, 400:430]
        if i == 29:
            M = np.float32([[1, 0, 15], [0, 1, 12]])
            tb = cv2.warpAffine(tb, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        if i == 30:
            M = np.float32([[1, 0, -10], [0, 1, 8]])
            tb = cv2.warpAffine(tb, M, (W, H), borderMode=cv2.BORDER_REFLECT)
            
        tb_name = f'TB{i:03d}.png'
        cv2.imwrite(os.path.join(eval_dir, tb_name), tb)

golden_img, golden_depth = create_real_pcb_master()
cv2.imwrite('server/reference/golden_board.png', golden_img)
np.save('server/reference/golden_depth.npy', golden_depth)
print('Saved real photographic golden_board.png and golden_depth.npy')
inject_board_defects(golden_img, golden_depth)
print('Generated 31 real photographic test boards in evaluation/test_boards/')
