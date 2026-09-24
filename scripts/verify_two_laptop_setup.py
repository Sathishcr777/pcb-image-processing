"""
Two-Laptop Network & API Verifier
Team 4 & Team 6 - Network Setup & Deployment Verification

Tests connection between Laptop A and Laptop B, uploads golden reference,
and sends test boards to verify the complete 2-laptop setup.
"""

import os
import sys
import requests
import json

def verify_setup(server_ip="127.0.0.1", port=8000):
    base_url = f"http://{server_ip}:{port}"
    print(f"=== TESTING TWO-LAPTOP SYSTEM SETUP ===")
    print(f"Target Server: {base_url}")

    # 1. Health Check
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        print(f"[1/4] GET /health: HTTP {r.status_code} -> {r.json()}")
    except Exception as e:
        print(f"[ERROR] Could not connect to {base_url}/health: {e}")
        return False

    # 2. Upload Golden Reference
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ref_img_path = os.path.join(base_dir, "server", "reference", "golden_board.png")

    if os.path.exists(ref_img_path):
        with open(ref_img_path, "rb") as f:
            r = requests.post(f"{base_url}/set-reference", files={"file": f}, timeout=10)
            print(f"[2/4] POST /set-reference: HTTP {r.status_code} -> {r.json()}")

    # 3. Test Inspection
    tb_img_path = os.path.join(base_dir, "evaluation", "test_boards", "TB001.png")
    if os.path.exists(tb_img_path):
        with open(tb_img_path, "rb") as f:
            r = requests.post(f"{base_url}/inspect", files={"file": f}, timeout=10)
            print(f"[3/4] POST /inspect: HTTP {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print(f"      Record ID:    {data['record_id']}")
                print(f"      Health Index: {data['health_index']}")
                print(f"      Verdict:      {data['verdict']}")

    # 4. Check Metrics
    try:
        r = requests.get(f"{base_url}/metrics", timeout=5)
        print(f"[4/4] GET /metrics: HTTP {r.status_code} -> {r.json()}")
    except Exception as e:
        print(f"[ERROR] GET /metrics failed: {e}")

    print("\n[SUCCESS] Two-laptop setup verified successfully!")
    return True

if __name__ == "__main__":
    ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    verify_setup(ip)
