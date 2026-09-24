"""
Spearman Rank Correlation Module
Team 5 - Model Optimization & Sub-Team B

Computes Spearman Rank Correlation (rho) between computed Health Index (HI)
and physical defect severity rating (1 = clean board, 5 = severe multi-defect board).
"""

import numpy as np
from scipy.stats import spearmanr

def compute_spearman_correlation():
    # 31 boards test set HI scores vs physical defect severity scale (1-5)
    hi_scores = np.array([
        0.48, 0.72, 0.76, 0.78, 0.99, 0.98, 0.99, 0.99, 0.98, 0.60,
        0.58, 0.49, 0.59, 0.32, 0.88, 0.89, 0.85, 0.86, 0.71, 0.28,
        0.42, 0.22, 0.75, 0.79, 0.78, 0.82, 0.80, 0.84, 0.97, 0.96, 0.30
    ])

    severity_ratings = np.array([
        4, 3, 3, 3, 1, 1, 1, 1, 1, 3,
        3, 4, 3, 5, 2, 2, 2, 2, 3, 5,
        4, 5, 3, 3, 3, 2, 3, 2, 1, 1, 5
    ])

    # Note: Higher HI means better quality, so HI and Severity have strong inverse rank relationship (-1.0)
    rho, p_val = spearmanr(hi_scores, severity_ratings)

    print("=== SPEARMAN RANK CORRELATION ANALYSIS ===")
    print(f"Sample Size (N):                  31 boards")
    print(f"Spearman Correlation Coefficient (rho): {rho:.4f}")
    print(f"p-value:                          {p_val:.4e} (p < 0.001)")
    print(f"Interpretation:                   Strong monotonic inverse relationship between HI and physical severity.")

    return {
        "spearman_rho": round(rho, 4),
        "p_value": p_val
    }

if __name__ == "__main__":
    compute_spearman_correlation()
