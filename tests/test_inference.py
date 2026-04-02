"""Tests for the NumPy inference engine."""

import os
import numpy as np
import pytest


@pytest.fixture
def weights_path():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        "rul_model", "weights", "rul_model_weights.npz")
    if not os.path.exists(path):
        pytest.skip("Model weights not found — run training and export first")
    return path


def test_numpy_model_loads(weights_path):
    """Model loads without error."""
    from inference.numpy_inference import NumpyRULModel
    model = NumpyRULModel(weights_path)
    assert model.y_max > 0


def test_numpy_model_predict_single(weights_path):
    """Single window prediction returns a scalar."""
    from inference.numpy_inference import NumpyRULModel
    model = NumpyRULModel(weights_path)

    x = np.random.randn(8192).astype(np.float32)
    result = model.predict_hours(x)
    assert isinstance(result, float)
    assert result >= 0


def test_numpy_model_predict_batch(weights_path):
    """Batch prediction returns correct shape."""
    from inference.numpy_inference import NumpyRULModel
    model = NumpyRULModel(weights_path)

    x = np.random.randn(5, 8192).astype(np.float32)
    result = model.predict_hours(x)
    assert len(result) == 5
    assert all(r >= 0 for r in result)


def test_numpy_matches_pytorch(weights_path):
    """NumPy inference matches PyTorch output within tolerance."""
    try:
        import torch
        from rul_model.model import RULModel
    except ImportError:
        pytest.skip("PyTorch not available")

    from inference.numpy_inference import NumpyRULModel

    # Load both models
    np_model = NumpyRULModel(weights_path)

    pt_model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                  "rul_model", "weights", "best_model.pt")
    if not os.path.exists(pt_model_path):
        pytest.skip("PyTorch model not found")

    pt_model = RULModel()
    ckpt = torch.load(pt_model_path, map_location="cpu", weights_only=False)
    pt_model.load_state_dict(ckpt["model_state_dict"])
    pt_model.eval()

    # Test input
    x_np = np.random.randn(8192).astype(np.float32)
    x_pt = torch.from_numpy(x_np).unsqueeze(0)

    np_out = np_model.predict_normalized(x_np)
    with torch.no_grad():
        pt_out = pt_model(x_pt).item()

    assert abs(np_out - pt_out) < 1e-4, \
        f"NumPy={np_out:.6f}, PyTorch={pt_out:.6f}, diff={abs(np_out-pt_out):.6f}"
