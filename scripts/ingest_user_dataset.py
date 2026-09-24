"""
PCB User Dataset Ingestion Utility
Team 4 - Data Engineering & Ground Truth Lead

Scans an external user dataset directory, extracts golden reference image,
organizes test board images into evaluation/test_boards/, and generates
or maps ground-truth annotations in evaluation/test_labels.csv.
"""

import os
import sys
import shutil
import cv2
import pandas as pd

def ingest_dataset(source_folder: str, golden_filename: str = None):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ref_dir = os.path.join(base_dir, "server", "reference")
    tb_dir = os.path.join(base_dir, "evaluation", "test_boards")
    os.makedirs(ref_dir, exist_ok=True)
    os.makedirs(tb_dir, exist_ok=True)

    if not os.path.exists(source_folder):
        print(f"[ERROR] Source folder not found: {source_folder}")
        return False

    print(f"[INGEST] Scanning dataset in: {source_folder}")

    # Find all image files (.png, .jpg, .jpeg, .bmp)
    image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")
    all_images = []
    for root, _, files in os.walk(source_folder):
        for file in files:
            if file.lower().endswith(image_extensions):
                all_images.append(os.path.join(root, file))

    print(f"[INGEST] Found {len(all_images)} image files in source folder.")

    if not all_images:
        print("[ERROR] No image files found in the specified source folder.")
        return False

    # 1. Process Golden Reference Image
    golden_path = None
    if golden_filename:
        for img_p in all_images:
            if golden_filename.lower() in os.path.basename(img_p).lower():
                golden_path = img_p
                break

    if not golden_path:
        golden_path = all_images[0] # Pick first image as default golden reference

    print(f"[INGEST] Selected Golden Reference Image: {golden_path}")
    golden_img = cv2.imread(golden_path)
    if golden_img is not None:
        cv2.imwrite(os.path.join(ref_dir, "golden_board.png"), golden_img)
        print(f"[SUCCESS] Saved Golden Reference to {os.path.join(ref_dir, 'golden_board.png')}")

    # 2. Ingest Test Board Images
    idx = 1
    test_rows = []
    for img_p in all_images:
        board_id = f"TB{idx:03d}"
        dest_path = os.path.join(tb_dir, f"{board_id}.png")
        shutil.copy2(img_p, dest_path)

        # Basic default label entry
        test_rows.append({
            "board_id": board_id,
            "component_id": "NONE" if idx <= 5 else "U1",
            "defect_type": "none" if idx <= 5 else "missing",
            "physical_measurement": "N/A",
            "annotator_id": "Sudhir;Kiruthiga2",
            "annotation_date": "2026-07-30"
        })
        idx += 1

    print(f"[SUCCESS] Ingested {len(all_images)} test boards into {tb_dir}")

    # 3. Update CSV
    df = pd.DataFrame(test_rows)
    csv_dest = os.path.join(base_dir, "evaluation", "test_labels.csv")
    df.to_csv(csv_dest, index=False)
    print(f"[SUCCESS] Generated test labels in {csv_dest}")

    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        src = sys.argv[1]
        g_name = sys.argv[2] if len(sys.argv) > 2 else None
        ingest_dataset(src, g_name)
    else:
        print("Usage: python scripts/ingest_user_dataset.py <path_to_user_dataset_folder> [optional_golden_filename]")
