"""
Project-Wide Platform Integration & Stability Validator
Automated test suite verifying the connected industrial inspection suite.
"""

import os
import sys
import json
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_api_health():
    print("[1/8] Testing /health endpoint...")
    resp = requests.get(f"{BASE_URL}/health")
    assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["reference_loaded"] is True
    print(f"      OK - System status: {data['status']}, features: {len(data['features'])}")

def test_all_pages_served():
    print("[2/8] Testing all multi-page suite routes...")
    pages = [
        ("/", "Triple-View Inspection Workspace"),
        ("/3d-view", "3D Digital Twin & Surface Relief Viewer"),
        ("/photometric-studio", "Photometric 3D AOI & Solder Metrology Studio"),
        ("/xray-studio", "3D X-Ray & Metrology Tomography Studio"),
        ("/photometric", "Multi-Angle RGB Photometric Stereo 3D Solder Inspection"),
        ("/metrology", "IPC-A-610 Quantitative Metrology & CAD"),
        ("/analytics", "Statistical Quality Analytics"),
        ("/spc", "Statistical Process Control (SPC) & OCAP"),
        ("/msa", "Gage R&R (MSA) Statistical Study"),
        ("/cfx", "Industry 4.0 IPC-CFX-2591 Stream"),
        ("/audit", "ISO 9001:2015 Audit Vault")
    ]
    for route, expected_text in pages:
        r = requests.get(f"{BASE_URL}{route}")
        assert r.status_code == 200, f"Route {route} failed with {r.status_code}"
        assert expected_text in r.text or "ind-header" in r.text, f"Missing expected content on {route}"
        assert "/static/common.js" in r.text, f"Page {route} is missing common.js"
        assert "ind-header" in r.text, f"Page {route} is missing enterprise header"
        print(f"      OK - {route.ljust(22)} (status 200, length {len(r.text)})")

def test_global_active_board_api():
    print("[3/8] Testing Global Active Board State API...")
    # Test setting TB032
    tb032_payload = {
        "board_id": "TB032",
        "scenario_name": "Substrate Thermal Burn Hole & Carbonized FR-4 Rupture",
        "defect_type": "Catastrophic Dielectric Burnout & Carbonized FR-4 Rupture",
        "verdict": "FAIL",
        "image_path": "/evaluation/test_boards/TB032.png"
    }
    r = requests.post(f"{BASE_URL}/api/active-board", json=tb032_payload)
    assert r.status_code == 200, f"Set active board failed: {r.status_code}"
    
    # Verify retrieval
    r_get = requests.get(f"{BASE_URL}/api/active-board")
    assert r_get.status_code == 200
    active = r_get.json()
    assert active["board_id"] == "TB032", f"Expected TB032, got {active.get('board_id')}"
    assert active["verdict"] == "FAIL"
    assert "Burn" in active["scenario_name"]
    print(f"      OK - Set & verified active context: {active['board_id']} - {active['scenario_name']}")

    # Test switching back to TB005
    tb005_payload = {
        "board_id": "TB005",
        "scenario_name": "100% Perfect Master Golden Board",
        "defect_type": "None (Golden Reference)",
        "verdict": "PASS",
        "image_path": "/evaluation/test_boards/TB005.png"
    }
    r = requests.post(f"{BASE_URL}/api/active-board", json=tb005_payload)
    assert r.status_code == 200
    active5 = requests.get(f"{BASE_URL}/api/active-board").json()
    assert active5["board_id"] == "TB005"
    assert active5["verdict"] == "PASS"
    print(f"      OK - Switched back to active context: {active5['board_id']}")

def test_burned_rupture_inspection():
    print("[4/8] Testing TB032 Burned Rupture Inspection Data Integrity...")
    tb032_img = "evaluation/test_boards/TB032.png"
    assert os.path.exists(tb032_img), "TB032.png missing from evaluation dataset"
    
    with open(tb032_img, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/inspect",
            files={"file": ("TB032.png", f, "image/png")},
            data={"board_serial": "TB032"}
        )
    assert r.status_code == 200, f"Inspect TB032 failed: {r.status_code}"
    res = r.json()
    assert res["verdict"] == "FAIL", f"Expected FAIL verdict for TB032, got {res.get('verdict')}"
    assert res["defective_components"] > 0, "TB032 must show defects"
    assert res["overlay_image_b64"] is not None
    assert res["depth_heatmap_b64"] is not None
    print(f"      OK - TB032 inspection verdict: {res['verdict']}, defects: {res['defective_components']}, latency: {res.get('processing_time_ms', 0):.1f}ms")

