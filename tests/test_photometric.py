import numpy as np
import pytest
from server.pipeline.photometric_stereo import PhotometricStereoEngine

def test_photometric_normal_recovery():
    engine = PhotometricStereoEngine()
    
    # Create test 3-channel image (100x100)
    dummy_rgb = np.zeros((100, 100, 3), dtype=np.uint8)
    dummy_rgb[:, :] = (120, 150, 180)

    normals_vis, albedo, slopes, height = engine.reconstruct_surface_normals(dummy_rgb)

    assert normals_vis.shape == (100, 100, 3)
    assert albedo.shape == (100, 100)
    assert slopes.shape == (100, 100)
    assert height.shape == (100, 100)
    assert np.all(slopes >= 0.0)
    assert np.all(slopes <= 90.0)

def test_poisson_3d_height_integration():
    engine = PhotometricStereoEngine()
    # Create normal vectors representing a hemisphere
    h, w = 64, 64
    y_coords = np.linspace(-1.0, 1.0, h)
    x_coords = np.linspace(-1.0, 1.0, w)
    X, Y = np.meshgrid(x_coords, y_coords)
    
    R = np.sqrt(X*X + Y*Y)
    R = np.clip(R, 0.0, 0.95)

    nx = X * 0.6
    ny = Y * 0.6
    nz = np.sqrt(np.maximum(0.01, 1.0 - nx*nx - ny*ny))

    normals = np.stack([nx, ny, nz], axis=2)
    height = engine.integrate_poisson_height(normals)

    assert height.shape == (64, 64)
    assert np.max(height) > np.min(height)

def test_solder_joint_classification():
    engine = PhotometricStereoEngine()
    
    # Test optimal wetting
    opt_roi = np.zeros((50, 50, 3), dtype=np.uint8)
    opt_roi[:, :] = (140, 180, 160)
    res = engine.classify_solder_joint(opt_roi)

    assert "mean_wetting_angle_deg" in res
    assert "ipc_classification" in res
    assert "solder_status" in res
