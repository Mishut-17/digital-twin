"""Tests for the data generation pipeline."""

import os
import numpy as np
import pytest

from data_generator.config import (
    LIFE_WEIGHT_BREAKPOINTS, SLOPE_WEIGHT_BREAKPOINTS,
    BEARING_LIFE_HOURS, WINDOW_SIZE,
)
from data_generator.build_rul_dataset import (
    interpolate_weight, compute_rms,
)


def test_interpolate_weight_at_breakpoints():
    """Weight at exact breakpoints matches."""
    for x, expected in LIFE_WEIGHT_BREAKPOINTS:
        result = interpolate_weight(x, LIFE_WEIGHT_BREAKPOINTS)
        assert abs(result - expected) < 1e-6, f"At {x}: got {result}, expected {expected}"


def test_interpolate_weight_between():
    """Weight is interpolated between breakpoints."""
    result = interpolate_weight(0.25, LIFE_WEIGHT_BREAKPOINTS)
    assert 1.0 < result < 3.0, f"Expected between 1 and 3, got {result}"
    assert abs(result - 2.0) < 1e-6, f"At 0.25 (midpoint of 0-0.5): expected 2.0, got {result}"


def test_interpolate_weight_clamped():
    """Values outside range are clamped to endpoints."""
    assert interpolate_weight(-1.0, LIFE_WEIGHT_BREAKPOINTS) == 1.0
    assert interpolate_weight(2.0, LIFE_WEIGHT_BREAKPOINTS) == 5.0


def test_slope_weight_breakpoints():
    """Slope weight at key points matches sponsor spec."""
    assert abs(interpolate_weight(0.0, SLOPE_WEIGHT_BREAKPOINTS) - 1.0) < 1e-6
    assert abs(interpolate_weight(5.0, SLOPE_WEIGHT_BREAKPOINTS) - 2.0) < 1e-6
    assert abs(interpolate_weight(10.0, SLOPE_WEIGHT_BREAKPOINTS) - 3.0) < 1e-6
    assert abs(interpolate_weight(20.0, SLOPE_WEIGHT_BREAKPOINTS) - 5.0) < 1e-6


def test_compute_rms():
    """RMS of known signal."""
    signal = np.array([1.0, -1.0, 1.0, -1.0], dtype=np.float32)
    assert abs(compute_rms(signal) - 1.0) < 1e-6

    zeros = np.zeros(100, dtype=np.float32)
    assert compute_rms(zeros) == 0.0


def test_sponsor_weight_example():
    """
    Sponsor's diagram shows: 4.6 (life weight) × 3 (slope weight) = 13.8x.
    Verify: life_weight at ~92% of life ≈ 4.6, slope at ~10°C change ≈ 3.0.
    """
    life_w = interpolate_weight(0.92, LIFE_WEIGHT_BREAKPOINTS)
    slope_w = interpolate_weight(10.0, SLOPE_WEIGHT_BREAKPOINTS)
    combined = life_w * slope_w

    assert abs(life_w - 4.68) < 0.1, f"Life weight at 92%: expected ~4.68, got {life_w}"
    assert abs(slope_w - 3.0) < 0.01, f"Slope weight at 10: expected 3.0, got {slope_w}"
    assert abs(combined - 14.04) < 0.5, f"Combined: expected ~14, got {combined}"


@pytest.fixture
def generated_data_dir():
    """Check if generated data exists."""
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        "data_generator", "generated")
    if not os.path.exists(os.path.join(path, "X_rul.npy")):
        pytest.skip("Generated data not found — run build_rul_dataset first")
    return path


def test_generated_data_shapes(generated_data_dir):
    """Generated data has consistent shapes."""
    X = np.load(os.path.join(generated_data_dir, "X_rul.npy"))
    y = np.load(os.path.join(generated_data_dir, "y_rul.npy"))
    w = np.load(os.path.join(generated_data_dir, "w_rul.npy"))

    assert X.ndim == 2
    assert X.shape[1] == WINDOW_SIZE
    assert len(y) == len(X)
    assert len(w) == len(X)
    assert y.min() >= 0, "RUL should be non-negative"
    assert y.max() <= BEARING_LIFE_HOURS + 1, "RUL should not exceed bearing life"
    assert w.min() > 0, "Weights should be positive"
