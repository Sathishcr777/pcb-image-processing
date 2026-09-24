"""
Statistical Process Control (SPC) & DPMO Calculator
Team 5 - Model Optimization & Sub-Team B

Plots p-chart (fraction defective per batch), c-chart (defect count per board),
computes DPMO and derives Process Sigma level.
"""

import numpy as np
import math

def calculate_spc():
    # Inspection data across 31 boards
    defects_per_board = [
        1, 1, 1, 1, 0, 0, 0, 0, 0, 1, # TB1 - TB10
        1, 1, 1, 2, 1, 1, 1, 1, 1, 2, # TB11 - TB20
        2, 3, 1, 1, 1, 1, 1, 1, 0, 0, 2 # TB21 - TB31
    ]

    total_boards = len(defects_per_board)
    total_components_per_board = 10
    total_defects = sum(defects_per_board)
    total_opportunities = total_boards * total_components_per_board

    # 1. DPMO & Sigma Level
    dpmo = (total_defects / float(total_opportunities)) * 1e6
    defective_rate = total_defects / float(total_opportunities)

    # Approximate Process Sigma Level from Yield (Yield = 1 - defective_rate)
    pcb_yield = 1.0 - defective_rate
    # Standard normal quantile approximation for Sigma level
    sigma_level = round(1.5 + np.abs(np.percentile(np.random.normal(0, 1, 100000), pcb_yield * 100)), 2)

    # 2. c-Chart Control Limits (Defects per board)
    c_bar = float(np.mean(defects_per_board))
    ucl_c = c_bar + 3.0 * np.sqrt(c_bar)
    lcl_c = max(0.0, c_bar - 3.0 * np.sqrt(c_bar))

    # 3. p-Chart Control Limits (Fraction defective)
    p_bar = defective_rate
    n = total_components_per_board
    ucl_p = p_bar + 3.0 * np.sqrt((p_bar * (1.0 - p_bar)) / float(n))
    lcl_p = max(0.0, p_bar - 3.0 * np.sqrt((p_bar * (1.0 - p_bar)) / float(n)))

    print("=== STATISTICAL PROCESS CONTROL (SPC) METRICS ===")
    print(f"Total Boards Inspected: {total_boards}")
    print(f"Total Components:      {total_opportunities}")
    print(f"Total Defect Count:    {total_defects}")
    print(f"DPMO:                  {dpmo:.2f}")
    print(f"Process Sigma Level:   {sigma_level} Sigma (Target >= 3.0 Sigma)")
    print(f"c-Chart Limits:        Bar={c_bar:.2f}, UCL={ucl_c:.2f}, LCL={lcl_c:.2f}")
    print(f"p-Chart Limits:        Bar={p_bar:.4f}, UCL={ucl_p:.4f}, LCL={lcl_p:.4f}")

    return {
        "dpmo": round(dpmo, 2),
        "sigma_level": sigma_level,
        "c_bar": round(c_bar, 2),
        "ucl_c": round(ucl_c, 2),
        "lcl_c": round(lcl_c, 2),
        "p_bar": round(p_bar, 4),
        "ucl_p": round(ucl_p, 4),
        "lcl_p": round(lcl_p, 4)
    }

if __name__ == "__main__":
    calculate_spc()
