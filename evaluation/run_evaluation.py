"""
Automated Pipeline Evaluator
Team 5 - Model Optimization & Sub-Team B

Loads evaluation/test_labels.csv, passes all 31 test boards through the inspection pipeline,
and computes Precision, Recall, F1 Score, False Call Rate (FCR), Escape Rate, and Confusion Matrix.
"""

import os
import sys
import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server.pipeline.aligner import PCBAligner
from server.pipeline.detector_2d import Detector2D
from server.pipeline.detector_depth import DetectorDepth
from server.pipeline.health_index import HealthIndexCalculator

def evaluate_pipeline():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    labels_csv = os.path.join(base_dir, "evaluation", "test_labels.csv")
    tb_dir = os.path.join(base_dir, "evaluation", "test_boards")
    ref_img_path = os.path.join(base_dir, "server", "reference", "golden_board.png")

    if not os.path.exists(labels_csv) or not os.path.exists(ref_img_path):
        print("[ERROR] Evaluation files missing. Run generate_synthetic_boards.py first.")
        return

    df_labels = pd.read_csv(labels_csv)
    ref_img = cv2.imread(ref_img_path)

    aligner = PCBAligner()
    detector_2d = Detector2D()
    detector_depth = DetectorDepth()
    hi_calc = HealthIndexCalculator()

    ref_depth = detector_depth.estimate_depth(ref_img)

    config_path = os.path.join(base_dir, "server", "config", "components.json")
    import json
    with open(config_path, "r") as f:
        components_config = json.load(f)

    # Build ground truth dictionary: (board_id, component_id) -> is_defective
    gt_map = {}
    for _, row in df_labels.iterrows():
        bid = str(row["board_id"]).strip()
        cid = str(row["component_id"]).strip()
        dtype = str(row["defect_type"]).strip().lower()

        if cid != "NONE":
            gt_map[(bid, cid)] = True if dtype != "none" else False

    tp, fp, tn, fn = 0, 0, 0, 0

    print("=== RUNNING FULL PIPELINE EVALUATION ON 31 TEST BOARDS ===")

    board_ids = sorted(list(set(df_labels["board_id"].unique())))

    for bid in board_ids:
        board_path = os.path.join(tb_dir, f"{bid}.png")
        if not os.path.exists(board_path):
            continue

        test_img = cv2.imread(board_path)
        aligned_img, quality, _, _ = aligner.align(test_img, ref_img)

        results_2d = detector_2d.detect(aligned_img, ref_img, components_config)
        test_depth = detector_depth.estimate_depth(aligned_img)
        results_depth, _ = detector_depth.inspect(test_depth, ref_depth, components_config)

        hi_res = hi_calc.compute(components_config, results_2d, results_depth)

        for comp in hi_res["components"]:
            cid = comp["id"]
            pred_defective = comp["is_defective"]
            gt_defective = gt_map.get((bid, cid), False)

            if pred_defective and gt_defective:
                tp += 1
            elif pred_defective and not gt_defective:
                fp += 1
            elif not pred_defective and gt_defective:
                fn += 1
            else:
                tn += 1

    precision = tp / float(max(1, tp + fp))
    recall = tp / float(max(1, tp + fn))
    f1 = 2 * precision * recall / float(max(1e-5, precision + recall))
    fcr = fp / float(max(1, fp + tn)) # False Call Rate
    escape_rate = fn / float(max(1, fn + tp)) # Escape Rate (Missed defects)

    metrics = {
        "TP": tp, "FP": fp, "TN": tn, "FN": fn,
        "Precision": round(precision, 4),
        "Recall": round(recall, 4),
        "F1_Score": round(f1, 4),
        "False_Call_Rate": round(fcr, 4),
        "Escape_Rate": round(escape_rate, 4)
    }

    print(f"TP: {tp} | FP: {fp} | TN: {tn} | FN: {fn}")
    print(f"Precision:        {precision*100:.2f}%")
    print(f"Recall (Sensitivity): {recall*100:.2f}%")
    print(f"F1 Score:         {f1:.4f}")
    print(f"False Call Rate:  {fcr*100:.2f}%")
    print(f"Escape Rate:      {escape_rate*100:.2f}%")

    return metrics

if __name__ == "__main__":
    evaluate_pipeline()
