"""
ROC & PR Curve Threshold Sweeper
Team 5 - Model Optimization & Sub-Team A

Sweeps ssim_threshold from 0.50 to 0.90 to analyze trade-offs between
Precision, Recall, and False Call Rate.
"""

import os
import sys
import cv2
import numpy as np
import pandas as pd
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server.pipeline.aligner import PCBAligner
from server.pipeline.detector_2d import Detector2D
from server.pipeline.detector_depth import DetectorDepth

def sweep_thresholds():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    df_labels = pd.read_csv(os.path.join(base_dir, "evaluation", "test_labels.csv"))
    tb_dir = os.path.join(base_dir, "evaluation", "test_boards")
    ref_img = cv2.imread(os.path.join(base_dir, "server", "reference", "golden_board.png"))

    aligner = PCBAligner()
    detector_depth = DetectorDepth()

    with open(os.path.join(base_dir, "server", "config", "components.json"), "r") as f:
        components_config = json.load(f)

    gt_map = {}
    for _, row in df_labels.iterrows():
        bid = str(row["board_id"]).strip()
        cid = str(row["component_id"]).strip()
        dtype = str(row["defect_type"]).strip().lower()
        if cid != "NONE":
            gt_map[(bid, cid)] = True if dtype != "none" else False

    thresholds = [round(t, 2) for t in np.arange(0.50, 0.95, 0.05)]
    sweep_data = []

    board_ids = sorted(list(set(df_labels["board_id"].unique())))

    for thresh in thresholds:
        detector_2d = Detector2D(ssim_threshold=thresh)
        tp, fp, tn, fn = 0, 0, 0, 0

        for bid in board_ids:
            board_path = os.path.join(tb_dir, f"{bid}.png")
            if not os.path.exists(board_path):
                continue

            test_img = cv2.imread(board_path)
            aligned_img, _, _, _ = aligner.align(test_img, ref_img)
            res_2d = detector_2d.detect(aligned_img, ref_img, components_config)

            for comp in components_config:
                cid = comp["id"]
                pred_def = res_2d[cid]["is_missing"]
                gt_def = gt_map.get((bid, cid), False)

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
        fpr = fp / float(max(1, fp + tn))

        sweep_data.append({
            "SSIM_Threshold": thresh,
            "Precision": round(prec, 4),
            "Recall (TPR)": round(rec, 4),
            "FPR": round(fpr, 4),
            "F1_Score": round(f1, 4)
        })

    df_sweep = pd.DataFrame(sweep_data)
    print("=== SSIM THRESHOLD SWEEP DATA ===")
    print(df_sweep.to_string(index=False))
    return df_sweep

if __name__ == "__main__":
    sweep_thresholds()
