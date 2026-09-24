import cv2
import json
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from server.pipeline.metrology_engine import MetrologyEngine

engine = MetrologyEngine()
ref_img = cv2.imread("server/reference/golden_board.png")
gray_ref = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
with open("server/config/components.json") as f:
    comps = json.load(f)

for comp in comps:
    x, y, w, h = comp["bbox_xywh"]
    roi = gray_ref[y:y+h, x:x+w]
    if "ELECTRO" in comp.get("name", "").upper():
        is_s, s_score = engine._verify_cathode_stripe(roi)
        print(f"Cap {comp['id']}: Stripe diff = {s_score:.2f} -> is_stripe = {is_s}")
