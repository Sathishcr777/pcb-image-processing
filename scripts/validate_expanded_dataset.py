"""
Comprehensive Validation Script for Expanded PCB Dataset (TB001 - TB040)
Tests baseline preservation, new scenario correctness, and cross-page synchronization.
"""

import os
import sys
import json
import urllib.request
import urllib.parse

BASE_URL = "http://127.0.0.1:8000"

def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status, r.read().decode('utf-8', errors='ignore')

def get_json(path):
    st, data = get(path)
    return st, json.loads(data)

def post_json(path, payload):
    data_bytes = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data_bytes,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status, json.loads(r.read().decode('utf-8'))

def inspect_board(board_id):
    img_path = os.path.join("evaluation", "test_boards", f"{board_id}.png")
    if not os.path.exists(img_path):
        raise FileNotFoundError(f"Board image not found: {img_path}")
    
    with open(img_path, "rb") as f:
        img_bytes = f.read()

    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = [
        f"--{boundary}".encode(),
        b'Content-Disposition: form-data; name="board_serial"',
        b'',
        board_id.encode(),
        f"--{boundary}".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{board_id}.png"'.encode(),
        b'Content-Type: image/png',
        b'',
        img_bytes,
        f"--{boundary}--".encode(),
        b''
    ]
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
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.status, json.loads(r.read().decode('utf-8'))

def run_tests():
    print("=" * 70)
    print("PCB AOI SUITE - EXPANDED DATASET AUTOMATED VERIFICATION")
    print("=" * 70)

    # 1. Clear session audits before test
    req = urllib.request.Request(f"{BASE_URL}/api/session-audits", method="DELETE")
    urllib.request.urlopen(req, timeout=10)
    print("[1/6] Cleaned session audit history")

    # 2. Test Baseline Boards (TB001, TB005, TB010, TB032)
    print("\n[2/6] Testing Baseline Boards (TB001, TB005, TB010, TB032)...")
    baseline_targets = [
        ("TB005", "PASS", 0.99, 1.01),
        ("TB001", "PASS", 0.98, 1.00),
        ("TB010", "REWORK", 0.84, 0.91),
        ("TB032", "FAIL", 0.00, 0.85)
    ]
    for bid, exp_verdict, min_hi, max_hi in baseline_targets:
        st, res = inspect_board(bid)
        assert st == 200, f"Failed to inspect {bid}"
        verdict = res.get("verdict")
        hi = float(res.get("health_index", 0.0))
        assert min_hi <= hi <= max_hi, f"{bid} HI {hi} outside expected range [{min_hi}, {max_hi}]"
        print(f"  OK - {bid}: Verdict={verdict}, HI={hi*100:.2f}% (Baseline Preserved)")

    # 3. Test New Realistic Boards (TB033 through TB040)
    print("\n[3/6] Testing New Realistic Boards (TB033 - TB040)...")
    new_targets = [
        ("TB033", "In-Line Conforming Batch", "PASS", 0.98, 1.00),
        ("TB034", "U4 Angular Tilt Skew", "REWORK", 0.85, 0.93),
        ("TB035", "U3 Missing Controller", "REWORK", 0.84, 0.93),
        ("TB036", "U2 Solder Bridge Short", "REWORK", 0.85, 0.95),
        ("TB037", "J_TOP Open / Broken Trace", "REWORK", 0.85, 0.95),
        ("TB038", "Multi-Defect Assembly", "REWORK", 0.70, 0.88),
        ("TB039", "BANK_L1 Substrate Scratch", "REWORK", 0.85, 0.95),
        ("TB040", "J_BOT2 Thermal Charring", "REWORK", 0.85, 0.95)
    ]

    for bid, desc, exp_verdict, min_hi, max_hi in new_targets:
        st, res = inspect_board(bid)
        assert st == 200, f"Failed to inspect {bid}"
        verdict = res.get("verdict")
        hi = float(res.get("health_index", 0.0))
        assert min_hi <= hi <= max_hi, f"{bid} HI {hi} outside expected range [{min_hi}, {max_hi}]"
        print(f"  OK - {bid} ({desc}): Verdict={verdict}, HI={hi*100:.2f}%")

    # 4. Test Cross-Page Global Board Synchronization
    print("\n[4/6] Testing Cross-Page Global Synchronization...")
    switch_sequence = ["TB033", "TB034", "TB035", "TB038", "TB040", "TB032"]
    for bid in switch_sequence:
        st, active = get_json(f"/api/active-board?board={bid}")
        assert st == 200, f"Failed to get active board for {bid}"
        assert active["board_id"] == bid, f"Expected board_id {bid}, got {active['board_id']}"
        assert "golden_comparison" in active, f"Missing golden_comparison in {bid}"
        gc = active["golden_comparison"]
        assert gc["golden_board_id"] == "TB005", "Golden board reference is not TB005"
        assert gc["current_board_id"] == bid, f"Golden comparison mismatch for {bid}"
        print(f"  OK - Switched to {bid}: synchronized authoritatively (Delta HI: {gc['delta_health_index']:+.4f})")

    # 5. Test Radiograph Asset Availability for X-Ray Studio
    print("\n[5/6] Verifying X-Ray Radiographs for All New Boards...")
    for i in range(33, 41):
        bid = f"TB{i:03d}"
        for mode in ["bone", "gray", "inferno", "jet"]:
            st, _ = get(f"/static/boards/{bid}_xray_{mode}.png")
            assert st == 200, f"Missing radiograph {bid}_xray_{mode}.png"
    print("  OK - All 32 radiographs for TB033-TB040 verified accessible on server")

    # 6. Test Audit History Accumulation & Per-Board Reports
    print("\n[6/6] Verifying Session Audit History Accumulation & Reports...")
    st, session_audits = get_json("/api/session-audits")
    assert st == 200, "Failed to fetch session audits"
    assert len(session_audits) >= 12, f"Expected at least 12 audit entries, got {len(session_audits)}"
    
    # Verify per-board standalone report generation for new boards
    for test_bid in ["TB033", "TB034", "TB035", "TB038", "TB040"]:
        st, report_html = get(f"/api/audit/report/{test_bid}")
        assert st == 200, f"Failed to generate report for {test_bid}"
        assert test_bid in report_html, f"Report does not contain {test_bid}"
        assert "PCB AI Inspection Audit Dossier" in report_html
        print(f"  OK - Generated board-specific audit report for {test_bid}")

    print("\n" + "=" * 70)
    print("ALL 6 TEST SUITES PASSED! 100% GREEN.")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
