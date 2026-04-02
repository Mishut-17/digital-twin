# Data Format Documentation

## Generated Dataset Files

### X_rul.npy
- Shape: `(N, 8192)` — N vibration windows, 8192 samples each
- dtype: `float32`
- Each window is z-normalized (zero mean, unit variance)
- Sampling rate: 16 kHz (0.512 seconds per window)

### y_rul.npy
- Shape: `(N,)` — RUL labels in hours
- dtype: `float32`
- Range: 0 (failure) to 1500 (brand new)

### w_rul.npy
- Shape: `(N,)` — sample weights
- dtype: `float32`
- Computed as: `life_weight × slope_weight`

## Weight Computation

### Bearing Life Weight
| Life Fraction | Weight |
|--------------|--------|
| 0% (new)     | 1.0x   |
| 50% (half)   | 3.0x   |
| 100% (end)   | 5.0x   |

### Slope Weight (Vibration RMS Change)
| RMS Change | Weight |
|-----------|--------|
| 0         | 1.0x   |
| 5         | 2.0x   |
| 10        | 3.0x   |
| 20        | 5.0x   |

## Source Data
- University of Ottawa Ball-bearing Vibration and Acoustic Fault Data (UODS-VAFDC)
- 14 healthy recordings at 42 kHz, resampled to 16 kHz
- Synthetic degradation applied to create run-to-failure trajectories

## Synthetic Degradation
Each trajectory passes through 20 severity steps:
1. Amplitude scaling (1x → 5x)
2. Broadband noise injection
3. Periodic impulses (simulating BPFO)
4. Random spike events
