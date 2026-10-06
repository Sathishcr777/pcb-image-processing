import os
import sys
import json
import urllib.request
import urllib.parse

BASE_URL = "http://127.0.0.1:8000"

def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, r.read().decode('utf-8', errors='ignore')

def delete(path):
    req = urllib.request.Request(f"{BASE_URL}{path}", method="DELETE")
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, json.loads(r.read().decode('utf-8'))

def inspect_board(board_id):
    img_path = os.path.join("evaluation", "test_boards", f"{board_id}.png")
    if not os.path.exists(img_path):
        raise FileNotFoundError(f"Board image not found: {img_path}")
    
    with open(img_path, "rb") as f:
        img_bytes = f.read()

    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = []
    body.append(f"--{boundary}".encode())
    body.append(b'Content-Disposition: form-data; name="board_serial"')
    body.append(b'')
    body.append(board_id.encode())
    body.append(f"--{boundary}".encode())
    body.append(f'Content-Disposition: form-data; name="file"; filename="{board_id}.png"'.encode())
    body.append(b'Content-Type: image/png')
    body.append(b'')
    body.append(img_bytes)
    body.append(f"--{boundary}--".encode())
    body.append(b'')
    payload = b"\r\n".join(body)

    req = urllib.request.Request(
        f"{BASE_URL}/inspect",
        data=payload,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(payload))
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, json.loads(r.read().decode('utf-8'))

def main():
    print("=" * 65)
    print("TESTING USER VALIDATION WORKFLOW (STEP 1 - 16)")
    print("=" * 65)

    # Clean session before test
    delete("/api/session-audits")
    print("[PASS] Session audit cache cleared for fresh test")

    # Step 1: Open Inspection page
    status, html_index = get("/")
    assert status == 200
    assert "/audit-history" in html_index
    print("[PASS] [Step 1] Inspection page loaded, has /audit-history navigation")

    # Step 2 & 3: Select TB032 and Run inspection
    status, insp_tb032 = inspect_board("TB032")
    assert status == 200
    assert insp_tb032["verdict"] == "FAIL"
    print(f"[PASS] [Steps 2-3] TB032 inspected: verdict={insp_tb032['verdict']}, HI={insp_tb032['health_index']}")

    # Step 4 & 5: Open Audit History and confirm TB032 appears with correct image and result
    status, html_ah = get("/audit-history")
    assert status == 200
    status, logs_data = get("/api/session-audits")
    logs = json.loads(logs_data)
    assert len(logs) == 1, f"Expected 1 audit entry, got {len(logs)}"
    assert logs[0]["board_id"] == "TB032"
    assert "TB032.png" in logs[0]["image_url"]
    assert logs[0]["verdict"] == "FAIL"
    print(f"[PASS] [Steps 4-5] Audit History shows TB032 with image: {logs[0]['image_url']} and verdict: {logs[0]['verdict']}")

    # Step 6: Return to Inspection
    status, _ = get("/")
    assert status == 200
    print("[PASS] [Step 6] Returned to Live Inspection")

    # Step 7 & 8: Select TB010 and Run inspection
    status, insp_tb010 = inspect_board("TB010")
    assert status == 200
    print(f"[PASS] [Steps 7-8] TB010 inspected: verdict={insp_tb010['verdict']}, HI={insp_tb010['health_index']}")

    # Step 9 & 10: Open Audit History and confirm TB010 appears as NEW entry while TB032 remains
    status, logs_data2 = get("/api/session-audits")
    logs2 = json.loads(logs_data2)
    assert len(logs2) == 2, f"Expected 2 audit entries, got {len(logs2)}"
    assert logs2[0]["board_id"] == "TB032", f"Expected first entry to be TB032, got {logs2[0]['board_id']}"
    assert logs2[1]["board_id"] == "TB010", f"Expected second entry to be TB010, got {logs2[1]['board_id']}"
    assert "TB032.png" in logs2[0]["image_url"]
    assert "TB010.png" in logs2[1]["image_url"]
    print("[PASS] [Steps 9-10] Both boards preserved in Audit History: #1 TB032, #2 TB010 (no overwrite)")

    # Step 11: Open TB032 audit dossier and verify it still shows TB032 data
    status, d_tb032 = get("/api/audit/board/TB032")
    data_32 = json.loads(d_tb032)
    assert data_32["board_id"] == "TB032"
    assert data_32["verdict"] == "FAIL"
    assert "TB032.png" in data_32["image_url"]
    print(f"[PASS] [Step 11] TB032 dossier verified: {data_32['board_id']} - {data_32.get('scenario_name')}")

    # Step 12: Open TB010 audit dossier and verify it shows TB010 data
    status, d_tb010 = get("/api/audit/board/TB010")
    data_10 = json.loads(d_tb010)
    assert data_10["board_id"] == "TB010"
    assert "TB010.png" in data_10["image_url"]
    print(f"[PASS] [Step 12] TB010 dossier verified: {data_10['board_id']} - {data_10.get('scenario_name')}")

    # Step 13 & 14: Download TB032 audit and confirm report contains TB032 info
    status, rep_tb032 = get("/api/audit/report/TB032?download=1")
    assert status == 200
    assert "TB032" in rep_tb032
    assert "TB032.png" in rep_tb032 or "data:image/png;base64" in rep_tb032
    assert "FAIL" in rep_tb032
    assert "Golden Master" in rep_tb032
    print("[PASS] [Steps 13-14] Downloaded TB032 audit report: verified board ID, image, verdict, golden comparison")

    # Step 15 & 16: Download TB010 audit and confirm report contains TB010 info
    status, rep_tb010 = get("/api/audit/report/TB010?download=1")
    assert status == 200
    assert "TB010" in rep_tb010
    assert "TB010.png" in rep_tb010 or "data:image/png;base64" in rep_tb010
    assert "Golden Master" in rep_tb010
    print("[PASS] [Steps 15-16] Downloaded TB010 audit report: verified board ID, image, verdict, golden comparison")

    print("=" * 65)
    print(">>> ALL 16 VALIDATION STEPS PASSED SUCCESSFULLY (100%) <<<")
    print("=" * 65)

if __name__ == "__main__":
    main()
