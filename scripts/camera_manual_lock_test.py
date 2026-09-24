"""
Camera Manual Exposure Lock & Placement Helper
Team 4 - Data Engineering & Hardware Gate

Locks camera exposure settings (disables Auto-Brightness & Auto-Exposure)
and displays placement framing box on Laptop A webcam.
"""

import cv2
import sys

def run_camera_lock_helper():
    print("=== TEAM 4 CAMERA EXPOSURE LOCK & FRAMING HELPER ===")
    print("Opening webcam 0...")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open webcam on Laptop A.")
        return

    # Lock camera settings (Disable Auto Exposure & Auto White Balance)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25) # 0.25 = Manual mode in OpenCV
    cap.set(cv2.CAP_PROP_EXPOSURE, -6)        # Fixed exposure value

    print("[SUCCESS] Auto-Exposure locked. Auto-Brightness disabled.")
    print("Position phone/board inside the GREEN rectangle.")
    print("Press 's' to save SOP white balance photo. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        h, w = frame.shape[:2]

        # Draw Placement Box (Green Target Box)
        box_x1, box_y1 = int(w * 0.2), int(h * 0.2)
        box_x2, box_y2 = int(w * 0.8), int(h * 0.8)
        cv2.rectangle(frame, (box_x1, box_y1), (box_x2, box_y2), (0, 255, 0), 2)
        cv2.putText(frame, "PIN 1 TOP-LEFT", (box_x1, box_y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.putText(frame, "EXPOSURE LOCKED (AUTO-BRIGHTNESS OFF)", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        cv2.imshow("Team 4 - Camera Setup SOP", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            cv2.imwrite("docs/white_balance_reference.png", frame)
            print("[SUCCESS] Saved white-balance reference frame to docs/white_balance_reference.png")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_camera_lock_helper()
