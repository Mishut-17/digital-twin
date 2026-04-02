"""
Build RUL Dataset from Vibration Files
=======================================
Loads healthy vibration data from UODS-VAFDC .mat files and creates
synthetic run-to-failure trajectories by progressively degrading the
signals. This approach:
  1. Uses real healthy bearing vibration as the baseline
  2. Synthetically adds degradation (noise, impulses, amplitude growth)
  3. Creates multiple trajectories with different degradation patterns
  4. Labels each window with RUL (hours to failure)
  5. Computes sample weights (life weight × slope weight)

Output: X_rul.npy, y_rul.npy, w_rul.npy
"""

import os
import sys
import numpy as np
import scipy.io
from scipy.signal import resample

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_generator.config import (
    UODS_ROOT, TARGET_SR, WINDOW_SIZE, STEP_SIZE,
    BEARING_LIFE_HOURS, LIFE_WEIGHT_BREAKPOINTS,
    SLOPE_WEIGHT_BREAKPOINTS, GENERATED_DIR,
)


def resample_signal(signal, orig_sr):
    if orig_sr == TARGET_SR:
        return signal
    num_samples = int(len(signal) * TARGET_SR / orig_sr)
    return resample(signal, num_samples)


def compute_rms(window):
    return np.sqrt(np.mean(window ** 2))


def interpolate_weight(value, breakpoints):
    if value <= breakpoints[0][0]:
        return breakpoints[0][1]
    if value >= breakpoints[-1][0]:
        return breakpoints[-1][1]
    for i in range(len(breakpoints) - 1):
        x0, y0 = breakpoints[i]
        x1, y1 = breakpoints[i + 1]
        if value <= x1:
            frac = (value - x0) / (x1 - x0)
            return y0 + frac * (y1 - y0)
    return breakpoints[-1][1]


# ------------------------------------------------------------------
#  Load healthy UODS-VAFDC vibration signals
# ------------------------------------------------------------------
def load_healthy_signals():
    """Load all readable healthy .mat files from UODS-VAFDC."""
    healthy_dir = os.path.join(UODS_ROOT, "1_Healthy")
    signals = []

    if not os.path.isdir(healthy_dir):
        print(f"[error] Healthy directory not found: {healthy_dir}")
        return signals

    for fn in sorted(os.listdir(healthy_dir)):
        if not fn.endswith(".mat"):
            continue
        stem = fn[:-4]
        try:
            mat = scipy.io.loadmat(os.path.join(healthy_dir, fn))
            vibration = mat[stem][:, 0].astype(np.float64)
            vibration = resample_signal(vibration, 42000)  # 42 kHz → 16 kHz
            signals.append(vibration)
        except Exception:
            pass  # Skip corrupted files silently

    return signals


# ------------------------------------------------------------------
#  Synthetic degradation functions
# ------------------------------------------------------------------
def add_degradation(signal, severity, rng):
    """
    Add synthetic bearing fault signatures to a healthy signal.
    severity: 0.0 (healthy) to 1.0 (near failure)
    """
    n = len(signal)
    degraded = signal.copy()

    # 1. Increase overall amplitude (vibration energy grows with damage)
    amplitude_factor = 1.0 + severity * 4.0  # up to 5x at failure
    degraded *= amplitude_factor

    # 2. Add broadband noise (increases with damage)
    noise_level = severity * 0.5 * np.std(signal)
    degraded += rng.normal(0, max(noise_level, 1e-8), n)

    # 3. Add periodic impulses (characteristic of bearing faults)
    if severity > 0.2:
        # Ball pass frequency outer race (BPFO) ~ 3-5x shaft frequency
        impulse_period = int(TARGET_SR / (3.5 * 30))  # ~30 Hz shaft speed
        impulse_amplitude = severity * 2.0 * np.std(signal)
        n_impulses = n // impulse_period
        for i in range(n_impulses):
            pos = i * impulse_period + rng.integers(-10, 10)
            if 0 <= pos < n:
                # Exponentially decaying impulse
                decay_len = min(200, n - pos)
                impulse = impulse_amplitude * np.exp(-np.arange(decay_len) / 30.0)
                impulse *= rng.choice([-1, 1])
                degraded[pos:pos + decay_len] += impulse

    # 4. Add random spikes (localized damage events)
    if severity > 0.5:
        n_spikes = int(severity * 10)
        for _ in range(n_spikes):
            pos = rng.integers(0, n - 100)
            spike_amp = severity * 3.0 * np.std(signal) * rng.uniform(0.5, 2.0)
            spike_len = rng.integers(20, 100)
            degraded[pos:pos + spike_len] += spike_amp * rng.normal(0, 1, spike_len)

    return degraded


