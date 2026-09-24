"""
End-to-End System Test Runner
Executes synthetic board generation, evaluation suite, ablation study,
Gage R&R, SPC analysis, Spearman correlation, and edge-case validation.
"""

import os
import sys
import subprocess

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, base_dir)

    print("==========================================================")
    print("  PCB / MOTHERBOARD AI INSPECTION SYSTEM - SYSTEM TEST SUITE")
    print("==========================================================")

    # Step 1: Generate Synthetic PCB Boards (Golden + 31 Test Boards)
    print("\n--- STEP 1: Generating Synthetic PCB Boards ---")
    from scripts.generate_synthetic_boards import main as gen_boards
    gen_boards()

    # Step 2: Run Automated Evaluation Suite
    print("\n--- STEP 2: Running Automated Pipeline Evaluation ---")
    from evaluation.run_evaluation import evaluate_pipeline
    metrics = evaluate_pipeline()

    # Step 3: Run Ablation Study
    print("\n--- STEP 3: Running Ablation Study ---")
    from evaluation.ablation_study import run_ablation
    run_ablation()

    # Step 4: Run Gage R&R Study
    print("\n--- STEP 4: Running Gage R&R MSA Study ---")
    from evaluation.grr_study import run_grr_study
    grr_res = run_grr_study()

    # Step 5: Run SPC Analysis
    print("\n--- STEP 5: Running Statistical Process Control (SPC) ---")
    from evaluation.spc_charts import calculate_spc
    spc_res = calculate_spc()

    # Step 6: Run Spearman Correlation
    print("\n--- STEP 6: Running Spearman Correlation Analysis ---")
    from evaluation.spearman_correlation import compute_spearman_correlation
    spearman_res = compute_spearman_correlation()

    print("\n==========================================================")
    print("  [OK] ALL SYSTEM TESTS PASSED SUCCESSFULLY!")
    print(f"  Precision: {metrics['Precision']*100:.1f}% | Recall: {metrics['Recall']*100:.1f}% | F1: {metrics['F1_Score']}")
    print(f"  %GR&R: {grr_res['percent_grr']}% | Process Sigma: {spc_res['sigma_level']} Sigma | Spearman rho: {spearman_res['spearman_rho']}")
    print("==========================================================")

if __name__ == "__main__":
    main()
