"""
Comprehensive End-to-End Test Suite for Scenario Selection, Image Payloads & Inspection Reliability
Validates Task 12 requirements:
1. Valid image payload
2. Invalid image payload (corrupted/non-image bytes)
3. Empty image payload (0 bytes)
4. Missing image (file parameter omitted)
5. Scenario selection (TB001 - TB031 all resolvable)
6. PASS scenario (TB005)
7. FAIL scenario (TB016, TB010, TB020)
8. Switching from PASS -> FAIL
9. Switching from FAIL -> PASS
10. Multiple rapid scenario changes
11. Inspection after scenario change
"""

import os
import sys
import pytest
import cv2
import numpy as np
from fastapi.testclient import TestClient

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from server.main import app, load_components_config, get_reference_data

client = TestClient(app)

@pytest.fixture(scope="module")
def valid_board_bytes():
    # Load TB005 as reference test bytes
    tb5_path = os.path.join(ROOT_DIR, "evaluation", "test_boards", "TB005.png")
    assert os.path.exists(tb5_path), "TB005.png must exist"
    with open(tb5_path, "rb") as f:
        return f.read()

@pytest.fixture(scope="module")
def tb016_board_bytes():
    tb16_path = os.path.join(ROOT_DIR, "evaluation", "test_boards", "TB016.png")
    assert os.path.exists(tb16_path), "TB016.png must exist"
    with open(tb16_path, "rb") as f:
        return f.read()