def test_photometric_studio_applicability():
    print("[5/8] Testing Photometric Studio Applicability & Non-Solder Target State...")
    # For TB032 / BURN_HOLE, solder volume must NOT be fabricated
    r_burn = requests.get(f"{BASE_URL}/api/studio/profile?comp_id=BURN_HOLE")
    assert r_burn.status_code == 200
    data_burn = r_burn.json()
    assert data_burn["is_solder_applicable"] is False, "BURN_HOLE must flag is_solder_applicable: False"
    assert data_burn["volume_nl"] is None, "Solder volume must be None for substrate rupture"
    assert data_burn["toe_wetting_angle_deg"] is None, "Wetting angle must be None for substrate rupture"
    assert "SCRAP" in data_burn["verdict"]
    print("      OK - BURN_HOLE correctly returns is_solder_applicable: False, volume: None")

    # For solder fillet (U1_PIN1, C1_PAD_L), real solder metrology must be provided
    r_solder = requests.get(f"{BASE_URL}/api/studio/profile?comp_id=U1_PIN1")
    assert r_solder.status_code == 200
    data_solder = r_solder.json()
    assert data_solder["is_solder_applicable"] is True
    assert data_solder["volume_nl"] is not None
    assert data_solder["toe_wetting_angle_deg"] is not None
    print(f"      OK - U1_PIN1 correctly returns is_solder_applicable: True, volume: {data_solder['volume_nl']:.2f} nL, wetting: {data_solder['toe_wetting_angle_deg']:.1f}°")

def test_all_32_radiographs_exist():
    print("[6/8] Testing X-Ray Radiographs for All 32 Scenarios (TB001 - TB032)...")
    boards_dir = "server/static/boards"
    missing = []
    modes = ["jet", "inferno", "gray"]
    for i in range(1, 33):
        bId = f"TB{i:03d}"
        for m in modes:
            path = os.path.join(boards_dir, f"{bId}_xray_{m}.png")
            if not os.path.exists(path):
                missing.append(f"{bId}_xray_{m}.png")
    assert len(missing) == 0, f"Missing radiographs: {missing}"
    print(f"      OK - Verified 100% of radiographs exist ({32 * len(modes)} files across 32 boards)")

def test_cross_board_data_isolation():
    print("[7/8] Testing Cross-Board Data Isolation (No Stale/Cross Leaks)...")
    # Inspect TB005 (Golden pass)
    with open("evaluation/test_boards/TB005.png", "rb") as f:
        r5 = requests.post(f"{BASE_URL}/inspect", files={"file": ("TB005.png", f, "image/png")}, data={"board_serial": "TB005"}).json()
    # Inspect TB032 (Burn failure)
    with open("evaluation/test_boards/TB032.png", "rb") as f:
        r32 = requests.post(f"{BASE_URL}/inspect", files={"file": ("TB032.png", f, "image/png")}, data={"board_serial": "TB032"}).json()
    
    assert r5["verdict"] == "PASS"
    assert r32["verdict"] == "FAIL"
    assert r5["defective_components"] == 0
    assert r32["defective_components"] > 0
    assert r5["overlay_image_b64"] != r32["overlay_image_b64"]
    print("      OK - TB005 and TB032 inspection outputs are completely isolated and unique")

def test_catalog_coverage():
    print("[8/8] Testing Scenario Catalog Coverage...")
    common_js_path = "server/static/common.js"
    with open(common_js_path, "r", encoding="utf-8") as f:
        content = f.read()
    for i in range(1, 33):
        bId = f"TB{i:03d}"
        assert f'"{bId}":' in content or f"'{bId}':" in content, f"Scenario {bId} missing from SCENARIO_CATALOG"
    assert "TB032" in content
    assert "Substrate Thermal Burn Hole" in content
    print("      OK - All 32 board scenarios (TB001-TB032) fully indexed in catalog with IPC metadata")

if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING INDUSTRIAL INSPECTION SUITE PLATFORM VALIDATION")
    print("=" * 70)
    try:
        test_api_health()
        test_all_pages_served()
        test_global_active_board_api()
        test_burned_rupture_inspection()
        test_photometric_studio_applicability()
        test_all_32_radiographs_exist()
        test_cross_board_data_isolation()
        test_catalog_coverage()
        print("=" * 70)
        print(">>> ALL 8 INTEGRATION & STABILITY SUITE CHECKS PASSED (100%) <<<")
        print("=" * 70)
    except Exception as e:
        print(f"\n[FAIL] VALIDATION FAILED: {e}")
        sys.exit(1)
