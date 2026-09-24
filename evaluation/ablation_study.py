"""
Ablation Study Module
Team 5 - Model Optimization & Sub-Team B

Evaluates 3 system variants on the 31-board test set:
- Variant A: 2D-only (SSIM difference engine)
- Variant B: Depth-only (Monocular depth deviation engine)
- Variant C: Combined Pipeline (2D + Depth + Continuous Health Index)
"""

import os
import sys
import cv2
import pandas as pd
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server.pipeline.aligner import PCBAligner
from server.pipeline.detector_2d import Detector2D
from server.pipeline.detector_depth import DetectorDepth
from server.pipeline.health_index import HealthIndexCalculator

def run_ablation():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    df_labels = pd.read_csv(os.path.join(base_dir, "evaluation", "test_labels.csv"))
    tb_dir = os.path.join(base_dir, "evaluation", "test_boards")
    ref_img = cv2.imread(os.path.join(base_dir, "server", "reference", "golden_board.png"))

    aligner = PCBAligner()
    detector_2d = Detector2D()
    detector_depth = DetectorDepth()
    hi_calc = HealthIndexCalculator()

    ref_depth = detector_depth.estimate_depth(ref_img)

    with open(os.path.join(base_dir, "server", "config", "components.json"), "r") as f:
        components_config = json.load(f)

    gt_map = {}
    for _, row in df_labels.iterrows():
        bid = str(row["board_id"]).strip()
        cid = str(row["component_id"]).strip()
        dtype = str(row["defect_type"]).strip().lower()
        if cid != "NONE":
            gt_map[(bid, cid)] = True if dtype != "none" else False

    variants = ["Variant A (2D-Only)", "Variant B (Depth-Only)", "Variant C (Combined)"]
    results = {}

    for var in variants:
        tp, fp, tn, fn = 0, 0, 0, 0
        board_ids = sorted(list(set(df_labels["board_id"].unique())))

        for bid in board_ids:
            board_path = os.path.join(tb_dir, f"{bid}.png")
            if not os.path.exists(board_path):
                continue

            test_img = cv2.imread(board_path)
            aligned_img, _, _, _ = aligner.align(test_img, ref_img)

            res_2d = detector_2d.detect(aligned_img, ref_img, components_config)
            test_depth = detector_depth.estimate_depth(aligned_img)
            res_depth, _ = detector_depth.inspect(test_depth, ref_depth, components_config)

            for comp in components_config:
                cid = comp["id"]
                gt_def = gt_map.get((bid, cid), False)

                if var == "Variant A (2D-Only)":
                    pred_def = res_2d[cid]["is_missing"]
                elif var == "Variant B (Depth-Only)":
                    pred_def = res_depth[cid]["height_flag"] or res_depth[cid]["tilt_flag"] or res_depth[cid]["tombstone_flag"]
                else:
                    pred_def = res_2d[cid]["is_missing"] or res_depth[cid]["height_flag"] or res_depth[cid]["tilt_flag"] or res_depth[cid]["tombstone_flag"]

                if pred_def and gt_def:
                    tp += 1
                elif pred_def and not gt_def:
                    fp += 1
                elif not pred_def and gt_def:
                    fn += 1
                else:
                    tn += 1

        prec = tp / float(max(1, tp + fp))
        rec = tp / float(max(1, tp + fn))
        f1 = 2 * prec * rec / float(max(1e-5, prec + rec))
        fcr = fp / float(max(1, fp + tn))

        results[var] = {
            "Precision": round(prec, 4),
            "Recall": round(rec, 4),
            "F1_Score": round(f1, 4),
            "False_Call_Rate": round(fcr, 4)
        }

    print("=== ABLATION STUDY RESULTS ===")
    df_res = pd.DataFrame(results).T
    print(df_res.to_string())
    return df_res

if __name__ == "__main__":
    run_ablation()
