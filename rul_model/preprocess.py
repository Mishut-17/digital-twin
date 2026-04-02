"""
Preprocessing utilities for RUL model training.
Loads .npy arrays, normalizes, and creates train/val splits.
"""

import numpy as np
from torch.utils.data import Dataset, DataLoader


class RULDataset(Dataset):
    """PyTorch Dataset wrapping (X, y, weights) numpy arrays."""

    def __init__(self, X, y, weights):
        self.X = X
        self.y = y
        self.weights = weights

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx], self.weights[idx]


def load_rul_data(data_dir):
    """Load X_rul.npy, y_rul.npy, w_rul.npy from data_dir."""
    import os
    X = np.load(os.path.join(data_dir, "X_rul.npy"))
    y = np.load(os.path.join(data_dir, "y_rul.npy"))
    w = np.load(os.path.join(data_dir, "w_rul.npy"))
    return X, y, w


def normalize_targets(y):
    """Normalize RUL targets to [0, 1] range. Returns (y_norm, y_max)."""
    y_max = y.max()
    if y_max > 0:
        return y / y_max, y_max
    return y, 1.0


def train_val_split(X, y, w, val_fraction=0.2, seed=42):
    """Random split into train and validation sets."""
    rng = np.random.default_rng(seed)
    n = len(X)
    indices = rng.permutation(n)
    n_val = int(n * val_fraction)

    val_idx = indices[:n_val]
    train_idx = indices[n_val:]

    return (
        (X[train_idx], y[train_idx], w[train_idx]),
        (X[val_idx], y[val_idx], w[val_idx]),
    )


def create_dataloaders(X_train, y_train, w_train, X_val, y_val, w_val,
                       batch_size=64):
    """Create PyTorch DataLoaders for training and validation."""
    train_ds = RULDataset(X_train, y_train, w_train)
    val_ds = RULDataset(X_val, y_val, w_val)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                              num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False,
                            num_workers=0, pin_memory=True)

    return train_loader, val_loader
