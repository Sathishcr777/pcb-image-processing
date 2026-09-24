import pytest
import numpy as np
from fastapi.testclient import TestClient
from server.pipeline.xray_engine import XRayEngine
from server.main import app

@pytest.fixture
def xray():
    return XRayEngine(board_width=600, board_height=400)

@pytest.fixture
def client():
    return TestClient(app)

def test_xray_full_board_radiograph(xray):
    res = xray.get_full_board_radiograph(colormap="bone")
    assert "image_base64" in res
    assert res["image_base64"].startswith("data:image/jpeg;base64,")
    assert res["layers_count"] == 16
    assert res["board_thickness_um"] == 1600.0
    assert res["ipc_axi_status"] in ["PASS_CLASS_3", "ACCEPTABLE_CLASS_2", "REJECT_DEFECT"]
    assert "bga_summary" in res
    assert "qfn_summary" in res
    assert "tht_summary" in res

def test_xray_z_slice_laminography(xray):
    # Test top, middle BGA layer, inner copper, and bottom layer
    for depth in [0.0, 350.0, 750.0, 1500.0]:
        slice_res = xray.get_z_slice(depth_um=depth, colormap="inferno")
        assert "image_base64" in slice_res
        assert slice_res["image_base64"].startswith("data:image/jpeg;base64,")
        assert "layer_name" in slice_res
        assert slice_res["width"] == 600
        assert slice_res["height"] == 400

def test_bga_void_analysis(xray):
    bga = xray.analyze_bga_voids()
    assert bga["total_balls"] == 64
    assert len(bga["balls"]) == 64
    assert bga["defect_count"] >= 1
    assert bga["warning_count"] >= 1
    assert bga["pass_count"] >= 50
    assert bga["max_void_pct"] > 25.0
    
    # Verify defect ball has correct reason
    defect_balls = [b for b in bga["balls"] if b["status"] == "DEFECT"]
    assert len(defect_balls) >= 1
    assert any("EXCESSIVE_VOIDING" in b["defect_reason"] for b in defect_balls)

def test_qfn_thermal_pad(xray):
    qfn = xray.analyze_qfn_thermal_pad()
    assert "void_percentage" in qfn
    assert qfn["void_percentage"] > 0.0
    assert qfn["status"] in ["PASS", "WARNING", "DEFECT"]
    assert qfn["roi_image_base64"].startswith("data:image/jpeg;base64,")

def test_tht_barrel_fill(xray):
    tht = xray.analyze_tht_barrel_fill()
    assert tht["total_pins"] == 4
    # Pin 3 is configured as < 75% fill defect
    pin3 = next(p for p in tht["pins"] if p["pin_id"] == "PIN_3")
    assert pin3["status"] == "DEFECT"
    assert pin3["fill_percentage"] == 62.0

def test_xray_api_routes(client):
    r_studio = client.get("/xray-studio")
    assert r_studio.status_code == 200

    r_board = client.get("/api/xray/full-board?colormap=inferno")
    assert r_board.status_code == 200
    assert "image_base64" in r_board.json()

    r_slice = client.get("/api/xray/slice?depth_um=350&colormap=bone")
    assert r_slice.status_code == 200
    assert "layer_name" in r_slice.json()

    r_bga = client.get("/api/xray/bga-matrix")
    assert r_bga.status_code == 200
    assert r_bga.json()["total_balls"] == 64

    r_qfn = client.get("/api/xray/qfn")
    assert r_qfn.status_code == 200

    r_tht = client.get("/api/xray/tht")
    assert r_tht.status_code == 200

    r_3d = client.get("/3d-view")
    assert r_3d.status_code == 200
