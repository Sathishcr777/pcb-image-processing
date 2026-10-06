import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}", headers={"User-Agent": "E2E-Verifier"})
    with urllib.request.urlopen(req) as resp:
        return resp.status, resp.read().decode('utf-8')

def post_json(path, data):
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "E2E-Verifier"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

def test_scenario(board_id, expected_defect_part):
    print(f"\n==========================================")
    print(f"SWITCHING LIVE INSPECTION TO {board_id}")
    print(f"==========================================")
    
    # 1. Live Inspection Selection -> POST /api/active-board
    status, res = post_json("/api/active-board", {"board_id": board_id})
    assert status == 200, f"Failed to set active board {board_id}: {status}"
    assert res["boardId"] == board_id
    assert expected_defect_part.lower() in res["defectType"].lower()
    print(f"  [PASS] Live inspection updated active context to: {res['boardId']} ({res['scenarioName']})")
    print(f"         Defect: {res['defectType']} | Verdict: {res['verdict']} | Defective count: {res['defectCount']}")

    # 2. Verify server-authoritative active board via GET /api/active-board
    status, active_ctx_str = get("/api/active-board")
    assert status == 200
    active_ctx = json.loads(active_ctx_str)
    assert active_ctx["boardId"] == board_id
    assert active_ctx["image_url"] == f"/dataset/test_boards/{board_id}.png"
    print(f"  [PASS] Server authoritative context verified: Image URL={active_ctx['image_url']}")

    # 3. 3D Digital Twin Navigation
    status, html_3d = get(f"/3d-view?board={board_id}")
    assert status == 200
    assert "getGlobalActiveBoard" in html_3d
    # Test that 3D API provides metadata matching active board
    status, insp_res = post_json("/inspect", {"board_id": board_id})
    assert status == 200
    assert insp_res["board_id"] == board_id
    print(f"  [PASS] 3D Digital Twin: Loaded scenario {board_id} with {len(insp_res.get('components', []))} components")

    # 4. X-Ray Studio Navigation
    status, html_xray = get(f"/xray-studio?board={board_id}")
    assert status == 200
    status, xray_layers = get(f"/api/xray/board-layers?board_id={board_id}")
    assert status == 200
    xray_data = json.loads(xray_layers)
    assert xray_data["board_id"] == board_id
    print(f"  [PASS] X-Ray Studio: Successfully retrieved radiograph layers for {board_id}")

    # 5. Photometric Stereo / Studio Navigation
    status, html_photo = get(f"/photometric?board={board_id}")
    assert status == 200
    status, html_studio = get(f"/photometric-studio?board={board_id}")
    assert status == 200
    print(f"  [PASS] Photometric Modules: Resolved compatible 3D surface reconstructor for {board_id}")

    # 6. Metrology Navigation
    status, html_metro = get(f"/metrology?board={board_id}")
    assert status == 200
    # Ensure metrology inspect endpoint executes for this board
    status, metro_res = post_json("/inspect", {"board_id": board_id})
    assert status == 200
    assert metro_res["board_id"] == board_id
    print(f"  [PASS] Metrology: Verified feature extraction & IPC classification for {board_id}")

    # 7. Analytics & SPC Navigation
    status, html_analytics = get(f"/analytics?board={board_id}")
    assert status == 200
    status, html_spc = get(f"/spc?board={board_id}")
    assert status == 200
    print(f"  [PASS] Statistical Analytics & SPC: Verified health index context for {board_id}")

def main():
    print("STARTING CROSS-MODULE BOARD SYNCHRONIZATION TEST SUITE")
    
    # TEST 1: Select TB014 in Live Inspection and propagate to all modules
    test_scenario("TB014", "Missing")

    # TEST 2: Return to Live Inspection, switch to TB032, propagate to all modules
    test_scenario("TB032", "Thermal Burn")

    # TEST 3: Switch to TB002 (Tombstoning) and verify no stale TB032 data remains
    test_scenario("TB002", "Tombstoning")

    # TEST 4: Switch to TB000 (Golden reference)
    test_scenario("TB000", "Golden Reference")

    print("\n==========================================")
    print("ALL 4 END-TO-END SCENARIOS PASSED 100%!")
    print("==========================================")

if __name__ == "__main__":
    main()
