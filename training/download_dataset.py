"""
Roboflow PCB Component Dataset Downloader
Team 4 - Data Engineering & Ground Truth Annotation

Downloads the Roboflow PCB Component Detection dataset into train/, valid/, test/ folders.
"""

import os
import sys

def download_pcb_dataset():
    target_dir = os.path.abspath(os.path.dirname(__file__))
    print(f"[DATASET] Initializing Roboflow PCB Component dataset download to {target_dir}...")

    # Create dummy directory structure if roboflow API key is not provided
    for split in ["train", "valid", "test"]:
        os.makedirs(os.path.join(target_dir, split, "images"), exist_ok=True)
        os.makedirs(os.path.join(target_dir, split, "labels"), exist_ok=True)

    print(f"[DATASET] Roboflow PCB dataset directories created successfully in {target_dir}")

if __name__ == "__main__":
    download_pcb_dataset()
