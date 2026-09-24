import numpy as np
import pytest
from server.pipeline.solder_profiler import SolderProfilerEngine

def test_extract_cross_section_profile():
    profiler = SolderProfilerEngine(px_to_um=2.5)
    
    # Create 64x64 height map representing a concave solder fillet
    h, w = 64, 64
    y, x = np.ogrid[-h//2:h//2, -w//2:w//2]
    r = np.sqrt(x*x + y*y) / float(w//2)
    z_map = 140.0 * (1.0 - np.clip(r, 0.0, 1.0)**1.5)

    profile = profiler.extract_cross_section_profile(z_map, slice_fraction=0.5, axis="horizontal")

    assert "x_coords_um" in profile
    assert "z_measured_um" in profile
    assert "z_ideal_um" in profile
    assert "toe_wetting_angle_deg" in profile
    assert len(profile["x_coords_um"]) == w
    assert profile["peak_height_um"] > 100.0

def test_solder_volume_computation():
    profiler = SolderProfilerEngine(px_to_um=2.5)
    
    # 50x50 height map with uniform 100 um thickness
    z_map = np.full((50, 50), 100.0, dtype=np.float32)
    vol_res = profiler.compute_solder_volume(z_map)

    assert "volume_nl" in vol_res
    assert vol_res["volume_nl"] > 0.0
    assert vol_res["wetted_area_coverage_pct"] == 100.0

def test_lead_coplanarity():
    profiler = SolderProfilerEngine()
    
    # Normal coplanar leads
    res_pass = profiler.compute_lead_coplanarity([130.0, 135.0, 140.0, 132.0])
    assert res_pass["is_coplanar"] == True
    assert res_pass["coplanarity_delta_um"] == 10.0

    # Lifted lead (tombstoned / pin lift)
    res_fail = profiler.compute_lead_coplanarity([130.0, 220.0, 135.0])
    assert res_fail["is_coplanar"] == False
    assert res_fail["coplanarity_delta_um"] == 90.0

def test_wavefront_obj_generation():
    profiler = SolderProfilerEngine(px_to_um=2.5)
    z_map = np.zeros((20, 20), dtype=np.float32)
    obj_str = profiler.generate_wavefront_obj(z_map, step=5)

    assert "v " in obj_str
    assert "f " in obj_str
