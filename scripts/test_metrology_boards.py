import os
import sys
import json
import cv2

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from server.pipeline.aligner import PCBAligner
from server.pipeline.metrology_engine import MetrologyEngine

def test_boards():
    aligner = PCBAligner()
    engine = MetrologyEngine(px_to_mm_scale=0.05)

    ref_img = cv2.imread("server/reference/golden_board.png")
    with open("server/config/components.json") as f:
        comps = json.load(f)

    for board_id in ["TB001", "TB002", "TB003", "TB004", "TB005"]:
        test_img = cv2.imread(f"evaluation/test_boards/{board_id}.png")
        aligned, q, _, _ = aligner.align(test_img, ref_img)
        print(f"\n==================== BOARD: {board_id} ====================")
        
        ref_h, ref_w = ref_img.shape[:2]
        for comp in comps:
            x, y, w, h = comp["bbox_xywh"]
            x1, y1 = max(0, min(x, ref_w - 1)), max(0, min(y, ref_h - 1))
            x2, y2 = max(x1 + 1, min(ref_w, x + w)), max(y1 + 1, min(ref_h, y + h))
            rt = aligned[y1:y2, x1:x2]
            rr = ref_img[y1:y2, x1:x2]
            if rt.shape != rr.shape:
                rt = cv2.resize(rt, (rr.shape[1], rr.shape[0]))
            m = engine.inspect_component_metrology(rt, rr, comp)
            
            print(f"[{comp['id']}] dx={m['delta_x_mm']:+.3f}mm ({m['delta_x_px']:+.1f}px) | dy={m['delta_y_mm']:+.3f}mm ({m['delta_y_px']:+.1f}px) | rot={m['rotation_deg']:+.1f}deg | ovh={m['max_overhang_pct']:.1f}% | verdict={m['ipc_class_verdict']} | polarity={m['polarity_status']}")

if __name__ == "__main__":
    test_boards()
