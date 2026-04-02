"""
RUL Prediction Model
====================
Three-layer feedforward network for predicting remaining useful life
(hours until failure) from a vibration signal window.

Architecture: 8192 → 512 → 64 → 1
Total parameters: ~4.2M (small enough for .npz export ~17MB)
"""

import torch
import torch.nn as nn


class RULModel(nn.Module):
    """
    Feedforward regression model for bearing RUL prediction.

    Input:  (batch, 8192)  — z-normalized vibration window
    Output: (batch, 1)     — predicted hours until failure
    """

    def __init__(self, input_size=8192, hidden1=512, hidden2=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, hidden1),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden1, hidden2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden2, 1),
        )

    def forward(self, x):
        return self.net(x)
