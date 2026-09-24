"""
Automated Test Suite for PCB AI Inspection System
Tests Aligner, 2D Detector, Depth Detector, Health Index, Visualizer, Logger, and FastAPI Endpoints.
"""

import pytest
import numpy as np
import cv2
import os
import sys
import json
import tempfile
from fastapi.testclient import TestClient

# Add project root to sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from server.pipeline.aligner import PCBAligner
from server.pipeline.detector_2d import Detector2D
from server.pipeline.detector_depth import DetectorDepth
from server.pipeline.health_index import HealthIndexCalculator
from server.pipeline.visualizer import PCBVisualizer
from server.audit.logger import AuditLogger


@pytest.fixture
def dummy_images():
    """Generates synthetic 100x100 BGR test and reference images."""
    ref_img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(ref_img, (20, 20), (80, 80), (200, 200, 200), -1)
    
    test_img = ref_img.copy()
    cv2.circle(test_img, (50, 50), 10, (50, 50, 50), -1)
    return test_img, ref_img


@pytest.fixture
def dummy_components():
    return [
        {
            "id": "U1",
            "name": "Main IC",
            "type": "IC",
            "bbox_xywh": [20, 20, 30, 30],
            "weight": 5.0,
            "depth_check": True,
            "tilt_check": True,
            "tombstone_check": False
        },
        {
            "id": "C1",
            "name": "Cap C1",
            "type": "Capacitor",
            "bbox_xywh": [50, 50, 20, 20],
            "weight": 2.0,
            "depth_check": True,
            "tilt_check": True,
            "tombstone_check": True
        }
    ]


class TestPCBAligner:
    def test_align_identical_images(self, dummy_images):
        _, ref_img = dummy_images
        aligner = PCBAligner()
        aligned, quality, H, stats = aligner.align(ref_img, ref_img)
        assert aligned.shape == ref_img.shape
        assert quality >= 0.35
        assert H.shape == (3, 3)
        assert "optical_quality" in stats

    def test_align_grayscale(self):
        ref_gray = np.zeros((100, 100), dtype=np.uint8)
        test_gray = ref_gray.copy()
        aligner = PCBAligner()
        aligned, quality, H, stats = aligner.align(test_gray, ref_gray)
        assert quality > 0.0
        assert H.shape == (3, 3)


class TestDetector2D:
    def test_detect_components(self, dummy_images, dummy_components):
        test_img, ref_img = dummy_images
        detector = Detector2D()
        results = detector.detect(test_img, ref_img, dummy_components)
        assert "U1" in results
        assert "C1" in results
        assert "ssim_score" in results["U1"]
        assert "is_missing" in results["U1"]

    def test_detect_small_roi_safety(self, dummy_images):
        test_img, ref_img = dummy_images
        tiny_comps = [{"id": "T1", "name": "Tiny", "bbox_xywh": [1, 1, 3, 3]}]
        detector = Detector2D()
        results = detector.detect(test_img, ref_img, tiny_comps)
        assert results["T1"]["is_missing"] is True


class TestDetectorDepth:
    def test_estimate_depth(self, dummy_images):
        test_img, _ = dummy_images
        detector = DetectorDepth(use_model=False)
        depth_map = detector.estimate_depth(test_img)
        assert depth_map.shape == test_img.shape[:2]
        assert depth_map.min() >= -1e-6
        assert depth_map.max() <= 1.0 + 1e-6

    def test_inspect_depth(self, dummy_images, dummy_components):
        test_img, ref_img = dummy_images
        detector = DetectorDepth(use_model=False)
        t_depth = detector.estimate_depth(test_img)
        r_depth = detector.estimate_depth(ref_img)
        res, stats = detector.inspect(t_depth, r_depth, dummy_components)
        assert "U1" in res
        assert "height_flag" in res["U1"]
        assert "tilt_flag" in res["U1"]
        assert "tombstone_flag" in res["U1"]
        assert "test_board_slant" in stats


class TestHealthIndexCalculator:
    def test_compute_hi(self, dummy_components):
        calc = HealthIndexCalculator()
        res_2d = {
            "U1": {"presence_score": 1.0, "is_missing": False, "ssim_score": 0.98},
            "C1": {"presence_score": 0.2, "is_missing": True, "ssim_score": 0.35}
        }
        res_depth = {
            "U1": {"height_penalty": 0.0, "height_flag": False, "tilt_flag": False, "tombstone_flag": False},
            "C1": {"height_penalty": 0.0, "height_flag": False, "tilt_flag": False, "tombstone_flag": False}
        }
        hi_out = calc.compute(dummy_components, res_2d, res_depth)
        assert 0.0 <= hi_out["health_index"] <= 1.0
        assert hi_out["defective_components"] == 1
        assert hi_out["verdict"] in ["PASS", "REWORK", "FAIL"]

    def test_dpmo_calculation(self):
        dpmo = HealthIndexCalculator.calculate_dpmo(5, 10, 10)
        assert dpmo == 50000.0


