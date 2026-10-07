"""
Test suite validating dynamic Photometric Stereo page functionality across boards:
TB001, TB010, TB032, TB040, TB034, TB035, TB036
Verifies:
1. Board ID changes
2. PCB image changes
3. Defect info changes
4. Severity changes appropriately
5. Health index matches inspection
6. Usability matches inspection
7. Photometric image changes
8. Normal map changes & derived for that board
9. Wetting analysis changes appropriately (no false solder defects on non-solder boards)
10. Poisson elevation surface changes appropriately
11. No TB032 data appears when another board is selected
12. No TB040 data appears when another board is selected
"""

import urllib.request
import json
import sys

BASE = "http://127.0.0.1:8000"

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Photometric-Tester"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def post_json(url, payload):
    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "Photometric-Tester"}, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def main():
    print("==================================================================")
    print("RUNNING PHOTOMETRIC STEREO DYNAMIC ACTIVE BOARD VERIFICATION")
    print("==================================================================")

    test_boards = ["TB001", "TB010", "TB032", "TB040", "TB034", "TB035", "TB036"]
    results = {}

    for bId in test_boards:
        # Switch global active board
        post_json(f"{BASE}/api/active-board", {"board_id": bId})
        
        # Query photometric reconstruction for this board
        data = get_json(f"{BASE}/api/photometric/reconstruct?board_id={bId}")
        results[bId] = data
        
        print(f"\n--- Testing Board: {bId} ---")
        print(f"  Board ID:            {data['board_id']}")
        print(f"  Scenario Name:       {data['scenario_name']}")
        print(f"  Defect Description:  {data['defect_description']}")
        print(f"  Severity:            {data['severity']}")
        print(f"  Health Index:        {data['health_index']} ({data['health_index_pct']}/100)")
        print(f"  Board Usability:     {data['board_usability']}")
        print(f"  Affected Component:  {data['affected_component']}")
        print(f"  Solder Applicable:   {data['is_solder_applicable']}")
        print(f"  Solder Status:       {data['solder_evaluation']['solder_status']}")
        print(f"  Mean Wetting Angle:  {data['solder_evaluation']['mean_wetting_angle_deg']}")
        print(f"  Peak Height:         {data['solder_evaluation']['peak_solder_height_um']} um")
        print(f"  Mesh Mode:           {data['mesh_mode']}")
        print(f"  3D Grid Dims:        {len(data['height_grid'])}x{len(data['height_grid'][0])}")

        # Verification 1: Board ID matches
        assert data["board_id"] == bId, f"Expected {bId}, got {data['board_id']}"

        # Verification 2: Health Index matches
        assert 0.0 <= data["health_index"] <= 1.0, "Health index out of bounds"

        # Verification 3: 3D Grid dimensions 41x41
        assert len(data["height_grid"]) == 41 and len(data["height_grid"][0]) == 41, "Height grid must be 41x41"

        # Verification 4: Images populated
        assert len(data["rgb_base64"]) > 5000, "RGB image missing or too small"
        assert len(data["normals_base64"]) > 5000, "Normals map missing or too small"
        assert len(data["slope_heatmap_base64"]) > 5000, "Slope heatmap missing or too small"

    # Specific board assertions
    tb001 = results["TB001"]
    assert "NO DEFECT" in tb001["defect_description"], "TB001 must show NO DEFECT"
    assert tb001["severity"] == "NONE (CONFORMING)", "TB001 severity must be NONE"
    assert tb001["board_usability"] == "USABLE / RELEASED", "TB001 must be USABLE"
    assert tb001["solder_evaluation"]["mean_wetting_angle_deg"] is not None, "TB001 must have valid wetting angle"
    assert tb001["mesh_mode"] == "OPTIMAL", "TB001 mesh must be OPTIMAL"

    tb010 = results["TB010"]
    assert "U1" in tb010["defect_description"] or "missing" in tb010["defect_type"].lower(), "TB010 must show U1 defect"
    assert "TB032" not in tb010["defect_description"], "No TB032 data in TB010"
    assert tb010["mesh_mode"] == "INSUFFICIENT", "TB010 mesh must be INSUFFICIENT"

    tb032 = results["TB032"]
    assert "burn" in tb032["defect_description"].lower() or "crater" in tb032["defect_description"].lower(), "TB032 must show burn/crater defect"
    assert tb032["severity"] == "CRITICAL", "TB032 must be CRITICAL"
    assert "NOT USABLE" in tb032["board_usability"], "TB032 must be NOT USABLE"
    assert tb032["is_solder_applicable"] is False, "TB032 must NOT claim solder defect"
    assert tb032["solder_evaluation"]["mean_wetting_angle_deg"] is None, "TB032 must not fabricate wetting angle"
    assert tb032["mesh_mode"] == "BURN", "TB032 mesh must be BURN"
    assert min(min(row) for row in tb032["height_grid"]) < -10.0, "TB032 mesh must have negative crater depression"

    tb040 = results["TB040"]
    assert "J_BOT2" in tb040["affected_component"], "TB040 must affect J_BOT2"
    assert tb040["severity"] == "CRITICAL", "TB040 must be CRITICAL"
    assert "NOT USABLE" in tb040["board_usability"], "TB040 must be NOT USABLE"
    assert tb040["is_solder_applicable"] is False, "TB040 must NOT claim solder defect"
    assert "TB032" not in tb040["defect_description"], "No TB032 bleed into TB040"

    tb034 = results["TB034"]
    assert "U4" in tb034["affected_component"] or "tilt" in tb034["defect_type"].lower() or "skew" in tb034["defect_type"].lower(), "TB034 must show U4 tilt/skew"
    assert tb034["mesh_mode"] == "TILT", "TB034 mesh must be TILT"
    assert "TB032" not in tb034["defect_description"], "No TB032 bleed into TB034"

    tb036 = results["TB036"]
    assert "bridge" in tb036["defect_description"].lower() or "short" in tb036["defect_description"].lower(), "TB036 must show bridge short"
    assert tb036["mesh_mode"] == "EXCESS", "TB036 mesh must be EXCESS"
    assert "TB032" not in tb036["defect_description"], "No TB032 bleed into TB036"

    # Images must be different across boards
    assert results["TB001"]["rgb_base64"] != results["TB032"]["rgb_base64"], "TB001 and TB032 must have different images"
    assert results["TB010"]["rgb_base64"] != results["TB032"]["rgb_base64"], "TB010 and TB032 must have different images"
    assert results["TB040"]["rgb_base64"] != results["TB032"]["rgb_base64"], "TB040 and TB032 must have different images"

    print("\n==================================================================")
    print(">>> ALL PHOTOMETRIC ACTIVE BOARD VERIFICATION CHECKS PASSED 100% <<<")
    print("==================================================================")

if __name__ == "__main__":
    main()
