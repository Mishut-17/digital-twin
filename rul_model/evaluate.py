"""
RUL Model Evaluation
====================
Computes MAE, RMSE and generates prediction-vs-actual scatter plot.

Usage:
    python -m rul_model.evaluate [--model weights/best_model.pt]
"""

import os
import sys
import argparse
import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rul_model.model import RULModel
from rul_model.preprocess import load_rul_data, normalize_targets, train_val_split

GENERATED_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data_generator", "generated"
)
WEIGHTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weights")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=os.path.join(WEIGHTS_DIR, "best_model.pt"))
    parser.add_argument("--data-dir", default=GENERATED_DIR)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load data
    X, y, w = load_rul_data(args.data_dir)
    y_norm, y_max = normalize_targets(y)
    _, (X_val, y_val, _) = train_val_split(X, y_norm, w)

    # Load model
    model = RULModel(input_size=X.shape[1]).to(device)
    ckpt = torch.load(args.model, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    y_max_saved = ckpt.get("y_max", y_max)
    model.eval()

    # Predict
    X_val_t = torch.from_numpy(X_val).to(device)
    with torch.no_grad():
        preds_norm = model(X_val_t).cpu().numpy().squeeze()

    preds = preds_norm * y_max_saved
    actuals = y_val * y_max_saved

    # Metrics
    mae = np.mean(np.abs(preds - actuals))
    rmse = np.sqrt(np.mean((preds - actuals) ** 2))
    print(f"Validation Metrics:")
    print(f"  MAE:  {mae:.2f} hours ({mae/24:.2f} days)")
    print(f"  RMSE: {rmse:.2f} hours ({rmse/24:.2f} days)")

    # Scatter plot
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(actuals, preds, alpha=0.3, s=10, c="#e94560")
    ax.plot([0, y_max_saved], [0, y_max_saved], "k--", lw=1, label="Perfect")
    ax.set_xlabel("Actual RUL (hours)")
    ax.set_ylabel("Predicted RUL (hours)")
    ax.set_title(f"RUL Prediction — MAE={mae:.1f}h, RMSE={rmse:.1f}h")
    ax.legend()
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)

    plot_path = os.path.join(WEIGHTS_DIR, "rul_scatter.png")
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Scatter plot saved: {plot_path}")


if __name__ == "__main__":
    main()
