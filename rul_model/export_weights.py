"""
Export PyTorch model weights to NumPy .npz format.
Enables pure-NumPy inference without any ML framework dependency.

Usage:
    python -m rul_model.export_weights [--model weights/best_model.pt]
"""

import os
import sys
import argparse
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rul_model.model import RULModel

WEIGHTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weights")


def export(model_path, output_path):
    """Extract weight matrices and biases from PyTorch model, save as .npz."""
    ckpt = torch.load(model_path, map_location="cpu", weights_only=False)
    model = RULModel()
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    y_max = ckpt.get("y_max", 1500.0)

    # Extract weights from Sequential layers
    # net.0 = Linear(8192, 512), net.3 = Linear(512, 64), net.6 = Linear(64, 1)
    state = model.state_dict()

    np.savez(
        output_path,
        fc1_weight=state["net.0.weight"].numpy(),
        fc1_bias=state["net.0.bias"].numpy(),
        fc2_weight=state["net.3.weight"].numpy(),
        fc2_bias=state["net.3.bias"].numpy(),
        fc3_weight=state["net.6.weight"].numpy(),
        fc3_bias=state["net.6.bias"].numpy(),
        y_max=np.array([y_max]),
    )
    print(f"Exported to {output_path}")
    print(f"  fc1: ({state['net.0.weight'].shape[1]}, {state['net.0.weight'].shape[0]})")
    print(f"  fc2: ({state['net.3.weight'].shape[1]}, {state['net.3.weight'].shape[0]})")
    print(f"  fc3: ({state['net.6.weight'].shape[1]}, {state['net.6.weight'].shape[0]})")
    print(f"  y_max: {y_max}")

    # File size
    size_kb = os.path.getsize(output_path) / 1024
    print(f"  File size: {size_kb:.1f} KB")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=os.path.join(WEIGHTS_DIR, "best_model.pt"))
    parser.add_argument("--output", default=os.path.join(WEIGHTS_DIR, "rul_model_weights.npz"))
    args = parser.parse_args()

    if not os.path.exists(args.model):
        print(f"Model not found: {args.model}")
        print("Run training first: python -m rul_model.train")
        sys.exit(1)

    export(args.model, args.output)


if __name__ == "__main__":
    main()