class TestImagePayloadsAndScenarios:

    def test_1_valid_image_payload(self, valid_board_bytes):
        resp = client.post(
            "/inspect",
            data={"board_serial": "TB005"},
            files={"file": ("TB005.png", valid_board_bytes, "image/png")}
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "verdict" in data
        assert "health_index" in data
        assert "overlay_image_b64" in data
        assert len(data["overlay_image_b64"]) > 50

    def test_2_invalid_image_payload(self):
        # Corrupted non-image bytes (e.g. 404 text string or random binary)
        invalid_bytes = b"<html><head><title>404 Not Found</title></head></html>"
        resp = client.post(
            "/inspect",
            data={"board_serial": "TB-CORRUPT"},
            files={"file": ("corrupt.png", invalid_bytes, "image/png")}
        )
        assert resp.status_code == 400
        data = resp.json()
        assert "invalid_image_payload" in str(data)

    def test_3_empty_image_payload(self):
        # 0 bytes file
        resp = client.post(
            "/inspect",
            data={"board_serial": "TB-EMPTY"},
            files={"file": ("empty.png", b"", "image/png")}
        )
        assert resp.status_code == 400
        data = resp.json()
        assert "empty_image_payload" in str(data)

    def test_4_missing_image(self):
        # Request with file omitted entirely
        resp = client.post(
            "/inspect",
            data={"board_serial": "TB-NOFILE"}
        )
        assert resp.status_code == 422 # FastAPI validation failure for missing required file parameter

    def test_5_all_scenarios_exist_and_accessible(self):
        # Verify all 31 scenarios are in evaluation/test_boards/ and return 200 OK from static mount
        for i in range(1, 32):
            board_id = f"TB{i:03d}"
            resp = client.get(f"/evaluation/test_boards/{board_id}.png")
            assert resp.status_code == 200, f"Scenario {board_id}.png should return 200 from static route"
            assert len(resp.content) > 1000, f"Scenario {board_id}.png content should not be empty"

    def test_6_pass_scenario(self, valid_board_bytes):
        resp = client.post(
            "/inspect",
            data={"board_serial": "TB005"},
            files={"file": ("TB005.png", valid_board_bytes, "image/png")}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["verdict"] == "PASS"
        assert data["defective_components"] == 0

    def test_7_fail_scenario_tb016(self, tb016_board_bytes):
        resp = client.post(
            "/inspect",
            data={"board_serial": "TB016"},
            files={"file": ("TB016.png", tb016_board_bytes, "image/png")}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["verdict"] in ["REWORK", "FAIL"]
        assert data["defective_components"] >= 1
        defective_ids = [c["id"] for c in data["per_component_results"] if c.get("is_defective") or c.get("is_missing")]
        assert "J_BOT1" in defective_ids

    def test_8_switching_pass_to_fail(self, valid_board_bytes, tb016_board_bytes):
        # 1. Run PASS (TB005)
        resp1 = client.post(
            "/inspect",
            data={"board_serial": "TB005"},
            files={"file": ("TB005.png", valid_board_bytes, "image/png")}
        )
        assert resp1.status_code == 200
        assert resp1.json()["verdict"] == "PASS"

        # 2. Switch to FAIL (TB016)
        resp2 = client.post(
            "/inspect",
            data={"board_serial": "TB016"},
            files={"file": ("TB016.png", tb016_board_bytes, "image/png")}
        )
        assert resp2.status_code == 200
        assert resp2.json()["verdict"] in ["REWORK", "FAIL"]

    def test_9_switching_fail_to_pass(self, valid_board_bytes, tb016_board_bytes):
        # 1. Run FAIL (TB016)
        resp1 = client.post(
            "/inspect",
            data={"board_serial": "TB016"},
            files={"file": ("TB016.png", tb016_board_bytes, "image/png")}
        )
        assert resp1.status_code == 200
        assert resp1.json()["verdict"] in ["REWORK", "FAIL"]

        # 2. Switch to PASS (TB005)
        resp2 = client.post(
            "/inspect",
            data={"board_serial": "TB005"},
            files={"file": ("TB005.png", valid_board_bytes, "image/png")}
        )
        assert resp2.status_code == 200
        assert resp2.json()["verdict"] == "PASS"

    def test_10_multiple_rapid_scenario_inspections(self):
        # Sequentially inspect 5 different scenarios to simulate rapid switching
        scenarios = ["TB001", "TB005", "TB010", "TB016", "TB020"]
        for board_id in scenarios:
            board_path = os.path.join(ROOT_DIR, "evaluation", "test_boards", f"{board_id}.png")
            with open(board_path, "rb") as f:
                board_bytes = f.read()
            resp = client.post(
                "/inspect",
                data={"board_serial": board_id},
                files={"file": (f"{board_id}.png", board_bytes, "image/png")}
            )
            assert resp.status_code == 200, f"Failed on {board_id}: {resp.text}"
            data = resp.json()
            assert "health_index" in data

    def test_11_inspection_after_scenario_change(self, tb016_board_bytes):
        # Select scenario TB016, then run inspection
        resp = client.post(
            "/inspect",
            data={"board_serial": "TB016"},
            files={"file": ("TB016.png", tb016_board_bytes, "image/png")}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["defective_components"] >= 1

    def test_12_burn_defect_scenario_tb032(self):
        # Severe substrate thermal burn scenario
        tb032_path = os.path.join(ROOT_DIR, "evaluation", "test_boards", "TB032.png")
        assert os.path.exists(tb032_path), "TB032.png must exist"
        with open(tb032_path, "rb") as f:
            board_bytes = f.read()

        resp = client.post(
            "/inspect",
            data={"board_serial": "TB032"},
            files={"file": ("TB032.png", board_bytes, "image/png")}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["verdict"] in ["REWORK", "FAIL"]
        assert data["defective_components"] >= 1

    def test_13_global_active_board_sync(self, valid_board_bytes):
        # 1. Test GET /api/active-board
        get_res = client.get("/api/active-board")
        assert get_res.status_code == 200
        active_data = get_res.json()
        assert "board_id" in active_data

        # 2. Inspect TB005 and verify active board updates
        insp_res = client.post(
            "/inspect",
            data={"board_serial": "TB005"},
            files={"file": ("TB005.png", valid_board_bytes, "image/png")}
        )
        assert insp_res.status_code == 200
        active_after = client.get("/api/active-board").json()
        assert active_after["board_id"] == "TB005"
        assert active_after["verdict"] == "PASS"

        # 3. Test POST /api/active-board
        post_res = client.post(
            "/api/active-board",
            json={"board_id": "TB032", "serial": "TB032", "verdict": "FAIL"}
        )
        assert post_res.status_code == 200
        assert client.get("/api/active-board").json()["board_id"] == "TB032"

