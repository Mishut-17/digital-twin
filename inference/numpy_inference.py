"""
Pure-NumPy Inference Engine for RUL Prediction
===============================================
Loads weights from .npz file and performs forward pass using only
np.dot and np.maximum (ReLU). Zero dependency on PyTorch or any ML
framework. Designed for factory-floor deployment with minimal compute.
"""

import numpy as np


class NumpyRULModel:
    """
    Pure NumPy forward pass matching the PyTorch RULModel architecture:
    8192 → 512 (ReLU) → 64 (ReLU) → 1
    """

    def __init__(self, weights_path):
        w = np.load(weights_path)
        self.fc1_w = w["fc1_weight"]   # (512, 8192)
        self.fc1_b = w["fc1_bias"]     # (512,)
        self.fc2_w = w["fc2_weight"]   # (64, 512)
        self.fc2_b = w["fc2_bias"]     # (64,)
        self.fc3_w = w["fc3_weight"]   # (1, 64)
        self.fc3_b = w["fc3_bias"]     # (1,)
        self.y_max = float(w["y_max"][0])

    def predict_normalized(self, x):
        """
        Forward pass returning normalized prediction [0, 1].
        x: shape (8192,) or (batch, 8192) — z-normalized vibration window(s)
        """
        if x.ndim == 1:
            x = x.reshape(1, -1)

        h = np.maximum(0, x @ self.fc1_w.T + self.fc1_b)     # ReLU
        h = np.maximum(0, h @ self.fc2_w.T + self.fc2_b)     # ReLU
        out = h @ self.fc3_w.T + self.fc3_b                   # Linear
        return out.squeeze()

    def predict_hours(self, x):
        """
        Predict RUL in hours.
        x: shape (8192,) or (batch, 8192) — z-normalized vibration window(s)
        """
        norm_pred = self.predict_normalized(x)
        hours = np.clip(norm_pred * self.y_max, 0, self.y_max)
        return float(hours) if np.ndim(hours) == 0 else hours

    def predict_days(self, x):
        """Predict RUL in days."""
        hours = self.predict_hours(x)
        if isinstance(hours, (int, float)):
            return hours / 24.0
        return hours / 24.0