class TestPCBVisualizer:
    def test_draw_overlay(self, dummy_images):
        test_img, _ = dummy_images
        viz = PCBVisualizer()
        hi_results = {
            "health_index": 0.92,
            "verdict": "REWORK",
            "components": [
                {
                    "id": "U1",
                    "status": "PASS",
                    "bbox_px": [20, 20, 30, 30]
                },
                {
                    "id": "C1",
                    "status": "MISSING",
                    "bbox_px": [50, 50, 20, 20]
                }
            ]
        }
        overlay = viz.draw_overlay(test_img, hi_results, metrology_results=[], processing_ms=15.5)
        assert overlay.shape == test_img.shape
        b64_str = viz.to_base64(overlay)
        assert len(b64_str) > 100


class TestAuditLogger:
    def test_write_and_read_audit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            dummy_bytes = b"fake_image_bytes"
            hi_results = {
                "health_index": 0.95,
                "verdict": "PASS",
                "total_components": 2,
                "defective_components": 0,
                "components": [
                    {"id": "U1", "is_missing": False, "tombstone_flag": False, "tilt_flag": False, "height_flag": False},
                    {"id": "C1", "is_missing": False, "tombstone_flag": False, "tilt_flag": False, "height_flag": False}
                ]
            }
            rec = logger.write_record(dummy_bytes, hi_results, 0.99, 12.4, "SN-TEST-001")
            assert rec["board_serial"] == "SN-TEST-001"
            assert rec["verdict"] == "PASS"

            stats = logger.get_summary_stats()
            assert stats["boards_inspected"] == 1
            assert stats["pass_count"] == 1
            assert stats["session_fpy"] == 1.0


def test_validate_board_serial_accepts_expected_format():
    from server.main import validate_board_serial

    assert validate_board_serial("TB-001") == "TB-001"


def test_health_endpoint_reports_config():
    from server.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert "reference_loaded" in payload
    assert "depth_engine_type" in payload


def test_inspect_returns_payload_with_mocked_pipeline(monkeypatch):
    from server import main

    test_image = np.zeros((64, 64, 3), dtype=np.uint8)
    test_image[16:48, 16:48] = 255
    success, encoded = cv2.imencode(".png", test_image)
    assert success

    components = [
        {
            "id": "U1",
            "name": "Main IC",
            "bbox_xywh": [8, 8, 24, 24],
            "weight": 1.0,
            "depth_check": True,
            "tilt_check": True,
            "tombstone_check": True,
        }
    ]

    monkeypatch.setattr(main, "get_reference_data", lambda: (test_image.copy(), np.zeros((64, 64), dtype=np.float32), components))
    monkeypatch.setattr(main.aligner, "align", lambda test_img, ref_img: (ref_img.copy(), 0.98, np.eye(3), {"inlier_count": 100, "total_matches": 100}))
    monkeypatch.setattr(main.detector_2d, "detect", lambda aligned, ref, comps: {"U1": {"presence_score": 1.0, "is_missing": False, "ssim_score": 0.99}})
    monkeypatch.setattr(main.detector_depth, "estimate_depth", lambda img: np.zeros((64, 64), dtype=np.float32))
    monkeypatch.setattr(main.detector_depth, "inspect", lambda test_depth, ref_depth, comps: ({"U1": {"height_penalty": 0.0, "height_flag": False, "tilt_flag": False, "tombstone_flag": False}}, {"test_board_slant": {}}))
    monkeypatch.setattr(main.visualizer, "draw_overlay", lambda img, hi_results, metrology, processing_ms: img)
    monkeypatch.setattr(main.visualizer, "draw_depth_heatmap", lambda img, depth: img)
    monkeypatch.setattr(main.visualizer, "to_base64", lambda img: "AAAA")
    monkeypatch.setattr(main.audit_logger, "write_record", lambda *args, **kwargs: {"record_id": "REC-1"})

    client = TestClient(main.app)
    response = client.post(
        "/inspect",
        data={"board_serial": "TB-001"},
        files={"file": ("board.png", encoded.tobytes(), "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["record_id"] == "REC-1"
    assert payload["verdict"] in {"PASS", "REWORK", "FAIL"}
    assert payload["overlay_image_b64"] == "AAAA"
