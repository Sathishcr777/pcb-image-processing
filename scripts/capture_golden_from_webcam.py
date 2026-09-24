"""
Golden Reference Webcam Capture Tool
Team 4 - Data Engineering & Hardware Gate

Captures live photo of the Golden Reference PCB from Laptop A's webcam,
saves it to server/reference/golden_board.png, and automatically registers it.
"""

import cv2
import os
import requests
import sys

def capture_golden_reference(server_ip="127.0.0.1"):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ref_dir = os.path.join(base_dir, "server", "reference")
    os.makedirs(ref_dir, exist_ok=True)
    golden_path = os.path.join(ref_dir, "golden_board.png")

    print("=== TEAM 4 GOLDEN REFERENCE CAPTURE TOOL ===")
    print("Opening webcam 0 on Laptop A...")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open webcam on Laptop A.")
        return False

    print("\n-----------------------------------------------------------")
    print("1. Place your phone/board flat inside the GREEN target box.")
    print("2. Press SPACEBAR to capture the Golden Reference picture!")
    print("3. Press 'q' to cancel.")
    print("-----------------------------------------------------------\n")

    captured = False

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to grab frame from camera.")
            break

        h, w = frame.shape[:2]

        # Draw Target Box
        cv2.rectangle(frame, (int(w*0.15), int(h*0.15)), (int(w*0.85), int(h*0.85)), (0, 255, 0), 2)
        cv2.putText(frame, "GOLDEN REFERENCE TARGET ZONE", (int(w*0.15), int(h*0.15) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, "PRESS SPACEBAR TO CAPTURE REAL PHOTO", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        cv2.imshow("Laptop A - Capture Golden Reference", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("[CANCELLED] Golden reference capture cancelled.")
            break
        elif key == 32: # SPACEBAR
            cv2.imwrite(golden_path, frame)
            print(f"\n[SUCCESS] REAL PHOTO CAPTURED AND SAVED TO: {golden_path}")
            captured = True
            break

    cap.release()
    cv2.destroyAllWindows()

    if captured:
        # Try uploading to Laptop B server automatically if server IP provided
        server_url = f"http://{server_ip}:8000/set-reference"
        print(f"\n[UPLOADING] Transmitting golden reference to Laptop B server ({server_url})...")
        try:
            with open(golden_path, "rb") as f:
                r = requests.post(server_url, files={"file": f}, timeout=10)
                if r.status_code == 200:
                    print("[SUCCESS] Golden reference registered on Laptop B server!")
                    print(r.json())
                else:
                    print(f"[WARNING] Server returned status {r.status_code}: {r.text}")
        except Exception as e:
            print(f"[INFO] Image saved locally. Remember to run POST /set-reference on Laptop B.")

    return captured

if __name__ == "__main__":
    ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    capture_golden_reference(ip)
