"""
Laptop A — Webcam Capture & Inspection Client
Team 6 - AI Deployment, API Server & Client UX

Captures live webcam feed from Laptop A, transmits frames over Ubiquiti network
to Laptop B (Server IP: 192.168.1.100:8000), and renders inspection overlay.
"""

import cv2
import requests
import base64
import numpy as np
import time
import sys

SERVER_URL = "http://192.168.1.10:8000/inspect"
import os

def send_image_for_inspection(image_bgr, server_url=SERVER_URL):
    _, img_encoded = cv2.imencode(".png", image_bgr)
CLIENT_API_KEY = os.getenv("PCB_AOI_API_KEY", "").strip()
CLIENT_MAX_RETRIES = max(1, int(os.getenv("PCB_AOI_CLIENT_MAX_RETRIES", "3")))
CLIENT_TIMEOUT_SECONDS = float(os.getenv("PCB_AOI_CLIENT_TIMEOUT_SECONDS", "10"))
CLIENT_RETRY_BASE_SECONDS = float(os.getenv("PCB_AOI_CLIENT_RETRY_BASE_SECONDS", "1.5"))


def build_request_headers():
    headers = {"Accept": "application/json"}
    if CLIENT_API_KEY:
        headers["X-API-Key"] = CLIENT_API_KEY
    return headers
    files = {"file": ("inspection_board.png", img_encoded.tobytes(), "image/png")}

    success, img_encoded = cv2.imencode(".png", image_bgr)
    if not success:
        print("[ERROR] Failed to encode image for upload.")
        return None


    headers = build_request_headers()
    # Network retry handling
    for attempt in range(1, 3):
        try:
    # Retry transient transport/server errors with exponential backoff.
    for attempt in range(1, CLIENT_MAX_RETRIES + 1):
                return resp.json()
            resp = requests.post(server_url, files=files, headers=headers, timeout=CLIENT_TIMEOUT_SECONDS)
                print("[ERROR] Server returned 503: Reference Board Not Set!")
                return None
            elif resp.status_code == 503:
                try:
                    payload = resp.json()
                except Exception:
                    payload = {}
                if payload.get("detail") == "reference_not_set":
                    print("[ERROR] Server returned 503: Reference Board Not Set!")
                    return None
                if attempt < CLIENT_MAX_RETRIES:
                    delay = CLIENT_RETRY_BASE_SECONDS * attempt
                    print(f"[WARNING] Server unavailable on attempt {attempt}. Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                    continue
                print(f"[ERROR] HTTP 503: {resp.text}")
                return None
            elif resp.status_code in {408, 429} or 500 <= resp.status_code <= 599:
                if attempt < CLIENT_MAX_RETRIES:
                    delay = CLIENT_RETRY_BASE_SECONDS * attempt
                    print(f"[WARNING] HTTP {resp.status_code} on attempt {attempt}. Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                    continue
                print(f"[ERROR] HTTP {resp.status_code}: {resp.text}")
                return None
            elif resp.status_code == 401:
                print("[ERROR] Server rejected the API key (401 Unauthorized).")
                return None
                print("[ERROR] Server returned 422: Image Alignment Failed (< 0.40 score)!")
                return None
            else:
                print(f"[ERROR] HTTP {resp.status_code}: {resp.text}")
                return None
        except requests.exceptions.Timeout:
            print(f"[WARNING] Request timeout on attempt {attempt}. Retrying in 5 seconds...")
            if attempt < CLIENT_MAX_RETRIES:
                delay = CLIENT_RETRY_BASE_SECONDS * attempt
                print(f"[WARNING] Request timeout on attempt {attempt}. Retrying in {delay:.1f} seconds...")
                time.sleep(delay)
                continue
            print(f"[ERROR] Request timeout on final attempt {attempt}.")
            return None
        except requests.exceptions.RequestException as e:
            if attempt < CLIENT_MAX_RETRIES:
                delay = CLIENT_RETRY_BASE_SECONDS * attempt
                print(f"[WARNING] Connection error on attempt {attempt}: {e}. Retrying in {delay:.1f} seconds...")
                time.sleep(delay)
                continue
            print(f"[ERROR] Connection error: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Connection error: {e}")
            print(f"[ERROR] Connection error: {e}")

    return None
    return None

def main():
    server_url = sys.argv[1] if len(sys.argv) > 1 else SERVER_URL
    print(f"=== PCB AI Inspection Client ===")
    print(f"Target Server: {server_url}")
    print("Press SPACE to capture and inspect PCB. Press 'q' to quit.")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[WARNING] Could not open webcam 0. Using fallback synthetic test mode.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to grab frame.")
            break

        cv2.putText(frame, "PRESS SPACE TO INSPECT BOARD", (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Laptop A - Camera Feed", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == 32: # SPACE key
            print("[CLIENT] Capturing frame...")
            res = send_image_for_inspection(frame, server_url)
            if res:
                hi = res.get("health_index", 0.0)
                verdict = res.get("verdict", "UNKNOWN")
                latency = res.get("processing_time_ms", 0.0)
                print(f"[RESULT] Health Index: {hi:.3f} | Verdict: {verdict} | Latency: {latency:.1f} ms")

                if "overlay_image_b64" in res:
                    img_bytes = base64.b64decode(res["overlay_image_b64"])
                    nparr = np.frombuffer(img_bytes, np.uint8)
                    overlay_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    cv2.imshow("Inspection Result Overlay", overlay_bgr)
                    cv2.waitKey(0)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
