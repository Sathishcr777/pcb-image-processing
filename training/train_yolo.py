"""
YOLOv8 Fine-Tuning Module (Background Research Track)
Team 5 - Model Optimization & Computer Vision Engine

Fine-tunes YOLOv8n detector on PCB dataset (50 epochs, imgsz=640, batch=8).
"""

import os
import sys
import json

def create_dataset_yaml(base_dir: str) -> str:
    """Generates YOLO dataset.yaml configuration file."""
    yaml_path = os.path.join(base_dir, "pcb_dataset.yaml")
    content = f"""# PCB Inspection Dataset Specification
path: {os.path.abspath(base_dir)}
train: dataset/train/images
val: dataset/valid/images
test: dataset/test/images

names:
  0: IC
  1: Capacitor
  2: Resistor
  3: VoltageRegulator
  4: Connector
  5: MissingDefect
  6: TombstoneDefect
"""
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(content)
    return yaml_path

def train_yolo():
    print("=== STARTING YOLOV8 PCB COMPONENT FINE-TUNING (RESEARCH TRACK) ===")
    base_dir = os.path.abspath(os.path.dirname(__file__))
    yaml_path = create_dataset_yaml(base_dir)
    print(f"[YOLO] Dataset specification written to: {yaml_path}")

    try:
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")
        print("[YOLO] Base model 'yolov8n.pt' loaded successfully.")
        
        # Trigger training if dataset exists, else display ready status
        train_img_dir = os.path.join(base_dir, "dataset", "train", "images")
        if os.path.exists(train_img_dir) and len(os.listdir(train_img_dir)) > 0:
            print("[YOLO] Training dataset detected. Executing fine-tuning...")
            results = model.train(data=yaml_path, epochs=50, imgsz=640, batch=8, project=base_dir, name="runs/detect/train")
            print(f"[YOLO] Fine-tuning complete. Model saved to: {results.save_dir}")
        else:
            print("[YOLO] Pipeline ready. (Add images to training/dataset/train/images to start full training run).")
    except ImportError:
        print("[YOLO] 'ultralytics' package not installed. Install via `pip install ultralytics` for deep learning training.")
    except Exception as e:
        print(f"[YOLO] Fine-tuning error: {e}")

if __name__ == "__main__":
    train_yolo()
