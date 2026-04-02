"""
RUL Model Training
==================
Trains the feedforward RUL regression model using weighted MSE loss.
Sample weights reflect bearing life position and vibration slope
per the sponsor's weighting formula.

Usage:
    python -m rul_model.train [--epochs 200] [--batch-size 64] [--lr 1e-3]
"""

import os
import sys
import argparse
import csv
import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rul_model.model import RULModel
from rul_model.preprocess import (
    load_rul_data, normalize_targets, train_val_split, create_dataloaders
)

GENERATED_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data_generator", "generated"
)
OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "weights"
)


def weighted_mse_loss(pred, target, weights):
    """MSE loss where each sample is weighted by its importance."""
    mse = (pred.squeeze() - target) ** 2
    return (mse * weights).mean()


def train_one_epoch(model, loader, optimizer, device):
    model.train()
    total_loss = 0.0
    n_batches = 0
    for X_batch, y_batch, w_batch in loader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)
        w_batch = w_batch.to(device)

        optimizer.zero_grad()
        pred = model(X_batch)
        loss = weighted_mse_loss(pred, y_batch, w_batch)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        n_batches += 1

    return total_loss / max(n_batches, 1)


@torch.no_grad()
def evaluate(model, loader, device, y_max=1.0):
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_targets = []
    n_batches = 0

    for X_batch, y_batch, w_batch in loader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)
        w_batch = w_batch.to(device)

        pred = model(X_batch)
        loss = weighted_mse_loss(pred, y_batch, w_batch)
        total_loss += loss.item()
        n_batches += 1

        all_preds.append(pred.cpu().numpy().squeeze() * y_max)
        all_targets.append(y_batch.cpu().numpy() * y_max)

    preds = np.concatenate(all_preds)
    targets = np.concatenate(all_targets)

    mae = np.mean(np.abs(preds - targets))
    rmse = np.sqrt(np.mean((preds - targets) ** 2))

    return total_loss / max(n_batches, 1), mae, rmse


def main():
    parser = argparse.ArgumentParser(description="Train bearing RUL model")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--data-dir", type=str, default=GENERATED_DIR)
    parser.add_argument("--resume", type=str, default=None,
                        help="Path to checkpoint to resume from")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # Load data
    print(f"Loading data from {args.data_dir} ...")
    X, y, w = load_rul_data(args.data_dir)
    print(f"  X: {X.shape}, y: {y.shape}, w: {w.shape}")

    # Normalize targets to [0, 1]
    y_norm, y_max = normalize_targets(y)
    print(f"  y_max = {y_max:.1f} hours (used to denormalize predictions)")

    # Split
    (X_train, y_train, w_train), (X_val, y_val, w_val) = train_val_split(
        X, y_norm, w, val_fraction=0.2
    )
    print(f"  Train: {len(X_train)}, Val: {len(X_val)}")

    # DataLoaders
    train_loader, val_loader = create_dataloaders(
        X_train, y_train, w_train, X_val, y_val, w_val,
        batch_size=args.batch_size
    )

    # Model
    model = RULModel(input_size=X.shape[1]).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, patience=20, factor=0.5
    )

    start_epoch = 0
    if args.resume and os.path.exists(args.resume):
        ckpt = torch.load(args.resume, map_location=device, weights_only=False)
        model.load_state_dict(ckpt["model_state_dict"])
        optimizer.load_state_dict(ckpt["optimizer_state_dict"])
        start_epoch = ckpt.get("epoch", 0) + 1
        print(f"Resumed from epoch {start_epoch}")

    # Training log
    log_path = os.path.join(OUTPUT_DIR, "training_log.csv")
    log_file = open(log_path, "w", newline="")
    writer = csv.writer(log_file)
    writer.writerow(["epoch", "train_loss", "val_loss", "val_mae_hours", "val_rmse_hours"])

    best_val_loss = float("inf")

    print(f"\nTraining for {args.epochs} epochs ...")
    for epoch in range(start_epoch, args.epochs):
        train_loss = train_one_epoch(model, train_loader, optimizer, device)
        val_loss, val_mae, val_rmse = evaluate(model, val_loader, device, y_max)
        scheduler.step(val_loss)

        writer.writerow([epoch + 1, f"{train_loss:.6f}", f"{val_loss:.6f}",
                         f"{val_mae:.2f}", f"{val_rmse:.2f}"])
        log_file.flush()

        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"  Epoch {epoch+1:>3d}/{args.epochs}  "
                  f"train_loss={train_loss:.4f}  val_loss={val_loss:.4f}  "
                  f"MAE={val_mae:.1f}h  RMSE={val_rmse:.1f}h")

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_loss": val_loss,
                "y_max": y_max,
            }, os.path.join(OUTPUT_DIR, "best_model.pt"))

        # Checkpoint every 50 epochs
        if (epoch + 1) % 50 == 0:
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_loss": val_loss,
                "y_max": y_max,
            }, os.path.join(OUTPUT_DIR, f"checkpoint_epoch{epoch+1}.pt"))

    log_file.close()

    # Save final model
    torch.save({
        "epoch": args.epochs - 1,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "y_max": y_max,
    }, os.path.join(OUTPUT_DIR, "model_final.pt"))

    # Save y_max for inference
    np.save(os.path.join(OUTPUT_DIR, "y_max.npy"), np.array([y_max]))

    print(f"\nTraining complete!")
    print(f"  Best val loss: {best_val_loss:.6f}")
    print(f"  Models saved to {OUTPUT_DIR}/")
    print(f"  Training log: {log_path}")


if __name__ == "__main__":
    main()