def build_trajectory(healthy_signals, trajectory_id, rng):
    """
    Build one run-to-failure trajectory by:
    1. Start with a healthy signal (cycling through available ones)
    2. Progressively degrade it through ~20 severity steps
    3. Concatenate into one long signal representing bearing lifetime
    """
    n_steps = 20  # number of degradation steps per trajectory
    segments = []

    for step in range(n_steps):
        severity = step / (n_steps - 1)  # 0.0 to 1.0

        # Pick a healthy signal as base (cycle through them)
        base_idx = (trajectory_id * n_steps + step) % len(healthy_signals)
        base_signal = healthy_signals[base_idx]

        # Apply degradation
        degraded = add_degradation(base_signal, severity, rng)
        segments.append(degraded)

    return np.concatenate(segments)


# ------------------------------------------------------------------
#  Window and label the trajectory
# ------------------------------------------------------------------
def window_trajectory(trajectory):
    """
    Slide windows across the trajectory, label with RUL,
    and compute sample weights.
    """
    total_samples = len(trajectory)
    X_list = []
    y_list = []
    w_list = []

    for start in range(0, total_samples - WINDOW_SIZE + 1, STEP_SIZE):
        window = trajectory[start:start + WINDOW_SIZE].astype(np.float32)

        # Z-normalize
        std = window.std()
        if std < 1e-8:
            continue
        window = (window - window.mean()) / std

        # Position in trajectory
        center = start + WINDOW_SIZE // 2
        fraction = center / total_samples  # 0.0 = start, 1.0 = end

        # RUL label
        rul_hours = BEARING_LIFE_HOURS * (1.0 - fraction)
        rul_hours = max(rul_hours, 0.0)

        # Life weight
        life_weight = interpolate_weight(fraction, LIFE_WEIGHT_BREAKPOINTS)

        # Slope weight (based on RMS change within window)
        half = WINDOW_SIZE // 2
        rms_first = compute_rms(window[:half])
        rms_second = compute_rms(window[half:])
        rms_change = abs(rms_second - rms_first) * 100
        slope_weight = interpolate_weight(rms_change, SLOPE_WEIGHT_BREAKPOINTS)

        X_list.append(window)
        y_list.append(rul_hours)
        w_list.append(life_weight * slope_weight)

    return (
        np.array(X_list, dtype=np.float32),
        np.array(y_list, dtype=np.float32),
        np.array(w_list, dtype=np.float32),
    )


# ------------------------------------------------------------------
#  Main
# ------------------------------------------------------------------
def main():
    os.makedirs(GENERATED_DIR, exist_ok=True)

    print("=" * 60)
    print("BEARING RUL DATASET BUILDER")
    print(f"  Window: {WINDOW_SIZE} samples, step {STEP_SIZE}")
    print(f"  Target SR: {TARGET_SR} Hz")
    print(f"  Bearing life: {BEARING_LIFE_HOURS} hours")
    print("=" * 60)

    # Load healthy signals
    print("\n[1/3] Loading healthy vibration signals ...")
    healthy_signals = load_healthy_signals()
    print(f"       Loaded {len(healthy_signals)} healthy recordings")

    if len(healthy_signals) == 0:
        print("[FATAL] No healthy signals could be loaded.")
        print("        Check that UODS-VAFDC data exists in phase1/data/")
        sys.exit(1)

    # Build multiple trajectories
    n_trajectories = 15
    rng = np.random.default_rng(42)

    print(f"\n[2/3] Building {n_trajectories} synthetic run-to-failure trajectories ...")
    all_X, all_y, all_w = [], [], []

    for t in range(n_trajectories):
        trajectory = build_trajectory(healthy_signals, t, rng)
        X, y, w = window_trajectory(trajectory)
        all_X.append(X)
        all_y.append(y)
        all_w.append(w)
        print(f"       Trajectory {t+1}/{n_trajectories}: "
              f"{len(X)} windows, "
              f"RUL range [{y.min():.0f}, {y.max():.0f}]h")

    X = np.concatenate(all_X, axis=0)
    y = np.concatenate(all_y, axis=0)
    w = np.concatenate(all_w, axis=0)

    # Shuffle
    print(f"\n[3/3] Shuffling and saving ...")
    perm = rng.permutation(len(X))
    X, y, w = X[perm], y[perm], w[perm]

    np.save(os.path.join(GENERATED_DIR, "X_rul.npy"), X)
    np.save(os.path.join(GENERATED_DIR, "y_rul.npy"), y)
    np.save(os.path.join(GENERATED_DIR, "w_rul.npy"), w)

    print(f"\n{'='*60}")
    print(f"DATASET SUMMARY")
    print(f"{'='*60}")
    print(f"  Total windows: {len(X)}")
    print(f"  X shape: {X.shape}  dtype={X.dtype}")
    print(f"  y range: {y.min():.1f} — {y.max():.1f} hours")
    print(f"  w range: {w.min():.2f} — {w.max():.2f}")
    size_mb = X.nbytes / 1024 / 1024
    print(f"  X size: {size_mb:.1f} MB")
    print(f"\nSaved to {GENERATED_DIR}/")
    print("Done!")


if __name__ == "__main__":
    main()
